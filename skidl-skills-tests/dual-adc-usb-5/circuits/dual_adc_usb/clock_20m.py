"""Clock 20M — low-jitter 20.000 MHz sample clock for the ADC and the FPGA
Block from: architecture/block_diagram.md
Interface nets: ADC_CLK, FPGA_CLK, +3V3_A, GND

Datasheet notes applied (handoffs/04_datasheets.md item 5, OT252020MJBA4SL_SUMMARY.md):
  * X1 = OT252020MJBA4SL (LCSC C669067), NOT the sourced SX3M20.000B10F20TNN — the latter
    publishes no jitter spec; this one specifies 0.7 ps RMS [12kHz-20MHz], 7x under the 5 ps
    budget architecture risk R-4 sets.
  * Pin map: 1 = Tri-state/OE (high or floating = enabled), 2 = GND, 3 = OUT, 4 = VDD.
    Pin 1 is tied high — to the post-ferrite XO supply node, which is `+3V3_A` behind FB4,
    so the enable pin sits at exactly the part's own VDD potential and no OE current
    bypasses the bead. Never left floating (summary's explicit recommendation).
  * FB4 isolates the XO's supply from the rest of `+3V3_A` (net_plan: "X1.VCC via FB4").

One oscillator, two loads (net_plan clock table): X1.OUT fans out through R_s1 (33 ohm) to
`ADC_CLK` and R_s2 (33 ohm) to `FPGA_CLK`. The series resistors are the whole point of the
topology — they damp the two stubs so the ADC's clock edge is not corrupted by the FPGA
stub's reflection, and they must stay one per branch at the oscillator end. `ADC_CLK` is
never sourced from an FPGA output (architecture F14).

ERC note for the assembler: because the XO output is isolated by R_s1/R_s2, `ADC_CLK` and
`FPGA_CLK` see only passive + input pins, so a "no driving pin"/insufficient-drive warning
on those two nets is expected and is not an error.
"""
from skidl import *


@SubCircuit
def clock_20m(adc_clk, fpga_clk, v3v3_a, gnd):
    """20.000 MHz low-jitter XO driving the ADC sample clock and the FPGA reference clock.

    Args:
        adc_clk:  Net — 20 MHz to U5 (ADS5231) CLK, through R_s1. DRIVEN by this block
                  (through a 33 ohm series resistor — passive at the net boundary).
        fpga_clk: Net — 20 MHz to U6 GCLK pin, through R_s2. DRIVEN by this block
                  (same caveat).
        v3v3_a:   Net — +3V3_A analog rail. CONSUMED only (needs .drive = POWER at the top
                  level).
        gnd:      Net — GND (single ground net, per net_plan ground policy).

    Internal nets: XO_VDD (post-ferrite XO supply), XO_OUT (oscillator output node).
    """

    # ------------------------------------------------------------------ parts
    X1 = Part('dual_adc_usb', 'OT252020MJBA4SL', ref='X1', value='OT252020MJBA4SL',
              footprint='Oscillator:Oscillator_SMD_Kyocera_KC2520Z-4Pin_2.5x2.0mm')

    FB4 = Part('Device', 'FerriteBead', ref='FB4', value='PBY160808T-601Y-N',
               footprint='Inductor_SMD:L_0603_1608Metric')

    R_term = Part('Device', 'R', dest=TEMPLATE, value='33',
                  footprint='Resistor_SMD:R_0603_1608Metric')
    R_s1 = R_term(ref='R_s1')      # series damping into the ADC clock stub
    R_s2 = R_term(ref='R_s2')      # series damping into the FPGA clock stub

    C_d = Part('Device', 'C', dest=TEMPLATE, value='100nF',
               footprint='Capacitor_SMD:C_0402_1005Metric')
    C56, C57 = C_d(2, ref=['C56', 'C57'])   # XO decoupling, both at pin 4

    # --------------------------------------------------------- internal nets
    xo_vdd = Net('XO_VDD')
    xo_out = Net('XO_OUT')

    # --------------------------------------------------------------- supply
    v3v3_a += FB4[1]
    xo_vdd += FB4[2], X1[4], C56[1], C57[1]     # pin 4 = VDD
    gnd += C56[2], C57[2], X1[2]                # pin 2 = GND
    xo_vdd += X1[1]                             # pin 1 = Tri-state/OE, tied high = enabled

    # ---------------------------------------------------------- clock fan-out
    xo_out += X1[3], R_s1[1], R_s2[1]           # pin 3 = OUT
    adc_clk += R_s1[2]
    fpga_clk += R_s2[2]
