"""Netlist for the dual-channel 12-bit 10 MS/s USB ADC board.

Single source of truth for parts and connections. build_schematic.py turns
this into KiCad schematic sheets using the kicad-mcp-server editing tools.

Each part: (ref, lib, symbol, value, footprint, sheet, {pin: net}, nc_pins, unit)
A net of None or a pin listed in nc_pins gets a no-connect marker.
"""

PARTS = []

FP_R0603 = "Resistor_SMD:R_0603_1608Metric"
FP_R0805 = "Resistor_SMD:R_0805_2012Metric"
FP_C0603 = "Capacitor_SMD:C_0603_1608Metric"
FP_C0805 = "Capacitor_SMD:C_0805_2012Metric"
FP_LED = "LED_SMD:LED_0603_1608Metric"
FP_FB = "Inductor_SMD:L_0603_1608Metric"


def part(ref, lib, sym, value, fp, sheet, conns, nc=(), unit=1):
    newrow_flag = bool(PARTS) and PARTS[-1] is None
    if newrow_flag:
        PARTS.pop()
    PARTS.append(dict(newrow=newrow_flag, ref=ref, lib=lib, sym=sym, value=value, fp=fp, sheet=sheet,
                      conns={str(k): v for k, v in conns.items()}, nc=[str(p) for p in nc],
                      unit=unit))


def newrow():
    """Start a new row in the schematic layout at the next part."""
    PARTS.append(None)


def R(ref, value, n1, n2, sheet, fp=FP_R0603):
    part(ref, "Device", "R", value, fp, sheet, {1: n1, 2: n2})


def C(ref, value, n1, n2, sheet, fp=FP_C0603):
    part(ref, "Device", "C", value, fp, sheet, {1: n1, 2: n2})


def FB(ref, value, n1, n2, sheet):
    part(ref, "Device", "FerriteBead_Small", value, FP_FB, sheet, {1: n1, 2: n2})


def LED(ref, value, anode, cathode, sheet):
    part(ref, "Device", "LED", value, FP_LED, sheet, {1: cathode, 2: anode})


# ---------------------------------------------------------------------------
# Power: USB-C (USB 2.0 only), protection, regulators
# ---------------------------------------------------------------------------
S = "power"
part("J1", "Connector", "USB_C_Receptacle_USB2.0_16P", "USB-C (USB 2.0)",
     "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal", S,
     {"A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
      "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "S1": "SHIELD",
      "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DM", "B7": "USB_DM"},
     nc=["A8", "B8"])
R("R1", "5.1k", "CC1", "GND", S)
R("R2", "5.1k", "CC2", "GND", S)
R("R3", "1M", "SHIELD", "GND", S)
C("C1", "4.7nF 100V", "SHIELD", "GND", S)
part("U1", "Power_Protection", "USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6", S,
     {1: "USB_DP", 6: "USB_DP", 3: "USB_DM", 4: "USB_DM", 5: "VBUS", 2: "GND"})
part("F1", "Device", "Polyfuse", "0.75A hold", "Fuse:Fuse_1206_3216Metric", S, {1: "VBUS", 2: "+5V"})
C("C2", "4.7uF", "+5V", "GND", S, FP_C0805)
newrow()
# 3.3 V digital buck (TPS62162: fixed 3.3 V, FB to GND on fixed versions)
part("U2", "Regulator_Switching", "TPS62162DSG", "TPS62162DSGR",
     "Package_SON:WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm_ThermalVias", S,
     {2: "+5V", 3: "+5V", 1: "GND", 4: "GND", 9: "GND", 7: "SW_3V3", 6: "+3V3", 5: "GND"}, nc=[8])
part("L1", "Device", "L", "2.2uH 1.5A", "Inductor_SMD:L_Taiyo-Yuden_NR-30xx", S, {1: "SW_3V3", 2: "+3V3"})
C("C3", "22uF", "+3V3", "GND", S, FP_C0805)
C("C4", "100nF", "+3V3", "GND", S)
# 1.2 V FPGA core
part("U3", "Regulator_Linear", "AP2112K-1.2", "AP2112K-1.2", "Package_TO_SOT_SMD:SOT-23-5", S,
     {1: "+3V3", 3: "+3V3", 2: "GND", 5: "+1V2"}, nc=[4])
