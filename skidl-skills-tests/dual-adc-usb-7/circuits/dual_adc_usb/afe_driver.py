"""AFE Driver — THS4521 fully-differential driver + 4-pole passive LC anti-alias filter.
Block from: architecture/block_diagram.md (block 3+4, "FDA" and "LC anti-alias")
Interface nets: CH<ch>_BUF -> ADC_IN<ch>P / ADC_IN<ch>N, ADC_CM, P3V3A, GND
               (ch="A": CHA_BUF -> ADC_INAP/ADC_INAN;  ch="B": CHB_BUF -> ADC_INBP/ADC_INBN)

Instantiated twice, once per analog channel.  The `ch` argument selects the 1xx (A) or
2xx (B) reference-designator block so refs stay unique across the two instances.

NOTE ON THE PARAMETER NAME `ch`:  the work order specified this parameter as `tag`, but
SKiDL's @SubCircuit decorator *consumes* a `tag=` keyword for its own hierarchy naming
(skidl/node.py Node.__call__ pops "tag" out of kwargs before calling the wrapped
function), so a parameter named `tag` can never be filled by a keyword call.  Renamed to
`ch`; see handoffs/05_blocks/afe_driver.md § Decisions.
"""
from skidl import *


@SubCircuit
def afe_driver(v_buf, adc_inp, adc_inn, adc_cm, p3v3a, gnd, ch):
    """Single-ended -> differential conversion, level shift, and anti-alias filtering.

    One THS4521 fully-differential amplifier takes the ground-referenced, buffered
    single-ended signal on `v_buf` and produces a differential pair centred on the
    common-mode voltage presented on `adc_cm` (the ADS5231's CM output, ~1.5 V).  That
    is both the single-ended->differential conversion and the level shift: the ADS5231
    input window is 1.0-2.0 V per pin (SBAS295A p.8/p.19), and with the architecture's
    2 Vpp differential swing each output pin sits at 1.5 +/-0.5 V, i.e. inside it.

    Each output leg then passes through the 4-pole passive LC anti-alias filter
    100 ohm - 3.3 uH - 680 pF - 5.6 uH - 680 pF (architecture decision 7: -3 dB at
    4.23 MHz, -41.8 dB at 10 MHz, SPEC F8).  Those numbers hold only with the sourced
    L at +/-5 % and C0G at +/-2 % - do not substitute looser parts (design_risks R-4).
    A 22 ohm series isolation resistor and a BAT54S rail clamp finish each leg at the
    ADC pin.

    Args:
        v_buf:   IN  (sensed) - buffered single-ended input from `afe_buffer`
                 (CHA_BUF / CHB_BUF).
        adc_inp: OUT (driven) - ADC positive input (ADC_INAP / ADC_INBP).
        adc_inn: OUT (driven) - ADC negative input (ADC_INAN / ADC_INBN).
        adc_cm:  IN  (sensed) - ADC common-mode reference, drives VOCM.  Bypassed here
                 by C119/C219.  Purely capacitive load: the ADS5231 CM output allows
                 +/-2 mA and no resistive load (net_plan.md).
        p3v3a:   IN  (sensed) - 3.3 V analog rail.  Needs .drive = POWER at top level.
        gnd:     IN  (sensed) - ground.  Needs .drive = POWER at top level.
        ch:      "A" or "B" - selects the refdes block (1xx / 2xx) and net prefix.

    Polarity (net_plan.md, "do not fix this"): the single-ended->differential stage
    inverts, and the inversion is undone by crossing the pair at the ADC.  The FDA
    OUT+ leg therefore feeds `adc_inn` and the OUT- leg feeds `adc_inp`.
    """
    ch = str(ch).upper()
    if ch not in ('A', 'B'):
        raise ValueError("afe_driver: ch must be 'A' or 'B', got %r" % (ch,))

    # Refdes block: channel A -> 1xx (U2), channel B -> 2xx (U3).
    n = {'A': 100, 'B': 200}[ch]
    u_ref = {'A': 'U2', 'B': 'U3'}[ch]

    # ---- Templates (values/footprints verbatim from sourcing/sourced_bom.csv) --------
    r_0402 = Part('Device', 'R', dest=TEMPLATE,
                  footprint='Resistor_SMD:R_0402_1005Metric')
    c_0402 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0402_1005Metric')
    c_0603 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0603_1608Metric')
    l_0805 = Part('Device', 'L', dest=TEMPLATE,
                  footprint='Inductor_SMD:L_0805_2012Metric')

    # ---- U2/U3 — THS4521 fully-differential amplifier -------------------------------
    # Pins are addressed by NUMBER: the symbol's names ('+', '-', 'V_{S+}', '~{PD}')
    # contain regex metacharacters that are unsafe in SKiDL's name lookup.
    # 1 VIN-  2 VOCM  3 VS+  4 VOUT+  5 VOUT-  6 VS-  7 PD  8 VIN+   (TI SBOS defines
    # PD as active low: "PD = logic low puts device into low-power mode; PD = logic
    # high or open for normal operation" - datasheets/THS4521IDR.pdf pin table.)
    VINN, VOCM, VSP, VOUTP, VOUTN, VSN, PD, VINP = 1, 2, 3, 4, 5, 6, 7, 8
    fda = Part('Amplifier_Difference', 'THS4521ID', ref=u_ref, value='THS4521IDR',
               footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')

    p3v3a += fda[VSP], fda[PD]      # single supply; PD tied high = enabled
    gnd += fda[VSN]
    adc_cm += fda[VOCM]             # level shift: output CM follows the ADC's CM output

    # ---- Gain-setting network (net_plan.md CH*_FDA_INN / _INP / CH*_FDAP / _FDAN) ---
    # Differential gain = Rf/Rg = 1.10k/1.00k = 1.100.  The reference leg's Rg returns
    # to GND, which is what makes the ground-referenced input land on adc_cm.
    fda_inn = Net('CH{}_FDA_INN'.format(ch))    # driven leg
    fda_inp = Net('CH{}_FDA_INP'.format(ch))    # reference leg
    fdap = Net('CH{}_FDAP'.format(ch))
    fdan = Net('CH{}_FDAN'.format(ch))

    rg_drv = r_0402(ref='R{}'.format(n + 11), value='1.00k')   # R111 / R211
    rf_drv = r_0402(ref='R{}'.format(n + 12), value='1.10k')   # R112 / R212
    cf_drv = c_0402(ref='C{}'.format(n + 11), value='4.7pF')   # C111 / C211
    rg_ref = r_0402(ref='R{}'.format(n + 13), value='1.00k')   # R113 / R213
    rf_ref = r_0402(ref='R{}'.format(n + 14), value='1.10k')   # R114 / R214
    cf_ref = c_0402(ref='C{}'.format(n + 12), value='4.7pF')   # C112 / C212

    v_buf += rg_drv[1]
    fda_inn += rg_drv[2], rf_drv[1], cf_drv[1], fda[VINN]
    fdap += fda[VOUTP], rf_drv[2], cf_drv[2]

    gnd += rg_ref[1]
    fda_inp += rg_ref[2], rf_ref[1], cf_ref[1], fda[VINP]
    fdan += fda[VOUTN], rf_ref[2], cf_ref[2]

    def _aaf_leg(src, leg, rs_ref, l1_ref, c1_ref, l2_ref, c2_ref, rt_ref, d_ref,
                 adc_net):
        """One 4-pole LC leg: src - 100R - 3.3uH - 680p - 5.6uH - 680p - 22R - adc_net.

        Shunt caps return to GND (the AC common for the differential pair) - they are
        deliberately NOT hung on adc_cm, which tolerates no extra load.
        """
        f1 = Net('CH{}_F1{}'.format(ch, leg))
        f2 = Net('CH{}_F2{}'.format(ch, leg))   # filter node 1
        f3 = Net('CH{}_F3{}'.format(ch, leg))   # filter node 2
        rs = r_0402(ref=rs_ref, value='100')      # AAF source resistor
        l1 = l_0805(ref=l1_ref, value='3.3uH')    # +/-5 %, SRF 60 MHz
        c1 = c_0603(ref=c1_ref, value='680pF')    # C0G +/-2 %
        l2 = l_0805(ref=l2_ref, value='5.6uH')    # +/-5 %, SRF 70 MHz
        c2 = c_0603(ref=c2_ref, value='680pF')    # C0G +/-2 %
        rt = r_0402(ref=rt_ref, value='22')       # ADC series isolation resistor
        # BAT54S is a SERIES pair: 1 = A (anode of D1), 2 = K (cathode of D2),
        # 3 = COM (D1 cathode / D2 anode).  Orientation stated explicitly, not left to
        # a chain: COM on the signal, A to GND, K to the 3.3 V analog rail, so the node
        # is clamped to roughly -Vf .. P3V3A+Vf (design_risks R-10).
        dclamp = Part('Diode', 'BAT54S', ref=d_ref, value='BAT54S',
                      footprint='Package_TO_SOT_SMD:SOT-23')

        src += rs[1]
        f1 += rs[2], l1[1]
        f2 += l1[2], c1[1], l2[1]
        f3 += l2[2], c2[1], rt[1], dclamp[3]
        # Connected pin-side (`pin += net`) rather than `gnd += ...`: an augmented
        # assignment to a closed-over name would make it local to this helper.
        c1[2] += gnd
        c2[2] += gnd
        dclamp[1] += gnd
        dclamp[2] += p3v3a
        adc_net += rt[2]

    # OUT+ leg -> adc_inn and OUT- leg -> adc_inp: the deliberate crossing that undoes
    # the stage's inversion (net_plan.md polarity note).
    _aaf_leg(fdap, 'P',
             'R{}'.format(n + 15), 'L{}'.format(n + 11), 'C{}'.format(n + 13),
             'L{}'.format(n + 12), 'C{}'.format(n + 14), 'R{}'.format(n + 17),
             'D{}'.format(n + 11), adc_inn)
    _aaf_leg(fdan, 'N',
             'R{}'.format(n + 16), 'L{}'.format(n + 13), 'C{}'.format(n + 15),
             'L{}'.format(n + 14), 'C{}'.format(n + 16), 'R{}'.format(n + 18),
             'D{}'.format(n + 12), adc_inp)

    # ---- Supply decoupling and CM bypass --------------------------------------------
    c_dec = c_0402(ref='C{}'.format(n + 17), value='100nF')    # C117 / C217, at VS+
    c_bulk = c_0402(ref='C{}'.format(n + 18), value='1uF')     # C118 / C218, local bulk
    c_cm = c_0402(ref='C{}'.format(n + 19), value='100nF')     # C119 / C219, CM bypass

    p3v3a += c_dec[1], c_bulk[1]
    adc_cm += c_cm[1]
    gnd += c_dec[2], c_bulk[2], c_cm[2]
