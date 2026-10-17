"""AFE Channel — +/-10 V BNC input to differential ADC drive (instantiated for ch "A" and "B")
Block from: architecture/block_diagram.md (topology/values: architecture/net_plan.md Block 4)
Interface nets: A: VIN_A, AIN_AP, AIN_AN; B: VIN_B, AIN_BP, AIN_BN;
                both: ADC_CM, +4V0A, -4V0A, +3V3A, GND
"""
from skidl import *

# Footprint strings (sourcing/sourced_bom.csv, verbatim)
_FP_0402_C = 'Capacitor_SMD:C_0402_1005Metric'
_FP_0603_C = 'Capacitor_SMD:C_0603_1608Metric'
_FP_0402_R = 'Resistor_SMD:R_0402_1005Metric'
_FP_0603_R = 'Resistor_SMD:R_0603_1608Metric'
_FP_1206_R = 'Resistor_SMD:R_1206_3216Metric'

# (index, value, MPN, footprint) — index n gives ref R1nn / R2nn
_RES = [
    (1, '953k', 'WR12X9533FTL', 'C368327', _FP_1206_R),
    (2, '49.9k', '0603WAF4992T5E', 'C23184', _FP_0603_R),
    (3, '1k', '0603WAF1001T5E', 'C21190', _FP_0603_R),
    (4, '887', 'CRCW0402887RFKED', 'C4012675', _FP_0402_R),
    (5, '453', 'FRC0402F4530TS', 'C5126227', _FP_0402_R),
    (6, '374', 'RMS04FT3740', 'C208875', _FP_0402_R),
    (7, '232', 'GR0402F232RTAG00', 'C49655645', _FP_0402_R),
    (8, '698', 'GR0402F698RTAG00', 'C49655034', _FP_0402_R),
    (9, '698', 'GR0402F698RTAG00', 'C49655034', _FP_0402_R),
    (10, '1.27k', 'FRC0402F1271TS', 'C3013151', _FP_0402_R),
    (11, '1.27k', 'FRC0402F1271TS', 'C3013151', _FP_0402_R),
    (12, '576', '0402WGF5760TCE', 'C45320', _FP_0402_R),
    (13, '576', '0402WGF5760TCE', 'C45320', _FP_0402_R),
    (14, '46.4', 'RC0402FR-0746R4L', 'C273734', _FP_0402_R),
    (15, '46.4', 'RC0402FR-0746R4L', 'C273734', _FP_0402_R),
]

_CAP = [
    (1, '8.2p', 'GQM1875C2E8R2CB12D', 'C3874850', _FP_0603_C),
    # 2 = trimmer, created separately
    (3, '220p', 'GCM1885C2A221JA16D', 'C388907', _FP_0603_C),
    (4, '270p', 'GRM1555C1H271GA01D', 'C161546', _FP_0402_C),
    (5, '100p', '0603CG101G500NT', 'C182932', _FP_0603_C),
    (6, '1.8n', 'GRM1885C1H182FA01D', 'C882525', _FP_0603_C),
    (7, '82p', 'GQM1875C2E820GB12D', 'C2171259', _FP_0603_C),
    (8, '330p', 'GRM1555C1H331GA01D', 'C237507', _FP_0402_C),
    (9, '330p', 'GRM1555C1H331GA01D', 'C237507', _FP_0402_C),
    (10, '82p', 'GQM1875C2E820GB12D', 'C2171259', _FP_0603_C),
    (11, '82p', 'GQM1875C2E820GB12D', 'C2171259', _FP_0603_C),
    (12, '1.2n', 'GCM1885C1H122FA16D', 'C1517816', _FP_0603_C),
    (13, '100n', 'CL05B104KB54PNC', 'C307331', _FP_0402_C),
    (14, '100n', 'CL05B104KB54PNC', 'C307331', _FP_0402_C),
    (15, '100n', 'CL05B104KB54PNC', 'C307331', _FP_0402_C),
    (16, '100n', 'CL05B104KB54PNC', 'C307331', _FP_0402_C),
    (17, '100n', 'CL05B104KB54PNC', 'C307331', _FP_0402_C),
    (18, '1u', 'CL05A105KA5NQNC', 'C52923', _FP_0402_C),
    (19, '10n', 'CL05B103KB5NNNC', 'C15195', _FP_0402_C),
    (20, '2.2u', 'CL10A225KO8NNNC', 'C23630', _FP_0603_C),
    (21, '2.2u', 'CL10A225KO8NNNC', 'C23630', _FP_0603_C),
]