C("C5", "1uF", "+3V3", "GND", S)
C("C6", "1uF", "+1V2", "GND", S)
newrow()
# Analog +3.3 V (op amps, FDAs) and +3.0 V (ADC core, oscillator)
part("U4", "Regulator_Linear", "LP5907MFX-3.3", "LP5907MFX-3.3", "Package_TO_SOT_SMD:SOT-23-5", S,
     {1: "+5V", 3: "+5V", 2: "GND", 5: "+3V3A"}, nc=[4])
C("C7", "1uF", "+5V", "GND", S)
C("C8", "1uF", "+3V3A", "GND", S)
part("U5", "Regulator_Linear", "LP5907MFX-3.0", "LP5907MFX-3.0", "Package_TO_SOT_SMD:SOT-23-5", S,
     {1: "+5V", 3: "+5V", 2: "GND", 5: "+3V0A"}, nc=[4])
C("C9", "1uF", "+5V", "GND", S)
C("C10", "1uF", "+3V0A", "GND", S)
newrow()
# Analog -3.3 V: inverting charge pump + negative LDO
# VOUT = -1.22 V * (1 + R4/R5) = -3.28 V  (VERIFY reference value against LM27761 datasheet)
part("U6", "Regulator_SwitchedCapacitor", "LM27761", "LM27761DSGR",
     "Package_SON:WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm", S,
     {1: "+5V", 6: "+5V", 8: "CP_P", 7: "CP_N", 2: "GND", 9: "GND", 3: "CPOUT", 4: "-3V3A", 5: "NFB"})
C("C11", "1uF", "CP_P", "CP_N", S)
C("C12", "2.2uF", "CPOUT", "GND", S)
C("C13", "2.2uF", "-3V3A", "GND", S)
R("R4", "169k 1%", "-3V3A", "NFB", S)
R("R5", "100k 1%", "NFB", "GND", S)
newrow()
R("R6", "1k", "+3V3", "LED_PWR", S)
LED("D1", "green", "LED_PWR", "GND", S)
for i in range(1, 5):
    part(f"H{i}", "Mechanical", "MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", S, {})

# ---------------------------------------------------------------------------
# Analog front ends: BNC, 1 Mohm compensated /10 attenuator, clamp,
# FET-input buffer, single-ended-to-differential ADC driver
# ---------------------------------------------------------------------------
S = "afe"
for n, x in ((1, "A"), (2, "B")):
    b = n * 100
    newrow()
    part(f"J{b + 1}", "Connector", "Conn_Coaxial", f"BNC IN_{x}",
         "Connector_Coaxial:BNC_Amphenol_B6252HB-NPP3G-50_Horizontal", S, {1: f"IN_{x}", 2: "GND"})
    # Shunt C makes total input C ~19 pF so 10x scope probes can be compensated
    C(f"C{b + 1}", "15pF C0G 100V", f"IN_{x}", "GND", S, FP_C0805)
    R(f"R{b + 1}", "453k 0.1%", f"IN_{x}", f"ATT_M_{x}", S, FP_R0805)
    R(f"R{b + 2}", "453k 0.1%", f"ATT_M_{x}", f"ATT_{x}", S, FP_R0805)
    C(f"C{b + 2}", "4.7pF C0G 100V", f"IN_{x}", f"ATT_{x}", S, FP_C0805)
    R(f"R{b + 3}", "100k 0.1%", f"ATT_{x}", "GND", S)
    C(f"C{b + 3}", "30pF C0G", f"ATT_{x}", "GND", S)
    part(f"C{b + 4}", "Device", "C_Trim", "4.5-20pF", "Capacitor_SMD:C_Trimmer_Murata_TZC3", S,
         {1: f"ATT_{x}", 2: "GND"})
    # BAV99: pin1 anode, pin2 cathode, pin3 common
    part(f"D{b + 1}", "Diode", "BAV99", "BAV99", "Package_TO_SOT_SMD:SOT-23", S,
         {3: f"ATT_{x}", 1: "-3V3A", 2: "+3V3A"})
    R(f"R{b + 4}", "1k", f"ATT_{x}", f"BUFIN_{x}", S)
    # OPA810 SOT-23-5: 1 out, 2 V-, 3 +in, 4 -in, 5 V+
    part(f"U{b + 1}", "Amplifier_Operational", "OPA810xDBV", "OPA810IDBVR",
         "Package_TO_SOT_SMD:SOT-23-5", S,
         {3: f"BUFIN_{x}", 4: f"BUF_{x}", 1: f"BUF_{x}", 5: "+3V3A", 2: "-3V3A"})
    C(f"C{b + 5}", "100nF", "+3V3A", "GND", S)
    C(f"C{b + 6}", "100nF", "-3V3A", "GND", S)
    newrow()
    # THS4521: 1 IN-, 2 VOCM, 3 VS+, 4 OUT+, 5 OUT-, 6 VS-, 7 PD, 8 IN+
    # Vod = (Rf/Rg) * V(BUF) ; +/-0.994 V diff for +/-10 V at the BNC
    part(f"U{b + 2}", "Amplifier_Difference", "THS4521IDGK", "THS4521IDGK",
         "Package_SO:VSSOP-8_3x3mm_P0.65mm", S,
         {8: f"FDA_P_{x}", 1: f"FDA_N_{x}", 2: f"VCM_{x}", 3: "+3V3A", 6: "GND", 7: "+3V3A",
          4: f"FOUT_P_{x}", 5: f"FOUT_N_{x}"})
    R(f"R{b + 5}", "1.00k 0.1%", f"BUF_{x}", f"FDA_P_{x}", S)
    R(f"R{b + 6}", "1.00k 0.1%", "GND", f"FDA_N_{x}", S)
    R(f"R{b + 7}", "1.00k 0.1%", f"FOUT_N_{x}", f"FDA_P_{x}", S)
    C(f"C{b + 7}", "22pF C0G", f"FOUT_N_{x}", f"FDA_P_{x}", S)
    R(f"R{b + 8}", "1.00k 0.1%", f"FOUT_P_{x}", f"FDA_N_{x}", S)
    C(f"C{b + 8}", "22pF C0G", f"FOUT_P_{x}", f"FDA_N_{x}", S)
    R(f"R{b + 9}", "49.9", f"FOUT_P_{x}", f"AIN_P_{x}", S)
    R(f"R{b + 10}", "49.9", f"FOUT_N_{x}", f"AIN_N_{x}", S)
    C(f"C{b + 9}", "33pF C0G", f"AIN_P_{x}", f"AIN_N_{x}", S)
    C(f"C{b + 10}", "100nF", "+3V3A", "GND", S)

