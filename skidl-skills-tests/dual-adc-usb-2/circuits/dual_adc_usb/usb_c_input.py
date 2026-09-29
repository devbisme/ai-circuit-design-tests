"""USB-C Input & Protection -- receptacle, CC sink pull-downs, VBUS fuse/bulk/TVS,
D+/D- common-mode filtering + ESD clamp
Block from: architecture/block_diagram.md
Interface nets: VBUS, GND, USB_DP, USB_DM
"""
from skidl import *


@subcircuit
def usb_c_input(vbus, gnd, usb_dp, usb_dm):
    """USB-C receptacle input stage (net_plan.md secs 1-2).

    Topology (architecture-fixed):
      - J1 CC1/CC2 -> R1/R2 (5.1 kOhm 1%, [FIXED] USB-C sink advertisement) -> GND.
      - J1 SHIELD -> R3 (1 Mohm) || C2 (4.7 nF/2 kV) -> GND, single-point chassis tie.
      - J1 VBUS (x4 pins) -> F1 (polyfuse) -> `vbus` (interface net). C1 (10 uF bulk,
        [FIXED] <=10 uF total per USB inrush limit) and D2 (TVS) sit on `vbus`,
        post-fuse, pre-regulator (power_digital's U1 AP7361C-33E IN).
      - J1 D+/D- -> FB1 (common-mode choke, 2 independent windings) -> `usb_dp`/`usb_dm`
        (interface nets). D1 (USBLC6-2SC6 dual-line ESD array) shunts `usb_dp`/`usb_dm`
        (and `vbus`) to GND at this same node -- it is a shunt clamp, not a series
        element, so it lands on the same node the choke's output already defines; this
        node is what continues on to usb_bridge's U6 (FT232H) D+/D-.

    Args:
        vbus: USB-C bus power, post-fuse/post-bulk-cap/post-TVS. Feeds power_digital
            block's AP7361C-33E (U1) IN pin.
        gnd: Ground reference.
        usb_dp: USB2 HS D+ line, post-common-mode-choke, post-ESD-clamp. Feeds
            usb_bridge block's FT232H (U6) DP pin.
        usb_dm: USB2 HS D- line, post-common-mode-choke, post-ESD-clamp. Feeds
            usb_bridge block's FT232H (U6) DM pin.
    """

    # --- J1: USB-C receptacle, USB2.0-only 16-pin variant ---
    # MPN XKB U262-16XN-4BVC11 (sourcing-corrected suffix; matches the footprint below).
    j1 = Part(
        "Connector",
        "USB_C_Receptacle_USB2.0_16P",
        ref="J1",
        value="USB-C Receptacle (USB2.0)",
        footprint="Connector_USB:USB_C_Receptacle_XKB_U262-16XN-4BVC11",
    )

    # Raw (pre-fuse) VBUS net straight off the connector's 4 VBUS pins (A4,A9,B4,B9).
    vbus_raw = Net("usbVbusRaw")
    j1["VBUS"] += vbus_raw
    # All 4 GND pins (A1,A12,B1,B12) tie to the shared ground reference.
    j1["GND"] += gnd

    # SBU1/SBU2 unused -- USB2.0-only application, no alt-mode/sideband use.
    j1["SBU1"] += NC
    j1["SBU2"] += NC

    # --- CC1/CC2 pull-downs: fixed USB-C sink advertisement (R1, R2 = 5.1 kOhm 1%) ---
    # Each CC line gets its own independent pull-down -- do not tie CC1/CC2 together.
    r1 = Part("Device", "R", ref="R1", value="5.1k 1%", footprint="Resistor_SMD:R_0402_1005Metric")
    j1["CC1"] += r1[1]
    r1[2] += gnd

    r2 = Part("Device", "R", ref="R2", value="5.1k 1%", footprint="Resistor_SMD:R_0402_1005Metric")
    j1["CC2"] += r2[1]
    r2[2] += gnd

    # --- SHIELD: single-point chassis tie, R3 (1 Mohm bleed) parallel with C2 (4.7 nF/2 kV) ---
    shield = Net("usbShield")
    j1["SHIELD"] += shield

    r3 = Part("Device", "R", ref="R3", value="1M", footprint="Resistor_SMD:R_0402_1005Metric")
    r3[1] += shield
    r3[2] += gnd

    # C2: Murata GA355-series safety Y-cap equivalent, 4.7 nF/2 kV -- moved to 1808 case
    # size per sourcing (2 kV rating does not exist in a standard 0603 ceramic case).
    c2 = Part("Device", "C", ref="C2", value="4.7nF 2kV", footprint="Capacitor_SMD:C_1808_4520Metric")
    c2[1] += shield
    c2[2] += gnd

    # --- VBUS: F1 (polyfuse) -> `vbus` -> C1 (bulk) + D2 (TVS) ---
    # F1: MF-MSMF050-2, 500 mA hold / 1 A trip. Unnamed pins ("~"/1,2) -- polarity-agnostic.
    f1 = Part("Device", "Polyfuse", ref="F1", value="500mA Hold / 1A Trip", footprint="Fuse:Fuse_1206_3216Metric")
    f1[1] += vbus_raw
    f1[2] += vbus

    # C1: 10 uF X5R 16 V bulk cap on `vbus`. [FIXED] <=10 uF total -- this is the ONLY
    # bulk cap this block places on VBUS, per the USB inrush-current limit.
    c1 = Part("Device", "C", ref="C1", value="10uF", footprint="Capacitor_SMD:C_0805_2012Metric")
    c1[1] += vbus
    c1[2] += gnd

    # D2: Nexperia PESD5V0S1BA, bidirectional TVS, post-fuse/pre-regulator VBUS clamp.
    # Generic Device:D_TVS symbol -- pins A1/A2 are the two (interchangeable) terminals.
    d2 = Part("Device", "D_TVS", ref="D2", value="PESD5V0S1BA", footprint="Diode_SMD:D_SOD-323")
    d2["A1"] += vbus
    d2["A2"] += gnd

    # --- D+/D-: FB1 (common-mode choke) -> `usb_dp`/`usb_dm`, D1 (ESD array) shunts there ---
    # FB1: DLW21SN900HQ2L, 90 ohm @ 100 MHz. Device:Filter_EMI_CommonMode has 2 independent
    # windings: pins 1<->2 (winding A) and pins 3<->4 (winding B). Winding A carries D+,
    # winding B carries D-. Pin-1/3 = connector side (raw), pin-2/4 = downstream side
    # (the protected interface net).
    fb1 = Part(
        "Device",
        "Filter_EMI_CommonMode",
        ref="FB1",
        value="90ohm@100MHz",
        footprint="Inductor_SMD:L_CommonModeChoke_Coilcraft_0805USB",
    )

    dp_raw = Net("usbDpRaw")
    dm_raw = Net("usbDmRaw")
    j1["D+"] += dp_raw
    j1["D-"] += dm_raw

    fb1[1] += dp_raw
    fb1[2] += usb_dp
    fb1[3] += dm_raw
    fb1[4] += usb_dm

    # D1: USBLC6-2SC6 dual-line ESD array. Pins I/O1 (1,6) and I/O2 (3,4) are each
    # dual-bonded pairs on the SAME net -- indexing by name ties both automatically.
    # Placed (schematically) right at the protected node so it clamps `usb_dp`/`usb_dm`
    # and `vbus` -- it is a shunt device, not in series with the signal path.
    d1 = Part("Power_Protection", "USBLC6-2SC6", ref="D1", value="USBLC6-2SC6", footprint="Package_TO_SOT_SMD:SOT-23-6")
    d1["I/O1"] += usb_dp
    d1["I/O2"] += usb_dm
    d1["VBUS"] += vbus
    d1["GND"] += gnd

    # No IC decoupling in this block -- J1 (connector), F1 (fuse), D1/D2 (passive ESD/TVS
    # diodes), FB1 (passive choke), R1-R3 (resistors) are all passive; none has a VCC pin.
