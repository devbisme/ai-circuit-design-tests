"""USB Power In — USB-C (USB 2.0) receptacle, PTC fuse, TVS, data-line ESD, soft-start load switch
Block from: architecture/block_diagram.md
Interface nets: VBUS_SW, USB_DP, USB_DM, GND
"""
from skidl import *

_R = 'Resistor_SMD:R_0402_1005Metric'


@SubCircuit
def usb_power_in(vbus_sw, usb_dp, usb_dm, gnd):
    """J1 USB-C sink (Rd 5.1k on CC1/CC2) -> VBUS -> F1 PTC 0.75 A -> VBUS_F.
    VBUS_F: D1 SMF5.0A TVS, U1 USBLC6 VBUS ref, C1 4.7 uF (only <=10 uF ahead of the switch).
    U2 TPS22918 load switch: VIN = VBUS_F, ON via R3 10k from VBUS_F, CT = C2 1 nF (tR 2.54 ms),
    QOD tied to VOUT (internal discharge), VOUT -> vbus_sw with C3 10 uF.
    Drives vbus_sw (U2.VOUT is a power output). usb_dp/usb_dm are bidirectional passthrough.
    Refs J1, U1, U2, F1, D1, R1, R2, R3, C1, C2, C3."""
    vbus = Net('VBUS')
    vbus_f = Net('VBUS_F')
    # The USB host is the source of VBUS_F (through J1 and F1, both passive), so the
    # net is marked as a power source here; the top level cannot reach this internal net.
    vbus_f.drive = POWER
    usb_on = Net('USB_ON')
    usb_ct = Net('USB_CT')
    cc1 = Net('CC1')
    cc2 = Net('CC2')

    j1 = Part('Connector', 'USB_C_Receptacle_USB2.0_16P', ref='J1', value='USB-C 16P',
              footprint='Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',
              MPN='TYPE-C-31-M-12', LCSC='C165948')
    j1['VBUS'] += vbus                    # A4, A9, B4, B9
    j1['GND'] += gnd                      # A1, A12, B1, B12
    j1['SHIELD'] += gnd                   # S1
    j1['A5'] += cc1                       # CC1
    j1['B5'] += cc2                       # CC2
    j1['A6', 'B6'] += usb_dp              # D+
    j1['A7', 'B7'] += usb_dm              # D-
    j1['A8', 'B8'] += NC                  # SBU1/SBU2 unused (USB 2.0)

    # UFP Rd pull-downs, one per CC (never tie CCs together)
    r1 = Part('Device', 'R', ref='R1', value='5.1k', footprint=_R, MPN='0402WGF5101TCE', LCSC='C25905')
    r2 = Part('Device', 'R', ref='R2', value='5.1k', footprint=_R, MPN='0402WGF5101TCE', LCSC='C25905')
    cc1 & r1 & gnd
    cc2 & r2 & gnd

    f1 = Part('Device', 'Polyfuse', ref='F1', value='0.75A',
              footprint='Fuse:Fuse_1206_3216Metric', MPN='SMD1206P075TF', LCSC='C20987')
    vbus & f1 & vbus_f

    # SMF5.0A unidirectional TVS: pin 1 = K -> VBUS_F, pin 2 = A -> GND (by number)
    d1 = Part('Diode', 'SMF5V0A', ref='D1', value='SMF5.0A',
              footprint='Diode_SMD:D_SOD-123F', MPN='SMF5.0A', LCSC='C19077497')
    d1[1] += vbus_f
    d1[2] += gnd

    # USBLC6-2SC6 flow-through: I/O1 (1,6) on D+, I/O2 (3,4) on D-
    u1 = Part('Power_Protection', 'USBLC6-2SC6', ref='U1', value='USBLC6-2SC6',
              footprint='Package_TO_SOT_SMD:SOT-23-6', MPN='USBLC6-2SC6', LCSC='C2687116')
    u1[1, 6] += usb_dp
    u1[3, 4] += usb_dm
    u1['VBUS'] += vbus_f
    u1['GND'] += gnd

    c1 = Part('Device', 'C', ref='C1', value='4.7uF', footprint='Capacitor_SMD:C_0603_1608Metric',
              MPN='CL10A475KO8NNNC', LCSC='C19666')
    vbus_f & c1 & gnd

    u2 = Part('dual_adc_usb', 'TPS22918DBVR', ref='U2', value='TPS22918DBVR',
              footprint='Package_TO_SOT_SMD:SOT-23-6', MPN='TPS22918DBVR', LCSC='C131941')
    u2['VIN'] += vbus_f
    u2['GND'] += gnd
    u2['ON'] += usb_on
    u2['CT'] += usb_ct
    u2['QOD'] += vbus_sw                  # internal quick-output-discharge enabled
    u2['VOUT'] += vbus_sw

    r3 = Part('Device', 'R', ref='R3', value='10k', footprint=_R, MPN='0402WGF1002TCE', LCSC='C25744')
    vbus_f & r3 & usb_on                  # ON high whenever VBUS present (VIH 1.0 V)

    c2 = Part('Device', 'C', ref='C2', value='1nF', footprint='Capacitor_SMD:C_0402_1005Metric',
              MPN='0402B102K500NT', LCSC='C1523')
    usb_ct & c2 & gnd                     # tR 2.54 ms @ 5 V

    c3 = Part('Device', 'C', ref='C3', value='10uF', footprint='Capacitor_SMD:C_0603_1608Metric',
              MPN='CL10A106KP8NNNC', LCSC='C19702')
    vbus_sw & c3 & gnd
