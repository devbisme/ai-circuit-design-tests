"""Dual-channel +/-10 V, 10 MSPS, 12-bit USB 2.0 ADC board -- circuit description.

Run gen_sch.py to turn this into a KiCad 10 project.
FPGA pin assignment for the swappable buses comes from pinmap.json when present
(written by assign_pins.py after placement), else a default in-order mapping.
"""
import json
from pathlib import Path
from circuit import Circuit, FP

HERE = Path(__file__).parent
PINMAP = HERE / "pinmap.json"

ADC_SIGS = [f"ADCA_D{i}" for i in range(12)] + ["ADC_OFA"] + [f"ADCB_D{i}" for i in range(12)] + ["ADC_OFB"]
FT_SIGS = [f"FT_D{i}" for i in range(8)] + ["FT_RXF_N", "FT_TXE_N", "FT_RD_N", "FT_WR_N", "FT_SIWU_N", "FT_OE_N",
                                            "LED0", "LED1"]
SD_SIGS = ([f"SD_DQ{i}" for i in range(16)] + [f"SD_A{i}" for i in range(12)] +
           ["SD_BA0", "SD_BA1", "SD_LDQM", "SD_UDQM", "SD_WE_N", "SD_CAS_N", "SD_RAS_N", "SD_CS_N",
            "SD_CKE", "SD_CLK_S"])

# Fixed FPGA pins (global-buffer inputs and dedicated config pins)
FPGA_FIXED = {"21": "FPGA_CLK", "49": "FT_CLKOUT"}
# FPGA I/O banks by package side (TQ144): bank3 left, bank2 bottom, bank1 right, bank0 top
SPI_PINS = {"67", "68", "70", "71"}


def fpga_io_pins(libpins):
    io = [p for p in libpins if p["name"].startswith(("IOL", "IOB", "IOR", "IOT")) and p["number"] not in SPI_PINS]
    side = lambda n: "L" if n <= 36 else "B" if n <= 72 else "R" if n <= 108 else "T"
    return {s: [p["number"] for p in io if side(int(p["number"])) == s and p["number"] not in FPGA_FIXED]
            for s in "LBRT"}


def default_pinmap(io):
    m = {}
    left = list(io["L"])
    for s in ADC_SIGS:
        m[s] = left.pop(0)
    bot = list(io["B"])
    for s in FT_SIGS:
        m[s] = bot.pop(0)
    rt = list(io["R"]) + list(io["T"])
    for s in SD_SIGS:
        m[s] = rt.pop(0)
    return m


