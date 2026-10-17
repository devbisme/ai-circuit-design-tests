"""Power Digital — TLV62569 3.3 V buck + TLV75712 1.2 V LDO + power LED
Block from: architecture/block_diagram.md (connections: architecture/net_plan.md Block 2)
Interface nets: +5V, +3V3, +1V2, GND
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
def power_digital(v5, v3v3, v1v2, gnd):
    """+5V -> U601 TLV62569 buck (1.5 MHz, L601 2.2 uH) -> +3V3 -> U602 TLV75712 -> +1V2.

    Consumes v5. Drives v3v3 (via L601, flagged here) and v1v2 (U602 OUT power_out).
    VOUT = 0.6 V x (1 + 453k/100k) = 3.318 V. C604 6.8 pF feed-forward across R601.
    L601 check: ripple dI = 3.3*(1-3.3/5)/(2.2u*1.5M) = 0.34 A; peak at 0.36 A load
    = 0.53 A << Isat 2.8 A. ILIM (DBV) 3 A typ > Isat: saturates only under short.
    """
    sw = Net('SW_3V3')
    fb = Net('FB_3V3')
    led = Net('LED_PWR')

    # ---- Buck ----
    u601 = _part('Regulator_Switching', 'TLV62569DBV', 'U601', 'TLV62569DBVR',
                 'Package_TO_SOT_SMD:SOT-23-5', 'TLV62569DBVR', 'C141836')
    v5 += u601['VIN'], u601['EN']        # EN must not float -> tie to VIN
    gnd += u601['GND']
    sw += u601['SW']
    fb += u601['FB']

    c601 = _part('Device', 'C', 'C601', '4.7u', _FP_C0603, 'CL10A475KO8NNNC', 'C19666')
    v5 & c601 & gnd

    l601 = _part('Device', 'L', 'L601', '2.2uH', 'Inductor_SMD:L_1008_2520Metric',
                 'TMS252012ALM-2R2MTAA', 'C1017131')
    sw += l601[1]
    v3v3 += l601[2]

    c602 = _part('Device', 'C', 'C602', '10u', _FP_C0603, 'CL10A106KP8NNNC', 'C19702')
    c603 = _part('Device', 'C', 'C603', '10u', _FP_C0603, 'CL10A106KP8NNNC', 'C19702')
    v3v3 & c602 & gnd
    v3v3 & c603 & gnd

    r601 = _part('Device', 'R', 'R601', '453k', _FP_R0402, '0402WGF4533TCE', 'C27009')
    r602 = _part('Device', 'R', 'R602', '100k', _FP_R0402, '0402WGF1003TCE', 'C25741')
    c604 = _part('Device', 'C', 'C604', '6.8p', _FP_C0402, '0402CG6R8C500NT', 'C1576')
    v3v3 & r601 & fb & r602 & gnd
    v3v3 & c604 & fb

    # +3V3 leaves the buck through a passive (inductor): source flag
    v3v3.drive = POWER
    flg = Part('power', 'PWR_FLAG', ref='#FLG601')
    v3v3 += flg[1]

    # ---- 1.2 V LDO ----
    u602 = _part('Regulator_Linear', 'TLV75712PDBV', 'U602', 'TLV75712PDBVR',
                 'Package_TO_SOT_SMD:SOT-23-5', 'TLV75712PDBVR', 'C1509296')
    v3v3 += u602['IN'], u602['EN']       # EN has no internal pull -> tie to IN
    gnd += u602['GND']
    v1v2 += u602['OUT']
    # pin 4 NC (no_connect in symbol) left unconnected

    c605 = _part('Device', 'C', 'C605', '1u', _FP_C0402, 'CL05A105KA5NQNC', 'C52923')
    c606 = _part('Device', 'C', 'C606', '1u', _FP_C0402, 'CL05A105KA5NQNC', 'C52923')
    v3v3 & c605 & gnd
    v1v2 & c606 & gnd

    # ---- Power LED ----
    r604 = _part('Device', 'R', 'R604', '1k', _FP_R0402, '0402WGF1001TCE', 'C11702')
    d601 = _part('Device', 'LED', 'D601', 'LED_Green', 'LED_SMD:LED_0603_1608Metric',
                 'PSC-1608U52GC-G4', 'C22371297')
    v3v3 & r604 & led
    led += d601['A']
    gnd += d601['K']
