"""Analog front end — one channel: BNC, compensated ÷11 attenuator, clamp, buffer, AAF, FDA
Block from: architecture/block_diagram.md  (block_id: analog_frontend)
Interface nets (CH1 instance): CH1_IN, CH1_ADC_P, CH1_ADC_N, VCM, +4V2A, -4V2A, GND

WRITTEN ONCE, INSTANTIATED TWICE (CH1 and CH2) by __main__.py. Nothing here hardcodes
a channel name; refdes are offset by 100*ch so CH1 gets U107/U108/J102... and CH2 gets
U207/U208/J202..., which maps back to the BOM's "U7 x2 / U8 x2 / J2 x2" lines.

Signal chain:

    BNC ±10V ──R13 909k──┬── R15 1k ──┬── U7A buffer ──> Sallen-Key (U7B)
       ‖ C34 15pF        │            │
                    R14 90.9k     D3 BAV199 clamp
                     ‖ C35 150pF   to ±4V2A
                         │
                        GND
    ──> THS4551 differential MFB, gain 1.10 ──> ADC_P / ADC_N (±1.0V diff @ 1.50V CM)

Signal budget (architecture/net_plan.md "## Signal-level budget"):
    ±10.0 V at the BNC → ÷11 → ±0.909 V → unity buffer + SK → FDA ×1.10 → ±1.000 V
    differential (2.0 Vpp) at 1.50 V common mode = AD9235 full scale.

*** ARCHITECTURE AMENDMENT A1 (architecture/driver_amendments.md) ***
U8 (THS4551) runs on a SINGLE +4.2 V supply: VS+ = +4V2A, VS- = GND. The architecture
originally wired it across ±4V2A = 8.4 V, over the part's 5.5 V absolute-maximum
supply. U7 (AD8066) keeps bipolar rails — it must swing to -0.909 V.

*** ERC-REVIEW FIX H1 (handoffs/06_erc.md) — MFB topology and values ***
The first version of this block, and `net_plan.md` rows CH1_MFB_P/CH1_MFB_N, put BOTH
filter capacitors in branches that carry no current with an ideal amplifier: Cf across
Rf (FB+ to the MFB node) and Cdiff across the amplifier's own inputs. That leaves the
summing node with a single resistor attached, so no current can flow through it, the
MFB node collapses onto the virtual ground, and the stage degenerates to ONE pole —
the 4th-order filter SPEC F7 requires becomes 3rd-order and misses the stopband.

The classic multiple-feedback topology needs, per half circuit:
    R1 (Rg)  source        -> node A
    R2 (Rf)  node A        -> output          <- feedback resistor
    R3       node A        -> summing node    <- into the virtual ground
    C1       node A        -> AC ground       <- here: one differential cap across the
                                                 two node-A's, of value C1/2
    C2       summing node  -> output          <- THE path that makes the loop 2nd-order
Values recomputed from w0^2 = 1/(C1*C2*R2*R3) and Q = 1/(w0*C2*R2*R3*(1/R1+1/R2+1/R3))
with R1 = R3 = 1.00k, R2 = 1.10k, using capacitor values already on the BOM:
    C41 = 30 pF differential (C1 = 60 pF per half), C39/C40 = 22 pF feedback
    -> f0 = 4.18 MHz, Q = 0.54
Cascaded with the Sallen-Key (3.95 MHz, Q 1.33) that gives -2.6 dB at 4 MHz,
**-31.4 dB at 10 MHz** (F7 needs >=30) and **-55.4 dB at 20 MHz** (F7 needs >=50).
DC gain is unchanged at R2/R1 = 1.10.
"""
from skidl import *


