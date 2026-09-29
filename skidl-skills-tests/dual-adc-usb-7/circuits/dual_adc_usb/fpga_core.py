"""FPGA Core — GW1NR-9 (U5) with in-package PSRAM, JTAG header and status LEDs
Block from: architecture/block_diagram.md
Interface nets: CLK10_FPGA, ADC_DA[0:11], ADC_DB[0:11], ADC_DVA, ADC_SEN, ADC_SCLK,
                ADC_SDATA, ADC_SEL, FIFO_D[0:7], FIFO_RXF_N, FIFO_TXE_N, FIFO_RD_N,
                FIFO_WR_N, FIFO_OE_N, FIFO_CLK60, P1V2, P1V8, P3V3D, GND
"""
from skidl import *


@SubCircuit
def fpga_core(clk_fpga, da, db, dva, sen, sclk, sdata, sel,
              fifo_d, rxf_n, txe_n, rd_n, wr_n, oe_n, fifo_clk60,
              p1v2, p1v8, p3v3d, gnd):
    """GW1NR-LV9QN88PC6/I5 FPGA with JTAG programming header and two status LEDs.

    Implements the `fpga_core` row of architecture/block_diagram.md (rev.3) and
    net_plan.md lines 20-22, 119, 125-145, 165-168, 179-181.

    Args:
        clk_fpga:   CLK10_FPGA. INPUT. 10 MHz system clock from X1 via R32.
        da:         ADC_DA, a 12-bit Bus. INPUT. ADS5231 channel-A data, da[11] = MSB.
        db:         ADC_DB, a 12-bit Bus. INPUT. ADS5231 channel-B data, db[11] = MSB.
        dva:        ADC_DVA. INPUT. Channel-A data-valid strobe (DVB is left NC by adc_dual).
        sen, sclk, sdata, sel: DRIVEN BY THIS BLOCK into U4's serial port. SEL is a
                    dynamic FPGA output, NOT a strap: SBAS295A p.19 requires a low-going
                    pulse to reset the serial registers, and the ADS5231's PLL powers up
                    ENABLED -- the serial PLL-disable write is the only path to 10 MSPS
                    (SPEC F3). Settled in architecture rev.3 decision 1; R402 stays deleted.
        fifo_d:     FIFO_D, an 8-bit Bus. BIDIRECTIONAL. FT232H ADBUS0-7, 245-sync FIFO.
        rxf_n, txe_n: INPUTS from U6 (ACBUS0/1).
        rd_n, wr_n, oe_n: DRIVEN BY THIS BLOCK into U6 (ACBUS2/3/6). FIFO_SIWU_N is NOT
                    here -- it is strapped inactive-high by R67 inside `usb_bridge`.
        fifo_clk60: INPUT. 60 MHz FIFO clock from U6 ACBUS5; the FT232H is clock master.
        p1v2:       P1V2 core supply (1.2 V), VCC pins. Consumed only.
        p1v8:       P1V8 (1.8 V, U15 output). VCCIO3 = PIN 12, the R53 RECONFIG_N
                    pull-up, and J3 pin 1 (the JTAG pod's I/O reference -- U5 pins 5-8
                    are BANK3/VCCIO3 pins, see the J3 comment). Consumed only.
        p3v3d:      P3V3D (3.3 V). VCCX/VCCIO0 (64/67/78) + VCCIO1 (58) + VCCIO2 (23/44).
                    Consumed only.
        gnd:        GND. Consumed only.

    All four supply nets are consumed, never driven, here -- the assembler sets
    .drive = POWER on each at the top level.

    Assumptions:
        - Pins are addressed BY NUMBER, not by name. The symbol repeats VCC x4, VSS x6
          and VCCX_VCCO0 x4, so name lookup is ambiguous for every supply pin.
        - THE SYMBOL'S PIN-12 NAME IS WRONG. symbols/dual_adc_usb.kicad_sym calls pin 12
          `VCCX_VCCO0`; Gowin UG803 p.5/17 ("Recommended Operating Conditions of QN88P
          Package Embedded with PSRAM") names it VCCIO3, 1.71-1.89 V, and it is an
          independent rail from VCCX/VCCIO0. Pin 12 is therefore wired to `p1v8` BY
          NUMBER, deliberately against the symbol label. Pins 64/67/78 are the real
          VCCX/VCCIO0 and MUST stay at 3.3 V: DS117 Table 3-2 sets VCCX min = 2.375 V and
          Table 3-5 puts the VCCX power-on-reset trip at 1.8-2.0 V, so 1.8 V there would
          leave the device held in reset. The symbol file is NOT edited here.
        - Bank edges read from the symbol's own pin names: IOL* = BANK3 (1.8 V, VCCIO3,
          shared with the PSRAM die), IOB* = BANK2 (VCCO2 23/44), IOR* = BANK1 (VCCIO1
          58), IOT* = top edge on VCCX/VCCIO0 (64/67/78). Every user signal below lands
          on an IOB/IOR/IOT pin, i.e. on a 3.3 V rail. No IOL pin carries a 3.3 V
          signal or reference: the only IOL pins used are 5-8 (JTAG) and 9
          (RECONFIG_N), and all five are referenced to P1V8 = VCCIO3.
        - JTAG_TCK/TMS/TDI/TDO, LED0, LED1, RECONFIG_N, MODE0 and MODE1 are internal to
          this block (net_plan.md lines 165-168); they are not part of the interface.
    """

    # ---- U5: GW1NR-LV9QN88PC6/I5 FPGA (sourced_bom.csv) --------------------------
    # Custom footprint from 04_datasheets: 89 pads, 10x10 mm body (NOT the 8x8 mm that
    # JLC's package string claims). Exposed pad is pin 89.
    u5 = Part('dual_adc_usb', 'GW1NR-LV9QN88PC6-I5', ref='U5',
              value='GW1NR-LV9QN88PC6/I5',
              footprint='ProjectLocal:QFN-88-1EP_10x10mm_P0.4mm_Gowin_QN88P')

    # ---- Supplies ----------------------------------------------------------------
    # VCC core 1.2 V: pins 1, 22, 45, 66
    p1v2 += u5[1], u5[22], u5[45], u5[66]
    # VCCIO3 (PSRAM bank) = pin 12 ONLY, at 1.8 V. See the docstring: the symbol's
    # `VCCX_VCCO0` label on this pin is a known defect (UG803 says VCCIO3), so the
    # connection is made by pin NUMBER and must not be "corrected" to 3.3 V.
    p1v8 += u5[12]
    # 3.3 V I/O supplies: VCCX/VCCIO0 = 64, 67, 78; VCCO2 = 23, 44; VCCIO1 = 58.
    p3v3d += u5[64], u5[67], u5[78], u5[23], u5[44], u5[58]
    # VSS: pins 2, 21, 24, 43, 46, 65; EP (pin 89) is the thermal/ground pad.
    gnd += u5[2], u5[21], u5[24], u5[43], u5[46], u5[65], u5[89]

    # ---- ADC data buses -> bottom edge (BANK2, VCCO2 at pins 23/44) ---------------
    # net_plan.md lines 125-126. BANK2 has 23 bonded I/O and the two buses need 24, so
    # db[11] spills onto the first BANK1 pin (48, IOR24B) -- both banks are at 3.3 V.
    da_pins = [17, 18, 19, 20, 25, 26, 27, 28, 29, 30, 31, 32]
    for bit, pin in enumerate(da_pins):
        u5[pin] += da[bit]

    db_pins = [33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 47, 48]
    for bit, pin in enumerate(db_pins):
        u5[pin] += db[bit]

    # ---- ADC status and serial control -> right edge (BANK1, VCCIO1 at pin 58) ----
    # net_plan.md lines 127-131.
    u5[51] += dva                   # IOR17B_GCLKC_3 -- strobe on a clock-capable pin
    u5[52] += fifo_clk60            # IOR17A_GCLKT_3 -- 60 MHz on the global clock pin
    # SEN/SCLK/SDATA/SEL land on configuration-shared pins. Harmless: the PLL-disable
    # write happens after configuration, and anything the ADC latches during config is
    # overwritten by that write.
    u5[53] += sen                   # IOR15B_DOUT_WE_N
    u5[54] += sclk                  # IOR15A_DIN_CLKHOLD_N
    u5[55] += sdata                 # IOR14B_SSPI_CS_N_D0
    u5[56] += sel                   # IOR14A_SO_D1
    u5[63] += clk_fpga              # IOR5A_RPLL_T_in -- 10 MHz onto the right PLL input

    # ---- FT232H 245-synchronous FIFO -> top edge ---------------------------------
    # net_plan.md lines 138-145. FIFO_CLK60 is on pin 52 (above) so the 60 MHz clock
    # gets a true global-clock pin. FIFO_SIWU_N is absent by design (R67, usb_bridge).
    fifo_d_pins = [68, 69, 70, 71, 72, 73, 74, 75]
    for bit, pin in enumerate(fifo_d_pins):
        u5[pin] += fifo_d[bit]

    u5[76] += rxf_n                 # IOT37B  <- U6 ACBUS0
    u5[77] += txe_n                 # IOT37A  <- U6 ACBUS1
    u5[79] += rd_n                  # IOT12B  -> U6 ACBUS2
    u5[80] += wr_n                  # IOT12A  -> U6 ACBUS3
    u5[81] += oe_n                  # IOT11B  -> U6 ACBUS6

    # ---- J3: JTAG programming header (net_plan.md line 165) ----------------------
    # Development only: the GW1NR-9 boots itself from 4 Mbit of on-die configuration
    # Flash (DS117 sec.2 / 2.12.2), so there is no external config memory and no
    # run-time dongle. Header order is documented in the block handoff.
    #
    # J3 pin 1 is the pod's I/O REFERENCE and must be P1V8, not P3V3D. U5 pins 5-8
    # (TMS/TCK/TDI/TDO) are IOL* = BANK3, whose VCCIO is pin 12 = P1V8 (Gowin UG803
    # per-pin table, BANK column = 3; they are typed I/O, not dedicated VCCX-referenced
    # pins). Three reasons, any one sufficient: (1) abs max on a BANK3 pin is
    # VCCIO3 + 0.3 V = 2.1 V, so a 3.3 V pod overdrives TCK/TMS/TDI by 1.2 V;
    # (2) TDO drives out at 1.8 V, below a 3.3 V pod's ~2.0 V V_IH, so programming
    # cannot work even undamaged; (3) P1V8 is deliberately the LAST rail up (U14 -> U15),
    # so a pod attached at plug-in back-powers BANK3 -- the rail that feeds the
    # in-package PSRAM, i.e. the whole 4 MB sample buffer (SPEC F6). Same rail as R53
    # on pin 9 below, for exactly the same reason. A 3.3 V-only pod would be a BOM
    # change (level shifter), not a coder fix.
    j3 = Part('Connector_Generic', 'Conn_01x06', ref='J3', value='Conn_01x06',
              footprint='Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical')
    p1v8 += j3[1]
    gnd += j3[2]
    j3[3] += u5[6]                  # IOL11B_TCK
    j3[4] += u5[5]                  # IOL11A_TMS
    j3[5] += u5[7]                  # IOL12B_TDI
    j3[6] += u5[8]                  # IOL13A_TDO

    # ---- R53: RECONFIG_N pull-up to P1V8 (net_plan.md line 167) ------------------
    # Pin 9 is IOL13B_RECONFIG_N -- an IOL*, i.e. BANK3, pin. Its abs max is
    # VCCIO3 + 0.3 V = 2.1 V, so the pull-up goes to P1V8, NOT P3V3D (architecture
    # rev.3 decision 11). Pull-up current 1.8 V / 10 k = 180 uA.
    r53 = Part('Device', 'R', ref='R53', value='10k',
               footprint='Resistor_SMD:R_0402_1005Metric')
    u5[9] += r53[1]
    r53[2] += p1v8

    # ---- R54/R55: MODE[1:0] configuration straps (net_plan.md line 168) ----------
    # MODE0 = pin 88, MODE1 = pin 87, each 4.7 k to GND -> MODE[1:0] = 00. MODE2 is not
    # bonded on QN88P and defaults to 0, so MODE[2:0] = 000 = AUTO BOOT from the
    # embedded configuration Flash (Gowin UG290 Table 5-1, verified in 04_datasheets
    # decision 15). Pull-DOWNS, not pull-ups: the straps are sampled at power-up and a
    # tie to GND is valid before any I/O rail has come up.
    r_mode = Part('Device', 'R', dest=TEMPLATE, value='4.7k',
                  footprint='Resistor_SMD:R_0402_1005Metric')
    r54 = r_mode(ref='R54')
    r55 = r_mode(ref='R55')
    u5[88] += r54[1]                # IOT5A_MODE0
    r54[2] += gnd
    u5[87] += r55[1]                # IOT6B_MODE1
    r55[2] += gnd

    # ---- D51/D52 status LEDs (net_plan.md line 166) ------------------------------
    # On BANK1 (VCCIO1, pin 58) at 3.3 V: a green LED's Vf ~2.0 V exceeds the entire
    # 1.8 V rail, so a BANK3 pin could not light one. Pins 49/50 are plain BANK1 I/O
    # (freed when ADC_OVRA/ADC_OVRB were retired in architecture rev.3), which keeps the
    # LEDs off the configuration-shared MSPI pins 57/59 they previously used -- no more
    # flicker while the FPGA configures.
    r_led = Part('Device', 'R', dest=TEMPLATE, value='1k',
                 footprint='Resistor_SMD:R_0402_1005Metric')
    r51 = r_led(ref='R51')
    r52 = r_led(ref='R52')

    d51 = Part('Device', 'LED', ref='D51', value='LED-Green',
               footprint='LED_SMD:LED_0603_1608Metric')
    d52 = Part('Device', 'LED', ref='D52', value='LED-Red',
               footprint='LED_SMD:LED_0603_1608Metric')

    # Device:LED is pin 1 = K, pin 2 = A -- wired explicitly so the anode faces the
    # series resistor. A bare `pin & R & LED & gnd` chain would reverse-bias them.
    u5[49] += r51[1]                # IOR24A -> LED0
    r51[2] += d51['A']
    d51['K'] += gnd
    u5[50] += r52[1]                # IOR22B -> LED1
    r52[2] += d52['A']
    d52['K'] += gnd

    # ---- Decoupling (net_plan.md lines 179-181, sourced_bom.csv) -----------------
    # Policy asks for 100 nF at EVERY supply pin: 6 on P3V3D (23, 44, 58, 64, 67, 78),
    # 4 on the P1V2 core (1, 22, 45, 66) and 1 on P1V8 (12) = 11. Sourcing rev.4 funded
    # the 4 that rev.2 of this block flagged as missing (C514-C517, sourced_bom.csv
    # row 55), so the policy is now met EXACTLY: 11 x 100 nF, one per supply pin.
    #   P1V2 core  (4 pins: 1, 22, 45, 66) -> C501, C502, C516, C517
    #   P3V3D I/O  (6 pins: 23, 44, 58, 64, 67, 78) -> C503, C504, C505, C506, C514, C515
    #   P1V8/VCCIO3 (1 pin: 12) -> C511
    # Each cap is decoupled to the rail its pin actually sits on. Pin 12 is VCCIO3, the
    # 1.8 V PSRAM bank (see decision 3 in the docstring), so it keeps its own 100 nF on
    # P1V8 and NONE of C514/C515 go there; the other VCCIO/VCCX pins are all 3.3 V.
    c_100n = Part('Device', 'C', dest=TEMPLATE, value='100nF',
                  footprint='Capacitor_SMD:C_0402_1005Metric')

    # P1V2 core: C501, C502, C516, C517 -- one per VCC pin (1, 22, 45, 66);
    # C516/C517 are the two added at sourcing rev.4. C507 local bulk; C508 rail bulk.
    for ref in ('C501', 'C502', 'C516', 'C517'):
        c = c_100n(ref=ref)
        p1v2 += c[1]
        gnd += c[2]
    c507 = Part('Device', 'C', ref='C507', value='1uF',
                footprint='Capacitor_SMD:C_0402_1005Metric')
    p1v2 += c507[1]
    gnd += c507[2]
    c508 = Part('Device', 'C', ref='C508', value='10uF',
                footprint='Capacitor_SMD:C_0805_2012Metric')
    p1v2 += c508[1]
    gnd += c508[2]

    # P3V3D I/O: C503-C506 + C514/C515 -- one per 3.3 V VCCX/VCCIO0 (64, 67, 78),
    # VCCO2 (23, 44) and VCCIO1 (58) pin; C514/C515 are the two added at sourcing
    # rev.4 to cover the last two. C509 local bulk; C510 rail bulk.
    for ref in ('C503', 'C504', 'C505', 'C506', 'C514', 'C515'):
        c = c_100n(ref=ref)
        p3v3d += c[1]
        gnd += c[2]
    c509 = Part('Device', 'C', ref='C509', value='1uF',
                footprint='Capacitor_SMD:C_0402_1005Metric')
    p3v3d += c509[1]
    gnd += c509[2]
    c510 = Part('Device', 'C', ref='C510', value='10uF',
                footprint='Capacitor_SMD:C_0805_2012Metric')
    p3v3d += c510[1]
    gnd += c510[2]

    # P1V8 / VCCIO3 point of load at pin 12: C511 = 100 nF HF, C512 = 4.7 uF local
    # bulk, C513 = 22 uF rail reservoir. Sized in net_plan.md line 181 for the PSRAM's
    # 66 mA / 320 ns burst: droop into 22 uF is 0.87 mV against the 90 mV (5 %) VCCIO
    # ripple allowance of DS117 Table 3-2.
    c511 = c_100n(ref='C511')
    p1v8 += c511[1]
    gnd += c511[2]
    c512 = Part('Device', 'C', ref='C512', value='4.7uF',
                footprint='Capacitor_SMD:C_0603_1608Metric')
    p1v8 += c512[1]
    gnd += c512[2]
    c513 = Part('Device', 'C', ref='C513', value='22uF',
                footprint='Capacitor_SMD:C_0805_2012Metric')
    p1v8 += c513[1]
    gnd += c513[2]

    # ---- Intentionally unconnected -----------------------------------------------
    # Left edge (BANK3, 1.8 V, shared with the PSRAM die -- unusable for any 3.3 V
    #            signal on this board): 3 (IOL2A), 4 (JTAGSEL_N/LPLL_T_in -- internal
    #            pull-up assumed to keep JTAG enabled), 10 (DONE), 11 (GCLKT_6),
    #            13, 14, 15, 16
    # Right edge: 57, 59 (freed when the LEDs moved to 49/50), 60, 61, 62 -- the MSPI
    #            flash bus, unused: the GW1NR-9 configures from its own embedded Flash
    #            and there is no external config memory in the BOM (R-13, closed)
    # Top edge:  82 (freed when FIFO_SIWU_N was strapped by R67 in usb_bridge),
    #            83, 84, 85, 86
    for pin in (3, 4, 10, 11, 13, 14, 15, 16,
                57, 59, 60, 61, 62, 82, 83, 84, 85, 86):
        u5[pin] += NC
