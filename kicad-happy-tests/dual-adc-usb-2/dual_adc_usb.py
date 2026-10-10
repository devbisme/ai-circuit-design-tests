"""
Dual-channel 12-bit / 10 MSPS USB data-acquisition board (SKiDL source).

Signal chain per channel:
  BNC (1 MOhm || ~20 pF, scope-probe compatible) -> /10 compensated attenuator
  -> clamp -> OPA810 unity buffer (+/-3.3 V) -> THS4521 FDA (G = 0.953, SE->diff,
  VOCM = ADC VCM) -> RC anti-alias -> LTC2291 (dual 12 b, 2 Vpp span).
Digital: LTC2291 -> iCE40HX4K (capture, SDRAM controller) -> IS42S16400J
  (8 MB = 0.2 s of 2 x 10 MSPS x 16 b) -> FT2232H channel B async FIFO -> USB 2.0 HS.
  FT2232H channel A (MPSSE) programs the iCE40 config flash (iceprog-compatible).
Power: USB VBUS 5 V -> TLV62569 buck 3.3 V (digital), AP2112 1.2 V (FPGA core),
  LP5907 3.3 V (ADC + FDA), LM27762 +/-3.3 V (input buffers).

See design_decisions.md for the option lists and rationale.
"""

import json
import os
import re
import skidl
from skidl import *

HERE = os.path.dirname(os.path.abspath(__file__))
set_default_tool(KICAD10)
lib_search_paths[KICAD10] = [os.path.join(HERE, "lib")]

# ----------------------------------------------------------------------------
# Footprints & helpers
# ----------------------------------------------------------------------------
FP_R = "Resistor_SMD:R_0603_1608Metric"
FP_R_HV = "Resistor_SMD:R_1206_3216Metric"
FP_C = "Capacitor_SMD:C_0603_1608Metric"
FP_C_BULK = "Capacitor_SMD:C_0805_2012Metric"
FP_C_HV = "Capacitor_SMD:C_1206_3216Metric"
FP_LED = "LED_SMD:LED_0603_1608Metric"
FP_FB = "Inductor_SMD:L_0603_1608Metric"


def resistor_mpn(v, tol, fp):
    """Yageo thick-film (1%) / thin-film (0.1%) part number for a resistor value."""
    code = v.upper().replace("R", "")
    m = re.match(r"^([0-9.]+)([KM]?)$", code)
    mant, mult = m.group(1), m.group(2)
    mant = mant.replace(".", mult or "R") if "." in mant else mant + (mult or "R")
    size = "1206" if "1206" in fp else "0603"
    return (f"RT{size}BRD07{mant}L" if tol == "0.1%" else f"RC{size}FR-07{mant}L")


# Murata part numbers (generic suggestions; check voltage rating/derating at order time).
CAP_MPN = {
    ("100nF", "0603"): "GRM188R71C104KA01D",
    ("1uF", "0603"): "GRM188R71C105KA12D",
    ("2.2uF", "0603"): "GRM188R61C225KE15D",
    ("2.2uF", "0805"): "GRM21BR71C225KA12L",
    ("4.7uF", "0805"): "GRM21BR71C475KE51L",
    ("10uF", "0805"): "GRM21BR61C106KE15L",
    ("22uF", "0805"): "GRM21BR61A226ME44L",
    ("27pF", "0603"): "GRM1885C1H270JA01D",
    ("22pF", "0603"): "GRM1885C1H220JA01D",
    ("10pF", "0603"): "GRM1885C1H100JA01D",
    ("330pF", "0603"): "GRM1885C1H331JA01D",
    ("6.8pF", "0603"): "GRM1885C1H6R8DA01D",
    ("15pF", "1206"): "GRM3195C2A150JA01D",
    ("2.2pF", "1206"): "GRM3195C2A2R2CA01D",
    ("4.7nF", "1206"): "GRM31BR72J472KW01L",
}


def R(value, fp=FP_R, **kw):
    """Resistor. 'value' may carry a tolerance, e.g. "953 0.1%" -> value 953, Tolerance 0.1%."""
    v, *tol = value.split()
    r = Part("Device", "R", value=v, footprint=fp, **kw)
    r.Tolerance = tol[0] if tol else "1%"
    r.MPN = resistor_mpn(v, r.Tolerance, fp)
    return r


def C(value, fp=FP_C, **kw):
    """Capacitor. 'value' may carry a dielectric, e.g. "22pF C0G"."""
    v, *diel = value.split()
    c = Part("Device", "C", value=v, footprint=fp, **kw)
    c.Dielectric = diel[0] if diel else ("C0G" if v.endswith("pF") else "X7R")
    c.MPN = CAP_MPN.get((v, re.search(r":C_(\d{4})_", fp).group(1)), "")
    # Murata GRM code: chars 7-8 give the temperature characteristic (R7=X7R, R6=X5R, 5C=C0G).
    if c.MPN.startswith("GRM"):
        c.Dielectric = {"R7": "X7R", "R6": "X5R", "5C": "C0G"}.get(c.MPN[6:8], c.Dielectric)
    return c


