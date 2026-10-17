"""Clock — 10 MHz 3.3 V CMOS XO with 2-output buffer fan-out (ADC clock + FPGA clock)
Block from: architecture/block_diagram.md (connections: architecture/net_plan.md Block 6)
Interface nets: +3V3, ADC_CLK, CLK10_FPGA, GND
"""
from skidl import *

_FP_C0402 = 'Capacitor_SMD:C_0402_1005Metric'
_FP_C0603 = 'Capacitor_SMD:C_0603_1608Metric'
_FP_R0402 = 'Resistor_SMD:R_0402_1005Metric'


@SubCircuit
def clock(v3v3, adc_clk, clk10_fpga, gnd):
    """Y401 10 MHz XO -> U401 SN74LVC2G34 dual buffer -> 33R series -> adc_clk / clk10_fpga.

    Inputs: v3v3 (consumed, filtered by FB401 into local +3V3_CLK), gnd.
    Outputs: adc_clk (to ADS5231 CLK), clk10_fpga (to FPGA GCLK) - both driven here,
    each through its own 33R source-termination resistor (R401 / R402).
    Assumptions: XO OE/EN tied to +3V3_CLK (always enabled). XO RMS jitter is not
    specified by the SX3M datasheet (architecture wanted <= 5 ps) - open item.
    """
    # ---- +3V3 -> FB401 -> +3V3_CLK ----
    vclk = Net('+3V3_CLK')
    vclk.drive = POWER           # ferrite output is the source for Y401/U401 power_in pins
    flg = Part('power', 'PWR_FLAG', ref='#FLG401')
    vclk += flg[1]
    fb = Part('Device', 'FerriteBead', ref='FB401', value='600R',
              footprint='Inductor_SMD:L_0603_1608Metric')
    fb.fields['MPN'] = 'BLM18KG601SN1D'
    fb.fields['LCSC'] = 'C85833'
    v3v3 += fb[1]
    vclk += fb[2]

    for ref, val, mpn, lcsc, fp in (('C401', '100n', 'CL05B104KB54PNC', 'C307331', _FP_C0402),
                                    ('C402', '100n', 'CL05B104KB54PNC', 'C307331', _FP_C0402),
                                    ('C403', '4.7u', 'CL10A475KO8NNNC', 'C19666', _FP_C0603)):
        c = Part('Device', 'C', ref=ref, value=val, footprint=fp)
        c.fields['MPN'] = mpn
        c.fields['LCSC'] = lcsc
        vclk += c[1]
        gnd += c[2]

    # ---- Y401 XO: 1 EN, 2 GND, 3 OUT, 4 Vdd ----
    xo = Part('Oscillator', 'ASE-xxxMHz', ref='Y401', value='10MHz',
              footprint='Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm')
    xo.fields['MPN'] = 'SX3M10.000B10F20TNN'
    xo.fields['LCSC'] = 'C5452682'
    vclk += xo[4], xo[1]
    gnd += xo[2]
    xo_out = Net('XO_OUT')
    xo_out += xo[3]

    # ---- U401 SN74LVC2G34: 1 1A, 2 GND, 3 2A, 4 2Y, 5 VCC, 6 1Y ----
    buf = Part('74xGxx', '74LVC2G34', ref='U401', value='SN74LVC2G34DBVR',
               footprint='Package_TO_SOT_SMD:SOT-23-6')
    buf.fields['MPN'] = 'SN74LVC2G34DBVR'
    buf.fields['LCSC'] = 'C7394039'
    vclk += buf[5]
    gnd += buf[2]
    xo_out += buf[1], buf[3]

    clkb1 = Net('CLKB1')
    clkb2 = Net('CLKB2')
    clkb1 += buf[6]
    clkb2 += buf[4]

    r401 = Part('Device', 'R', ref='R401', value='33', footprint=_FP_R0402)
    r401.fields['MPN'] = '0402WGF330JTCE'
    r401.fields['LCSC'] = 'C25105'
    r402 = Part('Device', 'R', ref='R402', value='33', footprint=_FP_R0402)
    r402.fields['MPN'] = '0402WGF330JTCE'
    r402.fields['LCSC'] = 'C25105'
    clkb1 += r401[1]
    adc_clk += r401[2]
    clkb2 += r402[1]
    clk10_fpga += r402[2]
