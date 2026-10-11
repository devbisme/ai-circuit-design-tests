"""Build the eda-agent DesignPlan (JSON) for the dual-channel USB ADC board.

The plan is the single source of truth for parts and connectivity. The
eda-agent tools (design_validate_plan, kicad_generate_project) consume it, and
so do this project's gap-filling scripts (schematic writer, board builder).

Output: ../plan/dual_adc_plan.json plus ../plan/no_connects.json (pins that are
intentionally unconnected; DesignPlan has no field for them).
"""

import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "plan")

parts = []
nets = defaultdict(list)          # net name -> [(ref, pin)]
no_connects = []                  # [(ref, pin)]
_count = defaultdict(int)

# Footprints / symbols for generic parts.
R_FP = "Resistor_SMD:R_0603_1608Metric"
C_FP = "Capacitor_SMD:C_0603_1608Metric"
C_FP_BULK = "Capacitor_SMD:C_0805_2012Metric"
FB_FP = "Inductor_SMD:L_0603_1608Metric"
LED_FP = "LED_SMD:LED_0603_1608Metric"


def part(prefix, lib_ref, value, footprint, sheet, mpn=None, mfr=None,
         datasheet=None, role=None):
    _count[prefix] += 1
    ref = f"{prefix}{_count[prefix]}"
    parts.append(dict(refdes=ref, lib_ref=lib_ref, value=value,
                      footprint=footprint, sheet=sheet, mpn=mpn,
                      manufacturer=mfr, datasheet_url=datasheet, role=role))
    return ref


def conn(net, *pins):
    for p in pins:
        if p in nets[net]:
            raise ValueError(f"{p} already on {net}")
        nets[net].append(p)


def nc(ref, *pins):
    for p in pins:
        no_connects.append((ref, str(p)))


def R(value, a, b, sheet, fp=R_FP, tol=None):
    r = part("R", "Device:R", value, fp, sheet,
             role=f"tolerance {tol}" if tol else None)
    conn(a, (r, "1"))
    conn(b, (r, "2"))
    return r


def C(value, a, b, sheet, fp=None):
    bulk = any(value.endswith(s) for s in ("10uF", "4.7uF", "2.2uF"))
    c = part("C", "Device:C", value, fp or (C_FP_BULK if bulk else C_FP), sheet)
    conn(a, (c, "1"))
    conn(b, (c, "2"))
    return c


def FB(a, b, sheet, value="600R@100MHz"):
    f = part("FB", "Device:FerriteBead", value, FB_FP, sheet,
             mpn="BLM18AG601SN1D", mfr="Murata")
    conn(a, (f, "1"))
    conn(b, (f, "2"))
    return f


def decouple(rail, n, sheet, value="100nF"):
    for _ in range(n):
        C(value, rail, "GND", sheet)


# ---------------------------------------------------------------- power ----
S = "power"
J_USB = part("J", "Connector:USB_B", "USB_B",
             "Connector_USB:USB_B_OST_USB-B1HSxx_Horizontal", "usb",
             mpn="USB-B1HSW6", mfr="On Shore Technology")
F1 = part("F", "Device:Polyfuse", "750mA", "Fuse:Fuse_1206_3216Metric", S,
          mpn="0ZCJ0050AF2E", mfr="Bel Fuse")
conn("VBUS", (J_USB, "1"), (F1, "1"))
conn("VBUS_F", (F1, "2"))
FB("VBUS_F", "+5V", S, value="120R@100MHz 2A")
C("4.7uF", "+5V", "GND", S)

# +3V3 digital: AP2112K-3.3
U = part("U", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3",
         "Package_TO_SOT_SMD:SOT-23-5", S, mpn="AP2112K-3.3TRG1", mfr="Diodes Inc")
conn("+5V", (U, "1"), (U, "3"))
conn("GND", (U, "2"))
nc(U, 4)
conn("+3V3", (U, "5"))
C("1uF", "+5V", "GND", S)
C("10uF", "+3V3", "GND", S)

# +1V2 FPGA core: AP2112K-1.2 from +3V3
U = part("U", "Regulator_Linear:AP2112K-1.2", "AP2112K-1.2",
         "Package_TO_SOT_SMD:SOT-23-5", S, mpn="AP2112K-1.2TRG1", mfr="Diodes Inc")
