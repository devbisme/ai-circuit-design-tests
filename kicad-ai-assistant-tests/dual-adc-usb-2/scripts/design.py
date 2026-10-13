"""Dual-channel 12-bit 10 Msps USB ADC -- design netlist (single source of truth).

Every part, value, footprint and pin->net assignment lives here.  build_schematic.py turns
this into KiCad schematic sheets using kcaa tools; docs/BOM are generated from it too.

Net naming: names in POWER_NETS become KiCad power symbols; everything else becomes a
label (local if the net stays on one sheet, global otherwise).  "NC" = no-connect flag.
"""

LIB = "dual_adc"          # project library of flattened symbols (see flatten_symbols.py)

POWER_NETS = {            # net -> power-library symbol
    "GND": "GND", "VBUS": "VBUS", "+5V": "+5V", "+3V3": "+3V3", "+1V2": "+1V2",
    "+3.3VA": "+3.3VA", "+5VA": "+5VA", "-5V": "-5V", "-5VA": "-5VA",
}
# nets driven only by passives (fuse, inductor, ferrites, resistors) or FT232H VCCD
PWR_FLAG_NETS = ["+5V", "+3V3", "+5VA", "-5VA", "FT_VCCD", "VCCPLL0", "VCCPLL1"]

FP = dict(
    R="Resistor_SMD:R_0603_1608Metric", R1206="Resistor_SMD:R_1206_3216Metric",
    C="Capacitor_SMD:C_0603_1608Metric", C0805="Capacitor_SMD:C_0805_2012Metric",
    CTRIM="Capacitor_SMD:C_Trimmer_Murata_TZC3", FB="Inductor_SMD:L_0603_1608Metric",
    L="Inductor_SMD:L_Coilcraft_XxL4020", FUSE="Fuse:Fuse_1206_3216Metric",
    LED="LED_SMD:LED_0603_1608Metric", XTAL="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    USB="Connector_USB:USB_B_OST_USB-B1HSxx_Horizontal",
    BNC="Connector_Coaxial:BNC_Amphenol_B6252HB-NPP3G-50_Horizontal",
    HDR="Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical",
    LQFP48="Package_QFP:LQFP-48_7x7mm_P0.5mm", HOLE="MountingHole:MountingHole_3.2mm_M3",
)

PARTS = {}   # ref -> dict(sheet, sym, value, fp, pins{num: net}, desc)


def part(ref, sheet, sym, value, pins, fp=None, desc=""):
    assert ref not in PARTS, ref
    PARTS[ref] = dict(sheet=sheet, sym=sym, value=value, fp=fp, pins=dict(pins), desc=desc)


def R(ref, sheet, val, a, b, fp=FP["R"], desc=""):
    part(ref, sheet, "R", val, {"1": a, "2": b}, fp, desc)


def C(ref, sheet, val, a, b="GND", fp=FP["C"], desc=""):
    part(ref, sheet, "C", val, {"1": a, "2": b}, fp, desc)


def decaps(prefix_start, sheet, net, vals, desc=""):
    """Bank of decoupling caps from net to GND; returns next ref number."""
    n = prefix_start
    for v in vals:
        fp = FP["C0805"] if v in ("10u", "22u", "4.7u") else FP["C"]
        C(f"C{n}", sheet, v, net, "GND", fp, desc or f"decoupling {net}")
        n += 1
    return n


# =====================================================================================
# Sheet "power": USB-B input, ESD, fuse, 3.3 V buck, 1.2 V LDO, 3.3 V analog LDO,
# +5 VA filter, -5 V charge pump + filter, power LED, mounting holes
# =====================================================================================
S = "power"
part("J1", S, "USB_B", "USB-B", {"1": "VBUS", "2": "USB_DM", "3": "USB_DP", "4": "GND",
                                  "SH": "USB_SHIELD"}, FP["USB"], "USB 2.0 type-B receptacle")