# ---------------------------------------------------------------------------
# ADC (LTC2290, dual 12-bit 10 MS/s) and sample clock
# ---------------------------------------------------------------------------
S = "adc"
adc = {1: "AIN_P_A", 2: "AIN_N_A", 16: "AIN_P_B", 15: "AIN_N_B",
       3: "REFH_A", 4: "REFH_A", 5: "REFL_A", 6: "REFL_A",
       13: "REFH_B", 14: "REFH_B", 11: "REFL_B", 12: "REFL_B",
       61: "VCM_A", 20: "VCM_B", 62: "+3V0A", 19: "+3V0A",
       8: "CLK_ADC_A", 9: "CLK_ADC_B", 21: "+3V0A", 60: "ADC_MODE",
       7: "+3V0A", 10: "+3V0A", 18: "+3V0A", 63: "+3V0A",
       17: "GND", 64: "GND", 65: "GND", 31: "GND", 50: "GND", 32: "+3V3", 49: "+3V3",
       58: "GND", 23: "GND", 59: "GND", 22: "GND"}
DA_PINS = [43, 44, 45, 46, 47, 48, 51, 52, 53, 54, 55, 56]
DB_PINS = [26, 27, 28, 29, 30, 33, 34, 35, 36, 37, 38, 39]
adc_sigs = []  # (adc pin, net name at FPGA)
for i, p in enumerate(DA_PINS):
    adc_sigs.append((p, f"DA{i}"))
adc_sigs.append((57, "OFA"))
for i, p in enumerate(DB_PINS):
    adc_sigs.append((p, f"DB{i}"))
adc_sigs.append((40, "OFB"))
for p, net in adc_sigs:
    adc[p] = f"{net}_S"
part("U301", "Analog_ADC", "LTC2290xUP", "LTC2290CUP",
     "Package_DFN_QFN:QFN-64-1EP_9x9mm_P0.5mm_EP7.15x7.15mm", S, adc, nc=[24, 25, 41, 42])
newrow()
# 33 ohm series resistor packs on the ADC outputs (reduce digital kickback)
for k in range(7):
    conns, nc = {}, []
    for slot in range(4):
        idx = 4 * k + slot
        if idx < len(adc_sigs):
            net = adc_sigs[idx][1]
            conns[slot + 1] = f"{net}_S"
            conns[8 - slot] = net
        else:
            nc += [slot + 1, 8 - slot]
    part(f"RN{301 + k}", "Device", "R_Pack04", "4x33", "Resistor_SMD:R_Array_Convex_4x0603", S, conns, nc)
