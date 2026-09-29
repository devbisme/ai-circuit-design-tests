"""Analog Front End — 2-ch BNC attenuator/buffer/driver
Block from: architecture/block_diagram.md (analog_front_end); topology per architecture/net_plan.md §4
Interface nets: AIN_A_P, AIN_A_N, AIN_B_P, AIN_B_N, ADC_VCM, VA_3V3, VA_P2V5, VA_N2V5, GND
"""
from skidl import *

# ---------------------------------------------------------------------------
# BOM for ONE channel — single source of truth, taken from
# sourcing/sourced_bom.md § analog_front_end (channel A refs; channel B = +10 for R/C).
# role: (ref offset, lib, symbol, value, MPN, LCSC, footprint)
# ---------------------------------------------------------------------------
_R0402 = 'Resistor_SMD:R_0402_1005Metric'
_R0603 = 'Resistor_SMD:R_0603_1608Metric'
_R1206 = 'Resistor_SMD:R_1206_3216Metric'
_C0402 = 'Capacitor_SMD:C_0402_1005Metric'
_C0603 = 'Capacitor_SMD:C_0603_1608Metric'

_RC_BOM = {
    # --- compensated 10:1 attenuator, 1 MOhm || ~20 pF to GND (net_plan AFE_x_MID/TAP)
    'r_top1':  ('R', 10, 'Device', 'R', '453k',   'FRC1206F4533TS',     'C2999488',  _R1206),  # 1% 200V
    'r_top2':  ('R', 11, 'Device', 'R', '453k',   'FRC1206F4533TS',     'C2999488',  _R1206),  # 1% 200V
    'r_bot':   ('R', 12, 'Device', 'R', '100k',   'RT0603BRD07100KL',   'C122538',   _R0603),  # 0.1% 25ppm
    'c_top':   ('C', 30, 'Device', 'C', '15pF',   'GCM1885C2A150JA16D', 'C388905',   _C0603),  # C0G 100V
    'c_bot':   ('C', 31, 'Device', 'C', '160pF',  'GRM1885C1H161JA01D', 'C710893',   _C0603),  # C0G 50V
    # --- clamp current limit into buffer
    'r_iso':   ('R', 13, 'Device', 'R', '1k',     '0603WAF1001T5E',     'C21190',    _R0603),
    # --- OPA354 decoupling (V+ / V-)
    'c_dec_p': ('C', 32, 'Device', 'C', '100nF',  'CL05B104KB54PNC',    'C307331',   _C0402),
    'c_dec_n': ('C', 33, 'Device', 'C', '100nF',  'CL05B104KB54PNC',    'C307331',   _C0402),
    # --- THS4521 gain network, gain Rf/Rg = 1.00k/1.10k = 0.909, Rf*Cf pole 7.2 MHz
    'rg_p':    ('R', 14, 'Device', 'R', '1.10k',  'PTFR0603B1K10P9',    'C351674',   _R0603),  # 0.1% matched
    'rg_n':    ('R', 15, 'Device', 'R', '1.10k',  'PTFR0603B1K10P9',    'C351674',   _R0603),  # 0.1% matched
    'rf_p':    ('R', 16, 'Device', 'R', '1.00k',  'FRH0603B1001TS',     'C49196685', _R0603),  # 0.1% matched
    'rf_n':    ('R', 17, 'Device', 'R', '1.00k',  'FRH0603B1001TS',     'C49196685', _R0603),  # 0.1% matched
    'cf_p':    ('C', 34, 'Device', 'C', '22pF',   'GRM1555C2A220JA01D', 'C710855',   _C0402),  # C0G 100V
    'cf_n':    ('C', 35, 'Device', 'C', '22pF',   'GRM1555C2A220JA01D', 'C710855',   _C0402),  # C0G 100V
    # --- output RC anti-alias filter, (2*49.9R)*220pF pole 7.2 MHz
    'r_out_p': ('R', 18, 'Device', 'R', '49.9',   '0402WGF499JTCE',     'C25120',    _R0402),
    'r_out_n': ('R', 19, 'Device', 'R', '49.9',   '0402WGF499JTCE',     'C25120',    _R0402),
    'c_diff':  ('C', 36, 'Device', 'C', '220pF',  'GRM1555C1H221JA01D', 'C71693',    _C0402),  # C0G 50V
    # --- THS4521 VS+ decoupling and VOCM decoupling
    'c_dec_f': ('C', 37, 'Device', 'C', '100nF',  'CL05B104KB54PNC',    'C307331',   _C0402),
    'c_vocm':  ('C', 38, 'Device', 'C', '100nF',  'CL05B104KB54PNC',    'C307331',   _C0402),
}

