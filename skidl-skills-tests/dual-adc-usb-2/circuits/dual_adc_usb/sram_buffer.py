"""SRAM Buffer -- 512 kB (256K x 16) async CMOS capture SRAM, IS61WV25616BLL-10TLI
Block from: architecture/block_diagram.md
Interface nets: V3V3_D, GND, SRAM_A[17:0], SRAM_D[15:0], SRAM_CE_N, SRAM_OE_N,
                SRAM_WE_N, SRAM_UB_N, SRAM_LB_N
"""
from skidl import *


@subcircuit
def sram_buffer(v3v3_d, gnd, addr, data, ce_n, oe_n, we_n, ub_n, lb_n):
    """256K x 16 (512 kB) async SRAM capture buffer -- IS61WV25616BLL-10TLI.

    Sets the design's published 131,072 samples/channel burst depth (256K words
    x 16 bits, split evenly between the two ADC channels by the FPGA capture
    state machine). Binding spec is the 10 ns access time (net_plan.md / R-14),
    not capacity -- do not substitute a slower part.

    No project-local KiCad symbol existed for this part; one was generated via
    kipart from the pin table in datasheets/IS61WV25616BLL-10TLI_SUMMARY.md and
    verified to load all 44 pins from lib/dual_adc_usb.kicad_sym (see this
    file's own compile/pin-count check).

    Fully static/asynchronous device -- no CLK pin. The FPGA (U9, fpga_core
    block) drives the address/data bus and all four control lines directly as
    a memory-mapped peripheral, timed to the part's 10 ns access window.
    SRAM_UB_N/SRAM_LB_N are actively driven by the FPGA (not tied low locally)
    per net_plan.md section 6 -- the FPGA capture logic uses independent byte-
    lane control rather than treating the part as a fixed 16-bit-wide memory.

    Args:
        v3v3_d: 3.3 V digital supply (V3V3_D) -- both VDD pins (11, 33).
        gnd: Ground reference -- both GND pins (12, 34).
        addr: 18-bit SKiDL Bus, SRAM_A[17:0], addr[0..17] -> A0..A17.
            Driven by the FPGA (U9); this block only receives it.
        data: 16-bit SKiDL Bus, SRAM_D[15:0], data[0..15] -> I/O0..I/O15.
            Bidirectional -- driven by the FPGA during writes, by the SRAM
            during reads (OE#/WE#/CE# arbitrate direction).
        ce_n: Chip Enable, active LOW (SRAM_CE_N). Driven by the FPGA.
        oe_n: Output Enable, active LOW (SRAM_OE_N). Driven by the FPGA.
        we_n: Write Enable, active LOW (SRAM_WE_N). Driven by the FPGA.
        ub_n: Upper-byte control, active LOW (SRAM_UB_N), gates I/O8-I/O15.
            Driven by the FPGA.
        lb_n: Lower-byte control, active LOW (SRAM_LB_N), gates I/O0-I/O7.
            Driven by the FPGA.
    """
    # --- U8: IS61WV25616BLL-10TLI, 256K x 16 async SRAM (project-local [GEN] symbol) ---
    u8 = Part(
        'lib/dual_adc_usb.kicad_sym',
        'IS61WV25616BLL-10TLI',
        ref='U8',
        value='IS61WV25616BLL-10TLI',
        footprint='Package_SO:TSOP-II-44_10.16x18.41mm_P0.8mm',
        tool=KICAD9,
    )

    # --- Power: 2x VDD (pins 11, 33), 2x GND (pins 12, 34) -- both pairs share ---
    # --- the single power/ground plane, so tie both to the same nets each. ---
    u8['VDD'] += v3v3_d
    u8['GND'] += gnd

    # --- Address bus: 18 lines, A0-A17 -> addr[0]-addr[17] (256K word depth) ---
    for i in range(18):
        u8[f'A{i}'] += addr[i]

    # --- Data bus: 16 lines, I/O0-I/O15 -> data[0]-data[15] (bidirectional) ---
    for i in range(16):
        u8[f'I/O{i}'] += data[i]

    # --- Control lines: all four driven externally by the FPGA (fpga_core, U9) ---
    u8['CE#'] += ce_n
    u8['OE#'] += oe_n
    u8['WE#'] += we_n
    u8['UB#'] += ub_n
    u8['LB#'] += lb_n

    # --- Intentional no-connect: pin 28 has no function on this device ---
    u8['NC'] += NC

    # --- Decoupling: 4x 100 nF (C41-C44), 2 per VDD/GND pin-pair region, plus ---
    # --- 10 uF (C45) + 1 uF (C46) bulk, per datasheets/IS61WV25616BLL-10TLI_SUMMARY.md ---
    # --- and net_plan.md section "Decoupling budget" (SRAM (U8): 1x10uF + 2x100nF, ---
    # --- rounded up here to the sourced BOM's actual C41-C46 allocation of 6 caps). ---

    # C41, C42: local 100 nF bypass at the VDD(11)/GND(12) pin-pair region
    c41 = Part('Device', 'C', ref='C41', value='100nF',
               footprint='Capacitor_SMD:C_0402_1005Metric')
    c41[1] += v3v3_d
    c41[2] += gnd

    c42 = Part('Device', 'C', ref='C42', value='100nF',
               footprint='Capacitor_SMD:C_0402_1005Metric')
    c42[1] += v3v3_d
    c42[2] += gnd

    # C43, C44: local 100 nF bypass at the VDD(33)/GND(34) pin-pair region
    c43 = Part('Device', 'C', ref='C43', value='100nF',
               footprint='Capacitor_SMD:C_0402_1005Metric')
    c43[1] += v3v3_d
    c43[2] += gnd

    c44 = Part('Device', 'C', ref='C44', value='100nF',
               footprint='Capacitor_SMD:C_0402_1005Metric')
    c44[1] += v3v3_d
    c44[2] += gnd

    # C45: 10 uF bulk decoupling for the whole part
    c45 = Part('Device', 'C', ref='C45', value='10uF',
               footprint='Capacitor_SMD:C_0805_2012Metric')
    c45[1] += v3v3_d
    c45[2] += gnd

    # C46: 1 uF bulk decoupling for the whole part
    c46 = Part('Device', 'C', ref='C46', value='1uF',
               footprint='Capacitor_SMD:C_0603_1608Metric')
    c46[1] += v3v3_d
    c46[2] += gnd