newrow()
for i in range(4):
    C(f"C{301 + i}", "100nF", "+3V0A", "GND", S)
C("C305", "10uF", "+3V0A", "GND", S, FP_C0805)
C("C306", "100nF", "+3V3", "GND", S)
C("C307", "100nF", "+3V3", "GND", S)
for x, c0 in (("A", 308), ("B", 312)):
    C(f"C{c0}", "2.2uF", f"REFH_{x}", f"REFL_{x}", S)
    C(f"C{c0 + 1}", "100nF", f"REFH_{x}", f"REFL_{x}", S)
    C(f"C{c0 + 2}", "1uF", f"REFH_{x}", "GND", S)
    C(f"C{c0 + 3}", "1uF", f"REFL_{x}", "GND", S)
C("C316", "2.2uF", "VCM_A", "GND", S)
C("C317", "2.2uF", "VCM_B", "GND", S)
# MODE = 2/3 VDD -> two's complement output, clock duty-cycle stabilizer on
R("R301", "10k", "+3V0A", "ADC_MODE", S)
R("R302", "20k", "ADC_MODE", "GND", S)
newrow()
# 10 MHz low-jitter sample clock, powered from the clean 3.0 V analog rail
part("Y301", "Oscillator", "ASE-xxxMHz", "ASE-10.000MHZ-LC-T",
     "Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm", S,
     {1: "OSC_VDD", 4: "OSC_VDD", 2: "GND", 3: "OSC_OUT"})
FB("FB301", "600R@100MHz", "+3V0A", "OSC_VDD", S)
C("C318", "100nF", "OSC_VDD", "GND", S)
C("C319", "1uF", "OSC_VDD", "GND", S)
R("R303", "33", "OSC_OUT", "CLK_ADC_A", S)
R("R304", "33", "OSC_OUT", "CLK_ADC_B", S)
R("R305", "33", "OSC_OUT", "CLK10M", S)

# ---------------------------------------------------------------------------
# FPGA (iCE40HX4K-TQ144), SDRAM capture buffer, configuration flash
# ---------------------------------------------------------------------------
S = "fpga"
BANK3 = [1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 28, 29, 31, 32, 33, 34]
BANK0 = [110, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 124, 125, 128, 129, 130,
         134, 135, 136, 137, 138, 139, 141, 142, 143, 144]
BANK1 = [73, 74, 75, 76, 78, 79, 80, 81, 82, 83, 84, 85, 87, 88, 90, 91, 93, 94, 95, 96, 97, 98,
         99, 101, 102, 104, 105, 106, 107]
BANK2 = [37, 38, 39, 41, 42, 43, 44, 45, 47, 48, 49, 52, 55, 56, 60, 61, 62, 63, 64]

fpga = {}
bank3_sigs = [net for _, net in adc_sigs]  # 26 ADC lines
for p, net in zip(BANK3, bank3_sigs + [None, None]):
    fpga[p] = net
bank0_sigs = [f"SD_DQ{i}" for i in range(16)] + [f"SD_A{i}" for i in range(11)]
for p, net in zip(BANK0, bank0_sigs):
    fpga[p] = net
bank1_sigs = ["SD_A11", "SD_A12", "SD_BA0", "SD_BA1", "SD_DQML", "SD_DQMH", "SD_CSn", "SD_RASn",
              "SD_CASn", "SD_WEn", "SD_CKE", "SD_CLK_FPGA",
              "FT_D0", "FT_D1", "FT_D2", "FT_D3", "FT_CLKOUT", "FT_D4", "FT_D5", "FT_D6", "FT_D7",
              "FT_RXFn", "FT_TXEn", "FT_RDn", "FT_WRn", "FT_OEn", "FT_SIWU", "LED1", "LED2"]
for p, net in zip(BANK1, bank1_sigs):
    fpga[p] = net
assert fpga[93] == "FT_CLKOUT"  # 60 MHz FIFO clock on a global buffer input (GBIN3)
bank2_sigs = ["GPIO0", "GPIO1", "GPIO2", "GPIO3", "GPIO4", "GPIO5"] + [None] * 4 + ["CLK10M"] + [None] * 8
for p, net in zip(BANK2, bank2_sigs):
    fpga[p] = net
