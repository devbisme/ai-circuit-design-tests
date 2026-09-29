"""USB Bridge — FT232H USB 2.0 HS to synchronous-245 FIFO (U10) with 93LC56B config EEPROM (U11)
Block from: architecture/block_diagram.md (usb_bridge)
Interface nets: USB_DP, USB_DN, FT_D0..FT_D7, FT_RXF_N, FT_TXE_N, FT_RD_N, FT_WR_N, FT_SIWU_N,
                FT_CLKOUT, FT_OE_N, V5, GND
Power config (driver decision, Adafruit FT232H reference design): VREGIN <- V5; VCCD is the
internal 3.3 V regulator OUTPUT and feeds local net FT_3V3 (VCCIO x3, VPHY/VPLL via ferrites,
EEPROM, RESET# pull-up). VCCCORE (1.8 V out) and VCCA are decouple-only.
"""
from skidl import *

# U10 sync-245 FIFO mapping (UNVERIFIED keystone: FTDI family convention, DS_FT232H not obtained)
ADBUS_D = ('ADBUS0', 'ADBUS1', 'ADBUS2', 'ADBUS3',
           'ADBUS4', 'ADBUS5', 'ADBUS6', 'ADBUS7')   # FT_D0..FT_D7
RXF_PIN, TXE_PIN, RD_PIN, WR_PIN = 'ACBUS0', 'ACBUS1', 'ACBUS2', 'ACBUS3'
SIWU_PIN, CLKOUT_PIN, OE_PIN = 'ACBUS4', 'ACBUS5', 'ACBUS6'
ACBUS_NC = ('ACBUS7', 'ACBUS8', 'ACBUS9')             # unused in sync-245 mode

_C0402 = 'Capacitor_SMD:C_0402_1005Metric'
_C0603 = 'Capacitor_SMD:C_0603_1608Metric'
_R0603 = 'Resistor_SMD:R_0603_1608Metric'


def _cap(ref, value, fp, a, b):
    c = Part('Device', 'C', ref=ref, value=value, footprint=fp)
    c[1] += a
    c[2] += b
    return c


