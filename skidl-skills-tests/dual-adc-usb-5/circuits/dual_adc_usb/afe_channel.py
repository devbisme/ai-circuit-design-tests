"""Analog front end, one channel — /20 compensated divider -> clamp -> OPA355 buffer -> THS4551 FDA
Block from: architecture/block_diagram.md
Interface nets: AIN1|AIN2, CH1_P|CH2_P, CH1_N|CH2_N, VBIAS, VREF_FE, VOCM, +3V3_A, GND

ONE file, instantiated TWICE. The `ch` argument (1 or 2) selects the ref-designator set
fixed by `sourcing/sourced_bom.md` ("afe_channel ref-number key"):

    ch=1 -> J2, U_buf1, U_fda1, D_clamp1, R101..R112, C101..C111
    ch=2 -> J3, U_buf2, U_fda2, D_clamp2, R201..R212, C201..C211

R111/R112/C111 (R211/R212/C211) are NEW at architecture rev 3: the anti-alias filter became
a multiple-feedback (MFB) section around the FDA, so each leg gained a 499 ohm resistor and
the pair gained one differential 68 pF cap (WO-1, closing ERC finding H-1).

`C_top<ch>` / `C_bot<ch>` in `02_architecture.md`'s parts-by-block list are the SAME parts as
C101/C102 (C201/C202) in the sourcing ref-number key, not extra components — the sourcing key
is authoritative ("Do not redo": use the R1xx/C1xx numbered mapping above), so no
C_top*/C_bot* ref designator is emitted.

Pin NUMBERS (not names) are used for U_buf and U_fda. Their KiCad symbol pin names contain
regex-significant characters that SKiDL would treat as patterns ('+', '-', '~', '~{PD}'), and
`Amplifier_Operational:OPA355NA` names its output pin '~'. Every number below is commented
with the datasheet pin name.

Two upstream uncertainties were CLOSED here against primary sources (see the block handoff):

  * THS4551 PD (pin 12) is active LOW -- TI SBOS778D Table 6-1: "PD = logic low = power off
    mode; PD = logic high = normal operation", and Section 10.1: "tie the PD pin to the
    positive supply voltage" for always-on. Tied to +3V3_A here.
  * THS4551 RGT-package FB pins ARE internally connected to the amplifier inputs, crosswise,
    through a 3.3 ohm internal trace -- TI SBOS778D Figure 9-2 (Functional Block Diagram):
    FB+ (pin 4) <-> IN- (pin 3), FB- (pin 1) <-> IN+ (pin 2). So R_f lands on the FB pin and
    R_g lands on the IN pin; they are deliberately NOT strapped together on the board, which
    is the whole point of the 16-pin package.
  * BAV99 polarity -- Nexperia BAV99 series datasheet Rev. 8 Table 3 (Pinning): pin 1 =
    anode(diode 1), pin 2 = cathode(diode 2), pin 3 = cathode(diode 1) + anode(diode 2).
    KiCad's `Diode:BAV99` pin *names* ("K", "A", "K") contradict its own graphics and the
    datasheet; the graphics and the datasheet agree. Wired by number accordingly.
"""
from skidl import *

# --- Footprint shorthands -------------------------------------------------------------
_FP_R0603 = 'Resistor_SMD:R_0603_1608Metric'
_FP_R0805 = 'Resistor_SMD:R_0805_2012Metric'
_FP_C0402 = 'Capacitor_SMD:C_0402_1005Metric'
_FP_C0603 = 'Capacitor_SMD:C_0603_1608Metric'
_FP_TRIM = 'Capacitor_Trimmer_SEHWA:C_Trimmer_SEHWA_STC3MA-2Pin_4.5x3.2mm'


