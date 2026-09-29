"""Digital Power -- 3.3 V and 1.2 V digital rails
Block from: architecture/block_diagram.md
Interface nets: VBUS, GND, V3V3_D, V1V2
"""
from skidl import *


@subcircuit
def power_digital(vbus, gnd, v3v3_d, v1v2):
    """Digital power supply: VBUS -> U1 (AP7361C-33E, 3.3 V/1 A) -> V3V3_D,
    V3V3_D -> U2 (AP2112K-1.2, 1.2 V/600 mA) -> V1V2 (iCE40 core rail).

    Two cascaded fixed LDOs per net_plan.md:
      VBUS -> U1 IN, U1 OUT -> V3V3_D (190 mA budget; loads: iCE40 VCCIO banks,
              SRAM VDD, FT232H VCCIO/VPHY/VPLL, EEPROM, U2 IN, LED anodes)
      V3V3_D -> U2 IN, U2 OUT -> V1V2 (45 mA budget; loads: iCE40 VCC core, VCCPLL)

    U1 has no EN pin (always-on once VBUS is present through the upstream F1/D2 in
    usb_c_input) -- this block does not gate it. U2's EN is tied directly to its own
    VIN (V3V3_D) for an always-on 1.2 V rail; the architecture calls out no
    power-sequencing requirement for the FPGA core rail.

    U1's SOT-223 package is a fixed thermal requirement (sourcing risk R-11, 0.37 W
    dissipation at the 187 mA digital 3.3 V load) -- do not substitute a smaller
    package.

    A hardwired power-good LED (D3/R4, net_plan.md "LED_PWR") runs directly off
    V3V3_D -> GND and is not switched or FPGA-controlled.

    Args:
        vbus: USB VBUS input (4.40-5.25 V, from usb_c_input block), U1 IN
        gnd: Ground reference
        v3v3_d: 3.3 V digital rail output (U1 OUT), 190 mA budget -- driven by this block
        v1v2: 1.2 V FPGA core rail output (U2 OUT), 45 mA budget -- driven by this block
    """

    # --- U1: AP7361C-33E-13, 3.3 V/1 A fixed LDO, SOT-223 (fixed package, R-11) ---
    # No EN pin on this part (3-pin symbol) -- always-on as soon as VBUS is present.
    u1 = Part(
        "Regulator_Linear",
        "AP7361C-33E",
        ref="U1",
        value="AP7361C-33E-13",
        footprint="Package_TO_SOT_SMD:SOT-223",
    )
    u1["VI"] += vbus
    u1["VO"] += v3v3_d
    u1["GND"] += gnd

    # --- U2: AP2112K-1.2TRG1, 1.2 V/600 mA LDO with EN, SOT-23-5 ---
    # Feeds the iCE40 FPGA core rail (V1V2). EN tied to VIN (V3V3_D) for always-on
    # operation -- an active-HIGH EN pin must never float per ERC rules.
    u2 = Part(
        "Regulator_Linear",
        "AP2112K-1.2",
        ref="U2",
        value="AP2112K-1.2TRG1",
        footprint="Package_TO_SOT_SMD:SOT-23-5",
    )
    u2["VIN"] += v3v3_d
    u2["EN"] += v3v3_d  # always-on: EN tied to VIN
    u2["GND"] += gnd
    u2["VOUT"] += v1v2
    u2["NC"] += NC  # pin 4: no internal bond per AP2204K-1.5 base symbol (SOT-23-5 pkg)

    # --- Decoupling ---
    # Sourced BOM allocates exactly 5 caps across the two LDOs: C3/C4 (1 uF input caps,
    # one per LDO), C5/C6 (10 uF output/bulk caps, one per LDO), and a single C7
    # (100 nF) not itemized per-IC in the BOM. C7 is placed on U2's output (V1V2, the
    # FPGA core rail) rather than U1's, since V1V2 is the lower-voltage / lower-margin
    # rail most sensitive to HF noise, and the higher-current V3V3_D rail already gets
    # additional bulk decoupling downstream at the FPGA (fpga_core block, per
    # net_plan.md "iCE40HX4K (U9): ... 8x 100 nF on V3V3_D banks"). See handoff
    # Decisions (DPow1) for this call.

    # C3: U1 input cap (VBUS side)
    c3 = Part("Device", "C", ref="C3", value="1uF", footprint="Capacitor_SMD:C_0603_1608Metric")
    c3[1] += vbus
    c3[2] += gnd

    # C4: U2 input cap (V3V3_D side)
    c4 = Part("Device", "C", ref="C4", value="1uF", footprint="Capacitor_SMD:C_0603_1608Metric")
    c4[1] += v3v3_d
    c4[2] += gnd

    # C5: U1 output/bulk cap (V3V3_D)
    c5 = Part("Device", "C", ref="C5", value="10uF", footprint="Capacitor_SMD:C_0805_2012Metric")
    c5[1] += v3v3_d
    c5[2] += gnd

    # C6: U2 output/bulk cap (V1V2)
    c6 = Part("Device", "C", ref="C6", value="10uF", footprint="Capacitor_SMD:C_0805_2012Metric")
    c6[1] += v1v2
    c6[2] += gnd

    # C7: extra 100 nF HF decoupling, placed on V1V2 (see rationale above)
    c7 = Part("Device", "C", ref="C7", value="100nF", footprint="Capacitor_SMD:C_0402_1005Metric")
    c7[1] += v1v2
    c7[2] += gnd

    # --- Power-good LED (hardwired, net_plan.md "LED_PWR": V3V3_D -> R4 -> D3 -> GND) ---
    # Not switched, not FPGA-controlled -- always lit whenever V3V3_D is up.
    r4 = Part("Device", "R", ref="R4", value="1k", footprint="Resistor_SMD:R_0402_1005Metric")
    r4[1] += v3v3_d

    d3 = Part("Device", "LED", ref="D3", value="LED_green", footprint="LED_SMD:LED_0603_1608Metric")
    r4[2] += d3["A"]
    d3["K"] += gnd

    # --- Supply net drive (this block generates V3V3_D and V1V2) ---
    v3v3_d.drive = POWER
    v1v2.drive = POWER
