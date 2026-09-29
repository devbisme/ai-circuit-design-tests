"""Digital power tree + load switch — +5V_IN -> U9 -> +5V_SW -> buck 3V3 -> LDO 1V2
Block from: architecture/block_diagram.md
Interface nets: +5V_IN, +5V_SW, PWREN_N, +3V3_D, +3V3_ADCD, +1V2_D, GND

Topology (architecture decision 9, as amended by decisions 13/14):
    +5V_IN --U9 (AP2161WG-7 load switch, EN# = FT232H PWREN#)--> +5V_SW
                                                  |-- U1 SY8089A1AAC buck --> +3V3_D
                                                  |                            |-- FB2 --> +3V3_ADCD
                                                  |                            |-- U2 TLV75801 --> +1V2_D
                                                  '-- (FB3/U3, owned by analog_power_ref)
Everything except the FT232H therefore sits behind U9, so before USB configuration the board
draws only the bridge's ~70 mA. SPEC P4 is met: U9's enable is active LOW and
GND-referenced, so FT232H PWREN# drives it directly and 3.3 V (unconfigured) = OFF.

Values that were fixed upstream and are NOT re-derived here:
  * U2 feedback divider = 11.8 kOhm (OUT->FB) / 10.0 kOhm (FB->GND) for 1.199 V
    (handoffs/04_datasheets.md decision 8 / "Next phase must" item 5, VFB = 0.55 V).
  * U1 feedback divider = 45.3 kOhm / 10.0 kOhm -> 3.318 V. CONFIRMED from a primary source
    (datasheets/SY8089A1AAC.pdf, Silergy AN_SY8089A1, obtained at architecture rev 2):
    VOUT = 0.6 x (1 + RH/RL) with VREF = 591 / 600 / 609 mV, giving 3.268-3.368 V over VREF
    tolerance alone. The rev-1 "if VFB is really 0.8 V the rail comes up at 4.4 V" caveat is
    ruled out and closed. The only condition remaining on these two values: substituting U1
    forces a recomputation against the substitute's own VREF (architecture decision 15).
  * U9 = AP2161WG-7 load switch, 1.1/1.5/1.9 A over-load limit against a 485 mA worst-case
    load, 95 mOhm, 0.6 ms controlled rise (inrush control), reverse-current blocking, UVLO.
    EN# thresholds VIH 2.0 V min / VIL 0.8 V max, GND-referenced; PWREN# is active low at
    0/3.3 V, so it drives EN# directly — no inverter, no level shift, no polarity trap, and
    no gate pull-up of this block's own (datasheets/AP2161WG-7_SUMMARY.md, decisions 13/14).

Values chosen here:
  * R7 = 1.00 kOhm for D4 (green, Vf ~2.0 V) -> ~1.3 mA. Indicator only.
"""
from skidl import *

# --- Footprint shorthands -------------------------------------------------------------
_FP_R0603 = 'Resistor_SMD:R_0603_1608Metric'
_FP_C0402 = 'Capacitor_SMD:C_0402_1005Metric'
_FP_C0805 = 'Capacitor_SMD:C_0805_2012Metric'
_FP_L0603 = 'Inductor_SMD:L_0603_1608Metric'


