"""
Dual-channel 12-bit, 10 MS/s, +/-10 V ADC board with USB 2.0 interface.

Signal chain per channel:
    BNC (1 Mohm || ~20 pF, scope-probe compatible)
    -> compensated 909k/100k attenuator biased to VBIAS (2.048 V ref)
    -> OPA356 unity-gain buffer
    -> THS4521 fully-differential amp (gain 1, VOCM from ADC) referenced
       to a matched, buffered copy of the attenuator's rest voltage
    -> RC kickback / anti-alias filter
    -> LTC2290 dual 12-bit 10 MS/s ADC.

Digital: iCE40HX4K-TQ144 FPGA captures both ADC buses into an 8 MB SDR SDRAM
(IS42S16400J, 0.2 s of 2-ch samples) and streams it to the host through an
FT232H in FT245 synchronous-FIFO mode (USB 2.0 high-speed).

Power: USB VBUS (5 V) -> TPS62160 buck 3.3 V (digital), AP2112 1.2 V (FPGA core),
LP5907 4.5 V (analog front end), LP5907 3.0 V (ADC + sample clock).

Run with:  python3 dual_adc.py
"""

import os
import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning)

from skidl import *

set_default_tool(KICAD10)
KICAD10_ROOT = "/home/devb/bin/kicad10-root/share/kicad"
lib_search_paths[KICAD10] = [KICAD10_ROOT + "/symbols"]
footprint_search_paths[KICAD10] = [KICAD10_ROOT + "/footprints"]

# ---------------------------------------------------------------------------
# Footprints for passives.
# ---------------------------------------------------------------------------
FP_R0402 = "Resistor_SMD:R_0402_1005Metric"
FP_R0603 = "Resistor_SMD:R_0603_1608Metric"
FP_R1206 = "Resistor_SMD:R_1206_3216Metric"
FP_C0402 = "Capacitor_SMD:C_0402_1005Metric"
FP_C0603 = "Capacitor_SMD:C_0603_1608Metric"
FP_C0805 = "Capacitor_SMD:C_0805_2012Metric"
FP_RPACK = "Resistor_SMD:R_Array_Convex_4x0603"
FP_LED = "LED_SMD:LED_0603_1608Metric"
FP_FB = "Inductor_SMD:L_0603_1608Metric"


def _part(name, value, fp, spec):
    p = Part("Device", name, value=value, footprint=fp)
    if spec:
        p.fields["Spec"] = spec  # tolerance / dielectric / voltage, for the BOM
    return p


def R(value, fp=FP_R0603, tolerance=None):
    return _part("R", value, fp, tolerance)


def C(value, fp=FP_C0603, tolerance=None):
    return _part("C", value, fp, tolerance)


def decouple(pwr, gnd, *values):
    """Place one capacitor per value between pwr and gnd."""
    for v in values:
        fp = FP_C0805 if v in ("10uF", "22uF", "4.7uF") else FP_C0603
        if v in ("100nF",):
            fp = FP_C0402
        c = C(v, fp=fp)
        c[1] += pwr
        c[2] += gnd


# ---------------------------------------------------------------------------
# Global supply nets.
# ---------------------------------------------------------------------------
gnd = Net("GND")
vbus = Net("VBUS")  # raw from connector (after polyfuse)
p5v = Net("+5V")  # filtered VBUS
p3v3 = Net("+3V3")  # digital 3.3 V (buck)
p1v2 = Net("+1V2")  # FPGA core
a4v5 = Net("+4V5A")  # analog front end
a3v0 = Net("+3V0A")  # ADC VDD and sample clock
for n in (gnd, vbus, p5v, p3v3, p1v2, a4v5, a3v0):
    n.drive = POWER

vbias = Net("VBIAS")  # 2.048 V attenuator bias reference


