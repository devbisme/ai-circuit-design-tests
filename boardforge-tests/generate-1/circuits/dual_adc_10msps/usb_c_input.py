"""USB-C Input — USB-C 2.0 sink receptacle, VBUS TVS + PTC, D+/D- ESD
Block from: architecture/block_diagram.md (connections: architecture/net_plan.md Block 1)
Interface nets: +5V, USB_DP, USB_DM, GND
"""
from skidl import *


def _part(lib, name, ref, value, fp, mpn, lcsc):
    p = Part(lib, name, ref=ref, value=value, footprint=fp)
    p.fields['MPN'] = mpn
    p.fields['LCSC'] = lcsc
    return p


@SubCircuit
def usb_c_input(v5, usb_dp, usb_dm, gnd):
    """J501 USB-C (sink, Rd 5.1k on CC1/CC2, no PD) -> VBUS -> F501 PTC 0.75 A -> v5.

    Drives: v5 (+5V, through the PTC; flagged as a power source here).
    Bidirectional: usb_dp / usb_dm (both receptacle orientations tied; USBLC6 ESD).
    Local nets: VBUS, CC1, CC2. SBU1/SBU2 not connected.
    VBUS capacitance budget: only C501 1 uF here (total VBUS domain <= 10 uF).
    """
    vbus = Net('VBUS')
    vbus.drive = POWER                # receptacle pins are passive: VBUS source flag
    flg502 = Part('power', 'PWR_FLAG', ref='#FLG502')
    vbus += flg502[1]
    cc1 = Net('CC1')
    cc2 = Net('CC2')

    j = _part('Connector', 'USB_C_Receptacle_USB2.0_16P', 'J501', 'TYPE-C-31-M-12',
              'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12', 'TYPE-C-31-M-12', 'C165948')
    vbus += j['A4', 'A9', 'B4', 'B9']
    gnd += j['A1', 'A12', 'B1', 'B12', 'SH']   # SH = SHIELD (symbol pin number)
    usb_dp += j['A6', 'B6']
    usb_dm += j['A7', 'B7']
    cc1 += j['A5']
    cc2 += j['B5']
    j['A8'] += NC
    j['B8'] += NC

    # Rd pull-downs (sink advertisement)
    r501 = _part('Device', 'R', 'R501', '5.1k', 'Resistor_SMD:R_0402_1005Metric', '0402WGF5101TCE', 'C25905')
    r502 = _part('Device', 'R', 'R502', '5.1k', 'Resistor_SMD:R_0402_1005Metric', '0402WGF5101TCE', 'C25905')
    cc1 & r501 & gnd
    cc2 & r502 & gnd

    # ESD on data lines: I/O1 = pins 1&6 (D+), I/O2 = pins 3&4 (D-), VBUS 5, GND 2
    u501 = _part('Power_Protection', 'USBLC6-2SC6', 'U501', 'USBLC6-2SC6',
                 'Package_TO_SOT_SMD:SOT-23-6', 'USBLC6-2SC6', 'C7519')
    usb_dp += u501['1', '6']
    usb_dm += u501['3', '4']
    vbus += u501['5']
    gnd += u501['2']

    # VBUS TVS (unidirectional SMF5.0A; pin 1 = cathode/band -> VBUS)
    d501 = _part('Device', 'D_TVS', 'D501', 'SMF5.0A', 'Diode_SMD:D_SOD-123F', 'SMF5.0A', 'C19077497')
    vbus += d501[1]
    gnd += d501[2]

    c501 = _part('Device', 'C', 'C501', '1u', 'Capacitor_SMD:C_0402_1005Metric', 'CL05A105KA5NQNC', 'C52923')
    vbus & c501 & gnd

    # PTC: VBUS -> +5V
    f501 = _part('Device', 'Polyfuse', 'F501', '750mA', 'Fuse:Fuse_1812_4532Metric', 'JK-mSMD075-33', 'C369169')
    vbus += f501[1]
    v5 += f501[2]

    # +5V enters through a passive (PTC): source flag for SKiDL and KiCad ERC
    v5.drive = POWER
    flg = Part('power', 'PWR_FLAG', ref='#FLG501')
    v5 += flg[1]
