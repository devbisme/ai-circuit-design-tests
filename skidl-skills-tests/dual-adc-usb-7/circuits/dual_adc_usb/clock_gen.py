"""Clock Gen — single 10 MHz CMOS XO fanned out to the ADC and the FPGA.
Block from: architecture/block_diagram.md (block "clock")
Interface nets: CLK10_ADC, CLK10_FPGA, P3V3D, GND
"""
from skidl import *


@SubCircuit
def clock_gen(clk_adc, clk_fpga, p3v3d, gnd):
    """10.000 MHz oscillator with a 33 ohm series termination on each of its two loads.

    ONE oscillator sets the sample rate for BOTH ADC channels: the ADS5231 samples A and
    B off the same CLK pin, so channel-to-channel skew is set by the converter's own
    aperture matching, not by clock distribution.  That is how SPEC F12 (<=5 ns skew) is
    met - do NOT add a second oscillator, a divider, or a buffer between X1 and the two
    loads.  The FPGA gets the same edge so its capture logic is phase-locked to the
    conversion without a PLL relationship to re-derive.

    X1's output drives two destinations from one pin (net CLK10_OSC, block-internal).
    R31 and R32 are 33 ohm series-source terminations placed AT the oscillator, one per
    branch, so each branch is damped independently: they roughly match a CMOS output's
    low tens of ohms to a ~50-70 ohm trace, killing the overshoot/ringing that a fast
    XO edge would otherwise put on a stub-split net (net_plan.md, "33 ohm series at the
    source").

    Args:
        clk_adc:  OUT (driven) - terminated clock to the ADS5231 CLK pin (CLK10_ADC).
        clk_fpga: OUT (driven) - terminated clock to the GW1NR-9 clock-capable input
                  (CLK10_FPGA).
        p3v3d:    IN  (sensed) - 3.3 V digital rail; supplies X1 (VDD 1.62-3.63 V) and
                  holds OE high.  Needs .drive = POWER at top level.
        gnd:      IN  (sensed) - ground.  Needs .drive = POWER at top level.

    X1 pinout (datasheets/SX3M10.000M20F30TNN_SUMMARY.md, generated symbol
    `dual_adc_usb:SX3M10.000M20F30TNN`): 1 OE, 2 GND, 3 OUT, 4 VDD.  OE is tied high
    rather than left floating - a floating tri-state enable is not a defined state and
    the part is freely substitutable, so a substitute without an internal pull-up would
    otherwise come up dead.
    """
    OE, XGND, OUT, VDD = 1, 2, 3, 4
    x1 = Part('dual_adc_usb', 'SX3M10.000M20F30TNN', ref='X1',
              value='SX3M10.000M20F30TNN',
              footprint='Oscillator:Oscillator_SMD_SiT_PQFN-4Pin_3.2x2.5mm')

    p3v3d += x1[VDD], x1[OE]        # supply + output enable asserted
    gnd += x1[XGND]

    # ---- Series terminations (net_plan.md CLK10_OSC / CLK10_ADC / CLK10_FPGA) -------
    r_0402 = Part('Device', 'R', dest=TEMPLATE, value='33',
                  footprint='Resistor_SMD:R_0402_1005Metric')
    r31 = r_0402(ref='R31')         # to the ADC
    r32 = r_0402(ref='R32')         # to the FPGA

    clk_osc = Net('CLK10_OSC')      # block-internal: X1 output before termination
    clk_osc += x1[OUT], r31[1], r32[1]
    clk_adc += r31[2]
    clk_fpga += r32[2]

    # ---- X1 supply decoupling -------------------------------------------------------
    c31 = Part('Device', 'C', ref='C31', value='100nF',
               footprint='Capacitor_SMD:C_0402_1005Metric')
    p3v3d += c31[1]
    c31[2] += gnd
