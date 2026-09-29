"""USB-C Port — USB-C 2.0 receptacle, CC sink advertisement, ESD/TVS protection, VBUS entry.
Block from: architecture/block_diagram.md
Interface nets: VBUS, GND, USB_DP, USB_DM
"""
from skidl import *


@SubCircuit
def usb_c_port(vbus, gnd, usb_dp, usb_dm):
    """USB-C 2.0 receptacle with VBUS entry filtering and USB data ESD protection.

    Args:
        vbus:    OUTPUT (driven by this block) — +5 V board rail, downstream of FB1.
                 Feeds U1 (AP2112K), U2 (TLV62569) and FB2 -> U5 (LM27762).
        gnd:     Single board ground (net_plan.md: one GND net, no AGND).
        usb_dp:  BIDIRECTIONAL — USB 2.0 HS D+ between J1 and U13 (FX2LP), through D1.
        usb_dm:  BIDIRECTIONAL — USB 2.0 HS D- between J1 and U13 (FX2LP), through D1.

    Topology (VBUS entry):
        J1 VBUS pins -> VBUS_CONN (D2 TVS, C1 10uF bulk, C2 100nF, D1 VBUS ref)
                     -> FB1 600R ferrite -> vbus (C3 100nF, TP1)

        The USB 2.0 spec (7.2.4.1, requirement P7) caps bypass capacitance *at the
        connector* at 10 uF: C1 is that entire allowance and the only bulk cap in this
        block. Downstream rail bulk belongs to the regulator blocks. The ferrite is in
        the VBUS path so connector-side transients and the ESD/TVS return current stay
        at the connector, ahead of the board rail.

    Assumptions:
        - Device (UFP) role only, 5 V default current, no PD negotiation:
          both CC pins get their own 5.1k pull-down (R1, R2), reversible cable support.
        - No 1.5k D+ pull-up and no D+/D- series resistors — the FX2LP integrates both
          (net_plan.md, USB / config / aux nets).
        - SBU1/SBU2 unused (no alt mode) -> NC.
        - Shield/shell (S1) tied directly to GND — single-GND design, no shell RC.
        - vbus is driven here, so the assembler does NOT need PWR_FLAG/.drive on it
          for this block's sake; see handoff.
    """
    # --- Connector-side (unfiltered) VBUS node, local to this block ---
    vbus_conn = Net('VBUS_CONN')

    # --- USB-C 2.0 16-pin mid-mount receptacle (TYPE-C 16PIN 2MD(073), C2765186) ---
    # Footprint land pattern confirmed against the datasheet drawing:
    # datasheets/TYPE-C_16PIN_2MD-073_SUMMARY.md ("CONFIRMED MATCH").
    J1 = Part('Connector', 'USB_C_Receptacle_USB2.0_16P', ref='J1',
              value='TYPE-C 16PIN 2MD(073)',
              footprint='Connector_USB:USB_C_Receptacle_HCTL_HC-TYPE-C-16P-01A')

    # --- CC sink advertisement: 5.1k to GND on each CC pin (0402WGF5101TCE, C25905) ---
    R_cc = Part('Device', 'R', dest=TEMPLATE, value='5.1k',
                footprint='Resistor_SMD:R_0402_1005Metric')
    R1 = R_cc(ref='R1')
    R2 = R_cc(ref='R2')

    # --- USB data-line ESD array (USBLC6-2SC6, C2687116) ---
    # Pins 1/6 are the same internal node (I/O1), 3/4 likewise (I/O2); connecting both
    # ends of each pair lets layout route the pair straight through the package.
    D1 = Part('Power_Protection', 'USBLC6-2SC6', ref='D1', value='USBLC6-2SC6',
              footprint='Package_TO_SOT_SMD:SOT-23-6')

    # --- VBUS TVS (SMAJ5.0A, C2925443, unidirectional: pin 1 = cathode/band) ---
    D2 = Part('Device', 'D_TVS', ref='D2', value='SMAJ5.0A',
              footprint='Diode_SMD:D_SMA')

    # --- VBUS ferrite (BLM18AG601SN1D, 600R @ 100 MHz, 500 mA) ---
    # Chip-ferrite land pattern == 0603 chip-resistor land pattern (sourcing note).
    FB1 = Part('Device', 'FerriteBead', ref='FB1', value='600R@100MHz',
               footprint='Resistor_SMD:R_0603_1608Metric')

    # --- VBUS capacitors ---
    C1 = Part('Device', 'C', ref='C1', value='10uF',      # CL21A106KOQNNNE, 16 V X5R
              footprint='Capacitor_SMD:C_0805_2012Metric')
    C_hf = Part('Device', 'C', dest=TEMPLATE, value='100nF',   # CL05B104KB54PNC
                footprint='Capacitor_SMD:C_0402_1005Metric')
    C2 = C_hf(ref='C2')
    C3 = C_hf(ref='C3')

    # --- VBUS test point ---
    TP1 = Part('Connector', 'TestPoint', ref='TP1', value='VBUS',
               footprint='TestPoint:TestPoint_Pad_D1.0mm')

    # ------------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------------
    # Connector power/ground (all four VBUS pins and all four GND pins in parallel)
    J1['A4', 'A9', 'B4', 'B9'] += vbus_conn
    J1['A1', 'A12', 'B1', 'B12'] += gnd
    J1['S1'] += gnd                      # shell / shield

    # CC pull-downs (UFP, 5 V default current) — net names per net_plan.md
    cc1 = Net('CC1')
    cc2 = Net('CC2')
    J1['A5'] += cc1
    J1['B5'] += cc2
    cc1 += R1[1]
    cc2 += R2[1]
    R1[2] += gnd
    R2[2] += gnd

    # Unused sideband pins
    J1['A8', 'B8'] += NC                 # SBU1 / SBU2 — no alt mode

    # USB 2.0 data pair: connector pins and FX2LP-side nets are the same nodes,
    # with D1 sitting across them at the connector.
    J1['A6', 'B6'] += usb_dp             # D+ lane 1 / lane 2
    J1['A7', 'B7'] += usb_dm             # D- lane 1 / lane 2
    D1[1] += usb_dp                      # I/O1 (connector side)
    D1[6] += usb_dp                      # I/O1 (host/FX2LP side)
    D1[3] += usb_dm                      # I/O2 (connector side)
    D1[4] += usb_dm                      # I/O2 (host/FX2LP side)
    D1[5] += vbus_conn                   # clamp rail reference, at the connector
    D1[2] += gnd

    # VBUS entry: TVS + bulk at the connector, ferrite into the board rail
    D2[1] += vbus_conn                   # cathode (band) to +5 V
    D2[2] += gnd                         # anode
    C1[1] += vbus_conn
    C1[2] += gnd
    C2[1] += vbus_conn
    C2[2] += gnd

    FB1[1] += vbus_conn
    FB1[2] += vbus                       # filtered board +5 V rail (block output)

    C3[1] += vbus
    C3[2] += gnd
    TP1[1] += vbus