@SubCircuit
def usb_bridge(usb_dp, usb_dn, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_siwu_n,
               ft_clkout, ft_oe_n, v5, gnd):
    """FT232H in synchronous-245 FIFO mode.

    usb_dp/usb_dn: USB HS data pair (bidirectional, to the ESD/connector block).
    ft_d: 8-net bus, index 0 = D0 (bidirectional). ft_rxf_n, ft_txe_n, ft_clkout: driven by
    U10. ft_rd_n, ft_wr_n, ft_siwu_n, ft_oe_n: sensed by U10 (driven by the FPGA).
    v5: VREGIN supply (consumed). gnd: ground.
    Local nets: FT_3V3 (VCCD regulator output, .drive = POWER), FT_VPHY, FT_VPLL, FT_VCORE,
    FT_VCCA, FT_REF, FT_RESET_N, FT_XCSI, FT_XCSO, FT_EECS, FT_EECLK, FT_EEDATA, FT_EEDO.
    """
    u10 = Part('Interface_USB', 'FT232H', ref='U10', value='FT232HL-REEL',
               footprint='Package_QFP:LQFP-48_7x7mm_P0.5mm')
    u11 = Part('dual_adc_usb', '93LC56BT-I_OT', ref='U11', value='93LC56BT-I/OT',
               footprint='Package_TO_SOT_SMD:SOT-23-6')
    y1 = Part('Device', 'Crystal_GND24', ref='Y1', value='X322512MSB4SI',
              footprint='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm')

    # ---- Local nets --------------------------------------------------------
    ft_3v3 = Net('FT_3V3')
    ft_3v3.drive = POWER          # VCCD is the FT232H internal 3.3 V regulator output
    ft_vphy = Net('FT_VPHY')
    ft_vphy.drive = POWER         # FT_3V3 through FB3 (passive ferrite hides the source)
    ft_vpll = Net('FT_VPLL')
    ft_vpll.drive = POWER         # FT_3V3 through FB4
    ft_vcore = Net('FT_VCORE')
    ft_vcca = Net('FT_VCCA')
    ft_ref = Net('FT_REF')
    ft_reset_n = Net('FT_RESET_N')
    ft_xcsi = Net('FT_XCSI')
    ft_xcso = Net('FT_XCSO')
    ft_eecs = Net('FT_EECS')
    ft_eeclk = Net('FT_EECLK')
    ft_eedata = Net('FT_EEDATA')
    ft_eedo = Net('FT_EEDO')

    # ---- U10 power ---------------------------------------------------------
    u10['VREGIN'] += v5
    u10['VCCD'] += ft_3v3
    u10[12, 24, 46] += ft_3v3                  # VCCIO x3 -> 3.3 V I/O (matches FPGA bank 1)
    u10['VPHY'] += ft_vphy
    u10['VPLL'] += ft_vpll
    u10['VCCCORE'] += ft_vcore                 # 1.8 V core regulator output, decouple only
    u10['VCCA'] += ft_vcca                     # own cap, NOT tied to VCCCORE
    u10[4, 9, 41] += gnd                       # AGND
    u10[10, 11, 22, 23, 35, 36, 47, 48] += gnd  # GND
    u10['TEST'] += gnd

    # VPHY / VPLL ferrite filters from FT_3V3
    fb3 = Part('Device', 'FerriteBead', ref='FB3', value='600R',
               footprint='Inductor_SMD:L_0603_1608Metric')
    fb4 = Part('Device', 'FerriteBead', ref='FB4', value='600R',
               footprint='Inductor_SMD:L_0603_1608Metric')
    fb3[1] += ft_3v3
    fb3[2] += ft_vphy
    fb4[1] += ft_3v3
    fb4[2] += ft_vpll
    _cap('C57', '10uF', _C0603, ft_vphy, gnd)
    _cap('C58', '100nF', _C0402, ft_vphy, gnd)
    _cap('C59', '10uF', _C0603, ft_vpll, gnd)
    _cap('C60', '100nF', _C0402, ft_vpll, gnd)

    # Decoupling
    _cap('C49', '100nF', _C0402, v5, gnd)          # VREGIN
    _cap('C50', '100nF', _C0402, ft_3v3, gnd)      # VCCIO pin 12
    _cap('C51', '100nF', _C0402, ft_3v3, gnd)      # VCCIO pin 24
    _cap('C52', '100nF', _C0402, ft_3v3, gnd)      # VCCIO pin 46
    _cap('C53', '100nF', _C0402, ft_vcca, gnd)     # VCCA
    _cap('C54', '100nF', _C0402, ft_vcore, gnd)    # VCCCORE
    _cap('C55', '4.7uF', _C0603, ft_vcore, gnd)    # VCCCORE bulk
    _cap('C56', '4.7uF', _C0603, ft_3v3, gnd)      # VCCD regulator output bulk

    # ---- REF, RESET# -------------------------------------------------------
    r25 = Part('Device', 'R', ref='R25', value='12k', footprint=_R0603)  # 1 % part (C22790) per BOM
    u10['REF'] += ft_ref
    r25[1] += ft_ref
    r25[2] += gnd
    r26 = Part('Device', 'R', ref='R26', value='10k', footprint=_R0603)
    u10['~{RESET}'] += ft_reset_n
    r26[1] += ft_reset_n
    r26[2] += ft_3v3

    # ---- 12 MHz crystal ----------------------------------------------------
    u10['XCSI'] += ft_xcsi
    u10['XCSO'] += ft_xcso
    y1[1] += ft_xcsi
    y1[3] += ft_xcso
    y1[2, 4] += gnd                                # case pads
    _cap('C47', '33pF', _C0402, ft_xcsi, gnd)
    _cap('C48', '33pF', _C0402, ft_xcso, gnd)

    # ---- Config EEPROM (93LC56B, x16) -------------------------------------
    u10['EECS'] += ft_eecs
    u10['EECLK'] += ft_eeclk
    u10['EEDATA'] += ft_eedata
    u11['CS'] += ft_eecs
    u11['CLK'] += ft_eeclk
    u11['DI'] += ft_eedata
    u11['DO'] += ft_eedo
    r27 = Part('Device', 'R', ref='R27', value='2.2k', footprint=_R0603)
    r27[1] += ft_eedo
    r27[2] += ft_eedata
    u11['VCC'] += ft_3v3
    u11['VSS'] += gnd

    # ---- USB ---------------------------------------------------------------
    u10['DP'] += usb_dp
    u10['DM'] += usb_dn

    # ---- Sync-245 FIFO interface -------------------------------------------
    for i, pin in enumerate(ADBUS_D):
        u10[pin] += ft_d[i]
    u10[RXF_PIN] += ft_rxf_n
    u10[TXE_PIN] += ft_txe_n
    u10[RD_PIN] += ft_rd_n
    u10[WR_PIN] += ft_wr_n
    u10[SIWU_PIN] += ft_siwu_n
    u10[CLKOUT_PIN] += ft_clkout
    u10[OE_PIN] += ft_oe_n
    for pin in ACBUS_NC:
        u10[pin] += NC
