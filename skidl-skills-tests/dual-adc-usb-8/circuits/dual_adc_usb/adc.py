"""ADC — ADS5231 dual 12-bit 40 MSPS ADC, parallel-pin mode, internal reference
Block from: architecture/block_diagram.md (adc)
Interface nets: AIN_A_P, AIN_A_N, AIN_B_P, AIN_B_N, VCM, ADC_CLK, DA0..DA11, DB0..DB11,
                ADC_DVA, ADC_STPD, V3V3A, GND
"""
from skidl import *


@SubCircuit
def adc(ain_a_p, ain_a_n, ain_b_p, ain_b_n, vcm, adc_clk, da, db, adc_dva, adc_stpd, v3v3a, gnd):
    """U8 ADS5231 dual ADC.

    Inputs: ain_a_p/n, ain_b_p/n (differential, CM = vcm), adc_clk (40 MHz CMOS),
    adc_stpd (FPGA-driven, R15 10k pull-down, high = power-down), v3v3a, gnd.
    Outputs: vcm (U8.CM pin 52, OUTPUT pin, ~1.5 V, decoupled C20 0.1u + C21 1u),
    da[0..11] = D0_A..D11_A, db[0..11] = D0_B..D11_B (index 0 = LSB), adc_dva (DVA).
    Mode: SEL/OEB/MSBI/OEA tied to GND (parallel mode, outputs on, offset binary);
    INT/EXT -> v3v3a (internal reference). VDRV fed from v3v3a via FB1 (local ADC_VDRV)
    so |AVDD - VDRV| <= 0.3 V always. DVB, OVRA, OVRB left NC per net_plan.
    """
    adc_vdrv = Net('ADC_VDRV')
    adc_vdrv.drive = POWER      # powered from v3v3a through FB1 (passive)
    adc_iset = Net('ADC_ISET')
    adc_reft_c = Net('ADC_REFT_C')
    adc_refb_c = Net('ADC_REFB_C')

    U8 = Part('dual_adc_usb', 'ADS5231IPAGT', ref='U8', value='ADS5231IPAGT',
              footprint='Package_QFP:TQFP-64_10x10mm_P0.5mm')

    # --- supplies ---
    for n in (3, 46, 57):                               # AVDD
        U8[n] += v3v3a
    for n in (5, 8, 40, 43):                            # VDRV
        U8[n] += adc_vdrv
    for n in (2, 47, 48, 49, 55, 58, 59, 61, 64):       # AGND
        U8[n] += gnd
    for n in (4, 7, 23, 25, 44):                        # driver GND
        U8[n] += gnd

    FB1 = Part('Device', 'FerriteBead', ref='FB1', value='600R',
               footprint='Inductor_SMD:L_0603_1608Metric')
    FB1[1] += v3v3a
    FB1[2] += adc_vdrv

    c_0402 = 'Capacitor_SMD:C_0402_1005Metric'
    c_0603 = 'Capacitor_SMD:C_0603_1608Metric'
    # AVDD: one 0.1u per pin (C22-C24) + 10u bulk (C25)
    for ref in ('C22', 'C23', 'C24'):
        v3v3a & Part('Device', 'C', ref=ref, value='100nF', footprint=c_0402) & gnd
    v3v3a & Part('Device', 'C', ref='C25', value='10uF', footprint=c_0603) & gnd
    # VDRV: one 0.1u per pin (C26-C29) + 10u bulk (C30)
    for ref in ('C26', 'C27', 'C28', 'C29'):
        adc_vdrv & Part('Device', 'C', ref=ref, value='100nF', footprint=c_0402) & gnd
    adc_vdrv & Part('Device', 'C', ref='C30', value='10uF', footprint=c_0603) & gnd

    # --- reference / bias ---
    U8['INT/EXT'] += v3v3a                               # pin 56: 1 = internal ref
    U8['ISET'] += adc_iset                               # pin 60
    adc_iset & Part('Device', 'R', ref='R12', value='56.2k',
                    footprint='Resistor_SMD:R_0603_1608Metric') & gnd
    R13 = Part('Device', 'R', ref='R13', value='2', footprint='Resistor_SMD:R_0603_1608Metric')
    R14 = Part('Device', 'R', ref='R14', value='2', footprint='Resistor_SMD:R_0603_1608Metric')
    C18 = Part('Device', 'C', ref='C18', value='100nF', footprint=c_0402)
    C19 = Part('Device', 'C', ref='C19', value='100nF', footprint=c_0402)
    U8['REFT'] & R13 & adc_reft_c & C18 & gnd           # pin 53 -> 2R -> 0.1u
    U8['REFB'] & R14 & adc_refb_c & C19 & gnd           # pin 54 -> 2R -> 0.1u

    # --- common-mode output (drives VCM for both FDAs) ---
    U8['CM'] += vcm                                      # pin 52 (OUTPUT)
    vcm & Part('Device', 'C', ref='C20', value='100nF', footprint=c_0402) & gnd
    vcm & Part('Device', 'C', ref='C21', value='1uF', footprint=c_0402) & gnd

    # --- analog inputs ---
    U8[50] += ain_a_p                                    # INA
    U8[51] += ain_a_n                                    # ~{INA}
    U8[63] += ain_b_p                                    # INB
    U8[62] += ain_b_n                                    # ~{INB}

    # --- clock ---
    U8['CLK'] += adc_clk                                 # pin 24

    # --- mode pins (parallel mode), tied explicitly ---
    U8['SEL'] += gnd                                     # pin 1
    U8['OEB'] += gnd                                     # pin 6
    U8['MSBI/SEN'] += gnd                                # pin 41
    U8['OEA/SCLK'] += gnd                                # pin 42
    U8['STPD/SDATA'] += adc_stpd                         # pin 45
    adc_stpd & Part('Device', 'R', ref='R15', value='10k',
                    footprint='Resistor_SMD:R_0603_1608Metric') & gnd

    # --- data outputs (index 0 = LSB) ---
    for i in range(12):
        U8['D{}_A'.format(i)] += da[i]                   # pins 27..38
        U8['D{}_B'.format(i)] += db[i]                   # pins 10..21
    U8['DVA'] += adc_dva                                 # pin 26

    # --- intentionally unused outputs ---
    U8['DVB'] += NC                                      # pin 22
    U8['OVRA'] += NC                                     # pin 39
    U8['OVRB'] += NC                                     # pin 9
