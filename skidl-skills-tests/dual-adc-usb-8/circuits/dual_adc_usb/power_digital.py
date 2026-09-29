"""Power Digital — 3.3 V and 1.2 V TLV62569 bucks, 1.8 V TLV75518P LDO, power LED
Block from: architecture/block_diagram.md (power_digital)
Interface nets: V5, V3V3D, V1V2, V1V8, GND
"""
from skidl import *


@SubCircuit
def power_digital(v5, v3v3d, v1v2, v1v8, gnd):
    """Digital supply rails from V5.

    U3 TLV62569 buck: V5 -> v3v3d, 0.6 V x (1 + 100k/22.1k) = 3.315 V (R3/R4), L1 2.2 uH.
    U4 TLV62569 buck: V5 -> v1v2,  0.6 V x (1 + 100k/100k)  = 1.200 V (R5/R6), L2 2.2 uH.
    U3/U4 EN tied to V5 (>= 4.40 V vs VIH <= 1.2 V).
    U5 TLV75518P fixed LDO: v3v3d -> v1v8 (IN and EN on v3v3d; FPGA bank 3 / PSRAM).
    D1 green power LED from v3v3d through R7 1k.
    v3v3d and v1v2 are driven only through inductors (passive) -> assembler must
    set .drive = POWER on them. v1v8 is driven by U5.OUT.
    FT232H is fed from V5 (driver decision); no FT232H load assumed on v3v3d.
    """
    # --- local nets (net_plan.md: SW33, FB33, SW12, FB12, PWR_LED) ---
    sw33, fb33 = Net('SW33'), Net('FB33')
    sw12, fb12 = Net('SW12'), Net('FB12')
    pwr_led = Net('PWR_LED')

    r_t = Part('Device', 'R', dest=TEMPLATE, footprint='Resistor_SMD:R_0603_1608Metric')
    buck_t = Part('Regulator_Switching', 'TLV62569DBV', dest=TEMPLATE,
                  value='TLV62569DBVR', footprint='Package_TO_SOT_SMD:SOT-23-5')
    l_t = Part('Device', 'L', dest=TEMPLATE, value='2.2uH',
               footprint='Inductor_SMD:L_Changjiang_FNR3015S')

    # --- U3: 3.3 V digital buck (pins: 1 EN, 2 GND, 3 SW, 4 VIN, 5 FB) ---
    U3 = buck_t(ref='U3')
    L1 = l_t(ref='L1')
    U3['VIN', 'EN'] += v5
    U3['GND'] += gnd
    U3['SW'] += sw33
    U3['FB'] += fb33
    sw33 & L1 & v3v3d
    R3 = r_t(ref='R3', value='100k')      # FB top
    R4 = r_t(ref='R4', value='22.1k')     # FB bottom
    v3v3d & R3 & fb33 & R4 & gnd
    C4 = Part('Device', 'C', ref='C4', value='10uF',
              footprint='Capacitor_SMD:C_0603_1608Metric')   # U3 input
    C5 = Part('Device', 'C', ref='C5', value='22uF',
              footprint='Capacitor_SMD:C_0805_2012Metric')   # U3 output
    v5 & C4 & gnd
    v3v3d & C5 & gnd

    # --- U4: 1.2 V FPGA core buck ---
    U4 = buck_t(ref='U4')
    L2 = l_t(ref='L2')
    U4['VIN', 'EN'] += v5
    U4['GND'] += gnd
    U4['SW'] += sw12
    U4['FB'] += fb12
    sw12 & L2 & v1v2
    R5 = r_t(ref='R5', value='100k')      # FB top
    R6 = r_t(ref='R6', value='100k')      # FB bottom
    v1v2 & R5 & fb12 & R6 & gnd
    C6 = Part('Device', 'C', ref='C6', value='10uF',
              footprint='Capacitor_SMD:C_0603_1608Metric')   # U4 input
    C7 = Part('Device', 'C', ref='C7', value='22uF',
              footprint='Capacitor_SMD:C_0805_2012Metric')   # U4 output
    v5 & C6 & gnd
    v1v2 & C7 & gnd

    # --- U5: 1.8 V LDO (pins: 1 IN, 2 GND, 3 EN, 4 NC, 5 OUT) ---
    U5 = Part('Regulator_Linear', 'TLV75518PDBV', ref='U5', value='TLV75518PDBVR',
              footprint='Package_TO_SOT_SMD:SOT-23-5')
    U5['IN', 'EN'] += v3v3d
    U5['GND'] += gnd
    U5['OUT'] += v1v8
    U5['NC'] += NC
    C8 = Part('Device', 'C', ref='C8', value='1uF',
              footprint='Capacitor_SMD:C_0402_1005Metric')   # U5 input
    C9 = Part('Device', 'C', ref='C9', value='1uF',
              footprint='Capacitor_SMD:C_0402_1005Metric')   # U5 output
    v3v3d & C8 & gnd
    v1v8 & C9 & gnd

    # --- Power LED: v3v3d -> R7 1k -> D1 anode, cathode -> gnd (~1.3 mA) ---
    R7 = r_t(ref='R7', value='1k')
    D1 = Part('Device', 'LED', ref='D1', value='green',
              footprint='LED_SMD:LED_0603_1608Metric')
    v3v3d & R7 & pwr_led
    D1['A'] += pwr_led
    D1['K'] += gnd
