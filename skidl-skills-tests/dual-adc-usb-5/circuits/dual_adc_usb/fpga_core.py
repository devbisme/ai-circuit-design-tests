"""FPGA Core — Gowin GW1NR-9C (GW1NR-LV9QN88PC6/I5) capture engine, JTAG, trigger, LED
Block from: architecture/block_diagram.md
Interface nets: ADC_D1[11:0], ADC_D2[11:0], ADC_OE_N, ADC_PDWN, FPGA_CLK, FIFO_D[7:0],
                FIFO_RXF_N, FIFO_TXE_N, FIFO_RD_N, FIFO_WR_N, FIFO_OE_N, FIFO_SIWU,
                FIFO_CLK, +3V3_D, +1V2_D, GND

Datasheet notes applied (handoffs/04_datasheets.md items 2/4, GW1NR-LV9QN88PC6-I5_SUMMARY.md):
  * Power pin map from Gowin UG119E Table 3-7 (authoritative over the EasyEDA pinout):
      VCC core 1.2V : 1, 22, 45, 66
      VCCX/VCCIO0   : 64, 67, 78      VCCIO1 : 58
      VCCIO2        : 23, 44          VCCIO3 : 12   (NOT a duplicate of 64/67/78)
      VSS           : 2, 21, 24, 43, 46, 65        EP (thermal/gnd pad) : 89
  * MODE[1:0] (pins 88/87) strapped low for AUTOBOOT from the internal config flash.
    CONFIRMED from a primary source this pass: Gowin UG284-1.9.7E "GW1N/GW1NR series of
    FPGA Products Schematic Manual", Table 6 "Mode Selection" — AUTO BOOT = MODE[2:0] = 000,
    "FPGA reads data from embedded Flash for configuration". QN88 bonds out only MODE1/MODE0;
    note [1] of that table states unbonded MODE pins (MODE2 here) are internally grounded or
    tied to the supply, and JTAG (note [2]) is independent of the MODE value.
    MODE pins have internal weak pull-ups (UG284 Table 5), so they must be actively held low.
  * FPGA_CLK lands on a dedicated global-clock pin (11 = IOL15A/GCLKT_6); FIFO_CLK lands on
    pin 52 = IOR17A/GCLKT_3, also global-clock-capable and on the FT232H side of the package.
  * JTAGSEL_N (pin 4) left NC — internal weak pull-up, and per UG284 "the JTAG configuration
    functions are always available if no JTAG pin multiplexing is set".
  * The in-package memory is SDR SDRAM (not PSRAM) and is entirely internal to the SiP —
    no memory pins are bonded out, so no extra bank voltage is needed.
"""
from skidl import *