R("R1", S, "1M", "USB_SHIELD", "GND", desc="shield bleed")
C("C1", S, "4.7n", "USB_SHIELD", "GND", desc="shield RF tie (250 V)")
part("U1", S, "USBLC6-2SC6", "USBLC6-2SC6", {"1": "USB_DM", "6": "USB_DM", "3": "USB_DP",
                                              "4": "USB_DP", "5": "VBUS", "2": "GND"},
     desc="USB ESD protection")
part("F1", S, "Polyfuse", "0.5A hold", {"1": "VBUS", "2": "+5V"}, FP["FUSE"],
     "resettable fuse, 500 mA hold")
C("C2", S, "4.7u", "+5V", fp=FP["C0805"], desc="+5V bulk (keep total VBUS C ~10 uF)")
# 3.3 V digital buck (TLV62569, Vfb = 0.6 V)
part("U2", S, "TLV62569DBV", "TLV62569DBV", {"4": "+5V", "1": "+5V", "2": "GND",
                                              "3": "BUCK_SW", "5": "BUCK_FB"},
     desc="5V->3.3V 2 A buck")
part("L1", S, "L", "2.2u XFL4020-222", {"1": "BUCK_SW", "2": "+3V3"}, FP["L"],
     "buck inductor")
R("R2", S, "453k", "+3V3", "BUCK_FB", desc="FB top: Vout = 0.6*(1+453k/100k) = 3.32 V")
R("R3", S, "100k", "BUCK_FB", "GND", desc="FB bottom")
C("C3", S, "22p", "+3V3", "BUCK_FB", desc="FB feed-forward")
C("C4", S, "4.7u", "+5V", fp=FP["C0805"], desc="buck input")
C("C5", S, "22u", "+3V3", fp=FP["C0805"], desc="buck output")
C("C6", S, "22u", "+3V3", fp=FP["C0805"], desc="buck output")
# 1.2 V core LDO
part("U3", S, "TLV73312PDBV", "TLV73312PDBV", {"1": "+3V3", "3": "+3V3", "2": "GND",
                                                "4": "NC", "5": "+1V2"}, desc="FPGA core 1.2 V LDO")
C("C7", S, "1u", "+3V3", desc="LDO in")
C("C8", S, "1u", "+1V2", desc="LDO out")
# 3.3 V analog LDO for the ADC
part("U4", S, "LP5907MFX-3.3", "LP5907MFX-3.3", {"1": "+5V", "3": "+5V", "2": "GND",
                                                  "4": "NC", "5": "+3.3VA"},
     desc="low-noise ADC supply")
C("C9", S, "1u", "+5V", desc="LDO in")
C("C10", S, "1u", "+3.3VA", desc="LDO out")
# +5 VA op-amp/FDA supply
part("FB1", S, "FerriteBead_Small", "BLM18PG221", {"1": "+5V", "2": "+5VA"}, FP["FB"],
     "analog +5 V filter")
C("C11", S, "10u", "+5VA", fp=FP["C0805"])
C("C12", S, "100n", "+5VA")
# -5 V charge pump + filter
part("U5", S, "TPS60403DBV", "TPS60403DBV", {"2": "+5V", "4": "GND", "5": "CP_FLYP",
                                              "3": "CP_FLYN", "1": "-5V"},
     desc="inverting charge pump, 60 mA")
C("C13", S, "1u", "CP_FLYP", "CP_FLYN", desc="flying cap")
C("C14", S, "1u", "+5V", desc="charge-pump input")
C("C15", S, "4.7u", "-5V", fp=FP["C0805"], desc="charge-pump output")
part("FB2", S, "FerriteBead_Small", "BLM18PG221", {"1": "-5V", "2": "-5VA"}, FP["FB"],
     "analog -5 V filter")
C("C16", S, "4.7u", "-5VA", fp=FP["C0805"])
C("C17", S, "100n", "-5VA")
# power LED
R("R4", S, "1k", "+3V3", "LED_PWR_A")
part("D1", S, "LED", "green", {"2": "LED_PWR_A", "1": "GND"}, FP["LED"], "power LED")
for i in range(1, 5):
    part(f"H{i}", S, "MountingHole", "M3", {}, FP["HOLE"], "mounting hole")


