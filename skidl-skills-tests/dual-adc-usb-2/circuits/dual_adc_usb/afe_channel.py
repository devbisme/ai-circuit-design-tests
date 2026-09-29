"""AFE Channel — 20:1 attenuator + 3-amp analog front end, one instance per channel
Block from: architecture/block_diagram.md
Interface nets: BNC_<X>_SIG, GND, V5_A, VN5_A, V3V3_A, VREF_0V5_<X>, ADC_<X>_IN,
                ADC_<X>_VINN   (<X> = A or B)

This file is instantiated TWICE by the assembler (once per channel) with ch='A' and
ch='B' -- it is written parameterised, not duplicated. Ref designators and internal net
names are built from the `ch` suffix so the two instances never collide:
    Channel A -> J2, U100, U101, D100, D101, R100-R109, C100-C112
    Channel B -> J3, U200, U201, D200, D201, R200-R209, C200-C212
(R110-R115/R210-R215 are allocated but unused by this synthesis -- see handoff.)

Signal chain (net_plan.md section 3, ic_selection.md F3, design_risks.md R-05/R-06/R-12):
  BNC -> 20:1 compensated passive attenuator (950 kOhm / 49.9 kOhm, Zin = 1.000 MOhm) ->
  1 kOhm series limiter + BAV99 clamp -> A1 (AD8066 #1, unity-gain buffer) ->
  A2 (AD8066 #2, Sallen-Key 2nd-order LPF, unity gain, Q=0.5412) ->
  A3 (OPA836, inverting MFB 2nd-order LPF + level-shift, gain -2, Q=1.3065) ->
  33 Ohm series damper + 22 pF charge-kickback cap -> ADC_<X>_IN.

**Polarity note (do NOT "fix" in hardware):** A3 is inverting, so ADC_<X>_IN falls as
BNC_<X>_SIG rises. The FPGA packer restores polarity digitally: code_out = 4095 - code_raw
(architecture Decision A6/Carried-forward #6). Do not add a 4th op-amp stage for this.

**A3 runs on +3V3_A single supply** (architecture Decision A7) -- this is ADC
over-voltage protection (A3's own rails bound its output), not a preference.
"""
from skidl import *