conn("+3V3", (U, "1"), (U, "3"))
conn("GND", (U, "2"))
nc(U, 4)
conn("+1V2", (U, "5"))
C("1uF", "+3V3", "GND", S)
C("10uF", "+1V2", "GND", S)

# +3V3A analog: LP5907-3.3 from +5V
U = part("U", "Regulator_Linear:LP5907MFX-3.3", "LP5907MFX-3.3",
         "Package_TO_SOT_SMD:SOT-23-5", S, mpn="LP5907MFX-3.3/NOPB", mfr="Texas Instruments")
conn("+5V", (U, "1"), (U, "3"))
conn("GND", (U, "2"))
nc(U, 4)
conn("+3V3A", (U, "5"))
C("1uF", "+5V", "GND", S)
C("1uF", "+3V3A", "GND", S)
C("10uF", "+3V3A", "GND", S)

# +/-4V for the input buffers: LM27762 (SNVSAF7C eq. 1 and 3)
U = part("U", "Regulator_SwitchedCapacitor:LM27762", "LM27762",
         "Package_SON:WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65", S,
         mpn="LM27762DSSR", mfr="Texas Instruments")
conn("LM_PGOOD_N", (U, "1"))                # open drain, monitored by the FPGA
R("10k", "+3V3", "LM_PGOOD_N", S)
conn("LM_FBP", (U, "2"))
conn("+5V", (U, "3"), (U, "8"), (U, "12"))  # VIN, EN-, EN+
conn("GND", (U, "4"), (U, "13"))
conn("LM_CP", (U, "5"))
conn("-4V", (U, "6"))
conn("LM_FBN", (U, "7"))
conn("LM_CN", (U, "9"))
conn("LM_CPF", (U, "10"))
conn("+4V", (U, "11"))
C("2.2uF", "+5V", "GND", S)
C("1uF", "LM_CPF", "LM_CN", S, fp="Capacitor_SMD:C_0402_1005Metric")  # flying cap, tight to pins 9/10
C("4.7uF", "LM_CP", "GND", S)
C("2.2uF", "+4V", "GND", S)
C("2.2uF", "-4V", "GND", S)
R("232k", "+4V", "LM_FBP", S)     # R1: 1.2*(232+100)/100 = 3.98 V
R("100k", "LM_FBP", "GND", S)     # R2
R("226k", "-4V", "LM_FBN", S)     # R3: -1.22*(226+100)/100 = -3.98 V
R("100k", "LM_FBN", "GND", S)     # R4

# Power-on LED
D = part("D", "Device:LED", "Green", LED_FP, S)
R("1k", "+3V3", "LED_PWR", S)
conn("LED_PWR", (D, "2"))
conn("GND", (D, "1"))

# Mounting holes (no electrical connection)
for _ in range(4):
    part("H", "Mechanical:MountingHole", "MountingHole",
         "MountingHole:MountingHole_3.2mm_M3", S)

# ------------------------------------------------------------------ usb ----
S = "usb"
conn("USB_DM", (J_USB, "2"))
conn("USB_DP", (J_USB, "3"))
conn("GND", (J_USB, "4"))
conn("USB_SHIELD", (J_USB, "SH"))
R("1M", "USB_SHIELD", "GND", S)
C("4.7nF", "USB_SHIELD", "GND", S)

U_ESD = part("U", "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6",
             "Package_TO_SOT_SMD:SOT-23-6", S, mpn="USBLC6-2SC6", mfr="STMicroelectronics")
conn("USB_DM", (U_ESD, "1"), (U_ESD, "6"))
conn("GND", (U_ESD, "2"))
conn("USB_DP", (U_ESD, "3"), (U_ESD, "4"))
conn("VBUS_F", (U_ESD, "5"))
C("100nF", "VBUS_F", "GND", S)

U_FT = part("U", "Interface_USB:FT232H", "FT232HL",
            "Package_QFP:LQFP-48_7x7mm_P0.5mm", S, mpn="FT232HL-REEL", mfr="FTDI")
Y = part("Y", "Device:Crystal_GND24", "12MHz",
         "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", S,
         mpn="ABM8-12.000MHZ-B2-T", mfr="Abracon")
