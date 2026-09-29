"""USB Power Input — USB-C receptacle, ESD protection, CC pulldowns, inrush
soft-start, and the analog/digital VBUS split.
Block from: architecture/block_diagram.md
Interface nets: vbus_5v, vbus_a5v, gnd, usb_dp, usb_dm
"""
from skidl import *

@subcircuit
def usb_power_input(vbus_5v, vbus_a5v, gnd, usb_dp, usb_dm):
    """USB-C 2.0-device power/data entry point (net_plan.md section 3.1).

    - J1 is wired as a USB 2.0 DEVICE only: D+/D- pins are shorted pairs
      (A6/B6 and A7/B7), no SS/SBU high-speed lanes are used.
    - Dual 5.1 k CC pulldowns (R1, R2) are both populated per constraint 6 —
      a single-CC design would leave the connector non-compliant.
    - Q1 is an always-on inrush soft-start P-FET (not a load switch): its
      gate is driven by a slow R3/C5 RC (~5 ms) with R4 as a gate pull-down
      so the FET defaults OFF (safe state) until the RC charges.
    - L1/L2 perform the mandated analog/digital split AT THE SOURCE: VBUS_5V
      is the digital branch (post-ferrite L1), VBUS_A5V is the analog branch
      (post-ferrite L2). Both branches originate from the same Q1 drain node
      so they share one soft-start event but are isolated from each other's
      switching noise downstream.
    - VBUS bulk caps are held to 10 uF (C1, C3) per USB inrush compliance —
      NOT increased, per net_plan constraint.

    Args:
        vbus_5v: Digital-branch 5 V rail, post L1 ferrite (drives power_digital)
        vbus_a5v: Analog-branch 5 V rail, post L2 ferrite (drives power_analog,
            vref_2v5, clock_40m)
        gnd: Ground reference
        usb_dp: USB 2.0 D+ signal, out to usb_bridge_ft2232h
        usb_dm: USB 2.0 D- signal, out to usb_bridge_ft2232h
    """

    # ------------------------------------------------------------------
    # J1 — USB-C 2.0 device receptacle, 16-pin (TYPE-C-31-M-12 / HRO)
    # KiCad symbol has duplicate pin *names* for VBUS (A4,A9,B4,B9), GND
    # (A1,A12,B1,B12), D+ (A6,B6) and D- (A7,B7). Indexing by name in SKiDL
    # returns ALL pins sharing that name as a NetPinList, so a single `+=`
    # ties every physical pin of that name to the same net — this is exactly
    # what net_plan.md 3.1 calls for ("tied together").
    # ------------------------------------------------------------------
    J1 = Part('Connector', 'USB_C_Receptacle_USB2.0_16P', ref='J1',
              value='USB-C 2.0 Device (TYPE-C-31-M-12)',
              footprint='Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12')

    # Raw VBUS in from the connector (pre-TVS, pre-soft-start) — this is a
    # block-internal node, not one of the interface nets.
    vbusRaw = Net('vbusRaw')
    J1['VBUS'] += vbusRaw          # A4, A9, B4, B9 — all four pins
    J1['GND'] += gnd               # A1, A12, B1, B12 — per net_plan 3.1
    J1['SHIELD'] += gnd            # shell/shield tied to GND per work order

    # USB 2.0 only: SBU1/SBU2 are unused on a device-only design.
    J1['SBU1', 'SBU2'] += NC

    # D+/D- straight through the connector's shorted pin pairs, into the
    # ESD array (D2) below. usb_dp/usb_dm ARE the shunt-protected node —
    # USBLC6-2SC6 is a shunt clamp, not a series element (see D2 below), so
    # J1's D+/D- pair and the interface net are literally the same node.
    usb_dp += J1['D+']             # A6, B6
    usb_dm += J1['D-']             # A7, B7

    # ------------------------------------------------------------------
    # D1 — SMAJ5.0A VBUS TVS. Generic symmetric D_TVS symbol used (the
    # part itself is unidirectional in application: cathode to VBUS,
    # anode to GND, clamping positive VBUS transients to ground).
    # ------------------------------------------------------------------
    D1 = Part('Device', 'D_TVS', ref='D1', value='SMAJ5.0A',
              footprint='Diode_SMD:D_SMA')
    D1['A1'] += vbusRaw
    D1['A2'] += gnd

    # ------------------------------------------------------------------
    # CC pulldowns — MANDATORY DUAL per net_plan constraint 6. Each CC line
    # gets its own independent 5.1 k to GND so the connector presents a
    # valid Rd on both CC1 and CC2 regardless of cable/plug orientation.
    # ------------------------------------------------------------------
    R1 = Part('Device', 'R', ref='R1', value='5.1k',
              footprint='Resistor_SMD:R_0402_1005Metric')
    R2 = Part('Device', 'R', ref='R2', value='5.1k',
              footprint='Resistor_SMD:R_0402_1005Metric')
    J1['CC1'] += R1[1]
    R1[2] += gnd
    J1['CC2'] += R2[1]
    R2[2] += gnd

    # ------------------------------------------------------------------
    # Q1 — DMP2160U P-channel MOSFET inrush soft-start (net_plan 3.1 +
    # constraint 7: always-on after RC ramp, NOT a post-enumeration switch).
    #   Source (S) <- vbusRaw (through D1's node)
    #   Drain  (D) -> qDrain, the common node feeding BOTH ferrites (L1, L2)
    #   Gate   (G) <- R3/C5 RC to GND (~5 ms turn-on ramp), R4 gate pulldown
    # Generic Device:Q_PMOS_GSD symbol (pin1=G, pin2=S, pin3=D) matches the
    # DMP2160U-7 SOT-23 pinout (G,S,D).
    # ------------------------------------------------------------------
    Q1 = Part('Transistor_FET', 'Q_PMOS_GSD', ref='Q1', value='DMP2160U',
              footprint='Package_TO_SOT_SMD:SOT-23')
    qDrain = Net('qDrain')         # common pre-split node, both branches
    Q1['S'] += vbusRaw
    Q1['D'] += qDrain

    # Gate RC: R3 (100k) from source (vbusRaw) to gate, C5 (100n) from gate
    # to GND -> ~5 ms ramp (R3*C5 = 100k * 100n = 10 ms tau, giving the
    # ~5 ms turn-on referenced in net_plan). R4 (100k) gate pulldown keeps
    # the FET OFF (safe default) before the RC has charged and bleeds the
    # gate when VBUS is removed.
    R3 = Part('Device', 'R', ref='R3', value='100k',
              footprint='Resistor_SMD:R_0402_1005Metric')
    R4 = Part('Device', 'R', ref='R4', value='100k',
              footprint='Resistor_SMD:R_0402_1005Metric')
    C5 = Part('Device', 'C', ref='C5', value='100n',
              footprint='Capacitor_SMD:C_0402_1005Metric')
    gateNode = Net('qGate')
    vbusRaw += R3[1]
    R3[2] += gateNode
    Q1['G'] += gateNode
    gateNode += C5[1], R4[1]
    C5[2] += gnd
    R4[2] += gnd

    # ------------------------------------------------------------------
    # L1 — digital-branch ferrite. qDrain -> L1 -> vbus_5v (interface net).
    # ------------------------------------------------------------------
    L1 = Part('Device', 'FerriteBead', ref='L1', value='600R@100MHz',
              footprint='Inductor_SMD:L_0805_2012Metric')
    L1[1] += qDrain
    L1[2] += vbus_5v

    C1 = Part('Device', 'C', ref='C1', value='10uF',
              footprint='Capacitor_SMD:C_0805_2012Metric')
    C2 = Part('Device', 'C', ref='C2', value='100n',
              footprint='Capacitor_SMD:C_0402_1005Metric')
    vbus_5v += C1[1], C2[1]
    C1[2] += gnd
    C2[2] += gnd

    # ------------------------------------------------------------------
    # L2 — analog-branch ferrite. qDrain -> L2 -> vbus_a5v (interface net).
    # Separate net from vbus_5v: the split survives into the netlist per
    # net_plan section 1.1's explicit "must survive into the netlist"
    # requirement — vbus_5v and vbus_a5v only ever meet at qDrain, upstream
    # of both ferrites.
    # ------------------------------------------------------------------
    L2 = Part('Device', 'FerriteBead', ref='L2', value='600R@100MHz',
              footprint='Inductor_SMD:L_0805_2012Metric')
    L2[1] += qDrain
    L2[2] += vbus_a5v

    C3 = Part('Device', 'C', ref='C3', value='10uF',
              footprint='Capacitor_SMD:C_0805_2012Metric')
    C4 = Part('Device', 'C', ref='C4', value='100n',
              footprint='Capacitor_SMD:C_0402_1005Metric')
    vbus_a5v += C3[1], C4[1]
    C3[2] += gnd
    C4[2] += gnd

    # ------------------------------------------------------------------
    # D2 — USBLC6-2SC6 USB data-line ESD array (shunt clamp, not series).
    # I/O1 (pins 1 & 6) and I/O2 (pins 3 & 4) are internally the SAME node
    # on each channel — SKiDL's name-based indexing ties both physical pins
    # of each channel to usb_dp / usb_dm automatically, exactly matching
    # the shunt topology net_plan 3.1 describes ("-> U_esd -> out").
    # ------------------------------------------------------------------
    D2 = Part('Power_Protection', 'USBLC6-2SC6', ref='D2',
              value='USBLC6-2SC6',
              footprint='Package_TO_SOT_SMD:SOT-23-6')
    D2['I/O1'] += usb_dp
    D2['I/O2'] += usb_dm
    D2['GND'] += gnd
    D2['VBUS'] += vbus_5v          # ESD array supply — digital-branch rail

    # Decoupling for D2's VBUS pin per project convention (100nF + 10uF per
    # IC VCC/VBUS pin), even though the rail is already bulk-decoupled by
    # C1/C2 immediately upstream on the same net.
    C_DECOUP_D2 = Part('Device', 'C', ref='C_DECOUP_D2', value='100nF',
                        footprint='Capacitor_SMD:C_0402_1005Metric')
    C_DECOUP_D2_BULK = Part('Device', 'C', ref='C_DECOUP_D2_BULK',
                             value='10uF',
                             footprint='Capacitor_SMD:C_0805_2012Metric')
    vbus_5v += C_DECOUP_D2[1], C_DECOUP_D2_BULK[1]
    C_DECOUP_D2[2] += gnd
    C_DECOUP_D2_BULK[2] += gnd
