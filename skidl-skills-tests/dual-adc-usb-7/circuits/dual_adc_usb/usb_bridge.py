"""USB Bridge — USB-C receptacle + ESD array + FT232HL + config EEPROM
Block from: architecture/block_diagram.md
Interface nets: VBUS, FT_3V3, FIFO_D[0:7], FIFO_RXF_N, FIFO_TXE_N, FIFO_RD_N,
                FIFO_WR_N, FIFO_OE_N, FIFO_CLK60, PWREN_N, GND
"""
from skidl import *


@SubCircuit
def usb_bridge(vbus, ft_3v3, fifo_d, rxf_n, txe_n, rd_n, wr_n, oe_n,
               fifo_clk60, pwren_n, gnd):
    """USB 2.0 Hi-Speed host link: USB-C receptacle -> ESD array -> FT232HL in
    245 synchronous-FIFO mode, with the 93LC56B configuration EEPROM.

    Inputs (consumed):
        vbus       -- 5 V from the USB-C receptacle's VBUS pins. DRIVEN by this
                      block (J4 is the source), but the assembler owns the
                      `.drive = POWER` assignment at top level.
    Outputs (driven by this block):
        ft_3v3     -- 3.3 V from U6's internal LDO (VCCD, pin 39, is an OUTPUT
                      because VREGIN is fed from 5 V VBUS). Nothing else may
                      drive this rail.
        rxf_n, txe_n, fifo_clk60, pwren_n -- driven by U6 towards the FPGA.
        fifo_clk60 -- 60 MHz FIFO clock; the FT232HL is the clock master.
    Inputs from the FPGA (sensed by U6):
        rd_n, wr_n, oe_n
    Bidirectional:
        fifo_d     -- 8-bit SKiDL Bus, U6 ADBUS0-7 <-> FPGA.
        gnd        -- common ground.

    Assumptions:
      * Assembler sets `.drive = POWER` on vbus, ft_3v3 and gnd.
      * VBUS bulk (C83, <=10 uF USB inrush limit) lives in `power_tree`; this
        block adds only a local 1 uF at U6's VREGIN pin.
      * PWREN_N leaves this block to drive Q1's gate in `power_tree`; R65 is the
        FTDI-mandated 10k pull-up and lives here.
      * ACBUS9 = PWREN# only holds because U7 (93LC56B) is fitted and programmed.
      * FIFO_SIWU_N is NOT an interface net any more (architecture rev.3): BANK3's
        23 I/O follow VCCIO3 to 1.8 V for the in-package PSRAM, leaving 48 3.3 V
        I/O against 51 required. SIWU# is therefore strapped inactive inside this
        block by R67 and never reaches the FPGA.
    """

    # ---- Templates (sourcing/sourced_bom.csv) -----------------------------
    R_0402 = Part('Device', 'R', dest=TEMPLATE,
                  footprint='Resistor_SMD:R_0402_1005Metric')
    C_0402 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0402_1005Metric')

    # ---- Internal nets (net_plan.md "USB and power control") --------------
    usb_dp = Net('USB_DP')        # 90 ohm diff pair, J4 <-> U8 <-> U6
    usb_dm = Net('USB_DM')
    cc1 = Net('CC1')
    cc2 = Net('CC2')
    ft_ref = Net('FT_REF')        # U6 REF -> 12k -> GND (FTDI-mandated)
    ee_cs = Net('EE_CS')
    ee_sk = Net('EE_SK')
    ee_di = Net('EE_DI')          # U6 EEDATA, wired direct to EEPROM DI
    ee_do = Net('EE_DO')          # EEPROM DO, reaches EEDATA via R64 (2.2k)
    # Block-internal since architecture rev.3 — no longer on the FPGA.
    fifo_siwu_n = Net('FIFO_SIWU_N')
    xi = Net('XI')                # 12 MHz crystal, Y1
    xo = Net('XO')
    # U6 pins 37/38 are +1.8V INTERNAL REGULATOR OUTPUTS, not 3.3 V inputs.
    # net_plan.md line 16 wrongly lists VCORE on FT_3V3 — see handoff.
    ft_vcca = Net('FT_VCCA_1V8')
    ft_vcore = Net('FT_VCORE_1V8')

    # ---- J4: USB-C receptacle, USB 2.0, no PD controller ------------------
    J4 = Part('Connector', 'USB_C_Receptacle_USB2.0_16P', ref='J4',
              value='TYPE-C-16PIN',
              footprint='Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal')
    J4['A4', 'A9', 'B4', 'B9'] += vbus
    J4['A1', 'A12', 'B1', 'B12'] += gnd
    J4['S1'] += gnd                       # shell to chassis/signal ground
    J4['A5'] += cc1
    J4['B5'] += cc2
    # Both D+/D- pairs strapped so the cable works in either orientation.
    J4['A6'] += usb_dp
    J4['B6'] += usb_dp
    J4['A7'] += usb_dm
    J4['B7'] += usb_dm
    J4['A8'] += NC                        # SBU1 unused (no alt-mode)
    J4['B8'] += NC                        # SBU2 unused

    # Separate 5.1k pulldown per CC pin — a shared resistor would misreport the
    # sink and stop the source advertising current (net_plan.md line 99).
    R61 = R_0402(ref='R61', value='5.1k')
    R62 = R_0402(ref='R62', value='5.1k')
    cc1 += R61[1]
    R61[2] += gnd
    cc2 += R62[1]
    R62[2] += gnd

    # ---- U8: USBLC6-2SC6 ESD array ---------------------------------------
    # Pins 1/6 are one internal node (I/O1) and 3/4 are the other (I/O2); the
    # part is a layout pass-through, so each pair is a single net.
    U8 = Part('Power_Protection', 'USBLC6-2SC6', ref='U8', value='USBLC6-2SC6',
              footprint='Package_TO_SOT_SMD:SOT-23-6')
    U8[1] += usb_dm
    U8[6] += usb_dm
    U8[3] += usb_dp
    U8[4] += usb_dp
    U8[5] += vbus
    U8[2] += gnd

    # ---- U6: FT232HL, USB HS <-> 245 synchronous FIFO ---------------------
    U6 = Part('Interface_USB', 'FT232H', ref='U6', value='FT232HL',
              footprint='Package_QFP:LQFP-48_7x7mm_P0.5mm')

    # USB PHY
    U6['DP'] += usb_dp
    U6['DM'] += usb_dm

    # Power. VREGIN (40) takes 5 V from VBUS; VCCD (39) then becomes the 3.3 V
    # LDO output that supplies VCCIO/VPHY/VPLL and the rest of the board.
    U6[40] += vbus                        # VREGIN
    U6[39] += ft_3v3                      # VCCD, +3.3 V output
    U6[12] += ft_3v3                      # VCCIO
    U6[24] += ft_3v3                      # VCCIO
    U6[46] += ft_3v3                      # VCCIO
    U6[3] += ft_3v3                       # VPHY
    U6[8] += ft_3v3                       # VPLL
    U6[37] += ft_vcca                     # +1.8 V out, cap to GND only
    U6[38] += ft_vcore                    # +1.8 V out, cap to GND only
    U6[4, 9, 41] += gnd                   # AGND
    U6[10, 11, 22, 23, 35, 36, 47, 48] += gnd
    U6[42] += gnd                         # TEST -> GND for normal operation

    # RESET# (pin 34): absent from net_plan.md. FTDI: "tied to VCCIO (+3.3V) if
    # not being used" — a direct wire, no resistor.
    U6[34] += ft_3v3

    # Current reference: 12k 1% to GND (FTDI-mandated).
    R63 = R_0402(ref='R63', value='12k')
    U6['REF'] += ft_ref
    ft_ref += R63[1]
    R63[2] += gnd

    # 12 MHz crystal. Crystal_GND24 is the 4-pad SMD3225 variant: pads 1/3 are
    # the terminals, pads 2/4 the grounded shield.
    Y1 = Part('Device', 'Crystal_GND24', ref='Y1', value='12MHz',
              footprint='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm')
    U6[1] += xi                           # OSCI
    U6[2] += xo                           # OSCO
    Y1[1] += xi
    Y1[3] += xo
    Y1[2, 4] += gnd
    C601 = C_0402(ref='C601', value='12pF')
    C602 = C_0402(ref='C602', value='12pF')
    xi += C601[1]
    C601[2] += gnd
    xo += C602[1]
    C602[2] += gnd

    # 245 synchronous FIFO interface (net_plan.md "FPGA <-> FT232HL").
    for i in range(8):
        U6['ADBUS{}'.format(i)] += fifo_d[i]
    U6['ACBUS0'] += rxf_n                 # RXF#  U6 -> FPGA
    U6['ACBUS1'] += txe_n                 # TXE#  U6 -> FPGA
    U6['ACBUS2'] += rd_n                  # RD#   FPGA -> U6
    U6['ACBUS3'] += wr_n                  # WR#   FPGA -> U6
    U6['ACBUS4'] += fifo_siwu_n           # SIWU# strapped inactive, see R67
    U6['ACBUS5'] += fifo_clk60            # CLKOUT 60 MHz, U6 is clock master
    U6['ACBUS6'] += oe_n                  # OE#   FPGA -> U6
    U6['ACBUS7'] += ft_3v3                # PWRSAV# tied high (net_plan line 92)
    U6['ACBUS8'] += NC                    # unused
    U6['ACBUS9'] += pwren_n               # PWREN#, EEPROM-configured

    # R65: FTDI Table 3.5 footnote — PWREN# "must be used with a 10k resistor
    # pull up". Mandatory, not a placeholder.
    R65 = R_0402(ref='R65', value='10k')
    pwren_n += R65[1]
    R65[2] += ft_3v3

    # R67: SIWU# tie-off. FT232H datasheet pin table — "Send Immediate / Wake Up
    # (SI/WU#)" is ACTIVE LOW, so the INACTIVE state is HIGH. Pulled to FT_3V3,
    # never driven low. 3.3 V through 10k against +/-1 uA input leakage drops
    # 10 mV => 3.29 V vs VIH 2.0 V.
    R67 = R_0402(ref='R67', value='10k')
    fifo_siwu_n += R67[1]
    R67[2] += ft_3v3

    # ---- U7: 93LC56B configuration EEPROM (Microwire) ---------------------
    # Load-bearing: without it ACBUS9 defaults to tri-state-pull-up and the
    # PWREN# power gating silently fails.
    U7 = Part('Memory_EEPROM', '93LCxxBxxOT', ref='U7', value='93LC56BT-I/OT',
              footprint='Package_TO_SOT_SMD:SOT-23-6')
    # SYMBOL PIN-TYPE OVERRIDE (ERC correctness, not ERC suppression).
    # Interface_USB:FT232H declares EECLK (symbol pin 44) and EECS (symbol pin 45)
    # as INPUT, and Memory_EEPROM:93LCxxBxxOT declares CLK (4) and CS (5) as INPUT
    # too. The hardware is the other way round: the FT232H is the Microwire BUS
    # MASTER -- the FT232H drives the EEPROM's clock and chip select, and the
    # 93LC56B's CLK/CS are device INPUTS. Contrast EEDATA, which the FT232H symbol
    # already declares BIDIR and which therefore never warned.
    # (Pins are addressed BY NAME below, so the symbol's own numbering governs;
    #  the netlist confirms EE_SK on U6.44 and EE_CS on U6.45.)
    # With two INPUT pins per net, SKiDL's net_erc() computes net_drive = NONE and
    # emits 3 warnings per net: "No drivers" + 2 x "Insufficient drive current"
    # (INPUT has min_rcv = PASSIVE). That is 6 warnings for 2 nets, all spurious.
    # Correcting U6's two pin FUNCTIONS -- the idiomatic SKiDL override -- gives
    # them drive = PUSHPULL and clears all 6, WITHOUT disabling any check: EE_SK
    # and EE_CS are still fully ERC'd, and a second driver appearing on either net
    # would now be caught as an OUTPUT-OUTPUT conflict ERROR that the INPUT/INPUT
    # declaration would have hidden. `do_erc = False` was rejected for exactly that
    # reason. The KiCad symbol libraries are stock and are NOT edited; the override
    # is local to this block and also propagates the correct pin type into the
    # exported netlist.
    U6['EECS'].func = Pin.types.OUTPUT
    U6['EECLK'].func = Pin.types.OUTPUT

    U6['EECS'] += ee_cs
    U6['EECLK'] += ee_sk
    U6['EEDATA'] += ee_di
    U7['CS'] += ee_cs
    U7['CLK'] += ee_sk
    U7['DI'] += ee_di                     # EEDATA connects DIRECTLY to DI
    U7['DO'] += ee_do
    U7['VCC'] += ft_3v3
    U7['GND'] += gnd

    # FTDI Table 3.3: EEDATA reaches EEPROM Data-Out through a 2.2k resistor.
    R64 = R_0402(ref='R64', value='2.2k')
    ee_do += R64[1]
    R64[2] += ee_di

    # R66: FTDI Table 3.3 also requires a 10k pull-up on EEPROM Data-Out, IN
    # ADDITION to R64's 2.2k series resistor. Sourced rev.3; without it the
    # EEPROM read is unreliable and the ACBUS9 = PWREN# strap may not load.
    R66 = R_0402(ref='R66', value='10k')
    ee_do += R66[1]
    R66[2] += ft_3v3

    # ---- Decoupling (net_plan.md "Decoupling policy") ---------------------
    # rev.3: the rev.2 shortfall is closed — C610/C611/C612 now cover U6 VPHY,
    # U6 VPLL and U7 VCC. All 10 supply pins in this block are decoupled.
    C603 = C_0402(ref='C603', value='100nF')   # VCCIO pin 12
    C604 = C_0402(ref='C604', value='100nF')   # VCCIO pin 24
    C605 = C_0402(ref='C605', value='100nF')   # VCCIO pin 46
    C606 = C_0402(ref='C606', value='100nF')   # VCCA pin 37, mandated
    C608 = C_0402(ref='C608', value='100nF')   # VCORE pin 38, mandated
    C607 = C_0402(ref='C607', value='1uF')     # FT_3V3 bulk at VCCD pin 39
    C609 = C_0402(ref='C609', value='1uF')     # VBUS local bypass at VREGIN
    C610 = C_0402(ref='C610', value='100nF')   # VPHY pin 3  (new rev.3)
    C611 = C_0402(ref='C611', value='100nF')   # VPLL pin 8  (new rev.3)
    C612 = C_0402(ref='C612', value='100nF')   # U7 EEPROM VCC (new rev.3)

    for cap in (C603, C604, C605, C607, C610, C611, C612):
        ft_3v3 += cap[1]
        cap[2] += gnd
    ft_vcca += C606[1]
    C606[2] += gnd
    ft_vcore += C608[1]
    C608[2] += gnd
    vbus += C609[1]
    C609[2] += gnd