@SubCircuit
def fpga_core(adc_d1, adc_d2, adc_oe_n, adc_pdwn, fpga_clk, fifo_d, fifo_rxf_n,
              fifo_txe_n, fifo_rd_n, fifo_wr_n, fifo_oe_n, fifo_siwu, fifo_clk,
              v3v3_d, v1v2_d, gnd):
    """Gowin GW1NR-9C FPGA capture core with JTAG header, trigger input and capture LED.

    Args:
        adc_d1:      Bus(12) — ADC channel-1 data, input to the FPGA (driven by U5).
        adc_d2:      Bus(12) — ADC channel-2 data, input to the FPGA (driven by U5).
        adc_oe_n:    Net — ADC output-enable, active low. DRIVEN by this block (FPGA output).
        adc_pdwn:    Net — ADC power-down. DRIVEN by this block (FPGA output).
        fpga_clk:    Net — 20 MHz sample clock from X1. SENSED only (input to GCLK pin 11).
        fifo_d:      Bus(8) — FT232H 245-sync-FIFO data bus, bidirectional.
        fifo_rxf_n:  Net — FT232H RXF#, SENSED only (input).
        fifo_txe_n:  Net — FT232H TXE#, SENSED only (input).
        fifo_rd_n:   Net — FT232H RD#, DRIVEN by this block.
        fifo_wr_n:   Net — FT232H WR#, DRIVEN by this block.
        fifo_oe_n:   Net — FT232H OE#, DRIVEN by this block.
        fifo_siwu:   Net — FT232H SIWU, DRIVEN by this block.
        fifo_clk:    Net — 60 MHz FT232H CLKOUT. SENSED only (input to GCLK pin 52).
        v3v3_d:      Net — +3V3_D, supplies VCCX and every VCCIOx bank. CONSUMED only.
        v1v2_d:      Net — +1V2_D core rail. CONSUMED only.
        gnd:         Net — GND. CONSUMED only.

    Internal nets: JTAG_TCK/TMS/TDI/TDO, RECONFIG_N, TRIG_RAW, TRIG_IN, LED_CAP, LED_CAP_A.
    """

    # ---------------------------------------------------------------- parts
    U6 = Part('dual_adc_usb', 'GW1NR-LV9QN88PC6-I5', ref='U6',
              value='GW1NR-LV9QN88PC6/I5',
              footprint='Package_DFN_QFN:ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm')

    J4 = Part('Connector_Generic', 'Conn_01x06', ref='J4', value='JTAG',
              footprint='Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical')
    J5 = Part('Connector_Generic', 'Conn_01x02', ref='J5', value='TRIG',
              footprint='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical')

    D5 = Part('Device', 'LED', ref='D5', value='KT-0603R',
              footprint='LED_SMD:LED_0603_1608Metric')

    # R13 is deliberately NOT instantiated here — see the block handoff. The net plan
    # assigns it to the EEDATA (U7<->U8) Microwire pull-up, which lives entirely inside
    # usb_bridge; placing it here would either duplicate the ref or strand it on a net
    # this block does not see.
    R_t = Part('Device', 'R', dest=TEMPLATE,
               footprint='Resistor_SMD:R_0603_1608Metric')
    R15 = R_t(ref='R15', value='4.7k')    # RECONFIG_N pull-up (UG284 Figure 5: 4.7k)
    R16 = R_t(ref='R16', value='1k')      # TRIG_IN series / current limit at the FPGA pin
    R17 = R_t(ref='R17', value='10k')     # TRIG_IN pull-down at the connector
    R18 = R_t(ref='R18', value='330')     # D5 series, ~4 mA from 3.3V

    C100n = Part('Device', 'C', dest=TEMPLATE, value='100nF',
                 footprint='Capacitor_SMD:C_0402_1005Metric')   # CL05B104KO5NNNC
    C10u = Part('Device', 'C', dest=TEMPLATE, value='10uF',
                footprint='Capacitor_SMD:C_0805_2012Metric')    # CL21A106KAYNNNE

    # Per-supply-pin 100 nF (one cap per power pin, placed at that pin) ...
    C23, C24, C25, C26 = C100n(4)                 # VCC core   pins 1, 22, 45, 66
    C28, C29, C30 = C100n(3)                      # VCCX/VCCIO0 pins 64, 67, 78
    C31 = C100n()                                 # VCCIO1     pin 58
    C32, C33 = C100n(2)                           # VCCIO2     pins 23, 44
    C34 = C100n()                                 # VCCIO3     pin 12
    C38, C39, C40 = C100n(3)                      # extra distributed HF decoupling
    # ... plus bulk on each rail.
    C27, C36 = C10u(2)                            # +1V2_D bulk
    C35, C37 = C10u(2)                            # +3V3_D bulk
    for c, r in ((C23, 'C23'), (C24, 'C24'), (C25, 'C25'), (C26, 'C26'), (C27, 'C27'),
                 (C28, 'C28'), (C29, 'C29'), (C30, 'C30'), (C31, 'C31'), (C32, 'C32'),
                 (C33, 'C33'), (C34, 'C34'), (C35, 'C35'), (C36, 'C36'), (C37, 'C37'),
                 (C38, 'C38'), (C39, 'C39'), (C40, 'C40')):
        c.ref = r

    # ------------------------------------------------------------- power pins
    U6[1, 22, 45, 66] += v1v2_d                   # VCC, 1.2V core
    U6[2, 21, 24, 43, 46, 65] += gnd              # VSS
    U6[89] += gnd                                 # EP thermal/ground pad

    # Every I/O bank supply is 3.3V in this design. Pin 12 is VCCIO3 (Bank 3) — a bank
    # supply in its own right, not a duplicate of 64/67/78 — and gets its own local 100 nF.
    U6[64, 67, 78] += v3v3_d                      # VCCX / VCCIO0 (Bank 0)
    U6[58] += v3v3_d                              # VCCIO1        (Bank 1)
    U6[23, 44] += v3v3_d                          # VCCIO2        (Bank 2)
    U6[12] += v3v3_d                              # VCCIO3        (Bank 3)

    # ----------------------------------------------------------- decoupling
    for c in (C23, C24, C25, C26, C27, C36, C38):
        v1v2_d += c[1]
        gnd += c[2]
    for c in (C28, C29, C30, C31, C32, C33, C34, C35, C37, C39, C40):
        v3v3_d += c[1]
        gnd += c[2]

    # ----------------------------------------------- boot-mode strap (AUTOBOOT)
    # MODE[2:0] = 000 -> AUTO BOOT from the embedded config flash (UG284 Table 6).
    # MODE2 is not bonded out on QN88. Tied hard to GND rather than through UG284's
    # recommended 1 kOhm pull-down because no ref designators were allocated for MODE
    # straps; these two pins are therefore permanently unavailable as GPIO (acceptable:
    # Gowin's own guidance is to avoid using MODE0/1 as I/O).
    U6[87] += gnd                                 # IOT6B/MODE1 = 0
    U6[88] += gnd                                 # IOT5A/MODE0 = 0

    # ------------------------------------------------------- ADC data + control
    # ADC_D1 on Bank 2 (bottom edge, ADC side of the package).
    for pin, line in zip((17, 18, 19, 20, 25, 26, 27, 28, 29, 30, 31, 32), adc_d1):
        U6[pin] += line
    # ADC_D2 continues along Bank 2 and wraps onto the lower Bank 3 (left) pins.
    for pin, line in zip((33, 34, 37, 38, 39, 40, 41, 42, 47, 13, 14, 15), adc_d2):
        U6[pin] += line
    U6[16] += adc_oe_n                            # IOL26B -> U5 OE#  (FPGA drives)
    U6[3] += adc_pdwn                             # IOL2A  -> U5 PDWN (FPGA drives)

    # ------------------------------------------------------------------ clocks
    U6[11] += fpga_clk                            # IOL15A/GCLKT_6 — 20 MHz sample clock
    U6[52] += fifo_clk                            # IOR17A/GCLKT_3 — 60 MHz FT232H CLKOUT

    # ------------------------------------------- FT232H 245 synchronous FIFO (Bank 0)
    for pin, line in zip((79, 80, 81, 82, 83, 84, 85, 86), fifo_d):
        U6[pin] += line
    U6[68] += fifo_rxf_n                          # IOT42B — input from U7
    U6[69] += fifo_txe_n                          # IOT42A — input from U7
    U6[70] += fifo_rd_n                           # IOT41B — FPGA drives
    U6[71] += fifo_wr_n                           # IOT41A — FPGA drives
    U6[72] += fifo_oe_n                           # IOT39B — FPGA drives
    U6[73] += fifo_siwu                           # IOT39A — FPGA drives

    # ------------------------------------------------------------- JTAG header
    # J4: 1 = +3V3_D (programmer VREF), 2 = TMS, 3 = TCK, 4 = TDI, 5 = TDO, 6 = GND.
    jtag_tms, jtag_tck = Net('JTAG_TMS'), Net('JTAG_TCK')
    jtag_tdi, jtag_tdo = Net('JTAG_TDI'), Net('JTAG_TDO')
    J4[1] += v3v3_d
    J4[2] += jtag_tms
    J4[3] += jtag_tck
    J4[4] += jtag_tdi
    J4[5] += jtag_tdo
    J4[6] += gnd
    U6[5] += jtag_tms                             # IOL11A/TMS
    U6[6] += jtag_tck                             # IOL11B/TCK
    U6[7] += jtag_tdi                             # IOL12B/TDI
    U6[8] += jtag_tdo                             # IOL13A/TDO

    # RECONFIG_N: 4.7k pull-up per UG284 Figure 5. Not brought out to J4 — a 1x6 header
    # is fully consumed by VREF + GND + the four JTAG signals (see the block handoff).
    reconfig_n = Net('RECONFIG_N')
    U6[9] += reconfig_n                           # IOL13B/RECONFIG_N
    v3v3_d & R15 & reconfig_n

    # ---------------------------------------------------------- trigger input
    # J5.1 -> R17 (10k pull-down, defines the level with nothing plugged in)
    #      -> R16 (1k series at the FPGA pin) -> U6 pin 74.
    trig_raw, trig_in = Net('TRIG_RAW'), Net('TRIG_IN')
    J5[1] += trig_raw
    J5[2] += gnd
    trig_raw & R17 & gnd
    trig_raw & R16 & trig_in
    U6[74] += trig_in                             # IOT38B

    # ------------------------------------------------------------ capture LED
    # U6 pin 75 -> R18 (330R) -> D5 anode, D5 cathode -> GND. Active-high drive.
    led_cap = Net('LED_CAP')
    U6[75] += led_cap                             # IOT38A — FPGA drives
    led_cap & R18 & D5['A']
    D5['K'] += gnd

    # ----------------------------------------------------- intentional no-connects
    # 4  = IOL5A/JTAGSEL_N  — internal weak pull-up; JTAG stays available (UG284 Table 7).
    # 10 = IOL14A/DONE      — status only; see the handoff for the recommended 4.7k pull-up.
    # 35/36 = spare GCLK pair, 48-51/53-63 = spare Bank 1 (incl. unused MSPI/SSPI config
    # pins, free in AUTOBOOT mode), 76/77 = spare Bank 0.
    for pin in (4, 10, 35, 36, 48, 49, 50, 51, 53, 54, 55, 56, 57, 59, 60, 61, 62, 63,
                76, 77):
        U6[pin] += NC
