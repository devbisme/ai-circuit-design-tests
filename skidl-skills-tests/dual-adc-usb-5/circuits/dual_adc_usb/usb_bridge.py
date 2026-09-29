"""USB Bridge — FT232H (245 synchronous FIFO) + 93Cxx config EEPROM + 12 MHz crystal
Block from: architecture/block_diagram.md
Interface nets: USB_DP, USB_DM, FIFO_D[7:0], FIFO_RXF_N, FIFO_TXE_N, FIFO_RD_N, FIFO_WR_N,
                FIFO_OE_N, FIFO_SIWU, FIFO_CLK, PWREN_N, +5V_IN, GND

Primary source used in this block: FTDI FT232H datasheet FT_000288 v1.81 (fetched this pass
from Farnell mirror https://www.farnell.com/datasheets/1913746.pdf — the datasheet phase
could not obtain it; every claim below is from that document, section/table cited).

Power topology (datasheet Table 3.1 + section 6.1 "USB Bus Powered Configuration"):
  * VREGIN (40) = +5V in  -> on-chip +3.3V/+1.8V LDO.
  * VCCD (39) BECOMES A 3.3V OUTPUT when VREGIN is +5V, and is the supply for VCCIO
    (12/24/46), VPLL (8) and VPHY (3). Hence this block needs no external 3.3V rail —
    which is why the work-order signature has no `v3v3_d` parameter. Local net FT232H_3V3.
  * VCCA (37) and VCORE (38) are +1.8V LDO OUTPUTS: "Should not be used. Terminate with
    0.1uF capacitor to GND" — C17/C18 do exactly that, nothing else touches them.
  * TEST (42) -> GND ("for normal operation must be connected to GND").

Datasheet-mandated parts that the sourced BOM does not contain (added here with
non-numeric refs so they cannot collide with any other block's ref designators — see
handoffs/05_blocks/usb_bridge.md § Carried forward for the BOM delta):
  * R_ref   12k 1%  REF (5) -> GND        — Table 3.2: "Current reference – connect via a
                                            12KOhm resistor @ 1% to GND" (mandatory).
  * R_eedo  10k     EEPROM DO -> 3V3      — Table 3.3: "pull Data-Out of the EEPROM to VCCD
                                            via a 10K resistor for correct operation".
  * R_pwren 10k     PWREN# -> 3V3         — Table 3.5 note *: PWREN# "must be used with a
                                            10kOhm resistor pull up".
  * C_vregin, C_io24, C_io46, C_ee  100nF — decoupling for VREGIN, the two remaining VCCIO
                                            pins and the EEPROM's VCC (only C17-C22 were
                                            budgeted, which covers 6 of 9 U7 supply pins).

Deviation from architecture/net_plan.md line 80 (PWREN# on ACBUS7): in SYNC 245 FIFO mode
ACBUS7 is PWRSAV# only (datasheet mode table, section 3.2) and Table 3.5 lists PWREN# as
available on ACBUS0-6/8/9 only — ACBUS0..6 are all consumed by the FIFO interface, so
PWREN# MUST be configured on ACBUS8 (pin 32). Wired there. ACBUS7 (31) is left NC: it has
an internal ~75k pull-down and the "Suspend on ACBUS7 low" EEPROM option is disabled by
default (datasheet section 7 default-configuration table) — the EEPROM image must keep it
disabled.

X2 crystal pins 2/4 ("GND" label ambiguity flagged in handoffs/04_datasheets.md item 9):
resolved as case/shield ground and tied to GND, using KiCad's `Device:Crystal_GND24`
(pins 1/3 = the two electrodes, pins 2/4 = GND) which is the standard pad convention of
the `Crystal_SMD_3225-4Pin_3.2x2.5mm` footprint this crystal was sourced with. Reasoning
and the physical check that would falsify it are recorded in the block handoff.

C13/C14 = 18pF: Cext ~ 2*(CL - Cstray) = 2*(12 - 3) = 18pF for this crystal's 12pF load
(handoffs/04_datasheets.md item 7 — NOT FTDI's generic 27pF figure).
"""
from skidl import *