conn("FT_XI", (U_FT, "1"), (Y, "1"))
conn("FT_XO", (U_FT, "2"), (Y, "3"))
conn("GND", (Y, "2"), (Y, "4"))
C("27pF", "FT_XI", "GND", S)
C("27pF", "FT_XO", "GND", S)
# Supplies. TODO(verify vs DS_FT232H): VREGIN and VCCD both on +3V3 (3.3 V-only
# supply option); VCCA/VCCCORE are internal 1.8 V outputs that only get decoupling.
FB("+3V3", "FT_VPHY", S)
conn("FT_VPHY", (U_FT, "3"), (U_FT, "8"))
C("4.7uF", "FT_VPHY", "GND", S)
decouple("FT_VPHY", 2, S)
conn("GND", *[(U_FT, p) for p in ("4", "9", "10", "11", "22", "23", "35",
                                   "36", "41", "47", "48", "42")])   # 42 = TEST
R("12k", "FT_REF", "GND", S, tol="1%")
conn("FT_REF", (U_FT, "5"))
conn("USB_DM", (U_FT, "6"))
conn("USB_DP", (U_FT, "7"))
conn("+3V3", (U_FT, "12"), (U_FT, "24"), (U_FT, "46"), (U_FT, "39"), (U_FT, "40"))
decouple("+3V3", 4, S)
C("4.7uF", "+3V3", "GND", S)
conn("FT_VCCA", (U_FT, "37"))
conn("FT_VCORE", (U_FT, "38"))
C("100nF", "FT_VCCA", "GND", S)
C("100nF", "FT_VCORE", "GND", S)
# 245 synchronous FIFO interface to the FPGA
for i in range(8):
    conn(f"FT_D{i}", (U_FT, str(13 + i)))
ft_ctl = {"FT_RXF_N": "21", "FT_TXE_N": "25", "FT_RD_N": "26", "FT_WR_N": "27",
          "FT_SIWU_N": "28", "FT_CLKOUT": "29", "FT_OE_N": "30",
          "FT_ACBUS8": "32", "FT_ACBUS9": "33"}
for n, p in ft_ctl.items():
    conn(n, (U_FT, p))
conn("FT_PWRSAV_N", (U_FT, "31"))
R("10k", "+3V3", "FT_PWRSAV_N", S)
conn("FT_RESET_N", (U_FT, "34"))
R("10k", "+3V3", "FT_RESET_N", S)
# Configuration EEPROM (93LC56B, x16)
U = part("U", "Memory_EEPROM:93LCxxB", "93LC56B",
         "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", S, mpn="93LC56BT-I/SN", mfr="Microchip")
conn("FT_EECS", (U_FT, "45"), (U, "1"))
conn("FT_EECLK", (U_FT, "44"), (U, "2"))
conn("FT_EEDATA", (U_FT, "43"), (U, "3"))
conn("FT_EEDO", (U, "4"))
R("2.2k", "FT_EEDO", "FT_EEDATA", S)
R("10k", "+3V3", "FT_EECS", S)
R("10k", "+3V3", "FT_EECLK", S)
R("10k", "+3V3", "FT_EEDATA", S)
conn("GND", (U, "5"))
nc(U, 6, 7)
conn("+3V3", (U, "8"))
decouple("+3V3", 1, S)

# ----------------------------------------------------------- front end ----
S = "frontend"
U_BUF = part("U", "Amplifier_Operational:OPA1656ID", "OPA1656ID",
             "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", S, mpn="OPA1656IDR", mfr="Texas Instruments")
conn("+4V", (U_BUF, "8"))
conn("-4V", (U_BUF, "4"))
decouple("+4V", 1, S)
C("100nF", "-4V", "GND", S)


