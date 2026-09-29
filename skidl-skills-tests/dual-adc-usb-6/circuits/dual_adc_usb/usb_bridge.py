"""USB Bridge — CY7C68013A (FX2LP) in 8-bit slave FIFO, 24 MHz crystal, boot EEPROM
Block from: architecture/block_diagram.md
Interface nets: USB_DP, USB_DM, FIFO_D[7:0], IFCLK, SLWR_N, SLRD_N, SLOE_N, PKTEND_N,
                FIFOADR[1:0], FLAGB, FLAGC, +3V3D, GND
"""
from skidl import *


# ---------------------------------------------------------------------------------
# CY7C68013A-56LTX pin names, verbatim from the stock KiCad symbol
# `MCU_Cypress:CY7C68013A-56LTX` (57 pins = 56 QFN pins + EP on pin 57 — confirmed
# against the QFN-56-1EP footprint, which has pads 1..57).
#
# The symbol's names carry the alternate functions, so slave-FIFO signals have to be
# reached by their composite names. Exact-name lookup verified under SKiDL 3.0.0.
# ---------------------------------------------------------------------------------

# FIFO_D[7:0] -> PB0..PB7 (= FD0..FD7 in 8-bit slave FIFO mode). Bit 0 = LSB,
# matching fpga_core's _P_FIFO_D ordering.
_N_FIFO_D = [f'PB{i}/FD{i}' for i in range(8)]

# FIFOADR[1:0] -> PA4/PA5. Bit 0 = FIFOADR0.
_N_FIFOADR = ['PA4/FIOADDR0', 'PA5/FIOADDR1']

# Port pins with no role in this design. All are configurable I/O that come up as
# inputs; left as explicit no-connects rather than floating by accident.
#   PD0..PD7 = FD8..FD15, unused because the FIFO is 8 bits wide (architecture
#   decision #4 — 8-bit slave FIFO at 48 MHz already beats the USB HS bulk ceiling).
_N_UNUSED = (['CTL0/FLAGA', 'PA0/~{INT0}', 'PA1/~{INT1}', 'PA3/WU2',
              'PA7/FLAGD/~{SLCS}', 'CLKOUT']
             + [f'PD{i}/FD{i + 8}' for i in range(8)])


