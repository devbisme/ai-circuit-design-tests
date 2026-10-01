"""Power Digital — three TLV62569DBV bucks from VBUS_SW: +3V3D (EN-delayed), +1V2, +1V8
Block from: architecture/block_diagram.md
Interface nets: VBUS_SW, +3V3D, +1V2, +1V8, GND
"""
from skidl import *

_R = 'Resistor_SMD:R_0402_1005Metric'
_C0402 = 'Capacitor_SMD:C_0402_1005Metric'
_C0603 = 'Capacitor_SMD:C_0603_1608Metric'
_C0805 = 'Capacitor_SMD:C_0805_2012Metric'
_L = 'Inductor_SMD:L_Changjiang_FNR4020S'


def _r(ref, value, mpn, lcsc):
    return Part('Device', 'R', ref=ref, value=value, footprint=_R, MPN=mpn, LCSC=lcsc)


def _c(ref, value, fp, mpn, lcsc):
    return Part('Device', 'C', ref=ref, value=value, footprint=fp, MPN=mpn, LCSC=lcsc)


def _buck(ref, lref, vin, en, sw, fb, vout, gnd):
    u = Part('Regulator_Switching', 'TLV62569DBV', ref=ref, value='TLV62569DBVR',
             footprint='Package_TO_SOT_SMD:SOT-23-5', MPN='TLV62569DBVR', LCSC='C141836')
    u['VIN'] += vin
    u['EN'] += en
    u['GND'] += gnd
    u['SW'] += sw
    u['FB'] += fb
    l = Part('Device', 'L', ref=lref, value='2.2uH', footprint=_L,
             MPN='FHD4020S-2R2MT', LCSC='C602029')
    sw & l & vout
    return u


@SubCircuit
def pwr_digital(vbus_sw, v3v3d, v1v2, v1v8, gnd):
    """U3 -> v3v3d (R5 100k / R6 22k -> 3.327 V), EN via R9 100k / C8 100 nF RC delay (2.0-3.2 ms).
    U4 -> v1v2 (R7 100k / R8 100k -> 1.200 V), EN = vbus_sw.
    U12 -> v1v8 (R14 200k / R15 100k -> 1.800 V), EN = vbus_sw (VCC and VCCO3 ramp together, UG284).
    Inputs: C4/C6/C9 10 uF on vbus_sw. Outputs: C5/C7/C17 22 uF.
    Drives v3v3d, v1v2, v1v8 (marked .drive = POWER here: the regulator's PWROUT pin is SW,
    which reaches the rail only through the passive inductor). Consumes vbus_sw, gnd.
    Assumption K10: +1V8 load <= 100 mA (unverified, accepted)."""
    for rail in (v3v3d, v1v2, v1v8):
        rail.drive = POWER

    sw_3v3, fb_3v3, en_3v3 = Net('SW_3V3'), Net('FB_3V3'), Net('EN_3V3')
    sw_1v2, fb_1v2 = Net('SW_1V2'), Net('FB_1V2')
    sw_1v8, fb_1v8 = Net('SW_1V8'), Net('FB_1V8')

    # +3V3D (U3), enable delayed by R9/C8 so it follows +1V2/+1V8
    _buck('U3', 'L1', vbus_sw, en_3v3, sw_3v3, fb_3v3, v3v3d, gnd)
    v3v3d & _r('R5', '100k', '0402WGF1003TCE', 'C25741') & fb_3v3 & _r('R6', '22k', '0402WGF2202TCE', 'C25768') & gnd
    vbus_sw & _r('R9', '100k', '0402WGF1003TCE', 'C25741') & en_3v3 & _c('C8', '100nF', _C0402, 'CL05B104KO5NNNC', 'C1525') & gnd
    vbus_sw & _c('C4', '10uF', _C0603, 'CL10A106KP8NNNC', 'C19702') & gnd
    v3v3d & _c('C5', '22uF', _C0805, 'CL21A226MAQNNNE', 'C45783') & gnd

    # +1V2 (U4)
    _buck('U4', 'L2', vbus_sw, vbus_sw, sw_1v2, fb_1v2, v1v2, gnd)
    v1v2 & _r('R7', '100k', '0402WGF1003TCE', 'C25741') & fb_1v2 & _r('R8', '100k', '0402WGF1003TCE', 'C25741') & gnd
    vbus_sw & _c('C6', '10uF', _C0603, 'CL10A106KP8NNNC', 'C19702') & gnd
    v1v2 & _c('C7', '22uF', _C0805, 'CL21A226MAQNNNE', 'C45783') & gnd

    # +1V8 (U12)
    _buck('U12', 'L3', vbus_sw, vbus_sw, sw_1v8, fb_1v8, v1v8, gnd)
    v1v8 & _r('R14', '200k', '0402WGF2003TCE', 'C25764') & fb_1v8 & _r('R15', '100k', '0402WGF1003TCE', 'C25741') & gnd
    vbus_sw & _c('C9', '10uF', _C0603, 'CL10A106KP8NNNC', 'C19702') & gnd
    v1v8 & _c('C17', '22uF', _C0805, 'CL21A226MAQNNNE', 'C45783') & gnd
