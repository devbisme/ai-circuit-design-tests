"""USB FIFO — FT232H USB 2.0 HS bridge in 245 synchronous FIFO mode, 3.3 V-only supply
Block from: architecture/block_diagram.md (connections: architecture/net_plan.md Block 8)
Interface nets: USB_DP, USB_DM, FT_D0..7, FT_RXF_N, FT_TXE_N, FT_RD_N, FT_WR_N, FT_OE_N,
                FT_CLKOUT, +3V3, GND
"""
from skidl import *

# Footprint / MPN strings (sourcing/sourced_bom.csv, verbatim)
_FP_C0402 = 'Capacitor_SMD:C_0402_1005Metric'
_FP_C0603 = 'Capacitor_SMD:C_0603_1608Metric'
_FP_R0402 = 'Resistor_SMD:R_0402_1005Metric'
_FP_FB = 'Inductor_SMD:L_0603_1608Metric'

_MPN_100N = 'CL05B104KB54PNC'
_LCSC_100N = 'C307331'
_MPN_4U7 = 'CL10A475KO8NNNC'
_LCSC_4U7 = 'C19666'
_MPN_18P = '0402CG180J500NT'
_LCSC_18P = 'C1549'
_MPN_10K = '0402WGF1002TCE'
_LCSC_10K = 'C25744'


def _cap(ref, value, mpn, lcsc, fp=_FP_C0402):
    c = Part('Device', 'C', ref=ref, value=value, footprint=fp)
    c.fields['MPN'] = mpn
    c.fields['LCSC'] = lcsc
    return c


def _res(ref, value, mpn, lcsc):
    r = Part('Device', 'R', ref=ref, value=value, footprint=_FP_R0402)
    r.fields['MPN'] = mpn
    r.fields['LCSC'] = lcsc
    return r


