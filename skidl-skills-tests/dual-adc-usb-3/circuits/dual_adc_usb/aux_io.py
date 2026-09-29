"""Aux I/O — external trigger header with ESD protection, power and capture LEDs
Block from: architecture/block_diagram.md  (block_id: aux_io)
Interface nets: +3V3, +3V3_AON, GND, TRIG_IO, LED_CAP_N

Implements architecture/net_plan.md "## USB / config / aux nets" rows TRIG_IO,
LED_CAP_N and LED_PWR.

The power LED hangs off +3V3_AON so it lights as soon as the board is plugged in,
before enumeration — it indicates "USB power present", which is what you want when
debugging a board that is failing to enumerate. The capture LED is driven by the
FPGA and is therefore only alive once PWR_EN has brought the main rails up.
"""
from skidl import *


@SubCircuit
def aux_io(v3v3, v3v3_aon, gnd, trig_io, led_cap_n):
    """External trigger I/O and the two status LEDs.

    Args:
        v3v3 (Net): INPUT. Switched 3.3 V rail — the trigger header's reference pin.
        v3v3_aon (Net): INPUT. Always-on 3.3 V — powers the PWR LED.
        gnd (Net): INPUT. Single GND net.
        trig_io (Net): BIDIRECTIONAL. 3.3 V logic trigger to/from the FPGA (Bank 1),
                       through a 100 R series resistor and an ESD clamp.
        led_cap_n (Net): INPUT. Active-low capture indicator from the FPGA. Driven at
                       1.8 V (amendment A2) — the series resistor below is sized for
                       that, not for 3.3 V.

    LED currents: the amber capture LED runs from a 1.8 V Bank-3 pin, so with a ~1.9 V
    forward drop it would barely conduct if wired LED-to-ground. It is therefore wired
    as a SINK: anode to +3V3 through the series resistor, cathode to the FPGA pin, so
    the FPGA pulls it low to light it. Current = (3.3 - 1.9 - Vol) / 1k ~ 1.3 mA,
    which is plenty for a modern high-efficiency 0603 and keeps the Bank-3 pin inside
    its sink rating. This is why the net is named LED_CAP_N (active low).
    """

    r_0402 = Part('Device', 'R', dest=TEMPLATE,
                  footprint='Resistor_SMD:R_0402_1005Metric')

    # ---- J4: 1x3 external trigger header (SPEC I10) ------------------------------
    # pin 1 = +3V3 reference, pin 2 = TRIG_IO, pin 3 = GND
    J4 = Part('Connector_Generic', 'Conn_01x03', ref='J4', value='EXT TRIG',
              footprint='Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical')
    J4[1] += v3v3
    J4[3] += gnd

    # Series resistor then the ESD clamp, so the clamp sees the connector side and
    # the resistor limits what reaches the FPGA pin.
    R43 = r_0402(ref='R43', value='100')
    trig_pin = Net('TRIG_PIN')
    J4[2] += trig_pin
    trig_pin & R43 & trig_io

    D4 = Part('Device', 'D_TVS', ref='D4', value='PESD3V3L1BA',
              footprint='Diode_SMD:D_SOD-323')
    D4[1] += trig_pin
    D4[2] += gnd

    # ---- D5: power LED, green, off the always-on rail ----------------------------
    D5 = Part('Device', 'LED', ref='D5', value='XL-1608UGC-04 green',
              footprint='LED_SMD:LED_0603_1608Metric')
    R46 = r_0402(ref='R46', value='1k')
    v3v3_aon & R46 & D5 & gnd          # ~1.4 mA, deliberately dim (SPEC P3 budget)

    # ---- D6: capture LED, amber, sunk by the FPGA (see docstring) ----------------
    D6 = Part('Device', 'LED', ref='D6', value='SML-D12D8WT86 amber',
              footprint='LED_SMD:LED_0603_1608Metric')
    R45 = r_0402(ref='R45', value='1k')
    v3v3 & R45 & D6 & led_cap_n

    # ---- Test points (SPEC N5) ---------------------------------------------------
    tp = Part('Connector', 'TestPoint', dest=TEMPLATE,
              footprint='TestPoint:TestPoint_Pad_D1.0mm')
    for ref, net in [('TP16', trig_io), ('TP17', v3v3), ('TP18', v3v3_aon), ('TP19', gnd)]:
        tp(ref=ref, value=net.name)[1] += net
