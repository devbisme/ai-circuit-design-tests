"""ADC Dual — ADS5231 dual 12-bit 40 MSPS ADC with internal-reference bypass, ISET and decoupling
Block from: architecture/block_diagram.md
Interface nets: ADC_AINA_P, ADC_AINA_N, ADC_AINB_P, ADC_AINB_N, ADC_VCM, ADC_CLK, ADC_DA[0..11],
                ADC_DB[0..11], ADC_SEL, ADC_MSBI_SEN, ADC_OEA_SCLK, ADC_STPD_SDATA, ADC_OEB, +3V3A, +3V3D, GND
"""
from skidl import *

_R = 'Resistor_SMD:R_0402_1005Metric'
_C0402 = 'Capacitor_SMD:C_0402_1005Metric'
_C0603 = 'Capacitor_SMD:C_0603_1608Metric'


def _c100n(ref):
    return Part('Device', 'C', ref=ref, value='100nF', footprint=_C0402,
                MPN='CL05B104KO5NNNC', LCSC='C1525')


def _c10u(ref):
    return Part('Device', 'C', ref=ref, value='10uF', footprint=_C0603,
                MPN='CL10A106KP8NNNC', LCSC='C19702')


def _c2u2(ref):
    return Part('Device', 'C', ref=ref, value='2.2uF', footprint=_C0402,
                MPN='CL05A225MQ5NSNC', LCSC='C12530')


@SubCircuit
def adc_dual(aina_p, aina_n, ainb_p, ainb_n, adc_vcm, adc_clk, adc_da, adc_db, adc_sel,
             adc_msbi_sen, adc_oea_sclk, adc_stpd_sdata, adc_oeb, v3v3a, v3v3d, gnd):
    """ADS5231 (U7), parallel pin mode, internal reference.
    Inputs: aina_p/n, ainb_p/n (from AFEs), adc_clk (from clock_gen), control pins (from FPGA).
    Outputs: adc_da/adc_db (12-bit Bus, index 0 = LSB), adc_vcm (CM pin, 1.5 V, feeds AFE VOCM).
    Refs: U7, R60-R62, C60-C73. DVA/DVB/OVRA/OVRB left NC (arch rev 2).
    Pins connected by number (symbol dual_adc_usb:ADS5231IPAGT)."""
    u7 = Part('dual_adc_usb', 'ADS5231IPAGT', ref='U7', value='ADS5231IPAGT',
              footprint='Package_QFP:TQFP-64_10x10mm_P0.5mm',
              MPN='ADS5231IPAGT', LCSC='C2670079')

    # --- Analog inputs ---
    u7[50] += aina_p      # INA
    u7[51] += aina_n      # ~{INA}
    u7[63] += ainb_p      # INB
    u7[62] += ainb_n      # ~{INB}
    u7[52] += adc_vcm     # CM (1.5 V output)
    u7[24] += adc_clk     # CLK

    # --- Control (FPGA-driven) ---
    u7[1] += adc_sel           # SEL
    u7[41] += adc_msbi_sen     # MSBI/SEN
    u7[42] += adc_oea_sclk     # OEA/SCLK
    u7[45] += adc_stpd_sdata   # STPD/SDATA
    u7[6] += adc_oeb           # OEB

    # --- Data outputs: D0_A..D11_A = pins 27..38, D0_B..D11_B = pins 10..21 ---
    for i in range(12):
        u7[27 + i] += adc_da[i]
        u7[10 + i] += adc_db[i]

    # --- Unused outputs (arch rev 2) ---
    for pin in (9, 22, 26, 39):   # OVRB, DVB, DVA, OVRA
        u7[pin] += NC

    # --- Internal reference select: INT/~{EXT} high ---
    u7[56] += v3v3a

    # --- Power and ground ---
    for pin in (3, 46, 57):               # AVDD
        u7[pin] += v3v3a
    for pin in (5, 8, 40, 43):            # VDRV
        u7[pin] += v3v3d
    for pin in (2, 47, 48, 49, 55, 58, 59, 61, 64, 4, 7, 23, 25, 44):  # AGND, GND
        u7[pin] += gnd

    # AVDD decoupling: C60-C62 100 nF + C63 10 uF
    for ref in ('C60', 'C61', 'C62'):
        c = _c100n(ref); c[1] += v3v3a; c[2] += gnd
    c = _c10u('C63'); c[1] += v3v3a; c[2] += gnd
    # VDRV decoupling: C64-C67 100 nF + C68 10 uF
    for ref in ('C64', 'C65', 'C66', 'C67'):
        c = _c100n(ref); c[1] += v3v3d; c[2] += gnd
    c = _c10u('C68'); c[1] += v3v3d; c[2] += gnd

    # --- Reference bypass (Fig. 21, K9): pin -> 2 ohm -> 0.1 uF || 2.2 uF to GND ---
    adc_reft, adc_reft_f = Net('ADC_REFT'), Net('ADC_REFT_F')
    adc_refb, adc_refb_f = Net('ADC_REFB'), Net('ADC_REFB_F')
    u7[53] += adc_reft
    u7[54] += adc_refb
    r60 = Part('Device', 'R', ref='R60', value='2R', footprint=_R, MPN='FRC0402F2R00TS', LCSC='C2998051')
    r61 = Part('Device', 'R', ref='R61', value='2R', footprint=_R, MPN='FRC0402F2R00TS', LCSC='C2998051')
    adc_reft & r60 & adc_reft_f
    adc_refb & r61 & adc_refb_f
    c = _c100n('C69'); c[1] += adc_reft_f; c[2] += gnd
    c = _c2u2('C70'); c[1] += adc_reft_f; c[2] += gnd
    c = _c100n('C72'); c[1] += adc_refb_f; c[2] += gnd
    c = _c2u2('C73'); c[1] += adc_refb_f; c[2] += gnd

    # --- Bias current set: ISET -> 56.2 k 1 % -> GND ---
    adc_iset = Net('ADC_ISET')
    u7[60] += adc_iset
    r62 = Part('Device', 'R', ref='R62', value='56.2k', footprint=_R, MPN='0402WGF5622TCE', LCSC='C54968')
    adc_iset & r62 & gnd

    # --- CM output bypass ---
    c = _c100n('C71'); c[1] += adc_vcm; c[2] += gnd
