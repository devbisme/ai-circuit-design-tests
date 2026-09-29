"""Sample Clock — 20 MHz 3.3 V CMOS oscillator (X1) fanned out to the ADC and the FPGA
Block from: architecture/block_diagram.md
Interface nets: ADC_CLK, ADC_CLK_FPGA, VA_3V3, GND
Net plan: architecture/net_plan.md §1 (OSC_VDD) and §6 (sample_clock).
Parts: sourcing/sourced_bom.md rows X1, R57, R58, C63, C64, FB7, TP9.
"""
from skidl import *

_R_FP = 'Resistor_SMD:R_0402_1005Metric'
_C_FP = 'Capacitor_SMD:C_0402_1005Metric'


@SubCircuit
def sample_clock(adc_clk, adc_clk_fpga, va_3v3, gnd):
    """20 MHz XO with two source-terminated branches: ADC (R57) and FPGA GCLKT_4 (R58).

    Args:
        adc_clk: 20 MHz clock to U12.CLK, driven through R57 (33 Ω). TP9 sits on it.
        adc_clk_fpga: the same edge to U15 pin 35, driven through R58 (33 Ω).
        va_3v3: low-noise 3.3 V analog rail (consumed). It feeds OSC_VDD through FB7.
        gnd: single ground net.
    Assumptions:
        - X1 (SX3M20.000B10F20TNN) pinout is 1 OE, 2 GND, 3 OUT, 4 VDD
          (datasheets/SX3M20.000B10F20TNN_SUMMARY.md). OE is active high and tied to OSC_VDD,
          so the clock always runs.
        - The 4-pin Oscillator:ASE-xxxMHz symbol (EN/GND/OUT/Vdd) replaces the BOM's 2-pin
          Device:Crystal, and matches the Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm footprint.
    """
    osc_vdd = Net('OSC_VDD')        # ferrite-isolated oscillator supply
    osc_vdd.drive = POWER           # fed only through passive FB7
    osc_out = Net('OSC_OUT')

    # --- FB7: VA_3V3 -> OSC_VDD ---
    fb7 = Part('Device', 'FerriteBead', ref='FB7', value='600R@100MHz',
               footprint='Inductor_SMD:L_0805_2012Metric', MPN='BLM21PG601SN1D', LCSC='C41556732')
    va_3v3 & fb7 & osc_vdd

    # --- X1 20 MHz CMOS XO ---
    x1 = Part('Oscillator', 'ASE-xxxMHz', ref='X1', value='20MHz',
              footprint='Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm',
              MPN='SX3M20.000B10F20TNN', LCSC='C5452685')
    x1['Vdd'] += osc_vdd
    x1['EN'] += osc_vdd             # OE high = output always enabled
    x1['GND'] += gnd
    x1['OUT'] += osc_out

    # --- Decoupling at X1 VDD ---
    c63 = Part('Device', 'C', ref='C63', value='100nF', footprint=_C_FP,
               MPN='CL05B104KB54PNC', LCSC='C307331')
    c64 = Part('Device', 'C', ref='C64', value='1uF', footprint=_C_FP,
               MPN='CL05A105KA5NQNC', LCSC='C52923')
    osc_vdd & (c63 | c64) & gnd

    # --- Source terminations (place R57/R58 at X1) ---
    r57 = Part('Device', 'R', ref='R57', value='33', footprint=_R_FP,
               MPN='0402WGF330JTCE', LCSC='C25105')
    r58 = Part('Device', 'R', ref='R58', value='33', footprint=_R_FP,
               MPN='0402WGF330JTCE', LCSC='C25105')
    osc_out & r57 & adc_clk
    osc_out & r58 & adc_clk_fpga

    # --- TP9 on ADC_CLK ---
    tp9 = Part('Connector', 'TestPoint', ref='TP9', value='ADC_CLK',
               footprint='TestPoint:TestPoint_Pad_D1.5mm')
    tp9[1] += adc_clk
