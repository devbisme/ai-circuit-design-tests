"""FPGA Core -- iCE40HX4K-TQ144 capture/readout controller (U9) + SPI config flash (U18)
Block from: architecture/block_diagram.md
Interface nets: V3V3_D, V1V2, GND, ADCA_D[11:0], ADCA_OTR, ADCA_PDWN, ADCB_D[11:0],
    ADCB_OTR, ADCB_PDWN, CLK_10M, CLK60, SRAM_A[17:0], SRAM_D[15:0], SRAM_CE_N,
    SRAM_OE_N, SRAM_WE_N, SRAM_UB_N, SRAM_LB_N, FIFO_D[7:0], FIFO_RXF_N, FIFO_TXE_N,
    FIFO_RD_N, FIFO_WR_N, FIFO_OE_N, EXT_TRIG, LED_USB_N, LED_CAP_N

This block also owns purely internal nets not in its signature (created with Net(...)
below, per the work order): SPI_SCK, SPI_SI, SPI_SO, SPI_SS_N, CDONE, CRESET_N.
(LED_PWR is NOT instantiated here -- see the docstring Note and the block handoff's
Decisions table.)
"""
from skidl import *


@subcircuit
def fpga_core(v3v3_d, v1v2, gnd, adca_data, adca_otr, adca_pdwn, adcb_data, adcb_otr,
              adcb_pdwn, clk_10m, clk60, sram_addr, sram_data, sram_ce_n, sram_oe_n,
              sram_we_n, sram_ub_n, sram_lb_n, fifo_data, rxf_n, txe_n, rd_n, wr_n,
              oe_n, ext_trig, led_usb_n, led_cap_n):
    """iCE40HX4K-TQ144 (U9), the design's ADC->SRAM capture engine and SRAM->FT232H
    sync-FIFO readout engine, plus its SPI configuration flash (U18, W25Q32JVSSIQ),
    programming header (J4), external-trigger header (J5) and status LEDs (D4-D7).

    SCHEMATIC BLOCK ONLY -- this file wires the interfaces the gateware needs; it does
    NOT implement the capture state machine, the FIFO packer, the in-band 4-byte
    command-frame parser (architecture decision A2 / ic_selection.md F2), or the
    polarity-correction subtraction (code_out = 4095 - code_raw, architecture Carried
    forward #6). GATEWARE TODO for a later phase:
      - ADC capture FSM: PDWN control, address counter into SRAM, byte-lane (UB#/LB#)
        sequencing for the 12-bit-in-16-bit-word packing described in
        architecture/ic_selection.md F1.
      - FT245 sync-FIFO packer/parser at 60 MHz: R-08 (design_risks.md) requires all
        FIFO_D/FIFO_WR_N outputs to be registered in iCE40 I/O-cell flip-flops (not
        fabric flops) and the on-chip PLL used to phase-shift the FIFO output clock
        domain relative to CLK60 -- schematically this just means CLK60 must land on a
        global-buffer/PLL-adjacent pin (done below); the phase-shift logic itself is
        gateware.
      - In-band command parser (0xA5 CMD ARG_L ARG_H) on FIFO_D, per ic_selection.md F2.

    Pin-budget check (work order requires this be verified, not assumed): the
    ICE40HX4K-TQ144 KiCad symbol was parsed directly for this block (144 physical
    pins) and has **101 GPIO-capable pins** once power/ground/PLL/VPP pins, the 7
    internally-bonded NC pins, and the 9 pins dedicated to CBSEL0/1 + CDONE + CRESET#
    + the 4-wire SPI-master config bus are excluded. This block's signature (all buses
    and single-bit control/status nets) needs exactly **83 general-purpose GPIO pins
    plus 2 clock-input (GBIN) pins = 85**, leaving 16 pins spare. It fits with margin;
    no escalation needed. See the block handoff's Decisions table for the exact
    pin-to-net allocation table and the two GBIN pin choices.

    Args:
        v3v3_d: 3.3 V digital rail -- U9 VCCIO_0..3, VCC_SPI, VPP_2V5 (see Decisions),
            U18 VCC, all pull-ups, LED anodes, J4 pin 1.
        v1v2: 1.2 V FPGA core rail -- U9 VCC (core, 4 pins) and, via R26 filter, VCCPLL0/1.
        gnd: Ground reference.
        adca_data / adcb_data: 12-bit SKiDL Bus each, ADCA_D[11:0] / ADCB_D[11:0] --
            inputs, driven by the adc_channel blocks' series-damping resistors.
        adca_otr / adcb_otr: Out-of-range flag inputs from each ADC channel.
        adca_pdwn / adcb_pdwn: Power-down outputs, this block drives each ADC's PDWN pin.
        clk_10m: 10.000 MHz input from clock_gen -- lands on a GBIN (global buffer)
            pin, never routed through fabric before use (architecture decision A9).
        clk60: 60.000 MHz FT232H FIFO clock input -- lands on a second GBIN pin,
            PLL-adjacent per R-08's mitigation.
        sram_addr: 18-bit output Bus, SRAM_A[17:0] -- this block drives the SRAM address.
        sram_data: 16-bit bidirectional Bus, SRAM_D[15:0].
        sram_ce_n / sram_oe_n / sram_we_n / sram_ub_n / sram_lb_n: SRAM control outputs,
            all active LOW, all driven by this block (sram_buffer only consumes them).
        fifo_data: 8-bit bidirectional Bus, FIFO_D[7:0], shared with the FT232H.
        rxf_n / txe_n: FT232H status inputs (host data available / FIFO write space).
        rd_n / wr_n / oe_n: FT232H strobe/turnaround outputs, driven by this block.
        ext_trig: External trigger input (from J5, series-damped and clamped locally).
        led_usb_n / led_cap_n: Active-LOW LED-driver outputs (D5 USB-active, D6
            capture-armed), driven by this block.
    """

    # ------------------------------------------------------------------
    # U9 -- iCE40HX4K-TQ144, 3520 LUT, 107 I/O FPGA (TQFP-144)
    # ------------------------------------------------------------------
    u9 = Part(
        'FPGA_Lattice',
        'ICE40HX4K-TQ144',
        ref='U9',
        value='iCE40HX4K-TQ144',
        footprint='Package_QFP:TQFP-144_20x20mm_P0.5mm',
    )

    # --- Power: VCCIO banks 0-3 -> V3V3_D (each bank name aliases 2 physical pins) ---
    u9['VCCIO_0'] += v3v3_d
    u9['VCCIO_1'] += v3v3_d
    u9['VCCIO_2'] += v3v3_d
    u9['VCCIO_3'] += v3v3_d

    # --- Power: VCC (core, 4 physical pins, same name aliases all of them) -> V1V2 ---
    u9['VCC'] += v1v2

    # --- Ground: GND (9 physical pins, single name) -> single global GND ---
    u9['GND'] += gnd
    u9['GNDPLL0'] += gnd
    u9['GNDPLL1'] += gnd

    # ------------------------------------------------------------------
    # Decoupling: C47-C62 (16 caps), per net_plan.md Sec.10 ("1x10uF + 8x100nF on
    # V3V3_D banks; 1x10uF + 4x100nF on V1V2 core") and sourced_bom.md Block 9's exact
    # C47-C64 allocation (12x100nF + 2x1uF + 2x10uF, before the C63/C64 PLL-filter/
    # CRESET-timing caps handled separately below). All 8 physical VCCIO pins and all
    # 4 physical VCC(core) pins are already tied to the same V3V3_D/V1V2 nets above
    # (name-based connection aliases every physical pin of a given bank/rail), so the
    # caps below are placed straight on those top-level rails -- electrically
    # equivalent to "at the pin" since every physical pin of a given name is the same
    # node (same approach as sram_buffer.py's C41-C44).
    # ------------------------------------------------------------------
    # C47-C54: 8x100nF on V3V3_D (>=8 on VCCIO, one nominal per physical VCCIO pin:
    # pins 6, 30, 46, 57, 89, 100, 123, 131).
    for i, ref in enumerate(['C47', 'C48', 'C49', 'C50', 'C51', 'C52', 'C53', 'C54']):
        c = Part('Device', 'C', ref=ref, value='100nF',
                 footprint='Capacitor_SMD:C_0402_1005Metric')
        c[1] += v3v3_d
        c[2] += gnd

    # C55-C58: 4x100nF on V1V2 (one nominal per physical VCC-core pin: 27, 40, 92, 111)
    for ref in ['C55', 'C56', 'C57', 'C58']:
        c = Part('Device', 'C', ref=ref, value='100nF',
                 footprint='Capacitor_SMD:C_0402_1005Metric')
        c[1] += v1v2
        c[2] += gnd

    # C59, C60: 1uF extra bulk -- one per rail (sourced BOM's actual allocation goes
    # beyond net_plan.md's stated minimum, same pattern as sram_buffer.py's B1/B2)
    c59 = Part('Device', 'C', ref='C59', value='1uF',
               footprint='Capacitor_SMD:C_0603_1608Metric')
    c59[1] += v3v3_d
    c59[2] += gnd

    c60 = Part('Device', 'C', ref='C60', value='1uF',
               footprint='Capacitor_SMD:C_0603_1608Metric')
    c60[1] += v1v2
    c60[2] += gnd

    # C61, C62: 10uF bulk -- one per rail
    c61 = Part('Device', 'C', ref='C61', value='10uF',
               footprint='Capacitor_SMD:C_0805_2012Metric')
    c61[1] += v3v3_d
    c61[2] += gnd

    c62 = Part('Device', 'C', ref='C62', value='10uF',
               footprint='Capacitor_SMD:C_0805_2012Metric')
    c62[1] += v1v2
    c62[2] += gnd

    # --- PLL supply: sourced BOM allocates exactly one RC filter (R26 470R + C63
    # --- 100nF) for the *pair* of VCCPLL0/VCCPLL1 pins -- both PLL0 and PLL1 are tied
    # --- to the same filtered node (net_plan.md Sec.10 "VCCPLL via 100R+100nF" is the
    # --- rough estimate; sourced_bom.md's R26=470R/C63=100nF is the settled value and
    # --- takes precedence, per "do not redo" sourcing values).
    pll_filt = Net('ICE40_VCCPLL_FILT')
    u9['VCCPLL0'] += pll_filt
    u9['VCCPLL1'] += pll_filt

    r26 = Part('Device', 'R', ref='R26', value='470',
               footprint='Resistor_SMD:R_0402_1005Metric')
    r26[1] += v1v2
    r26[2] += pll_filt

    c63 = Part('Device', 'C', ref='C63', value='100nF',
               footprint='Capacitor_SMD:C_0402_1005Metric')
    c63[1] += pll_filt
    c63[2] += gnd

    # --- VPP_2V5 / VPP_FAST: NVCM programming-voltage supply pins. Judgement call --
    # --- see block handoff Decisions -- this architecture has no dedicated 2.5V rail
    # --- anywhere in net_plan.md, and this design never uses NVCM programming (single
    # --- external SPI flash image, CBSEL0/1 tied GND below selects SPI-master boot).
    # --- VPP_2V5 tied to V3V3_D (0.8V off its nominal 2.5V spec, accepted since it is
    # --- not used for programming) rather than adding a new board-wide rail for one
    # --- housekeeping pin. VPP_FAST tied GND per common iCE40 non-NVCM practice
    # --- (datasheet summary flagged this low-confidence -- not independently
    # --- re-verified against the full DS1040 datasheet, which was not fetched this
    # --- session).
    u9['VPP_2V5'] += v3v3_d
    u9['VPP_FAST'] += gnd

    # --- VCC_SPI: dedicated SPI-interface supply, same 3.3V rail as U18 ---
    u9['VCC_SPI'] += v3v3_d

    # --- 7 internally-bonded NC pins (same "NC" name aliases all of them) ---
    u9['NC'] += NC

    # --- Cold-boot config: CBSEL0/CBSEL1 tied GND -> single-image SPI-master boot ---
    # --- from the lowest configuration address (datasheet phase decision DS4) ---
    u9['IOB_103_CBSEL0'] += gnd
    u9['IOB_104_CBSEL1'] += gnd

    # ------------------------------------------------------------------
    # CDONE: config-done status, open-collector, needs an external pull-up.
    # R20 does double duty as that pull-up AND the D4 LED's series resistor
    # (sourced BOM's own framing: "needs external pull-up, shared with D4 LED + R20").
    # V3V3_D --R20(1k)--> CDONE node --> D4(anode->cathode) --> GND.
    # While configuring, U9 holds CDONE low internally (LED off, R20 sinks a small
    # current into the open-collector driver); once configuration completes, U9
    # releases CDONE and R20 pulls it to V3V3_D, lighting D4 as the "config done"
    # indicator.
    # ------------------------------------------------------------------
    cdone_net = Net('CDONE')
    u9['CDONE'] += cdone_net

    r20 = Part('Device', 'R', ref='R20', value='1k',
               footprint='Resistor_SMD:R_0402_1005Metric')
    r20[1] += v3v3_d
    r20[2] += cdone_net

    d4 = Part('Device', 'LED', ref='D4', value='Blue',
              footprint='LED_SMD:LED_0603_1608Metric')
    d4['A'] += cdone_net
    d4['K'] += gnd

    # ------------------------------------------------------------------
    # CRESET#: configuration reset, active LOW. R23 pull-up (10k) keeps it idle HIGH;
    # C64 (100nF) forms the standard iCE40 power-up RC delay so CRESET# rises after
    # V3V3_D/V1V2 have stabilised. Routed to J4 so an external programmer can pulse it.
    # ------------------------------------------------------------------
    creset_n = Net('CRESET_N')
    u9['~{CRESET}'] += creset_n

    r23 = Part('Device', 'R', ref='R23', value='10k',
               footprint='Resistor_SMD:R_0402_1005Metric')
    r23[1] += v3v3_d
    r23[2] += creset_n

    c64 = Part('Device', 'C', ref='C64', value='100nF',
               footprint='Capacitor_SMD:C_0402_1005Metric')
    c64[1] += creset_n
    c64[2] += gnd

    # ------------------------------------------------------------------
    # SPI configuration bus: U9 is SPI master, U18 (W25Q32JVSSIQ) is the config flash.
    # Net names match net_plan.md Sec.8 exactly (named from the J4 programming-header
    # perspective, not the FPGA's internal SDO/SDI pin names).
    # ------------------------------------------------------------------
    spi_sck = Net('SPI_SCK')
    spi_si = Net('SPI_SI')    # U9 SDO (pin 67) -> U18 DI
    spi_so = Net('SPI_SO')    # U18 DO -> U9 SDI (pin 68)
    spi_ss_n = Net('SPI_SS_N')

    u9['IOB_107_SCK'] += spi_sck
    u9['IOB_105_SDO'] += spi_si
    u9['IOB_106_SDI'] += spi_so
    u9['IOB_108_SS'] += spi_ss_n

    r24 = Part('Device', 'R', ref='R24', value='10k',
               footprint='Resistor_SMD:R_0402_1005Metric')
    r24[1] += v3v3_d
    r24[2] += spi_ss_n

    # ------------------------------------------------------------------
    # U18 -- W25Q32JVSSIQ, 32 Mbit SPI NOR config flash (SOIC-8)
    # ------------------------------------------------------------------
    u18 = Part(
        'Memory_Flash',
        'W25Q32JVSS',
        ref='U18',
        value='W25Q32JVSSIQ',
        footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
    )
    u18['~{CS}'] += spi_ss_n
    u18['CLK'] += spi_sck
    u18['DI/IO_{0}'] += spi_si
    u18['DO/IO_{1}'] += spi_so
    u18['VCC'] += v3v3_d
    u18['GND'] += gnd

    # ~WP and ~HOLD must be pulled HIGH for standard single-SPI mode (datasheet
    # summary flag: not itemized as separate resistors in the sourced BOM's fixed
    # R20-R26 passive count). Judgement call: tie directly to V3V3_D rather than add
    # unbudgeted parts -- this is the datasheet summary's own stated fallback ("tie
    # directly to VCC if no quad-mode future-proofing is wanted").
    u18['~{WP}/IO_{2}'] += v3v3_d
    u18['~{HOLD}/~{RESET}/IO_{3}'] += v3v3_d

    # ------------------------------------------------------------------
    # J4 -- 2x5 1.27mm SMD programming header: SPI + CRESET# + CDONE + 3V3 + GND
    # (sourced BOM note). 2 of 10 pins are spare; tied NC/GND per the block handoff.
    # ------------------------------------------------------------------
    j4 = Part(
        'Connector_Generic',
        'Conn_02x05_Odd_Even',
        ref='J4',
        value='FPGA_PROG',
        footprint='Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical',
    )
    j4[1] += v3v3_d
    j4[2] += gnd
    j4[3] += spi_sck
    j4[4] += spi_si
    j4[5] += spi_so
    j4[6] += spi_ss_n
    j4[7] += creset_n
    j4[8] += cdone_net
    j4[9] += gnd     # redundant ground pin -- common header-mechanical practice
    j4[10] += NC      # spare, intentionally unconnected

    # ------------------------------------------------------------------
    # J5 -- external trigger input header (2-pin 2.54mm). Series R25 (1k) + D7
    # (BAV99) clamp before the FPGA pin, per net_plan.md Sec.8.
    #
    # D7 wiring judgement call (see datasheets/BAV99_SUMMARY.md Notes and the block
    # handoff Decisions): the installed BAV99 KiCad symbol is COMMON-ANODE (pin 2 =
    # shared anode, pins 1/3 = independent cathodes). A common-anode dual diode
    # physically cannot form a symmetric clamp-to-both-rails circuit (that needs one
    # diode with anode=signal/cathode=V3V3_D *and* a separate diode with
    # anode=GND/cathode=signal -- different anodes, incompatible with a shared-anode
    # package). Implemented here: common anode -> EXT_TRIG node (high-side clamp
    # only, protecting against a trigger source driven above V3V3_D); cathode 2
    # (pin 3) left NC since tying it to GND would forward-bias the diode on every
    # normal HIGH pulse and clamp the trigger signal to ~0.6V, breaking the input.
    # ------------------------------------------------------------------
    j5 = Part(
        'Connector_Generic',
        'Conn_01x02',
        ref='J5',
        value='EXT_TRIG',
        footprint='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',
    )
    j5[1] += ext_trig
    j5[2] += gnd

    r25 = Part('Device', 'R', ref='R25', value='1k',
               footprint='Resistor_SMD:R_0402_1005Metric')
    r25[1] += ext_trig
    ext_trig_clamped = Net('EXT_TRIG_CLAMPED')
    r25[2] += ext_trig_clamped

    d7 = Part('Diode', 'BAV99', ref='D7', value='BAV99',
              footprint='Package_TO_SOT_SMD:SOT-23')
    d7[2] += ext_trig_clamped   # pin 2 = A, common anode -- ties to the signal node
    d7[1] += v3v3_d             # pin 1 = K -- high-side clamp
    d7[3] += NC                 # pin 3 = K -- unused (see docstring above)

    # --- U9 pin: EXT_TRIG (GPIO bank, non-GBIN -- input only, no clock use) ---
    u9[118] += ext_trig_clamped   # pin 118, IOT_177

    # ------------------------------------------------------------------
    # Status LEDs D5 (USB-active, green) / D6 (capture-armed, amber): active-LOW,
    # V3V3_D -> LED -> series R -> FPGA I/O (FPGA sinks current to light the LED),
    # per net_plan.md Sec.8.
    #
    # NOTE on LED_PWR / D3: the work order text (carried over from
    # handoffs/02_architecture.md's block manifest) lists LED_PWR as an internal net
    # "owned" by fpga_core, but net_plan.md Sec.8 describes it as fully hardwired
    # (V3V3_D -> 1k -> D3 -> GND, no FPGA pin involved), and the architecture's own
    # ref-designator allocation puts D3 and its resistor in the power_digital block
    # (refs U1, U2, D3, R4, C3-C7), not in fpga_core's refs (U9, U18, J4, J5, D4-D7,
    # R20-R26, C47-C64 -- no D3 or R4 here). Instantiating D3 here would collide with
    # power_digital's part. LED_PWR is therefore NOT built in this block; it is
    # entirely local to power_digital. Flagged in the block handoff.
    # ------------------------------------------------------------------
    d5 = Part('Device', 'LED', ref='D5', value='Green',
              footprint='LED_SMD:LED_0603_1608Metric')
    d5['A'] += v3v3_d

    r21 = Part('Device', 'R', ref='R21', value='1k',
               footprint='Resistor_SMD:R_0402_1005Metric')
    d5['K'] += r21[1]
    r21[2] += led_usb_n
    u9[119] += led_usb_n   # pin 119, IOT_178

    d6 = Part('Device', 'LED', ref='D6', value='Amber',
              footprint='LED_SMD:LED_0603_1608Metric')
    d6['A'] += v3v3_d

    r22 = Part('Device', 'R', ref='R22', value='1k',
               footprint='Resistor_SMD:R_0402_1005Metric')
    d6['K'] += r22[1]
    r22[2] += led_cap_n
    u9[120] += led_cap_n   # pin 120, IOT_179

    # ------------------------------------------------------------------
    # Clock inputs: both land on iCE40 GBIN (global-buffer-capable) pins, never
    # through fabric, per architecture decision A9 and R-08's PLL-adjacency
    # mitigation. Pin choices documented in the block handoff Decisions table.
    # ------------------------------------------------------------------
    u9[52] += clk_10m    # pin 52, IOB_82_GBIN4 -- PLL0-adjacent (GNDPLL0/VCCPLL0 @ 53/54)
    u9[129] += clk60     # pin 129, IOT_198_GBIN0 -- PLL1-adjacent (VCCPLL1/GNDPLL1 @ 126/127)

    # ------------------------------------------------------------------
    # ADC channel A: 12-bit data bus + OTR + PDWN. Pin allocation is an arbitrary
    # (but fixed, documented) slice of the GPIO-capable pin pool -- exact pin-to-net
    # assignment is refined later by the gateware .pcf constraints file, not by this
    # schematic; only bank/electrical fitness matters here (see docstring pin-budget
    # check).
    # ------------------------------------------------------------------
    adca_d_pins = [1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 15, 16]
    for bit, pin in enumerate(adca_d_pins):
        u9[pin] += adca_data[bit]
    u9[17] += adca_otr
    u9[18] += adca_pdwn

    # --- ADC channel B: same pattern ---
    adcb_d_pins = [19, 20, 21, 22, 23, 24, 25, 26, 28, 29, 31, 32]
    for bit, pin in enumerate(adcb_d_pins):
        u9[pin] += adcb_data[bit]
    u9[33] += adcb_otr
    u9[34] += adcb_pdwn

    # ------------------------------------------------------------------
    # SRAM bus: 18-bit address + 16-bit data + 5 control lines, all driven by this
    # block per net_plan.md Sec.6 (sram_buffer only consumes them).
    # ------------------------------------------------------------------
    sram_a_pins = [37, 38, 39, 41, 42, 43, 44, 45, 47, 48, 49, 55, 56, 60, 61, 62, 73, 74]
    for bit, pin in enumerate(sram_a_pins):
        u9[pin] += sram_addr[bit]

    sram_d_pins = [75, 76, 78, 79, 80, 81, 82, 83, 84, 85, 87, 88, 90, 91, 93, 94]
    for bit, pin in enumerate(sram_d_pins):
        u9[pin] += sram_data[bit]

    u9[95] += sram_ce_n
    u9[96] += sram_oe_n
    u9[97] += sram_we_n
    u9[98] += sram_ub_n
    u9[99] += sram_lb_n

    # ------------------------------------------------------------------
    # FT245 sync-FIFO bus: 8-bit bidirectional data + 5 handshake/strobe lines, per
    # net_plan.md Sec.7. R-08 (design_risks.md): these outputs must be registered in
    # iCE40 I/O-cell flip-flops in gateware -- schematically only the pin connections
    # are made here.
    # ------------------------------------------------------------------
    fifo_d_pins = [101, 102, 104, 105, 106, 107, 110, 112]
    for bit, pin in enumerate(fifo_d_pins):
        u9[pin] += fifo_data[bit]

    u9[113] += rxf_n
    u9[114] += txe_n
    u9[115] += rd_n
    u9[116] += wr_n
    u9[117] += oe_n