def build():
    c = Circuit()

    # ------------------------------------------------------------ Power
    c.sheet = "Power"
    c.group = "USBIN"
    c.add("J", "Connector:USB_B", "USB_B", "Connector_USB:USB_B_OST_USB-B1HSxx_Horizontal",
          {1: "VBUS", 2: "USB_DM", 3: "USB_DP", 4: "GND", "SH": "USB_SHIELD"})
    c.R("1M", "USB_SHIELD", "GND")
    c.C("4.7n", "USB_SHIELD", "GND", fp="C0805")
    c.add("U", "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
          {1: "USB_DM", 6: "USB_DM", 3: "USB_DP", 4: "USB_DP", 5: "VBUS", 2: "GND"})
    c.add("F", "Device:Polyfuse_Small", "750mA hold", "Fuse:Fuse_1206_3216Metric", {1: "VBUS", 2: "+5V"})
    c.decap("+5V", ["10u"])
    c.group = "BUCK"
    # 3.3 V digital: buck, Vout = 0.6 * (1 + 100k/22.1k) = 3.31 V
    c.add("U", "Regulator_Switching:TLV62569DBV", "TLV62569DBV", "Package_TO_SOT_SMD:SOT-23-5",
          {4: "+5V", 1: "+5V", 2: "GND", 3: "BUCK_SW", 5: "BUCK_FB"})
    c.decap("+5V", ["10u"])
    c.add("L", "Device:L", "2.2u", "Inductor_SMD:L_Bourns-SRN4018", {1: "BUCK_SW", 2: "+3V3"})
    c.R("100k", "+3V3", "BUCK_FB")
    c.R("22.1k", "BUCK_FB", "GND")
    c.decap("+3V3", ["22u", "22u"])
    # 1.2 V FPGA core
    c.group = "LDO12"
    c.add("U", "Regulator_Linear:AP2112K-1.2", "AP2112K-1.2", "Package_TO_SOT_SMD:SOT-23-5",
          {1: "+3V3", 3: "+3V3", 2: "GND", 5: "+1V2"}, nc=("4",))
    c.decap("+3V3", ["1u"])
    c.decap("+1V2", ["10u"])
    c.group = "LDO3VA"
    # 3.0 V low-noise ADC / clock / FDA rail
    c.add("U", "Regulator_Linear:LP5907MFX-3.0", "LP5907MFX-3.0", "Package_TO_SOT_SMD:SOT-23-5",
          {1: "+5V", 3: "+5V", 2: "GND", 5: "+3VA"}, nc=("4",))
    c.decap("+5V", ["1u"])
    c.decap("+3VA", ["10u"])
    # +/-5 V analog for the input buffers
    c.group = "NEG5"
    c.FB("+5V", "+5VA")
    c.decap("+5VA", ["10u"])
    c.add("U", "Regulator_SwitchedCapacitor:TPS60403DBV", "TPS60403DBV", "Package_TO_SOT_SMD:SOT-23-5",
          {2: "+5VA", 1: "-5VA", 3: "CP_FLYN", 5: "CP_FLYP", 4: "GND"})
    c.C("1u", "CP_FLYP", "CP_FLYN")
    c.decap("+5VA", ["1u"])
    c.decap("-5VA", ["4.7u"])
    c.group = "PWRLED"
    c.R("1k", "+3V3", "LED_PWR")
    c.LED("LED_PWR", "GND", "green")
    for net in ("+5V", "+5VA", "+3V3", "OSC_VDD", "VCCPLL0", "VCCPLL1", "FT_VPHY"):
        c.add("#FLG", "power:PWR_FLAG", "PWR_FLAG", "", {1: net})
    c.group = "HOLES"
    for _ in range(4):
        c.add("H", "Mechanical:MountingHole", "MountingHole", "MountingHole:MountingHole_3.2mm_M3", {})

    # ------------------------------------------------------------ Analog front end
    c.sheet = "FrontEnd"
    for ch in "AB":
        c.group = "FE" + ch
        c.add("J", "Connector:Conn_Coaxial", f"BNC_CH{ch}",
              "Connector_Coaxial:BNC_Amphenol_B6252HB-NPP3G-50_Horizontal", {1: f"IN_{ch}", 2: "GND"})
        # 1 MOhm, ~15 pF compensated 10:1 attenuator (scope-probe compatible)
        c.R("909k", f"IN_{ch}", f"ATT_{ch}", fp="R1206")
        c.C("16p C0G", f"IN_{ch}", f"ATT_{ch}", fp="C1206")
        c.R("100k", f"ATT_{ch}", "GND")
        c.C("150p C0G", f"ATT_{ch}", "GND")
        # clamp to the +/-5 V rails (BAV99: pin1 lower anode, pin2 upper cathode, pin3 common)
        c.add("D", "Diode:BAV99", "BAV99", "Package_TO_SOT_SMD:SOT-23", {1: "-5VA", 2: "+5VA", 3: f"ATT_{ch}"})
        # unity-gain FET-input buffer
        c.add("U", "Amplifier_Operational:OPA810xDBV", "OPA810", "Package_TO_SOT_SMD:SOT-23-5",
              {3: f"ATT_{ch}", 4: f"BUF_{ch}", 1: f"BUF_{ch}", 5: "+5VA", 2: "-5VA"})
        c.decap("+5VA", ["100n"])
        c.decap("-5VA", ["100n"])
        # single-ended -> differential, gain 0.953, Vocm = ADC VCM (1.5 V)
        c.add("U", "Amplifier_Difference:THS4521ID", "THS4521", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
              {8: f"FDA{ch}_INP", 1: f"FDA{ch}_INN", 4: f"FDA{ch}_OUTP", 5: f"FDA{ch}_OUTN",
               3: "+3VA", 6: "GND", 2: f"VCM_{ch}", 7: "+3VA"})
        c.decap("+3VA", ["100n"])
        c.R("1k", f"BUF_{ch}", f"FDA{ch}_INP")
        c.R("1k", "GND", f"FDA{ch}_INN")
        c.R("953", f"FDA{ch}_OUTN", f"FDA{ch}_INP")
        c.R("953", f"FDA{ch}_OUTP", f"FDA{ch}_INN")
        # 1-pole anti-alias, fc = 1/(2*pi*99.8*330p) = 4.8 MHz
        c.R("49.9", f"FDA{ch}_OUTP", f"AIN_{ch}_P")
        c.R("49.9", f"FDA{ch}_OUTN", f"AIN_{ch}_N")
        c.C("330p C0G", f"AIN_{ch}_P", f"AIN_{ch}_N")

    # ------------------------------------------------------------ ADC + clock
    c.sheet = "ADC"
    c.group = "ADC"
    adc = {1: "AIN_A_P", 2: "AIN_A_N", 3: "REFH_A", 4: "REFH_A", 5: "REFL_A", 6: "REFL_A",
           8: "ADC_CLK", 9: "ADC_CLK", 11: "REFL_B", 12: "REFL_B", 13: "REFH_B", 14: "REFH_B",
           15: "AIN_B_N", 16: "AIN_B_P", 17: "GND", 19: "+3VA", 20: "VCM_B", 21: "+3VA",
           22: "GND", 23: "GND", 31: "GND", 32: "+3V3", 49: "+3V3", 50: "GND", 58: "GND", 59: "GND",
           60: "ADC_MODE", 61: "VCM_A", 62: "+3VA", 64: "GND", 65: "GND"}
    for pin in (7, 10, 18, 63):
        adc[pin] = "+3VA"
    dpins_b = [26, 27, 28, 29, 30, 33, 34, 35, 36, 37, 38, 39]
    dpins_a = [43, 44, 45, 46, 47, 48, 51, 52, 53, 54, 55, 56]
    for i in range(12):
        adc[dpins_a[i]] = f"ADCA_D{i}_S"
        adc[dpins_b[i]] = f"ADCB_D{i}_S"
    adc[57] = "ADC_OFA_S"
    adc[40] = "ADC_OFB_S"
    c.add("U", "Analog_ADC:LTC2290xUP", "LTC2290", "Package_DFN_QFN:QFN-64-1EP_9x9mm_P0.5mm_EP7.15x7.15mm", adc)
    c.decap("+3VA", ["100n", "100n", "100n", "100n", "10u"])
    c.decap("+3V3", ["100n", "100n"])
    for ch in "AB":
        c.C("100n", f"REFH_{ch}", f"REFL_{ch}")
        c.C("2.2u", f"REFH_{ch}", f"REFL_{ch}")
        c.C("1u", f"REFH_{ch}", "GND")
        c.C("1u", f"REFL_{ch}", "GND")
        c.C("2.2u", f"VCM_{ch}", "GND")
    # MODE = 2/3 VDD: two's complement output, clock duty-cycle stabilizer on
    c.R("10k", "+3VA", "ADC_MODE")
    c.R("20k", "ADC_MODE", "GND")
    c.group = "RN"
    # 33 ohm series packs between ADC outputs and FPGA (limit digital kickback)
    sigs = ADC_SIGS
    for k in range(0, len(sigs), 4):
        grp = sigs[k:k + 4]
        pins, nc = {}, []
        for j in range(4):
            a, b = str(1 + j), str(8 - j)
            if j < len(grp):
                pins[a], pins[b] = grp[j] + "_S", grp[j]
            else:
                nc += [a, b]
        c.add("RN", "Device:R_Pack04", "4x33", FP["RARR"], pins, nc=nc)
    # 10 MHz sample clock, shared by ADC and FPGA
    c.group = "OSC"
    c.add("Y", "Oscillator:SiT8008xx-2x-xxE", "SiT8008 10MHz", "Oscillator:Oscillator_SMD_SiT_PQFN-4Pin_3.2x2.5mm",
          {1: "OSC_VDD", 4: "OSC_VDD", 2: "GND", 3: "OSC_OUT"})
    c.FB("+3VA", "OSC_VDD")
    c.decap("OSC_VDD", ["100n"])
    c.R("33", "OSC_OUT", "ADC_CLK")
    c.R("33", "OSC_OUT", "FPGA_CLK")

    # ------------------------------------------------------------ FPGA + config flash
    c.sheet = "FPGA"
    c.group = "FPGA"
    from sexp import load_symbol, symbol_pins
    fl = symbol_pins(load_symbol("FPGA_Lattice:ICE40HX4K-TQ144"))
    io = fpga_io_pins(fl)
    pm = json.loads(PINMAP.read_text()) if PINMAP.exists() else default_pinmap(io)
    fp_ = dict(FPGA_FIXED)
    for sig, pin in pm.items():
        assert pin not in fp_, (sig, pin)
        fp_[pin] = sig
    byname = {}
    for p in fl:
        byname.setdefault(p["name"], []).append(p["number"])
    for n in byname["VCC"]:
        fp_[n] = "+1V2"
    for nm in ("VCCIO_0", "VCCIO_1", "VCCIO_2", "VCCIO_3", "VCC_SPI", "VPP_2V5"):
        for n in byname[nm]:
            fp_[n] = "+3V3"
    for n in byname["GND"] + byname["GNDPLL0"] + byname["GNDPLL1"]:
        fp_[n] = "GND"
    fp_[byname["VCCPLL0"][0]] = "VCCPLL0"
    fp_[byname["VCCPLL1"][0]] = "VCCPLL1"
    fp_["65"], fp_["66"] = "FPGA_CDONE", "FPGA_CRESET"
    fp_["67"], fp_["68"], fp_["70"], fp_["71"] = "FLASH_MOSI", "FLASH_MISO", "FLASH_SCK", "FLASH_CS"
    nc = [p["number"] for p in fl if p["number"] not in fp_]   # spare I/O and VPP_FAST
    c.add("U", "FPGA_Lattice:ICE40HX4K-TQ144", "iCE40HX4K-TQ144", "Package_QFP:TQFP-144_20x20mm_P0.5mm",
          fp_, nc=nc)
    c.decap("+1V2", ["100n"] * 4 + ["10u"])
    c.decap("+3V3", ["100n"] * 8 + ["10u"])
    for k in ("0", "1"):     # Lattice-recommended PLL supply filter
        c.R("100", "+1V2", f"VCCPLL{k}")
        c.decap(f"VCCPLL{k}", ["10u", "100n"])
    c.R("10k", "+3V3", "FPGA_CRESET")
    c.R("10k", "+3V3", "FPGA_CDONE")
    c.group = "FLASH"
    c.add("U", "Memory_Flash:W25Q32JVSS", "W25Q32JVSS", "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm",
          {1: "FLASH_CS", 2: "FLASH_MISO", 3: "FLASH_WP", 4: "GND", 5: "FLASH_MOSI", 6: "FLASH_SCK",
           7: "FLASH_HOLD", 8: "+3V3"})
    c.decap("+3V3", ["100n"])
    for n in ("FLASH_CS", "FLASH_WP", "FLASH_HOLD"):
        c.R("10k", "+3V3", n)
    c.group = "PROG"
    c.add("J", "Connector_Generic:Conn_01x08", "PROG", "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
          {1: "+3V3", 2: "GND", 3: "FLASH_CS", 4: "FLASH_SCK", 5: "FLASH_MOSI", 6: "FLASH_MISO",
           7: "FPGA_CRESET", 8: "FPGA_CDONE"})
    c.group = "LEDS"
    for k in ("0", "1"):
        c.R("1k", f"LED{k}", f"LED{k}_K")
        c.LED(f"LED{k}_K", "GND", "yellow")

    # ------------------------------------------------------------ SDRAM
    c.sheet = "Memory"
    c.group = "SDRAM"
    sd = {38: "SD_CLK", 37: "SD_CKE", 19: "SD_CS_N", 18: "SD_RAS_N", 17: "SD_CAS_N", 16: "SD_WE_N",
          15: "SD_LDQM", 39: "SD_UDQM", 20: "SD_BA0", 21: "SD_BA1"}
    for n in (1, 14, 27, 3, 9, 43, 49):
        sd[n] = "+3V3"
    for n in (28, 41, 54, 6, 12, 46, 52):
        sd[n] = "GND"
    for i, n in enumerate([2, 4, 5, 7, 8, 10, 11, 13, 42, 44, 45, 47, 48, 50, 51, 53]):
        sd[n] = f"SD_DQ{i}"
    for i, n in enumerate([23, 24, 25, 26, 29, 30, 31, 32, 33, 34, 22, 35]):
        sd[n] = f"SD_A{i}"
    c.add("U", "Memory_RAM:IS42S16400J-xT", "IS42S16400J (8 MB)", "Package_SO:TSOP-II-54_22.2x10.16mm_P0.8mm", sd)
    c.decap("+3V3", ["100n"] * 7 + ["10u"])
    c.R("22", "SD_CLK_S", "SD_CLK")

    # ------------------------------------------------------------ USB bridge
    c.sheet = "USB"
    c.group = "FT"
    ft = {1: "FT_XI", 2: "FT_XO", 3: "FT_VPHY", 8: "FT_VPHY", 5: "FT_REF", 6: "USB_DM", 7: "USB_DP",
          12: "+3V3", 24: "+3V3", 46: "+3V3", 40: "+3V3", 39: "+3V3", 38: "FT_VCORE", 37: "FT_VCCA",
          34: "FT_RESET_N", 42: "GND", 43: "FT_EEDATA", 44: "FT_EECLK", 45: "FT_EECS",
          21: "FT_RXF_N", 25: "FT_TXE_N", 26: "FT_RD_N", 27: "FT_WR_N", 28: "FT_SIWU_N",
          29: "FT_CLKOUT", 30: "FT_OE_N"}
    for i, n in enumerate(range(13, 21)):
        ft[n] = f"FT_D{i}"
    for n in (4, 9, 10, 11, 22, 23, 35, 36, 41, 47, 48):
        ft[n] = "GND"
    c.add("U", "Interface_USB:FT232H", "FT232HL", "Package_QFP:LQFP-48_7x7mm_P0.5mm", ft, nc=("31", "32", "33"))
    c.R("12k 1%", "FT_REF", "GND")
    c.R("10k", "+3V3", "FT_RESET_N")
    c.add("Y", "Device:Crystal_GND24", "12MHz", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
          {1: "FT_XI", 3: "FT_XO", 2: "GND", 4: "GND"})
    c.C("18p C0G", "FT_XI", "GND")
    c.C("18p C0G", "FT_XO", "GND")
    c.FB("+3V3", "FT_VPHY")
    c.decap("FT_VPHY", ["4.7u", "100n", "100n"])
    c.decap("+3V3", ["100n", "100n", "100n", "100n", "4.7u"])
    c.decap("FT_VCORE", ["100n"])
    c.decap("FT_VCCA", ["100n"])
    c.add("U", "Memory_EEPROM:93LCxxB", "93LC56B", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
          {1: "FT_EECS", 2: "FT_EECLK", 3: "FT_EEDATA", 4: "EE_DO", 5: "GND", 8: "+3V3"})
    c.R("2.2k", "EE_DO", "FT_EEDATA")
    c.R("10k", "+3V3", "FT_EEDATA")
    c.decap("+3V3", ["100n"])
    return c


if __name__ == "__main__":
    c = build()
    nets = c.nets()
    print(len(c.parts), "parts", len(nets), "nets")
    for n, pins in sorted(nets.items()):
        if len(pins) < 2:
            print("SINGLE-PIN NET", n, pins)
