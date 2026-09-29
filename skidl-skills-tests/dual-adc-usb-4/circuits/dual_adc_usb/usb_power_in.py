"""USB Power In — USB-C sink receptacle, ESD/TVS protection, VBUS filter, SY6280 current-limit switch
Block from: architecture/block_diagram.md (usb_power_in)
Interface nets: VBUS_SW, USB_DP, USB_DM, GND
Net plan: architecture/net_plan.md §1 (VBUS, VBUS_F, VBUS_SW) and §2 (USB_*, SW_ISET).
Parts: sourcing/sourced_bom.md § usb_power_in; R3 value from datasheets/SY6280AAC_SUMMARY.md.
"""
from skidl import *

# Passive catalogue: value -> (footprint, MPN, LCSC). Single source of truth for this block.
_CAPS = {
    '4.7uF': ('Capacitor_SMD:C_0603_1608Metric', 'CL10A475KO8NNNC', 'C19666'),
    '100nF': ('Capacitor_SMD:C_0402_1005Metric', 'CL05B104KB54PNC', 'C307331'),
    '10uF': ('Capacitor_SMD:C_0805_2012Metric', 'CL21A106KAYNNNE', 'C15850'),
    '4.7nF 100V': ('Capacitor_SMD:C_0603_1608Metric', 'CC0603KRX7R0BB472', 'C115052'),
}
_RES = {
    '5.1k': ('Resistor_SMD:R_0603_1608Metric', '0603WAF5101T5E', 'C23186'),
    # ILIM = 6800 / R_ISET -> 8.45k gives ~0.805 A (datasheets/SY6280AAC_SUMMARY.md).
    '8.45k': ('Resistor_SMD:R_0603_1608Metric', '0603WAF8451T5E', 'C14892'),
    '1M': ('Resistor_SMD:R_0603_1608Metric', '0603WAF1004T5E', 'C22935'),
}


def _cap(ref, value, a, b):
    """One capacitor between nets a and b."""
    fp, mpn, lcsc = _CAPS[value]
    c = Part('Device', 'C', ref=ref, value=value, footprint=fp, MPN=mpn, LCSC=lcsc)
    a & c & b


def _res(ref, value, a, b):
    """One resistor between nets a and b."""
    fp, mpn, lcsc = _RES[value]
    r = Part('Device', 'R', ref=ref, value=value, footprint=fp, MPN=mpn, LCSC=lcsc)
    a & r & b


@SubCircuit
def usb_power_in(vbus_sw, usb_dp, usb_dm, gnd):
    """USB-C UFP sink entry: J1 receptacle, U1 USBLC6-2SC6 data-line ESD, D1 SMF5.0A VBUS TVS,
    FB1 + C1/C2 VBUS filter, U2 SY6280AAC load switch (~0.8 A limit, soft start).

    Args:
        vbus_sw: 5 V switched, current-limited output (U2.OUT). DRIVEN here (drive=POWER).
        usb_dp:  USB D+ (J1.A6/B6, U1 I/O1). Bidirectional, passes through to the USB bridge.
        usb_dm:  USB D- (J1.A7/B7, U1 I/O2). Bidirectional, passes through to the USB bridge.
        gnd:     Common ground.

    Assumptions:
        - Default-current sink only (CC1/CC2 5.1k pull-downs, no PD controller).
        - U2.EN is tied to VBUS_F per net_plan (switch always enabled when VBUS is present).
        - Total capacitance ahead of U2 is C1 + C2 = 4.8 uF (P5: <= 10 uF).
    """
    # Block-local nets (net_plan §1/§2). VBUS/VBUS_F are fed only by passive pins
    # (connector, ferrite), so they carry their own drive to satisfy ERC on U2.IN.
    vbus = Net('VBUS')
    vbus.drive = POWER
    vbus_f = Net('VBUS_F')
    vbus_f.drive = POWER
    cc1 = Net('USB_CC1')
    cc2 = Net('USB_CC2')
    shield = Net('USB_SHIELD')
    sw_iset = Net('SW_ISET')
    vbus_sw.drive = POWER

    # J1 — USB-C 16P receptacle (USB 2.0 only).
    j1 = Part('Connector', 'USB_C_Receptacle_USB2.0_16P', ref='J1', value='TYPE-C-31-M-12',
              footprint='Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',
              MPN='TYPE-C-31-M-12', LCSC='C165948')
    j1['VBUS'] += vbus            # A4, A9, B4, B9
    j1['GND'] += gnd              # A1, A12, B1, B12
    j1['D+'] += usb_dp            # A6, B6
    j1['D-'] += usb_dm            # A7, B7
    j1['CC1'] += cc1
    j1['CC2'] += cc2
    j1['SHIELD'] += shield
    j1['SBU1', 'SBU2'] += NC      # net_plan §2: SBU unused

    # CC pull-downs: 5.1k Rd on each CC line -> UFP sink, default current.
    _res('R1', '5.1k', cc1, gnd)
    _res('R2', '5.1k', cc2, gnd)

    # Shield: 1M bleed || 4.7nF 100V to GND.
    _res('R4', '1M', shield, gnd)
    _cap('C4', '4.7nF 100V', shield, gnd)

    # U1 — USBLC6-2SC6 ESD array. Pin mapping per net_plan §2: I/O1 (1,6) = D+, I/O2 (3,4) = D-.
    u1 = Part('Power_Protection', 'USBLC6-2SC6', ref='U1', value='USBLC6-2SC6',
              footprint='Package_TO_SOT_SMD:SOT-23-6', MPN='USBLC6-2SC6', LCSC='C2687116')
    u1[1, 6] += usb_dp
    u1[3, 4] += usb_dm
    u1[5] += vbus
    u1[2] += gnd

    # D1 — SMF5.0A unidirectional TVS on raw VBUS. Pin 1 = cathode (banded) -> VBUS.
    d1 = Part('Device', 'D_TVS', ref='D1', value='SMF5.0A', footprint='Diode_SMD:D_SOD-123F',
              MPN='SMF5.0A', LCSC='C19077497')
    d1[1] += vbus
    d1[2] += gnd

    # FB1 — VBUS -> VBUS_F ferrite (220R@100MHz, 45 mOhm, 2 A).
    fb1 = Part('Device', 'FerriteBead', ref='FB1', value='220R@100MHz',
               footprint='Inductor_SMD:L_0805_2012Metric', MPN='BLM21PG221SN1D', LCSC='C85840')
    vbus & fb1 & vbus_f

    # U2 input caps (<= 10 uF total ahead of the switch).
    _cap('C1', '4.7uF', vbus_f, gnd)
    _cap('C2', '100nF', vbus_f, gnd)

    # U2 — SY6280AAC load switch.
    u2 = Part('dual_adc_usb', 'SY6280AAC', ref='U2', value='SY6280AAC',
              footprint='Package_TO_SOT_SMD:SOT-23-5', MPN='SY6280AAC', LCSC='C55136')
    u2['IN'] += vbus_f
    u2['EN'] += vbus_f            # net_plan §1: EN on VBUS_F, always enabled
    u2['GND'] += gnd
    u2['ISET'] += sw_iset
    u2['OUT'] += vbus_sw
    _res('R3', '8.45k', sw_iset, gnd)

    # Output bulk cap on VBUS_SW.
    _cap('C3', '10uF', vbus_sw, gnd)
