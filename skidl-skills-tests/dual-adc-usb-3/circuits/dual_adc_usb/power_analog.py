"""Power Analog — +-4.2 V bipolar analog rails (LM27762) + 3.0 V AVDD (LP5907)
Block from: architecture/block_diagram.md
Interface nets: VBUS, GND, PWR_EN, +4V2A, -4V2A, +3V0A
"""
from skidl import *


@SubCircuit
def power_analog(vbus, gnd, pwr_en, vpos, vneg, avdd):
    """VBUS -> +-4.2 V analog rails -> +3.0 V ADC AVDD, all gated by PWR_EN.

    Args:
        vbus:    IN  (consumed) +5 V USB VBUS from usb_c_port. Filtered by FB2 before U5.
        gnd:     IN  (consumed) single board GND (architecture Decision: one GND net).
        pwr_en:  IN  (consumed) active-high enable from FX2LP PA0. Drives U5 EN+ and EN-.
                     100 k pulldown lives in usb_controller (R6), NOT here.
        vpos:    OUT (driven)   +4V2A, U5 OUT+ (pin 11), ~88 mA budget.
        vneg:    OUT (driven)   -4V2A, U5 OUT- (pin 6), ~28 mA budget.
        avdd:    OUT (driven)   +3V0A, U6 OUT through ferrite FB3, ~60 mA budget.

    Assumptions:
      - Feedback divider values are taken verbatim from handoffs/04_datasheets.md
        (LM27762DSSR_SUMMARY.md), NOT recomputed here:
          FB+ : R9 = 249k (OUT+ -> FB+), R10 = 100k (FB+ -> GND) -> +4.188 V
          FB- : R11 = 243k (OUT- -> FB-), R12 = 100k (FB- -> GND) -> -4.185 V
        Both bottom legs are >= 50 kohm as the datasheet requires. VFB- is an internal
        -1.22 V reference, so the FB- divider legitimately returns to GND (SNVSAF7C eq. 3).
      - U6 EN is tied to its own IN (+4V2A), i.e. always on once U5 is up. PWR_EN does not
        fan out to U6 in architecture/net_plan.md; U6 is already gated behind U5.
      - PGOOD (U5 pin 1) is tied to GND per SNVSAF7C Table 4-1 ("connect to ground if not
        used"). Architecture never uses the flag. This may raise an ERC pin-type note.
      - U5 thermal PAD (pin 13) is a real GND connection, not optional.
      - Decoupling for downstream loads (AD8066 / THS4551 / AD9235 AVDD) is NOT provided
        here - those blocks own their own local caps.
    """

    # ---- Passive templates (values/MPNs/footprints verbatim from sourcing/sourced_bom.md)
    C_100n = Part('Device', 'C', dest=TEMPLATE, value='100nF',
                  footprint='Capacitor_SMD:C_0402_1005Metric')          # CL05B104KB54PNC
    C_1u = Part('Device', 'C', dest=TEMPLATE, value='1uF',
                footprint='Capacitor_SMD:C_0603_1608Metric')            # CC0603KRX7R7BB105
    C_10u = Part('Device', 'C', dest=TEMPLATE, value='10uF',
                 footprint='Capacitor_SMD:C_0805_2012Metric')           # GRM21BZ71C106KE15L
    R_ = Part('Device', 'R', dest=TEMPLATE,
              footprint='Resistor_SMD:R_0402_1005Metric')               # 0402WGFxxxxTCE, 1%
    FB_ = Part('Device', 'FerriteBead', dest=TEMPLATE, value='600R@100MHz',
               footprint='Resistor_SMD:R_0603_1608Metric')              # BLM18AG601SN1D
    TP_ = Part('Connector', 'TestPoint', dest=TEMPLATE,
               footprint='TestPoint:TestPoint_Pad_1.0x1.0mm')

    # ---- Internal nets ------------------------------------------------------------
    # VIN_A: VBUS after FB2 - the analog-side supply island feeding U5 (design_risks R10).
    vin_a = Net('VIN_A')
    vin_a.drive = POWER          # sourced from VBUS through a passive bead
    # AVDD_RAW: U6 OUT at the package pin, before FB3. Keeps the LP5907's stability cap
    # (C31) directly on the pin instead of behind the bead.
    avdd_raw = Net('AVDD_RAW')
    # +3V0A reaches the outside world through FB3 (a passive), so the power_out drive of
    # U6 does not propagate. Assert it here so the block owns the rail it produces.
    avdd.drive = POWER

    # ---- U5  LM27762DSSR : inverting charge pump + dual LDO -----------------------
    # Pin map (KiCad Regulator_SwitchedCapacitor:LM27762, = SNVSAF7C Table 4-1):
    #   1 PGOOD  2 FB+  3 VIN  4 GND  5 CP  6 OUT-  7 FB-  8 EN-  9 C-  10 C+
    #   11 OUT+  12 EN+  13 PAD
    U5 = Part('Regulator_SwitchedCapacitor', 'LM27762', ref='U5', value='LM27762DSSR',
              footprint='Package_SON:WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65')

    # VBUS -> FB2 -> VIN_A -> U5 VIN, with 10uF bulk + 100nF HF (design_risks R10)
    FB2 = FB_(ref='FB2')
    vbus += FB2[1]
    vin_a += FB2[2], U5[3]
    C21 = C_10u(ref='C21')
    C22 = C_100n(ref='C22')
    vin_a += C21[1], C22[1]
    gnd += C21[2], C22[2]

    # Grounds: GND pin + thermal pad + unused PGOOD
    gnd += U5[4], U5[13], U5[1]

    # Enables: both LDO halves gated together by PWR_EN (no sequencing required)
    pwr_en += U5[12], U5[8]

    # Flying cap C1 across C+ / C- ; CP reservoir to GND
    C23 = C_1u(ref='C23')
    U5[10] += C23[1]
    U5[9] += C23[2]
    C24 = C_1u(ref='C24')
    U5[5] += C24[1]
    gnd += C24[2]

    # Positive rail: OUT+ -> +4V2A, output caps, FB+ divider 249k/100k -> +4.188 V
    vpos += U5[11]
    C25 = C_10u(ref='C25')
    C26 = C_100n(ref='C26')
    vpos += C25[1], C26[1]
    gnd += C25[2], C26[2]
    R9 = R_(ref='R9', value='249k')
    R10 = R_(ref='R10', value='100k')
    vpos += R9[1]
    U5[2] += R9[2], R10[1]
    gnd += R10[2]

    # Negative rail: OUT- -> -4V2A, output caps, FB- divider 243k/100k -> -4.185 V
    vneg += U5[6]
    C27 = C_10u(ref='C27')
    C28 = C_100n(ref='C28')
    vneg += C27[1], C28[1]
    gnd += C27[2], C28[2]
    R11 = R_(ref='R11', value='243k')
    R12 = R_(ref='R12', value='100k')
    vneg += R11[1]
    U5[7] += R11[2], R12[1]
    gnd += R12[2]

    # ---- U6  LP5907MFX-3.0 : +4V2A -> +3V0A analog AVDD ---------------------------
    # Pin map: 1 IN  2 GND  3 EN  4 NC  5 OUT.  EN tied to IN = always on behind U5.
    U6 = Part('Regulator_Linear', 'LP5907MFX-3.0', ref='U6', value='LP5907MFX-3.0',
              footprint='Package_TO_SOT_SMD:SOT-23-5')
    vpos += U6[1], U6[3]
    gnd += U6[2]
    U6[4] += NC                      # pin 4 is a true no-connect on the -5 pin variant
    avdd_raw += U6[5]

    # 1uF on IN and 1uF on OUT are mandatory for LP5907 stability (not optional).
    C29 = C_1u(ref='C29')
    C30 = C_100n(ref='C30')
    vpos += C29[1], C30[1]
    gnd += C29[2], C30[2]
    C31 = C_1u(ref='C31')
    avdd_raw += C31[1]
    gnd += C31[2]

    # FB3 on +3V0A (design_risks R10) - keeps switcher residue off the ADC AVDD rail.
    FB3 = FB_(ref='FB3')
    avdd_raw += FB3[1]
    avdd += FB3[2]
    C32 = C_10u(ref='C32')
    C33 = C_100n(ref='C33')
    avdd += C32[1], C33[1]
    gnd += C32[2], C33[2]

    # ---- Test points --------------------------------------------------------------
    # TP6/TP7/TP8 per architecture/net_plan.md. TP9 is unassigned upstream; put it on the
    # filtered analog VIN island so the LM27762 input can be probed at bring-up.
    vpos += TP_(ref='TP6', value='+4V2A')[1]
    vneg += TP_(ref='TP7', value='-4V2A')[1]
    avdd += TP_(ref='TP8', value='+3V0A')[1]
    vin_a += TP_(ref='TP9', value='VIN_A')[1]
