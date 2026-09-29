"""ADC dual — LTC2292 dual 12-bit 40 MSPS parallel-CMOS ADC.
Block from: architecture/block_diagram.md
Interface nets: v3v0_avdd, v3v3_d, gnd, vref_1v0, adc_vcm_a, adc_vcm_b,
                ain_ap, ain_an, ain_bp, ain_bn, enc_clk40,
                adc_data_a, adc_data_b, adc_of_a, adc_of_b,
                adc_shdn, adc_oe_bar
"""
from skidl import *


@subcircuit
def adc_dual(v3v0_avdd, v3v3_d, gnd, vref_1v0, adc_vcm_a, adc_vcm_b,
             ain_ap, ain_an, ain_bp, ain_bn,
             enc_clk40,
             adc_data_a, adc_data_b, adc_of_a, adc_of_b,
             adc_shdn, adc_oe_bar):
    """LTC2292 dual 12-bit 40 MSPS ADC, both channels sampled simultaneously.

    Every connection below is checked against
    `datasheets/LTC2292_LTC2293_LTC2291_229321fa.pdf` "Pin Functions" pp.11-12
    [VERIFIED-PDF] and against the 65-pin `Analog_ADC:LTC2292xUP` KiCad symbol.
    See net_plan.md §3.6, which was rewritten against the same two sources.

    THREE THINGS THAT ARE EASY TO GET WRONG HERE — all are datasheet facts:

    1. **There is no CLKOUT pin** (decision D3, net_plan.md §1.4.1). The part
       has CLKA (8) and CLKB (9), single-ended clock *inputs* only, and no
       ENC+/ENC- differential pair. The FPGA captures this bus using the
       `xoClkFpga` tap off the same 40 MHz XO, on its **FALLING** edge.

       Capture-edge arithmetic, from Timing Characteristics p.6 (LTC2292
       column, C_L = 5 pF, full temperature range):
         t_D(CLK->DATA) = 1.4 ns min / 2.7 typ / 5.4 ns max
       At 40 MHz (T = 25 ns) sample N is valid over [5.4, 26.4] ns — a 21.0 ns
       window measured from its own launching rising edge.
         - Rising-edge capture at 25 ns: setup 19.6 ns, hold only 1.4 ns. The
           iCE40's own t_H of 2.38 ns alone exceeds that, so it FAILS.
         - Falling-edge capture at 12.5 ns: **setup 7.1 ns, hold 13.9 ns**,
           near the centre of the window, and it needs no PLL. USE THIS.
       Holds across a 45/55 % duty cycle: worst case +5.49 ns setup /
       +11.98 ns hold after t_H, bank skew and trace mismatch.

    2. **VCMA (61) and VCMB (20) must NOT be joined.** The datasheet pin
       descriptions say verbatim "Do not connect to VCMB" and "Do not connect
       to VCMA". They are two independent 1.5 V outputs, exported here on two
       separate nets to the two `afe_channel` instances.

    3. **MODE (60) is biased to 1/3 V_DD, and that is required, not optional.**
       It selects offset-binary output *and turns the clock duty-cycle
       stabiliser ON*. With the stabiliser off the datasheet requires
       t_L/t_H >= 11.8 ns each, i.e. a duty cycle inside 47.2-52.8 %, which a
       generic 45/55 % XO violates. With it on, 40-60 % is accepted.

    Args:
        v3v0_avdd: 3.00 V analog supply from `power_analog`, VDD pins only.
        v3v3_d: 3.30 V digital supply; reaches OVDD through ferrite L8 so the
            26 switching output drivers never share a node with the analog rail.
        gnd: Ground (GND, OGND and the exposed pad are one netlist net; the
            split is a layout partition).
        vref_1v0: Precision 1.000 V from `vref_2v5`, driving SENSEA and SENSEB
            to program a +/-1 V = 2 Vpp full-scale span.
        adc_vcm_a: 1.5 V VCMA output -> `afe_channel('A')` FDA V_OCM.
        adc_vcm_b: 1.5 V VCMB output -> `afe_channel('B')` FDA V_OCM.
        ain_ap, ain_an: Channel A differential input from `afe_channel('A')`.
        ain_bp, ain_bn: Channel B differential input from `afe_channel('B')`.
        enc_clk40: 40 MHz LVCMOS encode clock from `clock_40m`, driving both
            CLKA and CLKB (adjacent package pins, so skew << the 1 ns limit).
        adc_data_a: Bus(12) DA0-DA11 -> `fpga_ice40`, 33 R series per line.
        adc_data_b: Bus(12) DB0-DB11 -> `fpga_ice40`, 33 R series per line.
        adc_of_a, adc_of_b: Over/under-range flags, 33 R series each.
        adc_shdn: Shutdown, driven by the FPGA; pulled DOWN so the ADC runs
            even while the FPGA is unconfigured.
        adc_oe_bar: Active-low output enable, likewise pulled DOWN (= enabled).
    """

    # ------------------------------------------------------------------
    # U7 — LTC2292CUP, QFN-64 (UP) 9x9 mm. Pin 65 is the exposed pad and is
    # ADC power ground: it MUST be soldered, not merely land-patterned.
    # ------------------------------------------------------------------
    u7 = Part(
        "Analog_ADC", "LTC2292xUP",
        ref="U7", value="LTC2292CUP",
        footprint="Package_DFN_QFN:QFN-64-1EP_9x9mm_P0.5mm_EP4.7x4.7mm",
    )

    # --- Supplies -----------------------------------------------------
    # VDD 7, 10, 18, 63 (net_plan §3.6). The symbol gives all four the name
    # "VDD", so one connection by name binds every one of them.
    u7["VDD"] += v3v0_avdd
    # GND 17, 64 and 65 (exposed pad) all carry the name "GND".
    u7["GND"] += gnd
    # OGND 31, 50 — output-driver ground, same netlist net.
    u7["OGND"] += gnd

    # OVDD via ferrite: V3V3_D -> L8 -> ovdd3V3 -> OVDD 32, 49.
    ovdd3V3 = Net("ovdd3V3")
    ovdd3V3.drive = POWER      # a supply rail behind L8, not a signal
    l8 = Part("Device", "FerriteBead", ref="L8", value="600R@100MHz",
              footprint="Inductor_SMD:L_0603_1608Metric")
    l8[1] += v3v3_d
    l8[2] += ovdd3V3
    u7["OVDD"] += ovdd3V3

    # 0.1 uF at EACH VDD pin (datasheet: "Bypass to GND with 0.1 uF ceramic
    # chip capacitors") plus one 10 uF bulk.
    for ref, val, fp in (
        ("C60", "100nF", "Capacitor_SMD:C_0402_1005Metric"),
        ("C61", "100nF", "Capacitor_SMD:C_0402_1005Metric"),
        ("C62", "100nF", "Capacitor_SMD:C_0402_1005Metric"),
        ("C63", "100nF", "Capacitor_SMD:C_0402_1005Metric"),
        ("C64", "10uF", "Capacitor_SMD:C_0805_2012Metric"),
    ):
        c = Part("Device", "C", ref=ref, value=val, footprint=fp)
        c[1] += v3v0_avdd
        c[2] += gnd

    # 0.1 uF at each OVDD pin + 10 uF bulk, all on the post-ferrite node.
    for ref, val, fp in (
        ("C65", "100nF", "Capacitor_SMD:C_0402_1005Metric"),
        ("C66", "100nF", "Capacitor_SMD:C_0402_1005Metric"),
        ("C67", "10uF", "Capacitor_SMD:C_0805_2012Metric"),
    ):
        c = Part("Device", "C", ref=ref, value=val, footprint=fp)
        c[1] += ovdd3V3
        c[2] += gnd

    # --- Analog inputs ------------------------------------------------
    u7["AINA+"] += ain_ap
    u7["AINA-"] += ain_an
    u7["AINB+"] += ain_bp
    u7["AINB-"] += ain_bn

    # --- Reference programming ---------------------------------------
    # SENSEA 62 / SENSEB 19 both driven from the external 1.000 V reference.
    # Datasheet: "An external reference greater than 0.5 V and less than 1 V
    # applied to SENSE selects an input range of +/-V_SENSE", and "For the best
    # channel matching, connect an external reference to SENSEA and SENSEB."
    u7["SENSEA"] += vref_1v0
    u7["SENSEB"] += vref_1v0

    # 1 uF from each SENSE pin to GND, as close to the device as possible —
    # the datasheet's explicit requirement for an externally driven SENSE.
    c68 = Part("Device", "C", ref="C68", value="1uF",
               footprint="Capacitor_SMD:C_0603_1608Metric")
    c68[1] += vref_1v0
    c68[2] += gnd
    c69 = Part("Device", "C", ref="C69", value="1uF",
               footprint="Capacitor_SMD:C_0603_1608Metric")
    c69[1] += vref_1v0
    c69[2] += gnd

    # --- Internal reference ladder bypassing ---------------------------
    # REFHA 3/4, REFLA 5/6, REFHB 13/14, REFLB 11/12. Each PAIR is one node
    # split across two package pins to halve bond-wire inductance — not two
    # separate nodes — so each pair is shorted onto a single internal net.
    refhA = Net("refhA")
    reflA = Net("reflA")
    refhB = Net("refhB")
    reflB = Net("reflB")
    u7["REFHA"] += refhA
    u7["REFLA"] += reflA
    u7["REFHB"] += refhB
    u7["REFLB"] += reflB

    # Channel A ladder: 0.1 uF + 2.2 uF differentially, 1 uF from each to GND.
    # The 0.1 uF must sit hard against the pins.
    c50 = Part("Device", "C", ref="C50", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c50[1] += refhA
    c50[2] += reflA
    c51 = Part("Device", "C", ref="C51", value="2.2uF",
               footprint="Capacitor_SMD:C_0603_1608Metric")
    c51[1] += refhA
    c51[2] += reflA
    c52 = Part("Device", "C", ref="C52", value="1uF",
               footprint="Capacitor_SMD:C_0603_1608Metric")
    c52[1] += refhA
    c52[2] += gnd
    c53 = Part("Device", "C", ref="C53", value="1uF",
               footprint="Capacitor_SMD:C_0603_1608Metric")
    c53[1] += reflA
    c53[2] += gnd

    # Channel B ladder — identical.
    c54 = Part("Device", "C", ref="C54", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c54[1] += refhB
    c54[2] += reflB
    c55 = Part("Device", "C", ref="C55", value="2.2uF",
               footprint="Capacitor_SMD:C_0603_1608Metric")
    c55[1] += refhB
    c55[2] += reflB
    c56 = Part("Device", "C", ref="C56", value="1uF",
               footprint="Capacitor_SMD:C_0603_1608Metric")
    c56[1] += refhB
    c56[2] += gnd
    c57 = Part("Device", "C", ref="C57", value="1uF",
               footprint="Capacitor_SMD:C_0603_1608Metric")
    c57[1] += reflB
    c57[2] += gnd

    # --- Common-mode outputs (SEPARATE NETS — see docstring point 2) ----
    u7["VCMA"] += adc_vcm_a
    u7["VCMB"] += adc_vcm_b
    c58 = Part("Device", "C", ref="C58", value="2.2uF",
               footprint="Capacitor_SMD:C_0603_1608Metric")
    c58[1] += adc_vcm_a
    c58[2] += gnd
    c59 = Part("Device", "C", ref="C59", value="2.2uF",
               footprint="Capacitor_SMD:C_0603_1608Metric")
    c59[1] += adc_vcm_b
    c59[2] += gnd

    # --- Encode clock --------------------------------------------------
    # CLKA 8 and CLKB 9 on the same net. Datasheet: "It is recommended that
    # CLKA and CLKB are shorted together"; skew must be < 1 ns, which tying
    # adjacent package pins satisfies trivially. "The input sample starts on
    # the positive edge."
    u7["CLKA"] += enc_clk40
    u7["CLKB"] += enc_clk40

    # --- MODE strap: 1/3 V_DD (see docstring point 3) --------------------
    # R46 20 k from V3V0_AVDD, R47 10 k to GND => V_MODE = 3.00 * 10/30 = 1.00 V
    # = 1/3 V_DD exactly. I_MODE leakage is +/-3 uA across the 6.67 k Thevenin
    # = +/-20 mV, well inside the 1/3 V_DD window.
    mode_bias = Net("modeBias")
    r46 = Part("Device", "R", ref="R46", value="20k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r46[1] += v3v0_avdd
    r46[2] += mode_bias
    r47 = Part("Device", "R", ref="R47", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r47[1] += mode_bias
    r47[2] += gnd
    u7["MODE"] += mode_bias

    # --- MUX strap: HIGH -------------------------------------------------
    # Datasheet: "If MUX is High, Channel A comes out on DA0-DA11, OFA;
    # Channel B comes out on DB0-DB11, OFB. If MUX is Low, the output busses
    # are swapped." HIGH gives the natural A->DA mapping these net names
    # assume. Both states are non-multiplexed — MUX only swaps the buses.
    u7["MUX"] += v3v0_avdd

    # --- Output damping arrays -------------------------------------------
    # RN1-RN3 (channel A) and RN4-RN6 (channel B): 4-element 33 R arrays, one
    # element per data line. Device:R_Pack04 numbers element i as pins
    # i and 9-i (1<->8, 2<->7, 3<->6, 4<->5).
    #
    # The datasheet notes the output buffers already contain an internal
    # series resistor that "makes the output appear as 50 R to external
    # circuitry and may eliminate the need for external damping resistors".
    # These arrays are kept anyway as an EMI/SI measure: 33 R + 50 R into the
    # iCE40's 6 pF is tau ~ 0.5 ns against a 21 ns window, so they cost
    # nothing, and they cap dI/dt on 26 simultaneously switching lines. The
    # §1.4.1 timing margins are computed WITHOUT crediting them.
    def _damp_bus(arr_refs, adc_pin_names, out_bus):
        """Wire 12 ADC output pins through three 4-element 33 R arrays."""
        for idx, (arr_ref, base) in enumerate(zip(arr_refs, (0, 4, 8))):
            rn = Part("Device", "R_Pack04", ref=arr_ref, value="33R",
                      footprint="Resistor_SMD:R_Array_Convex_4x0603")
            for elem in range(4):
                line = base + elem
                rn[elem + 1] += u7[adc_pin_names[line]]   # ADC side
                rn[8 - elem] += out_bus[line]             # FPGA side

    _damp_bus(("RN1", "RN2", "RN3"),
              ["DA%d" % i for i in range(12)], adc_data_a)
    _damp_bus(("RN4", "RN5", "RN6"),
              ["DB%d" % i for i in range(12)], adc_data_b)

    # OFA 57 / OFB 40 — discrete 33 R each. The 24 data lines consume
    # RN1-RN6 exactly, leaving no array element for the two flags.
    of_a_int = Net("ofAInt")
    of_b_int = Net("ofBInt")
    u7["OFA"] += of_a_int
    u7["OFB"] += of_b_int
    r44 = Part("Device", "R", ref="R44", value="33R",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r44[1] += of_a_int
    r44[2] += adc_of_a
    r45 = Part("Device", "R", ref="R45", value="33R",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r45[1] += of_b_int
    r45[2] += adc_of_b

    # --- Control pins, both per-channel, tied and pulled DOWN ------------
    # SHDN = GND with OE = GND is normal operation with outputs enabled, so
    # the pull-downs make the ADC convert and drive even before the FPGA is
    # configured. Neither pin is prohibited from being tied across channels.
    u7["SHDNA"] += adc_shdn
    u7["SHDNB"] += adc_shdn
    r48 = Part("Device", "R", ref="R48", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r48[1] += adc_shdn
    r48[2] += gnd

    u7["~{OEA}"] += adc_oe_bar
    u7["~{OEB}"] += adc_oe_bar
    r49 = Part("Device", "R", ref="R49", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r49[1] += adc_oe_bar
    r49[2] += gnd

    # --- No-connects ------------------------------------------------------
    # Pins 24, 25, 41, 42: "Do Not Connect These Pins".
    for pin_num in (24, 25, 41, 42):
        u7[pin_num] += NC
