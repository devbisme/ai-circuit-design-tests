"""USB-C input + protection — VBUS entry, ESD/TVS clamps, CC pulldowns, shield termination
Block from: architecture/block_diagram.md
Interface nets: +5V_IN, USB_DP, USB_DM, GND

USB 2.0 only, no PD controller (architecture "Do not redo": plain 5.1 kOhm CC pulldowns and
USB 2.0 signalling). The 5.1 kOhm pulldowns on CC1/CC2 are what advertise a UFP sink to a
Type-C source, which is what permits >500 mA once the source says so; nothing in this block
negotiates anything.

Local nets (not in the block signature, both live entirely inside this file):
  * VBUS_RAW — J1's four VBUS pads, D2 (TVS), D1's clamp reference, FB1 input. Listed in
    net_plan.md's inter-block table, but every ref on it (J1, D2, D1, FB1) is in THIS block,
    so it is created locally rather than passed in. The assembler must NOT pass it.
  * SHIELD   — J1's shell, terminated to GND by C15 (1 nF) || R12 (1 MOhm). Deliberately NOT
    the GND net: architecture decision 12's "one GND net" is about AGND/DGND, not about
    hard-bonding the connector shell.

Reversibility (handoffs/04_datasheets.md, TYPE-C-16PIN-2MD-073 summary): only USB 2.0 is
bonded out, so D+ appears on BOTH A6 and B6 and D- on both A7 and B7. Each pair is tied to
one net so the cable works either way up. Same for the 4 VBUS and 4 GND pads.

VBUS bulk budget (SPEC P4): C1 + C2 = 9.4 uF, under the USB 2.0 10 uF ceiling. The sourced
BOM lists two 10 uF parts for C1/C2 with an explicit instruction NOT to populate both at
10 uF; 4.7 uF each is the split taken here (same Samsung CL21A 0805 X5R family, MPN moves
from CL21A106KAYNNNE to a CL21A475K-class part — flagged in the handoff).
"""
from skidl import *

# --- Footprint shorthands -------------------------------------------------------------
_FP_R0603 = 'Resistor_SMD:R_0603_1608Metric'
_FP_C0603 = 'Capacitor_SMD:C_0603_1608Metric'
_FP_C0805 = 'Capacitor_SMD:C_0805_2012Metric'
_FP_L0603 = 'Inductor_SMD:L_0603_1608Metric'