@SubCircuit
def digital_power(v5_in, v5_sw, pwren_n, v3v3_d, v3v3_adcd, v1v2_d, gnd):
    """PWREN#-gated 5 V load switch, 5 V -> 3.3 V buck, 3.3 V -> 1.2 V LDO, ADC rail ferrite.

    Args:
        v5_in:      Net — +5V_IN, unswitched 5 V from `usb_c_input`. CONSUMED only
                    (needs .drive = POWER at the top level).
        v5_sw:      Net — +5V_SW, switched 5 V. DRIVEN by this block (U9's OUT pin); also
                    consumed by `analog_power_ref` (FB3/U3).
        pwren_n:    Net — PWREN#, FT232H ACBUS8 output. SENSED only here: it is U9's EN#
                    input. `usb_bridge` owns the 10 kOhm pull-up on it.
        v3v3_d:     Net — +3V3_D, 3.3 V digital rail. DRIVEN by this block (U1 + L1).
        v3v3_adcd:  Net — +3V3_ADCD, ferrite-isolated copy of +3V3_D for the ADC's DRVDD.
                    DRIVEN by this block (FB2).
        v1v2_d:     Net — +1V2_D, FPGA core rail. DRIVEN by this block (U2).
        gnd:        Net — GND (single ground net).

    Assumptions:
        * U1.EN and U2.EN are tied to their own input rails, so the tree self-sequences off
          U9: +5V_SW up -> buck up -> +3V3_D up -> 1.2 V LDO up. There is no separate
          sequencing signal anywhere in this design.
        * `adc_dual` provides the local HF decoupling at U5.DRVDD; C7 here is the bulk
          element of the FB2 filter, not a substitute for it.
        * R6 is a DNP 0 Ohm bring-up escape (architecture R-9) — populating it pulls U9's
          EN# low and forces the switch permanently ON. It must stay on the board as an
          unpopulated pad.
    """
    # --- Local nets ---------------------------------------------------------------------
    lx = Net('BUCK_LX')             # U1 switch node -> L1
    fb_3v3 = Net('V3V3D_FB')        # U1 feedback tap
    fb_1v2 = Net('V1V2D_FB')        # U2 feedback tap
    led_a = Net('LED_PWR_A')        # R7 -> D4 anode

    # === U9: AP2161WG-7 current-limited load switch, EN# = PWREN# (decisions 13/14) =====
    # Wired by pin NUMBER, not name: the symbol's names carry KiCad overbar markup
    # (~{EN}, ~{FLG}) and name lookup on those is fragile.
    # Pin table + thresholds: datasheets/AP2161WG-7_SUMMARY.md.
    U9 = Part('Power_Management', 'AP2161W', ref='U9', value='AP2161WG-7',
              footprint='Package_TO_SOT_SMD:SOT-23-5')
    U9[5] += v5_in      # IN
    U9[1] += v5_sw      # OUT
    U9[2] += gnd        # GND
    U9[4] += pwren_n    # EN# — active low, GND-referenced
    U9[3] += NC         # FLG — open-drain fault flag, no consumer on this board

    # R6: DNP 0 Ohm from PWREN_N to GND — the architecture R-9 bring-up escape. Populating it
    # pulls U9's EN# LOW = switch permanently ON. (The rev-1 comment said "gate-to-GND", from
    # when this pad grounded a P-FET gate; the pad and its purpose are unchanged, the sense of
    # "populated" is not inverted — low still means on.) No pull-up of our own belongs on this
    # node: `usb_bridge`'s R_pwren (10 kOhm to 3V3) is what holds EN# high = OFF from the
    # instant VBUS appears and through FT232H reset.
    R6 = Part('Device', 'R', ref='R6', value='0R DNP', footprint=_FP_R0603)
    R6[1] += pwren_n
    R6[2] += gnd

    # === U1: SY8089A1AAC 2 A buck, +5V_SW -> +3V3_D ====================================
    U1 = Part('dual_adc_usb', 'SY8089A1AAC', ref='U1', value='SY8089A1AAC',
              footprint='Package_TO_SOT_SMD:SOT-23-5')
    U1['IN'] += v5_sw               # pin 4
    U1['EN'] += v5_sw               # pin 1 — active high, tied on with the rail
    U1['GND'] += gnd                # pin 2
    U1['LX'] += lx                  # pin 3
    U1['FB'] += fb_3v3              # pin 5

    L1 = Part('Device', 'L', ref='L1', value='2.2uH',
              footprint='Inductor_SMD:L_Changjiang_FNR3015S')
    L1[1] += lx
    L1[2] += v3v3_d

    # FB divider: VOUT = 0.600 V x (1 + R4/R5) -> 3.318 V. VREF primary-sourced at
    # 591/600/609 mV (decision 15) — do not re-derive these two values.
    R4 = Part('Device', 'R', ref='R4', value='45.3k', footprint=_FP_R0603)
    R5 = Part('Device', 'R', ref='R5', value='10.0k', footprint=_FP_R0603)
    R4[1] += v3v3_d
    R4[2] += fb_3v3
    R5[1] += fb_3v3
    R5[2] += gnd

    C3 = Part('Device', 'C', ref='C3', value='10uF', footprint=_FP_C0805)
    C3[1] += v5_sw                  # buck input bulk (also the downstream half of the
    C3[2] += gnd                    # pi-filter that analog_power_ref's FB3 needs)
    C4 = Part('Device', 'C', ref='C4', value='10uF', footprint=_FP_C0805)
    C4[1] += v3v3_d                 # buck output bulk
    C4[2] += gnd

    # === U2: TLV75801PDRVR adjustable LDO, +3V3_D -> +1V2_D (FPGA core) ================
    # Pins by number: the stock symbol names BOTH pin 3 and pin 7 "GND" (7 is the exposed
    # pad), so name lookup is ambiguous by design.
    U2 = Part('Regulator_Linear', 'TLV75801PDRV', ref='U2', value='TLV75801PDRVR',
              footprint='Package_DFN_QFN:DFN-6-1EP_2x2mm_P0.65mm_EP1x1.6mm')
    U2[6] += v3v3_d                 # IN
    U2[4] += v3v3_d                 # EN — active HIGH (handoff 04), tied to its own input
    U2[3] += gnd                    # GND
    U2[7] += gnd                    # EP — exposed thermal pad, mandatory (architecture item 6)
    U2[5] += NC                     # DNC — datasheet: leave unconnected, do NOT ground
    U2[1] += v1v2_d                 # OUT
    U2[2] += fb_1v2                 # FB

    # FB divider FIXED by handoffs/04_datasheets.md decision 8 — do not re-derive.
    # R20/R21 are refs added by this block: the work order allocated only R3-R7 (5 refs)
    # for 7 resistor functions. See the handoff's "Decisions" item 2.
    R20 = Part('Device', 'R', ref='R20', value='11.8k', footprint=_FP_R0603)
    R21 = Part('Device', 'R', ref='R21', value='10.0k', footprint=_FP_R0603)
    R20[1] += v1v2_d                # OUT -> FB
    R20[2] += fb_1v2
    R21[1] += fb_1v2                # FB -> GND
    R21[2] += gnd

    C5 = Part('Device', 'C', ref='C5', value='100nF', footprint=_FP_C0402)
    C5[1] += v3v3_d                 # HF cap at U2.IN
    C5[2] += gnd
    C6 = Part('Device', 'C', ref='C6', value='10uF', footprint=_FP_C0805)
    C6[1] += v1v2_d                 # U2 output cap — datasheet needs >= 0.47 uF for stability
    C6[2] += gnd

    # === FB2 + C7: +3V3_D -> +3V3_ADCD (keeps 24 ADC data lines' switching current out ===
    # of the analog rail — architecture decision 9)
    FB2 = Part('Device', 'FerriteBead', ref='FB2', value='600R@100MHz', footprint=_FP_L0603)
    FB2[1] += v3v3_d
    FB2[2] += v3v3_adcd
    C7 = Part('Device', 'C', ref='C7', value='10uF', footprint=_FP_C0805)
    C7[1] += v3v3_adcd              # bulk half of the FB2 low-pass; U5's local HF caps are
    C7[2] += gnd                    # in adc_dual (C41-C55)

    # === D4 + R7: power-good indicator on +3V3_D ======================================
    R7 = Part('Device', 'R', ref='R7', value='1.0k', footprint=_FP_R0603)
    D4 = Part('Device', 'LED', ref='D4', value='CT-1608UGC-P4',
              footprint='LED_SMD:LED_0603_1608Metric')
    R7[1] += v3v3_d
    R7[2] += led_a
    D4[2] += led_a                  # A (anode)
    D4[1] += gnd                    # K (cathode)
