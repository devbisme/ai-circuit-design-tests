"""Clock Generation — 10.000 MHz MEMS XO + dual fanout buffer for the two ADCs and the FPGA
Block from: architecture/block_diagram.md  (block_id: clock_gen)
Interface nets: +3V3, GND, CLK_ADC1, CLK_ADC2, CLK_FPGA

Implements architecture/net_plan.md "## Clock nets (`clock_gen`)":
    CLK_XO    : Y1 OUT -> U11 1A, U11 2A          (block-internal net)
    CLK_ADC1  : U11 1Y -> R33 33R -> U9 CLK
    CLK_ADC2  : U11 2Y -> R34 33R -> U10 CLK
    CLK_FPGA  : Y1 OUT -> R32 33R -> U12 dedicated clock input

Architecture Decision 8: dedicated SiT1602 10.000 MHz XO + SN74LVC2G34 fanout,
~2.5 ps rms total against the 20 ps jitter bar (architecture/design_risks.md).
"""
from skidl import *


@SubCircuit
def clock_gen(v3v3, gnd, clk_adc1, clk_adc2, clk_fpga, avdd):
    """10 MHz sample-clock source and 1:2 fanout buffer.

    Args:
        v3v3     (Net): +3V3 digital rail, powers Y1 only. INPUT/consumed only.
        avdd     (Net): +3V0A analog rail. Powers the fanout buffer U11 through FB6
                        so the ADC clock swings to AVDD and stays inside the
                        AD9235's CLK absolute maximum (see H2 note below).
        gnd      (Net): Single GND net. INPUT/consumed only — ``.drive = POWER``
                        must be set at the top level.
        clk_adc1 (Net): OUTPUT. Driven by U11 1Y through R33 (33R series). To U9 CLK.
        clk_adc2 (Net): OUTPUT. Driven by U11 2Y through R34 (33R series). To U10 CLK.
        clk_fpga (Net): OUTPUT. Driven straight off the XO through R32 (33R series).
                        To U12's dedicated clock input.

    Phase alignment: CLK_ADC1 and CLK_ADC2 come from the two channels of a single
    SN74LVC2G34 die, so channel-to-channel skew is die-matched (a few hundred ps
    worst case) rather than part-to-part. Both paths use identical 33R series
    terminations. Layout must length-match the R33 and R34 nets to preserve this —
    the schematic can only guarantee the matched *topology*.

    CLK_FPGA is deliberately tapped ahead of the buffer (net_plan.md), so the XO
    output drives three loads: U11 1A, U11 2A and the R32/FPGA branch. This is a
    light CMOS load at 10 MHz; no separate buffer channel was budgeted for it. The
    FPGA clock is therefore NOT phase-matched to the ADC clocks (it leads them by
    the buffer's propagation delay, ~3 ns) — the FPGA re-times the ADC data anyway.

    Y1 verified against its primary datasheet (2026-09-10, after phase 6):
      * Pinout 1=OE, 2=GND, 3=OUT, 4=VDD — SiT1602B datasheet Rev 1.08, Table 2,
        p.2 (datasheets/SiT1602BI-22-33E-10.000000.pdf). The borrowed KiCad symbol
        Oscillator:SiT8008xx-2x-xxE maps the same names to the same numbers, and
        its footprint's pads match the datasheet land pattern exactly (p.10). This
        was the design's one unverified pin table while no datasheet was on disk.
      * Ordering code decoded (p.13): package "2" = 3.2x2.5 mm, supply "33" =
        3.3 V +/-10 %, feature pin "E" = Output Enable.
      * No OE control net exists in net_plan.md, so pin 1 is tied to +3V3 (always
        enabled). The datasheet recommends a pull-up of 10 k or less when pin 1 is
        not driven (p.2, note 1); a direct tie satisfies that. (An earlier note here
        said a floating OE disables the output. It doesn't: pin 1 has an internal
        50-150 k pull-up, which is just weaker than recommended.)
      * Datasheet requires >=0.1 uF from Vdd to GND (p.2, note 2): C71.
    """

    # ---- Templates (sourcing/sourced_bom.md) -------------------------------
    # 33R series/kickback resistor: FRC0402F33R0TS (LCSC C2906868), 0402, +/-1%
    r_33 = Part('Device', 'R', dest=TEMPLATE, value='33',
                footprint='Resistor_SMD:R_0402_1005Metric')
    # 100nF X7R 50V decoupling: CL05B104KB54PNC (LCSC C307331), 0402, Basic tier
    c_100n = Part('Device', 'C', dest=TEMPLATE, value='100nF',
                  footprint='Capacitor_SMD:C_0402_1005Metric')

    # ---- Y1: SiT1602BI-22-33E-10.000000, 10.000 MHz LVCMOS MEMS XO ---------
    # Symbol: SiTime 4-pad PQFN 3.2x2.5mm family; footprint string taken verbatim
    # from sourcing/sourced_bom.md (Oscillator_SMD_SiT_PQFN-4Pin_3.2x2.5mm).
    Y1 = Part('Oscillator', 'SiT8008xx-2x-xxE', ref='Y1',
              value='SiT1602BI-22-33E-10.000000',
              footprint='Oscillator:Oscillator_SMD_SiT_PQFN-4Pin_3.2x2.5mm')

    # ---- U11: SN74LVC2G34DBVR, dual non-inverting buffer, SOT-23-6 ---------
    # 3-unit KiCad symbol; the buffer I/O pins are unnamed, so they are addressed
    # by pin NUMBER: 1=1A, 6=1Y, 3=2A, 4=2Y, 5=VCC, 2=GND (TI datasheet, and
    # datasheets/SN74LVC2G34DBVR_SUMMARY.md).
    U11 = Part('74xGxx', '74LVC2G34', ref='U11', value='SN74LVC2G34DBVR',
               footprint='Package_TO_SOT_SMD:SOT-23-6')

    # ---- Series terminations ----------------------------------------------
    R32 = r_33(ref='R32')   # XO      -> CLK_FPGA
    R33 = r_33(ref='R33')   # U11 1Y  -> CLK_ADC1
    R34 = r_33(ref='R34')   # U11 2Y  -> CLK_ADC2

    # ---- Decoupling (100nF per IC VCC pin, placed at the pin) --------------
    C_DECOUP_Y1 = c_100n(ref='C71')
    C_DECOUP_U11 = c_100n(ref='C72')

    # ---- Power -------------------------------------------------------------
    # ERC-REVIEW FIX H2 (handoffs/06_erc.md): the AD9235's CLK absolute maximum is
    # AVDD + 0.3 V = 3.30 V, but +3V3 is specified at 3.318 V nominal (and ~3.4 V
    # with tolerance), so a buffer powered from +3V3 over-drives both converters'
    # clock inputs continuously. U11 therefore runs from +3V0A, which makes its
    # output swing exactly AVDD — what the AD9235 wants from a CMOS clock anyway.
    #
    # Options considered: (a) power U11 from +3V0A [selected]; (b) retrim the +3V3
    # rail — still lands inside the tolerance overlap, not robust; (c) rely on the
    # 33R series resistors and the ADC's ESD clamp — continuous clamp current, bad
    # practice; (d) raise AVDD to 3.3 V — electrically clean but re-sources U6 and
    # cannot be stock-checked this session (pcbparts MCP unavailable).
    #
    # Cost of (a): the buffer's switching current now sits on the ADC analog rail.
    # FB6 + local decoupling isolate it, and layout must keep the clock return path
    # away from the ADC reference pins (adds to design_risks R12's layout rules).
    #
    # Y1 stays on +3V3 so CLK_FPGA reaches the FPGA's 3.3 V bank at full level; the
    # SN74LVC2G34's inputs are 5.5 V tolerant regardless of its own VCC, so driving
    # a 3.0 V-powered buffer from a 3.3 V oscillator is fine.
    FB6 = Part('Device', 'FerriteBead', ref='FB6', value='600R@100MHz',
               footprint='Inductor_SMD:L_0603_1608Metric')
    clk_vdd = Net('CLKBUF_VDD')
    clk_vdd.drive = POWER       # fed through FB6; a ferrite is not an ERC driver
    avdd += FB6[1]
    clk_vdd += FB6[2]

    Y1['Vdd'] += v3v3
    Y1['GND'] += gnd
    U11[5] += clk_vdd       # VCC — now AVDD-referenced (H2)
    U11[2] += gnd           # GND

    v3v3 & C_DECOUP_Y1 & gnd
    clk_vdd & C_DECOUP_U11 & gnd
    clk_vdd & Part('Device', 'C', ref='C106', value='10uF',
                   footprint='Capacitor_SMD:C_0603_1608Metric') & gnd

    # ---- Y1 output enable: no OE net in net_plan.md -> tie always-on -------
    Y1['OE'] += v3v3

    # ---- CLK_XO: block-internal fanout node --------------------------------
    clk_xo = Net('CLK_XO')
    clk_xo += Y1['OUT'], U11[1], U11[3]     # XO -> 1A, 2A

    # ---- Buffered, phase-aligned ADC clocks --------------------------------
    # Named stubs between each buffer output and its series R (readability only;
    # they are block-internal and appear in the netlist as CLK_ADC*_BUF).
    clk_adc1_buf = Net('CLK_ADC1_BUF')
    clk_adc2_buf = Net('CLK_ADC2_BUF')
    U11[6] & clk_adc1_buf & R33 & clk_adc1  # 1Y -> 33R -> CLK_ADC1
    U11[4] & clk_adc2_buf & R34 & clk_adc2  # 2Y -> 33R -> CLK_ADC2

    # ---- Unbuffered FPGA clock tap -----------------------------------------
    clk_xo & R32 & clk_fpga
