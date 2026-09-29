"""USB bridge — FT2232HL. Channel A runs the synchronous 245 FIFO that drains
captured samples to the host; channel B runs MPSSE for FPGA/flash programming.
Block from: architecture/block_diagram.md
Interface nets: v3v3_d, gnd, usb_dp, usb_dm, fifo_*, ft_clk60, cfg_*,
                fpga_creset_bar, fpga_cdone, ft_reset_bar
"""
from skidl import *


@subcircuit
def usb_bridge_ft2232h(v3v3_d, gnd, usb_dp, usb_dm,
                       fifo_data, fifo_rxf_bar, fifo_txe_bar, fifo_rd_bar,
                       fifo_wr_bar, fifo_oe_bar, ft_clk60,
                       cfg_sck, cfg_mosi, cfg_miso, cfg_cs_bar,
                       fpga_creset_bar, fpga_cdone, ft_reset_bar):
    """USB 2.0 high-speed bridge: bulk sample drain plus in-system programming.

    WHY THIS PART. SPEC requires one USB 2.0 port to carry both power and
    digitised samples. The FT2232H's synchronous 245 FIFO reaches roughly
    35-42 MB/s of real bulk throughput, which is why the architecture buffers
    a burst in SRAM and drains it rather than streaming continuously: two
    channels at 10 MSPS x 12 bits packed into 16 bits is 40 MB/s sustained,
    right at the edge of what the link can hold. The second channel makes the
    same connector do programming, so the board needs no separate JTAG dongle.

    CORRECTION D4 — VPLL AND VPHY ARE 1.8 V PINS, NOT 3.3 V.
    net_plan.md §3.11 lists VPLL and VPHY under `V3V3_D`, fed "via L9/L10
    ferrite + 100 n". That is wrong and it is a part-damaging kind of wrong:
    on the FT2232**H** these are 1.8 V analog supplies for the PLL and the USB
    PHY, and FTDI's design guidelines connect them to **VREGOUT** through
    ferrite beads, not to the 3.3 V rail. This block feeds them from the
    internal 1.8 V regulator output (`vCore1V8`), which is also what VCORE
    takes. The ferrites and the 100 nF are kept exactly as tabulated; only the
    source rail changes. Same provenance as decision D3: the entry was written
    from a product page while the datasheet was unobtainable.

    CORRECTION D5 — THERE IS NO PWRSAV# PIN.
    net_plan.md §3.11 ends with "U13.PWRSAV# pulled high". PWRSAV# belongs to
    the FT2232**D**. The H part has ~PWREN (60) and ~SUSPEND (36), and both are
    OUTPUTS — pulling either high would fight the device. Both are left
    unconnected here. U13.TEST tied to GND, also from §3.11, is correct and is
    implemented.

    SYNCHRONOUS 245 FIFO PIN MAP (channel A). The bus signals are NOT on
    ADBUS4-7 as a first reading of §3.11 suggests; in sync-245 mode they sit
    on ACBUS:
        ADBUS0-7  = D0-D7 bidirectional data
        ACBUS0    = RXF#   (data available for the FPGA to read)
        ACBUS1    = TXE#   (space available for the FPGA to write)
        ACBUS2    = RD#
        ACBUS3    = WR#
        ACBUS5    = CLKOUT, 60 MHz — the FIFO clock, and a second FPGA GBIN
        ACBUS6    = OE#
        ACBUS7    = SIWU#  (send-immediate/wake-up, pulled high = inactive)
    Everything in this mode is clocked by ACBUS5, which is why `ftClk60` must
    land on a global clock input at the FPGA and not an ordinary I/O.

    THE EEPROM IS ALSO THE CALIBRATION STORE. U14 must exist for the FT2232H
    to enumerate with the right VID/PID, descriptors and channel modes — the
    part reverts to a generic identity without it. SPEC §2.1 additionally
    reserves its spare space for the per-board calibration constants, so the
    board carries its own gain/offset trim wherever it is plugged in.

    Args:
        v3v3_d: 3.30 V digital rail — VCCIO x4 and VREGIN.
        gnd: Ground (GND x8 plus AGND, one netlist net).
        usb_dp, usb_dm: USB 2.0 HS differential pair, 90 Ohm, from
            `usb_power_input` (connector and ESD live there).
        fifo_data: Bus(8) on ADBUS0-7.
        fifo_rxf_bar, fifo_txe_bar: Status to the FPGA (ACBUS0/1).
        fifo_rd_bar, fifo_wr_bar, fifo_oe_bar: Strobes from the FPGA
            (ACBUS2/3/6).
        ft_clk60: 60 MHz FIFO clock out of ACBUS5 -> FPGA GBIN.
        cfg_sck, cfg_mosi, cfg_miso, cfg_cs_bar: MPSSE SPI on BDBUS0-3,
            shared with the FPGA and the flash (100 R series in
            `config_flash`).
        fpga_creset_bar: BDBUS4 -> FPGA CRESET_B. Holding it low is what
            hands the SPI bus to this device.
        fpga_cdone: FPGA CDONE -> BDBUS5, so the host can see when
            configuration finished.
        ft_reset_bar: RESET#, with pull-up and RC here. The FPGA may drive it,
            but the board resets correctly if nothing does.
    """

    # Internal 1.8 V rail: VREGOUT feeds VCORE, and (per D4) VPLL and VPHY
    # through their ferrites.
    v_core_1v8 = Net("vCore1V8")
    v_pll_1v8 = Net("vPll1V8")
    v_phy_1v8 = Net("vPhy1V8")
    for _rail in (v_core_1v8, v_pll_1v8, v_phy_1v8):
        _rail.drive = POWER    # 1.8 V rails off VREGOUT, not signals
    osc_i = Net("ftOsci")
    osc_o = Net("ftOsco")
    ee_data = Net("ftEeData")
    ee_do = Net("ftEeDo")

    u13 = Part("Interface_USB", "FT2232HL",
               ref="U13", value="FT2232HL",
               footprint="Package_QFP:LQFP-64_10x10mm_P0.5mm")

    # ==================================================================
    # Power
    # ==================================================================
    u13["GND"] += gnd          # pins 1, 5, 11, 15, 25, 35, 47, 51
    u13["AGND"] += gnd         # pin 10, PHY analog ground
    u13["TEST"] += gnd         # pin 13 — must be grounded in normal operation
    u13["VCCIO"] += v3v3_d     # pins 20, 31, 42, 56
    u13["VREGIN"] += v3v3_d    # pin 50, input to the internal 1.8 V regulator
    u13["VREGOUT"] += v_core_1v8   # pin 49, 1.8 V out
    u13["VCORE"] += v_core_1v8     # pins 12, 37, 64

    # VREGOUT reservoir (net_plan §3.11): 100 nF + 4.7 uF.
    c130 = Part("Device", "C", ref="C130", value="100nF",
                footprint="Capacitor_SMD:C_0402_1005Metric")
    c130[1] += v_core_1v8
    c130[2] += gnd
    c131 = Part("Device", "C", ref="C131", value="4.7uF",
                footprint="Capacitor_SMD:C_0603_1608Metric")
    c131[1] += v_core_1v8
    c131[2] += gnd

    # 100 nF at each VCCIO pin (4) + one 10 uF bulk on the 3.3 V rail.
    for ref in ("C135", "C136", "C137", "C138"):
        c = Part("Device", "C", ref=ref, value="100nF",
                 footprint="Capacitor_SMD:C_0402_1005Metric")
        c[1] += v3v3_d
        c[2] += gnd
    c139 = Part("Device", "C", ref="C139", value="10uF",
                footprint="Capacitor_SMD:C_0805_2012Metric")
    c139[1] += v3v3_d
    c139[2] += gnd

    # 100 nF at each VCORE pin (3). VCORE is 1.8 V, not 3.3 V.
    for ref in ("C140", "C141", "C142"):
        c = Part("Device", "C", ref=ref, value="100nF",
                 footprint="Capacitor_SMD:C_0402_1005Metric")
        c[1] += v_core_1v8
        c[2] += gnd

    # 100 nF at VREGIN.
    c143 = Part("Device", "C", ref="C143", value="100nF",
                footprint="Capacitor_SMD:C_0402_1005Metric")
    c143[1] += v3v3_d
    c143[2] += gnd

    # VPLL and VPHY: ferrite from the 1.8 V rail (correction D4), 100 nF each
    # at the pin. The ferrites are what keep digital switching on VCORE out of
    # the PLL and the USB PHY — the two blocks whose jitter shows up directly
    # as USB eye closure.
    l9 = Part("Device", "FerriteBead", ref="L9", value="600R@100MHz",
              footprint="Inductor_SMD:L_0603_1608Metric")
    l9[1] += v_core_1v8
    l9[2] += v_pll_1v8
    u13["VPLL"] += v_pll_1v8
    c144 = Part("Device", "C", ref="C144", value="100nF",
                footprint="Capacitor_SMD:C_0402_1005Metric")
    c144[1] += v_pll_1v8
    c144[2] += gnd

    l10 = Part("Device", "FerriteBead", ref="L10", value="600R@100MHz",
               footprint="Inductor_SMD:L_0603_1608Metric")
    l10[1] += v_core_1v8
    l10[2] += v_phy_1v8
    u13["VPHY"] += v_phy_1v8
    c145 = Part("Device", "C", ref="C145", value="100nF",
                footprint="Capacitor_SMD:C_0402_1005Metric")
    c145[1] += v_phy_1v8
    c145[2] += gnd

    # ==================================================================
    # USB
    # ==================================================================
    u13["DP"] += usb_dp
    u13["DM"] += usb_dm

    # R70 — 12 kOhm 1 % from REF to ground. This sets the USB transceiver's
    # internal bias currents, so its tolerance directly affects the
    # transmitted eye. 1 % is a requirement, not a habit.
    r70 = Part("Device", "R", ref="R70", value="12k 1%",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r70[1] += u13["REF"]
    r70[2] += gnd

    # ==================================================================
    # 12 MHz crystal — its OWN crystal, deliberately not shared with the
    # 40 MHz sample-clock domain (net_plan §3.11). Sharing would couple USB
    # PLL activity into the ADC encode clock, and D2 has already identified
    # clock jitter as the largest unquantified term in the noise budget.
    # ==================================================================
    y1 = Part("Device", "Crystal_GND24", ref="Y1", value="12MHz 18pF",
              footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm")
    y1[1] += osc_i
    y1[3] += osc_o
    y1["G"] += gnd          # pins 2 and 4, the case ground pads
    u13["OSCI"] += osc_i
    u13["OSCO"] += osc_o

    c132 = Part("Device", "C", ref="C132", value="27pF C0G",
                footprint="Capacitor_SMD:C_0402_1005Metric")
    c132[1] += osc_i
    c132[2] += gnd
    c133 = Part("Device", "C", ref="C133", value="27pF C0G",
                footprint="Capacitor_SMD:C_0402_1005Metric")
    c133[1] += osc_o
    c133[2] += gnd

    # ==================================================================
    # Reset
    # ==================================================================
    u13["~{RESET}"] += ft_reset_bar
    r71 = Part("Device", "R", ref="R71", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r71[1] += v3v3_d
    r71[2] += ft_reset_bar
    c134 = Part("Device", "C", ref="C134", value="100nF",
                footprint="Capacitor_SMD:C_0402_1005Metric")
    c134[1] += ft_reset_bar
    c134[2] += gnd

    # ==================================================================
    # U14 — 93LC66B configuration EEPROM (see the docstring).
    # The FT2232H drives EEDATA as a bidirectional pin: it writes on EEDATA
    # directly and reads the EEPROM's DO through R72, which is a current
    # limiter for the interval when both ends drive. R73 holds DO high while
    # the EEPROM is deselected.
    # ==================================================================
    u14 = Part("Memory_EEPROM", "93LCxxBxxOT",
               ref="U14", value="93LC66BT-I/OT",
               footprint="Package_TO_SOT_SMD:SOT-23-6")
    u14["VCC"] += v3v3_d
    u14["GND"] += gnd
    u14["CS"] += u13["EECS"]
    u14["CLK"] += u13["EECLK"]
    u14["DI"] += ee_data
    u14["DO"] += ee_do
    u13["EEDATA"] += ee_data

    r72 = Part("Device", "R", ref="R72", value="2.2k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r72[1] += ee_do
    r72[2] += ee_data
    r73 = Part("Device", "R", ref="R73", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r73[1] += v3v3_d
    r73[2] += ee_do

    c146 = Part("Device", "C", ref="C146", value="100nF",
                footprint="Capacitor_SMD:C_0402_1005Metric")
    c146[1] += v3v3_d
    c146[2] += gnd

    # ==================================================================
    # Channel A — synchronous 245 FIFO
    # ==================================================================
    for i in range(8):
        u13["ADBUS%d" % i] += fifo_data[i]

    u13["ACBUS0"] += fifo_rxf_bar
    u13["ACBUS1"] += fifo_txe_bar
    u13["ACBUS2"] += fifo_rd_bar
    u13["ACBUS3"] += fifo_wr_bar
    u13["ACBUS5"] += ft_clk60
    u13["ACBUS6"] += fifo_oe_bar

    # SIWU# pulled high = the send-immediate/wake-up request is never
    # asserted. The FPGA drains in fixed-size bursts, so there is nothing to
    # flush early; leaving the pin floating would let noise trigger spurious
    # short packets.
    siwu_bar = Net("ftSiwuBar")
    u13["ACBUS7"] += siwu_bar
    r74 = Part("Device", "R", ref="R74", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r74[1] += v3v3_d
    r74[2] += siwu_bar

    u13["ACBUS4"] += NC     # unused in sync-245 mode

    # ==================================================================
    # Channel B — MPSSE, used for FPGA/flash programming
    # ==================================================================
    u13["BDBUS0"] += cfg_sck
    u13["BDBUS1"] += cfg_mosi
    u13["BDBUS2"] += cfg_miso
    u13["BDBUS3"] += cfg_cs_bar
    u13["BDBUS4"] += fpga_creset_bar
    u13["BDBUS5"] += fpga_cdone
    u13["BDBUS6"] += NC
    u13["BDBUS7"] += NC

    # BCBUS0-7 unused — channel B's control byte has no role in MPSSE here.
    for i in range(8):
        u13["BCBUS%d" % i] += NC

    # ~PWREN (60) and ~SUSPEND (36) are OUTPUTS and are left unconnected —
    # see correction D5 in the docstring. They are useful test points but
    # nothing on this board consumes them.
    u13["~{PWREN}"] += NC
    u13["~{SUSPEND}"] += NC
