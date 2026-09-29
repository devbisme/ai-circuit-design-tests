"""Dual 12-bit ADC — ADS5231IPAGT, 20 MSPS, parallel-control mode, internal reference
Block from: architecture/block_diagram.md
Interface nets: CH1_P, CH1_N, CH2_P, CH2_N, ADC_CLK, ADC_D1[11:0], ADC_D2[11:0],
                ADC_OE_N, ADC_PDWN, VOCM, +3V3_A, +3V3_ADCD, GND

Pin numbers (not names) are used throughout for U5: the generated symbol carries names
containing regex-significant characters ('INA+', 'OEA#/SCLK', 'D0_B(LSB)', 'INT/EXT#'),
which SKiDL's name lookup would treat as patterns. Every number is commented with the
datasheet pin name (datasheets/ADS5231IPAGT_SUMMARY.md, TI SBAS295A Pin Functions table).
"""
from skidl import *

# --- Footprint shorthands -------------------------------------------------------------
_FP_C0402 = 'Capacitor_SMD:C_0402_1005Metric'
_FP_C0603 = 'Capacitor_SMD:C_0603_1608Metric'
_FP_C0805 = 'Capacitor_SMD:C_0805_2012Metric'
_FP_R0603 = 'Resistor_SMD:R_0603_1608Metric'


