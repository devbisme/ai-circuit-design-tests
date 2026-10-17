"""FPGA — Spartan-6 XC6SLX9 + W25Q32 config flash + JTAG + status LEDs + trigger header
Block from: architecture/block_diagram.md (connections: architecture/net_plan.md Block 9)
Interface nets: CLK10_FPGA, DA0..DA11, DB0..DB11, ADC_DVA, ADC_OVRA, ADC_OVRB, ADC_SEL,
                ADC_SEN, ADC_SCLK, ADC_SDATA, SD_DQ0..15, SD_A0..11, SD_BA0..1, SD_CLK,
                SD_CKE, SD_CS_N, SD_RAS_N, SD_CAS_N, SD_WE_N, SD_LDQM, SD_UDQM, FT_D0..7,
                FT_RXF_N, FT_TXE_N, FT_RD_N, FT_WR_N, FT_OE_N, FT_CLKOUT, +3V3, +1V2, GND
"""
from skidl import *

# Footprint / MPN strings (sourcing/sourced_bom.csv, verbatim)
_FP_C0402 = 'Capacitor_SMD:C_0402_1005Metric'
_FP_C0603 = 'Capacitor_SMD:C_0603_1608Metric'
_FP_R0402 = 'Resistor_SMD:R_0402_1005Metric'
_FP_LED = 'LED_SMD:LED_0603_1608Metric'
_FP_FPGA = 'Package_QFP:TQFP-144_20x20mm_P0.5mm'
_FP_FLASH = 'Package_SO:SOIC-8_5.3x5.3mm_P1.27mm'
_FP_J6 = 'Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical'
_FP_J3 = 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical'

_MPN_100N = 'CL05B104KB54PNC'
_LCSC_100N = 'C307331'
_MPN_4U7 = 'CL10A475KO8NNNC'
_LCSC_4U7 = 'C19666'
_MPN_R = {'4.7k': '0402WGF4701TCE', '10k': '0402WGF1002TCE', '330': '0402WGF3300TCE',
          '1k': '0402WGF1001TCE', '100': '0402WGF1000TCE'}
_LCSC_R = {'4.7k': 'C25900', '10k': 'C25744', '330': 'C25104',
           '1k': 'C11702', '100': 'C25076'}

# ---- U1001 pin map (UG385 Table 2-2, TQG144; LX4/LX9 identical) ----
_VCCINT = [19, 28, 52, 89, 128]                                  # +1V2
_VCCAUX = [20, 36, 53, 90, 129]                                  # +3V3
_VCCO = [4, 18, 31, 42, 63, 76, 86, 103, 122, 125, 135]          # +3V3, all banks
_GND = [3, 13, 25, 49, 54, 68, 77, 91, 96, 108, 113, 130, 136]

# Bank 3 (left side): ADC data + both clocks (GCLK P-side pins)
_P_CLK10 = 15        # IO_L44P_GCLK21_3
_P_DVA = 22          # IO_L42P_GCLK25_TRDY2_3
_P_DA = [1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16]                # DA0..DA11
_P_DB = [17, 21, 23, 24, 26, 27, 29, 30, 32, 33, 34, 35]         # DB0..DB11

# Bank 2 (bottom): ADC overrange + FT232H FIFO (FT_CLKOUT on GCLK)
_P_OVRA, _P_OVRB = 40, 41
_P_FT_CLKOUT = 51    # IO_L31P_GCLK31_D14_2
_P_FT_D = [43, 44, 45, 46, 47, 48, 50, 55]                       # FT_D0..FT_D7
_P_FT_RXF, _P_FT_TXE, _P_FT_RD, _P_FT_WR, _P_FT_OE = 57, 58, 59, 61, 62

# Bank 0 (top): SDRAM data + control
_P_SD_DQ = [111, 112, 114, 115, 116, 117, 118, 119, 120, 121, 123, 124, 126, 127, 131, 132]
_P_SD_CLK, _P_SD_CKE, _P_SD_CS, _P_SD_RAS = 133, 134, 137, 138
_P_SD_CAS, _P_SD_WE, _P_SD_LDQM, _P_SD_UDQM, _P_SD_BA0 = 139, 140, 141, 142, 143

