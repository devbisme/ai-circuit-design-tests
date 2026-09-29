"""USB Bridge — FT232HL (U13) USB 2.0 HS to 245 synchronous FIFO, config EEPROM, 12 MHz crystal
Block from: architecture/block_diagram.md
Interface nets: USB_DP, USB_DM, FT_D0…FT_D7, FT_RXF_N, FT_TXE_N, FT_RD_N, FT_WR_N, FT_OE_N,
    FT_SIWU_N, FT_CLKOUT, VD_3V3, GND
Net plan: architecture/net_plan.md §1 (FT_VCORE, FT_VPHY) and §7 (usb_bridge).
Parts: sourcing/sourced_bom.md rows U13, U14, Y1, R60–R67, C65–C79, FB8.
"""
from skidl import *

_R_FP = 'Resistor_SMD:R_0402_1005Metric'

# Passive catalogue for this block — single source of truth for value -> (footprint, MPN, LCSC).
_CAPS = {
    '22pF': ('Capacitor_SMD:C_0402_1005Metric', 'GRM1555C2A220JA01D', 'C710855'),
    '100nF': ('Capacitor_SMD:C_0402_1005Metric', 'CL05B104KB54PNC', 'C307331'),
    '4.7uF': ('Capacitor_SMD:C_0603_1608Metric', 'CL10A475KO8NNNC', 'C19666'),
}
_RES = {
    '2.2k': ('0402WGF2201TCE', 'C25879'),
    '10k': ('0402WGF1002TCE', 'C25744'),
    '12k': ('0402WGF1202TCE', 'C25752'),
    '33': ('0402WGF330JTCE', 'C25105'),
}


def _cap(ref, value, a, b):
    """One capacitor between nets a and b."""
    fp, mpn, lcsc = _CAPS[value]
    c = Part('Device', 'C', ref=ref, value=value, footprint=fp, MPN=mpn, LCSC=lcsc)
    a & c & b


def _res(ref, value, a, b):
    """One 0402 resistor between nets a and b."""
    mpn, lcsc = _RES[value]
    r = Part('Device', 'R', ref=ref, value=value, footprint=_R_FP, MPN=mpn, LCSC=lcsc)
    a & r & b


