"""USB Power In — USB-C receptacle (USB 2.0), D+/D-/VBUS ESD array, soft-start load switch
Block from: architecture/block_diagram.md (usb_power_in)
Interface nets: V5, USB_DP, USB_DN, GND
"""
from skidl import *


@SubCircuit
def usb_power_in(v5, usb_dp, usb_dn, gnd):
    """USB-C sink input.

    J1 TYPE-C-31-M-12 (USB 2.0 only): CC1/CC2 each Rd 5.1k to GND (default-USB sink).
    D+ (A6/B6) and D- (A7/B7) are paralleled on the connector and brought out as
    usb_dp / usb_dn through U1 USBLC6-2SC6 ESD (pass-through pads 1/6 and 3/4).
    Raw VBUS (local net) -> U2 TPS22919 soft-start switch -> v5 (U2 drives v5).
    U2.ON tied to VBUS (4.4-5.25 V >= VIH 1.0 V); QOD tied to VOUT (24 ohm discharge).
    C1 4.7 uF on VBUS keeps pre-switch capacitance < 10 uF (USB inrush rule).
    SBU1/SBU2 unused -> NC. Shell and GND pins -> gnd.
    """
    # --- local nets (net_plan.md: VBUS, CC1, CC2) ---
    vbus = Net('VBUS')
    vbus.drive = POWER          # sole source is the connector (passive pins)
    cc1 = Net('CC1')
    cc2 = Net('CC2')

    # --- J1 USB-C receptacle (pins by number; matches HRO footprint pads) ---
    J1 = Part('Connector', 'USB_C_Receptacle_USB2.0_16P', ref='J1',
              value='TYPE-C-31-M-12',
              footprint='Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12')
    J1['A4', 'A9', 'B4', 'B9'] += vbus
    J1['A1', 'A12', 'B1', 'B12', 'S1'] += gnd
    J1['A5'] += cc1
    J1['B5'] += cc2
    J1['A6', 'B6'] += usb_dp
    J1['A7', 'B7'] += usb_dn
    J1['A8', 'B8'] += NC        # SBU1/SBU2 unused

    # --- CC Rd pull-downs (5.1k, sink / default USB power) ---
    R1 = Part('Device', 'R', ref='R1', value='5.1k',
              footprint='Resistor_SMD:R_0603_1608Metric')
    R2 = Part('Device', 'R', ref='R2', value='5.1k',
              footprint='Resistor_SMD:R_0603_1608Metric')
    cc1 & R1 & gnd
    cc2 & R2 & gnd

    # --- U1 USBLC6-2SC6 ESD: I/O1 (1,6) = D+, I/O2 (3,4) = D-, VBUS clamp on raw VBUS ---
    U1 = Part('Power_Protection', 'USBLC6-2SC6', ref='U1', value='USBLC6-2SC6',
              footprint='Package_TO_SOT_SMD:SOT-23-6')
    U1[1, 6] += usb_dp
    U1[3, 4] += usb_dn
    U1[5] += vbus
    U1[2] += gnd

    # --- U2 TPS22919 load switch: 1 IN, 2 GND, 3 ON, 4 NC, 5 QOD, 6 VOUT ---
    U2 = Part('dual_adc_usb', 'TPS22919DCKR', ref='U2', value='TPS22919DCKR',
              footprint='Package_TO_SOT_SMD:SOT-363_SC-70-6')
    U2[1] += vbus
    U2[3] += vbus               # always on while VBUS present
    U2[2] += gnd
    U2[4] += NC                 # datasheet: leave floating
    U2[5] += v5                 # QOD -> VOUT: internal quick discharge
    U2[6] += v5

    # --- bulk / HF capacitors ---
    C1 = Part('Device', 'C', ref='C1', value='4.7uF',
              footprint='Capacitor_SMD:C_0603_1608Metric')   # VBUS, pre-switch
    C2 = Part('Device', 'C', ref='C2', value='10uF',
              footprint='Capacitor_SMD:C_0603_1608Metric')   # V5 bulk
    C3 = Part('Device', 'C', ref='C3', value='100nF',
              footprint='Capacitor_SMD:C_0402_1005Metric')   # V5 HF
    vbus & C1 & gnd
    v5 & C2 & gnd
    v5 & C3 & gnd
