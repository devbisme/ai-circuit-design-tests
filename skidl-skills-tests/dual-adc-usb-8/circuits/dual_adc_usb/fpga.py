"""FPGA — GW1NR-LV9QN88PC6/I5 capture engine (8.6k LUT + 64 Mbit in-package PSRAM)
Block from: architecture/block_diagram.md (fpga)
Interface nets: FPGA_CLK, DA0..DA11, DB0..DB11, ADC_DVA, ADC_STPD, FT_D0..FT_D7, FT_RXF_N,
                FT_TXE_N, FT_RD_N, FT_WR_N, FT_SIWU_N, FT_CLKOUT, FT_OE_N, V3V3D, V1V2, V1V8, GND
Pin assignment table (for the HDL constraints file): circuits/dual_adc_usb/fpga_pinmap.md
"""
from skidl import *

# ---------------------------------------------------------------------------
# U9 pin map (pin numbers; names contain '/', so pins are referenced by number)
# Bank 2 (VCCIO2 = 3.3 V): FPGA_CLK, DA0..DA11, DB0..DB9
# Bank 1 (VCCIO1 = 3.3 V): DB10, DB11, ADC_DVA, ADC_STPD, FT_* (15), LEDs, TRIG, GPIO
# Bank 3 (VCCIO3 = 1.8 V, PSRAM bank): JTAG, RECONFIG_N, MODE0/1 only
# ---------------------------------------------------------------------------
FPGA_CLK_PIN = 35                                           # IOB29A/GCLKT_4
DA_PINS = (17, 18, 19, 20, 25, 26, 27, 28, 29, 30, 31, 32)  # DA0..DA11
DB_PINS = (33, 34, 36, 37, 38, 39, 40, 41, 42, 47, 48, 49)  # DB0..DB11
ADC_DVA_PIN = 50
ADC_STPD_PIN = 51
FT_CLKOUT_PIN = 52                                          # IOR17A/GCLKT_3
FT_D_PINS = (53, 54, 55, 56, 57, 59, 60, 61)                # FT_D0..FT_D7
FT_RXF_N_PIN = 62
FT_TXE_N_PIN = 63
FT_RD_N_PIN = 68
FT_WR_N_PIN = 69
FT_SIWU_N_PIN = 70
FT_OE_N_PIN = 71
LED_ACT_PIN = 72
LED_TRIG_PIN = 73
TRIG_IN_PIN = 74
TRIG_OUT_PIN = 75
GPIO1_PIN = 76
GPIO2_PIN = 77
TMS_PIN, TCK_PIN, TDI_PIN, TDO_PIN = 5, 6, 7, 8
RECONFIG_N_PIN = 9
MODE1_PIN, MODE0_PIN = 87, 88
# Unused bank-3 I/O (1.8 V) — intentionally NC. Pin 4 JTAGSEL_N has an internal pull-up.
BANK3_NC_PINS = (3, 4, 10, 11, 13, 14, 15, 16, 79, 80, 81, 82, 83, 84, 85, 86)