@SubCircuit
def usb_c_input(v5_in, usb_dp, usb_dm, gnd):
    """USB-C receptacle, ESD/surge protection, CC pulldowns, VBUS filter.

    Args:
        v5_in:   Net — +5V_IN, 5 V DOWNSTREAM of FB1 and the bulk caps. DRIVEN by this
                 block (it is the board's power entry). Needs .drive = POWER at the top
                 level so the rest of the tree passes ERC.
        usb_dp:  Net — USB_DP. Bidirectional pass-through: J1.A6/B6 <-> D1 <-> U7.
        usb_dm:  Net — USB_DM. Bidirectional pass-through: J1.A7/B7 <-> D1 <-> U7.
        gnd:     Net — GND (single ground net per net_plan.md ground policy).

    Assumptions:
        * No PD/CC logic anywhere on the board — CC1/CC2 are terminated here and nowhere
          else. Do not connect CC1/CC2 outside this block.
        * D1 (USBLC6-2SC6) is a pass-through clamp: pins 1/6 are the SAME internal node
          (I/O1) and pins 3/4 are the same node (I/O2), so both ends of each pair land on
          the one USB_DP / USB_DM net. There is no series element in the data path.
        * SBU1/SBU2 (A8/B8) are unused and explicitly NC.
    """
    # --- J1: USB-C receptacle (net_plan.md "Power nets" + "Control, config, debug") -----
    J1 = Part('dual_adc_usb', 'TYPE-C-16PIN-2MD-073', ref='J1',
              value='TYPE-C-16PIN-2MD-073',
              footprint='Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12')

    # --- Local nets ---------------------------------------------------------------------
    vbus_raw = Net('VBUS_RAW')      # connector-side 5 V, ahead of FB1
    shield = Net('SHIELD')          # connector shell, RC-terminated to GND

    # --- Connector power + ground (4 pads each, all tied together) ----------------------
    vbus_raw += J1['A4'], J1['A9'], J1['B4'], J1['B9']
    gnd += J1['A1'], J1['A12'], J1['B1'], J1['B12']

    # --- CC1/CC2 5.1 kOhm pulldowns: advertise a UFP sink, enable >500 mA offers --------
    R1 = Part('Device', 'R', ref='R1', value='5.1k', footprint=_FP_R0603)
    R2 = Part('Device', 'R', ref='R2', value='5.1k', footprint=_FP_R0603)
    cc1 = Net('CC1')                # net_plan.md names these; keep them out of N$n
    cc2 = Net('CC2')
    cc1 += J1['A5'], R1[1]
    cc2 += J1['B5'], R2[1]
    R1[2] += gnd
    R2[2] += gnd

    # --- USB 2.0 data pair: both A- and B-row pads tied together for reversibility ------
    usb_dp += J1['A6'], J1['B6']    # Dp1, Dp2
    usb_dm += J1['A7'], J1['B7']    # Dn1, Dn2

    # --- Unused sideband pins -----------------------------------------------------------
    J1['A8'] += NC                  # SBU1 — unused (USB 2.0 only)
    J1['B8'] += NC                  # SBU2 — unused

    # --- D1: USBLC6-2SC6 ESD array across the data pair, referenced to VBUS_RAW ---------
    # Pins by number; the symbol's names ("I/O1", "I/O2") contain a regex-significant "/".
    D1 = Part('Power_Protection', 'USBLC6-2SC6', ref='D1', value='USBLC6-2SC6',
              footprint='Package_TO_SOT_SMD:SOT-23-6')
    usb_dp += D1[1], D1[6]          # I/O1 (both pads are one internal node)
    usb_dm += D1[3], D1[4]          # I/O2
    D1[5] += vbus_raw               # VBUS — clamp reference, kept at the connector
    D1[2] += gnd                    # GND

    # --- D2: SMF5.0CA bidirectional TVS on VBUS (surge, not ESD-only) -------------------
    D2 = Part('Device', 'D_TVS', ref='D2', value='SMF5.0CA',
              footprint='Diode_SMD:D_SOD-123F')
    D2[1] += vbus_raw               # A1 (bidirectional part — orientation is free)
    D2[2] += gnd                    # A2

    # --- FB1 + C1/C2: VBUS_RAW -> +5V_IN ferrite + bulk (<= 10 uF total, SPEC P4) -------
    FB1 = Part('Device', 'FerriteBead', ref='FB1', value='600R@100MHz',
               footprint=_FP_L0603)
    FB1[1] += vbus_raw
    FB1[2] += v5_in

    C1 = Part('Device', 'C', ref='C1', value='4.7uF', footprint=_FP_C0805)
    C2 = Part('Device', 'C', ref='C2', value='4.7uF', footprint=_FP_C0805)
    for c in (C1, C2):              # 4.7 + 4.7 = 9.4 uF: under the USB 2.0 10 uF ceiling
        c[1] += v5_in
        c[2] += gnd

    # --- Shield: C15 (1 nF) || R12 (1 MOhm) to GND --------------------------------------
    # RC termination, not a hard bond: HF shield currents return through C15, static bleeds
    # through R12, and no LF ground loop is created between chassis and board ground.
    shield += J1['S1']
    C15 = Part('Device', 'C', ref='C15', value='1nF', footprint=_FP_C0603)
    R12 = Part('Device', 'R', ref='R12', value='1M', footprint=_FP_R0603)
    C15[1] += shield
    C15[2] += gnd
    R12[1] += shield
    R12[2] += gnd
