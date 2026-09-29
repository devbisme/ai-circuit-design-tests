"""Power — Digital rails (3.3 V buck + 1.2 V LDO core) — generates V3V3_D and V1V2_CORE
Block from: architecture/block_diagram.md
Interface nets: vbus_5v, v3v3_d, v1v2_core, gnd
"""
from skidl import *

@subcircuit
def power_digital(vbus_5v, v3v3_d, v1v2_core, gnd):
    """Digital power tree: 5 V -> 3.3 V (buck) -> 1.2 V (LDO, iCE40 core).

    Per net_plan.md sec 3.2. 3V3_D is deliberately a synchronous BUCK (TLV62569), not an
    LDO: at the ~250 mA digital load (FPGA + SRAM + flash + FT2232H + ADC OVDD), an LDO
    dropping 5V->3.3V would burn (5-3.3)*0.25A = 0.425 W ~= 17% of the 2.5 W board power
    budget (SPEC Sec3.1). The buck keeps that loss to a few tens of mW.

    V1V2_CORE (iCE40 core, ~tens of mA) stays an LDO (U2, TLV75512) off the 3.3 V rail --
    the small V drop and light load make the LDO's simplicity/low-noise worth it there.

    ARCHITECTURAL NOTE (SPEC Sec3.4, risk R6): this buck is the single largest noise
    injector on a 12-bit-precision board. 1.5 MHz switching harmonics can couple into the
    analog chain via ground/plane and via radiated field from L3. Layout keep-out:
    U1/L3/swNode copper must be kept away from and NOT routed under the AFE/ADC/VREF
    analog areas (power_analog, vref_2v5, afe_channel, adc_dual blocks); route the digital
    ground return for this block so its high di/dt loop (VIN cap -> U1 -> L3 -> VOUT cap)
    stays physically compact and does not bisect the analog ground pour.

    Args:
        vbus_5v: 5 V USB bus supply (buck input), from usb_power_input
        v3v3_d: 3.30 V digital rail (buck output), feeds fpga_ice40, sram_buffer,
            config_flash, usb_bridge_ft2232h, adc_dual (OVDD), aux_io
        v1v2_core: 1.20 V FPGA core rail (LDO output), feeds fpga_ice40 only
        gnd: Ground reference
    """

    # ------------------------------------------------------------------
    # U1: TLV62569DBVR, 2 A synchronous buck, 1.5 MHz, adjustable 0.6V-VIN.
    # LCSC C141836. KiCad symbol "Regulator_Switching:TLV62569DBV" documents this exact
    # MPN as package DBV = SOT-23-5 (5 pins: EN, GND, SW, VIN, FB -- no PG pin, that's
    # only on the "P" power-good variant in a 6-pin DDC/DRL package). The work order
    # listed "SOT-23-6"; per the TI datasheet (TLV62569DBVR.pdf, Sec5 Pin Configuration)
    # and the KiCad footprint property on this exact symbol, DBVR is unambiguously
    # SOT-23-5. Using SOT-23-5 here as the datasheet-verified correction.
    # ------------------------------------------------------------------
    u1 = Part("Regulator_Switching", "TLV62569DBV", ref="U1", value="TLV62569DBVR",
              footprint="Package_TO_SOT_SMD:SOT-23-5")

    # Input bulk + HF decoupling at U1.VIN, on VBUS_5V (BOM Sec6/Sec7.3).
    c10 = Part("Device", "C", ref="C10", value="10uF",
               footprint="Capacitor_SMD:C_0805_2012Metric")   # input bulk
    c11 = Part("Device", "C", ref="C11", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")   # input HF decoupling

    vbus_5v += u1["VIN"], c10[1], c11[1]
    gnd += c10[2], c11[2]

    # U1.GND (pin 2) -- the buck's power AND analog return. Omitted in the first
    # draft of this block and caught by ERC on the assembled circuit ("Unconnected
    # pin: POWER-IN pin 2/GND"): without it the converter has no return path at all
    # and the FB divider has no reference.
    gnd += u1["GND"]

    # EN: always-on. No post-enumeration USB power switching in this design -- tie EN to
    # VBUS_5V (same net as VIN) through R12 (100k) per net_plan Sec3.2. The series
    # resistor is not a divider (EN leakage is ~nA per the datasheet, so the IR drop is
    # negligible); it simply limits inrush/ESD current into the EN pin while presenting a
    # solid logic-high referenced to VIN as soon as VBUS_5V is present.
    r12 = Part("Device", "R", ref="R12", value="100k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    vbus_5v += r12[1]
    r12[2] += u1["EN"]

    # SW node (block-internal, high di/dt -- keep this loop tight and away from analog).
    swNode = Net("swNode")
    swNode += u1["SW"]

    # L3: 2.2 uH buck inductor, >=2 A saturation, SHIELDED, 4x4 mm.
    # SHIELDED IS MANDATORY (not a preference): an unshielded/open-core inductor here
    # would radiate 1.5 MHz switching-harmonic flux directly into a board whose whole
    # purpose is a 12-bit, sub-mV-noise analog front end (SPEC Sec3.4). Footprint mapped
    # to the closest stocked 4x4x1.8mm shielded power-inductor package (Vishay IFSC-1515AH
    # form factor) per BOM Sec6 note "4x4 mm shielded, mandatory".
    l3 = Part("Device", "L", ref="L3", value="2.2uH",
              footprint="Inductor_SMD:L_Vishay_IFSC-1515AH_4x4x1.8mm")
    l3[1] += swNode
    l3[2] += v3v3_d

    # Output bulk (2x22 uF) + HF decoupling on V3V3_D, at the L3/U1 output node
    # (net_plan Sec3.2: "L3 -> C12,C13 (2x22uF) + C14 (100n)").
    c12 = Part("Device", "C", ref="C12", value="22uF",
               footprint="Capacitor_SMD:C_0805_2012Metric")
    c13 = Part("Device", "C", ref="C13", value="22uF",
               footprint="Capacitor_SMD:C_0805_2012Metric")
    c14 = Part("Device", "C", ref="C14", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    v3v3_d += c12[1], c13[1], c14[1]
    gnd += c12[2], c13[2], c14[2]

    # ------------------------------------------------------------------
    # FB divider R10 (top, V3V3_D->FB) / R11 (bottom, FB->GND).
    # TLV62569 internal reference VFB = 0.600 V typical (0.588-0.612 datasheet range),
    # regulated so that VOUT = VFB * (1 + R10/R11).
    #
    # Target VOUT = 3.30 V  =>  R10/R11 = (3.30/0.60) - 1 = 4.50
    # Choose R11 = 100.0 kOhm (1% E96) for low divider current (keeps light-load/PSM
    # efficiency high, matches the datasheet's own low-IQ examples which favor
    # 100k-200k-class dividers over a minimum-resistance one).
    #   R10 = 4.50 * 100.0k = 450.0k  -> nearest 1% E96 value = 453 kOhm
    #   VOUT = 0.6 * (1 + 453/100) = 0.6 * 5.53 = 3.318 V  (+0.55% vs 3.300 V target,
    #   well inside the ADC/FPGA 3.3V rail tolerance and inside the buck's own +/-2% VFB
    #   spec width)
    # Divider current = 3.3V / 553k = ~6.0 uA -- negligible vs U1's 35 uA quiescent draw.
    # ------------------------------------------------------------------
    buckFbNode = Net("buckFbNode")
    r10 = Part("Device", "R", ref="R10", value="453k",
               footprint="Resistor_SMD:R_0402_1005Metric")   # top: V3V3_D -> FB
    r11 = Part("Device", "R", ref="R11", value="100k",
               footprint="Resistor_SMD:R_0402_1005Metric")   # bottom: FB -> GND

    v3v3_d += r10[1]
    r10[2] += buckFbNode
    buckFbNode += r11[1], u1["FB"]
    gnd += r11[2]

    # ------------------------------------------------------------------
    # U2: TLV75512PDBVR, fixed 1.2 V LDO, 500 mA, SOT-23-5. LCSC C2877864.
    # Confirmed against the KiCad "Regulator_Linear:TLV75512PDBV" symbol (extends the
    # generic TLV70012_SOT23-5 pinout): IN(1), GND(2), EN(3), NC(4), OUT(5).
    # Supplies the iCE40 1.2 V core rail (V1V2_CORE), net_plan Sec3.2.
    # ------------------------------------------------------------------
    u2 = Part("Regulator_Linear", "TLV75512PDBV", ref="U2", value="TLV75512PDBVR",
              footprint="Package_TO_SOT_SMD:SOT-23-5")

    # Local decoupling at U2.IN (net_plan Sec3.2: "U2(TLV75512).IN, C15"). The rail
    # already carries C12/C13 (2x22uF) bulk a few mm upstream, well above the datasheet's
    # 1 uF CIN minimum; C15 is the local 100 nF HF bypass right at the package pin.
    c15 = Part("Device", "C", ref="C15", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    v3v3_d += u2["IN"], c15[1]
    gnd += c15[2], u2["GND"]

    # EN: always-on. Net_plan Sec3.2 specifies R12 only for U1's EN; it is silent on
    # U2.EN. JUDGEMENT CALL: tie U2.EN directly to its own input rail (V3V3_D), the same
    # pattern as U1 but without a series resistor -- U2's EN leakage is ~10 nA (datasheet
    # Sec6.5), so no current-limiting/inrush concern exists, and V3V3_D is already the
    # supervised/sequenced rail (it only exists once U1 is enabled and in regulation), so
    # this gives correct power-up sequencing (1.2V core only comes up after 3.3V is
    # present) with no extra part. Escalate to architecture if a switched/controllable
    # V1V2_CORE enable is later required (e.g. FPGA-sequenced power-up).
    v3v3_d += u2["EN"]

    # NC pin (datasheet: "No internal connection") -- intentionally left unconnected.
    u2["NC"] += NC

    # Output bulk + HF decoupling on V1V2_CORE (net_plan Sec3.2: "U2.OUT -> C16(10uF) +
    # C17(100n)").
    c16 = Part("Device", "C", ref="C16", value="10uF",
               footprint="Capacitor_SMD:C_0805_2012Metric")
    c17 = Part("Device", "C", ref="C17", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    v1v2_core += u2["OUT"], c16[1], c17[1]
    gnd += c16[2], c17[2]
