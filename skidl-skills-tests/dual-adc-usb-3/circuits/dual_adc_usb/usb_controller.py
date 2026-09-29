"""USB controller — CY7C68013A-56LTXC (FX2LP), 24 MHz crystal, boot EEPROM, reset
Block from: architecture/block_diagram.md  (block_id: usb_controller)

USB 2.0 high-speed device in 8-bit slave-FIFO mode. The FPGA writes packed samples
into the FX2LP's FIFOs; the FX2LP moves them over a bulk IN endpoint. It also owns
the vendor control endpoint (arm/trigger/range/status, SPEC I8) and drives PWR_EN,
which gates every rail except its own +3V3_AON — that is how the board stays under
100 mA before enumeration (SPEC P3).

Implements architecture/net_plan.md "## FPGA <-> FX2LP slave-FIFO nets" and
"## USB / config / aux nets".

Pin numbers are the KiCad `MCU_Cypress:CY7C68013A-56LTX` symbol's, which matches
Cypress's 56-QFN numbering. Where datasheets/CY7C68013A-56LTXC_SUMMARY.md's hand-
transcribed pin numbers disagree with the symbol, the symbol wins — the summary
itself flags that its dual-function labels may render differently. The two agree on
every functional assignment that matters here.

NET-PLAN CORRECTION: net_plan.md maps SLWR_N to "PA1/SLWR". There is no such
function — in slave-FIFO mode SLWR is RDY1 (pin 2) and SLRD is RDY0 (pin 1), which
both the datasheet summary and the symbol confirm. PA1 (pin 34) is left unused.
"""
from skidl import *


