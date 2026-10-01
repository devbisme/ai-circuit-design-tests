"""FPGA — GW1NR-LV9QN88PC6 with config straps, JTAG header, status LEDs and trigger header
Block from: architecture/block_diagram.md
Interface nets: FPGA_CLK40, ADC_DA[0..11], ADC_DB[0..11], ADC_SEL, ADC_MSBI_SEN, ADC_OEA_SCLK,
                ADC_STPD_SDATA, ADC_OEB, FT_D[0..7], FT_RXF_N, FT_TXE_N, FT_RD_N, FT_WR_N,
                FT_CLKOUT, FT_OE_N, +1V2, +1V8, +3V3D, GND
"""
from skidl import *

_R = 'Resistor_SMD:R_0402_1005Metric'
_C = 'Capacitor_SMD:C_0402_1005Metric'
_C10 = 'Capacitor_SMD:C_0603_1608Metric'


def _r(ref, value, mpn, lcsc):
    return Part('Device', 'R', ref=ref, value=value, footprint=_R, MPN=mpn, LCSC=lcsc)


def _cap(ref, big, a, b):
    if big:
        c = Part('Device', 'C', ref=ref, value='10uF', footprint=_C10,
                 MPN='CL10A106KP8NNNC', LCSC='C19702')
    else:
        c = Part('Device', 'C', ref=ref, value='100nF', footprint=_C,
                 MPN='CL05B104KO5NNNC', LCSC='C1525')
    c[1] += a
    c[2] += b
    return c


