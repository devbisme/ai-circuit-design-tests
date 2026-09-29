"""Analog Front End — ±10 V compensated attenuator + 4th-order Butterworth AAF + FDA ADC driver
Block from: architecture/block_diagram.md
Interface nets: CHn_BNC, +3V3A_AMP, VREF_OFF, VCM_REF, CHn_AIN_P, CHn_AIN_N, GND
"""
from skidl import *


@SubCircuit
def analog_frontend(ch, bnc_in, avdd, vref_off, vcm_ref, ain_p, ain_n, gnd):
    """One analog input channel: BNC -> /11 compensated attenuator -> clamp -> CMOS
    follower -> two Sallen-Key sections (4th-order Butterworth, f0 ~4.44/4.45 MHz) ->
    THS4521 fully-differential ADC driver (G = 1.1) -> 33 ohm/22 pF kickback filter.

    Protection chain (architecture rev.2, D-r2.1/D-r2.2):
        BNC -> R100||C100 -> ATT -> R102 -> BUFIN{D100, D101, U100.IN+}
    Nothing clamps CHn_BNC itself. D101 is a 0.9 pF unidirectional ESD9L5.0ST5G on
    CHn_BUFIN, behind the 1.00k limiter R102. R102 into the ~8.4 pF clamp node
    (0.9 pF TVS + ~3 pF BAV199 + ~3 pF TPH2501 + ~1.5 pF trace) is a pole at
    18.9 MHz, which costs 0.06 MHz of passband edge: -3 dB at 4.39 MHz nominal /
    4.18 MHz worst case against SPEC F8's 4 MHz, and -30.5 dB at 10 MHz (F9).

    Instantiated twice. `ch` selects the instance and its refdes bank, so CH1 gets
    J2/U100-U103/R100-R112/C100-C116/D100-D101 and CH2 gets J3/U200-U203/R200-R212/
    C200-C216/D200-D201. Topology is identical for both.

    Args:
        ch:       Channel selector -- 'CH1'/'CH2' (or 1/2). Sets the refdes bank
                  (base = 100*n) and the internal net-name prefix.
        bnc_in:   [in]  CHn_BNC -- analog input at the BNC centre contact, +/-10 V.
        avdd:     [in]  +3V3A_AMP -- 3.300 V analog amp rail (driven by the power block;
                  this block only consumes it, so it needs .drive = POWER at top level).
        vref_off: [in]  VREF_OFF -- 1.807 V buffered offset reference. The attenuator's
                  bottom leg returns here, NOT to GND -- this is what level-shifts a
                  bipolar input into the single-supply amp's common-mode range.
        vcm_ref:  [in]  VCM_REF -- 1.650 V buffered common-mode reference. Drives both
                  the FDA's VOCM pin and the Rg leg of its non-inverting input.
        ain_p:    [out] CHn_AIN_P -- differential ADC input, positive leg.
        ain_n:    [out] CHn_AIN_N -- differential ADC input, negative leg.
        gnd:      [in]  GND -- analog/digital common.

    Assumptions (see handoffs/05_blocks/analog_frontend.md):
      - C101 (200 pF) and C116 (10 pF) sit in parallel with R101, so their far ends
        return to VREF_OFF (not GND); that is what makes both divider legs tau-match.
        The 210 pF fixed total is deliberately 10 pF SHORT of 220 pF: ~9.4 pF of
        CHn_BUFIN node capacitance appears across the bottom leg (R102 does not
        isolate it at the 8.8 kHz compensation corner), so 210 pF + C_node is what
        actually lands on 20.0 us. See section 2.
      - D100 (BAV199LT1G) clamps BUFIN to avdd/gnd with the common node (pin 3) on the
        signal. Pin 3's identity is EasyEDA-sourced, not manufacturer-verified.
      - C107-C115 are this block's decoupling/bypass allocation; sourced_bom.md groups
        them only under "decoupling generally".
    """
    # ---- Instance -> refdes bank -------------------------------------------------
    n = int(str(ch).upper().replace('CH', ''))   # 'CH1' -> 1, 'CH2' -> 2
    b = 100 * n                                  # refdes base: 100 / 200
    p = f'CH{n}'                                 # internal net-name prefix

    # ---- Part templates (values/footprints verbatim from sourcing/sourced_bom.md) --
    _r0402 = Part('Device', 'R', dest=TEMPLATE,
                  footprint='Resistor_SMD:R_0402_1005Metric')
    _r0603 = Part('Device', 'R', dest=TEMPLATE,
                  footprint='Resistor_SMD:R_0603_1608Metric')
    _r0805 = Part('Device', 'R', dest=TEMPLATE,
                  footprint='Resistor_SMD:R_0805_2012Metric')
    _c0402 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0402_1005Metric')
    _c0603 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0603_1608Metric')
    _c0805 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0805_2012Metric')
    _opamp = Part('dual_adc_usb', 'TPH2501-TR', dest=TEMPLATE, value='TPH2501-TR',
                  footprint='Package_TO_SOT_SMD:SOT-23-5')

    # ---- Internal nets (net_plan.md "analog_frontend instance nets") --------------
    att    = Net(f'{p}_ATT')       # attenuator tap
    bufin  = Net(f'{p}_BUFIN')     # clamped follower input
    buf    = Net(f'{p}_BUF')       # follower output
    ska_x  = Net(f'{p}_SKA_X')     # Sallen-Key A mid node
    ska_y  = Net(f'{p}_SKA_Y')     # Sallen-Key A amp input
    f1     = Net(f'{p}_F1')        # Sallen-Key A output
    skb_x  = Net(f'{p}_SKB_X')     # Sallen-Key B mid node
    skb_y  = Net(f'{p}_SKB_Y')     # Sallen-Key B amp input
    f2     = Net(f'{p}_F2')        # Sallen-Key B output / FDA input
    fda_in = Net(f'{p}_FDA_IN')    # FDA inverting summing node
    fda_rf = Net(f'{p}_FDA_REF')   # FDA non-inverting summing node
    adc_p  = Net(f'{p}_ADC_P')     # FDA VOUT+
    adc_n  = Net(f'{p}_ADC_N')     # FDA VOUT-

    # =============================================================================
    # 1. BNC input (net_plan: CHn_BNC) -- NO clamp on this node
    #    architecture rev.2 D-r2.1: a 5 V-standoff TVS here conducts 2.2 V past
    #    breakdown at the board's own +/-10 V full scale (F2), takes the +/-50 V DC
    #    fault with both limiters downstream of it (I3), and hangs its Cj straight
    #    on the probe node (I2: C100||C101 = 20.0 pF is the whole budget). The ESD
    #    clamp is in section 3, on CHn_BUFIN, behind R102.
    # =============================================================================
    J = Part('dual_adc_usb', 'KH-BNC50-3511', ref=f'J{n + 1}', value='KH-BNC50-3511',
             footprint='ProjectLocal:BNC_KH-BNC50-3511_Horizontal')

    bnc_in += J[1]                  # centre contact
    gnd += J[2], J[3], J[4]         # shell / footrest ground return

    # =============================================================================
    # 2. /11 compensated attenuator, bottom leg returning to VREF_OFF
    #    909 k || 22 pF  over  90.9 k || 210 pF  -> 1 MOhm || 20 pF, tau = 20.0 us
    #
    #    COMPENSATION INCLUDES C_node (rev.7, erc_report.md rev.2 MEDIUM-1).
    #    The ~9.4 pF on CHn_BUFIN (0.9 pF D101 + ~3 pF D100 + ~3 pF U100 + ~1.5 pF
    #    trace) is NOT isolated by R102: 1.00k is negligible against the divider's
    #    82.6 k source impedance at the 8.8 kHz corner, so C_node sits across the
    #    BOTTOM leg and adds to it. Compensating on the fixed part alone gave
    #        tau_top = 909k x 22p             = 20.00 us
    #        tau_bot = 90.9k x (220p + 9.4p)  = 20.85 us   -> +4.27 %
    #    i.e. a -0.33 dB (-3.7 %) gain shelf from DC to ~1 MHz, missing SPEC F12's
    #    +/-2 % across the whole plausible C_node range (-2.4 % at 6 pF, -5.5 % at
    #    14 pF). The bottom leg therefore carries 210 pF of FIXED capacitance, not
    #    220 pF, so that 210p + C_node = 220p:
    #        tau_bot = 90.9k x (210p + 9.4p)  = 19.94 us   -> -0.27 %, shelf +0.25 %
    #    and the 6-14 pF C_node range maps to +1.7 % .. -1.6 %, inside F12.
    #    210 pF is not an E-series MLCC value, so it is built as 200 pF || 10 pF,
    #    both C0G 0603 on the same two nets (CHn_ATT, VREF_OFF). Splitting it also
    #    makes C116/C216 the natural place to trim if C_node measures off nominal --
    #    SPEC I2 asks for "a trimmable compensation cap" and this is its refdes.
    # =============================================================================
    R_att_t = _r0805(ref=f'R{b + 0}', value='909k')      # [calc] exact E96 - not 910k
    R_att_b = _r0603(ref=f'R{b + 1}', value='90.9k')     # [calc] returns to VREF_OFF
    # C_att_t sits directly on the BNC input node, which SPEC I3 requires to survive
    # +/-50 V DC continuous. 0603/100 V C0G (GCM1885C2A220JA16D), not the 0402/50 V
    # part sourcing first picked -- 50 V there leaves no derating margin. rev.5.
    C_att_t = _c0603(ref=f'C{b + 0}', value='22pF')      # [calc] C0G 100V, || R_att_t
    C_att_b = _c0603(ref=f'C{b + 1}', value='200pF')     # [calc] C0G, || R_att_b
    # Parallel trim leg: 200p + 10p = 210p fixed. Separate refdes so the value can be
    # changed without touching the bulk part. C0G 0603, same two nets as C_att_b.
    C_att_trim = _c0603(ref=f'C{b + 16}', value='10pF')  # [calc] C0G, || C_att_b

    bnc_in += R_att_t[1], C_att_t[1]
    att += R_att_t[2], C_att_t[2], R_att_b[1], C_att_b[1], C_att_trim[1]
    vref_off += R_att_b[2], C_att_b[2], C_att_trim[2]

    # =============================================================================
    # 3. Series clamp resistor + BAV199 rail clamp + ESD TVS (net_plan: CHn_BUFIN)
    #    D100 pin1 = A (to GND), pin2 = C (to avdd), pin3 = C/A common (signal).
    #    D101 (ESD9L5.0ST5G, LCSC C82326, 0.9 pF, SOD-923) is the fast ESD path the
    #    BAV199 is too slow for. It is UNIDIRECTIONAL, so POLARITY IS LOAD-BEARING:
    #    pin 1 = CATHODE -> CHn_BUFIN, pin 2 = ANODE -> GND. Reversed, it forward-
    #    biases across the signal path. BUFIN never leaves 0.734-2.552 V in service
    #    (5 V standoff, never conducts) and the -0.7 V fault case is pinned by D100.
    #    Symbol note: Device:D_Zener (pin 1 = K, pin 2 = A) is used rather than
    #    Device:D_TVS, whose glyph is bidirectional and whose pins are named A1/A2.
    #    Pin numbers are identical either way, so the netlist is unaffected -- but on
    #    a part whose polarity is load-bearing, the honest glyph is what a schematic
    #    reviewer needs. Architecture rev.2 explicitly permits this substitution.
    # =============================================================================
    R_clamp = _r0603(ref=f'R{b + 2}', value='1.00k')     # [calc] 35 uA at +/-50 V
    D_clamp = Part('dual_adc_usb', 'BAV199LT1G', ref=f'D{b + 0}', value='BAV199LT1G',
                   footprint='Package_TO_SOT_SMD:SOT-23')
    D_esd = Part('Device', 'D_Zener', ref=f'D{b + 1}', value='ESD9L5.0ST5G',
                 footprint='Diode_SMD:D_SOD-923')

    att += R_clamp[1]
    bufin += R_clamp[2], D_clamp[3], D_esd[1]   # D_esd pin 1 = CATHODE
    gnd += D_clamp[1]
    gnd += D_esd[2]                             # D_esd pin 2 = ANODE
    avdd += D_clamp[2]

    # =============================================================================
    # 4. U100 unity-gain CMOS follower (net_plan: CHn_BUF)
    # =============================================================================
    U_buf = _opamp(ref=f'U{b + 0}')
    bufin += U_buf['+In']
    buf += U_buf['Out'], U_buf['-In']
    avdd += U_buf['+VS']
    gnd += U_buf['-VS']

    # =============================================================================
    # 5. Sallen-Key section A -- f0 = 4.443 MHz, Q = 0.554 (net_plan: CHn_SKA_*/CHn_F1)
    # =============================================================================
    R_ska_a = _r0402(ref=f'R{b + 3}', value='147R')      # [calc]
    R_ska_b = _r0402(ref=f'R{b + 4}', value='147R')      # [calc]
    C_ska_f = _c0603(ref=f'C{b + 2}', value='270pF')     # [calc] C0G 5%, feedback
    C_ska_g = _c0603(ref=f'C{b + 3}', value='220pF')     # [calc] C0G 5%, to GND
    U_ska = _opamp(ref=f'U{b + 1}')

    buf += R_ska_a[1]
    ska_x += R_ska_a[2], R_ska_b[1], C_ska_f[1]
    ska_y += R_ska_b[2], C_ska_g[1], U_ska['+In']
    gnd += C_ska_g[2]
    f1 += U_ska['Out'], U_ska['-In'], C_ska_f[2]
    avdd += U_ska['+VS']
    gnd += U_ska['-VS']

    # =============================================================================
    # 6. Sallen-Key section B -- f0 = 4.454 MHz, Q = 1.304 (net_plan: CHn_SKB_*/CHn_F2)
    # =============================================================================
    R_skb_a = _r0402(ref=f'R{b + 5}', value='137R')      # [calc]
    R_skb_b = _r0402(ref=f'R{b + 6}', value='137R')      # [calc]
    C_skb_f = _c0603(ref=f'C{b + 4}', value='680pF')     # [calc] C0G 5%, feedback
    C_skb_g = _c0603(ref=f'C{b + 5}', value='100pF')     # [calc] C0G 5%, to GND
    U_skb = _opamp(ref=f'U{b + 2}')

    f1 += R_skb_a[1]
    skb_x += R_skb_a[2], R_skb_b[1], C_skb_f[1]
    skb_y += R_skb_b[2], C_skb_g[1], U_skb['+In']
    gnd += C_skb_g[2]
    f2 += U_skb['Out'], U_skb['-In'], C_skb_f[2]
    avdd += U_skb['+VS']
    gnd += U_skb['-VS']

    # =============================================================================
    # 7. THS4521 fully-differential ADC driver, G = Rf/Rg = 1.10k/1.00k = 1.1
    #    Pins 4 (VOUT+) and 5 (VOUT-) have EMPTY name fields in the KiCad symbol, and
    #    pins 1/8 are named just '-'/'+', so every pin here is addressed BY NUMBER.
    #      1 = VIN-   2 = VOCM   3 = VS+   4 = VOUT+
    #      5 = VOUT-  6 = VS-    7 = PD    8 = VIN+
    # =============================================================================
    U_fda = Part('Amplifier_Difference', 'THS4521ID', ref=f'U{b + 3}', value='THS4521IDR',
                 footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')
    R_rg_n = _r0402(ref=f'R{b + 7}', value='1.00k')      # [calc] Rg, inverting side
    R_rf_p = _r0402(ref=f'R{b + 8}', value='1.10k')      # [calc] Rf, VOUT+ -> VIN-
    R_rg_p = _r0402(ref=f'R{b + 9}', value='1.00k')      # [calc] Rg, VCM_REF -> VIN+
    R_rf_n = _r0402(ref=f'R{b + 10}', value='1.10k')     # [calc] Rf, VOUT- -> VIN+

    f2 += R_rg_n[1]
    fda_in += R_rg_n[2], R_rf_p[1], U_fda[1]            # VIN-
    vcm_ref += R_rg_p[1]
    fda_rf += R_rg_p[2], R_rf_n[1], U_fda[8]            # VIN+
    adc_p += U_fda[4], R_rf_p[2]                        # VOUT+
    adc_n += U_fda[5], R_rf_n[2]                        # VOUT-

    vcm_ref += U_fda[2]                                 # VOCM sets 1.650 V output CM
    avdd += U_fda[3]                                    # VS+
    gnd += U_fda[6]                                     # VS-
    avdd += U_fda[7]                                    # PD active-low: tied high
                                                        # explicitly, not left floating

    # =============================================================================
    # 8. ADC kickback filter -- 33 ohm series + 22 pF differential, tau = 1.45 ns
    # =============================================================================
    R_kb_p = _r0402(ref=f'R{b + 11}', value='33R')       # [calc]
    R_kb_n = _r0402(ref=f'R{b + 12}', value='33R')       # [calc]
    C_kb   = _c0402(ref=f'C{b + 6}', value='22pF')       # [calc] C0G, differential

    adc_p += R_kb_p[1]
    adc_n += R_kb_n[1]
    ain_p += R_kb_p[2], C_kb[1]
    ain_n += R_kb_n[2], C_kb[2]

    # =============================================================================
    # 9. Decoupling / reference bypass (C107-C115 per channel)
    #    sourced_bom.md groups these under the generic 100 nF / 10 uF buckets:
    #    100 nF = CL05B104KB54PNC (0402), 10 uF = CL21A106KAYNNNE (0805).
    # =============================================================================
    C_dec_u0 = _c0402(ref=f'C{b + 7}', value='100nF')    # C_DECOUP_U100
    C_dec_u1 = _c0402(ref=f'C{b + 8}', value='100nF')    # C_DECOUP_U101
    C_dec_u2 = _c0402(ref=f'C{b + 9}', value='100nF')    # C_DECOUP_U102
    C_dec_u3 = _c0402(ref=f'C{b + 10}', value='100nF')   # C_DECOUP_U103
    C_blk_u3 = _c0805(ref=f'C{b + 11}', value='10uF')    # U103 local bulk
    C_vcm    = _c0402(ref=f'C{b + 12}', value='100nF')   # VCM_REF bypass (net_plan)
    C_vref   = _c0402(ref=f'C{b + 13}', value='100nF')   # VREF_OFF bypass
    C_rail_b = _c0805(ref=f'C{b + 14}', value='10uF')    # +3V3A_AMP block bulk
    C_rail_d = _c0402(ref=f'C{b + 15}', value='100nF')   # +3V3A_AMP block entry

    for c in (C_dec_u0, C_dec_u1, C_dec_u2, C_dec_u3, C_blk_u3, C_rail_b, C_rail_d):
        avdd += c[1]
        gnd += c[2]
    vcm_ref += C_vcm[1]
    gnd += C_vcm[2]
    vref_off += C_vref[1]
    gnd += C_vref[2]