# =====================================================================================
# Sheet "frontend": per channel -- BNC, 1 MOhm || ~13.5 pF compensated 10:1 attenuator,
# BAV99 clamp, OPA810 buffer, THS4521 differential MFB low-pass (f0 3.2 MHz, Q 1) +
# output RC pole -> ~3rd-order Butterworth.  Overall gain 0.0944: +/-10 V -> +/-0.944 V.
# =====================================================================================
S = "frontend"
cref = 100
for ch, base in (("A", 0), ("B", 20)):
    n = lambda k: f"{k}{ch}"
    part(f"J{2 + base // 20}", S, "Conn_Coaxial", "BNC", {"1": n("IN"), "2": "GND"},
         FP["BNC"], f"channel {ch} input (scope-probe compatible)")
    r0 = 10 + base
    R(f"R{r0}", S, "909k 0.1%", n("IN"), n("ATT"), FP["R1206"], "attenuator top")
    C(f"C{cref}", S, "15p C0G 100V", n("IN"), n("ATT"), FP["C0805"], "attenuator top comp")
    R(f"R{r0 + 1}", S, "100k 0.1%", n("ATT"), "GND", desc="attenuator bottom")
    C(f"C{cref + 1}", S, "120p C0G", n("ATT"), "GND", desc="attenuator bottom comp")
    part(f"C{cref + 2}", S, "C_Trim", "5-30p", {"1": n("ATT"), "2": "GND"}, FP["CTRIM"],
         "compensation trim (adjust for flat 1 kHz square wave)")
    part(f"D{2 + base // 20}", S, "BAV99", "BAV99", {"3": n("ATT"), "1": "-5VA", "2": "+5VA"},
         desc="input clamp to analog rails")
    R(f"R{r0 + 2}", S, "1k", n("ATT"), n("BUFIN"), desc="buffer input isolation")
    part(f"U{10 + base // 20}", S, "OPA810xDBV", "OPA810IDBVR",
         {"3": n("BUFIN"), "4": n("BUF"), "1": n("BUF"), "5": "+5VA", "2": "-5VA"},
         desc="FET-input unity-gain buffer")
    C(f"C{cref + 3}", S, "100n", "+5VA")
    C(f"C{cref + 4}", S, "100n", "-5VA")
    # differential MFB around THS4521 (signal leg drives IN-, reference leg from GND)
    R(f"R{r0 + 3}", S, "806", n("BUF"), n("MFBP"), desc="MFB R1 (signal leg)")
    R(f"R{r0 + 4}", S, "768", n("MFBP"), n("FDAOP"), desc="MFB R2 (signal leg)")
    R(f"R{r0 + 5}", S, "147", n("MFBP"), n("FDAINN"), desc="MFB R3 (signal leg)")
    C(f"C{cref + 5}", S, "47p C0G", n("FDAOP"), n("FDAINN"), desc="MFB C2 (signal leg)")
    R(f"R{r0 + 6}", S, "806", "GND", n("MFBN"), desc="MFB R1 (reference leg)")
    R(f"R{r0 + 7}", S, "768", n("MFBN"), n("FDAON"), desc="MFB R2 (reference leg)")
    R(f"R{r0 + 8}", S, "147", n("MFBN"), n("FDAINP"), desc="MFB R3 (reference leg)")
    C(f"C{cref + 6}", S, "47p C0G", n("FDAON"), n("FDAINP"), desc="MFB C2 (reference leg)")
    C(f"C{cref + 7}", S, "220p C0G", n("MFBP"), n("MFBN"), desc="MFB C1 (differential)")
    part(f"U{12 + base // 20}", S, "THS4521IDGK", "THS4521IDGK",
         {"1": n("FDAINN"), "8": n("FDAINP"), "4": n("FDAOP"), "5": n("FDAON"),
          "2": f"VCM{ch}", "3": "+5VA", "6": "GND", "7": "+5VA"},
         desc="fully-differential ADC driver / 2-pole MFB")
    C(f"C{cref + 8}", S, "100n", "+5VA")
    C(f"C{cref + 9}", S, "100n", f"VCM{ch}", desc="VOCM local bypass")
    # output pole; FDA inverts, so OUT- feeds AIN+ to keep overall polarity non-inverting
    R(f"R{r0 + 9}", S, "49.9", n("FDAON"), f"AIN{ch}_P", desc="ADC drive / RC pole")
    R(f"R{r0 + 10}", S, "49.9", n("FDAOP"), f"AIN{ch}_N", desc="ADC drive / RC pole")
    C(f"C{cref + 10}", S, "470p C0G", f"AIN{ch}_P", f"AIN{ch}_N",
      desc="differential RC pole, ~3.4 MHz")
    cref += 20


