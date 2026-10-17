"""ADC — ADS5231 dual 12-bit ADC (run at 10 MSPS, PLL disabled via serial register)
Block from: architecture/block_diagram.md (connections: architecture/net_plan.md Block 5)
Interface nets: AIN_AP, AIN_AN, AIN_BP, AIN_BN, ADC_CM, ADC_CLK, DA0..DA11, DB0..DB11,
                ADC_DVA, ADC_OVRA, ADC_OVRB, ADC_SEL, ADC_SEN, ADC_SCLK, ADC_SDATA,
                +3V3A, +3V3, GND
"""
from skidl import *

# Footprint / MPN strings (sourcing/sourced_bom.csv, verbatim)
_FP_C0402 = 'Capacitor_SMD:C_0402_1005Metric'
_FP_C0603 = 'Capacitor_SMD:C_0603_1608Metric'
_FP_R0402 = 'Resistor_SMD:R_0402_1005Metric'
_FP_RN = 'Resistor_SMD:R_Array_Convex_4x0402'
_FP_FB = 'Inductor_SMD:L_0603_1608Metric'
_FP_ADC = 'Package_QFP:TQFP-64_10x10mm_P0.5mm'

_MPN_100N = 'CL05B104KB54PNC'
_LCSC_100N = 'C307331'
_MPN_1U = 'CL05A105KA5NQNC'
_LCSC_1U = 'C52923'
_MPN_4U7 = 'CL10A475KO8NNNC'
_LCSC_4U7 = 'C19666'


def _cap(ref, value, mpn, lcsc, fp):
    c = Part('Device', 'C', ref=ref, value=value, footprint=fp)
    c.fields['MPN'] = mpn
    c.fields['LCSC'] = lcsc
    return c


def _res(ref, value, mpn, lcsc):
    r = Part('Device', 'R', ref=ref, value=value, footprint=_FP_R0402)
    r.fields['MPN'] = mpn
    r.fields['LCSC'] = lcsc
    return r


