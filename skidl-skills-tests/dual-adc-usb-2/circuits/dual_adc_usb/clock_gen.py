"""Clock Generation — 10 MHz Low-Jitter Clock
Block from: architecture/block_diagram.md
Interface nets: V3V3_CLK, GND, CLK_ADC_A, CLK_ADC_B, CLK_10M
"""
from skidl import *


@subcircuit
def clock_gen(v3v3_clk, gnd, clk_adc_a, clk_adc_b, clk_10m):
    """10 MHz low-jitter clock generation for the dual-ADC sample clock (decision A9 / risk R-01).

    X1 is a dedicated 10.000 MHz XO (<=5 ps RMS jitter, 12 kHz-20 MHz; +/-25 ppm) that sets
    the design's ENOB budget. Its output is series-terminated (R10, 33 ohm) and fanned out
    to two independent 74LVC1G34 non-inverting buffers (U16, U17) so each ADC channel gets
    its own dedicated clock driver -- the two ADCs never share a buffer's output pin, and
    the sample clock is never generated in or routed through FPGA fabric (binding
    constraint). The same post-R10 node is also tapped directly to CLK_10M, which is only a
    reference fed to the FPGA's global clock input (GBIN) -- NOT a sample clock for the
    ADCs -- so this does not violate the "never through FPGA fabric" constraint.

    Args:
        v3v3_clk: 3.3 V supply for clock_gen (from V3V3_A via ferrite bead FB6, per net_plan.md)
        clk_adc_a: 10 MHz CMOS clock to ADC channel A (U14 CLK), buffered by U16, series-terminated by R11
        clk_adc_b: 10 MHz CMOS clock to ADC channel B (U15 CLK), buffered by U17, series-terminated by R12
        clk_10m: 10 MHz CMOS clock reference fanned out to the FPGA (U9 GBIN), tapped from the
            XO side of R10 (not buffered/re-driven -- matches net_plan.md's single-resistor topology)
        gnd: Ground reference
    """

    # --- Master clock source: 10 MHz low-jitter XO (X1) ---
    # ASEM1-10.000MHZ-LC-T, 3225 4-pad CMOS XO. +/-25 ppm, <=5 ps RMS jitter (12 kHz-20 MHz).
    # This is the single highest-risk part in the design's ENOB budget (architecture R-01).
    x1 = Part(
        "Oscillator",
        "ASE-xxxMHz",
        ref="X1",
        value="ASEM1-10.000MHZ-LC-T",
        footprint="Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm",
    )

    # EN (pin 1) must be tied explicitly high (always-on) -- do not rely on an assumed
    # internal pull-up; a floating control pin is an ERC risk regardless of family default.
    x1["EN"] += v3v3_clk
    x1["Vdd"] += v3v3_clk
    x1["GND"] += gnd

    # Internal net: raw XO output, upstream of the series termination resistor R10.
    xo_out = Net("clk_xo_raw")
    x1["OUT"] += xo_out

    # --- Series termination + fan-out node (R10) ---
    # R10 (33 ohm) terminates the XO output. The node downstream of R10 fans out three ways:
    #   1) U16 IN  -> dedicated buffer/driver for ADC channel A
    #   2) U17 IN  -> dedicated buffer/driver for ADC channel B
    #   3) CLK_10M -> direct reference tap to the FPGA's GBIN pin (net_plan.md line 56:
    #      "X1 OUT -> R 33 ohm -> fan to U16 IN, U17 IN, and (via R 33 ohm) CLK_10M" -- the
    #      single R10 termination is shared by the whole fan-out node, consistent with the
    #      3-resistor BOM allocation (R10-R12) for this block: R10=XO out, R11=ADC A leg,
    #      R12=ADC B leg. CLK_10M is NOT buffered/re-driven -- it is a reference only, and
    #      the FPGA never generates or re-drives the ADC sample clock (binding constraint).
    r10 = Part(
        "Device",
        "R",
        ref="R10",
        value="33",
        footprint="Resistor_SMD:R_0402_1005Metric",
    )
    r10[1] += xo_out

    clk_fanout = Net("clk_10m_xo")
    r10[2] += clk_fanout

    # CLK_10M reference tap to FPGA GBIN -- direct connection to the terminated fan-out node.
    clk_fanout += clk_10m

    # --- ADC channel A clock buffer (U16) ---
    # 74LVC1G34, SOT-23-5, single non-inverting buffer -- gives ADC channel A its own
    # dedicated clock driver, isolated from channel B's buffer.
    u16 = Part(
        "74xGxx",
        "74LVC1G34",
        ref="U16",
        value="74LVC1G34GW,125",
        footprint="Package_TO_SOT_SMD:SOT-23-5",
    )
    u16[2] += clk_fanout  # Pin 2 = A (input); symbol reports name generically as "~"
    u16["VCC"] += v3v3_clk
    u16["GND"] += gnd
    u16["NC"] += NC  # Pin 1: no internal bond in this single-gate SOT-23-5 package

    u16_out = Net("clk_adc_a_pre")
    u16[4] += u16_out  # Pin 4 = Y (output); symbol reports name generically as "~"

    # R11 (33 ohm) series termination between U16 output and ADC channel A's CLK pin.
    r11 = Part(
        "Device",
        "R",
        ref="R11",
        value="33",
        footprint="Resistor_SMD:R_0402_1005Metric",
    )
    r11[1] += u16_out
    r11[2] += clk_adc_a

    # --- ADC channel B clock buffer (U17) ---
    # 74LVC1G34, SOT-23-5, single non-inverting buffer -- gives ADC channel B its own
    # dedicated clock driver, isolated from channel A's buffer.
    u17 = Part(
        "74xGxx",
        "74LVC1G34",
        ref="U17",
        value="74LVC1G34GW,125",
        footprint="Package_TO_SOT_SMD:SOT-23-5",
    )
    u17[2] += clk_fanout  # Pin 2 = A (input); symbol reports name generically as "~"
    u17["VCC"] += v3v3_clk
    u17["GND"] += gnd
    u17["NC"] += NC  # Pin 1: no internal bond in this single-gate SOT-23-5 package

    u17_out = Net("clk_adc_b_pre")
    u17[4] += u17_out  # Pin 4 = Y (output); symbol reports name generically as "~"

    # R12 (33 ohm) series termination between U17 output and ADC channel B's CLK pin.
    # NOTE: route CLK_ADC_A and CLK_ADC_B matched to +/-2 mm (net_plan.md constraint,
    # layout-phase concern -- flagged here for the assembler/layout stage).
    r12 = Part(
        "Device",
        "R",
        ref="R12",
        value="33",
        footprint="Resistor_SMD:R_0402_1005Metric",
    )
    r12[1] += u17_out
    r12[2] += clk_adc_b

    # --- Decoupling (V3V3_CLK rail) ---
    # Sourced BOM allocates exactly 3 caps for this block's 3 ICs (X1, U16, U17): C22, C23
    # (100 nF each) and C24 (1 uF bulk). Per the datasheet summary notes, C22/C23 form one
    # shared 100 nF bypass group across X1/U16/U17 (all on the same V3V3_CLK rail), with C24
    # as the shared bulk cap -- there was not a dedicated 100 nF + 10 uF pair per IC in the
    # sourced BOM, so C22/C23/C24 are connected across V3V3_CLK/GND per the sourced part
    # count rather than duplicated per IC (see handoff Decisions).
    c22 = Part(
        "Device",
        "C",
        ref="C22",
        value="100nF",
        footprint="Capacitor_SMD:C_0402_1005Metric",
    )
    c22[1] += v3v3_clk
    c22[2] += gnd

    c23 = Part(
        "Device",
        "C",
        ref="C23",
        value="100nF",
        footprint="Capacitor_SMD:C_0402_1005Metric",
    )
    c23[1] += v3v3_clk
    c23[2] += gnd

    c24 = Part(
        "Device",
        "C",
        ref="C24",
        value="1uF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    c24[1] += v3v3_clk
    c24[2] += gnd