# =====================================================================================
# Sheet "adc": LTC2290 dual 12-bit 10 Msps, references, 10 MHz low-jitter clock
# =====================================================================================
S = "adc"
adc = {"1": "AINA_P", "2": "AINA_N", "16": "AINB_P", "15": "AINB_N",
       "3": "REFHA", "4": "REFHA", "5": "REFLA", "6": "REFLA",
       "13": "REFHB", "14": "REFHB", "11": "REFLB", "12": "REFLB",
       "7": "+3.3VA", "10": "+3.3VA", "18": "+3.3VA", "63": "+3.3VA",
       "17": "GND", "64": "GND", "65": "GND", "31": "GND", "50": "GND",
       "32": "+3V3", "49": "+3V3",
       "8": "ADC_CLK", "9": "ADC_CLK", "62": "+3.3VA", "19": "+3.3VA",   # SENSE=VDD: 2 Vpp
       "61": "VCMA", "20": "VCMB", "21": "+3.3VA",                         # MUX high: no swap
       "59": "ADC_SHDN", "22": "ADC_SHDN", "58": "GND", "23": "GND", "60": "ADC_MODE",
       "24": "NC", "25": "NC", "41": "NC", "42": "NC",
       "57": "ADC_OFA", "40": "ADC_OFB"}
for i, p in enumerate([43, 44, 45, 46, 47, 48, 51, 52, 53, 54, 55, 56]):
    adc[str(p)] = f"ADC_DA{i}"
for i, p in enumerate([26, 27, 28, 29, 30, 33, 34, 35, 36, 37, 38, 39]):
    adc[str(p)] = f"ADC_DB{i}"
part("U20", S, "LTC2290xUP", "LTC2290CUP", adc, desc="dual 12-bit 10 Msps ADC")
c = decaps(200, S, "+3.3VA", ["100n"] * 4 + ["10u"], "ADC VDD")
c = decaps(c, S, "+3V3", ["100n"] * 2, "ADC OVDD")
for ch in "AB":
    C(f"C{c}", S, "2.2u", f"VCM{ch}", desc="VCM bypass"); c += 1
    C(f"C{c}", S, "2.2u", f"REFH{ch}", f"REFL{ch}", desc="REFH-REFL bypass"); c += 1
    C(f"C{c}", S, "100n", f"REFH{ch}", f"REFL{ch}", desc="REFH-REFL bypass"); c += 1
    C(f"C{c}", S, "100n", f"REFH{ch}", desc="REFH bypass"); c += 1
    C(f"C{c}", S, "100n", f"REFL{ch}", desc="REFL bypass"); c += 1
R("R70", S, "20k", "+3.3VA", "ADC_MODE", desc="MODE = VDD/3: offset binary, DCS on")
R("R71", S, "10k", "ADC_MODE", "GND")
R("R72", S, "10k", "+3V3", "ADC_SHDN", desc="ADC held in shutdown until FPGA enables it")
part("X1", S, "ASE-xxxMHz", "ASE-10.000MHZ", {"1": "+3.3VA", "2": "GND", "3": "OSC10M",
                                               "4": "+3.3VA"},
     desc="10 MHz sample clock (dedicated, low jitter)")
C(f"C{c}", S, "100n", "+3.3VA", desc="oscillator bypass"); c += 1
R("R73", S, "33", "OSC10M", "ADC_CLK", desc="ADC clock series term")
R("R74", S, "33", "OSC10M", "ADC_CLK_FPGA", desc="FPGA copy of sample clock")


