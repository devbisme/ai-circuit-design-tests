"""USB Bridge — FT232H Hi-Speed USB to 245 sync FIFO bridge with 93LC56B config EEPROM and 12 MHz crystal
Block from: architecture/block_diagram.md
Interface nets: USB_DP, USB_DM, FT_D[0..7], FT_RXF_N, FT_TXE_N, FT_RD_N, FT_WR_N, FT_CLKOUT, FT_OE_N, VBUS_SW, +3V3D, GND
"""
from skidl import *

_R = 'Resistor_SMD:R_0402_1005Metric'
_C = 'Capacitor_SMD:C_0402_1005Metric'
_C0603 = 'Capacitor_SMD:C_0603_1608Metric'


@SubCircuit
def usb_bridge(usb_dp, usb_dm, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_clkout, ft_oe_n, vbus_sw, v3v3d, gnd):
    """U10 FT232HL in 245 synchronous FIFO mode, VREGIN 5 V mode (DS_FT232H Fig 6.1, Table 3.1 note):
    VREGIN <- VBUS_SW; VCCD is the internal 3.3 V LDO OUTPUT (net FT_VCCD) feeding VPLL, VPHY,
    the EEPROM and the EEDO pull-up. VCCIO x3 stay on +3V3D (FIFO I/O to the 3.3 V FPGA bank).
    ft_d is an 8-bit Bus (ADBUS0..7). ACBUS0..6 = RXF#, TXE#, RD#, WR#, SIWU# (tied high), CLKOUT, OE#.
    U11 93LC56B (SOT-23-6) per DS_FT232H Table 3.3. Y2 12 MHz with C110/C111 33 pF.
    Refs: U10, U11, Y2, R100-R103, C100-C111."""
    ft_vcccore = Net('FT_VCCCORE')
    ft_vccd = Net('FT_VCCD')
    ft_xi = Net('FT_XI')
    ft_xo = Net('FT_XO')
    ft_ref = Net('FT_REF')
    ft_reset_n = Net('FT_RESET_N')
    ft_eecs = Net('FT_EECS')
    ft_eeclk = Net('FT_EECLK')
    ft_eedata = Net('FT_EEDATA')
    ft_eedo = Net('FT_EEDO')

    u10 = Part('Interface_USB', 'FT232H', ref='U10', value='FT232HL-REEL',
               footprint='Package_QFP:LQFP-48_7x7mm_P0.5mm',
               MPN='FT232HL-REEL', LCSC='C51997')
    # Symbol pin-type corrections (KiCad lib types vs DS_FT232H):
    #  - VCCA and VCCCORE are both POWER-OUT; VCCA is fed from the same internal 1.8 V LDO
    #    node, so treat it as POWER-IN to avoid a false out<->out conflict on FT_VCCCORE.
    #  - EECS/EECLK are FT232H outputs to the EEPROM but typed INPUT in the symbol.
    u10['VCCA'].func = Pin.types.PWRIN
    u10['EECS'].func = Pin.types.OUTPUT
    u10['EECLK'].func = Pin.types.OUTPUT
    #  - VCCD is an OUTPUT (3.3 V LDO) when VREGIN = 5 V; symbol types it POWER-IN.
    u10['VCCD'].func = Pin.types.PWROUT
    # Supplies (5 V VREGIN mode, Fig 6.1): VCCD = LDO output, never tied to +3V3D
    u10['VREGIN'] += vbus_sw
    u10['VCCD', 'VPLL', 'VPHY'] += ft_vccd
    u10['VCCIO'] += v3v3d
    u10['VCCCORE', 'VCCA'] += ft_vcccore
    u10['GND', 'AGND', 'TEST'] += gnd
    # USB
    u10['DP'] += usb_dp
    u10['DM'] += usb_dm
    # Crystal, reference, reset
    u10['XCSI'] += ft_xi
    u10['XCSO'] += ft_xo
    u10['REF'] += ft_ref
    u10['~{RESET}'] += ft_reset_n
    # EEPROM interface
    u10['EECS'] += ft_eecs
    u10['EECLK'] += ft_eeclk
    u10['EEDATA'] += ft_eedata
    # 245 sync FIFO
    for i in range(8):
        u10['ADBUS{}'.format(i)] += ft_d[i]
    u10['ACBUS0'] += ft_rxf_n
    u10['ACBUS1'] += ft_txe_n
    u10['ACBUS2'] += ft_rd_n
    u10['ACBUS3'] += ft_wr_n
    u10['ACBUS4'] += v3v3d      # SIWU# unused -> tied high
    u10['ACBUS5'] += ft_clkout
    u10['ACBUS6'] += ft_oe_n
    u10['ACBUS7', 'ACBUS8', 'ACBUS9'] += NC

    # Config EEPROM (x16, SOT-23-6)
    u11 = Part('Memory_EEPROM', '93LCxxBxxOT', ref='U11', value='93LC56BT-I/OT',
               footprint='Package_TO_SOT_SMD:SOT-23-6',
               MPN='93LC56BT-I/OT', LCSC='C190271')
    u11['VCC'] += ft_vccd      # powered with the FT232H, before +3V3D (EN_3V3 delay)
    u11['GND'] += gnd
    u11['CS'] += ft_eecs
    u11['CLK'] += ft_eeclk
    u11['DI'] += ft_eedata
    u11['DO'] += ft_eedo

    r100 = Part('Device', 'R', ref='R100', value='12k', footprint=_R, MPN='0402WGF1202TCE', LCSC='C25752')
    r101 = Part('Device', 'R', ref='R101', value='10k', footprint=_R, MPN='0402WGF1002TCE', LCSC='C25744')
    r102 = Part('Device', 'R', ref='R102', value='10k', footprint=_R, MPN='0402WGF1002TCE', LCSC='C25744')
    r103 = Part('Device', 'R', ref='R103', value='2.2k', footprint=_R, MPN='0402WGF2201TCE', LCSC='C25879')
    ft_ref & r100 & gnd
    v3v3d & r101 & ft_reset_n
    ft_vccd & r102 & ft_eedo    # DS Table 3.3: EEPROM DO pulled to VCCD
    ft_eedata & r103 & ft_eedo

    # 12 MHz crystal and load caps
    y2 = Part('Device', 'Crystal_GND24', ref='Y2', value='12MHz',
              footprint='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',
              MPN='X322512MSB4SI', LCSC='C9002')
    y2[1] += ft_xi
    y2[3] += ft_xo
    y2[2, 4] += gnd
    c110 = Part('Device', 'C', ref='C110', value='33pF', footprint=_C, MPN='0402CG330J500NT', LCSC='C1562')
    c111 = Part('Device', 'C', ref='C111', value='33pF', footprint=_C, MPN='0402CG330J500NT', LCSC='C1562')
    ft_xi & c110 & gnd
    ft_xo & c111 & gnd

    # Decoupling (Fig 6.1): 100 nF per supply pin, 4.7 uF bulk on VREGIN.
    #  C100 VREGIN | C101 VCCD | C102-C104 VCCIO x3 | C105 VPLL | C106 VPHY | C107 U11 VCC
    cap_rail = {100: vbus_sw, 101: ft_vccd, 102: v3v3d, 103: v3v3d, 104: v3v3d,
                105: ft_vccd, 106: ft_vccd, 107: ft_vccd}
    for n, rail in cap_rail.items():
        c = Part('Device', 'C', ref='C{}'.format(n), value='100nF', footprint=_C,
                 MPN='CL05B104KO5NNNC', LCSC='C1525')
        rail & c & gnd
    c108 = Part('Device', 'C', ref='C108', value='4.7uF', footprint=_C0603,
                MPN='CL10A475KO8NNNC', LCSC='C19666')   # 16 V X5R, VREGIN bulk
    vbus_sw & c108 & gnd
    c109 = Part('Device', 'C', ref='C109', value='100nF', footprint=_C,
                MPN='CL05B104KO5NNNC', LCSC='C1525')
    ft_vcccore & c109 & gnd
