"""FPGA Core — XC6SLX9 capture FSM host, SPI config flash, JTAG header
Block from: architecture/block_diagram.md
Interface nets: ADC1_D[11:0], ADC2_D[11:0], ADC1_OTR, ADC2_OTR, ADC_PDWN, CLK_FPGA,
                SDR_DQ[15:0], SDR_A[12:0], SDR_BA[1:0], SDR_CLK, SDR_CKE, SDR_CS_N,
                SDR_RAS_N, SDR_CAS_N, SDR_WE_N, SDR_LDQM, SDR_UDQM, FIFO_D[7:0], IFCLK,
                SLWR_N, SLRD_N, SLOE_N, PKTEND_N, FIFOADR[1:0], FLAGB, FLAGC,
                +3V3D, +1V2, GND
"""
from skidl import *


# ---------------------------------------------------------------------------------
# XC6SLX9-2TQG144C pin map (physical pin numbers, TQG144).
# Source: datasheets/xc6slx9_kipart.csv, the same table the generated symbol was built
# from. Bank grouping keeps each interface inside one VCCO domain (all banks = +3V3D).
# ---------------------------------------------------------------------------------

# Bank 0 — ADC capture side (24 data + 2 spare-free) + the global clock input.
_P_CLK_FPGA = 124                                    # IO_L37P_GCLK13_0 (clock-capable)
_P_ADC1_D = [111, 112, 114, 115, 116, 117,
             118, 119, 120, 121, 123, 126]           # D0(LSB) .. D11(MSB)
_P_ADC2_D = [127, 131, 132, 133, 134, 137,
             138, 139, 140, 141, 142, 143]           # D0(LSB) .. D11(MSB)
_P_HSWAPEN = 144                                     # IO_L1P_HSWAPEN_0 — config strap

# Bank 3 — SDRAM data bus + low address bits (all 26 bank-3 I/O used).
_P_SDR_DQ = [1, 2, 5, 6, 7, 8, 9, 10,
             11, 12, 14, 15, 16, 17, 21, 22]         # DQ0(LSB) .. DQ15(MSB)
_P_SDR_A_LO = [23, 24, 26, 27, 29, 30, 32, 33, 34, 35]   # A0 .. A9

# Bank 1 — SDRAM high address/control + ADC sideband + status LEDs.
_P_SDR_A_HI = [78, 79, 80]                           # A10, A11, A12
_P_SDR_BA = [81, 82]                                 # BA0, BA1
_P_SDR_CKE = 83
_P_SDR_CLK = 84                                      # IO_L43N_GCLK4_1 (clock-capable)
_P_SDR_CS_N = 85
_P_SDR_RAS_N = 87
_P_SDR_CAS_N = 88
_P_SDR_WE_N = 92
_P_SDR_LDQM = 93
_P_SDR_UDQM = 94
_P_ADC_PDWN = 95
_P_ADC1_OTR = 97
_P_ADC2_OTR = 98
_P_RESET_N = 99
_P_LED_RUN = 100
_P_LED_USB = 101

# Bank 2 — FX2LP slave-FIFO interface (shares the bank with the SPI config pins).
_P_FIFO_D = [40, 41, 43, 44, 45, 46, 47, 48]         # FD0(LSB) .. FD7(MSB)
_P_SLWR_N = 50
_P_SLRD_N = 51
_P_FLAGC = 55
_P_IFCLK = 56                                        # IO_L30P_GCLK1_D13_2 (clock-capable)
_P_SLOE_N = 57
_P_PKTEND_N = 58
_P_FIFOADR = [59, 61]                                # FIFOADR0, FIFOADR1
_P_FLAGB = 62

# Bank 2 — dual-purpose configuration pins (Master SPI boot from U31).
_P_CSO_B = 38                                        # IO_L65N_CSO_B_2   -> flash ~CS
_P_INIT_B = 39                                       # IO_L65P_INIT_B_2
_P_M1 = 60                                           # IO_L13P_M1_2
_P_MOSI = 64                                         # IO_L3N_MOSI_CSI_B_MISO0_2
_P_MISO = 65                                         # IO_L3P_D0_DIN_MISO_MISO1_2
_P_M0 = 69                                           # IO_L1N_M0_CMPMISO_2
_P_CCLK = 70                                         # IO_L1P_CCLK_2     -> flash CLK

