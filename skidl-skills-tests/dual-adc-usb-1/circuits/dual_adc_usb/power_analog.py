"""Analog Power — isolated 3.0 V ADC AVDD LDO + LM27762 charge-pump/LDO +-4.00 V rails
Block from: architecture/block_diagram.md
Interface nets: vbus_a5v, v3v0_avdd, vp4v0, vn4v0, gnd
"""
from skidl import *

@subcircuit
def power_analog(vbus_a5v, v3v0_avdd, vp4v0, vn4v0, gnd):
    """Analog supply rails: isolated ADC AVDD LDO and the +-4.00 V analog amplifier rails.

    Architecture references:
      - net_plan.md section 3.3 (this block's literal net/part table)
      - ic_selection.md section 4.3 (LP5907-3.0 AVDD LDO selection, genuine-part flag)
      - ic_selection.md section 4.4 (LM27762 +-4.00 V rail derivation / headroom arithmetic)
      - sourced_bom.md section 6 (power tree parts), section 6.1 (counterfeit-clone rejection)
      - SPEC.md section 3.1 (split analog/digital supply at source)
      - SPEC.md section 3.4 (keep 2 MHz charge-pump residue off AVDD / front end)

    Args:
        vbus_a5v: Post-ferrite, analog-side 5 V USB bus rail (from usb_power_input). Feeds both
                  regulators in this block. Physically isolated from VBUS_5V (digital) by a
                  ferrite in usb_power_input -- SPEC section 3.1.
        v3v0_avdd: Regulated 3.00 V, ultra-low-noise rail for adc_dual's analog VDD ONLY. Never
                   shared with V3V3_D (digital) -- net_plan.md section 1.1, SPEC section 3.1.
        vp4v0: Regulated +4.00 V analog rail (LM27762 OUT+, FB-divider trimmed). Feeds
               afe_channel A/B, vref_2v5, clock_40m osc LDO input.
        vn4v0: Regulated -4.00 V analog rail (LM27762 OUT-, FB-divider trimmed). Feeds
               afe_channel A/B, vref_2v5.
        gnd: Ground reference.
    """

    # ------------------------------------------------------------------
    # U3 -- LP5907MFX-3.0/NOPB : VBUS_A5V -> V3V0_AVDD (ADC analog VDD only)
    # ------------------------------------------------------------------
    # ic_selection.md section 4.3: LP5907-3.0 chosen for 6.5 uVrms noise / 82 dB PSRR@1kHz --
    # this rail directly sets the ADC's noise floor, so noise spec is the selection driver.
    #
    # sourced_bom.md section 6.1: LCSC C23380873 ("TECH PUBLIC" clone, noise unspecified) was
    # REJECTED at sourcing. This design uses ONLY the genuine TI part, LCSC C475492.
    #
    # SPEC section 3.1 / net_plan section 1.1: this LDO is a SEPARATE regulator off VBUS_A5V,
    # not a tap off the digital 3.3 V rail -- keeps digital switching noise off ADC AVDD.
    u3 = Part(
        "Regulator_Linear", "LP5907MFX-3.0",
        ref="U3", value="LP5907MFX-3.0/NOPB",
        footprint="Package_TO_SOT_SMD:SOT-23-5",
    )
    u3.fields["manf#"] = "LP5907MFX-3.0/NOPB"
    u3.fields["LCSC"] = "C475492"

    # U3.IN input cap -- net_plan section 3.3: "U3(LP5907-3.0).IN + C20"
    c20 = Part("Device", "C", ref="C20", value="1uF",
               footprint="Capacitor_SMD:C_0603_1608Metric")

    # EN not itemised in net_plan's table for U3; per LP5907 datasheet EN must be tied high for
    # always-on operation (mirrors U1.EN-always-on pattern documented for power_digital in
    # net_plan section 3.2, and the U9.OE-tied-high pattern in clock_40m section 3.7). Tied
    # directly to IN -- no enable control needed on this always-on analog rail.
    u3["IN"] += vbus_a5v, c20[1]
    u3["EN"] += vbus_a5v
    u3["GND"] += gnd
    c20[2] += gnd
    u3["NC"] += NC  # LP5907 SOT-23-5 pin 4 is a no-connect per datasheet

    # V3V0_AVDD: U3.OUT -> L4 ferrite -> C22(10uF) + C23(100nF)
    # SPEC section 3.4: ferrite isolation keeps this rail's own regulator quiet locally; the
    # LM27762's 2 MHz charge-pump residue lives on a *different* regulator entirely (U4) so it
    # never reaches AVDD through this path -- U3/U4 share only the VBUS_A5V input node.
    avddPreFerrite = Net("avddPreFerrite")
    u3["OUT"] += avddPreFerrite

    l4 = Part("Device", "FerriteBead_Small", ref="L4", value="600R@100MHz",
              footprint="Inductor_SMD:L_0603_1608Metric")
    l4[1] += avddPreFerrite
    l4[2] += v3v0_avdd

    c22 = Part("Device", "C", ref="C22", value="10uF",
               footprint="Capacitor_SMD:C_0805_2012Metric")
    c23 = Part("Device", "C", ref="C23", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    v3v0_avdd += c22[1], c23[1]
    gnd += c22[2], c23[2]

    # ------------------------------------------------------------------
    # U4 -- LM27762DSSR : VBUS_A5V -> charge pump -> +4.00 V / -4.00 V dual LDO
    # ------------------------------------------------------------------
    # ic_selection.md section 4.4: regulated +-5.0 V is NOT achievable from a 5 V USB bus with
    # this part (45 mV positive-LDO dropout needs >=5.05 V in; USB VBUS is 4.75 V min at the
    # receptacle). Rails are deliberately set to +-4.00 V instead -- see FB divider arithmetic
    # below. This is a documented deviation from SPEC section 3.1's literal "+-5 V", accepted
    # because the 3 V of headroom over the +-1 V signal swing fully retains what the +-5 V
    # rail was buying (common-mode headroom, level-shift removal, overdrive recovery).
    u4 = Part(
        "Regulator_SwitchedCapacitor", "LM27762",
        ref="U4", value="LM27762DSSR",
        footprint="Package_SON:WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65",
    )
    u4.fields["manf#"] = "LM27762DSSR"
    u4.fields["LCSC"] = "C473398"

    # VIN + input cap. net_plan section 3.3: "U4(LM27762).VIN + C21 (2.2 uF); U4.EN+, U4.EN-
    # tied to VIN" -- always-on, no sequencing/enable logic required for this design.
    c21 = Part("Device", "C", ref="C21", value="2.2uF",
               footprint="Capacitor_SMD:C_0805_2012Metric")
    u4["VIN"] += vbus_a5v, c21[1]
    c21[2] += gnd
    u4["EN+"] += vbus_a5v
    u4["EN-"] += vbus_a5v
    u4["GND"] += gnd
    u4["PAD"] += gnd  # exposed thermal/ground pad, WSON-12-EP
    u4["PGOOD"] += NC  # open-drain power-good, unused in this design (not in net_plan)

    # Charge-pump flying cap: U4.C+/C- <-> C24 (1 uF X7R >=10V). net_plan section 3.3
    # "internal cpFly+-".
    cpFlyP = Net("cpFlyP")
    cpFlyN = Net("cpFlyN")
    c24 = Part("Device", "C", ref="C24", value="1uF",
               footprint="Capacitor_SMD:C_0603_1608Metric")
    u4["C+"] += cpFlyP
    u4["C-"] += cpFlyN
    c24[1] += cpFlyP
    c24[2] += cpFlyN

    # Charge-pump output reservoir: U4.CPOUT -> C25 (4.7 uF). net_plan section 3.3
    # "internal cpOut". This node feeds the negative LDO internally; C25 is required by the
    # LM27762 datasheet for charge-pump stability, not a rail decoupling cap.
    cpOut = Net("cpOut")
    c25 = Part("Device", "C", ref="C25", value="4.7uF",
               footprint="Capacitor_SMD:C_0805_2012Metric")
    u4["CP"] += cpOut
    c25[1] += cpOut
    c25[2] += gnd

    # ------------------------------------------------------------------
    # VP4V0 -- positive LDO output, FB divider R20/R21
    # ------------------------------------------------------------------
    # net_plan section 3.3: "U4.OUT+ -> C26 (2.2 uF) -> L5 ferrite -> C27 (10uF) + C28 (100n);
    # FB+ divider R20/R21". C26 sits directly on OUT+ (required by LM27762 datasheet for LDO
    # loop stability) BEFORE the isolation ferrite; C27/C28 are the post-ferrite rail bulk +
    # local decoupling that afe_channel/vref_2v5/clock_40m actually see.
    #
    # FB+ divider arithmetic (ic_selection.md section 4.4):
    #   VOUT+ = VFB+ x (1 + R20/R21),  VFB+ = 1.200 V (typ, LM27762 datasheet SNVSAF7C)
    #   Target: VOUT+ = 4.00 V  =>  R20/R21 = (4.00 / 1.200) - 1 = 2.3333
    #   Choose R21 = 10.0 kOhm (E96, 1%)  =>  R20_ideal = 23.33 kOhm
    #   Nearest E96 1% value: R20 = 23.2 kOhm
    #   Actual VOUT+ = 1.200 x (1 + 23.2/10.0) = 1.200 x 3.32 = 3.984 V
    #   Deviation from 4.00 V target: -0.4%, well inside the 3 V headroom budget of
    #   ic_selection.md section 4.4 (signal swing is only +-1 V).
    vOutPPreCap = Net("vOutPPreCap")
    u4["OUT+"] += vOutPPreCap
    c26 = Part("Device", "C", ref="C26", value="2.2uF",
               footprint="Capacitor_SMD:C_0805_2012Metric")
    c26[1] += vOutPPreCap
    c26[2] += gnd

    l5 = Part("Device", "FerriteBead_Small", ref="L5", value="600R@100MHz",
              footprint="Inductor_SMD:L_0603_1608Metric")
    l5[1] += vOutPPreCap
    l5[2] += vp4v0

    c27 = Part("Device", "C", ref="C27", value="10uF",
               footprint="Capacitor_SMD:C_0805_2012Metric")
    c28 = Part("Device", "C", ref="C28", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    vp4v0 += c27[1], c28[1]
    gnd += c27[2], c28[2]

    # FB+ divider: R20 (top, OUT+ to FB+) / R21 (bottom, FB+ to GND). Sensed BEFORE the
    # isolation ferrite (feedback must see the true regulator output, not the filtered rail).
    fbPlus = Net("fbPlus")
    r20 = Part("Device", "R", ref="R20", value="23.2k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r21 = Part("Device", "R", ref="R21", value="10.0k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r20[1] += vOutPPreCap
    r20[2] += fbPlus
    r21[1] += fbPlus
    r21[2] += gnd
    u4["FB+"] += fbPlus

    # ------------------------------------------------------------------
    # VN4V0 -- negative LDO output, FB divider R22/R23
    # ------------------------------------------------------------------
    # net_plan section 3.3: "U4.OUT- -> C29 (2.2 uF) -> L6 ferrite -> C30 (10uF) + C31 (100n);
    # FB- divider R22/R23". Same OUT-cap-before-ferrite topology as the positive rail.
    #
    # FB- divider arithmetic (ic_selection.md section 4.4):
    #   VOUT- = VFB- x (1 + R22/R23),  VFB- = -1.220 V (typ, LM27762 datasheet SNVSAF7C)
    #   Target: VOUT- = -4.00 V  =>  R22/R23 = (-4.00 / -1.220) - 1 = 2.2787
    #   Choose R23 = 10.0 kOhm (E96, 1%)  =>  R22_ideal = 22.79 kOhm
    #   Nearest E96 1% value: R22 = 22.6 kOhm
    #   Actual VOUT- = -1.220 x (1 + 22.6/10.0) = -1.220 x 3.26 = -3.977 V
    #   Deviation from -4.00 V target: -0.57%, same headroom-budget rationale as VP4V0 above.
    vOutNPreCap = Net("vOutNPreCap")
    u4["OUT-"] += vOutNPreCap
    c29 = Part("Device", "C", ref="C29", value="2.2uF",
               footprint="Capacitor_SMD:C_0805_2012Metric")
    c29[1] += vOutNPreCap
    c29[2] += gnd

    l6 = Part("Device", "FerriteBead_Small", ref="L6", value="600R@100MHz",
              footprint="Inductor_SMD:L_0603_1608Metric")
    l6[1] += vOutNPreCap
    l6[2] += vn4v0

    c30 = Part("Device", "C", ref="C30", value="10uF",
               footprint="Capacitor_SMD:C_0805_2012Metric")
    c31 = Part("Device", "C", ref="C31", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    vn4v0 += c30[1], c31[1]
    gnd += c30[2], c31[2]

    # FB- divider: R22 (top, OUT- to FB-) / R23 (bottom, FB- to GND). Sensed BEFORE the
    # isolation ferrite, same rationale as FB+.
    fbMinus = Net("fbMinus")
    r22 = Part("Device", "R", ref="R22", value="22.6k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r23 = Part("Device", "R", ref="R23", value="10.0k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r22[1] += vOutNPreCap
    r22[2] += fbMinus
    r23[1] += fbMinus
    r23[2] += gnd
    u4["FB-"] += fbMinus
