"""Power Digital — digital rails +3V3_AON / +3V3 / +1V2 / +1V8 from VBUS
Block from: architecture/block_diagram.md (## Power tree)
Interface nets: VBUS, GND, PWR_EN, +3V3_AON, +3V3, +1V2, +1V8

Cascade (block_diagram.md power tree, TLV62568DBVR_SUMMARY.md Notes):
    VBUS ──> U1 AP2112K-3.3 (always on)      ──> +3V3_AON
    VBUS ──> U2 TLV62569 buck (EN=PWR_EN)+L1 ──> +3V3
    +3V3 ──> U3 TLV62568 buck (EN=PWR_EN)+L2 ──> +1V2
    +3V3 ──> U4 LP5907-1.8   (EN=PWR_EN)     ──> +1V8

Sources for every value/footprint/pin used here:
    sourcing/sourced_bom.md          — MPN, LCSC#, footprint strings (verbatim)
    datasheets/TLV62569DBVR_SUMMARY.md — pinout, FB divider R1=453k / R2=100k -> 3.318V
    datasheets/TLV62568DBVR_SUMMARY.md — pinout, FB divider R1=R2=100k       -> 1.200V
    datasheets/LP5907MFX-1.8_NOPB_SUMMARY.md — pinout, EN default-OFF, 1uF on IN and OUT
    datasheets/FNR3015S2R2MT_SUMMARY.md — custom footprint for L1/L2
    architecture/net_plan.md         — net names, PWR_EN fan-out, test points
"""

from skidl import *


