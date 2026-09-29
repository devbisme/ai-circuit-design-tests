"""FPGA — iCE40HX4K-TQ144. Captures both ADC buses, decimates, triggers,
runs the SRAM burst controller and drains the FT2232H FIFO.
Block from: architecture/block_diagram.md
Interface nets: v3v3_d, v1v2_core, gnd, + every bus on the board
"""
from skidl import *


@subcircuit
def fpga_ice40(v3v3_d, v1v2_core, gnd,
               adc_data_a, adc_data_b, adc_of_a, adc_of_b,
               adc_shdn, adc_oe_bar, xo_clk_fpga,
               sram_addr, sram_data, sram_ce_bar, sram_oe_bar, sram_we_bar,
               fifo_data, fifo_rxf_bar, fifo_txe_bar, fifo_rd_bar,
               fifo_wr_bar, fifo_oe_bar, ft_clk60,
               cfg_sck, cfg_mosi, cfg_miso, cfg_cs_bar,
               fpga_creset_bar, fpga_cdone, mode_strap,
               probe_comp_drv, ext_trig, led_status, led_activity):
    """iCE40HX4K in TQFP-144: the only active logic on the board.

    Chosen because the ENTIRE toolchain is open source (Yosys / nextpnr /
    icestorm). That was a binding constraint from the requirements interview,
    not a preference, and it is what rules out the larger vendor-locked
    families that would otherwise be the obvious pick for a 92-signal design.

    PIN ASSIGNMENT IS PART OF THE ELECTRICAL DESIGN HERE, NOT A LAYOUT
    DETAIL — two placements are load-bearing:

    1. **`xo_clk_fpga` on GBIN7 (pin 20), in the SAME BANK as all 26 ADC
       input signals (bank 3).** The ADC bus is captured in PIO input
       registers on this clock's FALLING edge (net_plan.md §1.4.1). Putting
       clock and data in one bank keeps them inside the 290 ps t_SKEW_IO
       figure the timing budget uses; splitting them across banks would add
       an unbudgeted term to a margin that has already been shown to fail on
       the rising edge.

       Capture timing, restated so the pin choice is traceable
       [VERIFIED-PDF, LTC2292 p.6 and the iCE40 I/O parameters]:
         ADC t_D = 1.4 ns min / 5.4 ns max  ->  data valid over [5.4, 26.4] ns
         iCE40 PIO input register: t_SU = -0.43 ns, t_H = 2.38 ns,
                                   t_SKEW_IO = 290 ps  (global buffer, NO PLL)
         Rising edge at 25.0 ns: hold = 1.4 ns, and t_H alone is 2.38 ns.
                                 Net margin -1.77 ns. IMPOSSIBLE, not tight.
         Falling edge at 12.5 ns: setup 7.1 ns / hold 13.9 ns
                                 -> net +6.74 ns setup, +10.73 ns hold.
       Worst case over a 45/55 % XO duty cycle is still +5.49 / +11.98 ns.
       **Do not "improve" this by moving to the rising edge or adding a PLL.**
       The PLL would cost 4.16 ns of t_SU_PLL and buy nothing.

    2. **`ft_clk60` on GBIN0 (pin 129).** The FT2232H's synchronous 245 FIFO
       is entirely clocked by ACBUS5; every FIFO signal is synchronous to it,
       so it needs a global buffer, not an ordinary I/O.

    The two clock domains — 40 MHz capture/SRAM and 60 MHz FIFO — are
    genuinely asynchronous. The gateware must cross between them properly
    (async FIFO with Gray-coded pointers); this block only guarantees that
    both clocks arrive on global networks so the crossing is well defined.

    ALL FOUR I/O BANKS RUN AT VCCIO = 3.3 V, and VCC_SPI is 3.3 V to match the
    W25Q32JV — no mixed-voltage bank and no level translation anywhere.

    DESIGNATOR-RANGE CORRECTION. pipeline_state.json assigns this block
    "C90-C119", but `afe_channel` already occupies C101-C115 (channel A) and
    C201-C215 (channel B) from net_plan.md §3.5. The ranges overlap, and a
    collision would either be silently renamed at netlist time or land two
    different parts on one designator. This block therefore uses **C90-C99 and
    C150-C169**, which are unused across the whole design. Flagged rather than
    quietly resolved.

    Args:
        v3v3_d: 3.30 V — VCCIO_0/1/2/3, VCC_SPI, VPP_2V5, VPP_FAST.
        v1v2_core: 1.20 V core supply (VCC x4), and the PLL rails behind R50.
        gnd: Ground, including both PLL grounds.
        adc_data_a, adc_data_b: Bus(12) each, captured on the falling edge.
        adc_of_a, adc_of_b: ADC over-range flags, captured with the data.
        adc_shdn, adc_oe_bar: Static ADC control. Both have 10 k pull-downs in
            `adc_dual`, so the ADC runs correctly while this device is
            unconfigured and its I/O are tri-stated.
        xo_clk_fpga: 40 MHz from `clock_40m` -> GBIN7. System clock AND ADC
            capture clock. Never synthesised here (SPEC Q7).
        sram_addr: Bus(21), sram_data: Bus(16), plus CE#/OE#/WE#.
        fifo_data: Bus(8) and the five sync-245 control lines.
        ft_clk60: 60 MHz FIFO clock from the FT2232H -> GBIN0.
        cfg_sck, cfg_mosi, cfg_miso, cfg_cs_bar: SPI config bus on the
            dedicated SCK/SS/SDO/SDI pins, reusable as user I/O after CDONE.
        fpga_creset_bar: CRESET_B with a 10 k pull-up here.
        fpga_cdone: CDONE with a 10 k pull-up and an indicator LED here.
        mode_strap: Boot-mode strap from JP1, 10 k pull-up here so an unfitted
            jumper defaults to self-boot.
        probe_comp_drv, ext_trig, led_status, led_activity: Front-panel I/O.
    """

    u10 = Part("FPGA_Lattice", "ICE40HX4K-TQ144",
               ref="U10", value="ICE40HX4K-TQ144",
               footprint="Package_QFP:TQFP-144_20x20mm_P0.5mm")

    # ==================================================================
    # Supplies
    # ==================================================================
    u10["GND"] += gnd                 # 5, 13, 14, 59, 69, 86, 103, 132, 140
    u10["VCC"] += v1v2_core           # 27, 40, 92, 111 — 1.2 V core
    u10["VCCIO_0"] += v3v3_d          # 123, 131
    u10["VCCIO_1"] += v3v3_d          # 89, 100
    u10["VCCIO_2"] += v3v3_d          # 46, 57
    u10["VCCIO_3"] += v3v3_d          # 6, 30
    u10["VCC_SPI"] += v3v3_d          # 72 — matches the W25Q32JV's 3.3 V
    # VPP_2V5 accepts 2.30-3.47 V, so 3.3 V is inside spec; VPP_FAST is the
    # NVCM/configuration programming rail and takes the same 3.3 V.
    u10["VPP_2V5"] += v3v3_d          # 108
    u10["VPP_FAST"] += v3v3_d         # 109

    # PLL rails. The PLL is UNUSED in this design — the capture clock is
    # deliberately not PLL-derived (§1.4.1) — but Lattice requires VCCPLL to
    # be powered and filtered regardless, and an unpowered PLL rail is a
    # documented cause of configuration failures.
    v_pll = Net("fpgaVccPll")
    v_pll.drive = POWER        # supply rail behind R50
    r50 = Part("Device", "R", ref="R50", value="10R",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r50[1] += v1v2_core
    r50[2] += v_pll
    u10["VCCPLL0"] += v_pll           # 54
    u10["VCCPLL1"] += v_pll           # 126
    u10["GNDPLL0"] += gnd             # 53
    u10["GNDPLL1"] += gnd             # 127

    c90 = Part("Device", "C", ref="C90", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c90[1] += v_pll
    c90[2] += gnd
    c91 = Part("Device", "C", ref="C91", value="10uF",
               footprint="Capacitor_SMD:C_0805_2012Metric")
    c91[1] += v_pll
    c91[2] += gnd

    # 100 nF at each of the four VCC (core) pins, plus two 10 uF reservoirs.
    # An HX4K toggling 92 I/O plus fabric draws its core current in 40 MHz
    # bursts; one shared bulk cap does not substitute for per-pin ceramics.
    for ref in ("C92", "C93", "C94", "C95"):
        c = Part("Device", "C", ref=ref, value="100nF",
                 footprint="Capacitor_SMD:C_0402_1005Metric")
        c[1] += v1v2_core
        c[2] += gnd
    for ref in ("C96", "C97"):
        c = Part("Device", "C", ref=ref, value="10uF",
                 footprint="Capacitor_SMD:C_0805_2012Metric")
        c[1] += v1v2_core
        c[2] += gnd

    # 100 nF at each of the eight VCCIO pins + one 10 uF per bank.
    for ref in ("C98", "C99", "C150", "C151", "C152", "C153", "C154", "C155"):
        c = Part("Device", "C", ref=ref, value="100nF",
                 footprint="Capacitor_SMD:C_0402_1005Metric")
        c[1] += v3v3_d
        c[2] += gnd
    for ref in ("C156", "C157", "C158", "C159"):
        c = Part("Device", "C", ref=ref, value="10uF",
                 footprint="Capacitor_SMD:C_0805_2012Metric")
        c[1] += v3v3_d
        c[2] += gnd

    # VCC_SPI, VPP_2V5, VPP_FAST each get their own 100 nF.
    for ref in ("C160", "C161", "C162"):
        c = Part("Device", "C", ref=ref, value="100nF",
                 footprint="Capacitor_SMD:C_0402_1005Metric")
        c[1] += v3v3_d
        c[2] += gnd

    # ==================================================================
    # BANK 3 (IOL, 28 I/O) — the entire ADC interface plus its capture clock.
    # Keeping all 26 data/flag signals and the clock in one bank is what makes
    # the 290 ps skew figure in the timing budget applicable. See docstring.
    # ==================================================================
    u10[20] += xo_clk_fpga            # IOL_13B_GBIN7 — falling-edge capture

    adc_a_pins = (1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 15, 16)
    for i, pin in enumerate(adc_a_pins):
        u10[pin] += adc_data_a[i]

    adc_b_pins = (17, 18, 19, 22, 23, 24, 25, 26, 28, 29, 31, 32)
    for i, pin in enumerate(adc_b_pins):
        u10[pin] += adc_data_b[i]

    u10[33] += adc_of_a               # IOL_25A
    u10[34] += adc_of_b               # IOL_25B

    # ==================================================================
    # BANK 1 (IOR, 29 I/O) — SRAM address bus and the low half of the data
    # bus. The SRAM is the widest interface on the board (40 signals) and it
    # spans banks 1 and 0, which is acceptable: it is an ASYNCHRONOUS SRAM
    # driven by a state machine that already allows a full 25 ns bus slot, so
    # inter-bank skew is irrelevant here in a way it is not for the ADC.
    # GBIN2 (94) and GBIN3 (93) are left free.
    # ==================================================================
    addr_pins = (73, 74, 75, 76, 78, 79, 80, 81, 82, 83, 84,
                 85, 87, 88, 90, 91, 95, 96, 97, 98, 99)
    for i, pin in enumerate(addr_pins):
        u10[pin] += sram_addr[i]

    data_lo_pins = (101, 102, 104, 105, 106, 107)
    for i, pin in enumerate(data_lo_pins):
        u10[pin] += sram_data[i]

    # ==================================================================
    # BANK 0 (IOT, 27 I/O) — SRAM data high half + control, and the whole
    # FT2232H FIFO data path with its 60 MHz clock on GBIN0.
    # ==================================================================
    u10[129] += ft_clk60              # IOT_198_GBIN0

    data_hi_pins = (110, 112, 113, 114, 115, 116, 117, 118, 119, 120)
    for i, pin in enumerate(data_hi_pins):
        u10[pin] += sram_data[6 + i]

    u10[121] += sram_ce_bar
    u10[122] += sram_oe_bar
    u10[124] += sram_we_bar

    fifo_pins = (125, 130, 134, 135, 136, 137, 138, 139)
    for i, pin in enumerate(fifo_pins):
        u10[pin] += fifo_data[i]

    u10[141] += fifo_rxf_bar
    u10[142] += fifo_txe_bar
    u10[143] += fifo_rd_bar
    u10[144] += fifo_wr_bar

    # ==================================================================
    # BANK 2 (IOB, 23 I/O) — configuration SPI on its dedicated pins, static
    # ADC control, and the front-panel signals.
    # ==================================================================
    # Dedicated SPI-config pins. Direction matters: in master mode the FPGA
    # drives SDO into the flash's DI, and reads the flash's DO on SDI.
    u10[70] += cfg_sck                # IOB_107_SCK
    u10[71] += cfg_cs_bar             # IOB_108_SS
    u10[67] += cfg_mosi               # IOB_105_SDO -> flash DI
    u10[68] += cfg_miso               # IOB_106_SDI <- flash DO

    u10[37] += fifo_oe_bar            # the one FIFO signal bank 0 had no room for
    u10[38] += adc_shdn
    u10[39] += adc_oe_bar
    u10[41] += mode_strap
    u10[42] += probe_comp_drv
    u10[43] += ext_trig
    u10[44] += led_status
    u10[45] += led_activity

    # ==================================================================
    # Configuration control pins
    # ==================================================================
    u10["~{CRESET}"] += fpga_creset_bar       # 66
    r51 = Part("Device", "R", ref="R51", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r51[1] += v3v3_d
    r51[2] += fpga_creset_bar

    u10["CDONE"] += fpga_cdone                # 65, open-drain
    r52 = Part("Device", "R", ref="R52", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r52[1] += v3v3_d
    r52[2] += fpga_cdone

    # CDONE indicator (net_plan §1.8: "470R + LED"). CDONE is open-drain and
    # is held LOW until configuration completes, so the LED is wired from the
    # rail INTO the pin and the FPGA sinks its current.
    # READ THE INDICATOR THIS WAY: **LED ON = not yet configured.** It goes
    # out when the bitstream has loaded. Sourcing current out of CDONE
    # instead would be the intuitive polarity but is not what an open-drain
    # pin can do.
    r54 = Part("Device", "R", ref="R54", value="470R",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r54[1] += v3v3_d
    d14 = Part("Device", "LED", ref="D14", value="red (CDONE)",
               footprint="LED_SMD:LED_0603_1608Metric")
    d14["A"] += r54[2]
    d14["K"] += fpga_cdone

    # modeStrap pull-up: an unfitted JP1 jumper reads HIGH = self-boot.
    r53 = Part("Device", "R", ref="R53", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r53[1] += v3v3_d
    r53[2] += mode_strap

    # ==================================================================
    # Unused pins
    # ==================================================================
    # Factory no-connects.
    for pin in (35, 36, 50, 51, 58, 77, 133):
        u10[pin] += NC

    # Spare I/O — 15 uncommitted pins across all four banks, deliberately
    # left free (net_plan §4 budgeted only 4 "spare/debug"). Marked NC so ERC
    # reports a clean, intentional state rather than 15 floating-pin warnings.
    # Two of them are global clock inputs (93 = GBIN3, 94 = GBIN2) and two are
    # the cold-boot image selects (63 = CBSEL0, 64 = CBSEL1), which stay
    # unconnected because this board boots a single image.
    spare_io = (21,                                   # bank 3, GBIN6
                93, 94,                               # bank 1, GBIN3/GBIN2
                128,                                  # bank 0, GBIN1
                47, 48, 49, 52, 55, 56, 60, 61, 62, 63, 64)   # bank 2
    for pin in spare_io:
        u10[pin] += NC