# Bank 1 (right, near bank-0 corner): SDRAM address + slow I/O
_P_SD_A = [105, 104, 102, 101, 100, 99, 98, 97, 95, 94, 93, 92]  # SD_A0..SD_A11
_P_SD_BA1 = 88
_P_ADC_SEL, _P_ADC_SEN, _P_ADC_SCLK, _P_ADC_SDATA = 87, 85, 84, 83
_P_LED_ARMED, _P_LED_TRIG, _P_TRIG_IN, _P_TRIG_OUT = 82, 81, 80, 79

# Dedicated / configuration
_P_PROG_B, _P_CSO_B, _P_INIT_B, _P_M1 = 37, 38, 39, 60
_P_MOSI, _P_DIN, _P_M0, _P_CCLK = 64, 65, 69, 70
_P_DONE, _P_CMPCS_B, _P_SUSPEND, _P_HSWAPEN = 71, 72, 73, 144
_P_TDO, _P_TMS, _P_TCK, _P_TDI = 106, 107, 109, 110

_P_SPARE = [56, 66, 67, 74, 75, 78]                              # unused user I/O -> NC


def _cap(ref, value, mpn, lcsc, fp):
    c = Part('Device', 'C', ref=ref, value=value, footprint=fp)
    c.fields['MPN'] = mpn
    c.fields['LCSC'] = lcsc
    return c


def _res(ref, value):
    r = Part('Device', 'R', ref=ref, value=value, footprint=_FP_R0402)
    r.fields['MPN'] = _MPN_R[value]
    r.fields['LCSC'] = _LCSC_R[value]
    return r