def bypass(rail, gnd, *values):
    """Hang one capacitor per value between rail and gnd."""
    for v in values:
        fp = FP_C_BULK if v in ("4.7uF", "10uF", "22uF") else FP_C
        c = C(v, fp)
        c[1] += rail
        c[2] += gnd


def pwr_flag(*nets):
    """Mark nets fed through passives (ferrites, filters) as driven, for ERC."""
    for n in nets:
        Part("power", "PWR_FLAG")[1] += n


def _empty_fp(part):
    if not part.ref.startswith("#"):
        raise ValueError(f"No footprint for {part.ref}")


skidl.empty_footprint_handler = _empty_fp


def ic(lib, name, fp, mpn, value=None, **kw):
    p = Part(lib, name, footprint=fp, **kw)
    p.MPN = mpn
    if value:
        p.value = value
    return p


# ----------------------------------------------------------------------------
# Global nets
# ----------------------------------------------------------------------------
gnd = Net("GND")
vbus = Net("VBUS")
p5v = Net("+5V")
p3v3 = Net("+3V3")
p1v2 = Net("+1V2")
p3v3_adc = Net("+3V3_ADC")
p3v3a = Net("+3V3A")
n3v3a = Net("-3V3A")

for n in (gnd, vbus, p5v, p3v3, p1v2, p3v3_adc, p3v3a, n3v3a):
    n.drive = POWER
    n.stub = True  # drawn as power symbols / labels, not wires