@subcircuit
def afe_channel(bnc_sig, gnd, v5_a, vn5_a, v3v3_a, vref_0v5, adc_in, adc_vinn, ch='A'):
    """20:1 attenuator + 3-amp AFE (AD8066ARZ dual + OPA836IDBVR single), one per channel.

    Filter synthesis (deferred to the coder by architecture/design_risks.md R-06):
    4th-order Butterworth, fc = 5.0 MHz, split into two 2nd-order sections with the
    standard Butterworth pole pair Q's Q1 = 0.5412 (a1 = 1/Q1 = 1.8478 = 2*cos(22.5 deg))
    and Q2 = 1.3065 (a2 = 1/Q2 = 0.7654 = 2*cos(67.5 deg)).

    Section 1 (A2, Sallen-Key unity-gain low-pass, R1=R2=R):
        wo = 1/(R*sqrt(C1*C2)),  Q = 0.5*sqrt(C2/C1)   [K=1, standard unity-gain result]
        Target Q1=0.5412 -> C2/C1 = (2*Q1)^2 = 1.1716.
        Choose C1=120pF, C2=140pF (ratio 1.1667, 0.4% low -> Q=0.5400, 0.2% error).
        R = 1/(wo*sqrt(C1*C2)) = 1/(2*pi*5e6 * sqrt(120e-12*140e-12)) = 245.6 Ohm
        -> R1=R2=246 Ohm (E96). Check: fc=4.993 MHz, Q=0.5400 (targets 5.000 MHz/0.5412).

    Section 2 (A3, inverting MFB low-pass, gain -Ho with Ho=R2/R1=2, level-shifted):
        Nodal analysis of the standard 3R+2C MFB topology (R1 in, R2 feedback-to-out,
        R3 mid-to--in, C1 mid-to-gnd shunt, C2 -in-to-out feedback) gives:
        wo^2 = 1/(R2*R3*C1*C2)
        1/(Q*wo) = C2*(R2*R3/R1 + R2 + R3)
        Ho = R2/R1 = 2  ->  R2 = 2*R1
        Choosing C2=10pF, C1=220pF and solving the resulting quadratic in R3 for
        Q2=1.3065 gives R3=300 Ohm, R1=768 Ohm, R2=1536 Ohm (all E96 1%).
        Check with these exact values: fc = 4.999 MHz, Q = 1.307 (targets 5.000/1.3065).
        The DC level shift (architecture ic_selection.md F3: Vout = Vref*(1+Rf/Rin) -
        Vin*(Rf/Rin) = 0.5*3 - 2*Vin) comes for free by biasing the op-amp's + input at
        `vref_0v5` (0.500 V) instead of GND -- no extra parts needed.

    BAV99 clamp decision (datasheets/BAV99_SUMMARY.md flags the installed KiCad symbol
    is COMMON ANODE: pin2=A shared, pins1/3=K). A common-anode pair cannot symmetrically
    clamp one signal node to BOTH a positive and a negative rail (the "low-side" diode
    would end up permanently forward-biased -- verified by hand analysis in this block's
    handoff Decisions table). Decision taken: wire pin2 (common anode) to the signal node
    and pin1 (K) to V5_A only (D_hi, correct polarity: conducts above V5_A + Vf). Pin3 (K)
    is left NC -- true low-side protection is unnecessary here because design_risks.md
    R-12 already shows the attenuator node never exceeds +-2.0 V at the +-40 V [SOFT]
    fault limit, comfortably inside both +-5 V rails; the clamp is a belated backup for
    a far larger fault, not a normal-operation element.

    Args:
        bnc_sig: BNC center-pin signal input (BNC_<X>_SIG), +-10 V full scale,
            +-40 V survivable per design_risks.md R-12.
        gnd: Ground reference (single global GND net, architecture Decision A11).
        v5_a: +5 V analog rail (unregulated, filtered) -- A1/A2 (AD8066) V+.
        vn5_a: -5 V analog rail -- A1/A2 (AD8066) V-.
        v3v3_a: +3.3 V low-noise analog rail -- A3 (OPA836) V+ only (single supply).
        vref_0v5: 0.500 V reference (VREF_0V5_<X>), driven externally by the
            `power_analog` block's REF3025/divider -- this block only loads it (as A3's
            non-inverting input) and does not drive or decouple it further.
        adc_in: Analog output to the ADC (ADC_<X>_IN) -- 0.500-2.500 V, CM 1.500 V,
            already series-damped (R_s 33 Ohm) and charge-kickback filtered (C_s 22 pF)
            by this block before reaching the adc_channel block's VIN+.
        adc_vinn: ADC_<X>_VINN net -- **deliberately NOT connected by this block.** The
            adc_channel block (already written) generates and fully decouples its own
            local 1.500 V VIN- bias from V3V3_A. This block's F3 level-shift is entirely
            separate (injected at A3's + input via `vref_0v5`), so there is nothing for
            afe_channel to add here. Accepted as a parameter only because the work
            order's fixed function signature requires it; recorded as a Decision below.
        ch: Instance suffix, 'A' or 'B'. Selects ref designators and internal net names.
    """
    suffix = ch.upper()
    if suffix == 'A':
        j_ref, ua_ref, ub_ref = 'J2', 'U100', 'U101'
        d_base, r_base, c_base = 100, 100, 100
    else:
        j_ref, ua_ref, ub_ref = 'J3', 'U200', 'U201'
        d_base, r_base, c_base = 200, 200, 200

    def d_ref(n):
        return f'D{d_base + n}'

    def r_ref(n):
        return f'R{r_base + n}'

    def c_ref(n):
        return f'C{c_base + n}'

    # --- Internal nets (not part of the interface) ---
    attn_mid = Net(f'ATTN_{suffix}_MID')     # between R_top1 and R_top2
    attn = Net(f'ATTN_{suffix}')             # attenuator output / divider tap
    bufin = Net(f'AFE_{suffix}_BUFIN')       # after R_ser + clamp, into A1 +input
    afe_1 = Net(f'AFE_{suffix}_1')           # A1 (buffer) output
    afe_2 = Net(f'AFE_{suffix}_2')           # A2 (Sallen-Key) output
    afe_out = Net(f'AFE_{suffix}_OUT')       # A3 (MFB) output, pre-R_s
    sk_na = Net(f'AFE_{suffix}_SK_NA')       # Sallen-Key mid node (R1-R2-C2 junction)
    sk_nb = Net(f'AFE_{suffix}_SK_NB')       # Sallen-Key +input node (R2-C1-opamp junction)
    mfb_na = Net(f'AFE_{suffix}_MFB_NA')     # MFB mid node (R1-R3-C1 junction)
    mfb_nb = Net(f'AFE_{suffix}_MFB_NB')     # MFB -input node (R3-C2-opamp junction)

    # =====================================================================
    # 1. BNC input jack (Amphenol 031-6575, right-angle THT) -- panel edge,
    #    mechanically critical per sourced_bom.md / design_risks.md (unresolved,
    #    carried forward to layout -- verify physical part before panel cutout).
    # =====================================================================
    j_bnc = Part(
        'Connector', 'Conn_Coaxial',
        ref=j_ref, value='BNC_Amphenol_031-6575',
        footprint='Connector_Coaxial:BNC_Amphenol_031-6575_Horizontal',
    )
    j_bnc['In'] += bnc_sig
    j_bnc['Ext'] += gnd  # shield -> chassis/analog ground, single-point per net_plan

    # =====================================================================
    # 2. 20:1 compensated passive attenuator (ic_selection.md F3, design_risks.md R-05/R-12)
    #    950 kOhm (two series 475 kOhm 0805, R-12: package size is a voltage rating, do
    #    not shrink to 0402) : 49.9 kOhm -> Zin = 1.000 MOhm, ratio (950+49.9)/49.9 = 20.04
    #    Compensation: R_top*C_top = R_bot*C_bot keeps the divider flat to 5 MHz across
    #    board/assembly stray capacitance (R-05, an open production trim step). C_trim
    #    (2-10 pF Voltronics JR300 trimmer) parallels R_top2, per net_plan.md section 3's
    #    literal topology ("R_top2 + C_trim -> node"); nominal set point during bring-up
    #    solves R_top2*C_trim = R_bot*C_bot -> C_trim ~= 49.9k*180p/475k = 18.9 pF, which
    #    is ABOVE the 2-10 pF trimmer's range -- flagged in the handoff; the trim range
    #    may need widening once a real board is on the bench (R-05 residual).
    # =====================================================================
    r_top1 = Part('Device', 'R', ref=r_ref(0), value='475k',
                   footprint='Resistor_SMD:R_0805_2012Metric')
    r_top1[1] += bnc_sig
    r_top1[2] += attn_mid

    r_top2 = Part('Device', 'R', ref=r_ref(1), value='475k',
                   footprint='Resistor_SMD:R_0805_2012Metric')
    r_top2[1] += attn_mid
    r_top2[2] += attn

    c_trim = Part('Device', 'C_Trim', ref=c_ref(0), value='2-10pF',
                   footprint='Capacitor_SMD:C_Trimmer_Voltronics_JR')
    c_trim[1] += attn_mid
    c_trim[2] += attn

    r_bot = Part('Device', 'R', ref=r_ref(2), value='49.9k',
                  footprint='Resistor_SMD:R_0603_1608Metric')
    r_bot[1] += attn
    r_bot[2] += gnd

    c_bot = Part('Device', 'C', ref=c_ref(1), value='180pF',
                  footprint='Capacitor_SMD:C_0603_1608Metric')
    c_bot[1] += attn
    c_bot[2] += gnd

    # Optional low-cap TVS at the BNC node -- DNP by default (design_risks.md R-12):
    # footprint populated only if bench ESD testing (IEC 61000-4-2 beyond +-4 kV) demands
    # it. Must stay <2 pF (or it loads the 1 MOhm/5 MHz input) and >=45 V standoff.
    d_esd = Part('Device', 'D_TVS', ref=d_ref(1), value='ESD9L12ST5G (DNP, <2pF, >=45V)',
                  footprint='Diode_SMD:D_SOD-923')
    d_esd[1] += bnc_sig
    d_esd[2] += gnd

    # =====================================================================
    # 3. Series limiter + input clamp -- see docstring for the common-anode BAV99
    #    wiring decision. Only the high-side (V5_A) leg is implemented; see Decisions.
    # =====================================================================
    r_ser = Part('Device', 'R', ref=r_ref(3), value='1k',
                  footprint='Resistor_SMD:R_0402_1005Metric')
    r_ser[1] += attn
    r_ser[2] += bufin

    d_clamp = Part('Diode', 'BAV99', ref=d_ref(0), value='BAV99',
                    footprint='Package_TO_SOT_SMD:SOT-23')
    # Pin names collide (both cathodes are named "K"), so address by pin NUMBER:
    # pin 2 = A (common anode), pin 1 = K, pin 3 = K.
    d_clamp[2] += bufin   # common anode -> signal node
    d_clamp[1] += v5_a    # K (diode 1) -> +5V rail (D_hi: conducts above V5_A + Vf)
    d_clamp[3] += NC      # K (diode 2) -> intentionally NC, see docstring/Decisions

    # =====================================================================
    # 4. A1 -- AD8066 amplifier 1, unity-gain FET-input buffer. Isolates the 47.5 kOhm
    #    attenuator Thevenin source from the filter network (design_risks.md R-06: this
    #    stage is mandatory, not gold-plating -- the attenuator cannot drive the filter
    #    directly).
    # =====================================================================
    u_a = Part(
        'lib/dual_adc_usb.kicad_sym', 'AD8066ARZ',
        ref=ua_ref, value='AD8066ARZ',
        footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
        tool=KICAD9,
    )
    u_a['+IN1'] += bufin
    u_a['-IN1'] += afe_1   # unity feedback: -in tied directly to output
    u_a['OUT1'] += afe_1

    # A1/A2 shared supply rails + decoupling (net_plan.md section 10: 100nF + 1uF at
    # each supply pin; AD8066 has 2 supply pins, shared across both internal amps).
    u_a['+VS'] += v5_a
    u_a['-VS'] += vn5_a

    c_a_pos_100n = Part('Device', 'C', ref=c_ref(7), value='100nF',
                         footprint='Capacitor_SMD:C_0402_1005Metric')
    c_a_pos_100n[1] += v5_a
    c_a_pos_100n[2] += gnd

    c_a_pos_1u = Part('Device', 'C', ref=c_ref(8), value='1uF',
                       footprint='Capacitor_SMD:C_0603_1608Metric')
    c_a_pos_1u[1] += v5_a
    c_a_pos_1u[2] += gnd

    c_a_neg_100n = Part('Device', 'C', ref=c_ref(9), value='100nF',
                         footprint='Capacitor_SMD:C_0402_1005Metric')
    c_a_neg_100n[1] += vn5_a
    c_a_neg_100n[2] += gnd

    c_a_neg_1u = Part('Device', 'C', ref=c_ref(10), value='1uF',
                       footprint='Capacitor_SMD:C_0603_1608Metric')
    c_a_neg_1u[1] += vn5_a
    c_a_neg_1u[2] += gnd

    # =====================================================================
    # 5. A2 -- AD8066 amplifier 2, unity-gain Sallen-Key 2nd-order low-pass.
    #    fc = 5.0 MHz, Q1 = 0.5412 (see docstring synthesis). R_sk1=R_sk2=246 Ohm,
    #    C_sk_shunt=120pF (at the +input node, to GND), C_sk_fb=140pF (mid-node
    #    feedback to the output). Gain = +1 (net_plan.md section 3).
    # =====================================================================
    r_sk1 = Part('Device', 'R', ref=r_ref(4), value='246',
                  footprint='Resistor_SMD:R_0402_1005Metric')
    r_sk1[1] += afe_1
    r_sk1[2] += sk_na

    r_sk2 = Part('Device', 'R', ref=r_ref(5), value='246',
                  footprint='Resistor_SMD:R_0402_1005Metric')
    r_sk2[1] += sk_na
    r_sk2[2] += sk_nb

    c_sk_fb = Part('Device', 'C', ref=c_ref(3), value='140pF',
                    footprint='Capacitor_SMD:C_0402_1005Metric')
    c_sk_fb[1] += sk_na
    c_sk_fb[2] += afe_2

    c_sk_shunt = Part('Device', 'C', ref=c_ref(2), value='120pF',
                       footprint='Capacitor_SMD:C_0402_1005Metric')
    c_sk_shunt[1] += sk_nb
    c_sk_shunt[2] += gnd

    u_a['+IN2'] += sk_nb
    u_a['-IN2'] += afe_2   # unity feedback: -in tied directly to output
    u_a['OUT2'] += afe_2

    # =====================================================================
    # 6. A3 -- OPA836, inverting MFB 2nd-order low-pass + level-shift, gain -2.
    #    fc = 5.0 MHz, Q2 = 1.3065 (see docstring synthesis). R1_mfb=768 Ohm (Rin),
    #    R2_mfb=1536 Ohm (Rf, Ho=Rf/Rin=2), R3_mfb=300 Ohm, C1_mfb=220pF (shunt to
    #    GND), C2_mfb=10pF (feedback to output). Non-inverting input biased at
    #    `vref_0v5` (0.500 V) instead of GND -- this is what produces the free level
    #    shift (ic_selection.md F3): Vout = 0.5*(1+2) - 2*Vin = 1.500 - 2*Vin.
    #    A3 runs on +3V3_A ONLY (architecture Decision A7) -- ADC over-voltage
    #    protection, do not substitute a +-5V-only part here.
    # =====================================================================
    u_b = Part(
        'lib/dual_adc_usb.kicad_sym', 'OPA836IDBVR',
        ref=ub_ref, value='OPA836IDBVR',
        footprint='Package_TO_SOT_SMD:SOT-23-6',
        tool=KICAD9,
    )

    r1_mfb = Part('Device', 'R', ref=r_ref(6), value='768',
                   footprint='Resistor_SMD:R_0402_1005Metric')
    r1_mfb[1] += afe_2
    r1_mfb[2] += mfb_na

    r3_mfb = Part('Device', 'R', ref=r_ref(8), value='300',
                   footprint='Resistor_SMD:R_0402_1005Metric')
    r3_mfb[1] += mfb_na
    r3_mfb[2] += mfb_nb

    r2_mfb = Part('Device', 'R', ref=r_ref(7), value='1536',
                   footprint='Resistor_SMD:R_0402_1005Metric')
    r2_mfb[1] += mfb_na
    r2_mfb[2] += afe_out

    c1_mfb = Part('Device', 'C', ref=c_ref(4), value='220pF',
                   footprint='Capacitor_SMD:C_0402_1005Metric')
    c1_mfb[1] += mfb_na
    c1_mfb[2] += gnd

    c2_mfb = Part('Device', 'C', ref=c_ref(5), value='10pF',
                   footprint='Capacitor_SMD:C_0402_1005Metric')
    c2_mfb[1] += mfb_nb
    c2_mfb[2] += afe_out

    u_b['VIN+'] += vref_0v5   # non-inverting input biased at 0.500V -- free level shift
    u_b['VIN-'] += mfb_nb
    u_b['VOUT'] += afe_out
    u_b['VS+'] += v3v3_a      # single-supply per Decision A7
    u_b['VS-'] += gnd
    u_b['PD'] += v3v3_a       # tie to VS+ for always-on (datasheet flags polarity as
                               # low-confidence -- see handoff Carried forward)

    c_b_100n = Part('Device', 'C', ref=c_ref(11), value='100nF',
                     footprint='Capacitor_SMD:C_0402_1005Metric')
    c_b_100n[1] += v3v3_a
    c_b_100n[2] += gnd

    c_b_1u = Part('Device', 'C', ref=c_ref(12), value='1uF',
                   footprint='Capacitor_SMD:C_0603_1608Metric')
    c_b_1u[1] += v3v3_a
    c_b_1u[2] += gnd

    # =====================================================================
    # 7. Output damper into the ADC (net_plan.md section 3): 33 Ohm series + 22 pF
    #    charge-kickback cap at the ADC_<X>_IN net. adc_in is the interface net that
    #    feeds adc_channel's VIN+; adc_vinn is intentionally untouched (see docstring).
    # =====================================================================
    r_s = Part('Device', 'R', ref=r_ref(9), value='33',
                footprint='Resistor_SMD:R_0402_1005Metric')
    r_s[1] += afe_out
    r_s[2] += adc_in

    c_s = Part('Device', 'C', ref=c_ref(6), value='22pF',
                footprint='Capacitor_SMD:C_0402_1005Metric')
    c_s[1] += adc_in
    c_s[2] += gnd

    # adc_vinn: deliberately not connected by this block -- see Args docstring and
    # this block's handoff Decisions table. Parameter accepted only to satisfy the
    # fixed function_signature from architecture/block_diagram.md.