@SubCircuit
def adc(ain_ap, ain_an, ain_bp, ain_bn, adc_cm, adc_clk, da, db, adc_dva, adc_ovra,
        adc_ovrb, adc_sel, adc_sen, adc_sclk, adc_sdata, v3v3a, v3v3, gnd):
    """ADS5231 dual ADC with references, bias, decoupling and 33R output series arrays.

    Inputs: ain_ap/an, ain_bp/bn (differential from afe_channel THS4551s), adc_clk (CMOS
    10 MHz), adc_sel/sen/sclk/sdata (serial control from FPGA; 10k pull-downs hold parallel
    mode, outputs enabled, while FPGA unconfigured).
    Outputs: adc_cm (1.5 V CM, feeds THS4551 VOCM), da[0..11]/db[0..11] via 33R arrays,
    adc_dva, adc_ovra, adc_ovrb.
    Power: v3v3a -> AVDD (+ INT/EXT high = internal reference); v3v3 -> FB301 -> local
    +3V3_ADCIO -> VDRV. da/db are indexable 12-wide buses (index 0 = LSB).
    """
    u = Part('dual_adc_10msps', 'ADS5231IPAGT', ref='U301', value='ADS5231IPAGT',
             footprint=_FP_ADC)
    u.fields['MPN'] = 'ADS5231IPAGT'
    u.fields['LCSC'] = 'C2670079'

    # ---- Ground (AGND and output-buffer GND both to the single GND net) ----
    for p in (2, 47, 48, 49, 55, 58, 59, 61, 64):   # AGND
        gnd += u[p]
    for p in (4, 7, 23, 25, 44):                     # GND
        gnd += u[p]
    gnd += u[6]                                      # OEB = 0 -> channel B outputs enabled

    # ---- Analog supply +3V3A: AVDD 3, 46, 57; INT/EXT 56 = 1 (internal reference) ----
    for p in (3, 46, 57, 56):
        v3v3a += u[p]
    for ref in ('C305', 'C306', 'C307'):
        c = _cap(ref, '100n', _MPN_100N, _LCSC_100N, _FP_C0402)
        v3v3a += c[1]
        gnd += c[2]
    c308 = _cap('C308', '4.7u', _MPN_4U7, _LCSC_4U7, _FP_C0603)
    v3v3a += c308[1]
    gnd += c308[2]

    # ---- Output-driver supply: +3V3 -> FB301 -> +3V3_ADCIO -> VDRV 5, 8, 40, 43 ----
    adcio = Net('+3V3_ADCIO')
    adcio.drive = POWER          # ferrite output is the source for the VDRV power_in pins
    flg = Part('power', 'PWR_FLAG', ref='#FLG301')   # KiCad ERC: source flag behind FB301
    adcio += flg[1]
    fb = Part('Device', 'FerriteBead', ref='FB301', value='600R', footprint=_FP_FB)
    fb.fields['MPN'] = 'BLM18KG601SN1D'
    fb.fields['LCSC'] = 'C85833'
    v3v3 += fb[1]
    adcio += fb[2]
    for p in (5, 8, 40, 43):
        adcio += u[p]
    for ref in ('C309', 'C310', 'C311', 'C312'):
        c = _cap(ref, '100n', _MPN_100N, _LCSC_100N, _FP_C0402)
        adcio += c[1]
        gnd += c[2]
    c313 = _cap('C313', '4.7u', _MPN_4U7, _LCSC_4U7, _FP_C0603)
    adcio += c313[1]
    gnd += c313[2]

    # ---- Analog inputs ----
    ain_ap += u[50]   # INA+
    ain_an += u[51]   # INA-
    ain_bp += u[63]   # INB+
    ain_bn += u[62]   # INB-

    # ---- Common mode output 1.5 V ----
    adc_cm += u[52]
    c303 = _cap('C303', '100n', _MPN_100N, _LCSC_100N, _FP_C0402)
    c304 = _cap('C304', '1u', _MPN_1U, _LCSC_1U, _FP_C0402)
    for c in (c303, c304):
        adc_cm += c[1]
        gnd += c[2]

    # ---- References: REFT/REFB each 2 ohm + 0.1 uF to GND ----
    reft = Net('ADC_REFT')
    refb = Net('ADC_REFB')
    reft_rc = Net('REFT_RC')
    refb_rc = Net('REFB_RC')
    reft += u[53]
    refb += u[54]
    r302 = _res('R302', '2', 'FRC0402F2R00TS', 'C2998051')
    r303 = _res('R303', '2', 'FRC0402F2R00TS', 'C2998051')
    c301 = _cap('C301', '100n', _MPN_100N, _LCSC_100N, _FP_C0402)
    c302 = _cap('C302', '100n', _MPN_100N, _LCSC_100N, _FP_C0402)
    reft += r302[1]
    reft_rc += r302[2], c301[1]
    gnd += c301[2]
    refb += r303[1]
    refb_rc += r303[2], c302[1]
    gnd += c302[2]

    # ---- Bias current set: ISET 56.2k 1 % to GND ----
    iset = Net('ADC_ISET')
    r301 = _res('R301', '56.2k', 'FRC0402F5622TS', 'C5126096')
    iset += u[60], r301[1]
    gnd += r301[2]

    # ---- Clock ----
    adc_clk += u[24]

    # ---- Serial control pins with 10k pull-downs (parallel mode default) ----
    for pin, net, ref in ((1, adc_sel, 'R304'), (41, adc_sen, 'R305'),
                          (42, adc_sclk, 'R306'), (45, adc_sdata, 'R307')):
        r = _res(ref, '10k', '0402WGF1002TCE', 'C25744')
        net += u[pin], r[1]
        gnd += r[2]

    # ---- Status outputs ----
    adc_dva += u[26]   # DVA
    adc_ovra += u[39]  # OVRA
    adc_ovrb += u[9]   # OVRB
    u[22] += NC        # DVB unused (DVA clocks both channels)

    # ---- Data outputs through 33R arrays: element k (k=1..4) = pin k (ADC) <-> pin 9-k ----
    def _data(chan, first_adc_pin, out_bus, rn_refs):
        for i in range(12):
            rn_idx, k = divmod(i, 4)
            rn = rn_parts[rn_refs[rn_idx]]
            local = Net('{}_ADC{}'.format(chan, i))
            local += u[first_adc_pin + i], rn[k + 1]
            out_bus[i] += rn[8 - k]

    rn_parts = {}
    for ref in ('RN301', 'RN302', 'RN303', 'RN304', 'RN305', 'RN306'):
        rn = Part('Device', 'R_Pack04', ref=ref, value='33', footprint=_FP_RN)
        rn.fields['MPN'] = '4D02WGJ0330TCE'
        rn.fields['LCSC'] = 'C25501'
        rn_parts[ref] = rn

    _data('DA', 27, da, ('RN301', 'RN302', 'RN303'))   # D0_A..D11_A = pins 27..38
    _data('DB', 10, db, ('RN304', 'RN305', 'RN306'))   # D0_B..D11_B = pins 10..21
