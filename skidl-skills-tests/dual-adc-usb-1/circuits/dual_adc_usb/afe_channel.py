"""AFE channel — one complete analog front end: BNC, compensated 10:1
attenuator, high-Z buffer, 2nd-order Sallen-Key, THS4521 FDA with a 2nd-order
differential MFB, and the ADC charge-kickback snubber.
Block from: architecture/block_diagram.md
Interface nets: vp4v0, vn4v0, gnd, adc_vcm, ain_p, ain_n

INSTANTIATED TWICE: afe_channel('A', ...) and afe_channel('B', ...).
"""
from skidl import *


@subcircuit
def afe_channel(ch, vp4v0, vn4v0, gnd, adc_vcm, ain_p, ain_n):
    """One oscilloscope-probe-compatible analog channel, BNC to ADC pins.

    `ch` is 'A' or 'B'. It selects the reference-designator block (1xx for A,
    2xx for B) and suffixes the block-internal net names. NOTHING ELSE differs
    between the two instances — see net_plan.md §3.5, which shows channel A.

    SIGNAL CHAIN
      BNC -> compensated 10:1 divider -> clamps -> unity buffer ->
      2nd-order Sallen-Key -> THS4521 FDA (2nd-order differential MFB) ->
      33 R / 22 pF snubber -> ADC AIN+/AIN-

    THE INPUT DIVIDER MUST LOOK LIKE A SCOPE INPUT.
    R1xx+R2xx+R3xx = 3 x 300 k = 900 k in series with R4xx = 100 k to ground:
    1.000 MOhm total, 10:1 division, exactly the load a 10:1 passive probe is
    built to compensate against. The capacitive half must track it or the
    division ratio becomes frequency-dependent:
        R_top * C_top = R_bot * C_bot
        900 k * 22 pF = 19.8 us      (C1xx, C0G, >=250 V)
        100 k * C_bot = 19.8 us  =>  C_bot = 198 pF
    C2xx = 180 pF C0G fixed plus CVx = 5-30 pF trimmer gives 185-210 pF, so
    198 pF sits mid-range with room for board and connector stray. The trimmer
    is what the user turns when compensating a probe.

    NO SERIES RESISTOR sits between the divider tap and the buffer: the 90 k
    Thevenin impedance of the tap IS the fault-current limiter. Adding one
    would only add Johnson noise.

    ANTI-ALIAS FILTER — 4th-order Butterworth, f_c = 4.3 MHz, split across the
    two active stages (design_risks.md §3, block_diagram.md):
      * Sallen-Key stage carries the Q = 1.3065 pole pair (design_risks.md
        names it "the Q = 1.307 stage"), unity gain, equal R = 249 R:
            sqrt(C1*C2) = 1/(2*pi*249*4.3e6) = 148.7 pF
            C1/C2 = (2Q)^2 = 6.828
            -> C1 = 390 pF (feedback), C2 = 56 pF (to ground), both E24 C0G
            realised: f_c = 4.325 MHz, Q = 1.3195  (target 4.30 MHz, 1.3065)
      * FDA stage carries the Q = 0.5412 pole pair as a differential
        multiple-feedback (MFB) section, R1 = R2 = R3 = 249 R:
            w0/Q = (1/C1)(1/R1 + 1/R2 + 1/R3)  ->  C1 = 241 pF
            w0^2 = 1/(R2 R3 C1 C2)             ->  C2 = 91.6 pF
        C1 is a single 120 pF cap BRIDGING the two mid-nodes (a differential
        cap of C/2 replaces two C-to-ground caps), C2 = 91 pF per half.
            realised: f_c = 4.325 MHz, Q = 0.5414 (target 4.30 MHz, 0.5412)

    DEVIATION FROM net_plan.md §3.5 — READ THIS.
    net_plan §3.5 lists the FDA stage as "Rf R109/R110 (249R) with Cf
    C105/C106 (differential 2nd-order)". That parts list is a FIRST-order
    section: an Rf||Cf pair is one real pole, and one real pole cannot
    realise a Q = 0.5412 complex pair. Built exactly as tabulated, the chain
    would be 3rd order, and alias rejection at the 37 MHz fold band would be
    about -56 dB instead of the -74.8 dB that design_risks.md §3 budgets — an
    18.8 dB shortfall in the number the whole oversampling argument rests on.
    This block therefore implements the 2nd-order MFB the architecture text
    calls for ("2nd order around the FDA", block_diagram.md line 97), which
    needs two parts per half beyond the tabulated range:
        R116/R117 (249 R mid-node resistors)  and  C113 (120 pF bridge)
        [R216/R217, C213 on channel B]
    Extra rail-decoupling refs C114/C115 (C214/C215) are likewise outside the
    tabulated range. Both extensions are flagged in the block report; nothing
    else departs from §3.5.

    The MFB section is inverting, which is free here: net_plan §3.5 already
    drives the FDA inverting (signal into IN- through Rg, GND into IN+), and
    on a differential output an inversion is a wire swap, absorbed by the
    gateware's calibration polarity.

    MANDATORY RAIL RC, NOT DECORATION.
    Each amplifier reaches VP4V0/VN4V0 through 10 R + 10 uF + 100 nF. This is
    the mitigation for the LM27762's 2 MHz switching residue, which lands
    INSIDE the 4.3 MHz passband and is ~40 uV RMS at the amplifier output
    without it. An RC and not a ferrite: a 600 R @ 100 MHz bead has only
    ~10-30 R of impedance at 2 MHz. See design_risks.md §2.2.

    Args:
        ch: 'A' or 'B'. Selects the 1xx/2xx designator block and net suffixes.
        vp4v0: +4.00 V analog rail from `power_analog`.
        vn4v0: -4.00 V analog rail from `power_analog`.
        gnd: Ground.
        adc_vcm: 1.5 V from the ADC's own VCMA (ch A) or VCMB (ch B) output,
            setting the FDA output common mode. THE TWO CHANNELS MUST BE
            PASSED DIFFERENT NETS — the LTC2292 datasheet forbids joining
            VCMA and VCMB (net_plan.md §1.2).
        ain_p: Differential output + -> ADC AIN{ch}+.
        ain_n: Differential output - -> ADC AIN{ch}-.
    """
    if ch not in ("A", "B"):
        raise ValueError("afe_channel: ch must be 'A' or 'B', got %r" % (ch,))

    # Designator block: channel A -> 1xx / J2 / CV1 ; channel B -> 2xx / J3 / CV2.
    b = 100 if ch == "A" else 200            # resistor/cap/diode/IC base
    jn = "J2" if ch == "A" else "J3"         # BNC connector
    cvn = "CV1" if ch == "A" else "CV2"      # compensation trimmer
    R = lambda n: "R%d" % (b + n)
    C = lambda n: "C%d" % (b + n)
    D = lambda n: "D%d" % (b + n)
    U = lambda n: "U%d" % (b + n)

    # Block-internal nets, suffixed so the two instances never collide.
    bnc_in = Net("bncIn" + ch)      # BNC centre pin, full +/-10 V swing
    att_out = Net("attOut" + ch)    # divider tap, "node X", +/-1 V
    buf_out = Net("bufOut" + ch)    # unity-gain buffer output
    sk_mid = Net("skMid" + ch)      # Sallen-Key R/R junction
    sk_out = Net("sk2Out" + ch)     # Sallen-Key output, single-ended
    fda_mid_p = Net("fdaMidP" + ch)  # MFB mid-node, signal half
    fda_mid_n = Net("fdaMidN" + ch)  # MFB mid-node, reference half
    vp_amp = Net("vpAmp" + ch)      # U101 V+ behind its 10 R RC
    vn_amp = Net("vnAmp" + ch)      # U101 V- behind its 10 R RC
    vp_fda = Net("vpFda" + ch)      # U102 VS+ behind its own 10 R RC
    # These three are supply rails, not signals: the 10 R RC makes them
    # block-internal nets that ERC would otherwise report as driving a
    # POWER-IN pin with insufficient current.
    for _rail in (vp_amp, vn_amp, vp_fda):
        _rail.drive = POWER

    # ==================================================================
    # Input connector and compensated 10:1 attenuator (net_plan §3.5)
    # ==================================================================
    j = Part("Connector", "Conn_Coaxial", ref=jn,
             value="BNC 031-6575",
             footprint="Connector_Coaxial:BNC_Amphenol_031-6575_Horizontal")
    j["In"] += bnc_in
    j["Ext"] += gnd

    # Three 300 k 0.1 % thin-film in series, not one 900 k: it divides the
    # working voltage and the self-heating three ways, and 0.1 % thin film is
    # not stocked at 900 k.
    prev = bnc_in
    for n in (1, 2, 3):
        r = Part("Device", "R", ref=R(n), value="300k 0.1% TF",
                 footprint="Resistor_SMD:R_0805_2012Metric")
        r[1] += prev
        nxt = att_out if n == 3 else Net("attSeries%s%d" % (ch, n))
        r[2] += nxt
        prev = nxt

    # C1xx — 22 pF C0G across the whole 900 k string. >=250 V rating: it sees
    # the full input swing plus any probe transient.
    c_top = Part("Device", "C", ref=C(1), value="22pF C0G 250V",
                 footprint="Capacitor_SMD:C_0805_2012Metric")
    c_top[1] += bnc_in
    c_top[2] += att_out

    # R4xx — 100 k bottom leg. 900 k : 100 k = 10:1 into 1.000 MOhm.
    r_bot = Part("Device", "R", ref=R(4), value="100k 0.1% TF",
                 footprint="Resistor_SMD:R_0603_1608Metric")
    r_bot[1] += att_out
    r_bot[2] += gnd

    # C2xx 180 pF fixed + CVx 5-30 pF trimmer = the 198 pF the R*C balance
    # needs, with adjustment range for stray.
    c_bot = Part("Device", "C", ref=C(2), value="180pF C0G",
                 footprint="Capacitor_SMD:C_0603_1608Metric")
    c_bot[1] += att_out
    c_bot[2] += gnd

    cv = Part("Device", "C_Variable", ref=cvn, value="5-30pF trimmer",
              footprint="Capacitor_SMD:C_Trimmer_Murata_TZC3")
    cv[1] += att_out
    cv[2] += gnd

    # ==================================================================
    # Node-X protection. The clamps go here, AFTER the divider, so they only
    # ever see +/-1 V in normal use and their leakage sits across a 90 k
    # Thevenin rather than across the input.
    # ==================================================================
    # BAV199 — low-leakage dual series diode, SOT-23. Pin 3 is the common
    # mid-node (anode of D1 / cathode of D2), pin 1 the free cathode, pin 2
    # the free anode. So: common -> node X, cathode -> VP4V0 (clamps above the
    # positive rail), anode -> VN4V0 (clamps below the negative rail). This is
    # net_plan §3.5's "anode-common to VN4V0, cathode-common to VP4V0".
    # Low leakage is the selection criterion, not current rating: any leakage
    # here flows in the 90 k source and becomes an offset.
    d_clamp = Part("Device", "D_Dual_Series_KAC", ref=D(1), value="BAV199LT1G",
                   footprint="Package_TO_SOT_SMD:SOT-23")
    d_clamp["K"] += vp4v0
    d_clamp["A"] += vn4v0
    d_clamp["common"] += att_out

    # 12 V bidirectional TVS to ground — the ESD/overvoltage path the diodes
    # cannot take, e.g. a probe touched to mains while the board is unpowered.
    d_tvs = Part("Device", "D_TVS", ref=D(2), value="PESD12VS1UB",
                 footprint="Diode_SMD:D_SOD-323")
    d_tvs[1] += att_out
    d_tvs[2] += gnd

    # ==================================================================
    # U1x1 — OPA1656 dual. Unit A = unity-gain buffer, unit B = Sallen-Key.
    # Symbol pins are accessed by NUMBER: 1=OUTA, 2=INA-, 3=INA+, 4=V-,
    # 5=INB+, 6=INB-, 7=OUTB, 8=V+ (the symbol names "~", "-", "+" repeat
    # across units and are ambiguous by name).
    # OPA1656 is chosen for its CMOS input: i_n = 6 fA/rtHz [VERIFIED-PDF],
    # 16x inside the <=100 fA/rtHz hard floor, because that current noise
    # flows in the 90 k source impedance.
    # ==================================================================
    u_amp = Part("Amplifier_Operational", "OPA1656ID",
                 ref=U(1), value="OPA1656IDR",
                 footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm")
    u_amp[8] += vp_amp     # V+
    u_amp[4] += vn_amp     # V-

    # Unit A: unity-gain buffer. IN+ takes node X directly.
    u_amp[3] += att_out    # INA+
    u_amp[1] += buf_out    # OUTA
    u_amp[2] += buf_out    # INA- tied to OUTA: unity gain

    # Unit B: 2nd-order Sallen-Key low-pass, unity gain, equal R.
    #   buf_out -R105- skMid -R106- INB+ ; C103 skMid->... no:
    #   C103 (C2) from INB+ to ground, C104 (C1) from OUTB back to skMid.
    r_sk1 = Part("Device", "R", ref=R(5), value="249R 0.1% TF",
                 footprint="Resistor_SMD:R_0402_1005Metric")
    r_sk1[1] += buf_out
    r_sk1[2] += sk_mid

    r_sk2 = Part("Device", "R", ref=R(6), value="249R 0.1% TF",
                 footprint="Resistor_SMD:R_0402_1005Metric")
    r_sk2[1] += sk_mid
    r_sk2[2] += u_amp[5]   # INB+

    # C2 = 56 pF from the non-inverting input to ground.
    c_sk2 = Part("Device", "C", ref=C(3), value="56pF C0G",
                 footprint="Capacitor_SMD:C_0402_1005Metric")
    c_sk2[1] += u_amp[5]
    c_sk2[2] += gnd

    # C1 = 390 pF, the positive-feedback cap from the output back to skMid.
    c_sk1 = Part("Device", "C", ref=C(4), value="390pF C0G",
                 footprint="Capacitor_SMD:C_0402_1005Metric")
    c_sk1[1] += sk_mid
    c_sk1[2] += sk_out

    u_amp[7] += sk_out     # OUTB
    u_amp[6] += sk_out     # INB- tied to OUTB: unity-gain SK

    # ==================================================================
    # U1x2 — THS4521 fully-differential amplifier, single-ended to
    # differential, carrying the Q = 0.5412 MFB section.
    # Symbol: 1=IN-, 2=V_OCM, 3=V_S+, 4=OUT+ (NAME IS EMPTY, use the number),
    # 5=OUT- (empty name, use the number), 6=V_S-, 7=~PD, 8=IN+.
    # Runs SINGLE-SUPPLY VS+ = vp_fda (+4.0 V), VS- = GND -> 4.0 V total,
    # inside the 5.5 V maximum. Its negative-rail input range (CM low
    # -0.2 V min referred to V-) is what allows the ground-referenced
    # reference half [VERIFIED-PDF, finding F13].
    # ==================================================================
    u_fda = Part("Amplifier_Difference", "THS4521ID",
                 ref=U(2), value="THS4521IDR",
                 footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm")
    u_fda["V_{S+}"] += vp_fda
    u_fda["V_{S-}"] += gnd
    u_fda["~{PD}"] += vp_fda        # PD high = enabled (referred to V_S-)
    u_fda["V_{OCM}"] += adc_vcm     # output common mode <- ADC VCM{ch}

    # R1 (input) 249 R into each mid-node. Signal half takes the SK output;
    # reference half takes ground, which is what converts single-ended to
    # differential.
    r_in_p = Part("Device", "R", ref=R(7), value="249R 0.1% TF",
                  footprint="Resistor_SMD:R_0402_1005Metric")
    r_in_p[1] += sk_out
    r_in_p[2] += fda_mid_p

    r_in_n = Part("Device", "R", ref=R(8), value="249R 0.1% TF",
                  footprint="Resistor_SMD:R_0402_1005Metric")
    r_in_n[1] += gnd
    r_in_n[2] += fda_mid_n

    # R3 (mid-node to summing junction) 249 R. OUTSIDE the net_plan §3.5
    # range — required by the 2nd-order MFB, see the deviation note above.
    r_mid_p = Part("Device", "R", ref=R(16), value="249R 0.1% TF",
                   footprint="Resistor_SMD:R_0402_1005Metric")
    r_mid_p[1] += fda_mid_p
    r_mid_p[2] += u_fda["-"]        # IN- (pin 1)

    r_mid_n = Part("Device", "R", ref=R(17), value="249R 0.1% TF",
                   footprint="Resistor_SMD:R_0402_1005Metric")
    r_mid_n[1] += fda_mid_n
    r_mid_n[2] += u_fda["+"]        # IN+ (pin 8)

    # R2 (feedback) 249 R: OUT+ -> IN-, OUT- -> IN+. Rg = Rf = 249 R at
    # 0.1 % is what sets the gain match and hence the CMRR of the pair.
    r_fb_p = Part("Device", "R", ref=R(9), value="249R 0.1% TF",
                  footprint="Resistor_SMD:R_0402_1005Metric")
    r_fb_p[1] += u_fda[4]           # OUT+
    r_fb_p[2] += u_fda["-"]         # IN-

    r_fb_n = Part("Device", "R", ref=R(10), value="249R 0.1% TF",
                  footprint="Resistor_SMD:R_0402_1005Metric")
    r_fb_n[1] += u_fda[5]           # OUT-
    r_fb_n[2] += u_fda["+"]         # IN+

    # C2 = 91 pF, mid-node to the output of that half (it bridges R3 and R2).
    c_mfb_p = Part("Device", "C", ref=C(5), value="91pF C0G",
                   footprint="Capacitor_SMD:C_0402_1005Metric")
    c_mfb_p[1] += fda_mid_p
    c_mfb_p[2] += u_fda[4]          # OUT+

    c_mfb_n = Part("Device", "C", ref=C(6), value="91pF C0G",
                   footprint="Capacitor_SMD:C_0402_1005Metric")
    c_mfb_n[1] += fda_mid_n
    c_mfb_n[2] += u_fda[5]          # OUT-

    # C1 = 241 pF equivalent, realised as ONE 120 pF cap bridging the two
    # mid-nodes: a differential cap of value C/2 replaces two C-to-ground
    # caps and rejects common-mode injection into the filter. OUTSIDE the
    # net_plan §3.5 range — see the deviation note.
    c_bridge = Part("Device", "C", ref=C(13), value="120pF C0G",
                    footprint="Capacitor_SMD:C_0402_1005Metric")
    c_bridge[1] += fda_mid_p
    c_bridge[2] += fda_mid_n

    # V_OCM decoupling, 100 nF.
    c_vocm = Part("Device", "C", ref=C(7), value="100nF",
                  footprint="Capacitor_SMD:C_0402_1005Metric")
    c_vocm[1] += adc_vcm
    c_vocm[2] += gnd

    # ==================================================================
    # ADC interface snubber. 33 R per leg + 22 pF differential absorbs the
    # LTC2292 sample-and-hold's charge kickback and gives the FDA a benign
    # capacitive load. tau = 66 R x 22 pF = 1.45 ns, i.e. a 110 MHz pole:
    # this is a KICKBACK FILTER, NOT one of the Butterworth poles. It sits far
    # enough above 4.3 MHz to leave the filter response untouched.
    # ==================================================================
    r_out_p = Part("Device", "R", ref=R(11), value="33R",
                   footprint="Resistor_SMD:R_0402_1005Metric")
    r_out_p[1] += u_fda[4]
    r_out_p[2] += ain_p

    r_out_n = Part("Device", "R", ref=R(12), value="33R",
                   footprint="Resistor_SMD:R_0402_1005Metric")
    r_out_n[1] += u_fda[5]
    r_out_n[2] += ain_n

    c_kick = Part("Device", "C", ref=C(8), value="22pF C0G",
                  footprint="Capacitor_SMD:C_0402_1005Metric")
    c_kick[1] += ain_p
    c_kick[2] += ain_n

    # ==================================================================
    # Rail RC filters — see the docstring; these are load-bearing.
    # ==================================================================
    # U1x1 V+ : VP4V0 -R113- vp_amp, 10 uF + 100 nF at the pin.
    r_vp_amp = Part("Device", "R", ref=R(13), value="10R",
                    footprint="Resistor_SMD:R_0603_1608Metric")
    r_vp_amp[1] += vp4v0
    r_vp_amp[2] += vp_amp
    for ref, val, fp in ((C(9), "10uF", "Capacitor_SMD:C_0805_2012Metric"),
                         (C(10), "100nF", "Capacitor_SMD:C_0402_1005Metric")):
        c = Part("Device", "C", ref=ref, value=val, footprint=fp)
        c[1] += vp_amp
        c[2] += gnd

    # U1x1 V- : VN4V0 -R115- vn_amp, 10 uF + 100 nF at the pin.
    r_vn_amp = Part("Device", "R", ref=R(15), value="10R",
                    footprint="Resistor_SMD:R_0603_1608Metric")
    r_vn_amp[1] += vn4v0
    r_vn_amp[2] += vn_amp
    for ref, val, fp in ((C(11), "10uF", "Capacitor_SMD:C_0805_2012Metric"),
                         (C(12), "100nF", "Capacitor_SMD:C_0402_1005Metric")):
        c = Part("Device", "C", ref=ref, value=val, footprint=fp)
        c[1] += vn_amp
        c[2] += gnd

    # U1x2 VS+ : its OWN 10 R + 10 uF + 100 nF, not shared with U1x1 — the
    # FDA's supply current swings with the differential output and would
    # otherwise modulate the buffer's rail. Refs C114/C115 are outside the
    # tabulated range (see the deviation note).
    r_vp_fda = Part("Device", "R", ref=R(14), value="10R",
                    footprint="Resistor_SMD:R_0603_1608Metric")
    r_vp_fda[1] += vp4v0
    r_vp_fda[2] += vp_fda
    for ref, val, fp in ((C(14), "10uF", "Capacitor_SMD:C_0805_2012Metric"),
                         (C(15), "100nF", "Capacitor_SMD:C_0402_1005Metric")):
        c = Part("Device", "C", ref=ref, value=val, footprint=fp)
        c[1] += vp_fda
        c[2] += gnd
