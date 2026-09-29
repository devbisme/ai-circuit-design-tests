"""SRAM Buffer -- 2M x 16 async SRAM frame buffer for the dual-ADC capture path
Block from: architecture/block_diagram.md
Interface nets: v3v3_d, gnd, sram_addr, sram_data, sram_ce_bar, sram_oe_bar, sram_we_bar
"""
from skidl import *

@subcircuit
def sram_buffer(v3v3_d, gnd, sram_addr, sram_data,
                sram_ce_bar, sram_oe_bar, sram_we_bar):
    """2M x 16 asynchronous SRAM used as the FPGA's capture frame buffer.

    Architecture / sourcing context (net_plan.md 1.6, 3.9; sourced_bom.md 2, 8):
    A 2x AS6C3216A-55TIN shared-bus scheme was evaluated and REJECTED (sourced_bom.md 2.1):
      - t_AW = 50 ns min against a 50 ns shared bus slot -> zero timing margin.
      - t_WP = 45 ns min inside that same 50 ns slot leaves only 5 ns for everything else,
        and is not even cleanly generatable at the FPGA's 40 MHz / 25 ns edge granularity.
      - The exact brief part (AS6C3216-55TIN) is discontinued at Digi-Key; the successor
        AS6C3216A-55TIN is 0 stock at Mouser/LCSC. The premise "cheap and available" inverted.
    Instead this block uses a SINGLE IS61WV204816BLL-10TLI (D1 option (a), sourced_bom.md 2.2/2.3):
      - 2M x 16, 10 ns access time -> ~5x timing margin in the same 50 ns bus slot.
      - $33.54, Mouser 870-WV204816BLL10TLI, stock 1303, Active -- cheaper AND in stock, unlike
        the rejected two-device scheme ($72.92 for two AS6C3216A, both effectively unobtainium).
      - Matches the net plan and FPGA pin budget exactly as already laid out (21 addr + 16 data +
        3 ctrl), so no architecture rework was required.
      - Trade accepted: off-JLC (not in the JLCPCB library), 0.5 mm-pitch TSOP-I-48 hand solder.
        A custom KiCad symbol was generated for it (sourced_bom.md 8) since it does not exist in
        the stock KiCad libraries.

    All accesses are 16-bit: UB# and LB# (byte-enable strobes) are tied permanently low to GND
    per net_plan.md 3.9, since this design never does 8-bit byte-lane accesses.

    Args:
        v3v3_d: 3.3 V digital supply rail (net_plan.md 1.1) -- powers U11.VDD.
        gnd: Ground reference -- U11.GND, and the permanently-asserted UB#/LB# byte enables.
        sram_addr: 21-bit Bus, FPGA -> SRAM address (A0..A20), net_plan.md 1.6 / 3.9.
        sram_data: 16-bit bidirectional Bus, FPGA <-> SRAM data (IO0..IO15), net_plan.md 1.6 / 3.9.
        sram_ce_bar: Chip enable, active low, FPGA -> SRAM (CE#).
        sram_oe_bar: Output enable, active low, FPGA -> SRAM (OE#).
        sram_we_bar: Write enable, active low, FPGA -> SRAM (WE#).
    """
    # ------------------------------------------------------------------
    # U11 -- IS61WV204816BLL-10TLI, 2M x 16 async SRAM, 10 ns, TSOP-I-48.
    # Custom symbol generated from the genuine 17-page ISSI datasheet
    # (datasheets/IS61WV204816BLL_issi_revA.pdf) via kipart; lives in the
    # project-local library lib/dual_adc_usb.kicad_sym (NOT the stock KiCad
    # libraries -- this part does not exist there). Loaded with an explicit
    # lib= path per the work order.
    #
    # Footprint note: the datasheet's "12mm x 20mm" figure is the lead-tip
    # span, not the JEDEC MO-142 body (18.4 x 12.0 mm, 0.5 mm pitch) that the
    # stock KiCad footprint library keys on. Same physical package --
    # reconciled in sourced_bom.md 8, footprint used as given below.
    # ------------------------------------------------------------------
    u11 = Part(
        lib='/home/devb/projects/AI/skidl-skills-test/lib/dual_adc_usb.kicad_sym',
        name='IS61WV204816BLL',
        ref='U11',
        value='IS61WV204816BLL-10TLI',
        footprint='Package_SO:TSOP-I-48_18.4x12mm_P0.5mm',
    )

    # ------------------------------------------------------------------
    # Decoupling -- net_plan.md 3.9: "U11.VDD x2, C120-C122 (100 n each,
    # at each VDD pin) + C123 (10 uF)". The device has two VDD pins
    # (pins 12 and 36); C120 and C121 are the direct at-pin 100 nF
    # bypass caps for those two pins, and C122 is the third 100 nF
    # placed alongside the C123 bulk cap (standard 100n+10uF bulk pairing
    # per the mandatory decoupling rule). All are electrically the same
    # V3V3_D-to-GND net; the split into three 0402 refs is a layout/
    # placement decision, not a netlist distinction.
    # ------------------------------------------------------------------
    c120 = Part('Device', 'C', ref='C120', value='100nF',
                footprint='Capacitor_SMD:C_0402_1005Metric')
    c121 = Part('Device', 'C', ref='C121', value='100nF',
                footprint='Capacitor_SMD:C_0402_1005Metric')
    c122 = Part('Device', 'C', ref='C122', value='100nF',
                footprint='Capacitor_SMD:C_0402_1005Metric')
    c123 = Part('Device', 'C', ref='C123', value='10uF',
                footprint='Capacitor_SMD:C_0805_2012Metric')

    for c in (c120, c121, c122, c123):
        c[1] += v3v3_d
        c[2] += gnd

    # VDD (pins 12, 36) -> V3V3_D ; GND (pins 13, 37) -> GND
    u11['VDD'] += v3v3_d
    u11['GND'] += gnd

    # ------------------------------------------------------------------
    # Byte enables tied low: UB#/LB# permanently asserted so every access
    # is a full 16-bit word access (net_plan.md 1.6 note, 3.9). No byte-
    # lane (8-bit) accesses are used anywhere in this design.
    # ------------------------------------------------------------------
    u11['UB#'] += gnd
    u11['LB#'] += gnd

    # ------------------------------------------------------------------
    # Control: FPGA -> SRAM (net_plan.md 1.6 / 3.9)
    # ------------------------------------------------------------------
    u11['CE#'] += sram_ce_bar
    u11['OE#'] += sram_oe_bar
    u11['WE#'] += sram_we_bar

    # ------------------------------------------------------------------
    # Address bus: A0..A20 <-> sram_addr[0:20], index for index.
    # ------------------------------------------------------------------
    for i in range(21):
        u11['A{}'.format(i)] += sram_addr[i]

    # ------------------------------------------------------------------
    # Data bus: IO0..IO15 <-> sram_data[0:15], index for index (bidirectional).
    # ------------------------------------------------------------------
    for i in range(16):
        u11['IO{}'.format(i)] += sram_data[i]

    # ------------------------------------------------------------------
    # NC1 (pin 6), NC2 (pin 19): intentionally unconnected per the
    # datasheet and the generated symbol -- mark explicitly rather than
    # tying them to anything, so ERC does not flag them as floating.
    # ------------------------------------------------------------------
    u11['NC1'] += NC
    u11['NC2'] += NC
