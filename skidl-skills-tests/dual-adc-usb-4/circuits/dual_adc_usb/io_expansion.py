"""I/O Expansion — status LEDs, external trigger/GPIO header, 1.8 V <-> 3.3 V/5 V level translation
Block from: architecture/block_diagram.md
Interface nets: LED_STAT_1V8, LED_ACT_1V8, TRIG_OUT_1V8, GPIO_OUT_1V8, TRIG_IN_1V8, VD_3V3, VD_1V8, GND
Net plan: architecture/net_plan.md §9 (io_expansion).
Parts: sourcing/sourced_bom.md rows U16, U17, LED2, LED3, R80–R85, C96, C97, J5.
"""
from skidl import *

_R_FP = 'Resistor_SMD:R_0402_1005Metric'
_C_FP = 'Capacitor_SMD:C_0402_1005Metric'
_RES = {  # value -> (MPN, LCSC)
    '100': ('0402WGF1000TCE', 'C25076'),
    '1k': ('0402WGF1001TCE', 'C11702'),
    '100k': ('0402WGF1003TCE', 'C25741'),
}


def _res(ref, value, a, b):
    """One 0402 1% resistor between nets a and b."""
    mpn, lcsc = _RES[value]
    r = Part('Device', 'R', ref=ref, value=value, footprint=_R_FP, MPN=mpn, LCSC=lcsc)
    a & r & b


def _decap(ref, rail, gnd):
    """100 nF 0402 decoupling capacitor from rail to gnd."""
    c = Part('Device', 'C', ref=ref, value='100nF', footprint=_C_FP,
             MPN='CL05B104KB54PNC', LCSC='C307331')
    rail & c & gnd


@SubCircuit
def io_expansion(led_stat_1v8, led_act_1v8, trig_out_1v8, gpio_out_1v8, trig_in_1v8,
                 vd_3v3, vd_1v8, gnd):
    """Up-translate four 1.8 V FPGA outputs to 3.3 V (U16) and down-translate one ≤5 V input (U17).

    Args:
        led_stat_1v8, led_act_1v8, trig_out_1v8, gpio_out_1v8: 1.8 V inputs from FPGA bank 3
            (sensed here by U16 1A/2A/3A/4A).
        trig_in_1v8: 1.8 V output to FPGA pin 83, driven by U17.Y.
        vd_3v3: U16 VCC and J5 pin 1 (consumed).
        vd_1v8: U17 VCC (consumed).
        gnd: single ground net.
    Assumptions:
        - U16 SN74LV4T125 at VCC = 3.3 V accepts 1.8 V logic inputs (LVxT reduced thresholds).
          All four OE# pins are tied to GND, so the buffers are always enabled (net_plan §9).
        - U17 SN74LV1T34 at VCC = 1.8 V has a 5.5 V-tolerant input. R84 (1 kΩ) limits current
          into it and R85 (100 kΩ) holds EXT_TRIG_IN low when the header is open.
    """
    # --- Local nets (net_plan §9). The "_R" suffix marks the IC side of a series resistor. ---
    led_stat, led_act = Net('LED_STAT'), Net('LED_ACT')
    led_stat_k, led_act_k = Net('LED_STAT_K'), Net('LED_ACT_K')   # R -> LED anode (plan's names)
    ext_trig_out_r, ext_trig_out = Net('EXT_TRIG_OUT_R'), Net('EXT_TRIG_OUT')
    ext_gpio_out_r, ext_gpio_out = Net('EXT_GPIO_OUT_R'), Net('EXT_GPIO_OUT')
    ext_trig_in, ext_trig_in_r = Net('EXT_TRIG_IN'), Net('EXT_TRIG_IN_R')

    # --- U16 SN74LV4T125 quad buffer, 1.8 V -> 3.3 V (symbol pins are unnamed; use numbers) ---
    # 1 1OE#, 2 1A, 3 1Y, 4 2OE#, 5 2A, 6 2Y, 7 GND, 8 3Y, 9 3A, 10 3OE#, 11 4Y, 12 4A, 13 4OE#, 14 VCC
    u16 = Part('74xx', 'SN74LV4T125', ref='U16', value='SN74LV4T125PWR',
               footprint='Package_SO:TSSOP-14_4.4x5mm_P0.65mm', MPN='SN74LV4T125PWR', LCSC='C90755')
    u16[14] += vd_3v3
    u16[7] += gnd
    u16[1, 4, 10, 13] += gnd                     # all OE# low -> always enabled
    u16[2] += led_stat_1v8
    u16[3] += led_stat
    u16[5] += led_act_1v8
    u16[6] += led_act
    u16[9] += trig_out_1v8
    u16[8] += ext_trig_out_r
    u16[12] += gpio_out_1v8
    u16[11] += ext_gpio_out_r
    _decap('C96', vd_3v3, gnd)

    # --- Status LEDs: U16.Y -> 1 kΩ -> LED -> GND ---
    led_t = Part('Device', 'LED', dest=TEMPLATE, footprint='LED_SMD:LED_0603_1608Metric',
                 MPN='CT-1608UGC-P4', LCSC='C52675989')
    led2 = led_t(ref='LED2', value='GRN_STAT')
    led3 = led_t(ref='LED3', value='GRN_ACT')
    _res('R80', '1k', led_stat, led_stat_k)
    _res('R81', '1k', led_act, led_act_k)
    led2['A'] += led_stat_k
    led2['K'] += gnd
    led3['A'] += led_act_k
    led3['K'] += gnd

    # --- Header outputs: 100 Ω series ---
    _res('R82', '100', ext_trig_out_r, ext_trig_out)
    _res('R83', '100', ext_gpio_out_r, ext_gpio_out)

    # --- Trigger input: J5.2 -> R84 1 kΩ -> U17.A, R85 100 kΩ pull-down at the header ---
    _res('R84', '1k', ext_trig_in, ext_trig_in_r)
    _res('R85', '100k', ext_trig_in, gnd)
    u17 = Part('Logic_LevelTranslator', 'SN74LV1T34DCK', ref='U17', value='SN74LV1T34DCKR',
               footprint='Package_TO_SOT_SMD:SOT-353_SC-70-5', MPN='SN74LV1T34DCKR', LCSC='C78541')
    u17['VCC'] += vd_1v8
    u17['GND'] += gnd
    u17['A'] += ext_trig_in_r
    u17['Y'] += trig_in_1v8
    u17['NC'] += NC                              # pin 1, no internal connection
    _decap('C97', vd_1v8, gnd)

    # --- J5 1x6 header: 1 VD_3V3, 2 EXT_TRIG_IN, 3 EXT_TRIG_OUT, 4 EXT_GPIO_OUT, 5 GND, 6 GND ---
    j5 = Part('Connector_Generic', 'Conn_01x06', ref='J5', value='EXT_IO',
              footprint='Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical', LCSC='C37208')
    j5[1] += vd_3v3
    j5[2] += ext_trig_in
    j5[3] += ext_trig_out
    j5[4] += ext_gpio_out
    j5[5, 6] += gnd
