"""Power Analog — TLV75733P 3.3 V LDO (+3V3A) and LM27762 charge pump + LDOs (VAFE_P/VAFE_N)
Block from: architecture/block_diagram.md
Interface nets: VBUS_SW, +3V3A, VAFE_P, VAFE_N, GND
"""
from skidl import *

_R = 'Resistor_SMD:R_0402_1005Metric'
_C0402 = 'Capacitor_SMD:C_0402_1005Metric'
_C0603 = 'Capacitor_SMD:C_0603_1608Metric'


def _r(ref, value, mpn, lcsc):
    return Part('Device', 'R', ref=ref, value=value, footprint=_R, MPN=mpn, LCSC=lcsc)


def _c(ref, value, fp, mpn, lcsc):
    return Part('Device', 'C', ref=ref, value=value, footprint=fp, MPN=mpn, LCSC=lcsc)


@SubCircuit
def pwr_analog(vbus_sw, v3v3a, vafe_p, vafe_n, gnd):
    """U5 TLV75733P: IN/EN = vbus_sw, OUT -> v3v3a (C10 1 uF in, C11 2.2 uF out).
    U6 LM27762: VIN/EN+/EN- = vbus_sw (C12 2.2 uF), flying C13 1 uF, CP C14 4.7 uF,
    OUT+ -> vafe_p (R10 180k / R11 100k -> +3.360 V, C15 2.2 uF),
    OUT- -> vafe_n (R12 180k / R13 100k -> -3.416 V, C16 2.2 uF).
    PGOOD unused -> GND; GND and thermal PAD (13) -> GND.
    Drives v3v3a, vafe_p, vafe_n directly from the regulators' PWROUT pins. Consumes vbus_sw, gnd."""
    lm_c1p, lm_c1n, lm_cp = Net('LM_C1P'), Net('LM_C1N'), Net('LM_CP')
    fb_afep, fb_afen = Net('FB_AFEP'), Net('FB_AFEN')

    u5 = Part('Regulator_Linear', 'TLV75733PDBV', ref='U5', value='TLV75733PDBVR',
              footprint='Package_TO_SOT_SMD:SOT-23-5', MPN='TLV75733PDBVR', LCSC='C485517')
    u5['IN'] += vbus_sw
    u5['EN'] += vbus_sw
    u5['GND'] += gnd
    u5['NC'] += NC
    u5['OUT'] += v3v3a
    vbus_sw & _c('C10', '1uF', _C0402, 'CL05A105KA5NQNC', 'C52923') & gnd
    v3v3a & _c('C11', '2.2uF', _C0603, 'CL10A225KO8NNNC', 'C23630') & gnd

    u6 = Part('Regulator_SwitchedCapacitor', 'LM27762', ref='U6', value='LM27762DSSR',
              footprint='Package_SON:WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65',
              MPN='LM27762DSSR', LCSC='C473398')
    u6['VIN'] += vbus_sw
    u6['EN+'] += vbus_sw
    u6['EN-'] += vbus_sw
    u6['PGOOD'] += gnd
    u6['GND'] += gnd
    u6['PAD'] += gnd
    u6['C+'] += lm_c1p
    u6['C-'] += lm_c1n
    u6['CP'] += lm_cp
    u6['OUT+'] += vafe_p
    u6['FB+'] += fb_afep
    u6['OUT-'] += vafe_n
    u6['FB-'] += fb_afen

    vbus_sw & _c('C12', '2.2uF', _C0603, 'CL10A225KO8NNNC', 'C23630') & gnd
    lm_c1p & _c('C13', '1uF', _C0402, 'CL05A105KA5NQNC', 'C52923') & lm_c1n
    lm_cp & _c('C14', '4.7uF', _C0603, 'CL10A475KO8NNNC', 'C19666') & gnd
    vafe_p & _r('R10', '180k', '0402WGF1802TCE', 'C25762') & fb_afep & _r('R11', '100k', '0402WGF1003TCE', 'C25741') & gnd
    vafe_n & _r('R12', '180k', '0402WGF1802TCE', 'C25762') & fb_afen & _r('R13', '100k', '0402WGF1003TCE', 'C25741') & gnd
    vafe_p & _c('C15', '2.2uF', _C0603, 'CL10A225KO8NNNC', 'C23630') & gnd
    vafe_n & _c('C16', '2.2uF', _C0603, 'CL10A225KO8NNNC', 'C23630') & gnd
