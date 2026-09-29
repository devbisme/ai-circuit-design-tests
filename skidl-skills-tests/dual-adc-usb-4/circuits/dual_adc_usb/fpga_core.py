"""FPGA Core — GW1NR-LV9QN88PC6/I5 (U15), boot-mode/JTAG straps, JTAG header, decoupling
Block from: architecture/block_diagram.md
Interface nets: ADC_DA0…ADC_DA11, ADC_DB0…ADC_DB11, ADC_OVRA, ADC_OVRB, ADC_DVA, ADC_SEL,
    ADC_SEN, ADC_SCLK, ADC_SDATA, ADC_CLK_FPGA, FT_D0…FT_D7, FT_RXF_N, FT_TXE_N, FT_RD_N,
    FT_WR_N, FT_OE_N, FT_SIWU_N, FT_CLKOUT, LED_STAT_1V8, LED_ACT_1V8, TRIG_OUT_1V8,
    GPIO_OUT_1V8, TRIG_IN_1V8, VD_3V3, VD_1V8, VD_1V2, GND
Pin map: architecture/net_plan.md §8 (bank assignment confirmed by driver against UG119E
    Fig. 3-8: pins 48-63/68-77 = bank 1, pins 3-11/13-16/79-88 = bank 3, bank 0 has no user I/O).
"""
from skidl import *

_R_FP = 'Resistor_SMD:R_0402_1005Metric'
_C0402_FP = 'Capacitor_SMD:C_0402_1005Metric'
_C0603_FP = 'Capacitor_SMD:C_0603_1608Metric'


def _cap(ref, value, rail, gnd):
    """One decoupling capacitor from `rail` to `gnd` (MPN/LCSC per sourcing/sourced_bom.md)."""
    if value == '100nF':
        fp, mpn, lcsc = _C0402_FP, 'CL05B104KB54PNC', 'C307331'
    elif value == '10uF':
        fp, mpn, lcsc = _C0603_FP, 'CL10A106MA8NRNC', 'C96446'
    else:  # 4.7uF
        fp, mpn, lcsc = _C0603_FP, 'CL10A475KO8NNNC', 'C19666'
    c = Part('Device', 'C', ref=ref, value=value, footprint=fp, MPN=mpn, LCSC=lcsc)
    rail & c & gnd


def _res(ref, value, a, b):
    """One 0402 1% resistor between nets a and b."""
    mpn, lcsc = {'1k': ('0402WGF1001TCE', 'C11702'),
                 '4.7k': ('0402WGF4701TCE', 'C25900'),
                 '10k': ('0402WGF1002TCE', 'C25744')}[value]
    r = Part('Device', 'R', ref=ref, value=value, footprint=_R_FP, MPN=mpn, LCSC=lcsc)
    a & r & b