def channel(ch, buf_pins):
    """One ±10 V input channel: BNC, 1 MΩ ÷11 compensated divider, clamp,
    unity buffer, single-ended→differential FDA (gain 1), ADC input RC."""
    j = part("J", "Connector:Conn_Coaxial", f"BNC_{ch}",
             "Connector_Coaxial:BNC_Amphenol_B6252HB-NPP3G-50_Horizontal", S,
             mpn="B6252HB-NPP3G-50", mfr="Amphenol RF")
    raw, div, cl = f"IN{ch}_RAW", f"IN{ch}_DIV", f"IN{ch}_CLAMP"
    buf = f"IN{ch}_BUF"
    conn(raw, (j, "1"))
    conn("GND", (j, "2"))
    C("12pF", raw, "GND", S)                 # brings Cin to ~15 pF
    R("909k", raw, div, S, tol="0.1%")
    C("2.7pF", raw, div, S)                  # compensation
    R("90.9k", div, "GND", S, tol="0.1%")
    C("22pF", div, "GND", S)                 # 10x C1 incl. ~5 pF parasitics (TODO trim)
    R("1k", div, cl, S)
    d = part("D", "Diode:BAV99", "BAV99", "Package_TO_SOT_SMD:SOT-23", S,
             mpn="BAV99,215", mfr="Nexperia")
    # Nexperia BAV99: 1 = anode D1, 2 = cathode D2, 3 = common
    conn("-4V", (d, "1"))
    conn("+4V", (d, "2"))
    conn(cl, (d, "3"))
    out, inn, inp = buf_pins
    conn(cl, (U_BUF, inp))
    conn(buf, (U_BUF, out), (U_BUF, inn))
    # FDA THS4521 (SBOS458H pinout: 1 VIN-, 2 VOCM, 3 VS+, 4 VOUT+, 5 VOUT-,
    # 6 VS-, 7 PD, 8 VIN+)
    u = part("U", "Amplifier_Difference:THS4521ID", "THS4521ID",
             "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", S, mpn="THS4521IDR", mfr="Texas Instruments")
    sp, sn = f"FDA{ch}_SP", f"FDA{ch}_SN"     # summing nodes VIN+ / VIN-
    op, on = f"FDA{ch}_OP", f"FDA{ch}_ON"
    conn(sn, (u, "1"))
    conn(f"VCM{ch}", (u, "2"))
    conn("+3V3A", (u, "3"), (u, "7"))
    conn(op, (u, "4"))
    conn(on, (u, "5"))
    conn("GND", (u, "6"))
    conn(sp, (u, "8"))
    R("1k", buf, sp, S)          # Rg (signal leg)
    R("1k", on, sp, S)           # Rf
    C("33pF", on, sp, S)         # Cf: 4.8 MHz pole
    R("1k", "GND", sn, S)        # Rg (reference leg)
    R("1k", op, sn, S)           # Rf
    C("33pF", op, sn, S)
    C("100nF", "+3V3A", "GND", S)
    C("100nF", f"VCM{ch}", "GND", S)
    ap, an = f"AIN{ch}_P", f"AIN{ch}_N"
    R("49.9", op, ap, S)
    R("49.9", on, an, S)
    C("100pF", ap, an, S)


channel("A", ("1", "2", "3"))
channel("B", ("7", "6", "5"))

# ------------------------------------------------------------------ adc ----
S = "adc"
U_ADC = part("U", "Analog_ADC:LTC2290xUP", "LTC2290CUP",
             "Package_DFN_QFN:QFN-64-1EP_9x9mm_P0.5mm_EP7.15x7.15mm", S,
             mpn="LTC2290CUP#PBF", mfr="Analog Devices",
             datasheet="https://www.analog.com/media/en/technical-documentation/data-sheets/2290fa.pdf")
conn("AINA_P", (U_ADC, "1"))
conn("AINA_N", (U_ADC, "2"))
conn("AINB_N", (U_ADC, "15"))
conn("AINB_P", (U_ADC, "16"))
conn("REFHA", (U_ADC, "3"), (U_ADC, "4"))
conn("REFLA", (U_ADC, "5"), (U_ADC, "6"))
conn("REFLB", (U_ADC, "11"), (U_ADC, "12"))
conn("REFHB", (U_ADC, "13"), (U_ADC, "14"))
for ch in "AB":
    C("100nF", f"REFH{ch}", f"REFL{ch}", S)
    C("2.2uF", f"REFH{ch}", f"REFL{ch}", S)
    C("1uF", f"REFH{ch}", "GND", S)
    C("1uF", f"REFL{ch}", "GND", S)
    C("2.2uF", f"VCM{ch}", "GND", S)
