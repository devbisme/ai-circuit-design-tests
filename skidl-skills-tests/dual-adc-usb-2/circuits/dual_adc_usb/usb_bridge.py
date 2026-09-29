"""USB Bridge -- FT232H USB2-HS Synchronous FIFO Bridge
Block from: architecture/block_diagram.md
Interface nets: VBUS, V3V3_D, GND, USB_DP, USB_DM, FIFO_D[7:0], FIFO_RXF_N, FIFO_TXE_N,
    FIFO_RD_N, FIFO_WR_N, FIFO_OE_N, CLK60, PWREN_N
"""
from skidl import *


@subcircuit
def usb_bridge(vbus, v3v3_d, gnd, usb_dp, usb_dm, fifo_data, rxf_n, txe_n, rd_n, wr_n,
                oe_n, clk60, pwren_n):
    """FT232HL USB 2.0 Hi-Speed bridge, configured (via the U7 EEPROM image) for FT245
    synchronous FIFO mode at 60 MHz (architecture decision A3: FT2232H's second channel
    is provably dead weight per FTDI AN_130 -- sync-FIFO mode only works on channel A --
    so the single-channel FT232H is used instead).

    U6 ADBUS0-7 form the 8-bit FIFO data bus; ACBUS0/1/2/3/5/6/9 carry the FT245 sync-FIFO
    handshake + clock-out + PWREN# housekeeping signals (net_plan.md Sec.7/9). ACBUS4
    (SIWU) and ACBUS7 (PWRSAV#) are unused GPIOs, each tied high with its own pull-up per
    net_plan.md Sec.7. ACBUS8 is likewise unused by the FIFO protocol and is repurposed
    here as a firmware-readable VBUS-sense GPIO (see Decisions in the block handoff --
    the FT232H has no dedicated hardware VBUS-sense pin, unlike FT232R).

    Y1 (12 MHz crystal) sets the FT232H's internal USB/FIFO PLL reference -- independent
    of the ADC sample-clock domain (X1/clock_gen), by design. U7 (93LC46B) is the
    Microwire configuration EEPROM that stores the FT245-sync-FIFO + PWREN# image FTDI's
    FT_PROG utility programs at manufacturing test.

    Args:
        vbus: raw 5 V USB bus supply (from J1, upstream of F1/regulators in other blocks)
              -- consumed here only by the R14/R15 VBUS-sense divider into U6 ACBUS8
        v3v3_d: 3.3 V digital rail (from U1 AP7361C-33E) -- U6 VCCIO/VCCD/VREGIN (via FB
              to VPHY/VPLL), U7 VCC, and all pull-ups in this block
        gnd: ground reference
        usb_dp: USB2 HS D+ (already passed through J1 -> FB1 -> D1 ESD clamp upstream,
              in usb_c_input) -- connects straight to U6 DP
        usb_dm: USB2 HS D- -- connects straight to U6 DM
        fifo_data: 8-bit SKiDL Bus, U6 ADBUS0-7 <-> U9 (FPGA) bank 1 I/O
        rxf_n: FT232H -> FPGA, low = host data available to read (U6 ACBUS0)
        txe_n: FT232H -> FPGA, low = FIFO has space to accept a write (U6 ACBUS1)
        rd_n: FPGA -> FT232H, read strobe (U6 ACBUS2)
        wr_n: FPGA -> FT232H, write strobe (U6 ACBUS3)
        oe_n: FPGA -> FT232H, output-enable / bus-turnaround (U6 ACBUS6)
        clk60: FT232H -> FPGA, 60.000 MHz FIFO clock out (U6 ACBUS5 CLKOUT)
        pwren_n: FT232H -> rest of board, open-drain active-low power-enable gate (U6
              ACBUS9, EEPROM-configured as PWREN#) -- drives Q1/U3/U4 enables elsewhere
    """

    # ------------------------------------------------------------------
    # U6 -- FT232HL USB 2.0 Hi-Speed / FT245 sync-FIFO bridge (LQFP-48)
    # ------------------------------------------------------------------
    u6 = Part(
        "Interface_USB",
        "FT232H",
        ref="U6",
        value="FT232HL",
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm",
    )

    # --- USB D+/D- (already ESD-clamped upstream in usb_c_input) ---
    u6["DP"] += usb_dp
    u6["DM"] += usb_dm

    # --- FT245 synchronous FIFO data bus (ADBUS0-7 <-> FPGA) ---
    u6["ADBUS0"] += fifo_data[0]
    u6["ADBUS1"] += fifo_data[1]
    u6["ADBUS2"] += fifo_data[2]
    u6["ADBUS3"] += fifo_data[3]
    u6["ADBUS4"] += fifo_data[4]
    u6["ADBUS5"] += fifo_data[5]
    u6["ADBUS6"] += fifo_data[6]
    u6["ADBUS7"] += fifo_data[7]

    # --- FT245 sync-FIFO handshake / clock / power-enable (ACBUS0-9) ---
    u6["ACBUS0"] += rxf_n      # RXF#    (FT232H -> FPGA, status)
    u6["ACBUS1"] += txe_n      # TXE#    (FT232H -> FPGA, status)
    u6["ACBUS2"] += rd_n       # RD#     (FPGA -> FT232H, strobe)
    u6["ACBUS3"] += wr_n       # WR#     (FPGA -> FT232H, strobe)
    u6["ACBUS5"] += clk60      # CLKOUT  (FT232H -> FPGA, 60.000 MHz)
    u6["ACBUS6"] += oe_n       # OE#     (FPGA -> FT232H, bus turnaround)
    u6["ACBUS9"] += pwren_n    # PWREN#  (FT232H -> board, EEPROM-configured GPIO)

    # ACBUS4 (SIWU) and ACBUS7 (PWRSAV#) are unused by the sync-FIFO protocol in this
    # design; net_plan.md Sec.7 calls for each to get its own 10 k pull-up to V3V3_D
    # (R18, R19) so they idle high rather than float.
    siwu_pullup_node = Net("FT_SIWU_N")
    u6["ACBUS4"] += siwu_pullup_node
    r18 = Part("Device", "R", ref="R18", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r18[1] += v3v3_d
    r18[2] += siwu_pullup_node

    pwrsav_pullup_node = Net("FT_PWRSAV_N")
    u6["ACBUS7"] += pwrsav_pullup_node
    r19 = Part("Device", "R", ref="R19", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r19[1] += v3v3_d
    r19[2] += pwrsav_pullup_node

    # ACBUS8 is likewise unused by the sync-FIFO protocol. net_plan.md Sec.1/9 calls for
    # a VBUS-sense divider (R14/R15, nominal 2.5 V at 5.0 V VBUS) into "U6 VBUS_SENSE" --
    # but the real FT232H (and this KiCad symbol) has no dedicated hardware VBUS pin
    # (unlike FT232R). Repurposing the spare ACBUS8 GPIO as a firmware-read VBUS-sense
    # input reaches the same design intent without inventing a pin that doesn't exist.
    # See block handoff Decisions for the full reasoning.
    vbus_sense = Net("FT_VBUS_SENSE")
    u6["ACBUS8"] += vbus_sense
    r14 = Part("Device", "R", ref="R14", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r15 = Part("Device", "R", ref="R15", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r14[1] += vbus
    r14[2] += vbus_sense
    r15[1] += vbus_sense
    r15[2] += gnd

    # --- Reset (~RESET, pin 34): pull-up only, no external reset control in this design ---
    ft_reset_n = Net("FT_RESET_N")
    u6["~{RESET}"] += ft_reset_n
    r16 = Part("Device", "R", ref="R16", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r16[1] += v3v3_d
    r16[2] += ft_reset_n

    # --- REF bias (pin 5): mandatory 12.0 k to GND -- board will not enumerate without it ---
    r13 = Part("Device", "R", ref="R13", value="12.0k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    u6["REF"] += r13[1]
    r13[2] += gnd

    # --- TEST (pin 42): tie to GND for normal operation ---
    u6["TEST"] += gnd

    # --- EEPROM Microwire interface (shared with U7, 93LC46B) ---
    ee_cs = Net("EE_CS")
    ee_sk = Net("EE_SK")
    ee_data = Net("EE_DATA")   # shared EEDATA (U6) <-> DI+DO (U7), half-duplex on U6 side
    u6["EECS"] += ee_cs
    u6["EECLK"] += ee_sk
    u6["EEDATA"] += ee_data
    r17 = Part("Device", "R", ref="R17", value="2.2k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r17[1] += v3v3_d
    r17[2] += ee_data

    # --- Crystal oscillator (Y1, 12 MHz, sets USB/FIFO PLL reference only) ---
    xtal_a = Net("FT_OSCI")
    xtal_b = Net("FT_OSCO")
    u6["XCSI"] += xtal_a
    u6["XCSO"] += xtal_b

    y1 = Part(
        "Device",
        "Crystal",
        ref="Y1",
        value="X322512MSB4SI",
        footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    )
    y1[1] += xtal_a
    y1[2] += xtal_b

    c25 = Part("Device", "C", ref="C25", value="27pF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c25[1] += xtal_a
    c25[2] += gnd

    c26 = Part("Device", "C", ref="C26", value="27pF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c26[1] += xtal_b
    c26[2] += gnd

    # ------------------------------------------------------------------
    # Power distribution + decoupling (net_plan.md Sec.9/10, FT232HL summary Notes)
    # ------------------------------------------------------------------
    # VCCD, VREGIN, and all 3 VCCIO pins tie directly to the 3.3 V digital rail per the
    # FTDI reference design ("tie VREGIN to VCCIO"). VPHY/VPLL are internally-regulated
    # analog/PLL nodes fed from V3V3_D through isolation ferrites (FB5 -> VPHY, FB4 ->
    # VPLL, per sourced BOM "FB4, FB5 | VPLL / VPHY isolation ferrites"). VCCA/VCCCORE
    # are the chip's internal 1.8 V regulator OUTPUTS -- decoupled only, never driven.
    # They are TWO SEPARATE regulator outputs (datasheets/FT232HL_SUMMARY.md pins 37/38:
    # VCCA = 1.8 V PHY-analog regulator output, VCCCORE = 1.8 V core regulator output),
    # so they get separate nets and separate decoupling. They were originally shorted onto
    # one FT_VCORE_1V8 net; that both tripped an ERC POWER-OUT/POWER-OUT conflict and was
    # electrically wrong -- shorting two independent LDO outputs makes them fight and
    # couples USB PHY noise straight into the core rail.
    u6["VCCD"] += v3v3_d
    u6["VREGIN"] += v3v3_d
    u6["VCCIO"] += v3v3_d   # pins 12, 24, 46 all alias to the same VCCIO pin name

    vphy_net = Net("FT_VPHY")
    vpll_net = Net("FT_VPLL")
    u6["VPHY"] += vphy_net
    u6["VPLL"] += vpll_net

    fb5 = Part("Device", "FerriteBead", ref="FB5", value="BLM18PG601SN1D",
               footprint="Inductor_SMD:L_0603_1608Metric")
    fb5[1] += v3v3_d
    fb5[2] += vphy_net

    fb4 = Part("Device", "FerriteBead", ref="FB4", value="BLM18PG601SN1D",
               footprint="Inductor_SMD:L_0603_1608Metric")
    fb4[1] += v3v3_d
    fb4[2] += vpll_net

    ft_vcca = Net("FT_VCCA_1V8")     # PHY-analog 1.8 V regulator output
    ft_vcore = Net("FT_VCORE_1V8")   # core 1.8 V regulator output
    u6["VCCA"] += ft_vcca
    u6["VCCCORE"] += ft_vcore

    # AGND/GND pins all tie to the single global ground net.
    u6["AGND"] += gnd   # pins 4, 9, 41 alias to the same AGND pin name
    u6["GND"] += gnd    # pins 10, 11, 22, 23, 35, 36, 47, 48 alias to the same GND pin name

    # 100 nF per supply pin (C27-C34, per FT232HL summary "Full 48-pin decoupling" note):
    # VPHY, VPLL, 3x VCCIO, VCCD, VREGIN, plus U7's VCC pin (shares this decoupling group
    # per the 93LC46B summary).
    c27 = Part("Device", "C", ref="C27", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c27[1] += vphy_net
    c27[2] += gnd

    c28 = Part("Device", "C", ref="C28", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c28[1] += vpll_net
    c28[2] += gnd

    c29 = Part("Device", "C", ref="C29", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c29[1] += v3v3_d   # local bypass at VCCIO pin 12
    c29[2] += gnd

    c30 = Part("Device", "C", ref="C30", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c30[1] += v3v3_d   # local bypass at VCCIO pin 24
    c30[2] += gnd

    c31 = Part("Device", "C", ref="C31", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c31[1] += v3v3_d   # local bypass at VCCIO pin 46
    c31[2] += gnd

    c32 = Part("Device", "C", ref="C32", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c32[1] += v3v3_d   # local bypass at VCCD
    c32[2] += gnd

    c33 = Part("Device", "C", ref="C33", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c33[1] += v3v3_d   # local bypass at VREGIN
    c33[2] += gnd

    c34 = Part("Device", "C", ref="C34", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c34[1] += v3v3_d   # local bypass at U7 (93LC46B) VCC pin
    c34[2] += gnd

    # 1 uF on each internal 1.8 V regulator output -- C35 on VCCA, C36 on VCCCORE.
    # One cap per rail (NOT two on a shared node): each output must be decoupled
    # independently, per datasheets/FT232HL_SUMMARY.md.
    c35 = Part("Device", "C", ref="C35", value="1uF",
               footprint="Capacitor_SMD:C_0603_1608Metric")
    c35[1] += ft_vcca
    c35[2] += gnd

    c36 = Part("Device", "C", ref="C36", value="1uF",
               footprint="Capacitor_SMD:C_0603_1608Metric")
    c36[1] += ft_vcore
    c36[2] += gnd

    # Bulk caps: C37 (4.7 uF) on V3V3_D at U6, C38 (4.7 uF) on the 1.8 V core rail,
    # C39 (10 uF) bulk on V3V3_D, C40 (100 nF) extra bypass on V3V3_D.
    c37 = Part("Device", "C", ref="C37", value="4.7uF",
               footprint="Capacitor_SMD:C_0805_2012Metric")
    c37[1] += v3v3_d
    c37[2] += gnd

    c38 = Part("Device", "C", ref="C38", value="4.7uF",
               footprint="Capacitor_SMD:C_0805_2012Metric")
    c38[1] += ft_vcore
    c38[2] += gnd

    c39 = Part("Device", "C", ref="C39", value="10uF",
               footprint="Capacitor_SMD:C_0805_2012Metric")
    c39[1] += v3v3_d
    c39[2] += gnd

    c40 = Part("Device", "C", ref="C40", value="100nF",
               footprint="Capacitor_SMD:C_0402_1005Metric")
    c40[1] += v3v3_d
    c40[2] += gnd

    # ------------------------------------------------------------------
    # U7 -- 93LC46B Microwire configuration EEPROM (SOT-23-6)
    # Stores the FT_PROG image: FT245 sync-FIFO mode + ACBUS9=PWREN#.
    # ------------------------------------------------------------------
    u7 = Part(
        "Memory_EEPROM",
        "93CxxC",
        ref="U7",
        value="93LC46BT-I/OT",
        footprint="Package_TO_SOT_SMD:SOT-23-6",
    )
    u7["CS"] += ee_cs
    u7["SCLK"] += ee_sk
    u7["DI"] += ee_data     # DI and DO both tie to U6's single shared EEDATA line
    u7["DO"] += ee_data
    u7["GND"] += gnd
    u7["VCC"] += v3v3_d
    # ORG tied to VCC selects x16 organization -- the FTDI-recommended configuration for
    # the FT232H EEPROM programming utility (decision DS5 in datasheets handoff).
    u7["ORG"] += v3v3_d
    u7["NC"] += NC   # pin 7, not internally bonded