@SubCircuit
def fpga_core(adc_da, adc_db, adc_ovra, adc_ovrb, adc_dva, adc_sel, adc_sen, adc_sclk,
              adc_sdata, adc_clk_fpga, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_oe_n,
              ft_siwu_n, ft_clkout, led_stat_1v8, led_act_1v8, trig_out_1v8, gpio_out_1v8,
              trig_in_1v8, vd_3v3, vd_1v8, vd_1v2, gnd):
    """GW1NR-9 FPGA with power, decoupling, boot straps, JTAG header and spare test point.

    Args:
        adc_da, adc_db: 12-bit buses (ADC_DA0..11, ADC_DB0..11), inputs from ADS5231.
        adc_ovra, adc_ovrb: ADC over-range inputs.
        adc_dva, adc_sel, adc_sen, adc_sclk, adc_sdata: ADC control/serial outputs from FPGA.
        adc_clk_fpga: 20 MHz sample clock input on GCLKT_4 (pin 35, fixed).
        ft_d: 8-bit bidirectional FT232H FIFO data bus (FT_D0..7).
        ft_rxf_n, ft_txe_n, ft_clkout: FT232H status/clock inputs (FT_CLKOUT on GCLKT_3, pin 52).
        ft_rd_n, ft_wr_n, ft_oe_n, ft_siwu_n: FT232H FIFO strobes driven by FPGA.
        led_stat_1v8, led_act_1v8, trig_out_1v8, gpio_out_1v8: 1.8 V outputs (bank 3) to U16.
        trig_in_1v8: 1.8 V input (bank 3) from U17.
        vd_3v3: VCCX/VCCIO0, VCCIO1, VCCIO2.  vd_1v8: VCCIO3 + JTAG VREF.  vd_1v2: core VCC.
        gnd: VSS pins + exposed pad (pin 89).
    Assumes all three rails are driven (POWER) by the power_rails block.
    """
    u15 = Part('dual_adc_usb', 'GW1NR-LV9QN88PC6/I5', ref='U15', value='GW1NR-LV9QN88PC6/I5',
               footprint='Package_DFN_QFN:ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm',
               MPN='GW1NR-LV9QN88PC6/I5', LCSC='C5799578')

    # ---------------- Power ----------------
    for p in (1, 22, 45, 66):            # VCC core
        u15[p] += vd_1v2
    for p in (64, 67, 78):               # VCCX/VCCIO0
        u15[p] += vd_3v3
    u15[58] += vd_3v3                    # VCCIO1
    for p in (23, 44):                   # VCCIO2
        u15[p] += vd_3v3
    u15[12] += vd_1v8                    # VCCIO3 (bank 3 @ 1.8 V)
    for p in (2, 21, 24, 43, 46, 65, 89):  # VSS + exposed pad
        u15[p] += gnd

    # Decoupling (net_plan §8): per-rail 0.1 uF at each pin group + bulk.
    for ref in ('C80', 'C81', 'C82', 'C83'):
        _cap(ref, '100nF', vd_1v2, gnd)
    _cap('C84', '10uF', vd_1v2, gnd)
    for ref in ('C85', 'C86', 'C87'):      # VCCX/VCCIO0
        _cap(ref, '100nF', vd_3v3, gnd)
    _cap('C88', '10uF', vd_3v3, gnd)
    _cap('C89', '100nF', vd_3v3, gnd)      # VCCIO1
    _cap('C90', '4.7uF', vd_3v3, gnd)
    for ref in ('C91', 'C92'):             # VCCIO2
        _cap(ref, '100nF', vd_3v3, gnd)
    _cap('C93', '4.7uF', vd_3v3, gnd)
    _cap('C94', '100nF', vd_1v8, gnd)      # VCCIO3
    _cap('C95', '4.7uF', vd_1v8, gnd)

    # ---------------- Bank 2 (3.3 V): ADC channel A, most of channel B, sample clock ----------------
    for bit, pin in enumerate((17, 18, 19, 20, 25, 26, 27, 28, 29, 30, 31, 32)):
        u15[pin] += adc_da[bit]
    for bit, pin in zip(range(2, 12), (33, 34, 36, 37, 38, 39, 40, 41, 42, 47)):
        u15[pin] += adc_db[bit]
    u15[35] += adc_clk_fpga              # GCLKT_4 — fixed pin

    # ---------------- Bank 1 (3.3 V): ADC DB0/1, OVR, control; FT232H FIFO ----------------
    u15[48] += adc_db[0]
    u15[49] += adc_db[1]
    u15[50] += adc_ovrb
    u15[51] += adc_ovra
    u15[52] += ft_clkout                 # GCLKT_3 — fixed pin
    for bit, pin in enumerate((53, 54, 55, 56, 57, 59, 60, 61)):
        u15[pin] += ft_d[bit]
    u15[62] += ft_rxf_n
    u15[63] += ft_txe_n
    u15[68] += ft_rd_n
    u15[69] += ft_wr_n
    u15[70] += ft_oe_n
    u15[71] += ft_siwu_n
    u15[72] += adc_dva
    u15[73] += adc_sel
    u15[74] += adc_sen
    u15[75] += adc_sclk
    u15[76] += adc_sdata

    spare_b1 = Net('SPARE_B1')
    u15[77] += spare_b1
    tp10 = Part('Connector', 'TestPoint', ref='TP10', value='SPARE_B1',
                footprint='TestPoint:TestPoint_Pad_D1.5mm')
    tp10[1] += spare_b1

    # ---------------- Bank 3 (1.8 V): JTAG, config, I/O-expansion signals ----------------
    jtag_tms = Net('JTAG_TMS')
    jtag_tck = Net('JTAG_TCK')
    jtag_tdi = Net('JTAG_TDI')
    jtag_tdo = Net('JTAG_TDO')
    reconfig_n = Net('FPGA_RECONFIG_N')
    jtagsel_n = Net('FPGA_JTAGSEL_N')
    mode0 = Net('FPGA_MODE0')
    mode1 = Net('FPGA_MODE1')

    u15[5] += jtag_tms
    u15[6] += jtag_tck
    u15[7] += jtag_tdi
    u15[8] += jtag_tdo
    u15[9] += reconfig_n
    u15[4] += jtagsel_n
    u15[87] += mode1
    u15[88] += mode0

    u15[79] += led_stat_1v8
    u15[80] += led_act_1v8
    u15[81] += trig_out_1v8
    u15[82] += gpio_out_1v8
    u15[83] += trig_in_1v8

    # Unused bank-3 I/O (net_plan §8). Pin 11 = GCLKT_6.
    for p in (3, 11, 13, 14, 15, 16, 84, 85, 86):
        u15[p] += NC

    # Straps — verified against UG290 v2.9.1E (datasheets/GW1NR-9-UG290-config.pdf):
    # Table 5-1 MODE[2:0]=000 = AUTO BOOT (MODE2 unbonded, grounded internally);
    # §"Dual-purpose Pin Configuration": 4.7 k pull-up or 1 k pull-down on MODE pins;
    # TCK needs a 4.7 k pull-down; DONE and RECONFIG_N: pull-up recommended.
    fpga_done = Net('FPGA_DONE')
    u15[10] += fpga_done                   # DONE (IOL14A, UG803)
    _res('R70', '1k', mode0, gnd)          # MODE0 low  } MODE[2:0]=000 auto-boot internal flash
    _res('R71', '1k', mode1, gnd)          # MODE1 low  }
    _res('R72', '10k', reconfig_n, vd_1v8)  # RECONFIG_N pull-up
    _res('R73', '4.7k', jtag_tck, gnd)     # TCK pull-down
    _res('R74', '10k', jtagsel_n, vd_1v8)  # JTAGSEL_N high keeps JTAG enabled
    _res('R75', '4.7k', fpga_done, vd_1v8)  # DONE pull-up (open-drain status)

    # JTAG header J4 (1x7, 1.8 V only — programmer must follow VREF)
    j4 = Part('Connector_Generic', 'Conn_01x07', ref='J4', value='JTAG_1V8',
              footprint='Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical',
              LCSC='C492406')
    j4[1] += vd_1v8      # VREF
    j4[2] += jtag_tms
    j4[3] += jtag_tck
    j4[4] += jtag_tdo
    j4[5] += jtag_tdi
    j4[6] += reconfig_n
    j4[7] += gnd
