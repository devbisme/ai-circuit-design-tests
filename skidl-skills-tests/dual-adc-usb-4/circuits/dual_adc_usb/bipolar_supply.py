"""Bipolar Supply — LM27762 charge pump + LDOs generating the +/-2.5 V front-end rails
Block from: architecture/block_diagram.md (bipolar_supply)
Interface nets: VBUS_SW, VA_P2V5, VA_N2V5, GND
Net plan: architecture/net_plan.md §1 (CP_VIN, VA_P2V5_R/VA_N2V5_R, VA_P2V5, VA_N2V5) and §3.
Parts: sourcing/sourced_bom.md § bipolar_supply; R6-R9 values from datasheets/LM27762DSSR_SUMMARY.md.
"""
from skidl import *

# Passive catalogue: value -> (footprint, MPN, LCSC). Single source of truth for this block.
_CAPS = {
    '10uF': ('Capacitor_SMD:C_0603_1608Metric', 'CL10A106MA8NRNC', 'C96446'),
    '100nF': ('Capacitor_SMD:C_0402_1005Metric', 'CL05B104KB54PNC', 'C307331'),
    '1uF': ('Capacitor_SMD:C_0402_1005Metric', 'CL05A105KA5NQNC', 'C52923'),
    '2.2uF': ('Capacitor_SMD:C_0603_1608Metric', '0603B225K160NT', 'C43922'),
}
# FB dividers: VOUT+ = 1.2 V * (R6+R7)/R7 = 2.484 V; VOUT- = -1.22 V * (R8+R9)/R9 = -2.501 V.
_RES = {
    '107k': ('Resistor_SMD:R_0402_1005Metric', 'RC0402FR-07107KL', 'C138070'),
    '105k': ('Resistor_SMD:R_0402_1005Metric', '0402WGF1053TCE', 'C25742'),
    '100k': ('Resistor_SMD:R_0402_1005Metric', '0402WGF1003TCE', 'C25741'),
}
_TP_FP = 'TestPoint:TestPoint_Pad_D1.5mm'


def _cap(ref, value, a, b):
    """One capacitor between nets a and b."""
    fp, mpn, lcsc = _CAPS[value]
    c = Part('Device', 'C', ref=ref, value=value, footprint=fp, MPN=mpn, LCSC=lcsc)
    a & c & b


def _res(ref, value, a, b):
    """One resistor between nets a and b."""
    fp, mpn, lcsc = _RES[value]
    r = Part('Device', 'R', ref=ref, value=value, footprint=fp, MPN=mpn, LCSC=lcsc)
    a & r & b


def _fb(ref, a, b):
    """One 600R@100MHz ferrite bead between nets a and b."""
    fb = Part('Device', 'FerriteBead', ref=ref, value='600R@100MHz',
              footprint='Inductor_SMD:L_0805_2012Metric', MPN='BLM21PG601SN1D', LCSC='C41556732')
    a & fb & b


@SubCircuit
def bipolar_supply(vbus_sw, va_p2v5, va_n2v5, gnd):
    """+/-2.5 V supply for the analog front end (OPA354 buffers, BAV199 clamps).

    FB2 isolates the 2 MHz charge pump from VBUS_SW (local CP_VIN). U7 LM27762 inverts VIN to
    CP_NEG and regulates OUT+ / OUT- via external dividers; FB3/FB4 + C20/C21 post-filter the
    LDO outputs into VA_P2V5 / VA_N2V5.

    Args:
        vbus_sw: 5 V switched input. CONSUMED (driven by usb_power_in).
        va_p2v5: +2.5 V filtered output. DRIVEN here (drive=POWER).
        va_n2v5: -2.5 V filtered output. DRIVEN here (drive=POWER).
        gnd:     Common ground.

    Assumptions: EN+ and EN- tied to CP_VIN (always on); PGOOD unused and tied to GND per
    SNVSAF7C pin table ("Connect to ground if not used").
    """
    va_p2v5.drive = POWER
    va_n2v5.drive = POWER

    # Block-local nets (net_plan §1 / §3).
    cp_vin = Net('CP_VIN')
    cp_vin.drive = POWER          # fed only through FB2 (passive)
    cp_flyp = Net('CP_FLYP')
    cp_flyn = Net('CP_FLYN')
    cp_neg = Net('CP_NEG')
    cp_fbp = Net('CP_FBP')
    cp_fbn = Net('CP_FBN')
    vp_r = Net('VA_P2V5_R')
    vn_r = Net('VA_N2V5_R')

    # Input filter: FB2 from VBUS_SW, C14 10uF + C15 100nF on CP_VIN.
    _fb('FB2', vbus_sw, cp_vin)
    _cap('C14', '10uF', cp_vin, gnd)
    _cap('C15', '100nF', cp_vin, gnd)

    # U7 — LM27762DSSR, WSON-12 + EP (pin 13 PAD -> GND).
    u7 = Part('Regulator_SwitchedCapacitor', 'LM27762', ref='U7', value='LM27762DSSR',
              footprint='Package_SON:WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65',
              MPN='LM27762DSSR', LCSC='C473398')
    u7['VIN'] += cp_vin
    u7['EN+'] += cp_vin
    u7['EN-'] += cp_vin
    u7['GND'] += gnd
    u7['PAD'] += gnd
    u7['PGOOD'] += gnd
    u7['C+'] += cp_flyp
    u7['C-'] += cp_flyn
    u7['CP'] += cp_neg
    u7['FB+'] += cp_fbp
    u7['FB-'] += cp_fbn
    u7['OUT+'] += vp_r
    u7['OUT-'] += vn_r

    # Charge pump: C16 1uF flying cap, C17 2.2uF on the unregulated negative output.
    _cap('C16', '1uF', cp_flyp, cp_flyn)
    _cap('C17', '2.2uF', cp_neg, gnd)

    # Positive LDO: R6 (OUT+ -> FB+), R7 (FB+ -> GND), C18 output cap.
    _res('R6', '107k', vp_r, cp_fbp)
    _res('R7', '100k', cp_fbp, gnd)
    _cap('C18', '2.2uF', vp_r, gnd)

    # Negative LDO: R8 (OUT- -> FB-), R9 (FB- -> GND), C19 output cap.
    _res('R8', '105k', vn_r, cp_fbn)
    _res('R9', '100k', cp_fbn, gnd)
    _cap('C19', '2.2uF', vn_r, gnd)

    # Post-filters: FB3/C20 -> VA_P2V5, FB4/C21 -> VA_N2V5.
    _fb('FB3', vp_r, va_p2v5)
    _cap('C20', '10uF', va_p2v5, gnd)
    _fb('FB4', vn_r, va_n2v5)
    _cap('C21', '10uF', va_n2v5, gnd)

    # Test points (net_plan §10).
    for ref, net in (('TP7', va_p2v5), ('TP8', va_n2v5)):
        tp = Part('Connector', 'TestPoint', ref=ref, value=net.name, footprint=_TP_FP)
        tp[1] += net