@SubCircuit
def power_digital(vbus, gnd, pwr_en, v3v3_aon, v3v3, v1v2, v1v8):
    """Generate the four digital supply rails for dual_adc_usb.

    Args:
        vbus      (Net): +5V USB VBUS input (sensed only — driven by usb_c_port).
        gnd       (Net): board ground (single GND net, per net_plan.md).
        pwr_en    (Net): active-high enable from FX2LP PA0 (sensed only; this block
                         provides the mandatory 100k pulldown R6, design_risks.md R8).
        v3v3_aon  (Net): +3.3V always-on rail — DRIVEN here by U1.
        v3v3      (Net): +3.3V gated rail     — DRIVEN here by U2 + L1.
        v1v2      (Net): +1.2V FPGA core rail — DRIVEN here by U3 + L2.
        v1v8      (Net): +1.8V PSRAM-bank rail— DRIVEN here by U4.

    Assumptions:
      - GND is the one and only ground net (net_plan.md preamble); no AGND here.
      - Every rail's decoupling *at the load* belongs to the consuming block; this block
        provides only regulator input/output caps and one 10uF + 100nF rail bulk per rail.
      - FB4 (+3V3_DRV ferrite) is NOT in this block — it hangs off +3V3 in adc_pair.
      - No feed-forward cap across the +3V3 FB divider (TI-optional, no 6.8pF part in the
        sourced BOM) — see handoffs/05_blocks/power_digital.md "Carried forward".
    """

    # ---------------------------------------------------------------- templates
    # Values/footprints/MPNs verbatim from sourcing/sourced_bom.md.
    c_100n = Part('Device', 'C', dest=TEMPLATE, value='100nF',
                  footprint='Capacitor_SMD:C_0402_1005Metric')
    c_100n.fields['MPN'] = 'CL05B104KB54PNC'
    c_100n.fields['LCSC'] = 'C307331'

    c_1u = Part('Device', 'C', dest=TEMPLATE, value='1uF',
                footprint='Capacitor_SMD:C_0603_1608Metric')
    c_1u.fields['MPN'] = 'CL10A105KB8NNNC'
    c_1u.fields['LCSC'] = 'C15849'

    c_10u = Part('Device', 'C', dest=TEMPLATE, value='10uF',
                 footprint='Capacitor_SMD:C_0805_2012Metric')
    c_10u.fields['MPN'] = 'CL21A106KOQNNNE'
    c_10u.fields['LCSC'] = 'C1713'

    r_100k = Part('Device', 'R', dest=TEMPLATE, value='100k',
                  footprint='Resistor_SMD:R_0402_1005Metric')
    r_100k.fields['MPN'] = '0402WGF1003TCE'
    r_100k.fields['LCSC'] = 'C25741'

    l_buck = Part('Device', 'L', dest=TEMPLATE, value='2.2uH',
                  footprint='Inductor_SMD_Custom:L_FNR3015S_3.0x3.0mm')
    l_buck.fields['MPN'] = 'FNR3015S2R2MT'
    l_buck.fields['LCSC'] = 'C167747'

    tp = Part('Connector', 'TestPoint', dest=TEMPLATE, value='TP',
              footprint='TestPoint:TestPoint_Pad_1.0x1.0mm')

    # ================================================================= U1: +3V3_AON
    # AP2112K-3.3 always-on LDO, VBUS -> +3V3_AON (feeds FX2LP + EEPROM + PWR LED,
    # the ~65mA pre-enumeration budget, block_diagram.md "Why PWR_EN exists").
    U1 = Part('Regulator_Linear', 'AP2112K-3.3', ref='U1', value='AP2112K-3.3TRG1',
              footprint='Package_TO_SOT_SMD:SOT-23-5')
    U1.fields['MPN'] = 'AP2112K-3.3TRG1'
    U1.fields['LCSC'] = 'C51118'

    U1['VIN'] += vbus
    U1['GND'] += gnd
    U1['EN'] += vbus          # always-on: EN tied to its own input (no gate net exists)
    U1['NC'] += NC            # pin 4, no internal connection
    U1['VOUT'] += v3v3_aon

    C4 = c_1u(ref='C4')       # AP2112 input cap
    C5 = c_1u(ref='C5')       # AP2112 output cap
    C6 = c_10u(ref='C6')      # +3V3_AON rail bulk
    C7 = c_100n(ref='C7')     # +3V3_AON HF decoupling
    vbus += C4[1]
    v3v3_aon += C5[1], C6[1], C7[1]
    gnd += C4[2], C5[2], C6[2], C7[2]

    # ================================================================= U2: +3V3
    # TLV62569DBVR 2A buck, VBUS -> +3V3, EN gated by PWR_EN.
    # Pinout per datasheets/TLV62569DBVR_SUMMARY.md: 1 EN, 2 GND, 3 SW, 4 VIN, 5 FB.
    U2 = Part('Regulator_Switching', 'TLV62569DBV', ref='U2', value='TLV62569DBVR',
              footprint='Package_TO_SOT_SMD:SOT-23-5')
    U2.fields['MPN'] = 'TLV62569DBVR'
    U2.fields['LCSC'] = 'C141836'

    sw_3v3 = Net('SW_3V3')    # switch node, local to this block
    fb_3v3 = Net('FB_3V3')    # feedback node, local to this block

    U2['VIN'] += vbus
    U2['GND'] += gnd
    U2['EN'] += pwr_en
    U2['SW'] += sw_3v3
    U2['FB'] += fb_3v3

    L1 = l_buck(ref='L1')     # +3V3 buck inductor
    sw_3v3 += L1[1]
    v3v3 += L1[2]

    # FB divider: VOUT = 0.6V * (1 + R3/R4) = 0.6 * 5.53 = 3.318V (values closed in
    # handoffs/04_datasheets.md #4 — do not recompute).
    R3 = Part('Device', 'R', ref='R3', value='453k',
              footprint='Resistor_SMD:R_0402_1005Metric')
    R3.fields['MPN'] = '0402WGF4533TCE'
    R4 = r_100k(ref='R4')
    v3v3 += R3[1]
    fb_3v3 += R3[2], R4[1]
    gnd += R4[2]

    C8 = c_10u(ref='C8')      # VIN bulk at U2
    C9 = c_100n(ref='C9')     # VIN HF
    C10 = c_10u(ref='C10')    # +3V3 output bulk (2x10uF for the 2A rail)
    C11 = c_10u(ref='C11')
    C12 = c_100n(ref='C12')   # +3V3 HF
    vbus += C8[1], C9[1]
    v3v3 += C10[1], C11[1], C12[1]
    gnd += C8[2], C9[2], C10[2], C11[2], C12[2]

    # ================================================================= U3: +1V2
    # TLV62568DBVR 1A buck, +3V3 -> +1V2 (FPGA core). Fed from +3V3, NOT VBUS
    # (datasheets/TLV62568DBVR_SUMMARY.md, block_diagram.md power tree).
    U3 = Part('Regulator_Switching', 'TLV62568DBV', ref='U3', value='TLV62568DBVR',
              footprint='Package_TO_SOT_SMD:SOT-23-5')
    U3.fields['MPN'] = 'TLV62568DBVR'
    U3.fields['LCSC'] = 'C163219'

    sw_1v2 = Net('SW_1V2')
    fb_1v2 = Net('FB_1V2')

    U3['VIN'] += v3v3
    U3['GND'] += gnd
    U3['EN'] += pwr_en
    U3['SW'] += sw_1v2
    U3['FB'] += fb_1v2

    L2 = l_buck(ref='L2')     # +1V2 buck inductor
    sw_1v2 += L2[1]
    v1v2 += L2[2]

    # FB divider: VOUT = 0.6V * (1 + R5/R7) = 1.200V exactly (R5 = R7 = 100k).
    R5 = r_100k(ref='R5')
    R7 = r_100k(ref='R7')
    v1v2 += R5[1]
    fb_1v2 += R5[2], R7[1]
    gnd += R7[2]

    C13 = c_10u(ref='C13')    # VIN bulk at U3 (on +3V3)
    C14 = c_100n(ref='C14')
    C15 = c_10u(ref='C15')    # +1V2 output bulk
    C16 = c_100n(ref='C16')
    v3v3 += C13[1], C14[1]
    v1v2 += C15[1], C16[1]
    gnd += C13[2], C14[2], C15[2], C16[2]

    # ================================================================= U4: +1V8
    # LP5907MFX-1.8/NOPB LDO, +3V3 -> +1V8 (GW1NR-9 PSRAM bank VCCIO).
    # EN is driven by PWR_EN (net_plan.md line 79); EN floats OFF via an internal 1M
    # pulldown, so it must never be left unconnected.
    U4 = Part('Regulator_Linear', 'LP5907MFX-1.8', ref='U4', value='LP5907MFX-1.8/NOPB',
              footprint='Package_TO_SOT_SMD:SOT-23-5')
    U4.fields['MPN'] = 'LP5907MFX-1.8/NOPB'
    U4.fields['LCSC'] = 'C92498'

    U4['IN'] += v3v3
    U4['GND'] += gnd
    U4['EN'] += pwr_en
    U4['NC'] += NC            # pin 4, no internal connection
    U4['OUT'] += v1v8

    C17 = c_1u(ref='C17')     # 1uF on IN — datasheet minimum, not optional
    C18 = c_1u(ref='C18')     # 1uF on OUT — datasheet minimum, not optional
    C19 = c_10u(ref='C19')    # +1V8 rail bulk
    C20 = c_100n(ref='C20')   # +1V8 HF
    v3v3 += C17[1]
    v1v8 += C18[1], C19[1], C20[1]
    gnd += C17[2], C18[2], C19[2], C20[2]

    # ================================================================= PWR_EN
    # Mandatory 100k pulldown (design_risks.md R8, net_plan.md line 79): FX2LP PORTA is
    # high-Z after reset, so without this every gated rail could come up uncommanded.
    R6 = r_100k(ref='R6')
    pwr_en += R6[1]
    gnd += R6[2]

    # ================================================================= test points
    # net_plan.md: TP2=+3V3, TP3=+1V2, TP4=+1V8. TP5 is this block's ref for the
    # +3V3_AON probe point (net_plan calls it TP15 — renumbered into this block's range).
    TP2 = tp(ref='TP2', value='+3V3')
    TP3 = tp(ref='TP3', value='+1V2')
    TP4 = tp(ref='TP4', value='+1V8')
    TP5 = tp(ref='TP5', value='+3V3_AON')
    v3v3 += TP2[1]
    v1v2 += TP3[1]
    v1v8 += TP4[1]
    v3v3_aon += TP5[1]
