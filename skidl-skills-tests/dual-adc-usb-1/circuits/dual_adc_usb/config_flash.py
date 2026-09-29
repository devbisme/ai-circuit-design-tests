"""Config flash — W25Q32JV SPI configuration flash on the shared FPGA/MPSSE
SPI bus, plus the boot-mode strap header.
Block from: architecture/block_diagram.md
Interface nets: v3v3_d, gnd, cfg_sck, cfg_mosi, cfg_miso, cfg_cs_bar,
                fpga_creset_bar, fpga_cdone, mode_strap
"""
from skidl import *


@subcircuit
def config_flash(v3v3_d, gnd, cfg_sck, cfg_mosi, cfg_miso, cfg_cs_bar,
                 fpga_creset_bar, fpga_cdone, mode_strap):
    """4 Mbyte SPI flash holding the iCE40 bitstream, on a three-master bus.

    THE 100 R SERIES RESISTORS ARE REQUIRED, NOT OPTIONAL (net_plan.md §1.8).
    Three devices sit on cfgSck/cfgMosi/cfgMiso/cfgCsBar: the flash, the FPGA
    (which drives these pins during self-boot and may reuse them afterwards),
    and the FT2232H's MPSSE channel B. The arbitration rule is procedural, not
    electrical:

        while fpgaCresetBar is LOW   -> the FPGA tri-states its SPI pins and
                                        the FT2232H owns the bus (it can
                                        program the flash, or slave-load the
                                        FPGA directly)
        after fpgaCdone rises        -> the FT2232H tri-states BDBUS0-3 and
                                        the FPGA may reuse SPI_SCK/SI/SO/SS_B
                                        as slow-control user I/O

    A procedural rule always loses a race eventually — a host that drives
    MPSSE while the FPGA is mid-boot WILL create a brief driver fight. The
    100 R in each line is what makes that survivable: it caps the contention
    current at roughly 3.3 V / 100 R = 33 mA per line, inside every device's
    absolute maximum, and turns a latch-up risk into a retried transaction.
    Remove them and the failure mode is silent damage.

    Args:
        v3v3_d: 3.30 V digital rail. VCC_SPI on the FPGA is also 3.3 V, so the
            whole config domain is single-voltage — no level translation.
        gnd: Ground.
        cfg_sck: Shared SPI clock -> flash CLK through R62.
        cfg_mosi: Shared SPI data to the flash -> flash DI through R63.
        cfg_miso: Flash DO -> shared SPI data from the flash, through R64.
        cfg_cs_bar: Shared active-low chip select -> flash ~CS through R65.
        fpga_creset_bar: Pass-through only. Routed between `usb_bridge_ft2232h`
            (BDBUS4) and `fpga_ice40` (CRESET_B); this block adds nothing to
            it. Its pull-up lives in `fpga_ice40`.
        fpga_cdone: Pass-through only, FPGA CDONE -> FT2232H BDBUS5.
        mode_strap: Centre pin of JP1. Selects self-boot-from-flash versus
            MPSSE override.
    """

    # ------------------------------------------------------------------
    # U12 — W25Q32JVSSIQ, 32 Mbit (4 MB) SPI flash, SOIC-8 208 mil.
    # An iCE40HX4K bitstream is ~135 kB, so the part is oversized on purpose:
    # the spare space holds multiple bitstream slots and the host-side
    # gateware images described in SPEC §2.
    # ------------------------------------------------------------------
    u12 = Part("Memory_Flash", "W25Q32JVSS",
               ref="U12", value="W25Q32JVSSIQ",
               footprint="Package_SO:SOIC-8_5.3x5.3mm_P1.27mm")
    u12["VCC"] += v3v3_d
    u12["GND"] += gnd

    c125 = Part("Device", "C", ref="C125", value="100nF",
                footprint="Capacitor_SMD:C_0402_1005Metric")
    c125[1] += v3v3_d
    c125[2] += gnd

    # ~WP and ~HOLD/~RESET pulled HIGH: quad-SPI IO2/IO3 are unused, and both
    # functions are active-low, so tying them high leaves the device in plain
    # single-SPI mode with write protection and hold disabled. Resistors
    # rather than hard ties so the pins can still be repurposed for quad mode.
    r60 = Part("Device", "R", ref="R60", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r60[1] += v3v3_d
    r60[2] += u12["~{WP}/IO_{2}"]

    r61 = Part("Device", "R", ref="R61", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r61[1] += v3v3_d
    r61[2] += u12["~{HOLD}/~{RESET}/IO_{3}"]

    # ------------------------------------------------------------------
    # 100 R series on all four shared lines — see the docstring.
    # ------------------------------------------------------------------
    for ref, shared_net, pin_name in (
        ("R62", cfg_sck, "CLK"),
        ("R63", cfg_mosi, "DI/IO_{0}"),
        ("R64", cfg_miso, "DO/IO_{1}"),
        ("R65", cfg_cs_bar, "~{CS}"),
    ):
        r = Part("Device", "R", ref=ref, value="100R",
                 footprint="Resistor_SMD:R_0402_1005Metric")
        r[1] += shared_net
        r[2] += u12[pin_name]

    # ~CS pull-up to 3.3 V. Without it the flash sees a floating select while
    # every master is tri-stated (power-up, and the window between CRESET_B
    # release and CDONE) and can decode noise as a command.
    r66 = Part("Device", "R", ref="R66", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r66[1] += v3v3_d
    r66[2] += cfg_cs_bar

    # ------------------------------------------------------------------
    # JP1 — boot-mode strap, 1x3 through-hole header (SPEC §5 allows TH for
    # user-serviceable parts). A jumper on pins 1-2 pulls `modeStrap` HIGH,
    # on pins 2-3 pulls it LOW; the centre pin is the signal.
    #   HIGH = self-boot: the FPGA reads its bitstream from U12 at power-up.
    #   LOW  = MPSSE override: the host owns the SPI bus and loads the FPGA
    #          or reprograms the flash.
    # `mode_strap` also reaches an FPGA I/O with a 10 k pull-up in
    # `fpga_ice40`, so an unfitted jumper defaults to self-boot.
    # ------------------------------------------------------------------
    jp1 = Part("Connector_Generic", "Conn_01x03", ref="JP1",
               value="Boot mode",
               footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical")
    jp1[1] += v3v3_d
    jp1[2] += mode_strap
    jp1[3] += gnd

    # ------------------------------------------------------------------
    # fpga_creset_bar / fpga_cdone are PASS-THROUGH nets: net_plan §3.10
    # lists them in this block only so the schematic sheet shows the whole
    # configuration domain together. Their pull-ups (R51, R52) and the CDONE
    # LED live in `fpga_ice40`. Referencing them here keeps the signature
    # honest without creating a second driver or a duplicated pull-up.
    # ------------------------------------------------------------------
    _ = (fpga_creset_bar, fpga_cdone)