@SubCircuit
def usb_controller(v3v3_aon, gnd, usb_dp, usb_dm, fd, ifclk, slwr_n, slrd_n, sloe_n,
                   fifoadr, flaga, flagb, flagc, pktend_n, pwr_en, fpga_rst_n):
    """FX2LP USB interface, its boot EEPROM, crystal and reset.

    Args:
        v3v3_aon (Net): INPUT. Always-on 3.3 V rail (U1) — this block is the only
                        consumer that must be alive before enumeration.
        gnd (Net): INPUT. Single GND net.
        usb_dp, usb_dm (Net): BIDIRECTIONAL USB high-speed pair, from usb_c_port
                        through the ESD array. No series resistors and no external
                        1.5k pull-up — the FX2LP integrates both.
        fd (Bus): BIDIRECTIONAL, 8 bits, slave-FIFO data to/from the FPGA.
        ifclk (Net): INPUT here (the FPGA sources the interface clock).
        slwr_n, slrd_n, sloe_n, pktend_n (Net): INPUT from the FPGA.
        fifoadr (Bus): INPUT, 2 bits, endpoint select from the FPGA.
        flaga, flagb, flagc (Net): OUTPUT to the FPGA (FIFO full/empty flags).
        pwr_en (Net): OUTPUT. PA0 — gates U2/U3/U4/U5 (every rail but +3V3_AON).
        fpga_rst_n (Net): OUTPUT. PA3 at 3.3 V — fpga_capture divides it to 1.8 V
                        before it reaches RECONFIG_N (amendment A3).

    EEPROM address: A0 = 1, A1 = A2 = 0 gives I2C address 0xA2, which is what the
    FX2LP looks for to perform a "C2 load" (full firmware boot) from a 16-bit-
    addressed EEPROM. 0xA0 would select a C0 load (VID/PID only) and the board would
    enumerate as a bare Cypress device with no firmware.
    """

    r_0402 = Part('Device', 'R', dest=TEMPLATE,
                  footprint='Resistor_SMD:R_0402_1005Metric')
    c_0402 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0402_1005Metric')
    c_0603 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0603_1608Metric')

    U13 = Part('MCU_Cypress', 'CY7C68013A-56LTX', ref='U13', value='CY7C68013A-56LTXC',
               footprint='Package_DFN_QFN:Cypress_QFN-56-1EP_8x8mm_P0.5mm_EP6.22x6.22mm_ThermalVias')
    U14 = Part('Memory_EEPROM', 'CAT24C128', ref='U14', value='CAT24C128WI-GT3',
               footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')
    Y2 = Part('Device', 'Crystal', ref='Y2', value='24MHz X322524MOB4SI',
              footprint='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm')

    # ---- Slave FIFO interface ----------------------------------------------------
    U13[1] += slrd_n          # RDY0/SLRD
    U13[2] += slwr_n          # RDY1/SLWR
    U13[13] += ifclk          # IFCLK, sourced by the FPGA PLL
    U13[35] += sloe_n         # PA2/SLOE
    U13[37] += fifoadr[0]     # PA4/FIFOADR0
    U13[38] += fifoadr[1]     # PA5/FIFOADR1
    U13[39] += pktend_n       # PA6/PKTEND
    U13[29] += flaga          # CTL0/FLAGA
    U13[30] += flagb          # CTL1/FLAGB
    U13[31] += flagc          # CTL2/FLAGC
    for i in range(8):
        U13[18 + i] += fd[i]  # PB0/FD0 .. PB7/FD7

    # ---- Control lines out -------------------------------------------------------
    U13[33] += pwr_en         # PA0 — rail enable
    U13[36] += fpga_rst_n     # PA3 — FPGA reconfigure request

    # PWR_EN needs a pull-down so the rails stay off until firmware drives PA0 high
    # (SPEC P3). It is provided ONCE, by `power_digital` (R6) per net_plan.md — a
    # second 100k here would halve it and was removed after the ERC review.

    # ---- USB ---------------------------------------------------------------------
    U13[8] += usb_dp          # D+
    U13[9] += usb_dm          # D-

    # ---- 24 MHz crystal, 12 pF load caps (net_plan.md "XTAL_IN/XTAL_OUT") --------
    xin, xout = Net('XTAL_IN'), Net('XTAL_OUT')
    U13[5] += xin
    U13[4] += xout
    Y2[1] += xin
    Y2[2] += xout
    xin & c_0402(ref='C91', value='12pF') & gnd
    xout & c_0402(ref='C92', value='12pF') & gnd

    # ---- Reset: 100k to VCC + 1 uF to GND, ~100 ms >> the 5 ms the part needs ----
    rst_n = Net('FX2_RST_N')
    R39 = r_0402(ref='R39', value='100k')
    v3v3_aon & R39 & rst_n
    rst_n & c_0603(ref='C93', value='1uF') & gnd
    U13[42] += rst_n          # RESET#

    # ---- I2C boot EEPROM ---------------------------------------------------------
    scl, sda = Net('SCL'), Net('SDA')
    U13[15] += scl
    U13[16] += sda
    U14['SCL'] += scl
    U14['SDA'] += sda
    R37 = r_0402(ref='R37', value='2.2k')
    R38 = r_0402(ref='R38', value='2.2k')
    v3v3_aon & R37 & scl
    v3v3_aon & R38 & sda
    U14['A0'] += v3v3_aon     # address 0xA2 -> C2 load (see docstring)
    U14['A1'] += gnd
    U14['A2'] += gnd
    U14['WP'] += gnd          # writable, so firmware can be re-flashed over USB
    U14['VCC'] += v3v3_aon
    U14['GND'] += gnd
    v3v3_aon & c_0402(ref='C94', value='100nF') & gnd

    # ---- Supplies ----------------------------------------------------------------
    # AVCC through FB5 so the PLL/analog side does not see digital switching noise.
    avcc = Net('FX2_AVCC')
    avcc.drive = POWER          # fed through FB5; the ferrite is not an ERC driver
    FB5 = Part('Device', 'FerriteBead', ref='FB5', value='600R@100MHz',
               footprint='Inductor_SMD:L_0603_1608Metric')
    v3v3_aon += FB5[1]
    avcc += FB5[2]
    for p in (3, 7):
        U13[p] += avcc
    for p in (6, 10):
        U13[p] += gnd         # AGND
    for p in (11, 17, 27, 32, 43, 55):
        U13[p] += v3v3_aon
    for p in (12, 26, 28, 41, 53, 56):
        U13[p] += gnd
    U13[57] += gnd            # exposed pad

    # WAKEUP must not float — tied high, suspend/remote-wakeup is not used.
    U13[44] += v3v3_aon

    # ---- Unused pins -------------------------------------------------------------
    # PD0-PD7 carry FD8-FD15, used only in 16-bit FIFO mode (this design is 8-bit).
    # PA1 and PA7 are unused GPIO. CLKOUT is unused (the FPGA sources IFCLK).
    # Pin 14 is RESERVED — the datasheet says do not treat it as GPIO, so it is left
    # unconnected rather than tied.
    for p in list(range(45, 53)) + [14, 34, 40, 54]:
        U13[p] += NC

    # ---- Decoupling: 100 nF per supply pin + bulk --------------------------------
    cap_ref = iter(range(95, 106))         # C95..C105
    for _ in range(6):                     # the six VCC pins
        v3v3_aon & c_0402(ref=f'C{next(cap_ref)}', value='100nF') & gnd
    avcc & c_0402(ref=f'C{next(cap_ref)}', value='100nF') & gnd
    v3v3_aon & c_0603(ref=f'C{next(cap_ref)}', value='10uF') & gnd
    avcc & c_0603(ref=f'C{next(cap_ref)}', value='1uF') & gnd

    # ---- Test point --------------------------------------------------------------
    TP15 = Part('Connector', 'TestPoint', ref='TP15', value='+3V3_AON',
                footprint='TestPoint:TestPoint_Pad_D1.0mm')
    TP15[1] += v3v3_aon
