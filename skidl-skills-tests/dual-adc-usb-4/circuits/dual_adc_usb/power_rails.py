"""Power Rails — linear regulators for VD_3V3, VD_1V8, VD_1V2 and VA_3V3, power LED, rail test points
Block from: architecture/block_diagram.md (power_rails)
Interface nets: VBUS_SW, VD_3V3, VD_1V8, VD_1V2, VA_3V3, GND
Net plan: architecture/net_plan.md §1 and §10 (test points).
Parts: sourcing/sourced_bom.md § power_rails.
"""
from skidl import *

# Passive catalogue: value -> (footprint, MPN, LCSC). Single source of truth for this block.
_CAPS = {
    '10uF': ('Capacitor_SMD:C_0805_2012Metric', 'CL21A106KAYNNNE', 'C15850'),
    '100nF': ('Capacitor_SMD:C_0402_1005Metric', 'CL05B104KB54PNC', 'C307331'),
    '1uF': ('Capacitor_SMD:C_0402_1005Metric', 'CL05A105KA5NQNC', 'C52923'),
}
_TP_FP = 'TestPoint:TestPoint_Pad_D1.5mm'
_SOT23_5 = 'Package_TO_SOT_SMD:SOT-23-5'


def _cap(ref, value, a, b):
    """One capacitor between nets a and b."""
    fp, mpn, lcsc = _CAPS[value]
    c = Part('Device', 'C', ref=ref, value=value, footprint=fp, MPN=mpn, LCSC=lcsc)
    a & c & b


def _tp(ref, net):
    """One test point on a net."""
    tp = Part('Connector', 'TestPoint', ref=ref, value=net.name, footprint=_TP_FP)
    tp[1] += net


def _sot23_ldo(ref, lib, name, mpn, lcsc, vin, vout, gnd, c_in, c_out):
    """SOT-23-5 fixed LDO (IN/GND/EN/NC/OUT) with EN tied to IN and 1 uF in/out caps."""
    u = Part(lib, name, ref=ref, value=mpn, footprint=_SOT23_5, MPN=mpn, LCSC=lcsc)
    u['IN'] += vin
    u['EN'] += vin                # always enabled with its input
    u['GND'] += gnd
    u['OUT'] += vout
    u['NC'] += NC
    _cap(c_in, '1uF', vin, gnd)
    _cap(c_out, '1uF', vout, gnd)


@SubCircuit
def power_rails(vbus_sw, vd_3v3, vd_1v8, vd_1v2, va_3v3, gnd):
    """All-linear power tree fed from the switched USB 5 V.

    U3 TLV1117LV33  VBUS_SW -> VD_3V3 (digital 3.3 V, ~240 mA)
    U4 TLV75512     VD_3V3  -> VD_1V2 (FPGA core)
    U5 TLV75518     VD_3V3  -> VD_1V8 (FPGA bank 3 / PSRAM, JTAG VREF)
    U6 TPS7A2033    VBUS_SW -> VA_3V3 (low-noise analog 3.3 V)
    LED1 + R5 power indicator on VD_3V3; TP1-TP6 rail test points.

    Args:
        vbus_sw: 5 V switched input from usb_power_in. CONSUMED (driven by U2 there).
        vd_3v3, vd_1v8, vd_1v2, va_3v3: regulator outputs. DRIVEN here (drive=POWER).
        gnd:     Common ground.

    Assumptions: all EN pins are tied to their regulator's input (always on). Downstream IC
    decoupling belongs to the consumer blocks; this block only has the regulators' own caps.
    """
    for rail in (vd_3v3, vd_1v8, vd_1v2, va_3v3):
        rail.drive = POWER

    # U3 — TLV1117LV33DCYR (genuine TI), SOT-223, tab = OUT. C5 in, C6 + C7 out.
    u3 = Part('Regulator_Linear', 'TLV1117-33', ref='U3', value='TLV1117LV33DCYR',
              footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2',
              MPN='TLV1117LV33DCYR', LCSC='C15578')
    u3['VI'] += vbus_sw
    u3['VO'] += vd_3v3
    u3['GND'] += gnd
    _cap('C5', '10uF', vbus_sw, gnd)
    _cap('C6', '10uF', vd_3v3, gnd)
    _cap('C7', '100nF', vd_3v3, gnd)

    # U4 — TLV75512PDBVR, VD_3V3 -> VD_1V2. C8 in, C9 out.
    _sot23_ldo('U4', 'Regulator_Linear', 'TLV75512PDBV', 'TLV75512PDBVR', 'C2877864',
               vd_3v3, vd_1v2, gnd, 'C8', 'C9')

    # U5 — TLV75518PDBVR, VD_3V3 -> VD_1V8. C10 in, C11 out.
    _sot23_ldo('U5', 'Regulator_Linear', 'TLV75518PDBV', 'TLV75518PDBVR', 'C2877863',
               vd_3v3, vd_1v8, gnd, 'C10', 'C11')

    # U6 — TPS7A2033PDBVR (generated symbol), VBUS_SW -> VA_3V3. C12 in, C13 out.
    _sot23_ldo('U6', 'dual_adc_usb', 'TPS7A2033PDBVR', 'TPS7A2033PDBVR', 'C2862740',
               vbus_sw, va_3v3, gnd, 'C12', 'C13')

    # Power LED on VD_3V3: R5 (1k) -> LED1 (green) -> GND.
    r5 = Part('Device', 'R', ref='R5', value='1k', footprint='Resistor_SMD:R_0603_1608Metric',
              MPN='0603WAF1001T5E', LCSC='C21190')
    led1 = Part('Device', 'LED', ref='LED1', value='green', footprint='LED_SMD:LED_0603_1608Metric',
                MPN='CT-1608UGC-P4', LCSC='C52675989')
    vd_3v3 & r5 & led1['A', 'K'] & gnd

    # Test points (net_plan §10).
    for ref, net in (('TP1', vbus_sw), ('TP2', vd_3v3), ('TP3', vd_1v8),
                     ('TP4', vd_1v2), ('TP5', va_3v3), ('TP6', gnd)):
        _tp(ref, net)