@SubCircuit
def adc_dual(in1_p, in1_n, in2_p, in2_n, adc_clk, adc_d1, adc_d2,
             adc_oe_n, adc_pdwn, vocm, v3v3_a, v3v3_adcd, gnd):
    """Dual 12-bit 20 MSPS ADC with 33 ohm series-damped output buses.

    Inputs  : in1_p/in1_n -> channel A (INA+/INA-), in2_p/in2_n -> channel B (INB+/INB-),
              both differential, 2 Vpp FS, biased at the ADC's own CM output;
              adc_clk (20.000 MHz, straight from X1 via clock_20m's R_s1);
              adc_oe_n and adc_pdwn are driven by fpga_core (each pulled low here so the
              default state is outputs-enabled / not-powered-down even with the FPGA
              unconfigured and its IOs high-Z).
    Outputs : adc_d1[11:0] = channel A data (D0_A..D11_A), adc_d2[11:0] = channel B data,
              each line through a 33 ohm array element placed at the ADC end;
              vocm is DRIVEN here from U5.CM (pin 52) -- the ADC's own common-mode buffer
              is the only source of VOCM in this design (net_plan.md), afe_channel only
              senses it.
    Rails   : v3v3_a -> AVDD (analog), v3v3_adcd -> VDRV (output-buffer, ferrite-isolated).
    Straps  : SEL=0 (parallel-control mode), INT/EXT=1 (internal reference -- no external
              reference IC exists in the BOM), MSBI=0 (straight offset binary).
    """
    # ---------------------------------------------------------------------------------
    # U5 — ADS5231IPAGT, generated symbol (64 pins, TQFP-64)
    # ---------------------------------------------------------------------------------
    u5 = Part('dual_adc_usb', 'ADS5231IPAGT', ref='U5', value='ADS5231IPAGT',
              footprint='Package_QFP:TQFP-64_10x10mm_P0.5mm')

    # --- Supplies ---------------------------------------------------------------------
    for p in (3, 46, 57):                 # AVDD
        v3v3_a += u5[p]
    for p in (5, 8, 40, 43):              # VDRV (output-buffer supply)
        v3v3_adcd += u5[p]
    for p in (2, 47, 48, 49, 55, 58, 59, 61, 64):   # AGND
        gnd += u5[p]
    for p in (4, 7, 23, 25, 44):          # GND (output-buffer ground)
        gnd += u5[p]

    # --- Analog inputs ----------------------------------------------------------------
    in1_p += u5[50]     # INA+
    in1_n += u5[51]     # INA-
    in2_p += u5[63]     # INB+
    in2_n += u5[62]     # INB-

    # --- Sample clock -----------------------------------------------------------------
    adc_clk += u5[24]   # CLK, 20.000 MHz (ADC floor with PLL enabled; see handoff 04 #1)

    # ---------------------------------------------------------------------------------
    # Control strapping (parallel-control mode). Nothing floating.
    # ---------------------------------------------------------------------------------
    gnd += u5[1]        # SEL = 0 -> parallel-control mode (41/42/45 = MSBI/OEA/STPD)
    v3v3_a += u5[56]    # INT/EXT = 1 -> internal reference (tied to AVDD, TI Figure 21)
    gnd += u5[41]       # MSBI = 0 -> straight offset binary output format

    # OEA# (42) and OEB# (6) share ADC_OE_N; STPD (45) takes ADC_PDWN. Both are FPGA
    # outputs per net_plan.md, and both are pulled low so the asserted-by-default state
    # (outputs enabled, normal operation) holds while the FPGA is unconfigured.
    adc_oe_n += u5[42], u5[6]
    adc_pdwn += u5[45]

    r44 = Part('Device', 'R', ref='R44', value='10k', footprint=_FP_R0603)
    r45 = Part('Device', 'R', ref='R45', value='10k', footprint=_FP_R0603)
    adc_oe_n += r44[1]
    gnd += r44[2]
    adc_pdwn += r45[1]
    gnd += r45[2]

    # --- Unused status outputs --------------------------------------------------------
    # Overrange flags and Data-Valid strobes are not brought to the FPGA (fpga_core
    # captures on ADC_CLK). Marked NC deliberately, not left floating by omission.
    u5[39] += NC        # OVRA
    u5[9] += NC         # OVRB
    u5[26] += NC        # DVA
    u5[22] += NC        # DVB

    # ---------------------------------------------------------------------------------
    # Bias and reference network (TI SBAS295A Figure 21, internal-reference mode)
    # ---------------------------------------------------------------------------------
    # ISET: 56.2k to ground sets the ~20 uA internal bias current. Deviating from this
    # value degrades device performance -- it is not a pull-down, do not substitute.
    r41 = Part('Device', 'R', ref='R41', value='56.2k', footprint=_FP_R0603)
    u5[60] += r41[1]    # ISET
    gnd += r41[2]

    # REFT / REFB: 0.1 uF directly at the pin, plus 2 ohm in series with a 2.2 uF
    # reservoir (Figure 21). The 2 ohm damps the reservoir against the internal
    # reference buffer -- omitting it risks reference-loop peaking.
    reft = Net('ADC_REFT')
    refb = Net('ADC_REFB')
    reft_res = Net('ADC_REFT_RES')
    refb_res = Net('ADC_REFB_RES')
    reft += u5[53]      # REFT
    refb += u5[54]      # REFB

    c50 = Part('Device', 'C', ref='C50', value='100nF', footprint=_FP_C0402)
    c52 = Part('Device', 'C', ref='C52', value='100nF', footprint=_FP_C0402)
    reft += c50[1]
    gnd += c50[2]
    refb += c52[1]
    gnd += c52[2]

    r42 = Part('Device', 'R', ref='R42', value='2R', footprint=_FP_R0603)
    r43 = Part('Device', 'R', ref='R43', value='2R', footprint=_FP_R0603)
    reft += r42[1]
    reft_res += r42[2]
    refb += r43[1]
    refb_res += r43[2]

    c51 = Part('Device', 'C', ref='C51', value='2.2uF', footprint=_FP_C0805)
    c53 = Part('Device', 'C', ref='C53', value='2.2uF', footprint=_FP_C0805)
    reft_res += c51[1]
    gnd += c51[2]
    refb_res += c53[1]
    gnd += c53[2]

    # CM (pin 52) is the design's only VOCM source: 1 uF reservoir (TI Figure 20's VOCM
    # treatment) plus a 100 nF high-frequency bypass. The buffer sources +/-2 mA.
    vocm += u5[52]      # CM, typ +1.5 V
    c54 = Part('Device', 'C', ref='C54', value='1uF', footprint=_FP_C0603)
    c55 = Part('Device', 'C', ref='C55', value='100nF', footprint=_FP_C0402)
    vocm += c54[1], c55[1]
    gnd += c54[2], c55[2]

    # ---------------------------------------------------------------------------------
    # Supply decoupling — one 100 nF per supply pin, plus a bulk cap per rail
    # ---------------------------------------------------------------------------------
    avdd_bypass = [
        ('C41', '100nF', _FP_C0402),     # AVDD pin 3
        ('C42', '100nF', _FP_C0402),     # AVDD pin 46
        ('C43', '100nF', _FP_C0402),     # AVDD pin 57
        ('C44', '10uF', _FP_C0805),      # AVDD bulk
    ]
    vdrv_bypass = [
        ('C45', '100nF', _FP_C0402),     # VDRV pin 5
        ('C46', '100nF', _FP_C0402),     # VDRV pin 8
        ('C47', '100nF', _FP_C0402),     # VDRV pin 40
        ('C48', '100nF', _FP_C0402),     # VDRV pin 43
        ('C49', '10uF', _FP_C0805),      # VDRV bulk
    ]
    for rail, spec in ((v3v3_a, avdd_bypass), (v3v3_adcd, vdrv_bypass)):
        for ref, val, fp in spec:
            c = Part('Device', 'C', ref=ref, value=val, footprint=fp)
            rail += c[1]
            gnd += c[2]

    # ---------------------------------------------------------------------------------
    # Output data buses — 33 ohm series damping at the ADC end (6x 4-element arrays)
    # ---------------------------------------------------------------------------------
    # R_Pack04 element n spans pins n and (9 - n): R1 = 1/8, R2 = 2/7, R3 = 3/6, R4 = 4/5.
    arrays = {}
    for n in range(1, 7):
        arrays[n] = Part('Device', 'R_Pack04', ref=f'RA{n}', value='33',
                         footprint='Resistor_SMD:R_Array_Concave_4x0402')

    # Channel A -> ADC_D1: D0_A..D11_A are pins 27..38 (bit 0 = D0_A = LSB).
    # Channel B -> ADC_D2: D0_B..D11_B are pins 10..21.
    for bus, first_pin, packs, label in (
        (adc_d1, 27, (arrays[1], arrays[2], arrays[3]), 'ADC_D1'),
        (adc_d2, 10, (arrays[4], arrays[5], arrays[6]), 'ADC_D2'),
    ):
        for bit in range(12):
            pack = packs[bit // 4]
            elem = bit % 4 + 1                      # 1..4 within this array
            stub = Net(f'{label}_S{bit}')           # ADC pin -> array, one resistor long
            stub += u5[first_pin + bit], pack[elem]
            bus[bit] += pack[9 - elem]
