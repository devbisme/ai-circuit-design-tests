"""Analog Power (gated) -- switched +5V/-5V/+3.3V analog rails + 0.5 V AFE bias
Block from: architecture/block_diagram.md
Interface nets: VBUS, GND, PWREN_N, V3V3_A, V3V3_CLK, V5_A, VN5_A, VREF_0V5_A, VREF_0V5_B
"""
from skidl import *


@subcircuit
def power_analog(vbus, gnd, pwren_n, v3v3_a, v3v3_clk, v5_a, vn5_a, vref_0v5_a, vref_0v5_b):
    """Gated analog power tree (decision A14 / risk R-10: PWREN#-gated analog rails
    are mandatory for USB pre-enumeration compliance -- the analog domain must be dead
    until the host has enumerated the device and PWREN_N is asserted low).

    Topology (per net_plan.md and sourcing/sourced_bom.md Block 3):
      Q1 (AO3401A P-FET, high-side load switch) -- Source=VBUS, Drain=internal V5_SW,
      Gate driven by a resistor network (R5 100k pull-up to VBUS = off by default,
      R6 10k series from PWREN_N = pulls the gate low and turns the switch on when
      PWREN_N is asserted, ~1 ms soft-start ramp per BOM note).

      V5_SW (switched, unregulated ~5 V, only present when PWREN_N is asserted) fans
      out through two independent ferrite-bead rail entries:
        FB2 -> L2/C12 post-filter -> V5_A (op-amp V+, U3 VIN)
        FB3 -> U4 (LP5907MFX-3.3, low-noise LDO) -> V3V3_A (ADC AVDD/DRVDD, OPA836 V+,
               REF3025 IN, and FB6 -> V3V3_CLK)
      This means V3V3_A and the LM2776 inverter (U3, whose VIN is V5_A) are ALSO gated
      by Q1, satisfying the "Q1 gates V5_A, V3V3_A, and the LM2776" binding constraint
      without a separate EN/PWREN_N fan-out to each regulator.

      U3 (LM2776) VIN=V5_A, EN tied to VIN (active-HIGH enable satisfied whenever the
      gated V5_A rail is up) -> VOUT -> L1/C13 post-filter -> VN5_A (op-amp V-).

      U5 (REF3025, 2.5 V precision reference) IN=V3V3_A -> OUT=internal VREF_2V5 ->
      R7 (4.02k)/R8 (1.00k) precision divider -> ~0.500 V tap -> VREF_0V5_A/_B (AFE
      OPA836 non-inverting offset input, per channel).

    AD9235 VIN- 1.500 V strapping split (see handoffs/04_datasheets.md and the
    AD9235BRUZ-20_SUMMARY.md "SENSE/REFT/REFB strapping" section): the datasheet phase
    called out that the ADC's VIN- 1.500 V DC bias needs a NEW divider off REF3025,
    distinct from the 0.5 V R7/R8 node here. THIS BLOCK DOES NOT BUILD THAT DIVIDER --
    it has no spare ref designators (R5-R9 are fully consumed: R5/R6 = Q1 gate, R7/R8 =
    the 0.5 V precision divider) and its interface does not expose VREF_2V5. The
    adc_channel block's own ref range (R120-R133 / R220-R233) reserves 2 spare
    resistors beyond its 12 R_damp for exactly this purpose; the AD9235 datasheet
    summary explicitly says precision is not critical for this DC bias node, so a local
    divider off V3V3_A (already exposed here) is an acceptable, simpler alternative to
    routing a new VREF_2V5 net across the block boundary. See this block's handoff
    "Carried forward" for the full rationale -- adc_channel coders must NOT wait for a
    net from this block for VIN-.

    Args:
        vbus: USB VBUS input (4.40-5.25 V, from usb_c_input), Q1 source
        gnd: Ground reference
        pwren_n: Active-low power-enable control (from usb_bridge FT232H ACBUS9),
            gates Q1 -> V5_A/V3V3_A/VN5_A/VREF_0V5_A/VREF_0V5_B
        v3v3_a: 3.3 V low-noise analog rail output (U4 LP5907 OUT), 105 mA budget --
            driven by this block
        v3v3_clk: 3.3 V clock-domain rail output (FB6 tap off V3V3_A), 20 mA budget --
            driven by this block
        v5_a: +5 V filtered analog rail output (post Q1/FB2/L2), 60 mA budget -- driven
            by this block
        vn5_a: -5 V filtered analog rail output (U3 LM2776 OUT, post L1 filter),
            30 mA budget -- driven by this block
        vref_0v5_a: 0.500 V AFE offset-bias output for channel A (OPA836 non-inverting
            input) -- driven by this block
        vref_0v5_b: 0.500 V AFE offset-bias output for channel B (OPA836 non-inverting
            input) -- driven by this block, via isolation resistor R9 (see Decisions)
    """

    # ------------------------------------------------------------------
    # Internal nets (not part of the interface)
    # ------------------------------------------------------------------
    v5_sw = Net("V5_SW")  # Q1 drain: switched, unregulated ~5 V (gated by PWREN_N)
    v5_a_mid = Net("V5_A_MID")  # between FB2 and L2 post-filter
    v3v3_a_pre = Net("V3V3_A_PRE")  # between FB3 and U4 IN (pre-LDO, still switched)
    vn5_raw = Net("VN5_RAW")  # U3 VOUT, pre L1 filter
    vref_2v5 = Net("VREF_2V5")  # U5 (REF3025) OUT, internal precision 2.5 V reference
    vref_0v5_tap = Net("VREF_0V5_TAP")  # R7/R8 divider midpoint (~0.500 V)
    gate_drive = Net("gateDrive")  # Q1 gate node (R5 pull-up / R6 series from PWREN_N)
    fly_p = Net("flyP")  # LM2776 C1+ flying-cap node
    fly_n = Net("flyN")  # LM2776 C1- flying-cap node

    # ------------------------------------------------------------------
    # Q1: AO3401A P-FET high-side load switch, gated by PWREN_N (A14/R-10)
    # ------------------------------------------------------------------
    q1 = Part(
        "Transistor_FET",
        "Q_PMOS_GSD",
        ref="Q1",
        value="AO3401A",
        footprint="Package_TO_SOT_SMD:SOT-23",
    )
    q1["S"] += vbus  # source tied to incoming (fused) VBUS
    q1["D"] += v5_sw  # drain: switched raw ~5 V rail
    q1["G"] += gate_drive

    # R5: gate pull-up to source (VBUS) -- off by default when PWREN_N is not sinking
    r5 = Part("Device", "R", ref="R5", value="100k", footprint="Resistor_SMD:R_0402_1005Metric")
    r5[1] += gate_drive
    r5[2] += vbus

    # R6: gate series resistor from PWREN_N -- pulls the gate low (Vgs << Vgs(th)) when
    # PWREN_N is asserted, turning Q1 on; forms a ~1 ms soft-start ramp with Q1's own
    # gate capacitance per the sourced BOM note.
    r6 = Part("Device", "R", ref="R6", value="10k", footprint="Resistor_SMD:R_0402_1005Metric")
    r6[1] += gate_drive
    r6[2] += pwren_n

    # ------------------------------------------------------------------
    # +5V_A entry: FB2 ferrite isolates the analog domain from the switched node,
    # L2/C12 post-filter cleans the rail for the AFE op-amps and feeds U3 (LM2776) VIN.
    # ------------------------------------------------------------------
    fb2 = Part(
        "Device",
        "FerriteBead",
        ref="FB2",
        value="BLM18PG601SN1D",
        footprint="Inductor_SMD:L_0603_1608Metric",
    )
    fb2[1] += v5_sw
    fb2[2] += v5_a_mid

    l2 = Part(
        "Device",
        "L",
        ref="L2",
        value="LQM2HPN100MGL",  # 10 uH, DCR ~0.35 Ohm, Idc ~550 mA (Murata)
        footprint="Inductor_SMD:L_0805_2012Metric",
    )
    l2[1] += v5_a_mid
    l2[2] += v5_a

    # C12: V5_A bulk post-filter cap
    c12 = Part("Device", "C", ref="C12", value="22uF", footprint="Capacitor_SMD:C_1206_3216Metric")
    c12[1] += v5_a
    c12[2] += gnd

    # ------------------------------------------------------------------
    # V3V3_A entry: FB3 ferrite isolates the analog 3.3 V domain from the switched
    # node, feeding U4 (LP5907MFX-3.3, ultra-low-noise LDO, EN required).
    # ------------------------------------------------------------------
    fb3 = Part(
        "Device",
        "FerriteBead",
        ref="FB3",
        value="BLM18PG601SN1D",
        footprint="Inductor_SMD:L_0603_1608Metric",
    )
    fb3[1] += v5_sw
    fb3[2] += v3v3_a_pre

    u4 = Part(
        "Regulator_Linear",
        "LP5907MFX-3.3",
        ref="U4",
        value="LP5907MFX-3.3/NOPB",
        footprint="Package_TO_SOT_SMD:SOT-23-5",
    )
    u4["IN"] += v3v3_a_pre
    u4["EN"] += v3v3_a_pre  # always-on once the gated switched rail is present
    u4["GND"] += gnd
    u4["OUT"] += v3v3_a
    u4["NC"] += NC  # pin 4, no internal bond (LP5907MFX-1.2 base symbol, SOT-23-5)

    # ------------------------------------------------------------------
    # -5V_A: U3 (LM2776) switched-capacitor inverter, VIN=V5_A (already gated/filtered)
    # EN tied to VIN so the inverter only runs when V5_A is up -- this is how "the
    # LM2776" is gated by PWREN_N per the binding constraint, without a direct EN
    # connection to pwren_n (which is a 3.3 V logic signal, not a valid EN reference
    # for a part whose EN threshold is referenced to its own ~5 V VIN).
    # ------------------------------------------------------------------
    u3 = Part(
        "Regulator_SwitchedCapacitor",
        "LM2776",
        ref="U3",
        value="LM2776DBVR",
        footprint="Package_TO_SOT_SMD:SOT-23-6",
    )
    u3["VIN"] += v5_a
    u3["EN"] += v5_a
    u3["GND"] += gnd
    u3["VOUT"] += vn5_raw
    u3["C1+"] += fly_p
    u3["C1-"] += fly_n

    # C8, C9: flying cap, paralleled for lower ESR/higher available charge-pump current
    c8 = Part("Device", "C", ref="C8", value="1uF", footprint="Capacitor_SMD:C_0603_1608Metric")
    c8[1] += fly_p
    c8[2] += fly_n
    c9 = Part("Device", "C", ref="C9", value="1uF", footprint="Capacitor_SMD:C_0603_1608Metric")
    c9[1] += fly_p
    c9[2] += fly_n

    # C10: U3 VIN bulk cap
    c10 = Part("Device", "C", ref="C10", value="10uF", footprint="Capacitor_SMD:C_0805_2012Metric")
    c10[1] += v5_a
    c10[2] += gnd

    # C11: U3 VOUT bulk cap (pre-filter)
    c11 = Part("Device", "C", ref="C11", value="10uF", footprint="Capacitor_SMD:C_0805_2012Metric")
    c11[1] += vn5_raw
    c11[2] += gnd

    # L1/C13: -5V_A post-filter
    l1 = Part(
        "Device",
        "L",
        ref="L1",
        value="LQM2HPN100MGL",  # 10 uH, DCR ~0.35 Ohm, Idc ~550 mA (Murata)
        footprint="Inductor_SMD:L_0805_2012Metric",
    )
    l1[1] += vn5_raw
    l1[2] += vn5_a

    c13 = Part("Device", "C", ref="C13", value="22uF", footprint="Capacitor_SMD:C_1206_3216Metric")
    c13[1] += vn5_a
    c13[2] += gnd

    # ------------------------------------------------------------------
    # V3V3_CLK: FB6 taps V3V3_A to isolate the 10 MHz XO/buffer switching noise from
    # the ADC AVDD domain (clock_gen block places X1's own decoupling downstream).
    # ------------------------------------------------------------------
    fb6 = Part(
        "Device",
        "FerriteBead",
        ref="FB6",
        value="BLM18PG601SN1D",
        footprint="Inductor_SMD:L_0603_1608Metric",
    )
    fb6[1] += v3v3_a
    fb6[2] += v3v3_clk

    # ------------------------------------------------------------------
    # U5: REF3025, 2.5 V precision reference, IN=V3V3_A (clean analog 3.3 V rail).
    # OUT feeds the R7/R8 precision divider that sets the AFE 0.5 V offset bias.
    # ------------------------------------------------------------------
    u5 = Part(
        "Reference_Voltage",
        "REF3025",
        ref="U5",
        value="REF3025AIDBZR",
        footprint="Package_TO_SOT_SMD:SOT-23",
    )
    u5["IN"] += v3v3_a
    u5["OUT"] += vref_2v5
    u5["GND"] += gnd

    # R7/R8: 4.02k/1.00k 0.1% 25 ppm precision divider (Susumu RG1005N-4021-B-T5 /
    # RG1005N-1001-B-T5) off VREF_2V5 -> ~0.500 V tap (2.5 V * 1.00k/5.02k = 0.498 V).
    #
    # DEVIATION from net_plan.md's literal "one divider per channel" (2x R_top/R_bot,
    # 4 resistors): this block's ref-designator budget is fixed at R5-R9 (5 total) by
    # both the architecture and sourcing handoffs. R5/R6 are consumed by Q1's gate
    # network, leaving only R7/R8/R9 -- enough for ONE precision divider plus one
    # extra resistor, not two full dividers. A single shared reference divider (rather
    # than two separately-toleranced 4.02k/1.00k pairs) is arguably the better choice
    # here anyway: it guarantees channel A and channel B see the identical 0.500 V DC
    # offset, which is what matters for gain/offset matching between the two ADC
    # channels. R9 is used as a small series isolation resistor on the B-channel tap so
    # each channel still gets its own physical node for layout/decoupling purposes,
    # even though both are within ~50 uV of each other (negligible drop at the <1 uA
    # per net_plan.md load).
    r7 = Part("Device", "R", ref="R7", value="4.02k", footprint="Resistor_SMD:R_0402_1005Metric")
    r7[1] += vref_2v5
    r7[2] += vref_0v5_tap

    r8 = Part("Device", "R", ref="R8", value="1.00k", footprint="Resistor_SMD:R_0402_1005Metric")
    r8[1] += vref_0v5_tap
    r8[2] += gnd

    vref_0v5_a += vref_0v5_tap  # channel A: direct tap

    r9 = Part("Device", "R", ref="R9", value="100", footprint="Resistor_SMD:R_0402_1005Metric")
    r9[1] += vref_0v5_tap
    r9[2] += vref_0v5_b  # channel B: isolated through R9

    # NOTE: net_plan.md also calls for a 1 uF bypass cap to GND at each VREF_0V5_<X>
    # node. This block's cap allocation (C8-C21, all 14 used above) has no spare ref
    # designator for it. Per good practice this bypass belongs at the point of use
    # anyway (the OPA836 non-inverting input pin) -- see this block's handoff
    # "Carried forward" for the note to the afe_channel coder.

    # ------------------------------------------------------------------
    # Decoupling: U4 (LP5907) and U5 (REF3025) share C14-C17 (1 uF) for in/out bulk and
    # C18-C21 (100 nF) for per-pin HF decoupling, per sourced_bom.md Block 3.
    # ------------------------------------------------------------------
    c14 = Part("Device", "C", ref="C14", value="1uF", footprint="Capacitor_SMD:C_0603_1608Metric")
    c14[1] += v3v3_a_pre  # U4 IN
    c14[2] += gnd

    c15 = Part("Device", "C", ref="C15", value="1uF", footprint="Capacitor_SMD:C_0603_1608Metric")
    c15[1] += v3v3_a  # U4 OUT
    c15[2] += gnd

    c16 = Part("Device", "C", ref="C16", value="1uF", footprint="Capacitor_SMD:C_0603_1608Metric")
    c16[1] += v3v3_a  # U5 IN
    c16[2] += gnd

    c17 = Part("Device", "C", ref="C17", value="1uF", footprint="Capacitor_SMD:C_0603_1608Metric")
    c17[1] += vref_2v5  # U5 OUT bypass (also stabilizes the R7/R8 source)
    c17[2] += gnd

    c18 = Part("Device", "C", ref="C18", value="100nF", footprint="Capacitor_SMD:C_0402_1005Metric")
    c18[1] += v5_a  # U3 VIN pin
    c18[2] += gnd

    c19 = Part("Device", "C", ref="C19", value="100nF", footprint="Capacitor_SMD:C_0402_1005Metric")
    c19[1] += v3v3_a_pre  # U4 IN pin
    c19[2] += gnd

    c20 = Part("Device", "C", ref="C20", value="100nF", footprint="Capacitor_SMD:C_0402_1005Metric")
    c20[1] += v3v3_a  # U4 OUT pin
    c20[2] += gnd

    c21 = Part("Device", "C", ref="C21", value="100nF", footprint="Capacitor_SMD:C_0402_1005Metric")
    c21[1] += vref_2v5  # U5 OUT pin
    c21[2] += gnd

    # ------------------------------------------------------------------
    # Supply net drive: this block generates all of these from local regulators/
    # dividers -- VREF_0V5_A/_B are driven purely through a passive resistor divider
    # (no active output pin on that net), so .drive = POWER is set explicitly here to
    # mark this block as their source for ERC.
    # ------------------------------------------------------------------
    v3v3_a.drive = POWER
    v3v3_clk.drive = POWER
    v5_a.drive = POWER
    vn5_a.drive = POWER
    vref_0v5_a.drive = POWER
    vref_0v5_b.drive = POWER
