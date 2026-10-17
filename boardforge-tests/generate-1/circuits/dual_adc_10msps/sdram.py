"""SDRAM — W9812G6KH-6 16 MB (2M x 16 x 4 banks) SDR SDRAM capture buffer
Block from: architecture/block_diagram.md (connections: architecture/net_plan.md Block 7)
Interface nets: SD_DQ0..15, SD_A0..11, SD_BA0..1, SD_CLK, SD_CKE, SD_CS_N, SD_RAS_N,
                SD_CAS_N, SD_WE_N, SD_LDQM, SD_UDQM, +3V3, GND
"""
from skidl import *

_FP_C0402 = 'Capacitor_SMD:C_0402_1005Metric'
_FP_C0603 = 'Capacitor_SMD:C_0603_1608Metric'
_FP_R0402 = 'Resistor_SMD:R_0402_1005Metric'


def _res(ref, value, mpn, lcsc):
    r = Part('Device', 'R', ref=ref, value=value, footprint=_FP_R0402)
    r.fields['MPN'] = mpn
    r.fields['LCSC'] = lcsc
    return r


@SubCircuit
def sdram(sd_dq, sd_a, sd_ba, sd_clk, sd_cke, sd_cs_n, sd_ras_n, sd_cas_n, sd_we_n,
          sd_ldqm, sd_udqm, v3v3, gnd):
    """U801 W9812G6KH-6 on the FPGA SDRAM bus.

    Inputs (driven by FPGA): sd_a (12-wide Bus), sd_ba (2-wide), sd_clk (via R801 22R
    series into local SD_CLK_M), sd_cke (R802 10k pull-down: CKE low = SDRAM idle while
    FPGA unconfigured), sd_cs_n (R803 10k pull-up: deselected), sd_ras_n, sd_cas_n,
    sd_we_n, sd_ldqm, sd_udqm. Bidirectional: sd_dq (16-wide Bus). Buses index 0 = LSB.
    Power: v3v3 -> VDD/VDDQ (7 pins, 0.1 uF each + 10 uF bulk), gnd -> VSS/VSSQ.
    Assumption: pinout/VDD range from the W9812G6JH datasheet (KH datasheet not obtained);
    JEDEC TSOP-54 x16 and the KiCad W9812G6KH-6 symbol agree.
    """
    u = Part('Memory_RAM', 'W9812G6KH-6', ref='U801', value='W9812G6KH-6',
             footprint='Package_SO:TSOP-II-54_22.2x10.16mm_P0.8mm')
    u.fields['MPN'] = 'W9812G6KH-6'
    u.fields['LCSC'] = 'C62379'

    # ---- Power: VDD 1, 14, 27; VDDQ 3, 9, 43, 49. GND: VSS 28, 41, 54; VSSQ 6, 12, 46, 52 ----
    vdd_pins = (1, 3, 9, 14, 27, 43, 49)
    for p in vdd_pins:
        v3v3 += u[p]
    for p in (6, 12, 28, 41, 46, 52, 54):
        gnd += u[p]
    for i in range(7):           # C801-C807: one 0.1 uF per supply pin
        c = Part('Device', 'C', ref=f'C80{i + 1}', value='100n', footprint=_FP_C0402)
        c.fields['MPN'] = 'CL05B104KB54PNC'
        c.fields['LCSC'] = 'C307331'
        v3v3 += c[1]
        gnd += c[2]
    c808 = Part('Device', 'C', ref='C808', value='10u', footprint=_FP_C0603)
    c808.fields['MPN'] = 'CL10A106KP8NNNC'
    c808.fields['LCSC'] = 'C19702'
    v3v3 += c808[1]
    gnd += c808[2]

    # ---- Data DQ0-15 ----
    dq_pins = (2, 4, 5, 7, 8, 10, 11, 13, 42, 44, 45, 47, 48, 50, 51, 53)
    for i, p in enumerate(dq_pins):
        sd_dq[i] += u[p]

    # ---- Address A0-A11 (A10/AP pin 22, A11 pin 35), bank BS0/BS1 ----
    a_pins = (23, 24, 25, 26, 29, 30, 31, 32, 33, 34, 22, 35)
    for i, p in enumerate(a_pins):
        sd_a[i] += u[p]
    sd_ba[0] += u[20]
    sd_ba[1] += u[21]

    # ---- Control ----
    sd_ras_n += u[18]
    sd_cas_n += u[17]
    sd_we_n += u[16]
    sd_cs_n += u[19]
    sd_cke += u[37]
    sd_ldqm += u[15]
    sd_udqm += u[39]

    # SD_CLK -> R801 22R -> SD_CLK_M -> CLK 38
    clk_m = Net('SD_CLK_M')
    r801 = _res('R801', '22', '0402WGF220JTCE', 'C25092')
    sd_clk += r801[1]
    clk_m += r801[2], u[38]

    # CKE 10k pull-down, CS# 10k pull-up
    r802 = _res('R802', '10k', '0402WGF1002TCE', 'C25744')
    sd_cke += r802[1]
    gnd += r802[2]
    r803 = _res('R803', '10k', '0402WGF1002TCE', 'C25744')
    sd_cs_n += r803[1]
    v3v3 += r803[2]

    # ---- NC: pin 36 (A12 on W9825G6KH second source), pin 40 ----
    u[36] += NC
    u[40] += NC
