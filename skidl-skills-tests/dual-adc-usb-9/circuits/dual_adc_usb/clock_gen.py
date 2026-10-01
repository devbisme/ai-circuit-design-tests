"""Clock Gen — 40 MHz CMOS XO feeding the ADC directly and the FPGA through a 74LVC1G34 buffer
Block from: architecture/block_diagram.md
Interface nets: ADC_CLK, FPGA_CLK40, +3V3D, GND
"""
from skidl import *

_R = 'Resistor_SMD:R_0402_1005Metric'
_C = 'Capacitor_SMD:C_0402_1005Metric'


@SubCircuit
def clock_gen(adc_clk, fpga_clk40, v3v3d, gnd):
    """Y1 OT322540MJBA4SL 40 MHz XO -> XO_OUT.
    XO_OUT -> R70 33 ohm -> adc_clk (ADS5231 CLK).
    XO_OUT -> U8 74LVC1G34 A; U8 Y -> R71 33 ohm -> fpga_clk40 (GW1NR pin 63).
    Drives adc_clk and fpga_clk40; consumes v3v3d, gnd. Refs Y1, U8, R70, R71, C75, C76.
    Pins connected by number (Y1: 1 EN, 2 GND, 3 OUT, 4 Vdd; U8: 2 A, 3 GND, 4 Y, 5 VCC, 1 NC)."""
    xo_out = Net('XO_OUT')
    fpga_clk_src = Net('FPGA_CLK40_SRC')

    y1 = Part('Oscillator', 'ASE-xxxMHz', ref='Y1', value='40MHz',
              footprint='Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm',
              MPN='OT322540MJBA4SL', LCSC='C2831396')
    y1[1] += v3v3d      # EN (tri-state): high = enabled
    y1[2] += gnd
    y1[3] += xo_out     # OUT
    y1[4] += v3v3d      # Vdd

    u8 = Part('74xGxx', '74LVC1G34', ref='U8', value='SN74LVC1G34DCKR',
              footprint='Package_TO_SOT_SMD:SOT-353_SC-70-5',
              MPN='SN74LVC1G34DCKR', LCSC='C353880')
    u8[1] += NC
    u8[2] += xo_out     # A
    u8[3] += gnd
    u8[4] += fpga_clk_src  # Y
    u8[5] += v3v3d

    r70 = Part('Device', 'R', ref='R70', value='33R', footprint=_R, MPN='0402WGF330JTCE', LCSC='C25105')
    r71 = Part('Device', 'R', ref='R71', value='33R', footprint=_R, MPN='0402WGF330JTCE', LCSC='C25105')
    xo_out & r70 & adc_clk
    fpga_clk_src & r71 & fpga_clk40

    c75 = Part('Device', 'C', ref='C75', value='100nF', footprint=_C, MPN='CL05B104KO5NNNC', LCSC='C1525')
    c76 = Part('Device', 'C', ref='C76', value='100nF', footprint=_C, MPN='CL05B104KO5NNNC', LCSC='C1525')
    c75[1] += v3v3d; c75[2] += gnd   # at Y1 Vdd
    c76[1] += v3v3d; c76[2] += gnd   # at U8 VCC
