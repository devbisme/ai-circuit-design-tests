"""FPGA capture — GW1NR-9 (QN88P, embedded PSRAM), decoupling, JTAG header
Block from: architecture/block_diagram.md  (block_id: fpga_capture)

Captures both ADC buses at 10 MSPS, packs 12-bit samples 4-into-3 16-bit words,
buffers bursts in the in-package PSRAM, and streams to the FX2LP slave FIFO.
Implements architecture/net_plan.md "## FPGA <-> FX2LP slave-FIFO nets".

PIN ASSIGNMENT IS PART OF THIS NETLIST. Pins are addressed by NUMBER, not by name,
because most GW1NR-9 pins carry multi-function names (IOL11A/TMS) whose short form
is ambiguous. The map below comes from datasheets/UG803_GW1NR9_Pinout.pdf, QN88P
column, parsed pin-by-pin.

Bank map for QN88P (UG803 "Power" sheet, QN88P table) — see
architecture/driver_amendments.md A2:

    Bank 0  VCCX/VCCIO0 (64, 67, 78)   2.375-3.6 V   NO user I/O in this package
    Bank 1  VCCIO1 (58)                1.14-3.6 V    25 user I/O  -> +3V3
    Bank 2  VCCIO2 (23, 44)            1.14-3.6 V    23 user I/O  -> +3V3
    Bank 3  VCCIO3 (12)                1.71-1.89 V   23 user I/O  -> +1V8, tied to PSRAM

Only 48 pins can carry 3.3 V logic and the data path needs 44 of them (after
amendment A2 drops the two OTR lines and moves LED_CAP_N into Bank 3). Four spare:
pins 51, 75, 76, 77.

*** ARCHITECTURE AMENDMENT A3 (architecture/driver_amendments.md) ***
RECONFIG_N (pin 9) sits in Bank 3 at 1.8 V but net_plan.md drives it from the FX2LP
at 3.3 V. GW1N I/O are not 3.3 V tolerant when VCCIO = 1.8 V, so FPGA_RST_N arrives
through a 10k/12k divider (3.3 V x 12/22 = 1.80 V) built here. R35 and R36 pull up
to +1V8, NOT +3V3, for the same reason, and J3 carries +1V8 as its reference — the
Gowin programmer must be set to 1.8 V VCCIO at bring-up.
"""
from skidl import *

# ---- QN88P pin assignment (see module docstring) --------------------------------
ADC1_D_PINS = [17, 18, 19, 20, 25, 26, 27, 28, 29, 30, 31, 32]   # Bank 2, [0]=LSB
ADC2_D_PINS = [33, 34, 36, 37, 38, 39, 40, 41, 42, 47, 48, 49]   # Bank 2 + 2 in Bank 1
FD_PINS = [50, 53, 54, 55, 56, 57, 59, 60]                       # Bank 1
CLK_FPGA_PIN = 35        # IOB29A/GCLKT_4 — global clock input
IFCLK_PIN = 52           # IOR17A/GCLKT_3 — driven OUT by the FPGA PLL
SLWR_PIN, SLRD_PIN, SLOE_PIN, PKTEND_PIN = 61, 62, 63, 68
FIFOADR_PINS = [69, 70]
FLAGA_PIN, FLAGB_PIN, FLAGC_PIN = 71, 72, 73
TRIG_PIN = 74            # Bank 1, 3.3 V
# ERC-REVIEW FIX (handoffs/06_erc.md): aux_io pulls this LED up to +3V3, so the pin
# must be in a 3.3 V bank — on a Bank-3 pin the pull-up would over-drive a 1.8 V input.
# Moved to spare Bank-1 pin 75. Amendment A2's pin budget still holds: 45 of 48 used.
LED_CAP_PIN = 75         # Bank 1, 3.3 V
RECONFIG_PIN = 9         # Bank 3, 1.8 V — fed through the A3 divider
TMS_PIN, TCK_PIN, TDI_PIN, TDO_PIN = 5, 6, 7, 8                  # Bank 3, 1.8 V JTAG
JTAGSEL_N_PIN = 4        # internal weak pull-up, left open per UG803
MODE0_PIN, MODE1_PIN = 88, 87
SPARE_PINS = [11, 51, 76, 77]   # 11 is Bank 3 (1.8 V); the rest are Bank 1

