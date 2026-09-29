"""Clock — 40 MHz CMOS XO with two series-terminated fan-out branches
Block from: architecture/block_diagram.md (clock)
Interface nets: ADC_CLK, FPGA_CLK, V3V3A, GND
"""
from skidl import *


@SubCircuit
def clock(adc_clk, fpga_clk, v3v3a, gnd):
    """X1 SX3M40.000B10F20TNN 40 MHz 3.3 V CMOS XO (3225).

    Supply: v3v3a -> FB2 600R bead -> local XO_VDD, decoupled C31 0.1u + C32 1u.
    X1 pin 1 (Tri-State/OE) tied to XO_VDD = output always enabled.
    Output XO_OUT fans out through R16 33R -> adc_clk (ADS5231 CLK) and
    R17 33R -> fpga_clk (GW1NR GCLKT_4). The ADC clock never passes through the FPGA.
    Drives adc_clk and fpga_clk (through series R); consumes v3v3a, gnd.
    """
    xo_vdd = Net('XO_VDD')
    xo_vdd.drive = POWER        # powered from v3v3a through FB2 (passive)
    xo_out = Net('XO_OUT')

    X1 = Part('dual_adc_usb', 'SX3M40.000B10F20TNN', ref='X1', value='SX3M40.000B10F20TNN',
              footprint='Oscillator:Oscillator_SMD_SeikoEpson_SG8002CE-4Pin_3.2x2.5mm')
    X1[1] += xo_vdd             # Tri-State / OE: high = enabled
    X1[2] += gnd                # GND
    X1[3] += xo_out             # Output
    X1[4] += xo_vdd             # Vdd

    FB2 = Part('Device', 'FerriteBead', ref='FB2', value='600R',
               footprint='Inductor_SMD:L_0603_1608Metric')
    FB2[1] += v3v3a
    FB2[2] += xo_vdd

    xo_vdd & Part('Device', 'C', ref='C31', value='100nF',
                  footprint='Capacitor_SMD:C_0402_1005Metric') & gnd
    xo_vdd & Part('Device', 'C', ref='C32', value='1uF',
                  footprint='Capacitor_SMD:C_0402_1005Metric') & gnd

    # Series source termination, one resistor per load (place R16 at X1, ADC_CLK <= 15 mm)
    xo_out & Part('Device', 'R', ref='R16', value='33',
                  footprint='Resistor_SMD:R_0603_1608Metric') & adc_clk
    xo_out & Part('Device', 'R', ref='R17', value='33',
                  footprint='Resistor_SMD:R_0603_1608Metric') & fpga_clk