# =====================================================================================
# Sheet "fpga": iCE40HX4K-TQ144, SPI config flash, programming header, 50 MHz clock
# =====================================================================================
S = "fpga"
fpga = {}
BANK3 = [1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 15, 16, 17, 18, 19, 20, 22, 23, 24, 25, 26, 28,
         29, 31, 32, 33]
adc_order = (["ADC_OFA"] + [f"ADC_DA{i}" for i in range(11, -1, -1)] + ["ADC_OFB"]
             + [f"ADC_DB{i}" for i in range(11, -1, -1)])
for p, net in zip(BANK3, adc_order):
    fpga[str(p)] = net
fpga["21"] = "ADC_CLK_FPGA"    # GBIN6
fpga["34"] = "ADC_SHDN"
# bank 2: FT232H synchronous FIFO
for p, net in zip([37, 38, 39, 41, 42, 43, 44, 45], [f"FT_D{i}" for i in range(8)]):
    fpga[str(p)] = net
for p, net in zip([47, 48, 49, 55, 56, 60, 61, 62],
                  ["FT_RXFn", "FT_TXEn", "FT_RDn", "FT_WRn", "FT_OEn", "FT_SIWUn",
                   "FT_PWRENn", "FT_AC8"]):
    fpga[str(p)] = net
fpga["52"] = "FT_CLKOUT"       # GBIN4, 60 MHz FIFO clock
fpga["63"] = "LED_D1"
fpga["64"] = "LED_D2"
# bank 1: SDRAM data + control, 50 MHz system clock on GBIN2
BANK1 = [73, 74, 75, 76, 78, 79, 80, 81, 82, 83, 84, 85, 87, 88, 90, 91, 93, 95, 96, 97, 98,
         99, 101, 102, 104, 105, 106, 107]
sd1 = ([f"SD_DQ{i}" for i in range(8)] + ["SD_DQML", "SD_WEn", "SD_CASn", "SD_RASn",
       "SD_CSn", "SD_BA0", "SD_BA1", "SD_CKE", "SD_CLK_SRC", "SD_DQMH"]
       + [f"SD_DQ{i}" for i in range(8, 16)])
for p, net in zip(BANK1, sd1):
    fpga[str(p)] = net
fpga["94"] = "SYS_CLK"         # GBIN2
# bank 0: SDRAM address
BANK0 = [110, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 124, 125, 128, 129, 130,
         134, 135, 136, 137, 138, 139, 141, 142, 143, 144]
for p, net in zip(BANK0, [f"SD_A{i}" for i in range(13)]):
    fpga[str(p)] = net
# config / power
fpga.update({"65": "FPGA_CDONE", "66": "FPGA_CRESETn", "67": "FLASH_MOSI", "68": "FLASH_MISO",
             "70": "FLASH_SCK", "71": "FLASH_CSn", "72": "+3V3", "108": "+3V3", "109": "+3V3",
             "53": "GND", "127": "GND", "54": "VCCPLL0", "126": "VCCPLL1"})
for p in (27, 40, 92, 111):
    fpga[str(p)] = "+1V2"
for p in (6, 30, 46, 57, 89, 100, 123, 131):
    fpga[str(p)] = "+3V3"
for p in (5, 13, 14, 59, 69, 86, 103, 132, 140):
    fpga[str(p)] = "GND"
for p in range(1, 145):          # everything else (NC pins and spare IO) gets a NC flag
    fpga.setdefault(str(p), "NC")
part("U30", S, "ICE40HX4K-TQ144", "ICE40HX4K-TQ144", fpga, desc="FPGA: capture, SDRAM, USB FIFO")
c = 300
c = decaps(c, S, "+1V2", ["100n"] * 4 + ["10u"], "FPGA VCC")
c = decaps(c, S, "+3V3", ["100n"] * 8 + ["10u"], "FPGA VCCIO")
c = decaps(c, S, "+3V3", ["100n"] * 2, "FPGA VCC_SPI / VPP")
for i, net in enumerate(("VCCPLL0", "VCCPLL1")):
    R(f"R{50 + i}", S, "100", "+1V2", net, desc="PLL supply filter")
    C(f"C{c}", S, "10u", net, fp=FP["C0805"], desc="PLL filter"); c += 1
    C(f"C{c}", S, "100n", net, desc="PLL filter"); c += 1