@SubCircuit
def fpga(fpga_clk, da, db, adc_dva, adc_stpd, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n,
         ft_siwu_n, ft_clkout, ft_oe_n, v3v3d, v1v2, v1v8, gnd):
    """U9 GW1NR-9 FPGA with JTAG header J4, aux header J5, status LEDs D2/D3.

    Inputs: fpga_clk (40 MHz CMOS, GCLKT_4 pin 35), da[0..11]/db[0..11] (index 0 = LSB),
    adc_dva, ft_rxf_n, ft_txe_n, ft_clkout (60 MHz, GCLKT_3 pin 52).
    Outputs: adc_stpd, ft_rd_n, ft_wr_n, ft_siwu_n, ft_oe_n. Bidirectional: ft_d[0..7].
    Power (consumed): v1v2 core, v3v3d VCCX/VCCIO0/1/2, v1v8 VCCIO3 (PSRAM bank 3), gnd.
    Config: MODE0/MODE1 pulled low with 1 k (R18/R19) -> AUTOBOOT from internal flash
    (MODE2 unbonded on QN88P, assumed 0). RECONFIG_N 10 k (R20) to v1v8. JTAG on J4 (VREF = V1V8).
    """
    U9 = Part('dual_adc_usb', 'GW1NR-LV9QN88PC6', ref='U9', value='GW1NR-LV9QN88PC6/I5',
              footprint='Package_DFN_QFN:ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm')

    # --- supplies (UG119 Table 3-8) ---
    vcc_pins = (1, 22, 45, 66)
    vccx_pins = (64, 67, 78)               # VCCX/VCCIO0
    vccio12_pins = (58, 23, 44)            # VCCIO1, VCCIO2 x2
    vccio3_pins = (12,)
    for n in vcc_pins:
        U9[n] += v1v2
    for n in vccx_pins + vccio12_pins:
        U9[n] += v3v3d
    for n in vccio3_pins:
        U9[n] += v1v8
    for n in (2, 21, 24, 43, 46, 65, 89):  # VSS + EP
        U9[n] += gnd

    # --- decoupling: 0.1 uF per supply pin (C33-C43) + bulk C44/C45/C46 ---
    c_0402 = 'Capacitor_SMD:C_0402_1005Metric'
    c_0603 = 'Capacitor_SMD:C_0603_1608Metric'
    rails = ([v1v2] * len(vcc_pins) + [v3v3d] * (len(vccx_pins) + len(vccio12_pins))
             + [v1v8] * len(vccio3_pins))
    for i, rail in enumerate(rails):       # 4 + 6 + 1 = 11 caps
        rail & Part('Device', 'C', ref=f'C{33 + i}', value='100nF', footprint=c_0402) & gnd
    v1v2 & Part('Device', 'C', ref='C44', value='10uF', footprint=c_0603) & gnd
    v3v3d & Part('Device', 'C', ref='C45', value='10uF', footprint=c_0603) & gnd
    v1v8 & Part('Device', 'C', ref='C46', value='4.7uF', footprint=c_0603) & gnd

    # --- ADC interface (banks 2/1) ---
    U9[FPGA_CLK_PIN] += fpga_clk
    for i, n in enumerate(DA_PINS):
        U9[n] += da[i]
    for i, n in enumerate(DB_PINS):
        U9[n] += db[i]
    U9[ADC_DVA_PIN] += adc_dva
    U9[ADC_STPD_PIN] += adc_stpd

    # --- FT232H sync-245 FIFO interface (bank 1) ---
    U9[FT_CLKOUT_PIN] += ft_clkout
    for i, n in enumerate(FT_D_PINS):
        U9[n] += ft_d[i]
    U9[FT_RXF_N_PIN] += ft_rxf_n
    U9[FT_TXE_N_PIN] += ft_txe_n
    U9[FT_RD_N_PIN] += ft_rd_n
    U9[FT_WR_N_PIN] += ft_wr_n
    U9[FT_SIWU_N_PIN] += ft_siwu_n
    U9[FT_OE_N_PIN] += ft_oe_n

    # --- configuration straps (bank 3, 1.8 V) ---
    mode0 = Net('FPGA_MODE0')
    mode1 = Net('FPGA_MODE1')
    reconfig_n = Net('FPGA_RECONFIG_N')
    r_0603 = 'Resistor_SMD:R_0603_1608Metric'
    U9[MODE0_PIN] += mode0
    U9[MODE1_PIN] += mode1
    U9[RECONFIG_N_PIN] += reconfig_n
    mode0 & Part('Device', 'R', ref='R18', value='1k', footprint=r_0603) & gnd
    mode1 & Part('Device', 'R', ref='R19', value='1k', footprint=r_0603) & gnd
    reconfig_n & Part('Device', 'R', ref='R20', value='10k', footprint=r_0603) & v1v8

    # --- JTAG header J4 (2x5, USB-Blaster-style layout, VREF = V1V8) ---
    tck, tms, tdi, tdo = Net('JTAG_TCK'), Net('JTAG_TMS'), Net('JTAG_TDI'), Net('JTAG_TDO')
    U9[TCK_PIN] += tck
    U9[TMS_PIN] += tms
    U9[TDI_PIN] += tdi
    U9[TDO_PIN] += tdo
    J4 = Part('Connector_Generic', 'Conn_02x05_Odd_Even', ref='J4', value='Conn_02x05',
              footprint='Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical')
    J4[1] += tck
    J4[2] += gnd
    J4[3] += tdo
    J4[4] += v1v8          # VREF
    J4[5] += tms
    J4[6] += reconfig_n    # spare position used for RECONFIG_N
    J4[7] += NC
    J4[8] += NC
    J4[9] += tdi
    J4[10] += gnd

    # --- status LEDs (bank 1, 3.3 V) ---
    led_act, led_trig = Net('LED_ACT'), Net('LED_TRIG')
    led_act_a, led_trig_a = Net('LED_ACT_A'), Net('LED_TRIG_A')
    U9[LED_ACT_PIN] += led_act
    U9[LED_TRIG_PIN] += led_trig
    led_act & Part('Device', 'R', ref='R21', value='1k', footprint=r_0603) & led_act_a
    led_trig & Part('Device', 'R', ref='R22', value='1k', footprint=r_0603) & led_trig_a
    D2 = Part('Device', 'LED', ref='D2', value='green', footprint='LED_SMD:LED_0603_1608Metric')
    D3 = Part('Device', 'LED', ref='D3', value='green', footprint='LED_SMD:LED_0603_1608Metric')
    D2['A'] += led_act_a
    D2['K'] += gnd
    D3['A'] += led_trig_a
    D3['K'] += gnd

    # --- aux header J5: TRIG_IN/OUT (100 R series), GPIO1/2, 3V3, GND ---
    trig_in, trig_out = Net('TRIG_IN'), Net('TRIG_OUT')
    trig_in_h, trig_out_h = Net('TRIG_IN_H'), Net('TRIG_OUT_H')
    gpio1, gpio2 = Net('GPIO1'), Net('GPIO2')
    U9[TRIG_IN_PIN] += trig_in
    U9[TRIG_OUT_PIN] += trig_out
    U9[GPIO1_PIN] += gpio1
    U9[GPIO2_PIN] += gpio2
    trig_in_h & Part('Device', 'R', ref='R23', value='100', footprint=r_0603) & trig_in
    trig_out & Part('Device', 'R', ref='R24', value='100', footprint=r_0603) & trig_out_h
    J5 = Part('Connector_Generic', 'Conn_01x06', ref='J5', value='Conn_01x06',
              footprint='Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical')
    J5[1] += trig_in_h
    J5[2] += trig_out_h
    J5[3] += gpio1
    J5[4] += gpio2
    J5[5] += v3v3d
    J5[6] += gnd

    # --- unused bank-3 I/O ---
    for n in BANK3_NC_PINS:
        U9[n] += NC