conn("+3V3A", (U_ADC, "7"), (U_ADC, "10"), (U_ADC, "18"), (U_ADC, "63"))
decouple("+3V3A", 4, S)
C("10uF", "+3V3A", "GND", S)
conn("ADC_CLKA", (U_ADC, "8"))
conn("ADC_CLKB", (U_ADC, "9"))
conn("GND", (U_ADC, "17"), (U_ADC, "64"), (U_ADC, "65"), (U_ADC, "31"), (U_ADC, "50"))
# Config (TODO verify vs LTC2290 datasheet): SENSE=VDD -> 2 Vpp range;
# MUX=VDD -> A on DA, B on DB; SHDN low = run; OE low = outputs on;
# MODE = 2/3 VDD -> two's complement, clock duty-cycle stabilizer on.
conn("+3V3A", (U_ADC, "19"), (U_ADC, "62"), (U_ADC, "21"))
conn("VCMB", (U_ADC, "20"))
conn("VCMA", (U_ADC, "61"))
conn("GND", (U_ADC, "22"), (U_ADC, "23"), (U_ADC, "58"), (U_ADC, "59"))
conn("ADC_MODE", (U_ADC, "60"))
R("10k", "+3V3A", "ADC_MODE", S)
R("20k", "ADC_MODE", "GND", S)
nc(U_ADC, 24, 25, 41, 42)
conn("+3V3", (U_ADC, "32"), (U_ADC, "49"))     # OVDD = FPGA I/O voltage
decouple("+3V3", 2, S)

# ADC outputs -> 33 Ω series resistor packs -> FPGA (cuts digital kickback)
adc_bits = ([(f"DA{i}", str(p)) for i, p in zip(range(6), range(43, 49))]
            + [(f"DA{i}", str(p)) for i, p in zip(range(6, 12), range(51, 57))]
            + [("OFA", "57")]
            + [(f"DB{i}", str(p)) for i, p in zip(range(5), range(26, 31))]
            + [(f"DB{i}", str(p)) for i, p in zip(range(5, 12), range(33, 40))]
            + [("OFB", "40")])
rpack = None
for k, (name, pin) in enumerate(adc_bits):
    if k % 4 == 0:
        rpack = part("RN", "Device:R_Pack04", "33", "Resistor_SMD:R_Array_Convex_4x0603", S,
                     mpn="CAY16-330J4LF", mfr="Bourns")
    conn(f"ADC_{name}_R", (U_ADC, pin), (rpack, str(k % 4 + 1)))
    conn(f"ADC_{name}", (rpack, str(8 - k % 4)))
nc(rpack, 3, 4, 5, 6)   # 26 bits use 6.5 packs; last pack half unused

# 10 MHz sample clock
X = part("X", "Oscillator:ASE-xxxMHz", "ASE-10.000MHz",
         "Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm", S,
         mpn="ASE-10.000MHZ-LC-T", mfr="Abracon")
FB("+3V3A", "OSC_VDD", S)
conn("OSC_VDD", (X, "1"), (X, "4"))
conn("GND", (X, "2"))
conn("CLK10", (X, "3"))
C("100nF", "OSC_VDD", "GND", S)
R("33", "CLK10", "ADC_CLKA", S)
R("33", "CLK10", "ADC_CLKB", S)
R("33", "CLK10", "FPGA_CLK10", S)

# ----------------------------------------------------------------- fpga ----
S = "fpga"
U_FPGA = part("U", "FPGA_Lattice:ICE40HX4K-TQ144", "ICE40HX4K-TQ144",
              "Package_QFP:TQFP-144_20x20mm_P0.5mm", S,
              mpn="ICE40HX4K-TQ144", mfr="Lattice")
F = lambda p: (U_FPGA, str(p))
bank0 = [110, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 124, 125,
         128, 129, 130, 134, 135, 136, 137, 138, 139, 141, 142, 143, 144]
bank1 = [73, 74, 75, 76, 78, 79, 80, 81, 82, 83, 84, 85, 87, 88, 90, 91, 93, 94,
         95, 96, 97, 98, 99, 101, 102, 104, 105, 106, 107]
bank2 = [37, 38, 39, 41, 42, 43, 44, 45, 47, 48, 49, 52, 55, 56, 60, 61, 62, 63, 64]
bank3 = [1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
         25, 26, 28, 29, 31, 32, 33, 34]
used = set()


def fpin(net, pin):
    conn(net, F(pin))
    used.add(pin)


# Bank 3 (left): ADC data, top->bottom; GBIN6 (21) = 10 MHz sample clock.
fpin("FPGA_CLK10", 21)
adc_order = (["ADC_OFA"] + [f"ADC_DA{i}" for i in range(11, -1, -1)]
             + ["ADC_OFB"] + [f"ADC_DB{i}" for i in range(11, -1, -1)])
