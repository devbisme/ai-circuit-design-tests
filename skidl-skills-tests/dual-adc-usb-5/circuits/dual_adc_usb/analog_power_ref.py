"""Analog LDO + bias references — +5V_SW -> FB3 -> TLV75733 -> +3V3_A, plus VBIAS / VREF_FE
Block from: architecture/block_diagram.md
Interface nets: +5V_SW, +3V3_A, VBIAS, VREF_FE, GND

Two jobs:
  1. The quiet 3.3 V analog rail. U3's own PSRR is 45 dB @ 100 kHz, which misses SPEC P8's
     >= 50 dB on its own; the architecture's answer is the input pi-filter, so FB3 + C8 here
     and C3 in `digital_power` are load-bearing for a spec, not generic decoupling
     (handoffs/04_datasheets.md, TLV75733PDRVR summary). Do not delete them.
  2. The two front-end reference rails, both from ONE divider chain so their noise is
     common-mode and cancels in the FDA (architecture decision 5):

       +3V3_A --R8 22.0k--+--R10 10.0k--> U4A(+)   U4A = unity buffer --> VBIAS_DRV
                          |         (C12 100nF)         VBIAS_DRV --R22 10R--> VBIAS = 1.1000 V
                       R9 11.0k
                          |
                         GND

       VBIAS --R19 1.00k--+--> U4B(+)              U4B = unity buffer --> VREF_FE = 1.0453 V
                          |
                      R11 19.1k
                          |
                         GND

     VBIAS = 3.3 x 11.0/33.0 = 1.1000 V exactly (11/33 = 1/3 exactly, both E24).
     VREF_FE = VBIAS x 19.1/(19.1 + 1.00) = 0.95025 x VBIAS = 1.0453 V. VREF_FE is derived
     from VBIAS (not from +3V3_A) so the two track: that is the whole point of decision 5,
     and the front end's zero-input match depends on the RATIO, not the absolute value, so
     nothing downstream needed a resistor change when VBIAS moved.

WHY 1.100 V and not the original 1.200 V (architecture rev 3 / WO-2, closing ERC M-1 and
improving risk R-3): OPA355's input common-mode ceiling is (V+) - 1.5 V = 1.800 V, and with
VBIAS = 1.200 V the buffer input reached 1.639 V at +10 V full scale -- 85 mV of worst-case
margin on the part the whole measurement depends on. At 1.100 V the buffer tops out at
1.544 V, margin ~180 mV. The sum stays 33 kOhm, so divider current and source impedance are
unchanged, and R10/C12 below is untouched.
AND SPECIFICALLY NOT R8 = 23.0k / VBIAS = 1.000 V, which the ERC report proposed: 23.0 kOhm
is not an E96/E24/E192 value, 1.000 V violates the OPA355 abs-max in the -30 V survival case
(SPEC I5), and it pushes the THS4551 summing node toward a floor that has never been read
from a datasheet. Architecture decision 19 -- do not re-litigate it here.

R19/R11 end assignment: R19 = 1.00k is the top (VBIAS-side) leg and R11 = 19.1k the bottom,
giving the 0.95025 ratio the design needs. `net_plan.md` was corrected to match at
architecture rev 2 (the rev-1 plan had the two ends the other way round, which would have
given 0.0498). Do not swap them back — "do not redo" in handoffs/02_architecture.md.

R22 = 10 Ohm isolates U4A's output from `VBIAS` (architecture decision 16, risk R-11).
`VBIAS` carries 200-250 pF — both channels' 82 pF C_bot plus stray — and a 10 MHz-GBW RRIO
op-amp driving that bare loses phase margin and rings on the one node the whole measurement
references. U4A now drives the local net `VBIAS_DRV` and its feedback is taken THERE, inside
R22, so the loop never sees the load capacitance; R22 bridges `VBIAS_DRV` -> `VBIAS`.
Isolation zero ~64 MHz. In the AC-ground role 10 Ohm against the 50 kOhm R_bot is -74 dB,
and the DC drop at the ~2.4 uA the AFE dividers draw is 24 nV, so neither the AC ground nor
the ratiometric DC accuracy is affected.

R10 is the one resistor the architecture left as "function not fixed, coder to specify": used
here as the series element of an R10/C12 low-pass (fc = 160 Hz) between the divider tap and
U4A's input, so +3V3_A's noise does not land on VBIAS. TLV9062's CMOS input bias current
(pA-class) makes the 10 kOhm series resistor's offset contribution negligible.
"""
from skidl import *