# ---------------------------------------------------------------------------
# USB connector, protection and power input.
# ---------------------------------------------------------------------------
@subcircuit
def usb_input(dp, dm):
    j = Part("Connector", "USB_B", ref="J3",
             footprint="Connector_USB:USB_B_OST_USB-B1HSxx_Horizontal")
    vconn = Net("VBUS_CONN")
    j["VBUS"] += vconn
    j["GND"] += gnd
    j["D+"] += dp
    j["D-"] += dm

    # Shield to ground through 1M || 4.7nF.
    shield = Net("USB_SHIELD")
    j["Shield"] += shield
    r = R("1M")
    c = C("4.7nF")
    r[1, 2] += shield, gnd
    c[1, 2] += shield, gnd

    # 500 mA polyfuse, then ferrite to the board 5 V rail.
    f = Part("Device", "Polyfuse", value="500mA", footprint="Fuse:Fuse_1206_3216Metric")
    f[1, 2] += vconn, vbus
    fb = Part("Device", "FerriteBead", value="600R@100MHz",
              footprint="Inductor_SMD:L_0805_2012Metric")
    fb[1, 2] += vbus, p5v

    esd = Part("Power_Protection", "USBLC6-2SC6",
               footprint="Package_TO_SOT_SMD:SOT-23-6")
    esd["GND"] += gnd
    esd["VBUS"] += vbus
    esd[1] += dp
    esd[6] += dp
    esd[3] += dm
    esd[4] += dm

    # Total capacitance seen by VBUS kept near the USB 2.0 10 uF limit.
    decouple(p5v, gnd, "2.2uF")


# ---------------------------------------------------------------------------
# Regulators.
# ---------------------------------------------------------------------------
@subcircuit
def power():
    # 5 V -> 3.3 V buck, 1 A.  Vout = 0.8 * (1 + 316k/100k) = 3.33 V.
    u = Part("Regulator_Switching", "TPS62160DSG")
    sw = Net("BUCK_SW")
    fbn = Net("BUCK_FB")
    u["VIN"] += p5v
    u["EN"] += p5v
    u["PGND", "AGND", "PAD"] += gnd
    u["SW"] += sw
    u["VOS"] += p3v3
    u["FB"] += fbn
    u["PG"] += NC
    l = Part("Device", "L", value="2.2uH",
             footprint="Inductor_SMD:L_Changjiang_FNR3015S")
    l[1, 2] += sw, p3v3
    r1 = R("316k")
    r2 = R("100k")
    r1[1, 2] += p3v3, fbn
    r2[1, 2] += fbn, gnd
    decouple(p5v, gnd, "4.7uF")
    decouple(p3v3, gnd, "22uF")

    # 3.3 V -> 1.2 V LDO for FPGA core.
    u = Part("Regulator_Linear", "AP2112K-1.2")
    u["VIN", "EN"] += p3v3
    u["GND"] += gnd
    u["VOUT"] += p1v2
    u["NC"] += NC
    decouple(p3v3, gnd, "1uF")
    decouple(p1v2, gnd, "1uF")

    # 5 V -> 4.5 V low-noise LDO for the analog front end.
    u = Part("Regulator_Linear", "LP5907MFX-4.5")
    u["IN", "EN"] += p5v
    u["GND"] += gnd
    u["OUT"] += a4v5
    u["NC"] += NC
    decouple(p5v, gnd, "1uF")
    decouple(a4v5, gnd, "1uF", "10uF")

    # 5 V -> 3.0 V low-noise LDO for ADC analog supply and sample clock.
    u = Part("Regulator_Linear", "LP5907MFX-3.0")
    u["IN", "EN"] += p5v
    u["GND"] += gnd
    u["OUT"] += a3v0
    u["NC"] += NC
    decouple(p5v, gnd, "1uF")
    decouple(a3v0, gnd, "1uF", "10uF")

    # 2.048 V reference for the attenuator bias.
    u = Part("Reference_Voltage", "REF3020")
    u["IN"] += a4v5
    u["GND"] += gnd
    u["OUT"] += vbias
    decouple(a4v5, gnd, "100nF")
    decouple(vbias, gnd, "100nF")

    # Power-good LED on 3.3 V.
    led = Part("Device", "LED", value="GRN", footprint=FP_LED)
    r = R("1k")
    r[1, 2] += p3v3, led["A"]
    led["K"] += gnd


