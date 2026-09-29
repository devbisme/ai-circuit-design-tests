"""Buffer Memory — 32 MB (256 Mbit x16) SDR SDRAM sample buffer, W9825G6KH-6I
Block from: architecture/block_diagram.md
Interface nets: SDR_DQ[15:0], SDR_A[12:0], SDR_BA[1:0], SDR_CLK, SDR_CKE, SDR_CS_N,
                SDR_RAS_N, SDR_CAS_N, SDR_WE_N, SDR_LDQM, SDR_UDQM, +3V3D, GND
"""
from skidl import *


# ---------------------------------------------------------------------------------
# W9825G6KH-6I pin names, taken verbatim from the generated symbol
# `symbols/dual_adc_usb.kicad_sym:W9825G6KH-6I` (54 pins, TSOP-II-54), which was built
# from `datasheets/sdram_kipart.csv`. Verified against
# `datasheets/W9825G6KH-6I_SUMMARY.md`'s pin table.
#
# Two naming traps this block has to respect and the assembler must not "clean up":
#   * bank-select pins are named BS0/BS1 on this symbol, not BA0/BA1 (net_plan.md
#     calls the nets SDR_BA[1:0]);
#   * address bit 10 is named 'A10/AP' (row address / auto-precharge dual function),
#     so it cannot be reached by a plain 'A10' lookup.
# Exact-name lookup was confirmed non-ambiguous under SKiDL 3.0.0 — 'A1' resolves to
# pin 24 only, it does not also catch 'A10/AP'.
# ---------------------------------------------------------------------------------

# SDR_DQ[15:0] — bit 0 = LSB, matching fpga_core's bus ordering.
_N_DQ = [f'DQ{i}' for i in range(16)]

# SDR_A[12:0] — bit 0 = LSB. Index 10 is the dual-function A10/AP pin.
_N_A = ['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9',
        'A10/AP', 'A11', 'A12']

# SDR_BA[1:0] — bit 0 = BA0.
_N_BA = ['BS0', 'BS1']