assert fpga[49] == "CLK10M"  # sample clock on GBIN5
fpga.update({67: "FLASH_MOSI", 68: "FLASH_MISO", 70: "FLASH_SCK", 71: "FLASH_CSn",
             66: "FPGA_CRESETn", 65: "FPGA_CDONE",
             27: "+1V2", 40: "+1V2", 92: "+1V2", 111: "+1V2",
             123: "+3V3", 131: "+3V3", 89: "+3V3", 100: "+3V3", 46: "+3V3", 57: "+3V3",
             6: "+3V3", 30: "+3V3", 72: "+3V3", 108: "+3V3",
             54: "VCCPLL0", 53: "GND", 126: "VCCPLL1", 127: "GND"})
for p in (5, 13, 14, 59, 69, 86, 103, 132, 140):
    fpga[p] = "GND"
FPGA_NC = [109, 35, 36, 50, 51, 58, 77, 133]
# iCE40 symbol has 5 units; the pin->unit split is taken from the library by the builder.
part("U401", "FPGA_Lattice", "ICE40HX4K-TQ144", "ICE40HX4K-TQ144", "Package_QFP:TQFP-144_20x20mm_P0.5mm",
     S, fpga, nc=FPGA_NC)
newrow()
# PLL supply filters (Lattice hardware checklist style RC filter)
R("R401", "100", "+1V2", "VCCPLL0", S)
C("C401", "10uF", "VCCPLL0", "GND", S, FP_C0805)
C("C402", "100nF", "VCCPLL0", "GND", S)
R("R402", "100", "+1V2", "VCCPLL1", S)
C("C403", "10uF", "VCCPLL1", "GND", S, FP_C0805)
C("C404", "100nF", "VCCPLL1", "GND", S)
for i in range(4):
    C(f"C{405 + i}", "100nF", "+1V2", "GND", S)
C("C409", "10uF", "+1V2", "GND", S, FP_C0805)
for i in range(8):
    C(f"C{410 + i}", "100nF", "+3V3", "GND", S)
C("C418", "10uF", "+3V3", "GND", S, FP_C0805)
C("C419", "100nF", "+3V3", "GND", S)
R("R403", "10k", "+3V3", "FPGA_CRESETn", S)
R("R404", "10k", "+3V3", "FPGA_CDONE", S)
R("R405", "10k", "+3V3", "FLASH_CSn", S)
newrow()
part("U403", "Memory_Flash", "W25Q32JVSS", "W25Q32JVSSIQ", "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm", S,
     {1: "FLASH_CSn", 6: "FLASH_SCK", 5: "FLASH_MOSI", 2: "FLASH_MISO", 3: "FLASH_WPn",
      7: "FLASH_HOLDn", 8: "+3V3", 4: "GND"})
R("R406", "10k", "+3V3", "FLASH_WPn", S)
R("R407", "10k", "+3V3", "FLASH_HOLDn", S)
C("C420", "100nF", "+3V3", "GND", S)
newrow()
# 32 MB SDR SDRAM capture buffer (0.1 s x 2 ch x 10 MS/s x 2 B = 4 MB needed)
sd = {20: "SD_BA0", 21: "SD_BA1", 19: "SD_CSn", 37: "SD_CKE", 38: "SD_CLK", 15: "SD_DQML", 39: "SD_DQMH",
      16: "SD_WEn", 17: "SD_CASn", 18: "SD_RASn"}
for i, p in enumerate([23, 24, 25, 26, 29, 30, 31, 32, 33, 34, 22, 35, 36]):
    sd[p] = f"SD_A{i}"
for i, p in enumerate([2, 4, 5, 7, 8, 10, 11, 13, 42, 44, 45, 47, 48, 50, 51, 53]):
    sd[p] = f"SD_DQ{i}"
for p in (1, 14, 27, 3, 9, 43, 49):
    sd[p] = "+3V3"
for p in (28, 41, 54, 6, 12, 46, 52):
    sd[p] = "GND"
part("U402", "Memory_RAM", "MT48LC16M16A2TG", "MT48LC16M16A2TG-6A", "Package_SO:TSOP-II-54_22.2x10.16mm_P0.8mm",
     S, sd, nc=[40])
R("R408", "22", "SD_CLK_FPGA", "SD_CLK", S)
for i in range(7):
    C(f"C{421 + i}", "100nF", "+3V3", "GND", S)