# Dedicated configuration / JTAG pins (not part of the 102 user I/O).
_P_PROGRAM_B = 37
_P_DONE = 71
_P_CMPCS_B = 72
_P_SUSPEND = 73
_P_TDO, _P_TMS, _P_TCK, _P_TDI = 106, 107, 109, 110

# User I/O deliberately left unused (marked NC so ERC stays quiet).
#   66/67 = CMPMOSI/CMPCLK — kept clear of user logic because CMPCS_B is a reserved pin.
#   74/75 = DOUT_BUSY / AWAKE — daisy-chain and Suspend-feature pins, neither used.
_P_SPARE = [66, 67, 74, 75, 102, 104, 105]


@SubCircuit
def fpga_core(adc1_d, adc2_d, adc1_otr, adc2_otr, adc_pdwn, clk_fpga, sdr_dq, sdr_a,
              sdr_ba, sdr_clk, sdr_cke, sdr_cs_n, sdr_ras_n, sdr_cas_n, sdr_we_n,
              sdr_ldqm, sdr_udqm, fifo_d, ifclk, slwr_n, slrd_n, sloe_n, pktend_n,
              fifoadr, flagb, flagc, v3v3d, v1v2, gnd):
    """Spartan-6 XC6SLX9 capture engine, its SPI boot flash and the JTAG header.

    The FPGA is the only master in the data path: it samples both ADCs on CLK_FPGA,
    buffers into the SDRAM, and pushes 8-bit words into the FX2LP slave FIFO. It boots
    itself from U31 (W25Q32JVSSIQ) in Master SPI mode; JTAG (J4) is available at all
    times regardless of the mode pins.

    Args:
        adc1_d, adc2_d:  [in]  ADCn_D[11:0], 12-bit Bus each, bit 0 = LSB. Driven by the
                               two `adc_channel` blocks, sampled here.
        adc1_otr,
        adc2_otr:        [in]  Out-of-range flags from the two ADCs. Sensed only.
        adc_pdwn:        [out] Shared ADC power-down control. Driven by this block.
        clk_fpga:        [in]  10.000 MHz system clock from the `clocking` block, landed
                               on a GCLK-capable bank-0 pin (124). Sensed only.
        sdr_*:           [out/bidir] SDRAM interface to `buffer_memory`. SDR_DQ is
                               bidirectional; every other SDRAM net is FPGA-driven.
        fifo_d:          [bidir] FIFO_D[7:0] to the FX2LP slave FIFO (write path in this
                               design, but the FX2 can drive it, so treat as bidir).
        ifclk:           [in]  48 MHz FX2LP interface clock, on a GCLK-capable pin (56).
        slwr_n, slrd_n,
        sloe_n,
        pktend_n,
        fifoadr:         [out] FX2LP slave-FIFO control, all FPGA-driven.
        flagb, flagc:    [in]  FX2LP FIFO full/empty flags. Sensed only.
        v3v3d:           [in]  +3V3D — VCCAUX *and* all four VCCO banks (see below).
                               Consumed only; needs .drive = POWER at the top level.
        v1v2:            [in]  +1V2 — VCCINT only. Consumed only; .drive = POWER.
        gnd:             [in]  GND.

    Assumptions (see handoffs/05_blocks/fpga_core.md):
      - VCCAUX ties to +3V3D, not to an invented 2.5 V rail (DS162 Table 2 lists 3.3 V
        as an equally valid recommended operating condition) — phase-4 Decision #3.
      - All four VCCO banks run at 3.3 V: SDRAM, SPI flash, FX2LP and the ADC CMOS
        outputs are all 3.3 V parts, so no bank needs a different level.
      - Mode pins are tied *directly* (no resistors): UG380 p.24 states "The M1 and M0
        mode pins should be set at a constant DC voltage level and tied directly to
        ground or VCCO_2." Master Serial/SPI is M[1:0] = 01 (UG380 Table 2-1), so
        M0 -> +3V3D and M1 -> GND.
      - HSWAPEN is tied to GND so the internal pull-ups are enabled during
        configuration (UG380 Table 5-2): that holds every active-low SDRAM and FX2LP
        control line inactive-high while the FPGA is unconfigured. The cost is that the
        FPGA design must never drive pin 144 (IO_L1P_HSWAPEN_0) — it is strapped, not a
        usable I/O.
      - J4 is a 6-pin header and therefore carries VREF/GND + the four JTAG signals
        only; PROGRAM_B, INIT_B and DONE stay on-board (pull-ups R30/R34/R35).
    """
    # ---- Part templates (values/footprints verbatim from sourcing/sourced_bom.md) ----
    _r0402 = Part('Device', 'R', dest=TEMPLATE,
                  footprint='Resistor_SMD:R_0402_1005Metric')
    _r0603 = Part('Device', 'R', dest=TEMPLATE,
                  footprint='Resistor_SMD:R_0603_1608Metric')
    _c0402 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0402_1005Metric')
    _c0805 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0805_2012Metric')

    # ---- U30: XC6SLX9-2TQG144C -----------------------------------------------------
    U30 = Part('dual_adc_usb', 'XC6SLX9-2TQG144C', ref='U30',
               value='XC6SLX9-2TQG144C',
               footprint='Package_QFP:LQFP-144_20x20mm_P0.5mm')

    def _named(part, name):
        """Every pin carrying exactly this name (the FPGA has 13 GND, 5 VCCINT, ...)."""
        return [p for p in part.pins if p.name == name]

    # Supplies. VCCINT = +1V2; VCCAUX and all four VCCO banks = +3V3D.
    for _p in _named(U30, 'GND'):
        gnd += _p
    for _p in _named(U30, 'VCCINT'):
        v1v2 += _p
    for _name in ('VCCAUX', 'VCCO_BANK0', 'VCCO_BANK1', 'VCCO_BANK2', 'VCCO_BANK3'):
        for _p in _named(U30, _name):
            v3v3d += _p

    # ---- Capture-side interface (bank 0) -------------------------------------------
    clk_fpga += U30[_P_CLK_FPGA]
    for i, pin in enumerate(_P_ADC1_D):
        adc1_d[i] += U30[pin]
    for i, pin in enumerate(_P_ADC2_D):
        adc2_d[i] += U30[pin]

    # ---- SDRAM interface (banks 3 and 1) -------------------------------------------
    for i, pin in enumerate(_P_SDR_DQ):
        sdr_dq[i] += U30[pin]
    for i, pin in enumerate(_P_SDR_A_LO + _P_SDR_A_HI):          # A0..A12
        sdr_a[i] += U30[pin]
    for i, pin in enumerate(_P_SDR_BA):                          # BA0..BA1
        sdr_ba[i] += U30[pin]
    sdr_clk += U30[_P_SDR_CLK]
    sdr_cke += U30[_P_SDR_CKE]
    sdr_cs_n += U30[_P_SDR_CS_N]
    sdr_ras_n += U30[_P_SDR_RAS_N]
    sdr_cas_n += U30[_P_SDR_CAS_N]
    sdr_we_n += U30[_P_SDR_WE_N]
    sdr_ldqm += U30[_P_SDR_LDQM]
    sdr_udqm += U30[_P_SDR_UDQM]

    # ---- ADC sideband (bank 1) ------------------------------------------------------
    adc_pdwn += U30[_P_ADC_PDWN]
    adc1_otr += U30[_P_ADC1_OTR]
    adc2_otr += U30[_P_ADC2_OTR]

    # ---- FX2LP slave-FIFO interface (bank 2) ---------------------------------------
    for i, pin in enumerate(_P_FIFO_D):
        fifo_d[i] += U30[pin]
    for i, pin in enumerate(_P_FIFOADR):
        fifoadr[i] += U30[pin]
    ifclk += U30[_P_IFCLK]
    slwr_n += U30[_P_SLWR_N]
    slrd_n += U30[_P_SLRD_N]
    sloe_n += U30[_P_SLOE_N]
    pktend_n += U30[_P_PKTEND_N]
    flagb += U30[_P_FLAGB]
    flagc += U30[_P_FLAGC]

    # ---- Configuration straps -------------------------------------------------------
    # Master Serial/SPI = M[1:0] = 01 (UG380 v2.11 Table 2-1), tied directly per UG380
    # p.24. HSWAPEN low -> internal I/O pull-ups enabled during configuration
    # (UG380 Table 5-2). SUSPEND must be grounded when the Suspend feature is unused
    # (UG380 Table 5-1).
    v3v3d += U30[_P_M0]
    gnd += U30[_P_M1]
    gnd += U30[_P_HSWAPEN]
    gnd += U30[_P_SUSPEND]

    # Config-pin pull-ups. Values are UG380 Figure 2-12's own: 4.7 kR on PROGRAM_B and
    # INIT_B, 330 R on DONE (note 11 — required for iMPACT indirect flash programming).
    PROGRAM_B = Net('PROGRAM_B')
    INIT_B = Net('INIT_B')
    DONE = Net('DONE')
    CMPCS_B = Net('CMPCS_B')

    R30 = _r0402(value='4.7k', ref='R30')   # PROGRAM_B pull-up
    R34 = _r0402(value='4.7k', ref='R34')   # INIT_B pull-up (open-drain pin)
    R35 = _r0402(value='330', ref='R35')    # DONE pull-up
    R36 = _r0402(value='4.7k', ref='R36')   # CSO_B / SPI_CS_N pull-up
    R37 = _r0402(value='4.7k', ref='R37')   # CMPCS_B (reserved input) pull-up

    PROGRAM_B += U30[_P_PROGRAM_B], R30[1]
    R30[2] += v3v3d
    INIT_B += U30[_P_INIT_B], R34[1]
    R34[2] += v3v3d
    DONE += U30[_P_DONE], R35[1]
    R35[2] += v3v3d
    # CMPCS_B is a reserved input: UG380 Table 5-1 says "Leave unconnected or pull up".
    CMPCS_B += U30[_P_CMPCS_B], R37[1]
    R37[2] += v3v3d

    # FPGA_RESET_N — user reset input, pulled high (net_plan.md: U30 + R31 10 kR).
    FPGA_RESET_N = Net('FPGA_RESET_N')
    R31 = _r0402(value='10k', ref='R31')
    FPGA_RESET_N += U30[_P_RESET_N], R31[1]
    R31[2] += v3v3d

    # ---- U31: W25Q32JVSSIQ SPI configuration flash ---------------------------------
    # Master SPI boot: FPGA CSO_B -> ~CS, CCLK -> CLK, MOSI -> DI, DIN/MISO <- DO.
    # Pins referenced by number: the KiCad symbol names carry ~{} overbar markup.
    U31 = Part('Memory_Flash', 'W25Q32JVSS', ref='U31', value='W25Q32JVSSIQ',
               footprint='Package_SO:SOIC-8_5.3x5.3mm_P1.27mm')  # SS = 208 mil

    SPI_CS_N = Net('SPI_CS_N')
    SPI_SCK = Net('SPI_SCK')
    SPI_MOSI = Net('SPI_MOSI')
    SPI_MISO = Net('SPI_MISO')

    SPI_CS_N += U30[_P_CSO_B], U31[1], R36[1]       # CSO_B keeps the flash deselected
    R36[2] += v3v3d                                 #   once the FPGA releases the pin
    SPI_SCK += U30[_P_CCLK], U31[6]
    SPI_MOSI += U30[_P_MOSI], U31[5]                # FPGA MOSI -> flash DI/IO0
    SPI_MISO += U30[_P_MISO], U31[2]                # flash DO/IO1 -> FPGA DIN/MISO
    U31[8] += v3v3d
    U31[4] += gnd

    # ~WP and ~HOLD are unused in single-bit SPI boot and must be tied off (UG380
    # Figure 2-12 note 8); pulled up rather than hard-tied so quad mode stays possible.
    R38 = _r0402(value='10k', ref='R38')
    R39 = _r0402(value='10k', ref='R39')
    U31[3] += R38[1]                                # ~WP/IO2
    R38[2] += v3v3d
    U31[7] += R39[1]                                # ~HOLD/~RESET/IO3
    R39[2] += v3v3d

    C59 = _c0402(value='100nF', ref='C59')          # U31 VCC decoupling
    C59[1] += v3v3d
    C59[2] += gnd

    # ---- J4: JTAG header (2x3, 1.27 mm) --------------------------------------------
    # 1 = VREF (+3V3D), 2 = GND, 3 = TMS, 4 = TCK, 5 = TDO, 6 = TDI.
    J4 = Part('Connector_Generic', 'Conn_02x03_Odd_Even', ref='J4',
              value='JTAG 2x3 1.27mm',
              footprint='Connector_PinHeader_1.27mm:PinHeader_2x03_P1.27mm_Vertical_SMD')
    TMS, TCK, TDO, TDI = Net('TMS'), Net('TCK'), Net('TDO'), Net('TDI')
    J4[1] += v3v3d
    J4[2] += gnd
    TMS += J4[3], U30[_P_TMS]
    TCK += J4[4], U30[_P_TCK]
    TDO += J4[5], U30[_P_TDO]
    TDI += J4[6], U30[_P_TDI]

    # ---- Status LEDs ----------------------------------------------------------------
    # net_plan.md: U30 -> R32/R33 (1 kR) -> D30/D31 -> GND (active-high drive).
    # Device:LED is pin 1 = K, pin 2 = A, so the anode is wired explicitly rather than
    # through a `&` chain, which would have landed the cathode on the resistor.
    LED_RUN, LED_USB = Net('LED_RUN'), Net('LED_USB')
    R32 = _r0603(value='1k', ref='R32')
    R33 = _r0603(value='1k', ref='R33')
    D30 = Part('Device', 'LED', ref='D30', value='GREEN',
               footprint='LED_SMD:LED_0603_1608Metric')
    D31 = Part('Device', 'LED', ref='D31', value='RED',
               footprint='LED_SMD:LED_0603_1608Metric')

    LED_RUN += U30[_P_LED_RUN], R32[1]
    R32[2] += D30['A']
    D30['K'] += gnd
    LED_USB += U30[_P_LED_USB], R33[1]
    R33[2] += D31['A']
    D31['K'] += gnd

    # ---- Unused user I/O -------------------------------------------------------------
    for pin in _P_SPARE:
        U30[pin] += NC

    # ---- Decoupling ------------------------------------------------------------------
    # One 100 nF per supply pin (C40-C58; VCCAUX pins 36/90 share their neighbours'
    # caps — VCCAUX draws only a few mA), plus ten 4.7 uF bulk caps weighted toward
    # VCCINT and the SDRAM bank. Placement intent is in the comments; electrically each
    # cap is rail-to-GND.
    _c100n_plan = [
        # (ref, rail, pin it sits next to)
        ('C40', v1v2, 19), ('C41', v1v2, 28), ('C42', v1v2, 52),
        ('C43', v1v2, 89), ('C44', v1v2, 128),                       # VCCINT x5
        ('C45', v3v3d, 20), ('C46', v3v3d, 53), ('C47', v3v3d, 129),  # VCCAUX x3
        ('C48', v3v3d, 122), ('C49', v3v3d, 125), ('C50', v3v3d, 135),  # VCCO_BANK0
        ('C51', v3v3d, 76), ('C52', v3v3d, 86), ('C53', v3v3d, 103),   # VCCO_BANK1
        ('C54', v3v3d, 42), ('C55', v3v3d, 63),                        # VCCO_BANK2
        ('C56', v3v3d, 4), ('C57', v3v3d, 18), ('C58', v3v3d, 31),     # VCCO_BANK3
    ]
    for ref, rail, _pin in _c100n_plan:
        c = _c0402(value='100nF', ref=ref)
        c[1] += rail
        c[2] += gnd

    _c4u7_plan = [
        ('C60', v1v2), ('C61', v1v2), ('C62', v1v2), ('C63', v1v2),  # VCCINT bulk
        ('C64', v3v3d),                                              # VCCAUX bulk
        ('C65', v3v3d), ('C66', v3v3d), ('C67', v3v3d),              # banks 0/1/2
        ('C68', v3v3d), ('C69', v3v3d),                              # bank 3 (SDRAM)
    ]
    for ref, rail in _c4u7_plan:
        c = _c0805(value='4.7uF', ref=ref)
        c[1] += rail
        c[2] += gnd