part("U31", S, "W25Q32JVSS", "W25Q32JVSSIQ", {"1": "FLASH_CSn", "2": "FLASH_MISO",
                                               "3": "+3V3", "4": "GND", "5": "FLASH_MOSI",
                                               "6": "FLASH_SCK", "7": "+3V3", "8": "+3V3"},
     desc="FPGA configuration flash (32 Mbit)")
C(f"C{c}", S, "100n", "+3V3", desc="flash bypass"); c += 1
R("R52", S, "10k", "+3V3", "FLASH_CSn", desc="SS_B high at reset -> SPI master boot")
R("R53", S, "10k", "+3V3", "FPGA_CRESETn")
R("R54", S, "10k", "+3V3", "FPGA_CDONE")
part("J4", S, "Conn_02x05_Odd_Even", "PROG", {"1": "+3V3", "2": "GND", "3": "FLASH_SCK",
                                               "4": "FLASH_CSn", "5": "FLASH_MOSI",
                                               "6": "FLASH_MISO", "7": "FPGA_CRESETn",
                                               "8": "FPGA_CDONE", "9": "GND", "10": "GND"},
     FP["HDR"], "SPI flash programming header (iceprog-style)")
part("X2", S, "ASE-xxxMHz", "ASE-50.000MHZ", {"1": "+3V3", "2": "GND", "3": "OSC50M",
                                               "4": "+3V3"}, desc="50 MHz system clock")
C(f"C{c}", S, "100n", "+3V3", desc="oscillator bypass"); c += 1
R("R55", S, "33", "OSC50M", "SYS_CLK")
R("R56", S, "22", "SD_CLK_SRC", "SD_CLK", desc="SDRAM clock series term")
R("R57", S, "1k", "LED_D1", "LED1_A")
part("D4", S, "LED", "green", {"2": "LED1_A", "1": "GND"}, FP["LED"], "status LED 1")
R("R58", S, "1k", "LED_D2", "LED2_A")
part("D5", S, "LED", "yellow", {"2": "LED2_A", "1": "GND"}, FP["LED"], "status LED 2")


# =====================================================================================
# Sheet "sdram": MT48LC16M16A2 256 Mbit (32 MB) -> 1.6 s of 2 x 16-bit samples @10 Msps
# =====================================================================================
S = "sdram"
sd = {"1": "+3V3", "14": "+3V3", "27": "+3V3", "3": "+3V3", "9": "+3V3", "43": "+3V3",
      "49": "+3V3", "28": "GND", "41": "GND", "54": "GND", "6": "GND", "12": "GND",
      "46": "GND", "52": "GND", "40": "NC",
      "15": "SD_DQML", "39": "SD_DQMH", "16": "SD_WEn", "17": "SD_CASn", "18": "SD_RASn",
      "19": "SD_CSn", "20": "SD_BA0", "21": "SD_BA1", "37": "SD_CKE", "38": "SD_CLK"}
for i, p in enumerate([2, 4, 5, 7, 8, 10, 11, 13, 42, 44, 45, 47, 48, 50, 51, 53]):
    sd[str(p)] = f"SD_DQ{i}"
for i, p in enumerate([23, 24, 25, 26, 29, 30, 31, 32, 33, 34, 22, 35, 36]):
    sd[str(p)] = f"SD_A{i}"
part("U40", S, "MT48LC16M16A2TG", "MT48LC16M16A2P-6A", sd, desc="256 Mbit SDR SDRAM capture buffer")
decaps(400, S, "+3V3", ["100n"] * 7 + ["10u"], "SDRAM VDD/VDDQ")