for net, pin in zip(adc_order, [p for p in bank3 if p != 21]):
    fpin(net, pin)
# Bank 2 (bottom): FT232H FIFO; GBIN4 (52) = 60 MHz CLKOUT.
fpin("FT_CLKOUT", 52)
ft_order = ([f"FT_D{i}" for i in range(8)]
            + ["FT_RXF_N", "FT_TXE_N", "FT_RD_N", "FT_WR_N", "FT_OE_N",
               "FT_SIWU_N", "FT_ACBUS8", "FT_ACBUS9", "LED1_N", "LED2_N"])
for net, pin in zip(ft_order, [p for p in bank2 if p != 52]):
    fpin(net, pin)
# Bank 1 (right) + bank 0 (top): SDRAM.
sd_ctl = ([f"SD_A{i}" for i in range(13)] + ["SD_BA0", "SD_BA1", "SD_CS_N",
          "SD_RAS_N", "SD_CAS_N", "SD_WE_N", "SD_CKE", "SD_CLK", "SD_DQML", "SD_DQMH"])
for net, pin in zip(sd_ctl, bank1):
    fpin(net, pin)
for net, pin in zip([f"SD_DQ{i}" for i in range(16)], bank0):
    fpin(net, pin)
fpin("LM_PGOOD_N", [p for p in bank1 if p not in used][0])
spare = [p for p in bank0 + bank1 + bank2 + bank3 if p not in used]

# Power
conn("+1V2", *[F(p) for p in (27, 40, 92, 111)])
conn("+3V3", *[F(p) for p in (123, 131, 89, 100, 46, 57, 6, 30, 72, 108)])
conn("GND", *[F(p) for p in (5, 13, 14, 59, 69, 86, 103, 132, 140, 53, 127)])
nc(U_FPGA, 35, 36, 50, 51, 58, 77, 133, 109)   # NC pins + VPP_FAST (unused)
decouple("+1V2", 4, S)
C("10uF", "+1V2", "GND", S)
decouple("+3V3", 10, S)
C("10uF", "+3V3", "GND", S)
# PLL supplies: 100 Ω + 10 µF + 100 nF filter each (Lattice iCE40 guidance)
for k, (vp, _) in enumerate(((54, 53), (126, 127))):
    n = f"VCCPLL{k}"
    R("100", "+1V2", n, S)
    conn(n, F(vp))
    C("10uF", n, "GND", S)
    C("100nF", n, "GND", S)

# Configuration: SPI flash + programming header
conn("CFG_SO", F(67))     # FPGA SDO -> flash DI
conn("CFG_SI", F(68))     # flash DO -> FPGA SDI
conn("CFG_SCK", F(70))
conn("CFG_SS_N", F(71))
conn("CDONE", F(65))
conn("CRESET_N", F(66))
R("10k", "+3V3", "CDONE", S)
R("10k", "+3V3", "CRESET_N", S)
R("10k", "+3V3", "CFG_SS_N", S)
U = part("U", "Memory_Flash:W25Q32JVSS", "W25Q32JVSS",
         "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm", S, mpn="W25Q32JVSSIQ", mfr="Winbond")
conn("CFG_SS_N", (U, "1"))
conn("CFG_SI", (U, "2"))
conn("FLASH_WP_N", (U, "3"))
conn("GND", (U, "4"))
conn("CFG_SO", (U, "5"))
conn("CFG_SCK", (U, "6"))
conn("FLASH_HOLD_N", (U, "7"))
conn("+3V3", (U, "8"))
R("10k", "+3V3", "FLASH_WP_N", S)
R("10k", "+3V3", "FLASH_HOLD_N", S)
decouple("+3V3", 1, S)
J = part("J", "Connector_Generic:Conn_02x04_Odd_Even", "PROG",
         "Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical", S)
conn("CFG_SS_N", (J, "1"))
conn("+3V3", (J, "2"))
conn("CFG_SCK", (J, "3"))
conn("CRESET_N", (J, "4"))
conn("CFG_SO", (J, "5"))
conn("GND", (J, "6"))
conn("CFG_SI", (J, "7"))
conn("CDONE", (J, "8"))
# User LEDs (active low from FPGA)
for n in ("LED1_N", "LED2_N"):
    d = part("D", "Device:LED", "Yellow", LED_FP, S)
    a = n.replace("_N", "_A")
    R("1k", "+3V3", a, S)
    conn(a, (d, "2"))
    conn(n, (d, "1"))