# Non-R/C parts: (ref prefix, number for ch A, step to ch B, lib, symbol, value, MPN, LCSC, footprint)
_IC_BOM = {
    # BNC-KWE-6 footprint: project-local, built from cntitle drawing CT3.660.861 (the BOM's
    # Amphenol 031-6575 string is a DUAL BNC — see handoffs/05_blocks/analog_front_end.md).
    'bnc':  ('J',  2, 1, 'Connector', 'Conn_Coaxial', 'BNC-KWE-6', 'BNC-KWE-6', 'C20415789',
             'ProjectLocal:BNC_cntitle_BNC-KWE-6_Horizontal'),
    # STC3MA06-T1 footprint: project-local, per SEHWA STC3M-SP-15 p.3 land pattern.
    'trim': ('VC', 1, 1, 'Device', 'C_Trim', '2-6pF', 'STC3MA06-T1', 'C22468120',
             'ProjectLocal:C_Trimmer_SEHWA_STC3M'),
    'clamp': ('D', 2, 1, 'dual_adc_usb', 'BAV199', 'BAV199', 'BAV199', 'C5184419',
              'Package_TO_SOT_SMD:SOT-23'),
    'buf':  ('U',  8, 2, 'dual_adc_usb', 'OPA354AIDBVR', 'OPA354AIDBVR', 'OPA354AIDBVR', 'C36384',
             'Package_TO_SOT_SMD:SOT-23-5'),
    'fda':  ('U',  9, 2, 'Amplifier_Difference', 'THS4521IDGK', 'THS4521IDGKR', 'THS4521IDGKR',
             'C170157', 'Package_SO:VSSOP-8_3x3mm_P0.65mm'),
}


def _part(lib, symbol, ref, value, mpn, lcsc, footprint):
    """The one Part() factory for this block — every part gets ref, value, footprint, MPN, LCSC."""
    part = Part(lib, symbol, ref=ref, value=value, footprint=footprint)
    # Set via .fields: a new key passed as a Part() kwarg becomes a plain attribute, not a
    # netlist/BOM field (SkidlBaseObject.__setattr__ only routes keys already in .fields).
    part.fields['MPN'] = mpn
    part.fields['LCSC'] = lcsc
    return part


