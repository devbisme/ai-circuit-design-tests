"""USB front end — USB-C 2.0 input, ESD protection, soft-start load switch
Block from: architecture/block_diagram.md
Interface nets: VBUS, VBUS_SW, USB_DP, USB_DM, GND
"""
from skidl import *


@SubCircuit
def usb_front(vbus, vbus_sw, usb_dp, usb_dm, gnd):
    """Board power and data entry point.

    Signal path:  J1 (USB-C 2.0 receptacle, 16P) -> U1 (USBLC6-2SC6 ESD array)
                  -> USB_DP / USB_DM out to `usb_bridge` (U50, CY7C68013A).
    Power path:   J1 VBUS -> C1 -> U2 (TPS22919 soft-start load switch) -> VBUS_SW,
                  bulked by C2 + C3 (2 x 22 uF).

    Design points that are load-bearing:

      * CC1/CC2 carry plain 5.1 kOhm pulldowns (R1/R2) only. Architecture decision #8
        closed the open question: the whole board draws 293 mA = 1.47 W, and even
        +30 % on every line is 381 mA, under the 450 mA default-source ceiling. Do NOT
        add CC current sensing or a PD controller.
      * U2's ON pin is ACTIVE HIGH, so R3 (100 kOhm) pulls it up to raw VBUS and the
        switch self-enables whenever a host is attached. The TPS22919's internal
        fixed soft-start is what limits inrush -- architecture decision #11 budgets
        118 mA into the ~44 uF of downstream bulk (C2 + C3), i.e. VBUS_SW ramps
        0 -> 5 V in roughly 1.9 ms. That ramp is the timing reference the `power`
        block's +3V3D EN delay is measured against.
      * Raw VBUS carries only C1 (100 nF). Decision #11 caps raw-VBUS capacitance at
        10 uF so the switch, not the connector, absorbs the inrush -- do not add bulk
        upstream of U2.

    Args:
        vbus:    [in]  VBUS -- raw 5 V (4.4-5.25 V) from the host, sourced by J1.
                 J1's VBUS pins are passive in the symbol, so this net has no
                 SKiDL-visible driver; the assembler must set .drive = POWER on it.
        vbus_sw: [out] VBUS_SW -- 5 V after the soft-start switch. Driven by U2.VOUT
                 (a power_out pin), so this net does have a real driver. Feeds both
                 bucks and both analog LDOs in the `power` block.
        usb_dp:  [bidir] USB_DP -- D+ after ESD clamping, to U50.D+.
        usb_dm:  [bidir] USB_DM -- D- after ESD clamping, to U50.D-.
        gnd:     [in]  GND -- single plane (architecture decision, risk R6).
    """
    # ---- Part templates (values/footprints verbatim from sourcing/sourced_bom.md) --
    _r0402 = Part('Device', 'R', dest=TEMPLATE,
                  footprint='Resistor_SMD:R_0402_1005Metric')
    _c0402 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0402_1005Metric')
    _c0805 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0805_2012Metric')

    # ---- Internal nets (net_plan.md rows USB_CC1 / USB_CC2 / PWR_EN) --------------
    usb_cc1 = Net('USB_CC1')   # J1.A5 -> R1 -> GND
    usb_cc2 = Net('USB_CC2')   # J1.B5 -> R2 -> GND
    pwr_en  = Net('PWR_EN')    # R3 -> U2.ON, pulled up to raw VBUS

    # =============================================================================
    # 1. J1 -- USB-C 2.0 receptacle, 16-pin SMD (SHOU HAN TYPE-C 16PIN 2MD(073))
    #    Symbol pin names are the USB-C mechanical designators (A1..A12 / B1..B12,
    #    plus S1 for the shell). The receptacle is reversible, so each function
    #    appears on both the A and B row and the two rows tie together on-board:
    #      VBUS  = A4, B4, A9, B9      GND  = A1, B1, A12, B12
    #      D+    = A6, B6              D-   = A7, B7
    #      CC1   = A5                  CC2  = B5      (NOT tied together)
    #      SBU1  = A8                  SBU2 = B8      (unused on a 2.0-only design)
    # =============================================================================
    J1 = Part('Connector', 'USB_C_Receptacle_USB2.0_16P', ref='J1',
              value='TYPE-C-16PIN-2MD(073)',
              footprint='ProjectLocal:USB_C_Receptacle_TYPE-C-16P-2MD073')

    vbus += J1['A4'], J1['B4'], J1['A9'], J1['B9']
    gnd  += J1['A1'], J1['B1'], J1['A12'], J1['B12']

    # Shell/shield. Single-plane board (risk R6) -- the shell ties straight to GND
    # rather than through the usual cap+resistor hybrid, which only makes sense when
    # there is a separate chassis pour to isolate. ASSUMPTION: net_plan.md is silent
    # on the shield; see the block handoff.
    gnd += J1['S1']

    usb_cc1 += J1['A5']
    usb_cc2 += J1['B5']

    # SBU1/SBU2 carry no function on a USB 2.0-only device. Explicit NC so the
    # assembler's ERC does not flag them and so nobody later assumes they are spare
    # GPIO -- they land on the connector, not on any IC.
    J1['A8'] += NC
    J1['B8'] += NC

    # CC pulldowns -- 5.1 kOhm each, one per CC line, never bridged. Bridging them
    # makes the board look like a powered cable to a PD source.
    R1 = _r0402(ref='R1', value='5.1k')   # CC1 pulldown (Rd)
    R2 = _r0402(ref='R2', value='5.1k')   # CC2 pulldown (Rd)

    usb_cc1 += R1[1]
    usb_cc2 += R2[1]
    gnd     += R1[2], R2[2]

    # =============================================================================
    # 2. U1 -- USBLC6-2SC6, 2-line ESD array, SOT-23-6
    #    Symbol Power_Protection:USBLC6-2SC6 names pins 1 and 6 identically ('I/O1')
    #    and pins 3 and 4 identically ('I/O2') because each pair IS one internal
    #    node -- the protected line passes through the package. Connect both pins of
    #    a pair to the same net; layout routes connector-side in and device-side out
    #    so the clamp sits in the path rather than on a stub.
    #      1, 6 = I/O1 -> USB_DP      3, 4 = I/O2 -> USB_DM
    #      2    = GND                 5    = VBUS (clamp reference / rail diode)
    # =============================================================================
    U1 = Part('Power_Protection', 'USBLC6-2SC6', ref='U1', value='USBLC6-2SC6',
              footprint='Package_TO_SOT_SMD:SOT-23-6')

    usb_dp += J1['A6'], J1['B6'], U1[1], U1[6]
    usb_dm += J1['A7'], J1['B7'], U1[3], U1[4]
    vbus   += U1[5]
    gnd    += U1[2]

    # =============================================================================
    # 3. U2 -- TPS22919DCKR soft-start load switch, SC-70-6
    #    Generated symbol dual_adc_usb:TPS22919DCKR, pins by name:
    #      1 = IN   2 = GND   3 = ON   4 = NC   5 = QOD   6 = VOUT
    #    ON is ACTIVE HIGH (confirmed from two independent JLC data fields; the TI
    #    PDF itself was never obtained -- flagged in the block handoff). If that
    #    polarity is ever proven wrong, R3 moves from VBUS to GND and nothing else
    #    in this block changes.
    # =============================================================================
    U2 = Part('dual_adc_usb', 'TPS22919DCKR', ref='U2', value='TPS22919DCKR',
              footprint='Package_TO_SOT_SMD:SOT-363_SC-70-6')

    vbus    += U2['IN']
    gnd     += U2['GND']
    vbus_sw += U2['VOUT']
    pwr_en  += U2['ON']

    # Pin 4 is a true no-connect on this package.
    U2['NC'] += NC

    # QOD (quick output discharge) left open: leaving it unconnected disables the
    # internal discharge FET. With 44 uF of downstream bulk a fast discharge is not
    # wanted anyway -- it would dump that charge through the switch on every unplug.
    # NOT datasheet-verified (no TI PDF was obtained for this part) -- see handoff.
    U2['QOD'] += NC

    R3 = _r0402(ref='R3', value='100k')   # ON pull-up to raw VBUS -> self-enable
    vbus   += R3[1]
    pwr_en += R3[2]

    # =============================================================================
    # 4. Bulk / bypass
    #    C1 on raw VBUS is deliberately small (100 nF) -- decision #11 keeps raw-VBUS
    #    capacitance under 10 uF so inrush is the switch's problem, not the cable's.
    #    C2 + C3 are the 44 uF downstream bulk that sets the soft-start ramp AND
    #    doubles as the input bulk for U3/U4 in the `power` block -- they must be
    #    placed next to the buck VIN pins, not next to U2. See the block handoff.
    # =============================================================================
    C1 = _c0402(ref='C1', value='100nF')  # raw VBUS HF bypass
    C2 = _c0805(ref='C2', value='22uF')   # VBUS_SW bulk 1 of 2
    C3 = _c0805(ref='C3', value='22uF')   # VBUS_SW bulk 2 of 2

    vbus += C1[1]
    gnd  += C1[2]

    for c in (C2, C3):
        vbus_sw += c[1]
        gnd     += c[2]