@SubCircuit
def usb_bridge(usb_dp, usb_dm, fifo_d, fifo_rxf_n, fifo_txe_n, fifo_rd_n, fifo_wr_n,
               fifo_oe_n, fifo_siwu, fifo_clk, pwren_n, v5_in, gnd):
    """FT232H USB 2.0 HS bridge in 245 synchronous FIFO mode, with its config EEPROM.

    Args:
        usb_dp:      Net — USB D+ to J1/D1. Bidirectional (USB differential pair).
        usb_dm:      Net — USB D- to J1/D1. Bidirectional.
        fifo_d:      Bus(8) — FIFO data bus ADBUS0..7, bidirectional.
        fifo_rxf_n:  Net — RXF#, DRIVEN by this block (FT232H output to the FPGA).
        fifo_txe_n:  Net — TXE#, DRIVEN by this block.
        fifo_rd_n:   Net — RD#, SENSED only (FPGA drives).
        fifo_wr_n:   Net — WR#, SENSED only (FPGA drives).
        fifo_oe_n:   Net — OE#, SENSED only (FPGA drives).
        fifo_siwu:   Net — SIWU#, SENSED only (FPGA drives).
        fifo_clk:    Net — 60 MHz CLKOUT, DRIVEN by this block (ACBUS5).
        pwren_n:     Net — PWREN# (ACBUS8), DRIVEN by this block; low after USB
                     configuration, gates Q1 in `digital_power`. 10k pull-up is local.
        v5_in:       Net — +5V_IN, feeds VREGIN. CONSUMED only (needs .drive = POWER at
                     the top level).
        gnd:         Net — GND (single ground net, per net_plan ground policy).

    Internal nets: FT232H_3V3 (VCCD 3.3V output rail), FT232H_RESET_N, FT232H_XI,
    FT232H_XO, EE_CS, EE_CLK, EE_DATA, EE_DO.
    """

    # ------------------------------------------------------------------ parts
    U7 = Part('Interface_USB', 'FT232H', ref='U7', value='FT232HL-REEL',
              footprint='Package_QFP:LQFP-48_7x7mm_P0.5mm')

    # FT_000288 section 4 requires a 16-bit-wide config EEPROM "such as a 93LC56B or
    # equivalent" and states "the 93LC46B is not compatible with the FT232H device".
    # RESOLVED (sourcing revision 2): the originally sourced 1 Kbit 93C46 was of that
    # incompatible density class and has been re-sourced to 93LC56BT-I/SN (2 Kbit, 128x16,
    # LCSC C6164). Pinout, symbol and footprint are unchanged, so only this value string
    # moved; it still reconciles against sourcing/sourced_bom.md.
    U8 = Part('Memory_EEPROM', '93CxxC', ref='U8', value='93LC56BT-I/SN',
              footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')

    X2 = Part('Device', 'Crystal_GND24', ref='X2', value='12MHz 12pF',
              footprint='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm')

    R_t = Part('Device', 'R', dest=TEMPLATE,
               footprint='Resistor_SMD:R_0603_1608Metric')
    R13 = R_t(ref='R13', value='2.2k')       # EEDATA <-> EEPROM DO series resistor
    R14 = R_t(ref='R14', value='10k')        # RESET# pull-up
    R_eedo = R_t(ref='R_eedo', value='10k')  # EEPROM DO -> 3V3 (FTDI Table 3.3)
    R_ref = R_t(ref='R_ref', value='12k 1%')  # REF -> GND (FTDI Table 3.2)
    R_pwren = R_t(ref='R_pwren', value='10k')  # PWREN# pull-up (FTDI Table 3.5)

    C_load = Part('Device', 'C', dest=TEMPLATE, value='18pF',
                  footprint='Capacitor_SMD:C_0603_1608Metric')
    C13, C14 = C_load(2, ref=['C13', 'C14'])  # crystal load caps (C0G/NP0)

    C_d = Part('Device', 'C', dest=TEMPLATE, value='100nF',
               footprint='Capacitor_SMD:C_0402_1005Metric')
    C16 = C_d(ref='C16')                      # RESET# filter
    C17, C18, C19, C20, C21, C22 = C_d(6, ref=['C17', 'C18', 'C19', 'C20', 'C21', 'C22'])
    C_vregin = C_d(ref='C_vregin')            # VREGIN (pin 40)
    C_io24 = C_d(ref='C_io24')                # VCCIO pin 24
    C_io46 = C_d(ref='C_io46')                # VCCIO pin 46
    C_ee = C_d(ref='C_ee')                    # U8 VCC

    # --------------------------------------------------------- internal nets
    ft3v3 = Net('FT232H_3V3')       # VCCD (39) output, 3.3V — supplies VCCIO/VPLL/VPHY
    reset_n = Net('FT232H_RESET_N')
    xi = Net('FT232H_XI')           # OSCI / XCSI
    xo = Net('FT232H_XO')           # OSCO / XCSO
    ee_cs = Net('EE_CS')
    ee_clk = Net('EE_CLK')
    ee_data = Net('EE_DATA')        # FT232H EEDATA, direct to EEPROM DI
    ee_do = Net('EE_DO')            # EEPROM DO: 10k to 3V3, 2.2k back to EEDATA

    # ------------------------------------------------------------ supplies
    v5_in += U7[40]                 # VREGIN: +5V in to the on-chip 3.3/1.8V LDO
    C_vregin[1, 2] += U7[40], gnd

    ft3v3 += U7[39]                 # VCCD = 3.3V OUTPUT (because VREGIN is +5V)
    C19[1, 2] += U7[39], gnd

    ft3v3 += U7[12], U7[24], U7[46]  # VCCIO — 3.3V I/O bank supply
    C22[1, 2] += U7[12], gnd
    C_io24[1, 2] += U7[24], gnd
    C_io46[1, 2] += U7[46], gnd

    ft3v3 += U7[3], U7[8]           # VPHY, VPLL — from VCCD per section 6.1
    C20[1, 2] += U7[3], gnd
    C21[1, 2] += U7[8], gnd

    # +1.8V LDO outputs: decouple only, never drive or load (Table 3.1).
    C17[1, 2] += U7[37], gnd        # VCCA
    C18[1, 2] += U7[38], gnd        # VCORE

    gnd += U7[10], U7[11], U7[22], U7[23], U7[35], U7[36], U7[47], U7[48]  # GND
    gnd += U7[4], U7[9], U7[41]     # AGND — one ground net, per net_plan ground policy
    gnd += U7[42]                   # TEST: must be tied low

    # ------------------------------------------------------- reset & bias
    ft3v3 += R14[1]
    reset_n += R14[2], U7[34], C16[1]   # RESET# 10k pull-up + 100nF filter
    gnd += C16[2]

    U7[5] += R_ref[1]                   # REF: 12k 1% to GND (mandatory current reference)
    gnd += R_ref[2]

    # ------------------------------------------------------- USB HS pair
    usb_dp += U7[7]                     # DP
    usb_dm += U7[6]                     # DM

    # ------------------------------------------------- 12 MHz crystal (X2)
    xi += U7[1], X2[1], C13[1]          # OSCI/XCSI  <-> electrode 1
    xo += U7[2], X2[3], C14[1]          # OSCO/XCSO  <-> electrode 3
    gnd += C13[2], C14[2]
    gnd += X2[2], X2[4]                 # case/shield pads — see module docstring

    # ------------------------------------- 245 synchronous FIFO to the FPGA
    for pin, line in zip(range(13, 21), fifo_d):
        U7[pin] += line                 # ADBUS0..7 = D0..D7
    U7[21] += fifo_rxf_n                # ACBUS0 — RXF#, U7 drives
    U7[25] += fifo_txe_n                # ACBUS1 — TXE#, U7 drives
    U7[26] += fifo_rd_n                 # ACBUS2 — RD#,  FPGA drives
    U7[27] += fifo_wr_n                 # ACBUS3 — WR#,  FPGA drives
    U7[28] += fifo_siwu                 # ACBUS4 — SIWU#, FPGA drives
    U7[29] += fifo_clk                  # ACBUS5 — CLKOUT 60 MHz, U7 drives
    U7[30] += fifo_oe_n                 # ACBUS6 — OE#,  FPGA drives

    # PWREN# on ACBUS8 (NOT ACBUS7 — see module docstring), 10k pull-up mandatory.
    pwren_n += U7[32], R_pwren[2]
    ft3v3 += R_pwren[1]

    U7[31] += NC                        # ACBUS7 = PWRSAV# input, internal 75k pull-down
    U7[33] += NC                        # ACBUS9 unused

    # ------------------------------------------------ config EEPROM (U8)
    ft3v3 += U8['VCC'], U8['ORG']       # ORG -> VCC forces x16 organisation (handoff 04 #6)
    gnd += U8['GND']
    C_ee[1, 2] += U8['VCC'], gnd
    U8[7] += NC                         # pin 7 unused on 93Cxx

    ee_cs += U7[45], U8['CS']           # EECS
    ee_clk += U7[44], U8['SCLK']        # EECLK
    ee_data += U7[43], U8['DI']         # EEDATA direct to DI
    ee_do += U8['DO'], R13[1], R_eedo[1]    # DO: 2.2k back to EEDATA, 10k up to 3V3
    ee_data += R13[2]
    ft3v3 += R_eedo[2]