def _afe_channel(ch, idx, ain_p, ain_n, adc_vcm, va_3v3, va_p2v5, va_n2v5, gnd):
    """One front-end channel: BNC -> 10:1 compensated divider -> BAV199 clamp -> OPA354 buffer
    -> THS4521 SE-to-diff (gain 0.909, VOCM = ADC_VCM) -> 49.9R/220pF filter -> ADC.

    ch: 'A' or 'B' (net-name prefix); idx: 0 or 1 (refdes offset per sourced_bom.md).
    """
    p = {}
    for role, (pfx, n, lib, sym, val, mpn, lcsc, fp) in _RC_BOM.items():
        p[role] = _part(lib, sym, f'{pfx}{n + 10 * idx}', val, mpn, lcsc, fp)
    for role, (pfx, n, step, lib, sym, val, mpn, lcsc, fp) in _IC_BOM.items():
        p[role] = _part(lib, sym, f'{pfx}{n + step * idx}', val, mpn, lcsc, fp)

    # Channel-local nets (net_plan.md §4)
    bnc = Net(f'BNC_{ch}')
    mid = Net(f'AFE_{ch}_MID')
    tap = Net(f'AFE_{ch}_TAP')
    bufin = Net(f'AFE_{ch}_BUFIN')
    buf = Net(f'AFE_{ch}_BUF')
    fip = Net(f'AFE_{ch}_FIP')
    fin = Net(f'AFE_{ch}_FIN')
    fon = Net(f'AFE_{ch}_FON')
    fop = Net(f'AFE_{ch}_FOP')

    # BNC: pin 1 = In (center), pin 2 = Ext (shield, all 4 legs in the footprint)
    p['bnc'][1] += bnc
    p['bnc'][2] += gnd

    # Compensated divider: 906k (2x453k) top || C_top + VC, 100k bottom || C_bot
    bnc & p['r_top1'] & mid & p['r_top2'] & tap
    bnc & (p['c_top'] | p['trim']) & tap
    tap & (p['r_bot'] | p['c_bot']) & gnd

    # BAV199 series pair: pin1 A1 -> -2.5V, pin2 K2 -> +2.5V, pin3 K1_A2 (junction) -> TAP
    clamp = p['clamp']
    clamp['A1'] += va_n2v5
    clamp['K2'] += va_p2v5
    clamp['K1_A2'] += tap

    # OPA354 unity buffer on +/-2.5V (SOT-23-5: 1 OUT, 2 V-, 3 IN+, 4 IN-, 5 V+)
    u_buf = p['buf']
    tap & p['r_iso'] & bufin
    u_buf['IN+'] += bufin
    buf += u_buf['OUT'], u_buf['IN-']   # unity-gain feedback
    u_buf['V+'] += va_p2v5
    u_buf['V-'] += va_n2v5
    va_p2v5 & p['c_dec_p'] & gnd
    va_n2v5 & p['c_dec_n'] & gnd

    # THS4521 FDA on 3.3V single supply. KiCad symbol pin names are '+', '-', '~{PD}' and the
    # outputs are unnamed, so connect by number (TI SLOS577 p.4, DGK pinout):
    # 1 VIN-, 2 VOCM, 3 VS+, 4 VOUT+, 5 VOUT-, 6 VS-, 7 PD (active LOW), 8 VIN+
    u_fda = p['fda']
    buf & p['rg_p'] & fip          # Rg from buffer into IN+
    gnd & p['rg_n'] & fin          # Rg from GND into IN-
    u_fda[8] += fip
    u_fda[1] += fin
    u_fda[5] += fon                # VOUT-
    u_fda[4] += fop                # VOUT+
    fon & (p['rf_p'] | p['cf_p']) & fip   # feedback OUT- -> IN+  => OUT+ in phase with BNC
    fop & (p['rf_n'] | p['cf_n']) & fin   # feedback OUT+ -> IN-
    u_fda[2] += adc_vcm            # VOCM = ADS5231 CM (1.5V)
    u_fda[3] += va_3v3             # VS+
    u_fda[6] += gnd                # VS-
    u_fda[7] += va_3v3             # PD: "logic high or open for normal operation" (SLOS577 p.4)
    va_3v3 & p['c_dec_f'] & gnd
    adc_vcm & p['c_vocm'] & gnd

    # Output anti-alias RC into the ADC
    fop & p['r_out_p'] & ain_p
    fon & p['r_out_n'] & ain_n
    ain_p & p['c_diff'] & ain_n


@SubCircuit
def analog_front_end(ain_a_p, ain_a_n, ain_b_p, ain_b_n, adc_vcm, va_3v3, va_p2v5, va_n2v5, gnd):
    """Two identical scope-style input channels (A: J2/U8/U9, B: J3/U10/U11).

    Each: BNC (1 MOhm || ~20 pF to GND) -> 906k/100k compensated 10:1 divider (VC1/VC2 trimmed
    with a 1 kHz square wave) -> BAV199 clamp to +/-2.5 V -> 1k -> OPA354 unity buffer (+/-2.5 V)
    -> THS4521 single-ended-to-differential, gain 0.909, output CM = ADC_VCM -> 49.9R/220pF
    -> AIN_x_P / AIN_x_N. +/-10 V at the BNC gives +/-0.904 V differential at the ADC.

    Inputs (consumed): va_3v3 (THS4521 VS+ and PD), va_p2v5 / va_n2v5 (OPA354 rails, clamp
    rails), adc_vcm (driven by ADS5231 CM pin; this block only loads it), gnd.
    Outputs (driven): ain_a_p, ain_a_n, ain_b_p, ain_b_n.
    Assumes bulk (10 uF) decoupling on VA_3V3 / VA_P2V5 / VA_N2V5 lives in the supply blocks.
    """
    rails = dict(adc_vcm=adc_vcm, va_3v3=va_3v3, va_p2v5=va_p2v5, va_n2v5=va_n2v5, gnd=gnd)
    _afe_channel('A', 0, ain_a_p, ain_a_n, **rails)
    _afe_channel('B', 1, ain_b_p, ain_b_n, **rails)
