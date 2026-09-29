"""Vref 2V5 — precision 2.5 V reference, divided and buffered down to a
1.000 V unity-gain output that programs the dual ADC's full-scale span.
Block from: architecture/block_diagram.md
Interface nets: vbus_a5v, vp4v0, vn4v0, gnd, vref_1v0
"""
from skidl import *

@subcircuit
def vref_2v5(vbus_a5v, vp4v0, vn4v0, gnd, vref_1v0):
    """Precision reference chain feeding the LTC2292 SENSEA/SENSEB pins.

    WHY THIS BLOCK MATTERS: `vref_1v0` drives the LTC2292's SENSEA and
    SENSEB pins, which program the ADC full-scale span to +/-1 V = 2 Vpp
    (net_plan.md §3.4, §3.6). Any error in this reference maps DIRECTLY
    to a gain error on BOTH ADC channels — this is a single point of
    calibration accuracy for the whole front end. The LTC2292 datasheet
    requires SENSE to be bypassed to ground with 1 uF as close to the ADC
    pin as possible; those bypass caps live in `adc_dual`, NOT here — do
    not duplicate them in this block.

    Architecture (net_plan.md §3.4):
      - U5 (ADR4525BRZ, 2.5 V precision reference) runs directly off
        `vbus_a5v`, output net `vref2V5` (internal), decoupled on both
        input and output.
      - A precision 0.1% divider (R30/R31) steps `vref2V5` down to node
        `vrefDiv`, filtered by C44.
      - U6 (OPA192, unity-gain buffer) buffers `vrefDiv` onto the output
        `vref_1v0`, isolating the divider from the SENSE pin loading in
        `adc_dual`.

    Datasheet facts [VERIFIED-PDF] (datasheets/ADR4525_ADI_RevG.pdf,
    Rev G, 41 pp):
      - ADR4525BRZ (B grade): initial output error +/-0.02% MAX, and
        TCVOUT 2 ppm/degC MAX over -40 to +125 degC. This is far better
        than the "0.1% / 10 ppm" class the architecture originally
        assumed, and far better than SPEC's 25 ppm/degC reference target.
      - ORDER EARLY: U5 (ADR4525BRZ) stock is only 110 units per
        sourced_bom.md — the thinnest active line in this whole design.

    Args:
        vbus_a5v: Filtered analog 5 V USB bus rail (net_plan.md §2 power
            table). Feeds U5's VIN pin directly (linear reference, no
            local regulator needed at this current level).
        vp4v0: Positive analog rail for U6 (OPA192 unity buffer), V+.
        vn4v0: Negative analog rail for U6 (OPA192 unity buffer), V-.
        gnd: Ground reference.
        vref_1v0: Precision 1.000 V output driving the LTC2292 SENSEA and
            SENSEB pins in `adc_dual` (programs +/-1 V ADC full scale).
    """

    # ------------------------------------------------------------------
    # Internal nets (net_plan.md §3.4 marks these "(internal)" — they do
    # not cross the block boundary, so they are declared locally here).
    # ------------------------------------------------------------------
    vref2V5 = Net("vref2V5")   # U5 output, precision 2.500 V
    vrefDiv = Net("vrefDiv")   # R30/R31 divider junction, nominal 1.000 V

    # ------------------------------------------------------------------
    # U5 — ADR4525BRZ precision 2.5 V reference (net_plan.md §3.4).
    # Symbol Reference_Voltage:ADR4525, 8-lead SOIC-N (BRZ suffix).
    # Verified pin map by instantiation: 2=IN, 4=GND, 6=OUT; pins
    # 1, 3, 5, 7, 8 are ALL named "NC" in the symbol (multiple same-name
    # pins) — connect every one individually by pin NUMBER so none is
    # left floating (ERC would otherwise flag them).
    # ------------------------------------------------------------------
    u5 = Part(
        "Reference_Voltage", "ADR4525",
        ref="U5", value="ADR4525BRZ",
        footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    )
    u5["IN"] += vbus_a5v
    u5["GND"] += gnd
    u5["OUT"] += vref2V5
    # Intentional no-connects — datasheet-defined NC pins on the SOIC-8.
    for pin_num in (1, 3, 5, 7, 8):
        u5[pin_num] += NC

    # C40 (100 n) + C41 (10 uF) on the input, at vbus_a5v (net_plan §3.4).
    c40 = Part("Device", "C", ref="C40", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c40[1] += vbus_a5v
    c40[2] += gnd

    c41 = Part("Device", "C", ref="C41", value="10uF",
               footprint="Capacitor_SMD:C_0805_2012Metric")
    c41[1] += vbus_a5v
    c41[2] += gnd

    # C42 (100 n) + C43 (10 uF) on the output, at vref2V5 (net_plan §3.4).
    c42 = Part("Device", "C", ref="C42", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c42[1] += vref2V5
    c42[2] += gnd

    c43 = Part("Device", "C", ref="C43", value="10uF",
               footprint="Capacitor_SMD:C_0805_2012Metric")
    c43[1] += vref2V5
    c43[2] += gnd

    # ------------------------------------------------------------------
    # R30/R31 — precision 0.1% thin-film divider, vref2V5 -> vrefDiv -> gnd
    # (net_plan.md §3.4). Both 0603, 0.1% tolerance, thin film (YAGEO
    # RT0603 series per sourced_bom.md).
    #
    # Divider arithmetic (state explicitly, per work order):
    #   Vout = Vref * R31 / (R30 + R31)
    #        = 2.500 V * 1.000 k / (1.500 k + 1.000 k)
    #        = 2.500 V * 1.000 / 2.500
    #        = 1.0000 V   exactly.
    # ------------------------------------------------------------------
    r30 = Part("Device", "R", ref="R30", value="1.500k 0.1% TF",
               footprint="Resistor_SMD:R_0603_1608Metric")
    r30[1] += vref2V5
    r30[2] += vrefDiv

    r31 = Part("Device", "R", ref="R31", value="1.000k 0.1% TF",
               footprint="Resistor_SMD:R_0603_1608Metric")
    r31[1] += vrefDiv
    r31[2] += gnd

    # C44 (1 uF) — noise filter on the divider node vrefDiv (net_plan §3.4).
    c44 = Part("Device", "C", ref="C44", value="1uF",
               footprint="Capacitor_SMD:C_0603_1608Metric")
    c44[1] += vrefDiv
    c44[2] += gnd

    # ------------------------------------------------------------------
    # U6 — OPA192IDBVR unity-gain buffer, isolating the divider from the
    # ADC SENSE-pin loading in adc_dual (net_plan.md §3.4).
    #
    # SYMBOL SUBSTITUTION: no OPA192 symbol exists in the KiCad 9
    # library. Amplifier_Operational:OPA197xDBV is TI's pin-identical
    # SOT-23-5 stand-in (same package, same pinout) used here as a
    # drop-in symbol for the OPA192IDBVR MPN actually specified in the
    # BOM. Verified pin map by instantiation: 1=OUT (symbol name "~",
    # blank pin, accessed by NUMBER), 2=V-, 3=+ (IN+), 4=- (IN-), 5=V+.
    # Pin numbers are used throughout for clarity and because pins 1
    # ("~"), 3 ("+") and 4 ("-") have symbol names that are awkward or
    # ambiguous to index by name.
    # ------------------------------------------------------------------
    u6 = Part(
        "Amplifier_Operational", "OPA197xDBV",
        ref="U6", value="OPA192IDBVR",
        footprint="Package_TO_SOT_SMD:SOT-23-5",
    )
    u6[3] += vrefDiv     # IN+  <- divider node
    u6[1] += vref_1v0    # OUT  -> block output
    u6[4] += vref_1v0    # IN-  tied to OUT: unity-gain buffer
    u6[5] += vp4v0        # V+
    u6[2] += vn4v0        # V-

    # C45 (100 n) — local decoupling on the buffered output vref_1v0
    # (net_plan §3.4). This is separate from the LTC2292 SENSE 1 uF
    # bypass caps, which live in adc_dual, close to the ADC pins.
    c45 = Part("Device", "C", ref="C45", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c45[1] += vref_1v0
    c45[2] += gnd

    # ------------------------------------------------------------------
    # U6 rail decoupling — "U6.V+ / U6.V- with 100n each" (net_plan §3.4).
    # REF-RANGE NOTE: the assigned range for this block (U5, U6, R30,
    # R31, C40-C45) has no spare capacitor refs left for these two rail
    # caps — this is a genuine shortfall in the assigned range. Extending
    # to C46/C47 to cover it; flagged explicitly here and in the final
    # report back to the orchestrator.
    # ------------------------------------------------------------------
    c46 = Part("Device", "C", ref="C46", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c46[1] += vp4v0
    c46[2] += gnd

    c47 = Part("Device", "C", ref="C47", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c47[1] += vn4v0
    c47[2] += gnd
