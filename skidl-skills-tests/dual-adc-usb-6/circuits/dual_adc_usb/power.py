"""Power — two synchronous bucks, two analog LDOs, and the two DC references
Block from: architecture/block_diagram.md
Interface nets: VBUS_SW, +3V3D, +1V2, +3V3A_ADC, +3V3A_AMP, VREF_OFF, VCM_REF, GND
"""
from skidl import *


@SubCircuit
def power(vbus_sw, v3v3d, v1v2, v3v3a_adc, v3v3a_amp, vref_off, vcm_ref, gnd):
    """Every rail on the board, plus the two analog reference voltages.

    Four supplies, all fed from VBUS_SW:

      U3  AP62200TWU-7 buck  -> +3V3D      3.296 V, 225 mA  (FPGA I/O, SDRAM, FX2, XO)
      U4  AP62200TWU-7 buck  -> +1V2       1.202 V,  80 mA  (FPGA VCCINT)
      U5  TPS73633     LDO   -> +3V3A_ADC  3.300 V,  55 mA  (both ADCs)
      U6  TPS73633     LDO   -> +3V3A_AMP  3.300 V,  43 mA  (front-end amps, U7)

    Plus U7 (TLV2372, dual RRIO) generating VREF_OFF = 1.807 V (buffered) and the
    unbuffered VCM_REF = 1.650 V divider.

    ------------------------------------------------------------------------------
    ANALOG RAILS ARE LDO'd OFF VBUS_SW, NEVER OFF A BUCK OUTPUT (requirement P6,
    architecture decision #9, risk R5). Both bucks switch at ~750 kHz-1 MHz, inside
    the 4.45 MHz analog passband, and one ADC LSB is only 488 uV. Each LDO therefore
    sits behind its own ferrite (FB1/FB2) with 10 uF in front of it, exactly as R5
    prescribes, because the TPS73633's PSRR at 1 MHz is far worse than its 58 dB at
    10 kHz. Do not "simplify" either analog rail onto +3V3D.
    ------------------------------------------------------------------------------

    RAIL SEQUENCING (architecture decision #12 -- +1V2 must lead +3V3D so VCCINT
    comes up before VCCO, per Xilinx's Spartan-6 recommendation):

      U4.EN is tied straight to VBUS_SW.  U3.EN is delayed by R18 (100 kOhm) /
      C22 (100 nF) from VBUS_SW.

    The AP62200T has an internal 1.5 uA pull-up current source from its own VCC onto
    EN. That source injects current into the R18/C22 node, so the real delay is
    SHORTER than architecture's nominal 2.74 ms. Worked out (see the block handoff
    for the ramped-source version):

      tau   = R18 * C22 = 100 kOhm * 100 nF = 10.0 ms
      Vinf  = 5.00 V + (1.5 uA * 100 kOhm) = 5.15 V    <- pull-up raises the asymptote
      t_on  = -tau * ln(1 - 1.20/5.15) = 2.653 ms      <- vs 2.744 ms with no pull-up

    i.e. 91 us / 3.3 % shorter. Meanwhile U4 cannot start until VBUS_SW clears the
    AP62200T's own 4.2 V minimum VIN, which the TPS22919's ~1.9 ms soft-start ramp
    reaches at ~1.56 ms. So +1V2 still leads +3V3D by ~2 ms even after the correction.
    The ordering holds with a wide margin -- R18 and C22 are UNCHANGED.

    R19 is now PLACED (rev.6): it is the 22 Ohm RNULL isolation resistor on U7 unit
    A's output. net_plan.md reserved R10-R19 and named only nine functions (R10-R18);
    R19 was the spare, and the phase-6 review's capacitive-load finding is what it is
    spent on. See section 6. R19 MUST appear in the BOM -- 22 Ohm, 0402.

    Args:
        vbus_sw:   [in]  VBUS_SW -- 5 V from usb_front's load switch. Consumed only;
                   the only driving pin on it lives in usb_front (U2.VOUT).
        v3v3d:     [out] +3V3D -- driven through L1, so no SKiDL-visible driver.
        v1v2:      [out] +1V2  -- driven through L2, same note.
        v3v3a_adc: [out] +3V3A_ADC -- driven through FB3, same note.
        v3v3a_amp: [out] +3V3A_AMP -- driven through FB4, same note.
        vref_off:  [out] VREF_OFF -- 1.807 V, driven by U7 unit A THROUGH R19 (22
                   Ohm RNULL), so there is no SKiDL-visible driving pin on this net
                   any more; the driver sits on the internal net VREF_OFF_AMP. Feeds
                   R101/R201 in the two analog_frontend instances, and every bypass
                   cap on it (C24 here, C113/C213 in the front ends) must stay on
                   THIS net -- they are the capacitive load R19 isolates.
        vcm_ref:   [out] VCM_REF -- 1.650 V, unbuffered R16/R17 divider off
                   +3V3A_AMP. No driving pin -- see the block handoff.
        gnd:       [in]  GND -- single plane.
    """
    # ---- Part templates (values/footprints verbatim from sourcing/sourced_bom.md) --
    _r0402 = Part('Device', 'R', dest=TEMPLATE,
                  footprint='Resistor_SMD:R_0402_1005Metric')
    _c0402 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0402_1005Metric')
    _c0603 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0603_1608Metric')
    _c0805 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0805_2012Metric')
    _fb0805 = Part('Device', 'FerriteBead', dest=TEMPLATE, value='600R@100MHz',
                   footprint='Inductor_SMD:L_0805_2012Metric')

    # ---- Internal nets ------------------------------------------------------------
    sw_3v3   = Net('SW_3V3D')      # U3.SW -> L1
    sw_1v2   = Net('SW_1V2')       # U4.SW -> L2
    fb_3v3   = Net('FB_3V3D')      # R10/R11/C34 tap -> U3.FB
    fb_1v2   = Net('FB_1V2')       # R12/R13 tap -> U4.FB
    en_3v3   = Net('EN_3V3D')      # R18/C22 RC delay node -> U3.EN
    ldo_adc_in  = Net('LDO_ADC_IN')    # FB1 -> U5.IN
    ldo_amp_in  = Net('LDO_AMP_IN')    # FB2 -> U6.IN
    ldo_adc_out = Net('LDO_ADC_OUT')   # U5.OUT -> FB3
    ldo_amp_out = Net('LDO_AMP_OUT')   # U6.OUT -> FB4
    vref_div = Net('VREF_OFF_DIV')  # R14/R15 tap -> U7 unit A non-inverting input
    vref_amp = Net('VREF_OFF_AMP')  # U7 unit A OUTPUT, inside the loop -> R19 -> VREF_OFF

    # =============================================================================
    # 1. U3 -- AP62200TWU-7 buck, VBUS_SW -> +3V3D  (3.296 V, 225 mA)
    #    TSOT26 pins BY NAME: GND(1) SW(2) VIN(3) FB(4) EN(5) BST(6).
    #    VFB = 0.763 V typ for the AP62200"T" sub-variant -- NOT the 0.800 V of the
    #    base AP62200/AP62201 in the same datasheet. R10/R11 below are computed for
    #    0.763 V and are taken verbatim from sourcing rev.4; do not recompute.
    #      VOUT = 0.763 * (1 + 33.2/10.0) = 3.296 V
    # =============================================================================
    U3 = Part('dual_adc_usb', 'AP62200TWU-7', ref='U3', value='AP62200TWU-7',
              footprint='Package_TO_SOT_SMD:TSOT-23-6')

    vbus_sw += U3['VIN']
    gnd     += U3['GND']
    sw_3v3  += U3['SW']
    fb_3v3  += U3['FB']
    en_3v3  += U3['EN']

    C10 = _c0402(ref='C10', value='100nF')   # U3 VIN local HF bypass
    vbus_sw += C10[1]
    gnd     += C10[2]

    # Dedicated VIN bulk. The AP62200T datasheet asks for >=10 uF at VIN per
    # regulator. usb_front's 2 x 22 uF on VBUS_SW is shared, remote bulk -- it is not
    # the same thing, and a "place C2/C3 near the VIN pins" layout note is a weaker
    # guarantee than a part. C35/C36 allocated in sourced_bom.md rev.5.
    C35 = _c0805(ref='C35', value='10uF')    # U3 VIN bulk
    vbus_sw += C35[1]
    gnd     += C35[2]

    # Bootstrap: 330 nF because VOUT > 3 V (datasheet section 13). BST -> SW.
    C32 = _c0402(ref='C32', value='330nF')
    U3['BST'] += C32[1]
    sw_3v3    += C32[2]

    L1 = Part('Device', 'L', ref='L1', value='3.3uH',
              footprint='Inductor_SMD:L_Changjiang_FNR4030S')
    sw_3v3 += L1[1]
    v3v3d  += L1[2]

    C18, C19 = _c0805(2, ref=['C18', 'C19'], value='22uF')   # 2 x 22 uF per Table 1
    for c in (C18, C19):
        v3v3d += c[1]
        gnd   += c[2]

    # Feedback divider + feedforward cap. C34 (22 pF) sits ACROSS R10 and is fitted
    # on this instance only -- Table 1 marks it "Open"/DNP for the 1.2 V rail.
    R10 = _r0402(ref='R10', value='33.2k')   # +3V3D fb TOP  (VOUT -> FB)
    R11 = _r0402(ref='R11', value='10.0k')   # +3V3D fb BOT  (FB -> GND)
    C34 = _c0402(ref='C34', value='22pF')    # feedforward, parallel with R10

    v3v3d  += R10[1], C34[1]
    fb_3v3 += R10[2], C34[2], R11[1]
    gnd    += R11[2]

    # =============================================================================
    # 2. U4 -- AP62200TWU-7 buck, VBUS_SW -> +1V2  (1.202 V, 80 mA)
    #      VOUT = 0.763 * (1 + 5.76/10.0) = 1.202 V
    #    EN tied STRAIGHT to VBUS_SW: this rail leads, no delay (decision #12).
    # =============================================================================
    U4 = Part('dual_adc_usb', 'AP62200TWU-7', ref='U4', value='AP62200TWU-7',
              footprint='Package_TO_SOT_SMD:TSOT-23-6')

    vbus_sw += U4['VIN'], U4['EN']
    gnd     += U4['GND']
    sw_1v2  += U4['SW']
    fb_1v2  += U4['FB']

    C13 = _c0402(ref='C13', value='100nF')   # U4 VIN local HF bypass
    vbus_sw += C13[1]
    gnd     += C13[2]

    C36 = _c0805(ref='C36', value='10uF')    # U4 VIN bulk -- see C35 note
    vbus_sw += C36[1]
    gnd     += C36[2]

    C33 = _c0402(ref='C33', value='100nF')   # bootstrap, 100 nF is fine for VOUT < 3 V
    U4['BST'] += C33[1]
    sw_1v2    += C33[2]

    L2 = Part('Device', 'L', ref='L2', value='2.2uH',
              footprint='Inductor_SMD:L_Changjiang_FNR4020S')
    sw_1v2 += L2[1]
    v1v2   += L2[2]

    C20, C21 = _c0805(2, ref=['C20', 'C21'], value='22uF')
    for c in (C20, C21):
        v1v2 += c[1]
        gnd  += c[2]

    R12 = _r0402(ref='R12', value='5.76k')   # +1V2 fb TOP  (VOUT -> FB)
    R13 = _r0402(ref='R13', value='10.0k')   # +1V2 fb BOT  (FB -> GND)

    v1v2   += R12[1]
    fb_1v2 += R12[2], R13[1]
    gnd    += R13[2]

    # =============================================================================
    # 3. Rail sequencing RC -- R18 / C22 delaying U3.EN only.
    #    See the docstring for the arithmetic including the AP62200T's internal
    #    1.5 uA EN pull-up. Result: 2.653 ms (step) vs architecture's 2.744 ms
    #    nominal, and +1V2 still leads +3V3D by ~2 ms. Values UNCHANGED.
    #    C22 also guarantees EN is never floating, which matters because a floating
    #    EN on this part AUTO-ENABLES via that same pull-up -- it is not a safe
    #    "leave it open to keep it off" pin.
    # =============================================================================
    R18 = _r0402(ref='R18', value='100k')
    C22 = _c0402(ref='C22', value='100nF')

    vbus_sw += R18[1]
    en_3v3  += R18[2], C22[1]
    gnd     += C22[2]

    # R19 is no longer spare: it is U7A's capacitive-load isolation resistor (RNULL),
    # placed in section 6 below. See that section for the arithmetic.

    # =============================================================================
    # 4. U5 -- TPS73633 LDO, VBUS_SW -> +3V3A_ADC (55 mA, both ADCs)
    #    SOT-23-5 pins BY NAME: IN(1) GND(2) EN(3) NR(4) OUT(5).
    #    EN tied to IN = always on (datasheet: "EN can be connected to IN if not
    #    used"). The analog rails have no sequencing requirement; only the FPGA's
    #    core-before-I/O ordering does.
    #    C28 on NR is 100 nF, which is the datasheet's OWN headline condition for
    #    the 30 uVrms figure architecture decision #9 / risk R5 relies on ("output
    #    noise 30 uVRMS with 0.1 uF CNR"). An internal 27 kOhm feeds NR, so 100 nF
    #    costs ~14 ms of extra start-up -- irrelevant next to USB enumeration.
    # =============================================================================
    FB1, FB2, FB3, FB4 = _fb0805(4, ref=['FB1', 'FB2', 'FB3', 'FB4'])

    # FB1 + C11 (10 uF) in front of U5 -- this pair IS risk R5's prescription.
    vbus_sw    += FB1[1]
    ldo_adc_in += FB1[2]

    C11 = _c0805(ref='C11', value='10uF')    # LDO input bulk, post-ferrite
    ldo_adc_in += C11[1]
    gnd        += C11[2]

    U5 = Part('Regulator_Linear', 'TPS73633DBV', ref='U5', value='TPS73633DBVR',
              footprint='Package_TO_SOT_SMD:SOT-23-5')

    ldo_adc_in  += U5['IN'], U5['EN']
    gnd         += U5['GND']
    ldo_adc_out += U5['OUT']

    C28 = _c0402(ref='C28', value='100nF')   # U5 NR (noise reduction) cap
    U5['NR'] += C28[1]
    gnd      += C28[2]

    C12 = _c0603(ref='C12', value='1uF')     # U5 output cap, before FB3
    ldo_adc_out += C12[1]
    gnd         += C12[2]

    # FB3 + C16/C26 form the output-side pi filter onto the ADC rail. The LDO senses
    # before the ferrite, so the ~0.15 ohm DCR costs ~8 mV of load regulation at
    # 55 mA -- acceptable for a rail whose absolute value is trimmed out by the ADC's
    # own reference, and worth it for the HF isolation.
    ldo_adc_out += FB3[1]
    v3v3a_adc   += FB3[2]

    C16 = _c0603(ref='C16', value='1uF')
    C26 = _c0402(ref='C26', value='100nF')
    for c in (C16, C26):
        v3v3a_adc += c[1]
        gnd       += c[2]

    # =============================================================================
    # 5. U6 -- TPS73633 LDO, VBUS_SW -> +3V3A_AMP (43 mA, front-end amps + U7)
    #    Identical topology to U5. A SEPARATE LDO, not a shared rail: the ADC's
    #    switching input currents must not land on the amplifiers' supply.
    # =============================================================================
    vbus_sw    += FB2[1]
    ldo_amp_in += FB2[2]

    C14 = _c0805(ref='C14', value='10uF')
    ldo_amp_in += C14[1]
    gnd        += C14[2]

    U6 = Part('Regulator_Linear', 'TPS73633DBV', ref='U6', value='TPS73633DBVR',
              footprint='Package_TO_SOT_SMD:SOT-23-5')

    ldo_amp_in  += U6['IN'], U6['EN']
    gnd         += U6['GND']
    ldo_amp_out += U6['OUT']

    C29 = _c0402(ref='C29', value='100nF')   # U6 NR cap
    U6['NR'] += C29[1]
    gnd      += C29[2]

    C15 = _c0603(ref='C15', value='1uF')     # U6 output cap, before FB4
    ldo_amp_out += C15[1]
    gnd         += C15[2]

    ldo_amp_out += FB4[1]
    v3v3a_amp   += FB4[2]

    C17 = _c0603(ref='C17', value='1uF')
    C27 = _c0402(ref='C27', value='100nF')
    for c in (C17, C27):
        v3v3a_amp += c[1]
        gnd       += c[2]

    # =============================================================================
    # 6. U7 -- TLV2372IDR dual RRIO op-amp, SOIC-8, the DC references.
    #    KiCad symbol Amplifier_Operational:TLV2372 extends LM2904 and names its
    #    signal pins '+', '-', '~', all duplicated across the two units -- so every
    #    pin is addressed BY NUMBER:
    #       unit A: 1 = OUT1, 2 = IN1-, 3 = IN1+
    #       unit B: 7 = OUT2, 6 = IN2-, 5 = IN2+
    #       power : 8 = V+,   4 = V-
    #
    #    Unit A buffers VREF_OFF, the front end's offset reference:
    #       R14 (10.0k) / R15 (12.1k) off +3V3A_AMP -> 3.3 * 12.1/22.1 = 1.8068 V.
    #    It MUST be buffered: R101/R201 in the two analog_frontend instances return
    #    the attenuator's bottom leg to this node, so it sinks and sources current
    #    with the signal. A bare divider would modulate with the input.
    #
    #    Unit B is the spare half, tied as a unity-gain follower with its input on
    #    VCM_REF -- required so the unused channel cannot oscillate or sit with a
    #    floating input (sourcing decision #5 and datasheets "Next phase must" #7).
    #    Its output drives nothing on purpose; see the block handoff for the option
    #    of using it to buffer VCM_REF instead.
    # =============================================================================
    U7 = Part('Amplifier_Operational', 'TLV2372', ref='U7', value='TLV2372IDR',
              footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')

    v3v3a_amp += U7[8]      # V+
    gnd       += U7[4]      # V-

    C23 = _c0402(ref='C23', value='100nF')   # C_DECOUP_U7
    v3v3a_amp += C23[1]
    gnd       += C23[2]

    R14 = _r0402(ref='R14', value='10.0k')   # VREF_OFF div top  (+3V3A_AMP -> tap)
    R15 = _r0402(ref='R15', value='12.1k')   # VREF_OFF div bottom (tap -> GND)

    v3v3a_amp += R14[1]
    vref_div  += R14[2], R15[1]
    gnd       += R15[2]

    # =============================================================================
    #    CAPACITIVE-LOAD ISOLATION (R19, added rev.6 from the phase-6 review):
    #    VREF_OFF carries C24 (100 nF) here plus C113 and C213 (100 nF each) in the
    #    two analog_frontend instances -- ~300 nF on a unity-gain follower output.
    #    TLV2372 datasheet SLOS270F section 8.3.2 "Driving a Capacitive Load":
    #    "for capacitive loads of greater than 10 pF, TI recommends that a resistor
    #    be placed in series (RNULL) with the output ... A minimum value of 20 Ohm
    #    should work well for most applications" (Figure 34). Figure 20 (phase
    #    margin vs capacitive load) is only characterised to 1000 pF, and at that
    #    point RNULL = 0 has already collapsed the phase margin; this net is 300x
    #    past the end of that curve. Direct drive is not a marginal case:
    #    with an open-loop Ro of 100-1000 Ohm the CL pole sits at 0.5-5 kHz, the
    #    loop crosses over near sqrt(GBW*f_p) ~ 40-90 kHz and the phase margin is a
    #    few degrees -> ringing/oscillation on the offset reference of BOTH channels.
    #    Fix, per Figure 34: R19 = 22 Ohm (nearest E24 value >= TI's 20 Ohm minimum)
    #    between the op-amp output and the load, with the FEEDBACK TAKEN AT THE
    #    OP-AMP OUTPUT (VREF_OFF_AMP) and ALL of the capacitance on the far side.
    #    The load pole moves to 1/(2*pi*(Ro+22)*300n) and a zero appears at
    #    1/(2*pi*22*300n) = 24 kHz, a decade or more below the new crossover ->
    #    phase margin back above 70 deg for any plausible Ro.
    #    C24 therefore sits on VREF_OFF (the LOAD side), not on VREF_OFF_AMP: it is
    #    the load being isolated, and it is also what gives C101/C201's HF return
    #    current a path to GND that does not run back through R19.
    #    Costs, both inside SPEC F12 (gain <= +/-2 % FS, offset <= +/-1 % FS):
    #      - R19 adds 22 Ohm to each channel's 90.9 kOhm attenuator bottom leg at
    #        DC -> 0.024 % gain error, shelving away above 24 kHz.
    #      - Each bottom leg swings -11.8/+8.2 uA, NOT a symmetric +/-8.2 uA: BUFIN
    #        spans 0.734-2.552 V about a 1.807 V reference, so the negative
    #        excursion is 1.073 V against the positive 0.745 V. Worst case is both
    #        legs at -11.8 uA -> -23.6 uA x 22 Ohm = -0.52 mV on VREF_OFF, which is
    #        5.2 mV referred to a +/-10 V input (x0.909 into the victim's ATT node,
    #        then /0.0909 back to the BNC = x10) = 0.026 % of the 20 V FS span.
    #      - Shared-impedance crosstalk: CH2's worst-case -11.8 uA puts -0.26 mV on
    #        VREF_OFF, reaching CH1's BUFIN at 0.909x -> 2.6 mV input-referred,
    #        i.e. -78 dB against the 20 V p-p full scale at DC (-81 dB on the
    #        positive excursion), falling above 24 kHz as the 300 nF shunts R19.
    #        At 12 bits the LSB is 4.88 mV, so that is ~0.5 LSB. Corrected from the
    #        -75 dB recorded at rev.6, which assumed a symmetric +/-8.2 uA swing;
    #        the real figure is marginally worse. SPEC states no channel-isolation
    #        requirement, so this is recorded rather than traded away. Comment-only
    #        correction -- no part, value or connection in this block changed.
    # =============================================================================
    vref_div += U7[3]           # IN1+  <- 1.8068 V divider tap
    vref_amp += U7[1], U7[2]    # OUT1 and IN1- (follower) -- feedback AT THE OUTPUT

    R19 = _r0402(ref='R19', value='22R')     # RNULL, SLOS270F Fig. 34 (min 20 Ohm)
    vref_amp += R19[1]
    vref_off += R19[2]

    C24 = _c0402(ref='C24', value='100nF')   # VREF_OFF bypass -- LOAD side of R19
    vref_off += C24[1]
    gnd      += C24[2]

    # VCM_REF -- unbuffered 1:1 divider, 3.3/2 = 1.650 V, per net_plan.md. It drives
    # only U103.VOCM / U203.VOCM, which are high-impedance inputs.
    R16 = _r0402(ref='R16', value='10.0k')   # VCM_REF div top
    R17 = _r0402(ref='R17', value='10.0k')   # VCM_REF div bottom

    v3v3a_amp += R16[1]
    vcm_ref   += R16[2], R17[1]
    gnd       += R17[2]

    C25 = _c0402(ref='C25', value='100nF')   # VCM_REF bypass (net_plan "C-bypass")
    vcm_ref += C25[1]
    gnd     += C25[2]

    # Spare half as a unity-gain follower on VCM_REF.
    vcm_ref += U7[5]            # IN2+
    U7[7] += U7[6]              # OUT2 -> IN2-, gain of 1, output unloaded