# --------------------------------------------------------------- memory ----
S = "memory"
U_SD = part("U", "Memory_RAM:MT48LC16M16A2TG", "MT48LC16M16A2TG-6A",
            "Package_SO:TSOP-II-54_22.2x10.16mm_P0.8mm", S,
            mpn="MT48LC16M16A2P-6A:G", mfr="Micron")
sd = {"DQ0": 2, "DQ1": 4, "DQ2": 5, "DQ3": 7, "DQ4": 8, "DQ5": 10, "DQ6": 11,
      "DQ7": 13, "DQML": 15, "WE_N": 16, "CAS_N": 17, "RAS_N": 18, "CS_N": 19,
      "BA0": 20, "BA1": 21, "A10": 22, "A0": 23, "A1": 24, "A2": 25, "A3": 26,
      "A4": 29, "A5": 30, "A6": 31, "A7": 32, "A8": 33, "A9": 34, "A11": 35,
      "A12": 36, "CKE": 37, "CLK": 38, "DQMH": 39, "DQ8": 42, "DQ9": 44,
      "DQ10": 45, "DQ11": 47, "DQ12": 48, "DQ13": 50, "DQ14": 51, "DQ15": 53}
for name, pin in sd.items():
    conn(f"SD_{name}", (U_SD, str(pin)))
conn("+3V3", *[(U_SD, str(p)) for p in (1, 14, 27, 3, 9, 43, 49)])
conn("GND", *[(U_SD, str(p)) for p in (28, 41, 54, 6, 12, 46, 52)])
nc(U_SD, 40)
decouple("+3V3", 7, S)
C("10uF", "+3V3", "GND", S)

# FPGA spare I/O pins: mark as no-connect.
nc(U_FPGA, *spare)

# ----------------------------------------------------------- emit plan ----
POWER = {"+5V", "+3V3", "+3V3A", "+1V2", "+4V", "-4V", "VBUS", "VBUS_F"}
plan = {
    "spec": open(os.path.join(HERE, "..", "dual-adc-prompt.txt")).read().strip(),
    "summary": ("Two BNC inputs (1 MΩ, ÷11 compensated divider, OPA1656 buffer, "
                "THS4521 FDA) drive an LTC2290 dual 12-bit 10 MS/s ADC clocked by "
                "a 10 MHz XO. An iCE40HX4K FPGA captures both channels into a 32 MB "
                "SDRAM (0.8 s at full rate) and uploads through an FT232H USB 2.0 "
                "HS sync FIFO. Bus powered (~330 mA) via USB-B; LDOs for 3.3 V "
                "digital, 3.3 V analog, 1.2 V core; LM27762 for ±4 V."),
    "topology": "mixed_signal_daq",
    "sheets": [{"name": s, "title": s} for s in
               ("power", "usb", "frontend", "adc", "fpga", "memory")],
    "parts": [{k: v for k, v in p.items() if v is not None} for p in parts],
    "nets": [],
    "open_questions": [
        "FT232H power-pin strapping and LTC2290 SENSE/MODE/REF connections are "
        "from memory: verify against DS_FT232H and the LTC2290 datasheet.",
        "Input compensation capacitors need trimming on the built board.",
        "USB 100 mA pre-enumeration limit is not enforced (no load switch).",
    ],
}
for name, pins in nets.items():
    if len(pins) < 2:
        raise SystemExit(f"net {name} has only {pins}")
    n = {"name": name, "pins": [{"refdes": r, "pin": p} for r, p in pins]}
    if name == "GND":
        n["is_ground"] = True
    elif name in POWER:
        n["is_power"] = True
    plan["nets"].append(n)

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "dual_adc_plan.json"), "w") as fh:
    json.dump(plan, fh, indent=1, ensure_ascii=False)
with open(os.path.join(OUT, "no_connects.json"), "w") as fh:
    json.dump(no_connects, fh)
print(f"{len(parts)} parts, {len(nets)} nets, {len(no_connects)} NC pins, "
      f"{len(spare)} spare FPGA I/O")