@SubCircuit
def usb_bridge(usb_dp, usb_dm, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_oe_n,
               ft_siwu_n, ft_clkout, vd_3v3, gnd):
    """FT232HL in FT245 synchronous-FIFO mode (60 MHz, 8-bit) with its support circuitry.

    Args:
        usb_dp, usb_dm: USB 2.0 HS pair to J1/U1 (usb_power_in). Bidirectional.
        ft_d: 8-wide bus FT_D0..FT_D7 (ADBUS0..7), bidirectional FIFO data.
        ft_rxf_n, ft_txe_n: FIFO status outputs driven by U13 (ACBUS0, ACBUS1).
        ft_rd_n, ft_wr_n, ft_oe_n, ft_siwu_n: strobes driven by the FPGA into U13
            (ACBUS2, ACBUS3, ACBUS6, ACBUS4).
        ft_clkout: 60 MHz CLKOUT (ACBUS5) through series R66 (33 Ω), driven by this block.
        vd_3v3: 3.3 V digital rail (consumed): VREGIN, VCCD, VCCIO×3, U14, pull-ups, FB8.
        gnd: single ground net (AGND and GND pins).
    Assumptions:
        - 3.3 V-only supply configuration: VREGIN and VCCD both on VD_3V3, VCORE (1.8 V internal
          LDO output) tied to VCCA on local net FT_VCORE.
        - VPHY/VPLL fed from VD_3V3 through FB8 on local net FT_VPHY (driven here as POWER).
        - FIFO mode is selected by the EEPROM contents (U14), programmed via FT_PROG.
    """
    # --- Local nets (net_plan.md §1, §7) ---
    ft_vcore = Net('FT_VCORE')      # 1.8 V, U13 internal LDO output (VCORE) -> VCCA
    ft_vphy = Net('FT_VPHY')        # 3.3 V ferrite-filtered PHY/PLL supply
    ft_vphy.drive = POWER           # fed only through passive FB8
    ft_clkout_r = Net('FT_CLKOUT_R')
    ft_pwrsav_n = Net('FT_PWRSAV_N')
    ft_reset_n = Net('FT_RESET_N')
    ft_xin, ft_xout = Net('FT_XIN'), Net('FT_XOUT')
    ft_ref = Net('FT_REF')
    ft_eecs, ft_eeclk, ft_eedata = Net('FT_EECS'), Net('FT_EECLK'), Net('FT_EEDATA')
    ft_eedo = Net('FT_EEDO')        # U14.DO -> R60 -> FT_EEDATA

    # --- U13 FT232HL ---
    u13 = Part('Interface_USB', 'FT232H', ref='U13', value='FT232HL-REEL',
               footprint='Package_QFP:LQFP-48_7x7mm_P0.5mm', MPN='FT232HL-REEL', LCSC='C51997')

    # Power pins (by number; symbol names: 38 = VCCCORE, 34 = ~{RESET})
    u13[40, 39, 12, 24, 46] += vd_3v3            # VREGIN, VCCD, VCCIO×3
    u13[3, 8] += ft_vphy                         # VPHY, VPLL
    u13[38, 37] += ft_vcore                      # VCORE (LDO out), VCCA (1.8 V analog in)
    # KiCad's FT232H symbol types VCCA (37) as power_out; per DS_FT232H it is the 1.8 V analog
    # supply *input* fed from VCORE. Retype it so ERC doesn't see two power outputs on FT_VCORE.
    u13[37].func = Pin.types.PWRIN
    u13[4, 9, 41, 10, 11, 22, 23, 35, 36, 47, 48] += gnd   # AGND×3, GND×8
    u13[42] += gnd                               # TEST -> GND (net_plan §7)

    # USB
    u13['DP'] += usb_dp
    u13['DM'] += usb_dm
    u13['REF'] += ft_ref
    _res('R64', '12k', ft_ref, gnd)              # PHY reference current, 12 kΩ 1 %

    # 12 MHz crystal (pads 1/3 = resonator, 2/4 = case -> GND)
    y1 = Part('Device', 'Crystal_GND24', ref='Y1', value='12MHz',
              footprint='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm', MPN='X322512MSB4SI', LCSC='C9002')
    u13['XCSI'] += ft_xin
    u13['XCSO'] += ft_xout
    y1[1] += ft_xin
    y1[3] += ft_xout
    y1[2, 4] += gnd
    _cap('C65', '22pF', ft_xin, gnd)             # load caps for CL = 20 pF
    _cap('C66', '22pF', ft_xout, gnd)

    # 245 sync FIFO: ADBUS = data, ACBUS0..7 = RXF#, TXE#, RD#, WR#, SIWU#, CLKOUT, OE#, PWRSAV#
    for i in range(8):
        u13[f'ADBUS{i}'] += ft_d[i]
    u13['ACBUS0'] += ft_rxf_n
    u13['ACBUS1'] += ft_txe_n
    u13['ACBUS2'] += ft_rd_n
    u13['ACBUS3'] += ft_wr_n
    u13['ACBUS4'] += ft_siwu_n
    u13['ACBUS5'] += ft_clkout_r
    _res('R66', '33', ft_clkout_r, ft_clkout)    # series termination at the source
    u13['ACBUS6'] += ft_oe_n
    u13['ACBUS7'] += ft_pwrsav_n
    _res('R67', '10k', ft_pwrsav_n, vd_3v3)      # PWRSAV# must read 1 for normal operation
    u13['ACBUS8', 'ACBUS9'] += NC                # unused (net_plan §7)

    # Reset: pull-up + RC
    u13[34] += ft_reset_n
    _res('R65', '10k', ft_reset_n, vd_3v3)
    _cap('C79', '100nF', ft_reset_n, gnd)

    # --- U14 93LC56B config EEPROM (SOT-23-6: 1 DO, 2 GND, 3 DI, 4 CLK, 5 CS, 6 VCC) ---
    u14 = Part('Memory_EEPROM', '93LCxxBxxOT', ref='U14', value='93LC56BT-I/OT',
               footprint='Package_TO_SOT_SMD:SOT-23-6', MPN='93LC56BT-I/OT', LCSC='C190271')
    u14['VCC'] += vd_3v3
    u14['GND'] += gnd
    u13['EECS'] += ft_eecs
    u13['EECLK'] += ft_eeclk
    u13['EEDATA'] += ft_eedata
    u14['CS'] += ft_eecs
    u14['CLK'] += ft_eeclk
    u14['DI'] += ft_eedata
    u14['DO'] += ft_eedo
    _res('R60', '2.2k', ft_eedo, ft_eedata)      # DO -> EEDATA (shared data line, DS_FT232H)
    _res('R61', '10k', ft_eecs, vd_3v3)
    _res('R62', '10k', ft_eeclk, vd_3v3)
    _res('R63', '10k', ft_eedata, vd_3v3)
    _cap('C78', '100nF', vd_3v3, gnd)            # U14 VCC decoupling

    # --- FB8: VD_3V3 -> FT_VPHY filter ---
    fb8 = Part('Device', 'FerriteBead', ref='FB8', value='600R@100MHz',
               footprint='Inductor_SMD:L_0805_2012Metric', MPN='BLM21PG601SN1D', LCSC='C41556732')
    vd_3v3 & fb8 & ft_vphy

    # --- U13 decoupling (one 100 nF per supply pin, bulk per domain) ---
    _cap('C67', '100nF', vd_3v3, gnd)            # VREGIN (40)
    _cap('C75', '4.7uF', vd_3v3, gnd)            # VREGIN bulk
    _cap('C68', '100nF', vd_3v3, gnd)            # VCCD (39)
    _cap('C69', '100nF', vd_3v3, gnd)            # VCCIO (12)
    _cap('C70', '100nF', vd_3v3, gnd)            # VCCIO (24)
    _cap('C71', '100nF', vd_3v3, gnd)            # VCCIO (46)
    _cap('C72', '100nF', ft_vphy, gnd)           # VPHY (3)
    _cap('C73', '100nF', ft_vphy, gnd)           # VPLL (8)
    _cap('C77', '4.7uF', ft_vphy, gnd)           # VPHY/VPLL bulk
    _cap('C74', '100nF', ft_vcore, gnd)          # VCORE/VCCA (37/38, adjacent pins)
    # DS_FT232H v1.81 Fig 6.3 (3.3 V config): VCORE gets 0.1 uF only; the 4.7 uF bulk sits on VCCD/VCC3V3.
    _cap('C76', '4.7uF', vd_3v3, gnd)            # VCCD (39) bulk