@SubCircuit
def analog_frontend(bnc_in, adc_p, adc_n, vcm, vpos, vneg, gnd, ch=1):
    """One ±10 V input channel, BNC to differential ADC drive.

    Args:
        bnc_in (Net): INPUT to the chain — the BNC centre pin (CH1_IN / CH2_IN).
                      ±10 V full scale, 1 MΩ ∥ ~18 pF.
        adc_p  (Net): OUTPUT. FDA + output through R24 33 Ω. To the ADC VIN+.
        adc_n  (Net): OUTPUT. FDA − output through R25 33 Ω. To the ADC VIN−.
        vcm    (Net): INPUT. 1.50 V common-mode reference from adc_pair's divider,
                      drives U8 VOCM.
        vpos   (Net): INPUT. +4V2A analog rail. U7 V+ and U8 VS+ (see A1).
        vneg   (Net): INPUT. -4V2A analog rail. U7 V− only (see A1).
        gnd    (Net): INPUT. Single GND net; also U8 VS− per amendment A1.
        ch     (int): 1 or 2. Only affects refdes numbering (100*ch offset), so the
                      two instances produce deterministic, layout-friendly references
                      instead of SKiDL's `_1` uniquifying suffixes.

    Assumptions and carried risks:
      * J2 footprint is CONFIRMED WRONG (handoffs/04_datasheets.md #3): the real
        KH-BNC50-3511 uses 10.1 mm hole spacing, not the sourced footprint's 2.54 mm
        grid, and the board-contact count could not be resolved from the available
        drawing. The sourced string is used so the netlist is complete and validates;
        a custom footprint MUST be built and checked against a physical sample before
        Gerbers. See architecture/driver_amendments.md A4.
      * Input compensation uses fixed caps, not a trimmer: the sourced trimmer had
        2–7 units of stock (handoffs/03_sourcing.md Decision 3). C35 is ±5 %, not the
        architecture's ±2 % target, which trades HF flatness at the top of the band.
      * D3 (BAV199) clamps the buffer input to the ±4.2 V rails, protecting U7 against
        the ±50 V survival requirement (SPEC F9) behind the ÷11 divider.
    """
    n = 100 * ch          # refdes offset: CH1 -> 1xx, CH2 -> 2xx

    # ---- Templates (values and footprints verbatim from sourcing/sourced_bom.md) ----
    r_0402 = Part('Device', 'R', dest=TEMPLATE,
                  footprint='Resistor_SMD:R_0402_1005Metric')
    r_0603 = Part('Device', 'R', dest=TEMPLATE,          # 909k needs the 100 V part
                  footprint='Resistor_SMD:R_0603_1608Metric')
    c_0402 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0402_1005Metric')
    c_0603 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0603_1608Metric')

    # ---- J2: BNC jack, ±10 V input, mates with standard scope leads (SPEC I3) ------
    J2 = Part('Connector', 'Conn_Coaxial', ref=f'J{n + 2}', value='KH-BNC50-3511',
              footprint='Connector_Coaxial:BNC_Win_364A2x95_Horizontal')

    # ---- U7: AD8066 dual FastFET — A = unity buffer, B = Sallen-Key ---------------
    U7 = Part('dual_adc_usb', 'AD8066ARZ', ref=f'U{n + 7}', value='AD8066ARZ-R7',
              footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')

    # ---- U8: THS4551 fully-differential ADC driver + MFB filter stage -------------
    U8 = Part('Amplifier_Difference', 'THS4551xRGT', ref=f'U{n + 8}',
              value='THS4551IRGTR',
              footprint='Package_DFN_QFN:QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm')

    # ---- Compensated 1 MΩ ÷11 attenuator (net_plan "Input network") ---------------
    R13 = r_0603(ref=f'R{n + 13}', value='909k')   # top leg, 100 V rated, ±0.1 %
    R14 = r_0402(ref=f'R{n + 14}', value='90.9k')  # bottom leg
    C34 = c_0603(ref=f'C{n + 34}', value='15pF')   # top compensation, ≥100 V
    C35 = c_0402(ref=f'C{n + 35}', value='150pF')  # bottom comp (±5 %, see docstring)

    # ---- Series stopper + clamp into the buffer ----------------------------------
    R15 = r_0402(ref=f'R{n + 15}', value='1k')
    # BAV199 is a dual low-leakage diode in SERIES (pin1 anode, pin3 common, pin2
    # cathode) — KiCad has no BAV199 SOT-23 symbol, so the generic series-pair symbol
    # with the matching pin order is used and the MPN carried in `value`.
    D3 = Part('Device', 'D_Dual_Series_AKC', ref=f'D{n + 3}', value='BAV199',
              footprint='Package_TO_SOT_SMD:SOT-23')

    # ---- Sallen-Key stage (U7B): R16/R17/C36/C37, fc 3.95 MHz Q 1.33 -------------
    R16 = r_0402(ref=f'R{n + 16}', value='324')
    R17 = r_0402(ref=f'R{n + 17}', value='324')
    C36 = c_0402(ref=f'C{n + 36}', value='330pF')  # feedback cap, to CH_SKMID
    C37 = c_0402(ref=f'C{n + 37}', value='47pF')   # cap to GND

    # ---- FDA network (U8): see the MFB discussion in the module docstring ---------
    R18 = r_0402(ref=f'R{n + 18}', value='1k')     # R1/Rg, signal side
    R19 = r_0402(ref=f'R{n + 19}', value='1k')     # R1/Rg, reference side
    R20 = r_0402(ref=f'R{n + 20}', value='1.1k')   # R2/Rf
    R21 = r_0402(ref=f'R{n + 21}', value='1.1k')   # R2/Rf
    R22 = r_0402(ref=f'R{n + 22}', value='1k')     # R3, into the summing node
    R23 = r_0402(ref=f'R{n + 23}', value='1k')     # R3, into the summing node
    C39 = c_0402(ref=f'C{n + 39}', value='22pF')   # C2, summing node -> FB+  (H1 fix)
    C40 = c_0402(ref=f'C{n + 40}', value='22pF')   # C2, summing node -> FB-  (H1 fix)
    C41 = c_0402(ref=f'C{n + 41}', value='30pF')   # C1, differential across node A (H1)
    R24 = r_0402(ref=f'R{n + 24}', value='33')     # ADC series isolation
    R25 = r_0402(ref=f'R{n + 25}', value='33')
    C42 = c_0402(ref=f'C{n + 42}', value='22pF')   # ADC differential kickback filter

    # ---- Decoupling: 100 nF + 10 µF per supply pin (skidl-syntax.md) -------------
    C_DECOUP_U7P = c_0402(ref=f'C{n + 43}', value='100nF')
    C_DECOUP_U7N = c_0402(ref=f'C{n + 44}', value='100nF')
    C_BULK_U7P = c_0603(ref=f'C{n + 45}', value='10uF')
    C_BULK_U7N = c_0603(ref=f'C{n + 46}', value='10uF')
    C_DECOUP_U8 = c_0402(ref=f'C{n + 38}', value='100nF')
    C_BULK_U8 = c_0603(ref=f'C{n + 47}', value='10uF')

    # =================== Connections ==========================================
    # BNC: centre → CH_IN, shell → GND
    J2[1] += bnc_in
    J2[2] += gnd

    # Compensated divider: CH_IN --R13/C34-- CH_TAP --R14/C35-- GND
    tap = Net(f'CH{ch}_TAP')
    bnc_in += R13[1], C34[1]
    tap += R13[2], C34[2], R14[1], C35[1]
    gnd += R14[2], C35[2]

    # Series stopper into the buffer input, clamped to the rails by D3.
    # pin 3 (common) is the clamped node; pin 1 (anode) to -4V2A clamps undershoot,
    # pin 2 (cathode) to +4V2A clamps overshoot.
    bufin = Net(f'CH{ch}_BUFIN')
    tap & R15 & bufin
    D3['common'] += bufin
    D3['A'] += vneg
    D3['K'] += vpos

    # U7A: unity-gain buffer (output tied to inverting input)
    buf = Net(f'CH{ch}_BUF')
    U7['INA_P'] += bufin
    U7['OUTA'] += buf
    U7['INA_N'] += buf

    # U7B: unity-gain Sallen-Key low-pass
    skmid = Net(f'CH{ch}_SKMID')
    sk = Net(f'CH{ch}_SK')
    buf & R16 & skmid & R17 & U7['INB_P']
    U7['INB_P'] += C37[1]
    gnd += C37[2]
    U7['OUTB'] += sk
    U7['INB_N'] += sk
    C36[1] += sk
    C36[2] += skmid

    # ---- U8 THS4551 differential MFB stage (topology per docstring / H1 fix) -----
    # Node A per side: signal enters through Rg, feedback returns through Rf, and R3
    # carries it on into the summing node.
    mfb_p = Net(f'CH{ch}_MFB_P')
    mfb_n = Net(f'CH{ch}_MFB_N')
    sk & R18 & mfb_p
    gnd & R19 & mfb_n

    # R3 into the amplifier summing nodes. Polarity matters: an FDA's OUT+ is out of
    # phase with IN-, so the node fed back from OUT+/FB+ must drive IN- (and vice
    # versa) or the loop is POSITIVE feedback and the stage latches.
    R22[1] += mfb_p
    R22[2] += U8['IN-']
    R23[1] += mfb_n
    R23[2] += U8['IN+']

    # C1: one differential capacitor across the two node-A's. In the half-circuit it
    # presents 2*C41 from node A to the AC-ground midpoint.
    C41[1] += mfb_p
    C41[2] += mfb_n

    # Rf: feedback resistor from the feedback-sense pin back to node A.
    # handoffs/04_datasheets.md: "Connect the MFB network's feedback resistor/cap
    # directly to FB+/FB-, not OUT+/OUT-" — FB+/FB- are internally tied to the
    # outputs but routed separately so the filter network sees less parasitic.
    U8['OUT+'] += adc_p
    U8['OUT-'] += adc_n
    R20[1] += U8['FB+']
    R20[2] += mfb_p
    R21[1] += U8['FB-']
    R21[2] += mfb_n

    # C2: THE second-order path — summing node to the output. Without this the stage
    # is first-order (see H1 in the docstring).
    C39[1] += U8['IN-']
    C39[2] += U8['FB+']
    C40[1] += U8['IN+']
    C40[2] += U8['FB-']

    # Output series isolation + differential kickback cap to the ADC
    adcin_p = Net(f'CH{ch}_ADCIN_P')
    adcin_n = Net(f'CH{ch}_ADCIN_N')
    adc_p & R24 & adcin_p
    adc_n & R25 & adcin_n
    C42[1] += adcin_p
    C42[2] += adcin_n

    # VOCM sets the 1.50 V output common mode; PD must be HIGH for normal operation
    # (handoffs/04_datasheets.md: "PD (pin 12) tied HIGH — do not float").
    U8['VOCM'] += vcm
    U8['~{PD}'] += vpos

    # ---- Supplies -------------------------------------------------------------
    # U7 bipolar (needs to swing below ground); U8 single-supply per amendment A1.
    U7['VS_POS'] += vpos
    U7['VS_NEG'] += vneg
    U8['VS+'] += vpos
    U8['VS-'] += gnd
    # Thermal pad ties to VS-, which amendment A1 makes GND.
    U8['EP'] += gnd

    vpos & C_DECOUP_U7P & gnd
    vpos & C_BULK_U7P & gnd
    vneg & C_DECOUP_U7N & gnd
    vneg & C_BULK_U7N & gnd
    vpos & C_DECOUP_U8 & gnd
    vpos & C_BULK_U8 & gnd
