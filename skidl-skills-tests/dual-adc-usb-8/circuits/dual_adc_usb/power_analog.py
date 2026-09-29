"""Power Analog — TPS7A2033 3.3 V analog LDO, LM27762 asymmetric +/- AFE buffer rails
Block from: architecture/block_diagram.md (power_analog)
Interface nets: V5, V3V3A, VP_AFE, VN_AFE, GND
"""
from skidl import *


@SubCircuit
def power_analog(v5, v3v3a, vp_afe, vn_afe, gnd):
    """Analog supply rails from V5.

    U6 TPS7A2033 fixed 3.3 V LDO: v5 -> v3v3a (ADC, FDAs, XO). EN tied to v5
    (internal 500k pull-down otherwise disables it). C10 1u in, C11 1u + C12 10u out.
    U7 LM27762 +/- LDO with charge-pump inverter, VIN/EN+/EN- on v5:
      vp_afe = 1.2 V x (174k + 100k)/100k   = +3.288 V (R8 top, R9 bottom)
      vn_afe = -1.22 V x (64.9k + 100k)/100k = -2.012 V (R10 top, R11 bottom)
    PGOOD unused -> GND (datasheet direction); thermal pad -> GND.
    U7 pins by number (symbol names contain '+'/'-'): 1 PGOOD, 2 FB+, 3 VIN, 4 GND,
    5 CP, 6 OUT-, 7 FB-, 8 EN-, 9 C1-, 10 C1+, 11 OUT+, 12 EN+, 13 PAD.
    Drives v3v3a (U6.OUT), vp_afe (U7.OUT+), vn_afe (U7.OUT-); consumes v5.
    """
    # --- local nets (net_plan.md: LM_C1P, LM_C1N, LM_CP, LM_FBP, LM_FBN) ---
    lm_c1p, lm_c1n, lm_cp = Net('LM_C1P'), Net('LM_C1N'), Net('LM_CP')
    lm_fbp, lm_fbn = Net('LM_FBP'), Net('LM_FBN')

    r_t = Part('Device', 'R', dest=TEMPLATE, footprint='Resistor_SMD:R_0603_1608Metric')

    # --- U6: 3.3 V analog LDO (1 IN, 2 GND, 3 EN, 4 N/C, 5 OUT) ---
    U6 = Part('dual_adc_usb', 'TPS7A2033PDBVR', ref='U6', value='TPS7A2033PDBVR',
              footprint='Package_TO_SOT_SMD:SOT-23-5')
    U6[1] += v5
    U6[3] += v5
    U6[2] += gnd
    U6[5] += v3v3a
    U6[4] += NC
    C10 = Part('Device', 'C', ref='C10', value='1uF',
               footprint='Capacitor_SMD:C_0402_1005Metric')   # U6 input
    C11 = Part('Device', 'C', ref='C11', value='1uF',
               footprint='Capacitor_SMD:C_0402_1005Metric')   # U6 output
    C12 = Part('Device', 'C', ref='C12', value='10uF',
               footprint='Capacitor_SMD:C_0603_1608Metric')   # U6 output bulk
    v5 & C10 & gnd
    v3v3a & C11 & gnd
    v3v3a & C12 & gnd

    # --- U7: LM27762 bipolar AFE rails ---
    U7 = Part('Regulator_SwitchedCapacitor', 'LM27762', ref='U7', value='LM27762DSSR',
              footprint='Package_SON:WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65')
    U7[3] += v5                 # VIN
    U7[12] += v5                # EN+
    U7[8] += v5                 # EN-
    U7[4] += gnd                # GND
    U7[13] += gnd               # thermal pad
    U7[1] += gnd                # PGOOD unused -> GND per datasheet
    U7[10] += lm_c1p            # C1+
    U7[9] += lm_c1n             # C1-
    U7[5] += lm_cp              # CP
    U7[11] += vp_afe            # OUT+
    U7[6] += vn_afe             # OUT-
    U7[2] += lm_fbp             # FB+
    U7[7] += lm_fbn             # FB-

    C13 = Part('Device', 'C', ref='C13', value='2.2uF',
               footprint='Capacitor_SMD:C_0603_1608Metric')   # CIN
    C14 = Part('Device', 'C', ref='C14', value='1uF',
               footprint='Capacitor_SMD:C_0402_1005Metric')   # flying cap C1
    C15 = Part('Device', 'C', ref='C15', value='4.7uF',
               footprint='Capacitor_SMD:C_0603_1608Metric')   # CP
    C16 = Part('Device', 'C', ref='C16', value='2.2uF',
               footprint='Capacitor_SMD:C_0603_1608Metric')   # COUT+
    C17 = Part('Device', 'C', ref='C17', value='2.2uF',
               footprint='Capacitor_SMD:C_0603_1608Metric')   # COUT-
    v5 & C13 & gnd
    lm_c1p & C14 & lm_c1n
    lm_cp & C15 & gnd
    vp_afe & C16 & gnd
    vn_afe & C17 & gnd

    # --- feedback dividers (bottom resistors 100k >= 50k datasheet minimum) ---
    R8 = r_t(ref='R8', value='174k')      # FB+ top
    R9 = r_t(ref='R9', value='100k')      # FB+ bottom
    R10 = r_t(ref='R10', value='64.9k')   # FB- top
    R11 = r_t(ref='R11', value='100k')    # FB- bottom
    vp_afe & R8 & lm_fbp & R9 & gnd
    vn_afe & R10 & lm_fbn & R11 & gnd
