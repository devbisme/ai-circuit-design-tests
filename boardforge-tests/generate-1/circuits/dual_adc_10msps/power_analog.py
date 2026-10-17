"""Power Analog — FB701-filtered +5VA, LP5907 +3V3A LDO, LM27762 +/-4 V charge pump/LDO
Block from: architecture/block_diagram.md (connections: architecture/net_plan.md Block 3)
Interface nets: +5V, +3V3A, +4V0A, -4V0A, GND
"""
from skidl import *


def _part(lib, name, ref, value, fp, mpn, lcsc):
    p = Part(lib, name, ref=ref, value=value, footprint=fp)
    p.fields['MPN'] = mpn
    p.fields['LCSC'] = lcsc
    return p


_FP_C0402 = 'Capacitor_SMD:C_0402_1005Metric'
_FP_C0603 = 'Capacitor_SMD:C_0603_1608Metric'
_FP_R0402 = 'Resistor_SMD:R_0402_1005Metric'


@SubCircuit
def power_analog(v5, v3v3a, vp4a, vn4a, gnd):
    """+5V -> FB701 -> +5VA -> U701 LP5907-3.3 (+3V3A) and U702 LM27762 (+4V0A / -4V0A).

    Consumes v5. Drives v3v3a (U701 OUT), vp4a (U702 OUT+), vn4a (U702 OUT-), all
    power_out pins. Local +5VA is behind a ferrite -> flagged here.
    VOUT+ = 1.200 x (1 + 232k/100k) = +3.984 V; VOUT- = -1.220 x (1 + 226k/100k) = -3.977 V.
    +3V3A Cout here 1 uF only (rail total <= 10 uF incl. consumers' decoupling).
    """
    v5a = Net('+5VA')
    c1p = Net('LM_C1P')
    c1n = Net('LM_C1N')
    cp = Net('LM_CP')
    fbp = Net('LM_FBP')
    fbn = Net('LM_FBN')

    fb701 = _part('Device', 'FerriteBead', 'FB701', '600R', 'Inductor_SMD:L_0603_1608Metric',
                  'BLM18KG601SN1D', 'C85833')
    v5 += fb701[1]
    v5a += fb701[2]
    v5a.drive = POWER                 # ferrite output feeds U701/U702 power_in pins
    flg = Part('power', 'PWR_FLAG', ref='#FLG701')
    v5a += flg[1]

    c702 = _part('Device', 'C', 'C702', '1u', _FP_C0402, 'CL05A105KA5NQNC', 'C52923')
    c705 = _part('Device', 'C', 'C705', '2.2u', _FP_C0603, 'CL10A225KO8NNNC', 'C23630')
    v5a & c702 & gnd
    v5a & c705 & gnd

    # ---- +3V3A LDO ----
    u701 = _part('Regulator_Linear', 'LP5907MFX-3.3', 'U701', 'LP5907MFX-3.3',
                 'Package_TO_SOT_SMD:SOT-23-5', 'LP5907MFX-3.3/NOPB', 'C80670')
    v5a += u701['IN'], u701['EN']     # EN has 1M pulldown -> tie to IN
    gnd += u701['GND']
    v3v3a += u701['OUT']
    # pin 4 N/C left unconnected
    c703 = _part('Device', 'C', 'C703', '1u', _FP_C0402, 'CL05A105KA5NQNC', 'C52923')
    v3v3a & c703 & gnd

    # ---- +/-4 V charge pump + LDOs ----
    u702 = _part('Regulator_SwitchedCapacitor', 'LM27762', 'U702', 'LM27762DSSR',
                 'Package_SON:WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65', 'LM27762DSSR', 'C473398')
    v5a += u702['VIN'], u702['EN+'], u702['EN-']
    gnd += u702['GND'], u702['PAD']
    # PGOOD (open drain) unused. DS allows GND tie but that clashes with the GND PWR_FLAG
    # (OC vs power_out); DS does not permit floating -> 100k pull-up to +4V0A instead.
    pgood = Net('LM_PGOOD')
    pgood += u702['PGOOD']
    r705 = _part('Device', 'R', 'R705', '100k', _FP_R0402, '0402WGF1003TCE', 'C25741')
    vp4a & r705 & pgood
    c1p += u702['C+']
    c1n += u702['C-']
    cp += u702['CP']
    vp4a += u702['OUT+']
    vn4a += u702['OUT-']
    fbp += u702['FB+']
    fbn += u702['FB-']

    c706 = _part('Device', 'C', 'C706', '1u', _FP_C0402, 'CL05A105KA5NQNC', 'C52923')   # flying cap
    c1p & c706 & c1n
    c707 = _part('Device', 'C', 'C707', '4.7u', _FP_C0603, 'CL10A475KO8NNNC', 'C19666')
    cp & c707 & gnd
    c708 = _part('Device', 'C', 'C708', '2.2u', _FP_C0603, 'CL10A225KO8NNNC', 'C23630')
    c709 = _part('Device', 'C', 'C709', '2.2u', _FP_C0603, 'CL10A225KO8NNNC', 'C23630')
    vp4a & c708 & gnd
    vn4a & c709 & gnd

    r701 = _part('Device', 'R', 'R701', '232k', _FP_R0402, 'FRC0402F2323TS', 'C3013159')
    r702 = _part('Device', 'R', 'R702', '100k', _FP_R0402, '0402WGF1003TCE', 'C25741')
    r703 = _part('Device', 'R', 'R703', '226k', _FP_R0402, 'FRC0402F2263TS', 'C5121518')
    r704 = _part('Device', 'R', 'R704', '100k', _FP_R0402, '0402WGF1003TCE', 'C25741')
    vp4a & r701 & fbp & r702 & gnd
    vn4a & r703 & fbn & r704 & gnd
