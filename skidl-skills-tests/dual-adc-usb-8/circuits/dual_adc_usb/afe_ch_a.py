"""AFE Channel A — Channel A front end (BNC -> ADC): 10:1 comp. divider, clamp, OPA356 buffer, THS4551 2-pole MFB driver
Block from: architecture/block_diagram.md (afe_ch_a); nets per architecture/net_plan.md
Interface nets: AIN_A_P, AIN_A_N, VCM, V3V3A, VP_AFE, VN_AFE, GND
"""
from skidl import *


@SubCircuit
def afe_ch_a(ain_p, ain_n, vcm, v3v3a, vp_afe, vn_afe, gnd):
    """Channel A analog front end, J2 BNC to ADS5231 INA/~INA.

    Signal chain:
      J2 centre -> A_BNC -> R101 909k || C101 22p -> A_DIV
      A_DIV: R102 100k, C102 150p, C103 15p, C104 JZ300 trimmer -> GND;
             D101 BAV199 clamp COM (A -> VN_AFE, K -> VP_AFE)
      A_DIV -> R103 1k -> A_BUF_IN (C105 8.2p -> GND) -> U101 OPA356 unity follower
      U101 out -> R104 1k -> A_XP; GND -> R105 1k -> A_XN (MFB, C108 27p XP-XN)
      A_XP -> R108 499 -> A_FIP (U102 IN+); A_XN -> R109 499 -> A_FIN (U102 IN-)
      R106 909 A_XP<->A_FON, R107 909 A_XN<->A_FOP; C109 12p A_FIP<->A_FON, C110 12p A_FIN<->A_FOP
      A_FOP -> R110 49.9 -> ain_p; A_FON -> R111 49.9 -> ain_n; C113 56p across ain_p/ain_n
    Outputs: ain_p/ain_n (driven by U102 through R110/R111). Senses vcm (U102 VOCM).
    Consumes v3v3a (U102), vp_afe/vn_afe (U101 + clamp), gnd.
    Decoupling local: C106/C107 (U101 rails), C111/C112 (U102 VS+), C114 (VCM at U102).
    Pins referenced by number: OPA356 symbol names are '~'/'+'/'-'; THS4551 pin 12 is
    named ~{PD} but is active-HIGH enable -> tied to v3v3a.
    """
    # --- local nets (net_plan.md, afe_ch_a) ---
    bnc, div = Net('A_BNC'), Net('A_DIV')
    buf_in, buf_out = Net('A_BUF_IN'), Net('A_BUF_OUT')
    xp, xn = Net('A_XP'), Net('A_XN')
    fip, fin = Net('A_FIP'), Net('A_FIN')
    fop, fon = Net('A_FOP'), Net('A_FON')

    r0603 = Part('Device', 'R', dest=TEMPLATE, footprint='Resistor_SMD:R_0603_1608Metric')
    r0402 = Part('Device', 'R', dest=TEMPLATE, footprint='Resistor_SMD:R_0402_1005Metric')
    c0603 = Part('Device', 'C', dest=TEMPLATE, footprint='Capacitor_SMD:C_0603_1608Metric')
    c0402 = Part('Device', 'C', dest=TEMPLATE, footprint='Capacitor_SMD:C_0402_1005Metric')

    # --- J2 BNC input (1 centre, 2 ground lead + shell pegs) ---
    J2 = Part('Connector', 'Conn_Coaxial', ref='J2', value='KH-BNC50-3511',
              footprint='ProjectLocal:BNC_Kinghelm_KH-BNC50-3511_Horizontal')
    J2[1] += bnc
    J2[2] += gnd

    # --- compensated 10:1 divider (1 Mohm // ~ 20 pF input) ---
    R101 = Part('Device', 'R', ref='R101', value='909k',
                footprint='Resistor_SMD:R_1206_3216Metric')      # R_T
    C101 = c0603(ref='C101', value='22pF')                      # C_T, 250 V C0G
    R102 = r0603(ref='R102', value='100k')                      # R_B
    C102 = c0603(ref='C102', value='150pF')                     # C_B1
    C103 = c0603(ref='C103', value='15pF')                      # C_B2
    # JZ300 hand trimmer 5.5-30 pF: pin 1 = hot (stator) -> A_DIV, pin 2 = rotor -> GND
    C104 = Part('Device', 'C_Variable', ref='C104', value='24pF',
                footprint='Capacitor_SMD:C_Trimmer_Voltronics_JZ')
    bnc & R101 & div
    bnc & C101 & div
    div & R102 & gnd
    div & C102 & gnd
    div & C103 & gnd
    C104[1] += div
    C104[2] += gnd

    # --- D101 BAV199 clamp: 1 A -> VN_AFE, 2 K -> VP_AFE, 3 COM -> A_DIV ---
    D101 = Part('dual_adc_usb', 'BAV199', ref='D101', value='BAV199',
                footprint='Package_TO_SOT_SMD:SOT-23')
    D101[1] += vn_afe
    D101[2] += vp_afe
    D101[3] += div

    # --- U101 OPA356 unity buffer (1 Out, 2 V-, 3 +In, 4 -In, 5 V+) ---
    R103 = r0603(ref='R103', value='1k')                        # R_S
    C105 = c0603(ref='C105', value='8.2pF')                     # C_S
    div & R103 & buf_in & C105 & gnd
    U101 = Part('Amplifier_Operational', 'OPA356xxDBV', ref='U101', value='OPA356AIDBVR',
                footprint='Package_TO_SOT_SMD:SOT-23-5')
    U101[3] += buf_in
    U101[1] += buf_out
    U101[4] += buf_out
    U101[5] += vp_afe
    U101[2] += vn_afe
    C106 = c0402(ref='C106', value='100nF')                     # VP_AFE local
    C107 = c0402(ref='C107', value='100nF')                     # VN_AFE local
    vp_afe & C106 & gnd
    vn_afe & C107 & gnd

    # --- MFB network around U102 ---
    R104 = r0603(ref='R104', value='1k')                        # R1a, 0.1 %
    R105 = r0603(ref='R105', value='1k')                        # R1b, 0.1 %
    R106 = r0603(ref='R106', value='909')                       # R2a
    R107 = r0603(ref='R107', value='909')                       # R2b
    R108 = r0603(ref='R108', value='499')                       # R3a
    R109 = r0603(ref='R109', value='499')                       # R3b
    C108 = c0603(ref='C108', value='27pF')                      # C1 differential
    C109 = c0603(ref='C109', value='12pF')                      # C2a
    C110 = c0603(ref='C110', value='12pF')                      # C2b
    buf_out & R104 & xp
    gnd & R105 & xn
    xp & C108 & xn
    xp & R108 & fip
    xn & R109 & fin
    xp & R106 & fon
    xn & R107 & fop
    fip & C109 & fon
    fin & C110 & fop

    # --- U102 THS4551 FDA ---
    U102 = Part('Amplifier_Difference', 'THS4551xRGT', ref='U102', value='THS4551IRGTR',
                footprint='Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm')
    # FB+/FB- are feedback sense pins joined to OUT+/OUT-; mark them as inputs so the
    # deliberate FB-OUT tie is not flagged as an output-output conflict.
    U102[1].func = Pin.types.INPUT
    U102[4].func = Pin.types.INPUT
    U102[2] += fip              # IN+
    U102[3] += fin              # IN-
    U102[10] += fop             # OUT+
    U102[4] += fop              # FB+
    U102[11] += fon             # OUT-
    U102[1] += fon              # FB-
    U102[9] += vcm              # VOCM
    U102[12] += v3v3a           # PD (active-high enable)
    for p in (5, 6, 7, 8):
        U102[p] += v3v3a        # VS+
    for p in (13, 14, 15, 16, 17):
        U102[p] += gnd          # VS- and EP
    C111 = c0402(ref='C111', value='100nF')                     # VS+ local
    C112 = c0402(ref='C112', value='1uF')                       # VS+ bulk
    C114 = c0402(ref='C114', value='100nF')                     # VCM at VOCM
    v3v3a & C111 & gnd
    v3v3a & C112 & gnd
    vcm & C114 & gnd

    # --- output RC to ADC ---
    R110 = r0402(ref='R110', value='49.9')
    R111 = r0402(ref='R111', value='49.9')
    C113 = c0402(ref='C113', value='56pF')
    fop & R110 & ain_p
    fon & R111 & ain_n
    ain_p & C113 & ain_n