# =====================================================================================
# Sheet "usb": FT232H USB 2.0 HS bridge in 245 synchronous FIFO mode
# =====================================================================================
S = "usb"
ft = {"1": "FT_XI", "2": "FT_XO", "3": "FT_VCCD", "8": "FT_VCCD", "5": "FT_REF",
      "6": "USB_DM", "7": "USB_DP", "12": "+3V3", "24": "+3V3", "46": "+3V3",
      "21": "FT_RXFn", "25": "FT_TXEn", "26": "FT_RDn", "27": "FT_WRn", "28": "FT_SIWUn",
      "29": "FT_CLKOUT", "30": "FT_OEn", "31": "NC", "32": "FT_AC8", "33": "FT_PWRENn",
      "34": "FT_RESETn", "37": "FT_VCCA", "38": "FT_VCORE", "39": "FT_VCCD", "40": "+5V",
      "42": "GND", "43": "FT_EEDATA", "44": "FT_EECLK", "45": "FT_EECS"}
for p in (4, 9, 41, 10, 11, 22, 23, 35, 36, 47, 48):
    ft[str(p)] = "GND"
for i, p in enumerate(range(13, 21)):
    ft[str(p)] = f"FT_D{i}"
part("U50", S, "FT232H", "FT232HL", ft, FP["LQFP48"], "USB 2.0 HS to sync FIFO bridge")
part("Y1", S, "Crystal_GND24", "12MHz 10pF", {"1": "FT_XI", "3": "FT_XO", "2": "GND",
                                              "4": "GND"}, FP["XTAL"], "FT232H crystal")
C("C500", S, "18p", "FT_XI", desc="crystal load")
C("C501", S, "18p", "FT_XO", desc="crystal load")
R("R60", S, "12k 1%", "FT_REF", "GND", desc="FT232H PHY reference")
R("R61", S, "10k", "+3V3", "FT_RESETn")
C("C502", S, "4.7u", "+5V", fp=FP["C0805"], desc="VREGIN")
C("C503", S, "100n", "+5V", desc="VREGIN")
C("C504", S, "4.7u", "FT_VCCD", fp=FP["C0805"], desc="VCCD 3.3 V out")
C("C505", S, "100n", "FT_VCCD", desc="VCCD")
C("C506", S, "100n", "FT_VCCD", desc="VPHY")
C("C507", S, "100n", "FT_VCCD", desc="VPLL")
C("C508", S, "100n", "FT_VCORE", desc="VCCCORE 1.8 V out")
C("C509", S, "100n", "FT_VCCA", desc="VCCA 1.8 V out")
decaps(510, S, "+3V3", ["100n"] * 3, "FT232H VCCIO")
part("U51", S, "93LCxxBxxOT", "93LC56BT-I/OT", {"1": "FT_EEDO", "2": "GND", "3": "FT_EEDATA",
                                                 "4": "FT_EECLK", "5": "FT_EECS", "6": "+3V3"},
     desc="FT232H config EEPROM (sets 245 sync FIFO mode)")
C("C513", S, "100n", "+3V3", desc="EEPROM bypass")
R("R62", S, "2.2k", "FT_EEDO", "FT_EEDATA", desc="EEPROM DO -> EEDATA")
R("R63", S, "10k", "+3V3", "FT_EECS")
R("R64", S, "10k", "+3V3", "FT_EECLK")
R("R65", S, "10k", "+3V3", "FT_EEDATA")

SHEETS = ["power", "frontend", "adc", "fpga", "sdram", "usb"]
SHEET_TITLES = {"power": "USB input and power", "frontend": "Analog front ends (A, B)",
                "adc": "LTC2290 ADC and sample clock", "fpga": "iCE40 FPGA, config, clocks",
                "sdram": "SDRAM capture buffer", "usb": "FT232H USB 2.0 bridge"}


def nets():
    """net -> list of (ref, pin)"""
    out = {}
    for ref, p in PARTS.items():
        for pin, net in p["pins"].items():
            if net != "NC":
                out.setdefault(net, []).append((ref, pin))
    return out


if __name__ == "__main__":
    N = nets()
    print(f"{len(PARTS)} parts, {len(N)} nets")
    for net, nodes in sorted(N.items()):
        if len(nodes) < 2:
            print("SINGLE-PIN NET:", net, nodes)