# ---------------------------------------------------------------------------
# Analog front end (one channel).
# ---------------------------------------------------------------------------
@subcircuit
def front_end(ch, ain_p, ain_n, vocm, clamp):
    """ch: 'A' or 'B'.  clamp: (anode, cathode, mid) pins of a BAV199 half."""
    vin = Net(f"IN_{ch}")
    node = Net(f"ATT_{ch}")
    buf = Net(f"BUF_{ch}")
    rest_div = Net(f"REST_DIV_{ch}")
    rest = Net(f"REST_{ch}")
    fda_inp = Net(f"FDA_INP_{ch}")
    fda_inn = Net(f"FDA_INN_{ch}")
    fda_outp = Net(f"FDA_OUTP_{ch}")
    fda_outn = Net(f"FDA_OUTN_{ch}")

    # BNC input (mates with standard scope probes / BNC leads).
    j = Part("Connector", "Conn_Coaxial", ref="J1" if ch == "A" else "J2",
             value=f"BNC CH{ch}",
             footprint="Connector_Coaxial:BNC_Amphenol_B6252HB-NPP3G-50_Horizontal")
    j["In"] += vin
    j["Ext"] += gnd

    # Input capacitance to look like a normal 1 Mohm || ~20 pF scope input.
    C("15pF", fp=FP_C0805, tolerance="C0G 100V")[1, 2] += vin, gnd

    # Compensated 1 Mohm attenuator: gain = 100k / 1009k = 0.0991.
    R("909k", fp=FP_R1206, tolerance="0.1%, 200V")[1, 2] += vin, node
    C("2.4pF", fp=FP_C0805, tolerance="C0G 100V")[1, 2] += vin, node
    R("100k", tolerance="0.1%")[1, 2] += node, vbias
    C("18pF", tolerance="C0G")[1, 2] += node, gnd

    # Over-voltage clamp of the attenuator node to the analog rails.
    a, k, m = clamp
    a += gnd
    k += a4v5
    m += node

    # Signal buffer.
    u = Part("Amplifier_Operational", "OPA356xxDBV")
    u["+"] += node
    u["-"] += buf
    u[1] += buf
    u["V+"] += a4v5
    u["V-"] += gnd
    decouple(a4v5, gnd, "100nF")

    # Matched copy of the attenuator's rest voltage: VBIAS * 909/1009.
    R("10k", tolerance="0.1%")[1, 2] += vbias, rest_div
    R("90.9k", tolerance="0.1%")[1, 2] += rest_div, gnd
    C("100nF")[1, 2] += rest_div, gnd
    u = Part("Amplifier_Operational", "OPA356xxDBV")
    u["+"] += rest_div
    u["-"] += rest
    u[1] += rest
    u["V+"] += a4v5
    u["V-"] += gnd
    decouple(a4v5, gnd, "100nF")

    # Fully-differential driver, gain = Rf/Rg = 1.
    # VOD = OUT+ - OUT- = BUF - REST = 0.0991 * Vin.  Rf*Cf pole = 4.8 MHz.
    u = Part("Amplifier_Difference", "THS4521ID",
             footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm")
    u["+"] += fda_inp
    u["-"] += fda_inn
    u[4] += fda_outp  # VOUT+
    u[5] += fda_outn  # VOUT-
    u["V_{OCM}"] += vocm
    u["V_{S+}"] += a4v5
    u["V_{S-}"] += gnd
    u["~{PD}"] += a4v5
    decouple(a4v5, gnd, "100nF", "2.2uF")

    R("1k", tolerance="0.1%")[1, 2] += buf, fda_inp  # Rg+
    R("1k", tolerance="0.1%")[1, 2] += fda_inp, fda_outn  # Rf+
    C("33pF", tolerance="C0G")[1, 2] += fda_inp, fda_outn
    R("1k", tolerance="0.1%")[1, 2] += rest, fda_inn  # Rg-
    R("1k", tolerance="0.1%")[1, 2] += fda_inn, fda_outp  # Rf-
    C("33pF", tolerance="C0G")[1, 2] += fda_inn, fda_outp

    # ADC kick-back / anti-alias RC: 2 x 49.9 ohm, 150 pF diff -> 10.6 MHz.
    R("49.9")[1, 2] += fda_outp, ain_p
    R("49.9")[1, 2] += fda_outn, ain_n
    C("150pF", tolerance="C0G")[1, 2] += ain_p, ain_n


# ---------------------------------------------------------------------------
# Sample clock: 10 MHz XO -> dual buffer -> ADC and FPGA.
# ---------------------------------------------------------------------------
@subcircuit
def sample_clock(adc_clk, fpga_clk):
    xo = Part("Oscillator", "ASE-xxxMHz", value="ASE-10.000MHz")
    osc = Net("OSC_10M")
    xo["Vdd", "EN"] += a3v0
    xo["GND"] += gnd
    xo["OUT"] += osc
    decouple(a3v0, gnd, "100nF")

    buf = Part("74xGxx", "74LVC2G34", footprint="Package_TO_SOT_SMD:SOT-363_SC-70-6")
    buf["VCC"] += a3v0
    buf["GND"] += gnd
    buf[1] += osc
    buf[3] += osc
    o1, o2 = Net("CLK_ADC_SRC"), Net("CLK_FPGA_SRC")
    buf[6] += o1
    buf[4] += o2
    decouple(a3v0, gnd, "100nF")
    R("33")[1, 2] += o1, adc_clk
    R("33")[1, 2] += o2, fpga_clk


# ---------------------------------------------------------------------------
# Dual ADC.
# ---------------------------------------------------------------------------
@subcircuit
def adc(ain, vcm, clk, da, ofa, db, ofb, shdn):
    u = Part("Analog_ADC", "LTC2292xUP", value="LTC2290CUP")
    u["AINA+"] += ain["A"][0]
    u["AINA-"] += ain["A"][1]
    u["AINB+"] += ain["B"][0]
    u["AINB-"] += ain["B"][1]
    u["VCMA"] += vcm["A"]
    u["VCMB"] += vcm["B"]
    decouple(vcm["A"], gnd, "2.2uF")
    decouple(vcm["B"], gnd, "2.2uF")

    # References: 0.1uF + 2.2uF REFH-REFL, 1uF each to ground.
    for ch in "AB":
        refh, refl = Net(f"REFH{ch}"), Net(f"REFL{ch}")
        u[f"REFH{ch}"] += refh
        u[f"REFL{ch}"] += refl
        decouple(refh, refl, "100nF", "2.2uF")
        decouple(refh, gnd, "1uF")
        decouple(refl, gnd, "1uF")

    u["CLKA", "CLKB"] += clk
    u["SENSEA", "SENSEB"] += a3v0  # internal ref, 2 Vpp differential range
    u["MUX"] += a3v0  # channel A on DA bus, B on DB bus
    u["MODE"] += gnd  # offset binary, clock duty-cycle stabilizer off
    u["SHDNA", "SHDNB"] += shdn
    u["~{OEA}", "~{OEB}"] += gnd
    u["VDD"] += a3v0
    u["GND"] += gnd
    u["OGND"] += gnd
    u["OVDD"] += p3v3
    u["NC"] += NC
    decouple(a3v0, gnd, "100nF", "100nF", "100nF", "100nF", "10uF")
    decouple(p3v3, gnd, "100nF", "100nF")
    R("10k")[1, 2] += shdn, gnd  # ADC runs unless FPGA asserts SHDN.

    # Data outputs to FPGA through 33-ohm series packs (reduces digital
    # feedback into the ADC).
    for i in range(12):
        u[f"DA{i}"] += da[i]
        u[f"DB{i}"] += db[i]
    u["OFA"] += ofa
    u["OFB"] += ofb


# ---------------------------------------------------------------------------
# SDRAM.
# ---------------------------------------------------------------------------
@subcircuit
def sdram(sd):
    u = Part("Memory_RAM", "IS42S16400J-xT", value="IS42S16400J-7TL")
    for i in range(12):
        u[f"A{i}"] += sd[f"A{i}"]
    for i in range(16):
        u[f"DQ{i}"] += sd[f"DQ{i}"]
    for s in ("BA0", "BA1", "LDQM", "UDQM", "CKE", "CLK"):
        u[s] += sd[s]
    u["~{WE}"] += sd["WE_N"]
    u["~{CAS}"] += sd["CAS_N"]
    u["~{RAS}"] += sd["RAS_N"]
    u["~{CS}"] += sd["CS_N"]
    u["VDD", "VDDQ"] += p3v3
    u["GND", "GNDQ"] += gnd
    u["NC"] += NC
    decouple(p3v3, gnd, *(["100nF"] * 7 + ["10uF"]))


# ---------------------------------------------------------------------------
# USB 2.0 HS bridge: FT232H in FT245 synchronous FIFO mode.
# ---------------------------------------------------------------------------
@subcircuit
def usb_bridge(dp, dm, fifo):
    u = Part("Interface_USB", "FT232H", value="FT232HL",
             footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm")
    u["DP"] += dp
    u["DM"] += dm
    for i in range(8):
        u[f"ADBUS{i}"] += fifo[f"D{i}"]
    # FT245 sync FIFO pin functions on ACBUS.
    u["ACBUS0"] += fifo["RXF_N"]
    u["ACBUS1"] += fifo["TXE_N"]
    u["ACBUS2"] += fifo["RD_N"]
    u["ACBUS3"] += fifo["WR_N"]
    u["ACBUS4"] += fifo["SIWU_N"]
    u["ACBUS5"] += fifo["CLKOUT"]
    u["ACBUS6"] += fifo["OE_N"]
    u["ACBUS8"] += fifo["GPIO8"]
    u["ACBUS9"] += fifo["GPIO9"]
    pwrsav = Net("FT_PWRSAV_N")
    u["ACBUS7"] += pwrsav
    R("10k")[1, 2] += pwrsav, p3v3

    # Power: VREGIN = 3.3 V, so VCCD is a 3.3 V input; VCCA/VCCCORE are the
    # internal 1.8 V regulator outputs.
    u["VREGIN", "VCCD", "VCCIO", "VPHY", "VPLL"] += p3v3
    u["GND", "AGND"] += gnd
    vcca, vccore = Net("FT_VCCA"), Net("FT_VCCCORE")
    u["VCCA"] += vcca
    u["VCCCORE"] += vccore
    decouple(vcca, gnd, "100nF", "4.7uF")
    decouple(vccore, gnd, "100nF", "4.7uF")
    decouple(p3v3, gnd, "100nF", "100nF", "100nF", "100nF", "100nF", "4.7uF")

    u["TEST"] += gnd
    rst = Net("FT_RESET_N")
    u["~{RESET}"] += rst
    R("10k")[1, 2] += rst, p3v3
    ref = Net("FT_REF")
    u["REF"] += ref
    R("12k", tolerance="1%")[1, 2] += ref, gnd

    # 12 MHz crystal.
    x = Part("Device", "Crystal_GND24", value="12MHz",
             footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm")
    xi, xo = Net("FT_XI"), Net("FT_XO")
    u["XCSI"] += xi
    u["XCSO"] += xo
    x[1] += xi
    x[3] += xo
    x["G"] += gnd
    C("18pF", fp=FP_C0402)[1, 2] += xi, gnd
    C("18pF", fp=FP_C0402)[1, 2] += xo, gnd

    # Configuration EEPROM (sets FT245 FIFO mode, descriptors).
    e = Part("Memory_EEPROM", "93LCxxB", value="93LC56B",
             footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm")
    eecs, eeclk, eedata, eedo = (Net("FT_EECS"), Net("FT_EECLK"),
                                 Net("FT_EEDATA"), Net("FT_EEDO"))
    u["EECS"] += eecs
    u["EECLK"] += eeclk
    u["EEDATA"] += eedata
    e["CS"] += eecs
    e["SCLK"] += eeclk
    e["DI"] += eedata
    e["DO"] += eedo
    R("2.2k")[1, 2] += eedo, eedata
    e["VCC"] += p3v3
    e["GND"] += gnd
    e["NC"] += NC
    for n in (eecs, eeclk, eedata):
        R("10k")[1, 2] += n, p3v3
    decouple(p3v3, gnd, "100nF")


# ---------------------------------------------------------------------------
# FPGA + configuration flash.
# ---------------------------------------------------------------------------
# Pin maps (TQ144). Banks: 0 = top (IOT), 1 = right (IOR), 2 = bottom (IOB),
# 3 = left (IOL). All banks run at 3.3 V.
ADC_PINS = [1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 15, 16, 17,  # OFA, DA11..DA0
            18, 19, 20, 21, 22, 23, 24, 25, 26, 28, 29, 31, 32]  # DB11..DB0, OFB
SDRAM_SIGS = (["DQ0", "DQ1", "DQ2", "DQ3", "DQ4", "DQ5", "DQ6", "DQ7", "LDQM",
               "WE_N", "CAS_N", "RAS_N", "CS_N", "BA0", "BA1", "A10", "A0", "A1",
               "A2", "A3"] +
              ["A4", "A5", "A6", "A7", "A8", "A9", "A11", "CKE", "CLK", "UDQM",
               "DQ8", "DQ9", "DQ10", "DQ11", "DQ12", "DQ13", "DQ14", "DQ15"])
SDRAM_PINS = [144, 143, 142, 141, 139, 138, 137, 136, 135, 134, 130, 129, 128,
              125, 124, 122, 121, 120, 119, 118,
              117, 116, 115, 114, 113, 112, 110, 107, 106, 105, 104, 102, 101,
              99, 98, 97, 96, 95]
FIFO_PINS = {"D0": 73, "D1": 74, "D2": 75, "D3": 76, "D4": 78, "D5": 79,
             "D6": 80, "D7": 81, "RXF_N": 82, "TXE_N": 83, "RD_N": 84,
             "WR_N": 85, "SIWU_N": 87, "OE_N": 88, "GPIO8": 90, "GPIO9": 91,
             "CLKOUT": 94}  # CLKOUT on GBIN2
CLK10_PIN = 49  # GBIN5
LED_PINS = [37, 38]
GPIO_PINS = [39, 41, 42, 43]
ADC_SHDN_PIN = 44


@subcircuit
def pll_filters(*vccpll):
    """RC filters (100 ohm, 10 uF + 100 nF) for the iCE40 PLL supplies."""
    for vpll in vccpll:
        R("100")[1, 2] += p1v2, vpll
        decouple(vpll, gnd, "100nF", "10uF")


@subcircuit
def fpga(adc_bus, adc_clk, adc_shdn, sd, fifo, leds, gpio):
    u = Part("FPGA_Lattice", "ICE40HX4K-TQ144", value="ICE40HX4K-TQ144")

    used = set()

    def con(pin, net):
        u[pin] += net
        used.add(pin)

    for pin, net in zip(ADC_PINS, adc_bus):
        con(pin, net)
    for pin, sig in zip(SDRAM_PINS, SDRAM_SIGS):
        con(pin, sd[sig])
    for sig, pin in FIFO_PINS.items():
        con(pin, fifo[sig])
    con(CLK10_PIN, adc_clk)
    con(ADC_SHDN_PIN, adc_shdn)
    for pin, net in zip(LED_PINS, leds):
        con(pin, net)
    for pin, net in zip(GPIO_PINS, gpio):
        con(pin, net)

    # Configuration: SPI master from flash.
    sck, sdo, sdi, ss = (Net("CFG_SCK"), Net("CFG_MOSI"), Net("CFG_MISO"),
                         Net("CFG_SS_N"))
    creset, cdone = Net("CRESET_N"), Net("CDONE")
    con(70, sck)
    con(67, sdo)
    con(68, sdi)
    con(71, ss)
    con(66, creset)
    con(65, cdone)
    R("10k")[1, 2] += creset, p3v3
    R("10k")[1, 2] += cdone, p3v3
    R("10k")[1, 2] += ss, p3v3

    fl = Part("Memory_Flash", "W25Q32JVSS")
    fl["~{CS}"] += ss
    fl["CLK"] += sck
    fl["DI/IO_{0}"] += sdo
    fl["DO/IO_{1}"] += sdi
    fl["~{WP}/IO_{2}", "~{HOLD}/~{RESET}/IO_{3}", "VCC"] += p3v3
    fl["GND"] += gnd
    decouple(p3v3, gnd, "100nF")

    # Programming header (iceprog-compatible signals).
    hdr = Part("Connector_Generic", "Conn_02x04_Odd_Even", ref="J4", value="FPGA_PROG",
               footprint="Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical")
    hdr[1, 2, 3, 4, 5, 6, 7, 8] += ss, sck, sdo, sdi, creset, cdone, p3v3, gnd

    # Power.
    vccpll0, vccpll1 = Net("VCCPLL0"), Net("VCCPLL1")
    vccpll0.drive = vccpll1.drive = POWER
    for p in (27, 40, 92, 111):
        con(p, p1v2)
    for p in (6, 30, 46, 57, 89, 100, 123, 131):
        con(p, p3v3)
    con(72, p3v3)  # VCC_SPI
    con(108, p3v3)  # VPP_2V5 (2.3..3.46 V allowed)
    con(54, vccpll0)
    con(126, vccpll1)
    for p in (5, 13, 14, 59, 69, 86, 103, 132, 140, 53, 127):  # GND, GNDPLL
        con(p, gnd)
    pll_filters(vccpll0, vccpll1)
    pwr_flag(vccpll0, vccpll1)
    decouple(p1v2, gnd, "100nF", "100nF", "100nF", "100nF", "10uF")
    decouple(p3v3, gnd, *(["100nF"] * 10 + ["10uF"]))

    # Everything else is unused.
    for pin in u.pins:
        if int(pin.num) not in used:
            pin += NC


# ---------------------------------------------------------------------------
# Top level.
# ---------------------------------------------------------------------------
def pwr_flag(*nets):
    """Mark rails fed through passives (fuse, inductor, filter R) as driven."""
    for n in nets:
        f = Part("power", "PWR_FLAG", footprint=":")
        f[1] += n


def top():
    dp, dm = Net("USB_DP"), Net("USB_DN")
    usb_input(dp, dm)
    power()
    pwr_flag(vbus, p5v, p3v3)

    ain = {ch: (Net(f"AIN{ch}_P"), Net(f"AIN{ch}_N")) for ch in "AB"}
    vcm = {ch: Net(f"VCM{ch}") for ch in "AB"}
    clamp = Part("Diode", "BAV199DW", value="BAV199DW")
    front_end("A", *ain["A"], vcm["A"], (clamp[1], clamp[2], clamp[3]))
    front_end("B", *ain["B"], vcm["B"], (clamp[4], clamp[5], clamp[6]))

    adc_clk, fpga_clk = Net("CLK_ADC"), Net("CLK_FPGA")
    sample_clock(adc_clk, fpga_clk)

    # ADC data: ADC-side nets and FPGA-side nets joined by 33R packs.
    da = [Net(f"DA{i}") for i in range(12)]
    db = [Net(f"DB{i}") for i in range(12)]
    ofa, ofb = Net("OFA"), Net("OFB")
    shdn = Net("ADC_SHDN")
    adc(ain, vcm, adc_clk, da, ofa, db, ofb, shdn)

    adc_side = [ofa] + da[::-1] + db[::-1] + [ofb]
    fpga_side = [Net("F_" + n.name) for n in adc_side]
    for k in range(0, len(adc_side), 4):
        pack = Part("Device", "R_Pack04", value="33", footprint=FP_RPACK)
        grp = list(zip(adc_side[k:k + 4], fpga_side[k:k + 4]))
        for (a, f), (p1, p2) in zip(grp, [(1, 8), (2, 7), (3, 6), (4, 5)]):
            pack[p1] += a
            pack[p2] += f
        if len(grp) < 4:  # unused resistors in the last pack
            for p1, p2 in [(1, 8), (2, 7), (3, 6), (4, 5)][len(grp):]:
                pack[p1] += NC
                pack[p2] += NC

    sd = {s: Net("SD_" + s) for s in SDRAM_SIGS}
    sdram(sd)

    fifo_sigs = list(FIFO_PINS.keys())
    fifo = {s: Net("FT_" + s) for s in fifo_sigs}
    usb_bridge(dp, dm, fifo)

    leds = [Net("LED_ARM"), Net("LED_TRIG")]
    for n in leds:
        led = Part("Device", "LED", value="YEL", footprint=FP_LED)
        r = R("330")
        r[1, 2] += n, led["A"]
        led["K"] += gnd

    gpio = [Net(f"GPIO{i}") for i in range(4)]
    gpio_h = [Net(f"GPIO{i}_HDR") for i in range(4)]
    hdr = Part("Connector_Generic", "Conn_01x06", ref="J5", value="GPIO/TRIG",
               footprint="Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical")
    hdr[1] += p3v3
    hdr[2, 3, 4, 5] += gpio_h
    hdr[6] += gnd
    for n, h in zip(gpio, gpio_h):  # series protection for off-board signals
        R("100")[1, 2] += n, h
    fpga(fpga_side, fpga_clk, shdn, sd, fifo, leds, gpio)

    # (Mounting holes H1-H4 are added directly in the PCB by make_pcb.py.)


if __name__ == "__main__":
    top()
    ERC()
    generate_netlist(file_="dual_adc.net")
    generate_xml(file_="dual_adc.xml")
    generate_schematic(filepath=".", top_name="dual_adc",
                       title="Dual 12-bit 10 MS/s USB ADC", auto_stub=True)