@SubCircuit
def fpga(fpga_clk40, adc_da, adc_db, adc_sel, adc_msbi_sen, adc_oea_sclk, adc_stpd_sdata,
         adc_oeb, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_clkout, ft_oe_n,
         v1v2, v1v8, v3v3d, gnd):
    """U9 GW1NR-LV9QN88PC6 (Gowin GW1NR-9, 64 Mb PSRAM in package).
    Pin map fixed by architecture/net_plan.md rev 2 (U9 connected by pin NUMBER).
    Banks 1/2 (3.3 V): ADC data/control, FT245 FIFO bus, clocks, LEDs, trigger.
    Bank 3 (1.8 V, VCCO3 = v1v8): JTAG, JTAGSEL_N, RECONFIG_N, MODE0/1 straps.
    adc_da/adc_db: 12-wide Bus (index 0 = LSB); ft_d: 8-wide Bus.
    FPGA drives adc_sel/msbi_sen/oea_sclk/stpd_sdata/oeb, ft_rd_n/wr_n/oe_n;
    senses adc_da/adc_db, ft_rxf_n/txe_n, ft_clkout, fpga_clk40; ft_d bidirectional.
    Consumes v1v2, v1v8, v3v3d, gnd. Assumes EP (pin 89) = GND."""
    u9 = Part('dual_adc_usb', 'GW1NR-LV9QN88PC6', ref='U9', value='GW1NR-LV9QN88PC6/I5',
              footprint='Package_DFN_QFN:ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm',
              MPN='GW1NR-LV9QN88PC6/I5', LCSC='C5799578')

    # ---- Power ----
    for n in (1, 22, 45, 66):            # VCC core
        u9[n] += v1v2
    for n in (64, 67, 78, 58, 23, 44):   # VCCX/VCCO0, VCCO1, VCCO2
        u9[n] += v3v3d
    u9[12] += v1v8                       # VCCO3 (bank 3, LVCMOS18)
    for n in (2, 21, 24, 43, 46, 65, 89):  # VSS x6 + EP (EP=GND assumed)
        u9[n] += gnd

    # Decoupling: 0.1 uF per supply pin + bulk per rail
    for ref in ('C80', 'C81', 'C82', 'C83'):
        _cap(ref, False, v1v2, gnd)
    _cap('C84', True, v1v2, gnd)
    for ref in ('C85', 'C86', 'C87', 'C88', 'C89', 'C90'):
        _cap(ref, False, v3v3d, gnd)
    _cap('C91', False, v1v8, gnd)
    _cap('C92', True, v3v3d, gnd)
    _cap('C93', True, v1v8, gnd)

    # ---- Bank 2: ADC data ----
    for bit, pin in zip(range(1, 12), (17, 18, 19, 20, 25, 26, 27, 28, 29, 30, 31)):
        u9[pin] += adc_db[bit]
    for bit, pin in enumerate((32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 47)):
        u9[pin] += adc_da[bit]

    # ---- Bank 1 ----
    u9[48] += adc_db[0]
    u9[49] += adc_sel
    u9[50] += adc_msbi_sen
    u9[51] += adc_oea_sclk
    u9[52] += ft_clkout          # IOR17A/GCLKT_3
    u9[53] += adc_stpd_sdata
    u9[54] += adc_oeb
    u9[55] += ft_rd_n
    u9[56] += ft_wr_n
    u9[57] += ft_oe_n
    u9[63] += fpga_clk40         # IOR5A/RPLL_T_in
    for bit, pin in enumerate(range(68, 76)):
        u9[pin] += ft_d[bit]
    u9[76] += ft_rxf_n
    u9[77] += ft_txe_n

    # LEDs: pin -> 1k -> LED anode, cathode -> GND (R86/D80 on pin 59 = MCLK pull-down)
    led0, led1 = Net('LED0'), Net('LED1')
    led0_a, led1_a = Net('LED0_A'), Net('LED1_A')
    u9[59] += led0
    u9[60] += led1
    r86 = _r('R86', '1k', '0402WGF1001TCE', 'C11702')
    r87 = _r('R87', '1k', '0402WGF1001TCE', 'C11702')
    led0 & r86 & led0_a
    led1 & r87 & led1_a
    d80 = Part('Device', 'LED', ref='D80', value='Green', footprint='LED_SMD:LED_0603_1608Metric',
               MPN='KT-0603G', LCSC='C12624')
    d81 = Part('Device', 'LED', ref='D81', value='Green', footprint='LED_SMD:LED_0603_1608Metric',
               MPN='KT-0603G', LCSC='C12624')
    d80['A'] += led0_a
    d80['K'] += gnd
    d81['A'] += led1_a
    d81['K'] += gnd

    # Trigger header J5: 1 TRIG_IN_EXT, 2 TRIG_OUT_EXT, 3 GND (3.3 V, not 5 V tolerant)
    trig_in, trig_out = Net('TRIG_IN'), Net('TRIG_OUT')
    trig_in_ext, trig_out_ext = Net('TRIG_IN_EXT'), Net('TRIG_OUT_EXT')
    u9[61] += trig_in
    u9[62] += trig_out
    r88 = _r('R88', '100R', 'RC0402FR-07100RL', 'C106232')
    r89 = _r('R89', '100R', 'RC0402FR-07100RL', 'C106232')
    trig_in_ext & r88 & trig_in
    trig_out & r89 & trig_out_ext
    j5 = Part('Connector_Generic', 'Conn_01x03', ref='J5', value='1x3',
              footprint='Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
              MPN='PZ254V-11-03P', LCSC='C2937625')
    j5[1] += trig_in_ext
    j5[2] += trig_out_ext
    j5[3] += gnd

    # ---- Bank 3 (1.8 V): config straps and JTAG ----
    jtagsel_n = Net('FPGA_JTAGSEL_N')
    reconfig_n = Net('FPGA_RECONFIG_N')
    mode0, mode1 = Net('FPGA_MODE0'), Net('FPGA_MODE1')
    tck, tms, tdi, tdo = Net('JTAG_TCK'), Net('JTAG_TMS'), Net('JTAG_TDI'), Net('JTAG_TDO')
    u9[4] += jtagsel_n
    u9[5] += tms
    u9[6] += tck
    u9[7] += tdi
    u9[8] += tdo
    u9[9] += reconfig_n
    u9[87] += mode1
    u9[88] += mode0

    r80 = _r('R80', '4k7', '0402WGF4701TCE', 'C25900')
    r85 = _r('R85', '4k7', '0402WGF4701TCE', 'C25900')
    r81 = _r('R81', '4k7', '0402WGF4701TCE', 'C25900')
    r83 = _r('R83', '1k', '0402WGF1001TCE', 'C11702')
    r84 = _r('R84', '1k', '0402WGF1001TCE', 'C11702')
    v1v8 & r80 & reconfig_n
    v1v8 & r85 & jtagsel_n
    tck & r81 & gnd
    mode0 & r83 & gnd
    mode1 & r84 & gnd

    # JTAG header J4: 1 VREF(+1V8), 2 TCK, 3 TMS, 4 TDI, 5 TDO, 6 GND
    j4 = Part('Connector_Generic', 'Conn_01x06', ref='J4', value='1x6',
              footprint='Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',
              MPN='PZ254V-11-06P', LCSC='C492405')
    j4[1] += v1v8
    j4[2] += tck
    j4[3] += tms
    j4[4] += tdi
    j4[5] += tdo
    j4[6] += gnd

    # Unused bank-3 user I/O (LVCMOS18, reserved for debug): intentionally NC
    for n in (3, 10, 11, 13, 14, 15, 16, 79, 80, 81, 82, 83, 84, 85, 86):
        u9[n] += NC