@SubCircuit
def usb_bridge(usb_dp, usb_dm, fifo_d, ifclk, slwr_n, slrd_n, sloe_n, pktend_n,
               fifoadr, flagb, flagc, v3v3d, gnd):
    """FX2LP USB 2.0 High-Speed bridge (U50) in 8-bit slave FIFO mode, with its
    24 MHz crystal (Y1) and its I2C boot EEPROM (U51).

    The FPGA is the slave-FIFO master: it drives the strobes and the address, and
    reads the flags. The FX2LP owns the interface clock and the USB PHY.

    Args:
        usb_dp, usb_dm: [bidir] USB_DP / USB_DM high-speed pair, straight from the
                        ESD array in `usb_front` (J1 -> U1 -> here). No series
                        resistors and no external pull-up: the FX2LP has an on-chip
                        1.5 k / 45 R HS-capable transceiver.
        fifo_d:         [bidir] FIFO_D[7:0], 8-bit Bus, bit 0 = LSB = FD0.
        ifclk:          [OUT]  48 MHz interface clock. **This block drives it** — the
                        FX2LP sources IFCLK and `fpga_core` samples it
                        (net_plan.md: "U50.IFCLK -> U30").
        slwr_n, slrd_n,
        sloe_n,
        pktend_n:       [in]  Slave-FIFO strobes, driven by U30, sensed here.
        fifoadr:        [in]  FIFOADR[1:0], 2-bit Bus, bit 0 = FIFOADR0. Driven by U30.
        flagb, flagc:   [OUT] Programmable FIFO full / empty flags. **This block drives
                        them**; U30 senses them.
        v3v3d:          [in]  +3V3D, 3.318 V, within the FX2LP's 3.0-3.6 V range.
        gnd:            [in]  GND.

    Assumptions:
        * SCL/SDA are local to this block (net_plan.md scopes them "U50 <-> U51"), so
          they are created here, not passed in. No other I2C device shares them.
        * AVCC/AGND go straight to +3V3D/GND. No ferrite is available in this block's
          ref list (FB1-FB4 belong to the analog/power blocks), so the analog supply
          isolation is by decoupling and layout only.
        * ~RESET is generated locally by an RC. There is no reset supervisor and no
          external reset source in this design.
    """

    # =================================================================================
    # U50 — Cypress/Infineon CY7C68013A-56LTXC, EZ-USB FX2LP, QFN-56-EP.
    # sourcing/sourced_bom.md row U50: LCSC C14912.
    # =================================================================================
    U50 = Part('MCU_Cypress', 'CY7C68013A-56LTX', ref='U50',
               value='CY7C68013A-56LTXC',
               footprint='Package_DFN_QFN:QFN-56-1EP_8x8mm_P0.5mm_EP5.6x5.6mm')

    # --- USB high-speed pair (net_plan.md: J1.A6/B6 -> U1.IO1 -> U50.D+) -------------
    usb_dp += U50['D+']
    usb_dm += U50['D-']

    # --- Slave FIFO data + control (net_plan.md rows FIFO_D[7:0] .. FLAGC) ----------
    for i, name in enumerate(_N_FIFO_D):
        fifo_d[i] += U50[name]
    for i, name in enumerate(_N_FIFOADR):
        fifoadr[i] += U50[name]

    ifclk += U50['IFCLK']                  # driven by U50
    slrd_n += U50['RDY0/SLRD']
    slwr_n += U50['RDY1/SLWR']
    sloe_n += U50['PA2/SLOE']
    pktend_n += U50['PA6/PKTEND']
    flagb += U50['CTL1/FLAGB']             # driven by U50
    flagc += U50['CTL2/FLAGC']             # driven by U50

    # --- Pins whose static level is load-bearing ------------------------------------
    # Pin 14, "RESERVED": the datasheet's pin-description table says, verbatim,
    # "Reserved. Connect to ground." — NOT a no-connect.
    # Source: Infineon CY7C68013A datasheet 38-08032 Rev. AD, pin description table.
    gnd += U50['RESERVED']

    # Pin 44, WAKEUP (active low): "Holding WAKEUP asserted inhibits the EZ-USB chip
    # from suspending." Unused here, so it is deasserted (tied high). Tying it low
    # would block USB suspend and blow the suspend-current budget; leaving it floating
    # would make suspend behaviour indeterminate.
    v3v3d += U50['WAKEUP']

    # --- Power / ground / exposed pad ------------------------------------------------
    # 6x VCC (11,17,27,32,43,55) + 2x AVCC (3,7); 6x GND + 2x AGND; EP = pad 57.
    v3v3d += U50['VCC'], U50['AVCC']
    gnd += U50['GND'], U50['AGND'], U50['EP']

    # --- Genuinely unused port pins --------------------------------------------------
    for name in _N_UNUSED:
        U50[name] += NC

    # =================================================================================
    # Y1 — 24 MHz crystal on XTALIN/XTALOUT.
    #
    # CORRECTION vs sourcing/sourced_bom.md: that row pairs the DSX321G with the 2-pin
    # symbol `Device:Crystal` while assigning the 4-pad footprint
    # `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm`. Two pins against four pads leaves the
    # two case pads with no net. Corrected here to `Device:Crystal_GND24` (pins 1 and 3
    # are the resonator, pins 2 and 4 are the grounded case). BOM row needs the symbol
    # field fixed; MPN, LCSC number and footprint are unchanged.
    #
    # C92/C93 = 12 pF each, which is what Cypress asks for, not a misread of the
    # crystal's 12 pF CL: the datasheet's "8051 Clock Frequency" section specifies a
    # 24 MHz parallel-resonant fundamental-mode crystal with "12-pF (5% tolerance)
    # load capacitors" (38-08032 Rev. AD, p.4).
    #
    # REF DESIGNATOR NOTE: C92/C93 are not in this block's work-order ref list
    # (C80-C91), but sourced_bom.md labels them "(Y1 load caps)" and Y1 is this
    # block's part. They are used here. No other block can own them.
    # =================================================================================
    Y1 = Part('Device', 'Crystal_GND24', ref='Y1', value='24MHz',
              footprint='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm')
    C92, C93 = Part('Device', 'C', dest=TEMPLATE, value='12pF',
                    footprint='Capacitor_SMD:C_0402_1005Metric')(2)
    C92.ref, C93.ref = 'C92', 'C93'

    U50['XTALIN'] += Y1[1]
    U50['XTALOUT'] += Y1[3]
    Y1[1] += C92[1]
    Y1[3] += C93[1]
    gnd += C92[2], C93[2]
    gnd += Y1[2], Y1[4]                    # grounded case pads — EMI shield

    # =================================================================================
    # ~RESET (pin 42) — power-on reset RC.
    #
    # The FX2LP has no adequate internal POR. Datasheet Table 5, "Reset Timing Values"
    # (38-08032 Rev. AD, p.8): with a crystal, TRESET must be "approximately 5 ms after
    # VCC reaches 3.0 V" so the crystal and PLL can stabilise.
    #
    # With R52 pulling to +3V3D and C89 to GND, ~RESET reaches the 2.0 V VIH at
    #     t = R*C * ln(3.3 / (3.3 - 2.0)) = 0.932 * R * C
    # A 10 k/100 nF pair gives 0.93 ms — 5x too short, which is exactly what the
    # BOM's 10 k placeholder would have produced. 100 k/100 nF gives 9.3 ms, 1.9x the
    # requirement. R52 is therefore 100 kOhm, not the placeholder 10 kOhm (same MPN
    # family already in the BOM for R3/R18: 0402WGF1003TCE, LCSC C25741).
    # =================================================================================
    RESET_N = Net('FX2_RESET_N')
    R52 = Part('Device', 'R', ref='R52', value='100k',
               footprint='Resistor_SMD:R_0402_1005Metric')
    C89 = Part('Device', 'C', ref='C89', value='100nF',
               footprint='Capacitor_SMD:C_0402_1005Metric')
    v3v3d += R52[1]
    RESET_N += R52[2], C89[1], U50['~{RESET}']
    gnd += C89[2]

    # =================================================================================
    # U51 — Microchip 24LC64-I/SN boot EEPROM on the FX2LP's I2C bus.
    #
    # *** THE LOAD-BEARING STRAP IN THIS DESIGN ***
    # The FX2LP boot loader looks for a 2-byte-address ("large") EEPROM at I2C 7-bit
    # address 0x51 (0xA2 as an 8-bit write byte) and NOWHERE ELSE. That requires
    # A2=0, A1=0, A0=1 — i.e. A0 pulled HIGH, not the 24LC64's all-low default of 0x50.
    # Strapping all three low means the FX2 never boots from this EEPROM and the board
    # enumerates as a bare "Cypress FX2" default device, if at all.
    # Sources, both primary and both read in phase 4:
    #   * Infineon CY7C68013A datasheet 38-08032 Rev. AD, p.16, Table 8, "Strap Boot
    #     EEPROM Address Lines to These Values" — names 24LC64 explicitly, 8K row
    #     gives (A2,A1,A0) = (0,0,1).
    #   * Microchip 24LC64 datasheet DS21189T, p.7, section 5.0 / Figure 5-1 — control
    #     byte is `1010 A2 A1 A0 R/W`, so (0,0,1) -> 1010 0010 = 0xA2 write / 0x51.
    # =================================================================================
    U51 = Part('Memory_EEPROM', '24LC64', ref='U51', value='24LC64-I/SN',
               footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')

    SCL = Net('SCL')
    SDA = Net('SDA')
    SCL += U50['SCL'], U51['SCL']
    SDA += U50['SDA'], U51['SDA']

    # R50/R51 — 2.2 kOhm I2C pull-ups (sourced_bom.md already identifies them as such;
    # confirmed against net_plan.md's SCL/SDA row, "2.2 kOhm pull-ups to +3V3D").
    R50, R51 = Part('Device', 'R', dest=TEMPLATE, value='2.2k',
                    footprint='Resistor_SMD:R_0402_1005Metric')(2)
    R50.ref, R51.ref = 'R50', 'R51'
    v3v3d += R50[1], R51[1]
    SCL += R50[2]
    SDA += R51[2]

    # Address straps. Pull resistors rather than hard copper ties so the address can be
    # moved by a rework if a future firmware load wants a different EEPROM slot; the
    # pins are static CMOS inputs, so the value only has to beat their leakage.
    R53 = Part('Device', 'R', ref='R53', value='10k',
               footprint='Resistor_SMD:R_0402_1005Metric')   # A0 -> HIGH  (the "1")
    R54 = Part('Device', 'R', ref='R54', value='10k',
               footprint='Resistor_SMD:R_0402_1005Metric')   # A1 -> LOW
    R55 = Part('Device', 'R', ref='R55', value='10k',
               footprint='Resistor_SMD:R_0402_1005Metric')   # A2 -> LOW
    # Named so the strap is readable in the netlist rather than an anonymous N$nn.
    EE_A0, EE_A1, EE_A2 = Net('EE_A0'), Net('EE_A1'), Net('EE_A2')
    v3v3d += R53[1]
    EE_A0 += R53[2], U51['A0']     # A0 = 1  <-- the bit that makes the address 0x51
    EE_A1 += R54[1], U51['A1']     # A1 = 0
    EE_A2 += R55[1], U51['A2']     # A2 = 0
    gnd += R54[2], R55[2]

    # WP (pin 7) tied hard to GND: the FX2 must be able to write its own config on
    # first programming, and no write-protect jumper is wanted on this board. The
    # 24LC64 datasheet permits a direct VSS tie (active-high protect). This is why
    # R52 was spent on the reset RC instead of a WP pull — see the ~RESET block above.
    gnd += U51['WP']

    # =================================================================================
    # Decoupling — sourced_bom.md assigns C80-C89 (100 nF 0402) and C90/C91 (10 uF
    # 0805) to this block. C89 is consumed by the reset RC above, so the 100 nF budget
    # here is C80-C88: eight for U50's supply pins (6x VCC + 2x AVCC) and one for U51.
    # C90/C91 are the local bulk reservoirs.
    # =================================================================================
    _c100n = Part('Device', 'C', dest=TEMPLATE, value='100nF',
                  footprint='Capacitor_SMD:C_0402_1005Metric')
    c_decoup = _c100n(9)
    for idx, cap in enumerate(c_decoup):
        cap.ref = f'C{80 + idx}'           # C80..C87 -> U50, C88 -> U51
        v3v3d += cap[1]
        gnd += cap[2]

    C90, C91 = Part('Device', 'C', dest=TEMPLATE, value='10uF',
                    footprint='Capacitor_SMD:C_0805_2012Metric')(2)
    C90.ref, C91.ref = 'C90', 'C91'        # C90 digital-side bulk, C91 AVCC-side bulk
    v3v3d += C90[1], C91[1]
    gnd += C90[2], C91[2]

    # U51 supply.
    v3v3d += U51['VCC']
    gnd += U51['GND']
