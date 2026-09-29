"""ADS5231 dual ADC — U12 dual 12-bit ADC with filtered supplies, reference bypass,
33-ohm output series termination and mode-strap pull-downs.
Block from: architecture/block_diagram.md (net plan: architecture/net_plan.md section 5)
Interface nets: AIN_A_P, AIN_A_N, AIN_B_P, AIN_B_N, ADC_VCM, ADC_CLK, ADC_DA0…ADC_DA11,
    ADC_DB0…ADC_DB11, ADC_OVRA, ADC_OVRB, ADC_DVA, ADC_SEL, ADC_SEN, ADC_SCLK, ADC_SDATA,
    VA_3V3, GND
"""
from skidl import *

# Part data, verbatim from sourcing/sourced_bom.md section "adc" (single source of truth here).
_U12 = dict(value='ADS5231IPAGT', footprint='Package_QFP:TQFP-64_10x10mm_P0.5mm',
            MPN='ADS5231IPAGT', LCSC='C2670079')
_R_ISET = dict(value='56.2k 1%', footprint='Resistor_SMD:R_0603_1608Metric',
               MPN='FRC0603F5622TS', LCSC='C2930117')
_R_REF = dict(value='2R 1%', footprint='Resistor_SMD:R_0402_1005Metric',
              MPN='FRC0402F2R00TS', LCSC='C2998051')
_R_PD = dict(value='10k 1%', footprint='Resistor_SMD:R_0402_1005Metric',
             MPN='0402WGF1002TCE', LCSC='C25744')
_RN_33R = dict(value='4x33R', footprint='Resistor_SMD:R_Array_Convex_4x0603',
               MPN='4D03WGJ0330T5E', LCSC='C25508')
_C_100N = dict(value='100nF', footprint='Capacitor_SMD:C_0402_1005Metric',
               MPN='CL05B104KB54PNC', LCSC='C307331')
_C_1U = dict(value='1uF', footprint='Capacitor_SMD:C_0402_1005Metric',
             MPN='CL05A105KA5NQNC', LCSC='C52923')
_C_2U2 = dict(value='2.2uF', footprint='Capacitor_SMD:C_0603_1608Metric',
              MPN='0603B225K160NT', LCSC='C43922')  # same BOM line as C17–C19 (design review)
_C_10U = dict(value='10uF', footprint='Capacitor_SMD:C_0603_1608Metric',
              MPN='CL10A106MA8NRNC', LCSC='C96446')
_FB_600R = dict(value='600R@100MHz', footprint='Inductor_SMD:L_0805_2012Metric',
                MPN='BLM21PG601SN1D', LCSC='C41556732')

# U12 data-pin names for bit i (SBAS295A p.11: bit 0 is tagged LSB, bit 11 MSB).
_BIT_SUFFIX = {0: '(LSB)', 11: '(MSB)'}


def _data_pin(ch, i):
    return f'D{i}_{ch}{_BIT_SUFFIX.get(i, "")}'


def _make(template, ref, spec):
    """Instantiate `template` as `ref`; MPN/LCSC go into netlist fields for the BOM."""
    part = template(ref=ref, value=spec['value'], footprint=spec['footprint'])
    part.fields.update(MPN=spec['MPN'], LCSC=spec['LCSC'])
    return part