@SubCircuit
def afe_channel(ain, adc_in_p, adc_in_n, vbias, vref_fe, vocm, v3v3_a, gnd, ch=1):
    """One analog input channel: 1 Mohm /20 compensated divider -> clamp -> buffer -> FDA.

    Signal chain (architecture decision 5):
      BNC -> R_top (2 x 475k) with a 2-6 pF trimmer across it -> tap -> R_bot 49.9k + 82 pF
      returning to VBIAS (the return to VBIAS, not GND, IS the level shift -- P6 forbids a
      negative rail) -> 1 kohm + BAV99 rail clamp -> OPA355 unity buffer -> THS4551 FDA at
      G = 2 referenced to VREF_FE, whose feedback network IS a 2nd-order MFB low-pass ->
      output RC -> 3rd-order Butterworth anti-alias, -3 dB at 6.1 MHz -> ADC.

    DC operating point (why VREF_FE = 0.95 * VBIAS): with AIN at 0 V the tap sits at
    VBIAS * 950k/999.9k = 1.0452 V, so subtracting VREF_FE = 1.0453 V gives zero differential
    output at zero input. The buffer input therefore spans 0.546...1.544 V over +-10 V in.
    Gain to the ADC = (49.9/999.9) * 1 * 2 = 1/10.02, i.e. +-10 V in -> 2.0 Vpp differential
    out.  VBIAS is 1.100 V and VREF_FE 1.0453 V as of architecture rev 3 (WO-2, ERC M-1:
    1.200 V left the OPA355 only 85 mV of input-CM headroom at +10 V full scale).  NO
    resistor in the divider changes -- the /20 ratio is untouched and the zero-input match
    depends on the VREF_FE/VBIAS *ratio*, not on the absolute value.

    Args:
        ain:      channel input, +-10 V, straight off the BNC centre pin (AIN1 / AIN2).
        adc_in_p: differential output +, to the ADC (CH1_P / CH2_P). DRIVEN by this block.
        adc_in_n: differential output -, to the ADC (CH1_N / CH2_N). DRIVEN by this block.
        vbias:    1.100 V divider return / AC ground. SENSED only -- driven by analog_power_ref.
        vref_fe:  1.0453 V FDA reference. SENSED only -- driven by analog_power_ref.
        vocm:     FDA output common-mode set, ~1.65 V. SENSED only -- driven by adc_dual from
                  the ADC's own CM pin (net_plan.md: do NOT generate it separately). No
                  decoupling on it here; adc_dual owns C_vocm.
        v3v3_a:   clean analog 3.3 V rail. Also the clamp's positive rail.
        gnd:      the single GND net (architecture decision 12 -- no AGND/DGND split).
        ch:       1 or 2. Selects the ref-designator set. MUST be passed explicitly by the
                  assembler for the second instance or refs collide.
    """
    if ch not in (1, 2):
        raise ValueError('afe_channel: ch must be 1 or 2, got %r' % (ch,))

    def r_ref(i):
        return 'R%d%02d' % (ch, i)      # ch=1,i=3 -> 'R103'

    def c_ref(i):
        return 'C%d%02d' % (ch, i)      # ch=2,i=10 -> 'C210'

    # Internal nets, named per architecture/net_plan.md's per-channel list.
    divnode = Net('CH%d_DIVNODE' % ch)   # divider tap, 47.5 kohm source impedance
    bufin = Net('CH%d_BUFIN' % ch)       # clamp node = OPA355 +IN (net_plan did not name it)
    bufout = Net('CH%d_BUFOUT' % ch)     # buffer output
    fda_inp = Net('CH%d_INP' % ch)       # R_mfb_p -> U_fda IN+
    fda_inn = Net('CH%d_INN' % ch)       # R_mfb_n -> U_fda IN-
    fda_fbp = Net('CH%d_FBP' % ch)       # U_fda FB+ (internally = IN-) and its C_f ONLY
    fda_fbn = Net('CH%d_FBN' % ch)       # U_fda FB- (internally = IN+) and its C_f ONLY
    mfb_p = Net('CH%d_MFBP' % ch)        # MFB summing node, signal leg (rev 3)
    mfb_n = Net('CH%d_MFBN' % ch)        # MFB summing node, reference leg (rev 3)

    # ---------------------------------------------------------------------------------
    # Input connector — KH-BNC50-3511, board-side elbow 50 ohm BNC
    # ---------------------------------------------------------------------------------
    # 4-pin generic symbol (not the 3-pin one the datasheet summary suggested) so that every
    # NUMBERED pad of the assigned footprint lands on a net: pin 1 = centre/signal,
    # pins 2-4 = the ground/mounting legs. See the handoff -- this footprint is an OPEN RISK
    # (datasheets/KH-BNC50-3511_SUMMARY.md); if layout replaces it with a custom 3-hole
    # footprint, drop pin 4 here at the same time.
    j = Part('Connector_Generic', 'Conn_01x04', ref='J%d' % (ch + 1),
             value='KH-BNC50-3511', footprint='Connector_Coaxial:BNC_Amphenol_031-6575_Horizontal')
    ain += j[1]                          # centre conductor
    gnd += j[2], j[3], j[4]              # shell / mounting legs

    # ---------------------------------------------------------------------------------
    # /20 compensated divider — R_top = 2 x 475k in series (voltage rating, ~+-150 V limit)
    # ---------------------------------------------------------------------------------
    r_top_a = Part('Device', 'R', ref=r_ref(1), value='475k',
                   footprint=_FP_R0805)   # 0805W8D4753T5E, +-0.5%
    r_top_b = Part('Device', 'R', ref=r_ref(2), value='475k', footprint=_FP_R0805)
    r_bot = Part('Device', 'R', ref=r_ref(3), value='49.9k',
                 footprint=_FP_R0603)     # ARG03DTC4992, +-0.5% (E96 nearest 50.0k)

    ain += r_top_a[1]
    r_top_a[2] += r_top_b[1]
    r_top_b[2] += divnode
    divnode += r_bot[1]
    r_bot[2] += vbias                     # <-- divider returns to VBIAS, not GND

    # Compensation: R_top * C_top = R_bot * C_bot_total.  950k * C_top = 49.9k * ~89 pF
    # -> C_top ~ 4.7 pF, mid-range of the 2-6 pF trimmer.  MUST stay a trimmer (architecture
    # decision 10): ~7 pF of the bottom leg is unpredictable stray (amp + clamp + trace).
    c_top = Part('Device', 'C_Trim', ref=c_ref(1), value='2-6pF (set ~4.7pF)',
                 footprint=_FP_TRIM)      # STC3MA06-T1, custom footprint from phase 04
    c_bot = Part('Device', 'C', ref=c_ref(2), value='82pF',
                 footprint=_FP_C0603)     # C0G, +-5% (trimmer nulls the residual)

    ain += c_top[1]
    c_top[2] += divnode                   # trimmer across the whole top leg
    divnode += c_bot[1]
    c_bot[2] += vbias                     # parallels R_bot, same AC-ground return

    # ---------------------------------------------------------------------------------
    # Overvoltage clamp — 1 kohm + BAV99 to the rails AT THE BUFFER INPUT
    # (architecture decision 11: deliberately NOT a TVS at the BNC, which would hang
    #  50-100 pF of nonlinear capacitance across the 1 Mohm input)
    # ---------------------------------------------------------------------------------
    r_prot = Part('Device', 'R', ref=r_ref(4), value='1k', footprint=_FP_R0603)
    divnode += r_prot[1]
    r_prot[2] += bufin

    d_clamp = Part('Diode', 'BAV99', ref='D_clamp%d' % ch, value='BAV99',
                   footprint='Package_TO_SOT_SMD:SOT-23')
    # Nexperia Table 3: 1 = anode(D1), 3 = cathode(D1)+anode(D2), 2 = cathode(D2).
    d_clamp[3] += bufin                   # common midpoint sits on the signal
    gnd += d_clamp[1]                     # D1 conducts GND -> signal  (negative clamp)
    v3v3_a += d_clamp[2]                  # D2 conducts signal -> +3V3_A (positive clamp)

    # ---------------------------------------------------------------------------------
    # U_buf — OPA355NA unity-gain buffer (chosen for 3 pA Ib into a 47.5 kohm node)
    # pins: 1=OUT, 2=V-, 3=+IN, 4=-IN, 5=ENABLE, 6=V+
    # ---------------------------------------------------------------------------------
    u_buf = Part('Amplifier_Operational', 'OPA355NA', ref='U_buf%d' % ch,
                 value='OPA355NA/3K', footprint='Package_TO_SOT_SMD:SOT-23-6')
    bufin += u_buf[3]                     # +IN
    bufout += u_buf[1], u_buf[4]          # OUT tied to -IN: unity-gain follower
    v3v3_a += u_buf[6]                    # V+
    gnd += u_buf[2]                       # V-
    v3v3_a += u_buf[5]                    # ENABLE — tied DIRECTLY to the rail. The TI
    #                                       datasheet states this pin must be driven; it
    #                                       cannot float (handoff 04 "Next phase must" 7).

    c_buf_dec = Part('Device', 'C', ref=c_ref(8), value='100nF', footprint=_FP_C0402)
    c_buf_bulk = Part('Device', 'C', ref=c_ref(9), value='1uF', footprint=_FP_C0603)
    for cap in (c_buf_dec, c_buf_bulk):
        v3v3_a += cap[1]
        cap[2] += gnd

    # ---------------------------------------------------------------------------------
    # U_fda — THS4551IRGTR fully-differential ADC driver, G = 2, single-ended in
    # pins: 1=FB-, 2=IN+, 3=IN-, 4=FB+, 5-8=VS+, 9=VOCM, 10=OUT+, 11=OUT-, 12=PD,
    #       13-16=VS-, 17=EP
    # ---------------------------------------------------------------------------------
    u_fda = Part('Amplifier_Difference', 'THS4551xRGT', ref='U_fda%d' % ch,
                 value='THS4551IRGTR',
                 footprint='Package_DFN_QFN:WQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm')

    for p in (5, 6, 7, 8):                # VS+ (all four must be tied)
        v3v3_a += u_fda[p]
    for p in (13, 14, 15, 16):            # VS- — single-supply design, so VS- = GND
        gnd += u_fda[p]
    gnd += u_fda[17]                      # EP: electrically isolated from the die but TI
    #                                       requires it soldered to a plane, never floated.
    v3v3_a += u_fda[12]                   # PD: active LOW -> tie high for normal operation
    vocm += u_fda[9]                      # VOCM: sensed, driven by adc_dual from U5.CM

    # Gain network = a 2nd-order MULTIPLE-FEEDBACK (MFB) low-pass, not a plain G = 2 divider
    # (architecture rev 3 / WO-1, closing ERC H-1: the rev-2 network was a single real pole,
    #  because two caps on one node behind one resistor are one pole).  Per leg:
    #
    #    bufout  -> R_g1 499 -> MFB_P -> R_mfb_p 499 -> IN+ (2)
    #    VREF_FE -> R_g2 499 -> MFB_N -> R_mfb_n 499 -> IN- (3)
    #    MFB_P -> R_f_p 1.00k -> OUT- (11)          MFB_N -> R_f_n 1.00k -> OUT+ (10)
    #    ONE differential C_mfb 68 pF between MFB_P and MFB_N
    #    C_f 10 pF from each FB pin to the output that feeds it back
    #
    # R_f moving off the FB pin onto the MFB node is the WHOLE change; FB+/FB- now carry only
    # the FB pin and its C_f.  Each leg still feeds back from the OPPOSITE output, which is
    # what makes the feedback negative given the RGT package's crosswise internal FB straps
    # (FB+ pin 4 <-> IN- pin 3, FB- pin 1 <-> IN+ pin 2, SBOS778D Fig. 9-2).
    #
    # C_mfb MUST be one cap between the two MFB nodes, NOT two caps to GND: a cap to real
    # ground on this node couples into the FDA's common-mode loop.
    #
    # DC is unchanged and must not drift: no DC current flows in R_mfb, so the MFB node sits
    # at the summing node's potential and the DC gain is still R_f/R_g = 1.00k/499 = 2.004.
    # +-10 V in -> 2.0 V p-p differential; zero differential out at 0 V in.
    #
    # AC response (synthesised in architecture/net_plan.md, section "Anti-alias filter" --
    # these are the numbers, do NOT recompute them from the component values here):
    #   MFB section:  f0 = 5.93 MHz, Q = 1.012.  C_f is 10 pF + THS4551's 0.6 pF internal per
    #                 side = 10.6 pF effective (SBOS778D Sec. 9.1); the internal 3.3 ohm FB
    #                 trace is in series with each C_f.
    #   output RC:    differential pole 6.35 MHz, common-mode pole 48 MHz (see below).
    #   TOGETHER:     3rd-order Butterworth, -3 dB at 6.1 MHz --
    #                 -0.15 dB @ 4.0 MHz, -1.0 dB @ 5 MHz, -5.25 dB @ 7 MHz, -13.3 dB @
    #                 10 MHz, -25.3 dB @ 16 MHz, -31.1 dB @ 20 MHz.
    #   worst case:   +-5% C0G, +-1% R -> <=0.40 dB @ 4 MHz, >=22.7 dB @ 16 MHz.
    # SPEC F9 (<=0.5 dB to 4.0 MHz) and F10 (>=25 dB above 16 MHz, the 20 MSPS alias edge)
    # are both met.  The 5-10 MHz band is the HOST's problem: SPEC S1 requires a digital
    # low-pass in its 2:1 decimation, or 5-10 MHz folds into the measurement band with no
    # hardware symptom.
    #
    # The FDA's feedback network is now part of the filter (architecture decision 18): any
    # substitute FDA must be unity-gain stable with >=100 MHz GBW, and R_g/R_f/R_mfb/C_mfb
    # must stay tight and the two legs symmetric (risk R-5 -- computed analytically, never
    # simulated; confirm on a network analyser before a second spin).
    r_g1 = Part('Device', 'R', ref=r_ref(5), value='499', footprint=_FP_R0603)
    r_g2 = Part('Device', 'R', ref=r_ref(6), value='499', footprint=_FP_R0603)
    bufout += r_g1[1]
    r_g1[2] += mfb_p                      # signal leg summing node
    vref_fe += r_g2[1]
    r_g2[2] += mfb_n                      # reference leg summing node

    # MFB node -> amplifier input.  These carry no DC current, so they do not shift the
    # operating point; +-0.1% is reused from the R_g line only to keep the legs matched.
    r_mfb_p = Part('Device', 'R', ref=r_ref(11), value='499', footprint=_FP_R0603)
    r_mfb_n = Part('Device', 'R', ref=r_ref(12), value='499', footprint=_FP_R0603)
    mfb_p += r_mfb_p[1]
    r_mfb_p[2] += fda_inp
    fda_inp += u_fda[2]                   # IN+
    mfb_n += r_mfb_n[1]
    r_mfb_n[2] += fda_inn
    fda_inn += u_fda[3]                   # IN-

    c_mfb = Part('Device', 'C', ref=c_ref(11), value='68pF', footprint=_FP_C0603)
    mfb_p += c_mfb[1]                     # ONE differential cap across the two MFB nodes;
    c_mfb[2] += mfb_n                     # never two caps to GND (CM-loop coupling)

    # R_f: MFB node -> the OPPOSITE output.
    r_f_p = Part('Device', 'R', ref=r_ref(7), value='1k', footprint=_FP_R0603)
    r_f_n = Part('Device', 'R', ref=r_ref(8), value='1k', footprint=_FP_R0603)
    mfb_p += r_f_p[1]
    r_f_p[2] += u_fda[11]                 # signal leg (-> IN+) feeds back from OUT-
    mfb_n += r_f_n[1]
    r_f_n[2] += u_fda[10]                 # reference leg (-> IN-) feeds back from OUT+

    # C_f stays ON the FB pins, one per side, to the output it feeds back from.
    c_f_p = Part('Device', 'C', ref=c_ref(3), value='10pF', footprint=_FP_C0603)
    c_f_n = Part('Device', 'C', ref=c_ref(4), value='10pF', footprint=_FP_C0603)
    fda_fbp += c_f_p[1], u_fda[4]         # FB+ (internally IN-) <- C_f <- OUT+
    c_f_p[2] += u_fda[10]
    fda_fbn += c_f_n[1], u_fda[1]         # FB- (internally IN+) <- C_f <- OUT-
    c_f_n[2] += u_fda[11]

    c_fda_dec = Part('Device', 'C', ref=c_ref(10), value='100nF', footprint=_FP_C0402)
    v3v3_a += c_fda_dec[1]
    c_fda_dec[2] += gnd

    # ---------------------------------------------------------------------------------
    # Output RC — the single REAL pole of the 3rd-order Butterworth; the MFB network above
    # supplies the complex pair.  Differential: 2 x R_o 33 ohm working into
    # C_cm + 2*C_diff = 100 + 660 = 760 pF -> 6.35 MHz.  Common mode: 33 ohm x 100 pF ->
    # 48 MHz.  R_o also isolates the FDA from the ADC's switched-capacitor input.
    # Overall (with the MFB): -3 dB at 6.1 MHz, -0.15 dB at 4.0 MHz, -25.3 dB at 16 MHz --
    # 16 MHz, not 15, is the alias edge (20 MSPS, host decimates 2:1 behind SPEC S1's
    # digital low-pass).  Full table in the gain-network comment above.
    # ---------------------------------------------------------------------------------
    r_o_p = Part('Device', 'R', ref=r_ref(9), value='33', footprint=_FP_R0603)
    r_o_n = Part('Device', 'R', ref=r_ref(10), value='33', footprint=_FP_R0603)
    c_diff = Part('Device', 'C', ref=c_ref(5), value='330pF', footprint=_FP_C0603)
    c_cm_p = Part('Device', 'C', ref=c_ref(6), value='100pF', footprint=_FP_C0603)
    c_cm_n = Part('Device', 'C', ref=c_ref(7), value='100pF', footprint=_FP_C0603)

    u_fda[10] += r_o_p[1]                 # OUT+
    r_o_p[2] += adc_in_p
    u_fda[11] += r_o_n[1]                 # OUT-
    r_o_n[2] += adc_in_n

    adc_in_p += c_diff[1]                 # differential pole: 2*33 ohm into 760 pF -> 6.35 MHz
    c_diff[2] += adc_in_n
    adc_in_p += c_cm_p[1]                 # common-mode poles: 33 ohm with 100 pF -> 48 MHz
    c_cm_p[2] += gnd
    adc_in_n += c_cm_n[1]
    c_cm_n[2] += gnd

    # TODO (architecture rev 3 WO-1 item 7, L-1, deliberately NOT done): TI's RGT layout
    # guidance wants one 100 nF per VS+ pin PAIR, i.e. a second cap next to C110/C210 on
    # +3V3_A.  Skipped here because rev 3's sourced ref delta is exactly R111/R112/C111 per
    # channel and C112/C212 is not in the BOM; adequate for a 1.4 mA part.  If a ref is ever
    # allocated, use C112/C212.