@SubCircuit
def usb_fifo(usb_dp, usb_dm, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_oe_n, ft_clkout,
             v3v3, gnd):
    """FT232HL (U901) USB<->FPGA bridge with 93LC56B config EEPROM (U902) and 12 MHz crystal.

    Inputs/outputs:
      usb_dp/usb_dm : USB HS pair from usb_c_input (90 ohm diff), bidirectional.
      ft_d          : 8-wide Bus (index 0 = LSB), bidirectional FIFO data, ADBUS0-7.
      ft_rxf_n, ft_txe_n : driven by FT232H (ACBUS0/1), sensed by FPGA.
      ft_rd_n, ft_wr_n, ft_oe_n : driven by FPGA, 10k pull-ups here (idle high while
                      FPGA unconfigured).
      ft_clkout     : 60 MHz CLKOUT (ACBUS5) via R910 22R series (source termination).
      v3v3, gnd     : consumed only.
    Assumptions: 3.3 V-only configuration (FT_000288 Fig 6.3): VREGIN and VCCD on +3V3,
    VCCCORE/VCCA are internal 1.8 V regulator outputs with 0.1 uF each. VPHY/VPLL from
    +3V3 through FB901 (+3V3_PHY). ACBUS7 PWRSAV# pulled high (R912); EEPROM option
    "suspend on ACBUS7 low" must stay off. Crystal Y901 pinout assumed 1/3 = crystal,
    2/4 = GND (2520 convention, UNVERIFIED - no datasheet); CL 12 pF -> 18 pF load caps.
    """
    # ---- U901 FT232HL ----
    u = Part('Interface_USB', 'FT232H', ref='U901', value='FT232HL',
             footprint='Package_QFP:LQFP-48_7x7mm_P0.5mm')
    u.fields['MPN'] = 'FT232HL'
    u.fields['LCSC'] = 'C51997'

    # Ground: AGND 4, 9, 41; GND 10, 11, 22, 23, 35, 36, 47, 48; TEST 42 -> GND
    for p in (4, 9, 41, 10, 11, 22, 23, 35, 36, 47, 48, 42):
        gnd += u[p]

    # +3V3: VCCIO 12, 24, 46; VCCD 39; VREGIN 40
    for p in (12, 24, 46, 39, 40):
        v3v3 += u[p]
    for ref in ('C906', 'C907', 'C908', 'C910', 'C913'):
        c = _cap(ref, '100n', _MPN_100N, _LCSC_100N)
        v3v3 += c[1]
        gnd += c[2]
    c909 = _cap('C909', '4.7u', _MPN_4U7, _LCSC_4U7, _FP_C0603)
    v3v3 += c909[1]
    gnd += c909[2]

    # +3V3_PHY: +3V3 -> FB901 -> VPHY 3, VPLL 8
    phy = Net('+3V3_PHY')
    phy.drive = POWER            # ferrite output is the source for VPHY/VPLL power_in pins
    flg = Part('power', 'PWR_FLAG', ref='#FLG901')
    phy += flg[1]
    fb = Part('Device', 'FerriteBead', ref='FB901', value='600R', footprint=_FP_FB)
    fb.fields['MPN'] = 'BLM18KG601SN1D'
    fb.fields['LCSC'] = 'C85833'
    v3v3 += fb[1]
    phy += fb[2]
    phy += u[3], u[8]
    c903 = _cap('C903', '4.7u', _MPN_4U7, _LCSC_4U7, _FP_C0603)
    phy += c903[1]
    gnd += c903[2]
    for ref in ('C904', 'C905'):
        c = _cap(ref, '100n', _MPN_100N, _LCSC_100N)
        phy += c[1]
        gnd += c[2]

    # Internal 1.8 V regulator outputs: VCCCORE 38, VCCA 37 -> 0.1 uF each
    vcore = Net('FT_VCORE')
    vcca = Net('FT_VCCA')
    vcore += u[38]
    vcca += u[37]
    c911 = _cap('C911', '100n', _MPN_100N, _LCSC_100N)
    vcore += c911[1]
    gnd += c911[2]
    c912 = _cap('C912', '100n', _MPN_100N, _LCSC_100N)
    vcca += c912[1]
    gnd += c912[2]

    # ---- USB ----
    usb_dp += u[7]
    usb_dm += u[6]

    # ---- REF: 12k 1 % to GND ----
    ft_ref = Net('FT_REF')
    r901 = _res('R901', '12k', '0402WGF1202TCE', 'C25752')
    ft_ref += u[5], r901[1]
    gnd += r901[2]

    # ---- RESET#: 10k pull-up ----
    rst = Net('FT_RESET_N')
    rst += u[34]
    r902 = _res('R902', '10k', _MPN_10K, _LCSC_10K)
    rst += r902[1]
    v3v3 += r902[2]

    # ---- 12 MHz crystal Y901, C901/C902 18 pF ----
    xi = Net('FT_XI')
    xo = Net('FT_XO')
    xi += u[1]
    xo += u[2]
    y = Part('Device', 'Crystal_GND24', ref='Y901', value='12MHz',
             footprint='Crystal:Crystal_SMD_2520-4Pin_2.5x2.0mm')
    y.fields['MPN'] = 'TXM12M0004252FBCEO00T'
    y.fields['LCSC'] = 'C284155'
    xi += y[1]
    xo += y[3]
    gnd += y[2], y[4]
    c901 = _cap('C901', '18p', _MPN_18P, _LCSC_18P)
    xi += c901[1]
    gnd += c901[2]
    c902 = _cap('C902', '18p', _MPN_18P, _LCSC_18P)
    xo += c902[1]
    gnd += c902[2]

    # ---- FIFO data ADBUS0-7 (pins 13-20) ----
    for i in range(8):
        ft_d[i] += u[13 + i]

    # ---- FIFO control ACBUS ----
    ft_rxf_n += u[21]            # ACBUS0 RXF#
    ft_txe_n += u[25]            # ACBUS1 TXE#
    ft_rd_n += u[26]             # ACBUS2 RD#
    ft_wr_n += u[27]             # ACBUS3 WR#
    siwu = Net('FT_SIWU_N')
    siwu += u[28]                # ACBUS4 SIWU#
    clk_s = Net('FT_CLKOUT_S')
    clk_s += u[29]               # ACBUS5 CLKOUT
    ft_oe_n += u[30]             # ACBUS6 OE#
    pwrsav = Net('FT_PWRSAV_N')
    pwrsav += u[31]              # ACBUS7 PWRSAV#
    u[32] += NC                  # ACBUS8 unused
    u[33] += NC                  # ACBUS9 unused

    # Pull-ups R907 RD#, R908 WR#, R909 SIWU#, R911 OE#, R912 PWRSAV#
    for ref, net in (('R907', ft_rd_n), ('R908', ft_wr_n), ('R909', siwu),
                     ('R911', ft_oe_n), ('R912', pwrsav)):
        r = _res(ref, '10k', _MPN_10K, _LCSC_10K)
        net += r[1]
        v3v3 += r[2]

    # CLKOUT 22R series termination
    r910 = _res('R910', '22', '0402WGF220JTCE', 'C25092')
    clk_s += r910[1]
    ft_clkout += r910[2]

    # ---- 93LC56B EEPROM U902 (SOT-23-6: DO 1, GND 2, DI 3, CLK 4, CS 5, VCC 6) ----
    ee = Part('Memory_EEPROM', '93LCxxBxxOT', ref='U902', value='93LC56BT-I/OT',
              footprint='Package_TO_SOT_SMD:SOT-23-6')
    ee.fields['MPN'] = '93LC56BT-I/OT'
    ee.fields['LCSC'] = 'C190271'
    v3v3 += ee['VCC']
    gnd += ee['GND']
    ee_cs = Net('EE_CS')
    ee_clk = Net('EE_CLK')
    ee_data = Net('EE_DATA')
    ee_do = Net('EE_DO')
    ee_cs += u[45], ee['CS']
    ee_clk += u[44], ee['CLK']
    ee_data += u[43], ee['DI']
    ee_do += ee['DO']
    r903 = _res('R903', '2.2k', '0402WGF2201TCE', 'C25879')
    ee_do += r903[1]
    ee_data += r903[2]
    for ref, net in (('R904', ee_cs), ('R905', ee_clk), ('R906', ee_data)):
        r = _res(ref, '10k', _MPN_10K, _LCSC_10K)
        net += r[1]
        v3v3 += r[2]