# ----------------------------------------------------------------------------
# USB connector, protection, FT2232H, EEPROM
# ----------------------------------------------------------------------------
@subcircuit
def usb_interface(vbus, p3v3, gnd, fifo_d, fifo_ctl, spi, ft_gpio):
    """USB-B connector -> FT2232HL. Ch A = MPSSE (flash prog), Ch B = 245 async FIFO."""
    j = Part("Connector", "USB_B", footprint="Connector_USB:USB_B_OST_USB-B1HSxx_Horizontal")
    j.MPN = "USB-B1HSW6"
    dp, dm = Net("USB_DP"), Net("USB_DM")
    j["VBUS"] += vbus
    j["D+"] += dp
    j["D-"] += dm
    j["GND"] += gnd
    # Shield: bleed to GND through 1M || 4.7nF (keeps cable shield ESD off signal ground DC path).
    shield = Net("USB_SHIELD")
    j["Shield"] += shield
    r = R("1M")
    r[1, 2] += shield, gnd
    c = C("4.7nF", FP_C_HV)
    c[1, 2] += shield, gnd

    esd = ic("Power_Protection", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6", "USBLC6-2SC6")
    esd[1] += dp  # I/O1
    esd[6] += dp
    esd[3] += dm  # I/O2
    esd[4] += dm
    esd[5] += vbus
    esd[2] += gnd

    ft = ic("Interface_USB", "FT2232HL", "Package_QFP:LQFP-64_10x10mm_P0.5mm", "FT2232HL-REEL")
    ft["DP"] += dp
    ft["DM"] += dm
    for pin in ("VCCIO", "VREGIN"):
        ft[pin] += p3v3
    ft["GND"] += gnd
    ft["AGND"] += gnd
    ft["TEST"] += gnd

    # VPHY / VPLL: filtered 3.3 V.
    vphy = Net("FT_VPHY")
    fb = Part("Device", "FerriteBead_Small", value="600R@100MHz", footprint=FP_FB)
    fb.MPN = "BLM18KG601SN1D"
    fb[1, 2] += p3v3, vphy
    ft["VPHY"] += vphy
    ft["VPLL"] += vphy
    pwr_flag(vphy)
    bypass(vphy, gnd, "4.7uF", "100nF", "100nF")

    # 1.8 V core from internal regulator.
    vcore = Net("FT_VCORE")
    ft["VREGOUT"] += vcore
    ft["VCORE"] += vcore
    bypass(vcore, gnd, "4.7uF", "100nF", "100nF", "100nF")
    bypass(p3v3, gnd, "4.7uF", "100nF", "100nF", "100nF", "100nF", "100nF")

    # REF: 12k 1% to GND.
    rref = R("12k 1%")
    rref[1, 2] += ft["REF"], gnd

    # Reset pulled up.
    rrst = R("10k")
    rrst[1, 2] += p3v3, ft["~{RESET}"]

    # 12 MHz crystal.
    xtal = ic("Device", "Crystal_GND24", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
              "ABM8-12.000MHZ-B2-T", value="12MHz")
    xi, xo = Net("FT_OSCI"), Net("FT_OSCO")
    xtal[1] += xi
    xtal[3] += xo
    xtal[2] += gnd
    xtal[4] += gnd
    ft["OSCI"] += xi
    ft["OSCO"] += xo
    for n in (xi, xo):
        c = C("27pF")
        c[1, 2] += n, gnd

    # 93LC56B EEPROM (16-bit org) - stores channel B = 245 FIFO configuration.
    ee = ic("Memory_EEPROM", "93LCxxB", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
            "93LC56BT-I/SN", value="93LC56B")
    eecs, eeclk, eedata = Net("FT_EECS"), Net("FT_EECLK"), Net("FT_EEDATA")
    ft["EECS"] += eecs
    ft["EECLK"] += eeclk
    ft["EEDATA"] += eedata
    ee["CS"] += eecs
    ee["SCLK"] += eeclk
    ee["DO"] += eedata
    rdi = R("2.2k")
    rdi[1, 2] += eedata, ee["DI"]
    ee["VCC"] += p3v3
    ee["GND"] += gnd
    ee["NC"] += NC
    for n in (eecs, eeclk, eedata):
        rp = R("10k")
        rp[1, 2] += p3v3, n
    bypass(p3v3, gnd, "100nF")

    # Channel A: MPSSE SPI to config flash + FPGA reset/done (iceprog pinout).
    ft["ADBUS0"] += spi["sck"]
    ft["ADBUS1"] += spi["mosi"]  # FT -> flash DI
    ft["ADBUS2"] += spi["miso"]  # flash DO -> FT
    ft["ADBUS4"] += spi["cs"]
    ft["ADBUS6"] += spi["cdone"]
    ft["ADBUS7"] += spi["creset"]
    ft["ADBUS3"] += NC
    ft["ADBUS5"] += NC
    for i in range(8):
        if i < 4:
            ft[f"ACBUS{i}"] += ft_gpio[i]  # spare GPIOH0-3 to FPGA
        else:
            ft[f"ACBUS{i}"] += NC

    # Channel B: 245 async FIFO.
    for i in range(8):
        ft[f"BDBUS{i}"] += fifo_d[i]
    ft["BCBUS0"] += fifo_ctl["rxf_n"]
    ft["BCBUS1"] += fifo_ctl["txe_n"]
    ft["BCBUS2"] += fifo_ctl["rd_n"]
    ft["BCBUS3"] += fifo_ctl["wr_n"]
    ft["BCBUS4"] += fifo_ctl["siwu_n"]
    for i in (5, 6, 7):
        ft[f"BCBUS{i}"] += NC
    ft["~{PWREN}"] += fifo_ctl["pwren_n"]
    ft["~{SUSPEND}"] += fifo_ctl["suspend_n"]
    rpw = R("10k")
    rpw[1, 2] += p3v3, fifo_ctl["pwren_n"]
    # SIWU must idle high.
    rsi = R("10k")
    rsi[1, 2] += p3v3, fifo_ctl["siwu_n"]


# ----------------------------------------------------------------------------
# Power
# ----------------------------------------------------------------------------
@subcircuit
def power(vbus, p5v, p3v3, p1v2, p3v3_adc, p3v3a, n3v3a, gnd, ana_en, ana_pg_n):
    # VBUS -> polyfuse -> ferrite -> +5V
    f = ic("Device", "Polyfuse", "Fuse:Fuse_1206_3216Metric", "MF-MSMF050-2", value="500mA")
    vf = Net("VBUS_F")
    f[1, 2] += vbus, vf
    fb = Part("Device", "FerriteBead_Small", value="120R@100MHz 2A",
              footprint="Inductor_SMD:L_0805_2012Metric")
    fb.MPN = "BLM21PG121SN1D"
    fb[1, 2] += vf, p5v
    # Total +5V capacitance kept < 10 uF (USB 2.0 inrush rule).
    bypass(p5v, gnd, "100nF")
    pwr_flag(p5v)

    # 3.3 V digital: TLV62569 buck. Vout = 0.6*(1+453k/100k) = 3.318 V
    u = ic("Regulator_Switching", "TLV62569DBV", "Package_TO_SOT_SMD:SOT-23-5", "TLV62569DBVR")
    u["VIN"] += p5v
    u["EN"] += p5v
    u["GND"] += gnd
    sw = Net("BUCK_SW")
    fbn = Net("BUCK_FB")
    u["SW"] += sw
    u["FB"] += fbn
    l = ic("Device", "L", "Inductor_SMD:L_Changjiang_FNR4020S", "FNR4020S2R2MT", value="2.2uH")
    l[1, 2] += sw, p3v3
    r1, r2 = R("453k 1%"), R("100k 1%")
    r1[1, 2] += p3v3, fbn
    r2[1, 2] += fbn, gnd
    cff = C("6.8pF")
    cff[1, 2] += p3v3, fbn
    pwr_flag(p3v3)  # buck output comes through L1 (passive)
    bypass(p5v, gnd, "4.7uF")
    bypass(p3v3, gnd, "22uF", "100nF")

    # 1.2 V FPGA core: AP2112K-1.2 from 3.3 V.
    u = ic("Regulator_Linear", "AP2112K-1.2", "Package_TO_SOT_SMD:SOT-23-5", "AP2112K-1.2TRG1")
    u["VIN"] += p3v3
    u["EN"] += p3v3
    u["GND"] += gnd
    u["VOUT"] += p1v2
    u["NC"] += NC
    bypass(p1v2, gnd, "10uF")
    bypass(p3v3, gnd, "1uF")

    # 3.3 V ADC / FDA supply: LP5907 low-noise LDO from +5V.
    u = ic("Regulator_Linear", "LP5907MFX-3.3", "Package_TO_SOT_SMD:SOT-23-5", "LP5907MFX-3.3/NOPB")
    u["IN"] += p5v
    u["EN"] += p5v
    u["GND"] += gnd
    u["OUT"] += p3v3_adc
    u["NC"] += NC
    bypass(p5v, gnd, "1uF")
    bypass(p3v3_adc, gnd, "10uF")

    # +/-3.3 V buffer rails: LM27762, enabled by FPGA (default off via pull-down).
    u = ic("Regulator_SwitchedCapacitor", "LM27762", "Package_SON:WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65_ThermalVias",
           "LM27762DSSR")
    u["VIN"] += p5v
    u["GND"] += gnd
    u["PAD"] += gnd
    u["EN+"] += ana_en
    u["EN-"] += ana_en
    rpd = R("100k")
    rpd[1, 2] += ana_en, gnd
    u["PGOOD"] += ana_pg_n
    rpu = R("10k")
    rpu[1, 2] += p3v3, ana_pg_n
    c1p, c1n = Net("CP_C1P"), Net("CP_C1N")
    u["C+"] += c1p
    u["C-"] += c1n
    cfly = C("1uF")
    cfly[1, 2] += c1p, c1n
    cp = Net("CP_OUT")
    u["CP"] += cp
    bypass(cp, gnd, "4.7uF")
    u["OUT+"] += p3v3a
    u["OUT-"] += n3v3a
    fbp, fbm = Net("LDOP_FB"), Net("LDON_FB")
    u["FB+"] += fbp
    u["FB-"] += fbm
    # +Vout = 1.2*(R1+R2)/R2 = 1.2*(174k+100k)/100k = 3.288 V
    r1, r2 = R("174k 1%"), R("100k 1%")
    r1[1, 2] += p3v3a, fbp
    r2[1, 2] += fbp, gnd
    # -Vout = -1.22*(R3+R4)/R4 = -1.22*(169k+100k)/100k = -3.282 V
    r3, r4 = R("169k 1%"), R("100k 1%")
    r3[1, 2] += n3v3a, fbm
    r4[1, 2] += fbm, gnd
    bypass(p5v, gnd, "2.2uF")
    bypass(p3v3a, gnd, "2.2uF")
    bypass(n3v3a, gnd, "2.2uF")

    # Power-on indicator.
    led = ic("Device", "LED", FP_LED, "LTST-C191KGKT", value="GRN")
    rl = R("1k")
    rl[1, 2] += p3v3, led["A"]
    led["K"] += gnd


# ----------------------------------------------------------------------------
# Analog front end (one per channel)
# ----------------------------------------------------------------------------
@subcircuit
def front_end(ch, ain_p, ain_n, vcm, p3v3a, n3v3a, p3v3_adc, gnd):
    """BNC -> 1M/10 attenuator -> clamp -> OPA810 buffer -> THS4521 FDA -> RC -> ADC."""
    j = ic("Connector", "Conn_Coaxial", "Connector_Coaxial:BNC_Amphenol_B6252HB-NPP3G-50_Horizontal",
           "B6252HB-NPP3G-50", value=f"IN_{ch}")
    vin = Net(f"VIN_{ch}")
    att = Net(f"ATT_{ch}")
    j["In"] += vin
    j["Ext"] += gnd

    # Shunt C sets total input capacitance ~20 pF (inside common scope-probe compensation range).
    cin = C("15pF C0G", FP_C_HV)
    cin[1, 2] += vin, gnd

    # Compensated /10 attenuator, Rin = 1.009 Mohm.
    rt = R("909k 0.1%", FP_R_HV)
    rt[1, 2] += vin, att
    ct = C("2.2pF C0G", FP_C_HV)
    ct[1, 2] += vin, att
    rb = R("100k 0.1%")
    rb[1, 2] += att, gnd
    cb = C("10pF C0G")
    cb[1, 2] += att, gnd
    ctrim = ic("Device", "C_Trim", "Capacitor_SMD:C_Trimmer_Murata_TZC3", "TZC3Z100A110R00",
               value="3-10pF")
    ctrim[1, 2] += att, gnd

    # Clamp to buffer rails (fault current limited by 909k).
    d = ic("Diode", "BAV99", "Package_TO_SOT_SMD:SOT-23", "BAV99")
    d[1] += n3v3a  # anode D1
    d[3] += att  # common
    d[2] += p3v3a  # cathode D2

    # Unity-gain FET-input buffer.
    buf_in = Net(f"BUF_IN_{ch}")
    buf_out = Net(f"BUF_OUT_{ch}")
    rs = R("100")
    rs[1, 2] += att, buf_in
    op = ic("Amplifier_Operational", "OPA810xD", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "OPA810IDR")
    op["+"] += buf_in
    op["-"] += buf_out
    op[6] += buf_out
    op["V+"] += p3v3a
    op["V-"] += n3v3a
    op["NC"] += NC
    bypass(p3v3a, gnd, "100nF", "1uF")
    bypass(n3v3a, gnd, "100nF", "1uF")

    # FDA: single-ended -> differential, G = Rf/Rg = 953/1000, VOCM from ADC VCM.
    fda = ic("Amplifier_Difference", "THS4521ID", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "THS4521IDR")
    sum_p, sum_n = Net(f"FDA_INP_{ch}"), Net(f"FDA_INN_{ch}")
    out_p, out_n = Net(f"FDA_OUTP_{ch}"), Net(f"FDA_OUTN_{ch}")
    fda[8] += sum_p  # VIN+
    fda[1] += sum_n  # VIN-
    fda[4] += out_p  # VOUT+
    fda[5] += out_n  # VOUT-
    fda[2] += vcm  # VOCM
    fda[3] += p3v3_adc
    fda[6] += gnd
    fda[7] += p3v3_adc  # PD high = enabled
    rg1, rg2 = R("1k 0.1%"), R("1k 0.1%")
    rg1[1, 2] += buf_out, sum_p
    rg2[1, 2] += gnd, sum_n
    rf1, rf2 = R("953 0.1%"), R("953 0.1%")
    rf1[1, 2] += sum_p, out_n
    rf2[1, 2] += sum_n, out_p
    cf1, cf2 = C("22pF C0G"), C("22pF C0G")
    cf1[1, 2] += sum_p, out_n
    cf2[1, 2] += sum_n, out_p
    bypass(p3v3_adc, gnd, "100nF", "1uF")

    # Anti-alias RC: 2 x 49.9R + 330 pF diff -> fc ~ 4.8 MHz.
    ra1, ra2 = R("49.9"), R("49.9")
    ra1[1, 2] += out_p, ain_p
    ra2[1, 2] += out_n, ain_n
    caa = C("330pF C0G")
    caa[1, 2] += ain_p, ain_n


# ----------------------------------------------------------------------------
# ADC
# ----------------------------------------------------------------------------
@subcircuit
def adc(ain, vcm, da, db, ofa, ofb, adc_clk, shdn, p3v3_adc, p3v3, gnd):
    u = ic("Analog_ADC", "LTC2291xUP", "Package_DFN_QFN:QFN-64-1EP_9x9mm_P0.5mm_EP7.15x7.15mm",
           "LTC2291IUP#PBF", value="LTC2291IUP")
    u["AINA+"] += ain["ap"]
    u["AINA-"] += ain["an"]
    u["AINB+"] += ain["bp"]
    u["AINB-"] += ain["bn"]
    u["VCMA"] += vcm["a"]
    u["VCMB"] += vcm["b"]
    bypass(vcm["a"], gnd, "2.2uF")
    bypass(vcm["b"], gnd, "2.2uF")

    # References: REFH-REFL 0.1u + 2.2u, each to GND 1u.
    for ch in "AB":
        rh, rl = Net(f"REFH{ch}"), Net(f"REFL{ch}")
        u[f"REFH{ch}"] += rh
        u[f"REFL{ch}"] += rl
        for v in ("100nF", "2.2uF"):
            c = C(v, FP_C_BULK if v == "2.2uF" else FP_C)
            c[1, 2] += rh, rl
        bypass(rh, gnd, "1uF")
        bypass(rl, gnd, "1uF")

    u["VDD"] += p3v3_adc
    bypass(p3v3_adc, gnd, "100nF", "100nF", "100nF", "100nF", "10uF")
    u["GND"] += gnd
    u["OVDD"] += p3v3
    u["OGND"] += gnd
    bypass(p3v3, gnd, "100nF", "100nF")

    # SENSE = VDD -> internal ref, 2 Vpp differential span.
    u["SENSEA"] += p3v3_adc
    u["SENSEB"] += p3v3_adc
    # MUX = VDD -> ch A on DA bus, ch B on DB bus.
    u["MUX"] += p3v3_adc
    # MODE = VDD/3 -> offset binary, clock duty-cycle stabilizer on.
    mode = Net("ADC_MODE")
    u["MODE"] += mode
    rm1, rm2 = R("20k"), R("10k")
    rm1[1, 2] += p3v3_adc, mode
    rm2[1, 2] += mode, gnd
    # Outputs always enabled; shutdown under FPGA control (pull-down = running).
    u["~{OEA}"] += gnd
    u["~{OEB}"] += gnd
    u["SHDNA"] += shdn
    u["SHDNB"] += shdn
    rsd = R("10k")
    rsd[1, 2] += shdn, gnd
    u["CLKA"] += adc_clk
    u["CLKB"] += adc_clk
    u["NC"] += NC

    for i in range(12):
        u[f"DA{i}"] += da[i]
        u[f"DB{i}"] += db[i]
    u["OFA"] += ofa
    u["OFB"] += ofb


# ----------------------------------------------------------------------------
# Clocks
# ----------------------------------------------------------------------------
@subcircuit
def clocks(adc_clk, fpga_adc_clk, sysclk, p3v3, gnd):
    # 10 MHz low-jitter sample clock: XO -> 22R -> ADC CLKA/B, XO -> 33R -> FPGA.
    xo = ic("Oscillator", "ASE-xxxMHz", "Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm",
            "ASE-10.000MHZ-LC-T", value="10MHz")
    raw = Net("XO10_OUT")
    xo["Vdd"] += p3v3
    xo["EN"] += p3v3
    xo["GND"] += gnd
    xo["OUT"] += raw
    r1, r2 = R("22"), R("33")
    r1[1, 2] += raw, adc_clk
    r2[1, 2] += raw, fpga_adc_clk
    bypass(p3v3, gnd, "100nF")

    # 25 MHz FPGA system clock (PLL ref -> 100 MHz SDRAM clock).
    xo = ic("Oscillator", "ASE-xxxMHz", "Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm",
            "ASE-25.000MHZ-LC-T", value="25MHz")
    raw = Net("XO25_OUT")
    xo["Vdd"] += p3v3
    xo["EN"] += p3v3
    xo["GND"] += gnd
    xo["OUT"] += raw
    r = R("33")
    r[1, 2] += raw, sysclk
    bypass(p3v3, gnd, "100nF")


# ----------------------------------------------------------------------------
# SDRAM
# ----------------------------------------------------------------------------
@subcircuit
def sdram(sd, p3v3, gnd):
    u = ic("Memory_RAM", "IS42S16400J-xT", "Package_SO:TSOP-II-54_22.2x10.16mm_P0.8mm",
           "IS42S16400J-7TL", value="IS42S16400J-7TL")
    for i in range(16):
        u[f"DQ{i}"] += sd["dq"][i]
    for i in range(12):
        u[f"A{i}"] += sd["a"][i]
    u["BA0"] += sd["ba"][0]
    u["BA1"] += sd["ba"][1]
    for pin, key in (("LDQM", "dqml"), ("UDQM", "dqmh"), ("~{CS}", "cs_n"), ("~{RAS}", "ras_n"),
                     ("~{CAS}", "cas_n"), ("~{WE}", "we_n"), ("CKE", "cke"), ("CLK", "clk")):
        u[pin] += sd[key]
    u["VDD"] += p3v3
    u["VDDQ"] += p3v3
    u["GND"] += gnd
    u["GNDQ"] += gnd
    u["NC"] += NC
    bypass(p3v3, gnd, *(["100nF"] * 7), "10uF")


# ----------------------------------------------------------------------------
# FPGA + configuration flash + status LEDs + expansion header
# ----------------------------------------------------------------------------
# Bank allocation (TQ144): bank 3 (left) = ADC, bank 1 (right) + top-right of bank 0 = SDRAM,
# bank 2 (bottom) = FT2232H FIFO/control + clocks, rest of bank 0 = LEDs/GPIO.
BANK3_ADC = [1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 15, 16, 17, 18, 19, 20, 22, 23, 24, 25, 26,
             28, 29, 31, 32, 33, 34]  # 27 pins (21 = GBIN6 reserved for ADC clock)
BANK1_SDRAM = [73, 74, 75, 76, 78, 79, 80, 81, 82, 83, 84, 85, 87, 88, 90, 91, 93, 94, 95,
               96, 97, 98, 99, 101, 102, 104, 105, 106, 107]  # 29 pins
BANK0_SDRAM = [110, 112, 113, 114, 115, 116, 117, 118, 119]  # 9 pins
BANK0_MISC = [120, 121, 122, 124, 125, 128, 129, 130, 134, 135, 136, 137, 138, 139, 141, 142, 143, 144]
BANK2_IO = [37, 38, 39, 41, 42, 43, 44, 45, 47, 48, 52, 55, 56, 60, 61, 62, 63, 64]  # 49 = GBIN5 sysclk


@subcircuit
def fpga(adc_bus, fifo_d, fifo_ctl, spi, ft_gpio, sd, fpga_adc_clk, sysclk, ctl, p3v3, p1v2, gnd):
    u = ic("FPGA_Lattice", "ICE40HX4K-TQ144", "Package_QFP:TQFP-144_20x20mm_P0.5mm", "ICE40HX4K-TQ144")

    # Supplies.
    u["VCC"] += p1v2
    for b in range(4):
        u[f"VCCIO_{b}"] += p3v3
    u["VCC_SPI"] += p3v3
    u["VPP_2V5"] += p3v3  # 3.3 V allowed for controller-SPI config (FPGA-TN-02006 Table 2.1)
    u["VPP_FAST"] += NC  # leave unconnected (FPGA-TN-02006 note 4)
    u["GND"] += gnd
    bypass(p1v2, gnd, "100nF", "100nF", "100nF", "100nF", "10uF")
    bypass(p3v3, gnd, *(["100nF"] * 8), "10uF", "10uF")

    # PLL supplies: 100R + 10u + 100n filter, GNDPLL isolated from board GND (FPGA-TN-02052 Fig 5.4).
    for i in (0, 1):
        vp, gp = Net(f"VCCPLL{i}"), Net(f"GNDPLL{i}")
        u[f"VCCPLL{i}"] += vp
        u[f"GNDPLL{i}"] += gp
        r = R("100")
        r[1, 2] += p1v2, vp
        c1, c2 = C("10uF", FP_C_BULK), C("100nF")
        c1[1, 2] += vp, gp
        c2[1, 2] += vp, gp
        pwr_flag(vp, gp)

    # Configuration (controller SPI from flash; FT2232H ch A can take over for programming).
    u["CDONE"] += spi["cdone"]
    u["~{CRESET}"] += spi["creset"]
    u["IOB_107_SCK"] += spi["sck"]
    u["IOB_105_SDO"] += spi["mosi"]  # FPGA out -> flash DI
    u["IOB_106_SDI"] += spi["miso"]  # flash DO -> FPGA in
    u["IOB_108_SS"] += spi["cs"]
    for n in (spi["cdone"], spi["creset"], spi["sck"], spi["cs"]):
        r = R("10k")
        r[1, 2] += p3v3, n

    fl = ic("Memory_Flash", "W25Q32JVSS", "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm", "W25Q32JVSSIQ")
    fl["~{CS}"] += spi["cs"]
    fl["CLK"] += spi["sck"]
    fl["DI/IO_{0}"] += spi["mosi"]
    fl["DO/IO_{1}"] += spi["miso"]
    wp, hold = Net("FLASH_WP_N"), Net("FLASH_HOLD_N")
    fl["~{WP}/IO_{2}"] += wp
    fl["~{HOLD}/~{RESET}/IO_{3}"] += hold
    for n in (wp, hold):
        r = R("10k")
        r[1, 2] += p3v3, n
    fl["VCC"] += p3v3
    fl["GND"] += gnd
    bypass(p3v3, gnd, "100nF")

    # Clocks.
    u.p[21] += fpga_adc_clk  # GBIN6, bank 3 (ADC capture domain)
    u.p[49] += sysclk  # GBIN5, bank 2 (PLL -> SDRAM)

    # Default pin assignment by bank; scripts/pin_swap.py may override it (fpga_pinmap.json) to
    # match the PCB placement and minimise bus crossings.
    adc_sigs = adc_bus["da"][:] + [adc_bus["ofa"]] + adc_bus["db"][:] + [adc_bus["ofb"]] + [ctl["adc_shdn"]]
    sd_sigs = (sd["dq"][:] + [sd["dqml"], sd["dqmh"], sd["we_n"], sd["cas_n"], sd["ras_n"], sd["cs_n"],
               sd["ba"][0], sd["ba"][1], sd["cke"], sd["clk"]] + sd["a"][:])
    b2_sigs = (fifo_d[:] + [fifo_ctl[k] for k in ("rxf_n", "txe_n", "rd_n", "wr_n", "siwu_n",
                                                    "pwren_n", "suspend_n")]
               + [ctl["ana_en"], ctl["ana_pg_n"]])
    groups = [(BANK3_ADC, adc_sigs), (BANK1_SDRAM + BANK0_SDRAM, sd_sigs), (BANK2_IO, b2_sigs)]
    pinmap_file = os.path.join(HERE, "fpga_pinmap.json")
    pinmap = json.load(open(pinmap_file)) if os.path.exists(pinmap_file) else {}
    for pins, sigs in groups:
        assign = dict(zip(sigs, pins))
        if pinmap:
            assign = {sig: int(pinmap[sig.name]) for sig in sigs}
        for sig, pin in assign.items():
            u.p[pin] += sig
        for pin in set(pins) - set(assign.values()):
            u.p[pin] += NC

    # Bank 0: LEDs, FT ACBUS GPIO, expansion header.
    leds = [Net("LED0"), Net("LED1")]
    hdr = [Net(f"GPIO{i}") for i in range(8)]
    b0 = leds + ft_gpio[:] + hdr
    for pin, sig in zip(BANK0_MISC, b0):
        u.p[pin] += sig
    for pin in BANK0_MISC[len(b0):]:
        u.p[pin] += NC
    for n in (35, 36, 50, 51, 58, 77, 133):
        u.p[n] += NC

    for i, n in enumerate(leds):
        led = ic("Device", "LED", FP_LED, "LTST-C191KRKT", value="RED")
        r = R("1k")
        r[1, 2] += n, led["A"]
        led["K"] += gnd

    # Expansion / debug header: 8 GPIO + 3V3 + GND.
    j = ic("Connector_Generic", "Conn_02x05_Odd_Even", "Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical",
           "", value="GPIO")
    j.MPN = "61301021121"
    for i in range(8):
        j[i + 1] += hdr[i]
    j[9] += p3v3
    j[10] += gnd


# ----------------------------------------------------------------------------
# Top level
# ----------------------------------------------------------------------------
@subcircuit
def dual_adc_usb():
    fifo_d = Bus("FT_D", 8)
    fifo_ctl = {k: Net(f"FT_{k.upper()}") for k in ("rxf_n", "txe_n", "rd_n", "wr_n", "siwu_n",
                                                     "pwren_n", "suspend_n")}
    spi = {k: Net(f"CFG_{k.upper()}") for k in ("sck", "mosi", "miso", "cs", "cdone", "creset")}
    ft_gpio = Bus("FT_ACBUS", 4)
    ctl = {k: Net(k.upper()) for k in ("adc_shdn", "ana_en", "ana_pg_n")}
    ain = {k: Net(f"AIN_{k[0].upper()}{'P' if k[1] == 'p' else 'N'}") for k in ("ap", "an", "bp", "bn")}
    vcm = {"a": Net("VCMA"), "b": Net("VCMB")}
    adc_bus = {"da": Bus("DA", 12), "db": Bus("DB", 12), "ofa": Net("OFA"), "ofb": Net("OFB")}
    adc_clk, fpga_adc_clk, sysclk = Net("ADC_CLK"), Net("FPGA_ADC_CLK"), Net("SYSCLK")
    sd = {"dq": Bus("SD_DQ", 16), "a": Bus("SD_A", 12), "ba": Bus("SD_BA", 2)}
    sd.update({k: Net(f"SD_{k.upper()}") for k in ("dqml", "dqmh", "cs_n", "ras_n", "cas_n", "we_n",
                                                    "cke", "clk")})

    power(vbus, p5v, p3v3, p1v2, p3v3_adc, p3v3a, n3v3a, gnd, ctl["ana_en"], ctl["ana_pg_n"])
    usb_interface(vbus, p3v3, gnd, fifo_d, fifo_ctl, spi, ft_gpio)
    front_end("A", ain["ap"], ain["an"], vcm["a"], p3v3a, n3v3a, p3v3_adc, gnd)
    front_end("B", ain["bp"], ain["bn"], vcm["b"], p3v3a, n3v3a, p3v3_adc, gnd)
    adc(ain, vcm, adc_bus["da"], adc_bus["db"], adc_bus["ofa"], adc_bus["ofb"], adc_clk,
        ctl["adc_shdn"], p3v3_adc, p3v3, gnd)
    clocks(adc_clk, fpga_adc_clk, sysclk, p3v3, gnd)
    sdram(sd, p3v3, gnd)
    fpga(adc_bus, fifo_d, fifo_ctl, spi, ft_gpio, sd, fpga_adc_clk, sysclk, ctl, p3v3, p1v2, gnd)


if __name__ == "__main__":
    import sys

    dual_adc_usb()
    ERC()
    generate_netlist(file_=os.path.join(HERE, "dual_adc_usb_skidl.net"))
    if "--schematizer" in sys.argv:
        # SKiDL's own schematic generator (see design_decisions.md: output failed connectivity check).
        generate_schematic(filepath=os.path.join(HERE, "schematizer_out"), top_name="dual_adc_usb",
                           tool=KICAD10, auto_stub=True)
    if "--sch" in sys.argv:
        import builtins

        sys.path.insert(0, os.path.join(HERE, "scripts"))
        from sch_writer import write_schematic

        kdir = os.path.join(HERE, "kicad")
        write_schematic(builtins.default_circuit, kdir, "dual_adc_usb",
                        os.path.join(HERE, "lib"), title="Dual 12-bit 10 MSPS USB ADC")
        # Project symbol library table -> the flattened libraries in ../lib.
        libs = sorted(f[:-10] for f in os.listdir(os.path.join(HERE, "lib")) if f.endswith(".kicad_sym"))
        with open(os.path.join(kdir, "sym-lib-table"), "w") as fh:
            fh.write("(sym_lib_table\n  (version 7)\n")
            for l in libs:
                fh.write(f'  (lib (name "{l}")(type "KiCad")(uri "${{KIPRJMOD}}/../lib/{l}.kicad_sym")(options "")(descr ""))\n')
            fh.write(")\n")