# --- Footprint shorthands -------------------------------------------------------------
_FP_R0603 = 'Resistor_SMD:R_0603_1608Metric'
_FP_C0402 = 'Capacitor_SMD:C_0402_1005Metric'
_FP_C0805 = 'Capacitor_SMD:C_0805_2012Metric'
_FP_L0603 = 'Inductor_SMD:L_0603_1608Metric'


@SubCircuit
def analog_power_ref(v5_sw, v3v3_a, vbias, vref_fe, gnd):
    """Analog 3.3 V LDO with input pi-filter, plus buffered 1.100 V / 1.0453 V references.

    Args:
        v5_sw:    Net — +5V_SW, switched 5 V from `digital_power`. CONSUMED only (needs
                  .drive = POWER at the top level if ERC complains). Also U3's enable
                  source, so this block powers up with the rest of the tree behind U9.
        v3v3_a:   Net — +3V3_A, quiet analog rail. DRIVEN by this block (U3.OUT). Consumed
                  by both `afe_channel`s, `adc_dual` (AVDD) and `clock_20m`.
        vbias:    Net — VBIAS, 1.1000 V. DRIVEN by this block (U4A output through R22, with
                  U4A's feedback taken inside R22). It is the AFE dividers' return node and
                  their AC ground.
        vref_fe:  Net — VREF_FE, 1.0453 V = 0.95025 x VBIAS. DRIVEN by this block (U4B out).
        gnd:      Net — GND (single ground net).

    Assumptions:
        * There is no sequencing/enable signal in this design: U3.EN is tied to `+5V_SW`,
          the same node `digital_power` ties U1.EN to, so the analog rail follows U9
          (handoffs/04_datasheets.md "Next phase must" item 6 — EN is active HIGH and must
          never float).
        * BOTH halves of U4 are used (A = VBIAS, B = VREF_FE); nothing is left floating.
        * `VOCM` comes from the ADC's own CM pin in `adc_dual` and is NOT generated here.
        * The AFE's R_bot legs return into VBIAS and its R_g2 legs into VREF_FE; U4 must
          therefore sink/source ~60 uA (the R19/R11 chain) plus a few uA per channel.
    """
    # --- Local nets ---------------------------------------------------------------------
    v5_ldo_in = Net('V5_LDO_IN')      # post-FB3, U3's input pin
    bias_div = Net('VBIAS_DIV')       # R8/R9 tap
    bias_flt = Net('VBIAS_FLT')       # after R10/C12, into U4A(+)
    ref_div = Net('VREF_FE_DIV')      # R19/R11 tap, into U4B(+)
    vbias_drv = Net('VBIAS_DRV')      # U4A output + its feedback tap, inside R22

    # === FB3 + C8: input pi-filter ahead of U3 (load-bearing for SPEC P8) ===============
    FB3 = Part('Device', 'FerriteBead', ref='FB3', value='600R@100MHz', footprint=_FP_L0603)
    FB3[1] += v5_sw
    FB3[2] += v5_ldo_in
    C8 = Part('Device', 'C', ref='C8', value='10uF', footprint=_FP_C0805)
    C8[1] += v5_ldo_in                # downstream leg of the pi (upstream leg = C3 in
    C8[2] += gnd                      # digital_power, on +5V_SW)

    # === U3: TLV75733PDRVR fixed 3.3 V LDO -> +3V3_A ===================================
    # Generated symbol used (not the stock Regulator_Linear:TLV75733PDRV) because it names
    # the exposed pad "EP"; the stock symbol calls both pin 3 and pin 7 "GND".
    U3 = Part('dual_adc_usb', 'TLV75733PDRVR', ref='U3', value='TLV75733PDRVR',
              footprint='Package_DFN_QFN:DFN-6-1EP_2x2mm_P0.65mm_EP1x1.6mm')
    U3['IN'] += v5_ldo_in             # pin 6
    U3['EN'] += v5_sw                 # pin 4 — ACTIVE HIGH, never floating (handoff 04 item 6)
    U3['GND'] += gnd                  # pin 3
    U3['EP'] += gnd                   # pin 7 — thermal pad, mandatory (architecture item 6)
    U3['OUT'] += v3v3_a               # pin 1
    U3[2] += NC                       # NC
    U3[5] += NC                       # NC

    C9 = Part('Device', 'C', ref='C9', value='10uF', footprint=_FP_C0805)
    C9[1] += v3v3_a                   # U3 output bulk (>= 1 uF required)
    C9[2] += gnd
    C10 = Part('Device', 'C', ref='C10', value='100nF', footprint=_FP_C0402)
    C10[1] += v3v3_a                  # HF, at U3.OUT
    C10[2] += gnd

    # === U4: TLV9062IDR dual RRIO op-amp — both halves are reference buffers ============
    # Pins by NUMBER: the symbol's pin names are "+", "-" and "~", all regex-significant.
    #   1 = OUT A, 2 = IN A-, 3 = IN A+, 4 = V-, 5 = IN B+, 6 = IN B-, 7 = OUT B, 8 = V+
    U4 = Part('Amplifier_Operational', 'TLV9062', ref='U4', value='TLV9062IDR',
              footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')
    U4[8] += v3v3_a                   # V+
    U4[4] += gnd                      # V-
    C11 = Part('Device', 'C', ref='C11', value='100nF', footprint=_FP_C0402)
    C11[1] += v3v3_a                  # C_DECOUP_U4 — at the V+ pin
    C11[2] += gnd

    # --- VBIAS: 3.3 V -> 1.1000 V divider -> RC -> U4A unity buffer ---------------------
    # 1.100 V, not 1.200 V, as of architecture rev 3 (WO-2 / ERC M-1): it buys the OPA355
    # ~180 mV of input-CM margin instead of 85 mV. See the module docstring for why 1.000 V
    # (R8 = 23.0k) was rejected. Sum unchanged at 33 kOhm.
    R8 = Part('Device', 'R', ref='R8', value='22.0k', footprint=_FP_R0603)
    R9 = Part('Device', 'R', ref='R9', value='11.0k', footprint=_FP_R0603)
    R8[1] += v3v3_a                   # 11.0/(22.0+11.0) = 1/3 exactly -> 3.3/3 = 1.1000 V
    R8[2] += bias_div
    R9[1] += bias_div
    R9[2] += gnd

    R10 = Part('Device', 'R', ref='R10', value='10.0k', footprint=_FP_R0603)
    C12 = Part('Device', 'C', ref='C12', value='100nF', footprint=_FP_C0402)
    R10[1] += bias_div                # R10/C12 = 160 Hz low-pass on the reference
    R10[2] += bias_flt
    C12[1] += bias_flt
    C12[2] += gnd

    U4[3] += bias_flt                 # IN A+
    U4[1] += vbias_drv                # OUT A  -> VBIAS_DRV (inside R22)
    U4[2] += vbias_drv                # IN A-  -> unity-gain follower, fed back INSIDE R22 so
                                      # the loop never sees VBIAS's 200-250 pF (decision 16)

    # R22: 10 Ohm capacitive-load isolation, VBIAS_DRV -> VBIAS (decision 16 / risk R-11).
    R22 = Part('Device', 'R', ref='R22', value='10R', footprint=_FP_R0603)
    R22[1] += vbias_drv
    R22[2] += vbias

    # --- VREF_FE: 0.95 x VBIAS, taken FROM VBIAS so the two track -> U4B unity buffer ---
    R19 = Part('Device', 'R', ref='R19', value='1.00k', footprint=_FP_R0603)
    R11 = Part('Device', 'R', ref='R11', value='19.1k', footprint=_FP_R0603)
    R19[1] += vbias                   # top leg (see the module docstring's note on the
    R19[2] += ref_div                 # net_plan R11/R19 end assignment)
    R11[1] += ref_div                 # 19.1/(19.1+1.00) = 0.95025
    R11[2] += gnd

    U4[5] += ref_div                  # IN B+
    U4[7] += vref_fe                  # OUT B  -> VREF_FE
    U4[6] += vref_fe                  # IN B-  -> unity-gain follower