@SubCircuit
def fpga(clk10_fpga, da, db, adc_dva, adc_ovra, adc_ovrb, adc_sel, adc_sen, adc_sclk,
         adc_sdata, sd_dq, sd_a, sd_ba, sd_clk, sd_cke, sd_cs_n, sd_ras_n, sd_cas_n,
         sd_we_n, sd_ldqm, sd_udqm, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_oe_n,
         ft_clkout, v3v3, v1v2, gnd):
    """Spartan-6 XC6SLX9-2TQG144C with Master-SPI config flash, JTAG, LEDs and trigger I/O.

    Buses: da/db 12-wide, sd_dq 16, sd_a 12, sd_ba 2, ft_d 8 (index 0 = LSB).
    Clocks: clk10_fpga, adc_dva, ft_clkout land on GCLK pins.
    Config: M[1:0] = 01 (Master SPI), HSWAPEN high (pull-ups off), SUSPEND to GND,
    CMPCS_B left NC (UG385 p22). All VCCO = +3V3, VCCAUX = +3V3, VCCINT = +1V2.
    All U1001 decoupling (0.1 uF per supply pin + bulk) is inside this block.
    """
    # ---- U1001 FPGA ----
    u = Part('FPGA_Xilinx_Spartan6', 'XC6SLX4-TQG144', ref='U1001',
             value='XC6SLX9-2TQG144C', footprint=_FP_FPGA)
    u.fields['MPN'] = 'XC6SLX9-2TQG144C'
    u.fields['LCSC'] = 'C27408'

    # Supplies + one 0.1 uF per supply pin: C1001-C1005 VCCINT, C1006-C1010 VCCAUX,
    # C1011-C1021 VCCO
    cref = 1001
    for p in _VCCINT:
        u[p] += v1v2
        c = _cap(f'C{cref}', '100n', _MPN_100N, _LCSC_100N, _FP_C0402)
        c[1] += v1v2
        c[2] += gnd
        cref += 1
    for p in _VCCAUX + _VCCO:
        u[p] += v3v3
        c = _cap(f'C{cref}', '100n', _MPN_100N, _LCSC_100N, _FP_C0402)
        c[1] += v3v3
        c[2] += gnd
        cref += 1
    for p in _GND:
        u[p] += gnd

    # Bulk: C1023 on +1V2, C1024/C1025 on +3V3
    for ref, rail in (('C1023', v1v2), ('C1024', v3v3), ('C1025', v3v3)):
        c = _cap(ref, '4.7u', _MPN_4U7, _LCSC_4U7, _FP_C0603)
        c[1] += rail
        c[2] += gnd

    # ---- ADC interface (bank 3 + overrange in bank 2, control in bank 1) ----
    u[_P_CLK10] += clk10_fpga
    u[_P_DVA] += adc_dva
    for i, p in enumerate(_P_DA):
        u[p] += da[i]
    for i, p in enumerate(_P_DB):
        u[p] += db[i]
    u[_P_OVRA] += adc_ovra
    u[_P_OVRB] += adc_ovrb
    u[_P_ADC_SEL] += adc_sel
    u[_P_ADC_SEN] += adc_sen
    u[_P_ADC_SCLK] += adc_sclk
    u[_P_ADC_SDATA] += adc_sdata

    # ---- SDRAM interface (banks 0 + 1) ----
    for i, p in enumerate(_P_SD_DQ):
        u[p] += sd_dq[i]
    for i, p in enumerate(_P_SD_A):
        u[p] += sd_a[i]
    u[_P_SD_BA0] += sd_ba[0]
    u[_P_SD_BA1] += sd_ba[1]
    u[_P_SD_CLK] += sd_clk
    u[_P_SD_CKE] += sd_cke
    u[_P_SD_CS] += sd_cs_n
    u[_P_SD_RAS] += sd_ras_n
    u[_P_SD_CAS] += sd_cas_n
    u[_P_SD_WE] += sd_we_n
    u[_P_SD_LDQM] += sd_ldqm
    u[_P_SD_UDQM] += sd_udqm

    # ---- FT232H sync FIFO (bank 2, same bank as FT_CLKOUT GCLK) ----
    u[_P_FT_CLKOUT] += ft_clkout
    for i, p in enumerate(_P_FT_D):
        u[p] += ft_d[i]
    u[_P_FT_RXF] += ft_rxf_n
    u[_P_FT_TXE] += ft_txe_n
    u[_P_FT_RD] += ft_rd_n
    u[_P_FT_WR] += ft_wr_n
    u[_P_FT_OE] += ft_oe_n

    # ---- Configuration straps / status (net plan CFG_* rows) ----
    cfg_prog = Net('CFG_PROG_N')
    cfg_init = Net('CFG_INIT_N')
    cfg_done = Net('CFG_DONE')
    cfg_m0 = Net('CFG_M0')
    cfg_m1 = Net('CFG_M1')
    cfg_hswap = Net('CFG_HSWAPEN')
    u[_P_PROG_B] += cfg_prog
    u[_P_INIT_B] += cfg_init
    u[_P_DONE] += cfg_done
    u[_P_M0] += cfg_m0
    u[_P_M1] += cfg_m1
    u[_P_HSWAPEN] += cfg_hswap
    u[_P_SUSPEND] += gnd
    u[_P_CMPCS_B] += NC

    for ref, val, net, rail in (('R1004', '4.7k', cfg_prog, v3v3),
                                ('R1005', '4.7k', cfg_init, v3v3),
                                ('R1006', '330', cfg_done, v3v3),
                                ('R1009', '1k', cfg_m0, v3v3),
                                ('R1008', '1k', cfg_m1, gnd),
                                ('R1010', '1k', cfg_hswap, v3v3)):
        r = _res(ref, val)
        r[1] += net
        r[2] += rail

    # ---- U1002 W25Q32 config flash (Master SPI x1) ----
    fl = Part('Memory_Flash', 'W25Q32JVSS', ref='U1002', value='W25Q32JVSSIQ',
              footprint=_FP_FLASH)
    fl.fields['MPN'] = 'W25Q32JVSSIQ'
    fl.fields['LCSC'] = 'C179173'
    cfg_cclk = Net('CFG_CCLK')
    cfg_mosi = Net('CFG_MOSI')
    cfg_din = Net('CFG_DIN')
    cfg_cs = Net('CFG_CS_N')
    fl_wp = Net('FL_WP_N')
    fl_hold = Net('FL_HOLD_N')
    u[_P_CCLK] += cfg_cclk
    u[_P_MOSI] += cfg_mosi
    u[_P_DIN] += cfg_din
    u[_P_CSO_B] += cfg_cs
    fl[6] += cfg_cclk      # CLK
    fl[5] += cfg_mosi      # DI/IO0
    fl[2] += cfg_din       # DO/IO1
    fl[1] += cfg_cs        # /CS
    fl[3] += fl_wp         # /WP/IO2
    fl[7] += fl_hold       # /HOLD/RESET/IO3
    fl[8] += v3v3
    fl[4] += gnd
    for ref, val, net in (('R1001', '4.7k', cfg_cs), ('R1002', '10k', fl_wp),
                          ('R1003', '10k', fl_hold)):
        r = _res(ref, val)
        r[1] += net
        r[2] += v3v3
    c = _cap('C1022', '100n', _MPN_100N, _LCSC_100N, _FP_C0402)
    c[1] += v3v3
    c[2] += gnd

    # ---- J1001 JTAG (Digilent HS2 order: VREF, GND, TCK, TDO, TDI, TMS) ----
    j = Part('Connector_Generic', 'Conn_01x06', ref='J1001', value='Conn_01x06',
             footprint=_FP_J6)
    j.fields['MPN'] = 'PZ254V-11-06P'
    j.fields['LCSC'] = 'C492405'
    jtag_tck = Net('JTAG_TCK')
    jtag_tdo = Net('JTAG_TDO')
    jtag_tdi = Net('JTAG_TDI')
    jtag_tms = Net('JTAG_TMS')
    j[1] += v3v3
    j[2] += gnd
    j[3] += jtag_tck
    j[4] += jtag_tdo
    j[5] += jtag_tdi
    j[6] += jtag_tms
    u[_P_TCK] += jtag_tck
    u[_P_TDO] += jtag_tdo
    u[_P_TDI] += jtag_tdi
    u[_P_TMS] += jtag_tms

    # ---- Status LEDs: FPGA I/O -> 1k -> LED anode, cathode -> GND ----
    for led_ref, r_ref, pin, name in (('D1002', 'R1012', _P_LED_ARMED, 'LED_ARMED'),
                                      ('D1003', 'R1013', _P_LED_TRIG, 'LED_TRIG')):
        n_io = Net(name)
        n_a = Net(name + '_A')
        u[pin] += n_io
        r = _res(r_ref, '1k')
        r[1] += n_io
        r[2] += n_a
        d = Part('Device', 'LED', ref=led_ref, value='LED_Green', footprint=_FP_LED)
        d.fields['MPN'] = 'PSC-1608U52GC-G4'
        d.fields['LCSC'] = 'C22371297'
        d['A'] += n_a
        d['K'] += gnd

    # ---- J1002 trigger header: 1 TRIG_IN, 2 TRIG_OUT, 3 GND ----
    jt = Part('Connector_Generic', 'Conn_01x03', ref='J1002', value='Conn_01x03',
              footprint=_FP_J3)
    jt.fields['MPN'] = 'PZ254V-11-03P'
    jt.fields['LCSC'] = 'C2937625'
    trig_in = Net('TRIG_IN')        # connector side
    trig_in_f = Net('TRIG_IN_F')    # FPGA side
    trig_out = Net('TRIG_OUT')      # connector side
    trig_out_f = Net('TRIG_OUT_F')  # FPGA side
    jt[1] += trig_in
    jt[2] += trig_out
    jt[3] += gnd
    r = _res('R1014', '100')
    r[1] += trig_in
    r[2] += trig_in_f
    r = _res('R1015', '10k')
    r[1] += trig_in
    r[2] += gnd
    r = _res('R1016', '100')
    r[1] += trig_out_f
    r[2] += trig_out
    u[_P_TRIG_IN] += trig_in_f
    u[_P_TRIG_OUT] += trig_out_f

    # ---- Unused user I/O ----
    for p in _P_SPARE:
        u[p] += NC