@SubCircuit
def adc(ain_a_p, ain_a_n, ain_b_p, ain_b_n, adc_vcm, adc_clk, adc_da, adc_db,
        adc_ovra, adc_ovrb, adc_dva, adc_sel, adc_sen, adc_sclk, adc_sdata, va_3v3, gnd):
    """ADS5231 dual 12-bit ADC (U12), 20 MSPS, internal reference, parallel CMOS outputs.

    Inputs:  ain_a_p/n, ain_b_p/n (differential analog, from analog_front_end),
             adc_clk (20 MHz CMOS sample clock, from sample_clock),
             adc_sel/sen/sclk/sdata (mode/serial-interface pins, driven by the FPGA;
             10k pull-downs give the power-up default when the FPGA is unconfigured),
             va_3v3 (clean analog 3.3 V; feeds AVDD via FB6 and VDRV via FB5 so the
             two supplies track within the 0.3 V abs-max), gnd.
    Outputs: adc_vcm (1.5 V CM from U12.CM, sourced here, sensed by the FDA VOCM pins),
             adc_da[0..11] / adc_db[0..11] (12-bit buses, 33-ohm series terminated),
             adc_ovra, adc_ovrb, adc_dva (33-ohm series terminated).
    Assumptions: pull-down straps = SEL 0 (parallel control), MSBI 0 (straight offset
             binary), OEA 0 (ch A on), STPD 0 (running); OEB tied low (ch B on);
             INT/EXT high (internal reference). DVB unused (DVA is the FPGA data strobe).
    """
    # ---- U12 ADS5231 (net_plan section 5) --------------------------------------------
    u12 = _make(Part('dual_adc_usb', 'ADS5231IPAGT', dest=TEMPLATE), 'U12', _U12)

    # The generated symbol types CLK as output and DVA/DVB as power_in. SBAS295A p.11-12
    # gives CLK = I, DVA/DVB = O. Corrected on this instance only.
    # TODO: fix these pin types in symbols/dual_adc_usb.kicad_sym, then drop these lines.
    u12['CLK'].func = Pin.types.INPUT
    for pin in u12['DVA DVB']:
        pin.func = Pin.types.OUTPUT

    # ---- Supplies: VA_3V3 -> FB6 -> ADC_AVDD, VA_3V3 -> FB5 -> ADC_VDRV ----------------
    # Both nets are fed through a ferrite bead (passive), so they carry drive here.
    adc_avdd = Net('ADC_AVDD')
    adc_avdd.drive = POWER
    adc_vdrv = Net('ADC_VDRV')
    adc_vdrv.drive = POWER

    fb_t = Part('Device', 'FerriteBead', dest=TEMPLATE)
    fb5 = _make(fb_t, 'FB5', _FB_600R)
    fb6 = _make(fb_t, 'FB6', _FB_600R)
    va_3v3 & fb6 & adc_avdd
    va_3v3 & fb5 & adc_vdrv

    adc_avdd += u12['AVDD']        # pins 3, 46, 57
    adc_vdrv += u12['VDRV']        # pins 5, 8, 40, 43
    gnd += u12['AGND'], u12['GND']

    # C_DECOUP_U12: one 100 nF per supply pin plus one 10 uF bulk per rail.
    # AVDD: C54->pin 3, C55->pin 46, C56->pin 57, C57 bulk.
    # VDRV: C58->pin 5, C59->pin 8, C60->pin 40, C61->pin 43, C62 bulk.
    c_t = Part('Device', 'C', dest=TEMPLATE)
    for ref in ('C54', 'C55', 'C56'):
        adc_avdd & _make(c_t, ref, _C_100N) & gnd
    adc_avdd & _make(c_t, 'C57', _C_10U) & gnd
    for ref in ('C58', 'C59', 'C60', 'C61'):
        adc_vdrv & _make(c_t, ref, _C_100N) & gnd
    adc_vdrv & _make(c_t, 'C62', _C_10U) & gnd

    # ---- Reference, bias and common mode ----------------------------------------------
    # Internal reference: INT/EXT high (SBAS295A p.12, Fig. 21).
    adc_avdd += u12['INT/EXT#']
    # REFT/REFB: 2-ohm in series with 0.1 uF to GND each (SBAS295A pin table).
    r_t = Part('Device', 'R', dest=TEMPLATE)
    adc_reft, adc_reft_c = Net('ADC_REFT'), Net('ADC_REFT_C')
    adc_refb, adc_refb_c = Net('ADC_REFB'), Net('ADC_REFB_C')
    adc_reft += u12['REFT']
    adc_refb += u12['REFB']
    adc_reft & _make(r_t, 'R51', _R_REF) & adc_reft_c & _make(c_t, 'C50', _C_100N) & gnd
    adc_refb & _make(r_t, 'R52', _R_REF) & adc_refb_c & _make(c_t, 'C51', _C_100N) & gnd
    # SBAS295A Fig. 21: each 2-ohm node also carries 2.2 uF to GND, in parallel with the 0.1 uF.
    adc_reft_c & _make(c_t, 'C98', _C_2U2) & gnd
    adc_refb_c & _make(c_t, 'C99', _C_2U2) & gnd
    # ISET: 56.2 k to GND.
    adc_iset = Net('ADC_ISET')
    adc_iset += u12['ISET']
    adc_iset & _make(r_t, 'R50', _R_ISET) & gnd
    # CM output (1.5 V, +/-2 mA) -> ADC_VCM, bypassed with 0.1 uF + 1 uF.
    adc_vcm += u12['CM']
    adc_vcm & _make(c_t, 'C52', _C_100N) & gnd
    adc_vcm & _make(c_t, 'C53', _C_1U) & gnd

    # ---- Analog inputs and sample clock -----------------------------------------------
    ain_a_p += u12['INA+']
    ain_a_n += u12['INA-']
    ain_b_p += u12['INB+']
    ain_b_n += u12['INB-']
    adc_clk += u12['CLK']

    # ---- Digital outputs through 33-ohm isolated arrays -------------------------------
    # R_Pack04 element k (1..4) spans pin k (ADC side) to pin 9-k (FPGA side).
    # RN1-RN3: DA0-3/4-7/8-11; RN4-RN6: DB0-3/4-7/8-11; RN7: OVRA, OVRB, DVA, spare.
    rn_t = Part('Device', 'R_Pack04', dest=TEMPLATE)
    rn = {n: _make(rn_t, f'RN{n}', _RN_33R) for n in range(1, 8)}

    def terminate(u_pin, r_pack, k, local_net, out_net):
        local_net += u_pin, r_pack[k]
        out_net += r_pack[9 - k]

    da_r = Bus('ADC_DA_R', 12)
    db_r = Bus('ADC_DB_R', 12)
    for i in range(12):
        k = i % 4 + 1
        terminate(u12[_data_pin('A', i)], rn[1 + i // 4], k, da_r[i], adc_da[i])
        terminate(u12[_data_pin('B', i)], rn[4 + i // 4], k, db_r[i], adc_db[i])

    terminate(u12['OVRA'], rn[7], 1, Net('ADC_OVRA_R'), adc_ovra)
    terminate(u12['OVRB'], rn[7], 2, Net('ADC_OVRB_R'), adc_ovrb)
    terminate(u12['DVA'], rn[7], 3, Net('ADC_DVA_R'), adc_dva)
    rn[7][4, 5] += NC              # element 4 spare
    u12['DVB'] += NC               # channel B data-valid unused (same timing as DVA)

    # ---- Output enable and mode straps ------------------------------------------------
    u12['OEB#'] += gnd             # channel B outputs always enabled
    # 10k pull-downs: R53 SEL, R54 MSBI/SEN, R55 OEA#/SCLK, R56 STPD/SDATA.
    straps = ((adc_sel, 'SEL', 'R53'), (adc_sen, 'MSBI/SEN', 'R54'),
              (adc_sclk, 'OEA#/SCLK', 'R55'), (adc_sdata, 'STPD/SDATA', 'R56'))
    for net, pin_name, ref in straps:
        net += u12[pin_name]
        net & _make(r_t, ref, _R_PD) & gnd