@SubCircuit
def buffer_memory(sdr_dq, sdr_a, sdr_ba, sdr_clk, sdr_cke, sdr_cs_n, sdr_ras_n,
                  sdr_cas_n, sdr_we_n, sdr_ldqm, sdr_udqm, v3v3d, gnd):
    """32 MB SDR SDRAM sample buffer (U40) hanging off the FPGA's memory controller.

    The whole block is one SDRAM plus its series clock termination and decoupling.
    Every signal here is driven by `fpga_core` (U30); this block drives nothing except
    the data bus during reads.

    Args:
        sdr_dq:    [bidir] SDR_DQ[15:0], 16-bit Bus, bit 0 = LSB = DQ0. Shared with U30.
        sdr_a:     [in]  SDR_A[12:0], 13-bit Bus, bit 0 = LSB = A0. Driven by U30 only.
        sdr_ba:    [in]  SDR_BA[1:0], 2-bit Bus, bit 0 = BA0. Driven by U30 only.
        sdr_clk:   [in]  100 MHz SDRAM clock from U30. Lands on R40 (22 R series
                         termination), NOT directly on U40.CLK — see net_plan.md row
                         "U30 -> R40 (22 ohm) -> U40.CLK". The damped node is local to
                         this block, so the assembler's SDR_CLK net stops at R40.
        sdr_cke:   [in]  Clock enable, driven by U30.
        sdr_cs_n,
        sdr_ras_n,
        sdr_cas_n,
        sdr_we_n:  [in]  Command bus, active low, driven by U30.
        sdr_ldqm,
        sdr_udqm:  [in]  Byte data masks, driven by U30.
        v3v3d:     [in]  +3V3D, 3.318 V. The SDRAM is a pure consumer of this rail, so
                         the assembler must set SDR-side +3V3D `.drive = POWER`.
        gnd:       [in]  GND.

    Assumptions:
        * VDD and VDDQ are tied to the same +3V3D rail (net_plan.md lists U40 as a
          +3V3D load with no separate VDDQ rail). VSS and VSSQ likewise share GND.
          The W9825G6KH datasheet permits this; the split exists for board-level
          noise isolation, which is a layout matter, not a schematic one.
        * Pin 40 (NC) is deliberately left unconnected per the part summary.
        * CKE is driven by the FPGA rather than strapped high, so the controller can
          use self-refresh during idle periods.
    """

    # -----------------------------------------------------------------------------
    # U40 — Winbond W9825G6KH-6I, 256 Mbit (16M x 16) SDR SDRAM, TSOP-II-54.
    # sourcing/sourced_bom.md row U40: LCSC C97572.
    # -----------------------------------------------------------------------------
    U40 = Part('dual_adc_usb', 'W9825G6KH-6I', ref='U40', value='W9825G6KH-6I',
               footprint='Package_SO:TSOP-II-54_22.2x10.16mm_P0.8mm')

    # -----------------------------------------------------------------------------
    # Data / address / bank buses. Bit 0 = LSB everywhere, matching fpga_core.
    # net_plan.md rows SDR_DQ[15:0], SDR_A[12:0], SDR_BA[1:0].
    # -----------------------------------------------------------------------------
    for i, name in enumerate(_N_DQ):
        sdr_dq[i] += U40[name]
    for i, name in enumerate(_N_A):
        sdr_a[i] += U40[name]
    for i, name in enumerate(_N_BA):
        sdr_ba[i] += U40[name]

    # -----------------------------------------------------------------------------
    # Clock: 22 R series termination at the *source* would be ideal, but net_plan.md
    # places R40 in this block, so it sits at the receiver end of the incoming net.
    # 22 R is a compromise against the ~50 R trace impedance; it damps the reflection
    # off the SDRAM's high-Z CLK input without slowing the 100 MHz edge appreciably.
    # -----------------------------------------------------------------------------
    R40 = Part('Device', 'R', ref='R40', value='22',
               footprint='Resistor_SMD:R_0402_1005Metric')
    sdr_clk += R40[1]
    R40[2] += U40['CLK']

    # -----------------------------------------------------------------------------
    # Control / command pins. All driven by U30; nothing here is bidirectional.
    # net_plan.md rows SDR_CKE, SDR_CS_N, SDR_RAS_N, SDR_CAS_N, SDR_WE_N,
    # SDR_LDQM, SDR_UDQM. Note the symbol spells the active-low pins with '#'.
    # -----------------------------------------------------------------------------
    sdr_cke += U40['CKE']
    sdr_cs_n += U40['CS#']
    sdr_ras_n += U40['RAS#']
    sdr_cas_n += U40['CAS#']
    sdr_we_n += U40['WE#']
    sdr_ldqm += U40['LDQM']
    sdr_udqm += U40['UDQM']

    # -----------------------------------------------------------------------------
    # Power. 3x VDD + 4x VDDQ = 7 supply pins, 3x VSS + 4x VSSQ = 7 return pins.
    # -----------------------------------------------------------------------------
    v3v3d += U40['VDD'], U40['VDDQ']
    gnd += U40['VSS'], U40['VSSQ']

    # Pin 40 is a true no-connect on this die (part summary, "Notes").
    U40['NC'] += NC

    # -----------------------------------------------------------------------------
    # Decoupling — sourced_bom.md assigns C70-C77 (100 nF 0402 X7R) and C78 (10 uF
    # 0805 X5R) to this block. Seven 100 nF caps give one per supply pin; the eighth
    # (C77) is an extra high-frequency bypass on the VDDQ/DQ side, where the x16 bus
    # switching current is concentrated. C78 is the local bulk reservoir.
    # -----------------------------------------------------------------------------
    _c100n = Part('Device', 'C', dest=TEMPLATE, value='100nF',
                  footprint='Capacitor_SMD:C_0402_1005Metric')
    c_decoup = _c100n(8)
    for idx, cap in enumerate(c_decoup):
        cap.ref = f'C{70 + idx}'
        v3v3d += cap[1]
        gnd += cap[2]

    C78 = Part('Device', 'C', ref='C78', value='10uF',
               footprint='Capacitor_SMD:C_0805_2012Metric')
    v3v3d += C78[1]
    gnd += C78[2]