C("C428", "10uF", "+3V3", "GND", S, FP_C0805)
newrow()
R("R409", "1k", "LED1", "LED1_A", S)
LED("D401", "green", "LED1_A", "GND", S)
R("R410", "1k", "LED2", "LED2_A", S)
LED("D402", "yellow", "LED2_A", "GND", S)
part("J401", "Connector_Generic", "Conn_01x08", "GPIO / trigger",
     "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", S,
     {1: "+3V3", 2: "GPIO0", 3: "GPIO1", 4: "GPIO2", 5: "GPIO3", 6: "GPIO4", 7: "GPIO5", 8: "GND"})

# ---------------------------------------------------------------------------
# USB interface: FT2232H. Channel A = 245 synchronous FIFO to the FPGA
# (sample upload); channel B = MPSSE for SPI-flash programming / FPGA reset.
# ---------------------------------------------------------------------------
S = "usb"
ft = {50: "+3V3", 49: "+1V8_FT", 12: "+1V8_FT", 37: "+1V8_FT", 64: "+1V8_FT", 4: "VPHY", 9: "VPLL",
      20: "+3V3", 31: "+3V3", 42: "+3V3", 56: "+3V3", 10: "GND",
      7: "USB_DM", 8: "USB_DP", 6: "FT_REF", 14: "FT_RESETn", 13: "GND",
      63: "EE_CS", 62: "EE_CLK", 61: "EE_DATA", 2: "XTAL_I", 3: "XTAL_O",
      26: "FT_RXFn", 27: "FT_TXEn", 28: "FT_RDn", 29: "FT_WRn", 30: "FT_SIWU", 32: "FT_CLKOUT", 33: "FT_OEn",
      38: "FLASH_SCK", 39: "FLASH_MOSI", 40: "FLASH_MISO", 43: "FLASH_CSn", 45: "FPGA_CDONE",
      46: "FPGA_CRESETn"}
for p in (1, 5, 11, 15, 25, 35, 47, 51):
    ft[p] = "GND"
for i, p in enumerate([16, 17, 18, 19, 21, 22, 23, 24]):
    ft[p] = f"FT_D{i}"
part("U501", "Interface_USB", "FT2232HL", "FT2232HL", "Package_QFP:LQFP-64_10x10mm_P0.5mm", S, ft,
     nc=[34, 41, 44, 48, 52, 53, 54, 55, 57, 58, 59, 60, 36])
newrow()
R("R501", "12k 1%", "FT_REF", "GND", S)
R("R502", "10k", "+3V3", "FT_RESETn", S)
part("U502", "Memory_EEPROM", "93LCxxB", "93LC56BT-I/SN", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", S,
     {1: "EE_CS", 2: "EE_CLK", 3: "EE_DATA", 4: "EE_DO", 8: "+3V3", 5: "GND"}, nc=[6, 7])
R("R503", "2.2k", "EE_DO", "EE_DATA", S)
R("R504", "10k", "+3V3", "EE_CS", S)
R("R505", "10k", "+3V3", "EE_CLK", S)
R("R506", "10k", "+3V3", "EE_DATA", S)
C("C501", "100nF", "+3V3", "GND", S)
newrow()
part("Y501", "Device", "Crystal_GND24", "12MHz", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", S,
     {1: "XTAL_I", 3: "XTAL_O", 2: "GND", 4: "GND"})
C("C502", "27pF", "XTAL_I", "GND", S)
C("C503", "27pF", "XTAL_O", "GND", S)
FB("FB501", "600R@100MHz", "+3V3", "VPHY", S)
C("C504", "4.7uF", "VPHY", "GND", S)
C("C505", "100nF", "VPHY", "GND", S)
FB("FB502", "600R@100MHz", "+3V3", "VPLL", S)
C("C506", "4.7uF", "VPLL", "GND", S)
C("C507", "100nF", "VPLL", "GND", S)
C("C508", "4.7uF", "+1V8_FT", "GND", S)
for i in range(3):
    C(f"C{509 + i}", "100nF", "+1V8_FT", "GND", S)
C("C512", "4.7uF", "+3V3", "GND", S)
for i in range(4):
    C(f"C{513 + i}", "100nF", "+3V3", "GND", S)

SHEETS = [
    ("power", "Power: USB-C input, regulators"),
    ("afe", "Analog front ends (A, B)"),
    ("adc", "ADC and sample clock"),
    ("fpga", "FPGA, SDRAM, config flash"),
    ("usb", "USB 2.0 interface (FT2232H)"),
]