VCC_PINS = [1, 22, 45, 66]           # core, +1V2
VCCIO3_PINS = [12]                   # PSRAM bank, +1V8
VCCIO2_PINS = [23, 44]               # +3V3
VCCIO1_PINS = [58]                   # +3V3
VCCX_PINS = [64, 67, 78]             # VCCX/VCCIO0, +3V3
VSS_PINS = [2, 21, 24, 43, 46, 65]


@SubCircuit
def fpga_capture(v3v3, v1v2, v1v8, gnd, clk_fpga, adc1_d, adc2_d, adc1_otr, adc2_otr,
                 fd, ifclk, slwr_n, slrd_n, sloe_n, fifoadr, flaga, flagb, flagc,
                 pktend_n, fpga_rst_n, trig_io, led_cap_n):
    """Capture/pack/buffer FPGA and its configuration interface.

    Args:
        v3v3, v1v2, v1v8 (Net): INPUT rails. v1v2 = core, v1v8 = PSRAM bank (Bank 3),
                          v3v3 = Banks 1/2 and VCCX.
        gnd (Net): INPUT. Single GND net.
        clk_fpga (Net): INPUT. 10 MHz from clock_gen, lands on GCLKT_4.
        adc1_d, adc2_d (Bus): INPUT, 12 bits each, [0] = LSB.
        adc1_otr, adc2_otr (Net): accepted for manifest compatibility, NOT connected
                          (amendment A2). __main__.py does not route them.
        fd (Bus): BIDIRECTIONAL, 8 bits, FX2LP slave-FIFO data.
        ifclk (Net): OUTPUT (FPGA sources the 48 MHz interface clock).
        slwr_n, slrd_n, sloe_n, pktend_n (Net): OUTPUT to the FX2LP.
        fifoadr (Bus): OUTPUT, 2 bits, FX2LP endpoint select.
        flaga, flagb, flagc (Net): INPUT from the FX2LP (FIFO full/empty flags).
        fpga_rst_n (Net): INPUT at 3.3 V from FX2LP PA3 — divided to 1.8 V here.
        trig_io (Net): BIDIRECTIONAL 3.3 V external trigger.
            led_cap_n (Net): OUTPUT, active-low capture LED on Bank-1 pin 75 (3.3 V), so
                          aux_io's 3.3 V pull-up is safe.

    Unused I/O are explicitly tied to NC so ERC sees them as intentional, not floating.
    """

    r_0402 = Part('Device', 'R', dest=TEMPLATE,
                  footprint='Resistor_SMD:R_0402_1005Metric')
    c_0402 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0402_1005Metric')
    c_0603 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0603_1608Metric')

    U12 = Part('dual_adc_usb', 'GW1NR-LV9QN88PC6-I5', ref='U12',
               value='GW1NR-LV9QN88PC6/I5',
               footprint='Package_DFN_QFN:ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm')

    # ---- Supplies ----------------------------------------------------------------
    for p in VCC_PINS:
        U12[p] += v1v2
    for p in VCCIO3_PINS:
        U12[p] += v1v8
    for p in VCCIO2_PINS + VCCIO1_PINS + VCCX_PINS:
        U12[p] += v3v3
    for p in VSS_PINS:
        U12[p] += gnd
    # UG803: "It is highly recommended that the epad connect to GND, but not a
    # requirement." Pad 89 in the QFN-88-1EP footprint.
    U12[89] += gnd

    # ---- Data path ---------------------------------------------------------------
    for i, p in enumerate(ADC1_D_PINS):
        U12[p] += adc1_d[i]
    for i, p in enumerate(ADC2_D_PINS):
        U12[p] += adc2_d[i]
    for i, p in enumerate(FD_PINS):
        U12[p] += fd[i]
    for i, p in enumerate(FIFOADR_PINS):
        U12[p] += fifoadr[i]

    U12[CLK_FPGA_PIN] += clk_fpga
    U12[IFCLK_PIN] += ifclk
    U12[SLWR_PIN] += slwr_n
    U12[SLRD_PIN] += slrd_n
    U12[SLOE_PIN] += sloe_n
    U12[PKTEND_PIN] += pktend_n
    U12[FLAGA_PIN] += flaga
    U12[FLAGB_PIN] += flagb
    U12[FLAGC_PIN] += flagc
    U12[TRIG_PIN] += trig_io
    U12[LED_CAP_PIN] += led_cap_n

    # ---- A3: 3.3 V FPGA_RST_N -> 1.8 V RECONFIG_N --------------------------------
    # A static reset, so a resistive divider is adequate and costs no new part family.
    R47 = r_0402(ref='R47', value='10k')      # series, from the 3.3 V side
    R48 = r_0402(ref='R48', value='12k')      # shunt to GND -> 3.3 * 12/22 = 1.80 V
    reconfig_n = Net('RECONFIG_N')
    fpga_rst_n & R47 & reconfig_n & R48 & gnd
    U12[RECONFIG_PIN] += reconfig_n

    R35 = r_0402(ref='R35', value='10k')      # RECONFIG_N pull-up — to +1V8 (A3)
    v1v8 & R35 & reconfig_n

    # ---- JTAG (Bank 3, 1.8 V logic — see module docstring) -----------------------
    tms, tck, tdi, tdo = Net('TMS'), Net('TCK'), Net('TDI'), Net('TDO')
    U12[TMS_PIN] += tms
    U12[TCK_PIN] += tck
    U12[TDI_PIN] += tdi
    U12[TDO_PIN] += tdo
    R36 = r_0402(ref='R36', value='10k')      # TMS pull-up — to +1V8 (A3)
    v1v8 & R36 & tms

    J3 = Part('Connector_Generic', 'Conn_02x03_Odd_Even', ref='J3', value='JTAG 1V8',
              footprint='Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical')
    J3[1] += v1v8      # programmer reference voltage — 1.8 V, NOT 3.3 V
    J3[2] += gnd
    J3[3] += tck
    J3[4] += tms
    J3[5] += tdi
    J3[6] += tdo

    # ---- Configuration straps ----------------------------------------------------
    # MODE0/MODE1 select the boot mode. UG803 does not carry the mode truth table
    # (it is in DS117E, which could not be obtained this session — see
    # handoffs/04_datasheets.md). Both are strapped low through 10k so the state is
    # defined and can be re-strapped at bring-up without cutting a track.
    # *** CONFIRM AGAINST DS117E BEFORE FAB. ***
    R49 = r_0402(ref='R49', value='10k')
    R50 = r_0402(ref='R50', value='10k')
    mode0, mode1 = Net('MODE0'), Net('MODE1')
    U12[MODE0_PIN] += mode0
    U12[MODE1_PIN] += mode1
    mode0 & R49 & gnd
    mode1 & R50 & gnd

    # JTAGSEL_N has an internal weak pull-up (UG803 pin definitions); leave it open.
    U12[JTAGSEL_N_PIN] += NC

    # ---- Unused I/O --------------------------------------------------------------
    used = set(ADC1_D_PINS + ADC2_D_PINS + FD_PINS + FIFOADR_PINS + VCC_PINS +
               VCCIO3_PINS + VCCIO2_PINS + VCCIO1_PINS + VCCX_PINS + VSS_PINS + [89] +
               [CLK_FPGA_PIN, IFCLK_PIN, SLWR_PIN, SLRD_PIN, SLOE_PIN, PKTEND_PIN,
                FLAGA_PIN, FLAGB_PIN, FLAGC_PIN, TRIG_PIN, LED_CAP_PIN, RECONFIG_PIN,
                TMS_PIN, TCK_PIN, TDI_PIN, TDO_PIN, JTAGSEL_N_PIN,
                MODE0_PIN, MODE1_PIN])
    for pin in U12.pins:
        if int(pin.num) not in used:
            pin += NC

    # ---- Decoupling: 100 nF at every supply pin + bulk per rail ------------------
    cap_ref = iter(range(73, 91))             # C73..C90
    for p in VCC_PINS:
        v1v2 & c_0402(ref=f'C{next(cap_ref)}', value='100nF') & gnd
    for p in VCCIO3_PINS:
        v1v8 & c_0402(ref=f'C{next(cap_ref)}', value='100nF') & gnd
    for p in VCCIO2_PINS + VCCIO1_PINS + VCCX_PINS:
        v3v3 & c_0402(ref=f'C{next(cap_ref)}', value='100nF') & gnd
    for rail in (v1v2, v1v8, v3v3):
        rail & c_0603(ref=f'C{next(cap_ref)}', value='10uF') & gnd

    # ---- Test point --------------------------------------------------------------
    TP14 = Part('Connector', 'TestPoint', ref='TP14', value='CLK_FPGA',
                footprint='TestPoint:TestPoint_Pad_D1.0mm')
    TP14[1] += clk_fpga
