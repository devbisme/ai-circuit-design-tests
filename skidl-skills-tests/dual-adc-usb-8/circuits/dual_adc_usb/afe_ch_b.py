"""AFE Channel B — Channel B front end (BNC -> ADC): 10:1 comp. divider, clamp, OPA356 buffer, THS4551 2-pole MFB driver
Block from: architecture/block_diagram.md (afe_ch_b); nets per architecture/net_plan.md
Interface nets: AIN_B_P, AIN_B_N, VCM, V3V3A, VP_AFE, VN_AFE, GND
"""
from skidl import *


@SubCircuit
def afe_ch_b(ain_p, ain_n, vcm, v3v3a, vp_afe, vn_afe, gnd):
    """Channel B analog front end, J3 BNC to ADS5231 INB/~INB.

    Signal chain:
      J3 centre -> B_BNC -> R201 909k || C201 22p -> B_DIV
      B_DIV: R202 100k, C202 150p, C203 15p, C204 JZ300 trimmer -> GND;
             D201 BAV199 clamp COM (A -> VN_AFE, K -> VP_AFE)
      B_DIV -> R203 1k -> B_BUF_IN (C205 8.2p -> GND) -> U201 OPA356 unity follower
      U201 out -> R204 1k -> B_XP; GND -> R205 1k -> B_XN (MFB, C208 27p XP-XN)
      B_XP -> R208 499 -> B_FIP (U202 IN+); B_XN -> R209 499 -> B_FIN (U202 IN-)
      R206 909 B_XP<->B_FON, R207 909 B_XN<->B_FOP; C209 12p B_FIP<->B_FON, C210 12p B_FIN<->B_FOP
      B_FOP -> R210 49.9 -> ain_p; B_FON -> R211 49.9 -> ain_n; C213 56p across ain_p/ain_n
    Outputs: ain_p/ain_n (driven by U202 through R210/R211). Senses vcm (U202 VOCM).
    Consumes v3v3a (U202), vp_afe/vn_afe (U201 + clamp), gnd.
    Decoupling local: C206/C207 (U201 rails), C211/C212 (U202 VS+), C214 (VCM at U202).
    Pins referenced by number: OPA356 symbol names are '~'/'+'/'-'; THS4551 pin 12 is
    named ~{PD} but is active-HIGH enable -> tied to v3v3a.
    """
    # --- local nets (net_plan.md, afe_ch_b) ---
    bnc, div = Net('B_BNC'), Net('B_DIV')
    buf_in, buf_out = Net('B_BUF_IN'), Net('B_BUF_OUT')
    xp, xn = Net('B_XP'), Net('B_XN')
    fip, fin = Net('B_FIP'), Net('B_FIN')
    fop, fon = Net('B_FOP'), Net('B_FON')

    r0603 = Part('Device', 'R', dest=TEMPLATE, footprint='Resistor_SMD:R_0603_1608Metric')
    r0402 = Part('Device', 'R', dest=TEMPLATE, footprint='Resistor_SMD:R_0402_1005Metric')
    c0603 = Part('Device', 'C', dest=TEMPLATE, footprint='Capacitor_SMD:C_0603_1608Metric')
    c0402 = Part('Device', 'C', dest=TEMPLATE, footprint='Capacitor_SMD:C_0402_1005Metric')

    # --- J3 BNC input (1 centre, 2 ground lead + shell pegs) ---
    J3 = Part('Connector', 'Conn_Coaxial', ref='J3', value='KH-BNC50-3511',
              footprint='ProjectLocal:BNC_Kinghelm_KH-BNC50-3511_Horizontal')
    J3[1] += bnc
    J3[2] += gnd

    # --- compensated 10:1 divider (1 Mohm // ~ 20 pF input) ---
    R201 = Part('Device', 'R', ref='R201', value='909k',
                footprint='Resistor_SMD:R_1206_3216Metric')      # R_T
    C201 = c0603(ref='C201', value='22pF')                      # C_T, 250 V C0G
    R202 = r0603(ref='R202', value='100k')                      # R_B
    C202 = c0603(ref='C202', value='150pF')                     # C_B1
    C203 = c0603(ref='C203', value='15pF')                      # C_B2
    # JZ300 hand trimmer 5.5-30 pF: pin 1 = hot (stator) -> B_DIV, pin 2 = rotor -> GND
    C204 = Part('Device', 'C_Variable', ref='C204', value='24pF',
                footprint='Capacitor_SMD:C_Trimmer_Voltronics_JZ')
    bnc & R201 & div
    bnc & C201 & div
    div & R202 & gnd
    div & C202 & gnd
    div & C203 & gnd
    C204[1] += div
    C204[2] += gnd

    # --- D201 BAV199 clamp: 1 A -> VN_AFE, 2 K -> VP_AFE, 3 COM -> B_DIV ---
    D201 = Part('dual_adc_usb', 'BAV199', ref='D201', value='BAV199',
                footprint='Package_TO_SOT_SMD:SOT-23')
    D201[1] += vn_afe
    D201[2] += vp_afe
    D201[3] += div

    # --- U201 OPA356 unity buffer (1 Out, 2 V-, 3 +In, 4 -In, 5 V+) ---
    R203 = r0603(ref='R203', value='1k')                        # R_S
    C205 = c0603(ref='C205', value='8.2pF')                     # C_S
    div & R203 & buf_in & C205 & gnd
    U201 = Part('Amplifier_Operational', 'OPA356xxDBV', ref='U201', value='OPA356AIDBVR',
                footprint='Package_TO_SOT_SMD:SOT-23-5')
    U201[3] += buf_in
    U201[1] += buf_out
    U201[4] += buf_out
    U201[5] += vp_afe
    U201[2] += vn_afe
    C206 = c0402(ref='C206', value='100nF')                     # VP_AFE local
    C207 = c0402(ref='C207', value='100nF')                     # VN_AFE local
    vp_afe & C206 & gnd
    vn_afe & C207 & gnd

    # --- MFB network around U202 ---
    R204 = r0603(ref='R204', value='1k')                        # R1a, 0.1 %
    R205 = r0603(ref='R205', value='1k')                        # R1b, 0.1 %
    R206 = r0603(ref='R206', value='909')                       # R2a
    R207 = r0603(ref='R207', value='909')                       # R2b
    R208 = r0603(ref='R208', value='499')                       # R3a
    R209 = r0603(ref='R209', value='499')                       # R3b
    C208 = c0603(ref='C208', value='27pF')                      # C1 differential
    C209 = c0603(ref='C209', value='12pF')                      # C2a
    C210 = c0603(ref='C210', value='12pF')                      # C2b
    buf_out & R204 & xp
    gnd & R205 & xn
    xp & C208 & xn
    xp & R208 & fip
    xn & R209 & fin
    xp & R206 & fon
    xn & R207 & fop
    fip & C209 & fon
    fin & C210 & fop

    # --- U202 THS4551 FDA ---
    U202 = Part('Amplifier_Difference', 'THS4551xRGT', ref='U202', value='THS4551IRGTR',
                footprint='Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm')
    # FB+/FB- are feedback sense pins joined to OUT+/OUT-; mark them as inputs so the
    # deliberate FB-OUT tie is not flagged as an output-output conflict.
    U202[1].func = Pin.types.INPUT
    U202[4].func = Pin.types.INPUT
    U202[2] += fip              # IN+
    U202[3] += fin              # IN-
    U202[10] += fop             # OUT+
    U202[4] += fop              # FB+
    U202[11] += fon             # OUT-
    U202[1] += fon              # FB-
    U202[9] += vcm              # VOCM
    U202[12] += v3v3a           # PD (active-high enable)
    for p in (5, 6, 7, 8):
        U202[p] += v3v3a        # VS+
    for p in (13, 14, 15, 16, 17):
        U202[p] += gnd          # VS- and EP
    C211 = c0402(ref='C211', value='100nF')                     # VS+ local
    C212 = c0402(ref='C212', value='1uF')                       # VS+ bulk
    C214 = c0402(ref='C214', value='100nF')                     # VCM at VOCM
    v3v3a & C211 & gnd
    v3v3a & C212 & gnd
    vcm & C214 & gnd

    # --- output RC to ADC ---
    R210 = r0402(ref='R210', value='49.9')
    R211 = r0402(ref='R211', value='49.9')
    C213 = c0402(ref='C213', value='56pF')
    fop & R210 & ain_p
    fon & R211 & ain_n
    ain_p & C213 & ain_n