@SubCircuit
def afe_channel(ch, vin, ain_p, ain_n, adc_cm, vp4a, vn4a, v3v3a, gnd):
    """One analog front-end channel.

    ch     : "A" (refs 1xx, local nets *_A) or "B" (refs 2xx, local nets *_B).
    vin    : BNC centre conductor (VIN_A / VIN_B), sensed only.
    ain_p/ain_n : differential ADC drive (AIN_xP / AIN_xN), driven by U1x3 via 46.4R + 1.2nF.
    adc_cm : ADS5231 CM output (1.5 V) -> THS4551 VOCM; sensed only (ADC drives it).
    vp4a/vn4a : +/-4 V op-amp rails; v3v3a : THS4551 supply; gnd : single ground. All consumed.

    Chain: /20.10 compensated attenuator -> 1k + BAV199 clamp -> OPA2810 A buffer ->
    Sallen-Key a (OPA2810 B) -> Sallen-Key b (OPA810) -> THS4551 MFB (G 1.8195, SE->diff)
    -> 2x46.4R + 1.2nF -> ADC. Values fixed by architecture (pre-distorted for 70 MHz GBW).
    """
    if ch not in ('A', 'B'):
        raise ValueError(f'afe_channel: ch must be "A" or "B", got {ch!r}')
    base = 100 if ch == 'A' else 200
    sfx = f'_{ch}'

    def ref(prefix, n):
        return f'{prefix}{base + n}'

    # ---- Passives ----
    R = {}
    for n, val, mpn, lcsc, fp in _RES:
        r = Part('Device', 'R', ref=ref('R', n), value=val, footprint=fp)
        r.fields['MPN'] = mpn
        r.fields['LCSC'] = lcsc
        R[n] = r
    C = {}
    for n, val, mpn, lcsc, fp in _CAP:
        c = Part('Device', 'C', ref=ref('C', n), value=val, footprint=fp)
        c.fields['MPN'] = mpn
        c.fields['LCSC'] = lcsc
        C[n] = c
    C[2] = Part('Device', 'C_Trim', ref=ref('C', 2), value='3.3p',
                footprint='my_board:C_Trimmer_SEHWA_STC3MA06')
    C[2].fields['MPN'] = 'STC3MA06-T1'
    C[2].fields['LCSC'] = 'C22468120'

    # ---- Active / connector parts ----
    J = Part('Connector', 'Conn_Coaxial', ref=ref('J', 1), value='BNC',
             footprint='my_board:BNC_KH-BNC50-3511')
    J.fields['MPN'] = 'KH-BNC50-3511'
    J.fields['LCSC'] = 'C2837587'
    D = Part('Diode', 'BAV99', ref=ref('D', 1), value='BAV199',
             footprint='Package_TO_SOT_SMD:SOT-23')
    D.fields['MPN'] = 'BAV199'
    D.fields['LCSC'] = 'C68971'
    U1 = Part('dual_adc_10msps', 'OPA2810IDR', ref=ref('U', 1), value='OPA2810IDR',
              footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')
    U1.fields['MPN'] = 'OPA2810IDR'
    U1.fields['LCSC'] = 'C1849413'
    U2 = Part('Amplifier_Operational', 'OPA810xDBV', ref=ref('U', 2), value='OPA810IDBVR',
              footprint='Package_TO_SOT_SMD:SOT-23-5')
    U2.fields['MPN'] = 'OPA810IDBVR'
    U2.fields['LCSC'] = 'C2833513'
    U3 = Part('Amplifier_Difference', 'THS4551xRGT', ref=ref('U', 3), value='THS4551IRGTR',
              footprint='Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm')
    U3.fields['MPN'] = 'THS4551IRGTR'
    U3.fields['LCSC'] = 'C2869590'

    # ---- Local nets ----
    att = Net('ATT' + sfx)
    bufin = Net('BUFIN' + sfx)
    buf = Net('BUF' + sfx)
    ska1 = Net('SKA1' + sfx)
    ska2 = Net('SKA2' + sfx)
    ska = Net('SKA' + sfx)
    skb1 = Net('SKB1' + sfx)
    skb2 = Net('SKB2' + sfx)
    skb = Net('SKB' + sfx)
    mfx_p = Net('MFX_P' + sfx)
    mfx_n = Net('MFX_N' + sfx)
    fda_inp = Net('FDA_INP' + sfx)
    fda_inn = Net('FDA_INN' + sfx)
    fda_outp = Net('FDA_OUTP' + sfx)
    fda_outn = Net('FDA_OUTN' + sfx)

    # ---- BNC input ----
    vin += J[1]                 # centre contact
    gnd += J[2]                 # shell / ground lead (all pad-2 pads)

    # ---- Compensated attenuator /20.10 ----
    vin += R[1][1], C[1][1], C[2][1]
    att += R[1][2], C[1][2], C[2][2], R[2][1], C[3][1], R[3][1]
    gnd += R[2][2], C[3][2]

    # ---- Series R + BAV199 clamp (connect by PIN NUMBER: 1 lower anode, 2 upper cathode, 3 common)
    bufin += R[3][2], D[3]
    vp4a += D[2]
    vn4a += D[1]

    # ---- U101 A: unity buffer ----
    bufin += U1['VIN1+']
    buf += U1['VO1'], U1['VIN1-'], R[4][1]

    # ---- Sallen-Key a (U101 B) ----
    ska1 += R[4][2], R[5][1], C[4][1]
    ska2 += R[5][2], C[5][1], U1['VIN2+']
    gnd += C[5][2]
    ska += U1['VO2'], U1['VIN2-'], C[4][2], R[6][1]

    # ---- Sallen-Key b (U102 OPA810: 1 VO, 2 VS-, 3 VIN+, 4 VIN-, 5 VS+) ----
    skb1 += R[6][2], R[7][1], C[6][1]
    skb2 += R[7][2], C[7][1], U2[3]
    gnd += C[7][2]
    skb += U2[1], U2[4], C[6][2], R[8][1]

    # ---- THS4551 MFB, single-ended -> differential ----
    mfx_p += R[8][2], C[8][1], R[10][1], R[12][1]
    mfx_n += R[9][2], C[9][1], R[11][1], R[13][1]
    gnd += R[9][1], C[8][2], C[9][2]
    fda_inp += R[12][2], C[10][1], U3[2]       # IN+
    fda_inn += R[13][2], C[11][1], U3[3]       # IN-
    fda_outn += U3[11], R[10][2], C[10][2], R[15][1]   # OUT-
    fda_outp += U3[10], R[11][2], C[11][2], R[14][1]   # OUT+
    adc_cm += U3[9], C[19][1]                  # VOCM <- ADC CM
    gnd += C[19][2]
    U3[1] += NC                                # FB- (internal tap of OUT-), intentional NC
    U3[4] += NC                                # FB+ (internal tap of OUT+), intentional NC

    # ---- ADC drive RC ----
    ain_p += R[14][2], C[12][1]
    ain_n += R[15][2], C[12][2]

    # ---- Power ----
    vp4a += U1['VS+'], U2[5], C[13][1], C[15][1], C[20][1]
    vn4a += U1['VS-'], U2[2], C[14][1], C[16][1], C[21][1]
    v3v3a += U3[5], U3[6], U3[7], U3[8], U3[12], C[17][1], C[18][1]   # VS+ x4, ~PD high = on
    gnd += U3[13], U3[14], U3[15], U3[16], U3[17]                     # VS- x4, EP
    gnd += C[13][2], C[14][2], C[15][2], C[16][2], C[17][2], C[18][2], C[20][2], C[21][2]
