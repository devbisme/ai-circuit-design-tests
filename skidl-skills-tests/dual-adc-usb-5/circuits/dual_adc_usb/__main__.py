"""dual_adc_usb — top-level assembly.

Wires the eight blocks of `architecture/block_diagram.md` together using the net names
of `architecture/net_plan.md` (exact, case-sensitive) and the FINAL block signatures
declared in `handoffs/05_blocks/*.md`.

Run from the project root, as a module (the block imports are relative):

    KICAD9_SYMBOL_DIR="$KICAD_SYMBOL_DIR:$PWD/symbols" python -m circuits.dual_adc_usb

Integration only: nothing in this file changes a block's internals.
"""

from skidl import *

from .usb_c_input import usb_c_input
from .digital_power import digital_power
from .analog_power_ref import analog_power_ref
from .afe_channel import afe_channel
from .adc_dual import adc_dual
from .clock_20m import clock_20m
from .fpga_core import fpga_core
from .usb_bridge import usb_bridge

# =====================================================================================
# Nets — every inter-block net of architecture/net_plan.md § Inter-block net summary.
# `VBUS_RAW` is NOT here: usb_c_input owns it internally (handoffs/05_blocks/
# usb_c_input.md decision 2). All block-local nets likewise stay inside their block.
# =====================================================================================

# --- Power rails (net_plan.md § Power nets) -------------------------------------------
V5V_IN = Net('+5V_IN')               # FB1.2 -> U9.IN, U7.VREGIN
V5V_SW = Net('+5V_SW')               # U9.OUT -> U1/FB3 (gated by PWREN_N)
V3V3_D = Net('+3V3_D')               # buck output, FPGA I/O + core logic rail
V3V3_ADCD = Net('+3V3_ADCD')         # ferrite-isolated ADC output-driver rail
V3V3_A = Net('+3V3_A')               # analog LDO output
V1V2_D = Net('+1V2_D')               # FPGA core rail
GND = Net('GND')                     # the ONE ground net (net_plan § Ground policy)

# One ground, and the two rails fed from passive/connector pins need the POWER flag.
# See "## Decisions" in handoffs/05_coding.md for why each flag is (or is not) set.
GND.drive = POWER
V5V_IN.drive = POWER                 # comes off J1 via FB1 — passive pins only
V3V3_D.drive = POWER                 # through L1 (buck inductor) — passive
V3V3_ADCD.drive = POWER              # through FB2 — passive
V1V2_D.drive = POWER                 # TLV75801 OUT, typed passive in the symbol
V3V3_A.drive = POWER                 # TLV75733 OUT, typed passive in the symbol
V5V_SW.drive = POWER                 # U9.OUT is power_out; flag is harmless/defensive

# --- Analog references (net_plan.md § Analog reference nets) --------------------------
VBIAS = Net('VBIAS')                 # 1.200 V divider return; U4A through R22 (10 R)
VREF_FE = Net('VREF_FE')             # 1.140 V = 0.95 * VBIAS, U4B output
VOCM = Net('VOCM')                   # driven by U5.CM only — no .drive here (adc_dual #3)
VBIAS.drive = POWER                  # driven THROUGH R22, a passive part (see handoff)
VREF_FE.drive = POWER                # U4B op-amp output; flag if ERC wants a driver

# --- Analog signal nets ---------------------------------------------------------------
AIN1 = Net('AIN1')                   # J2 centre, +/-10 V
AIN2 = Net('AIN2')                   # J3 centre, +/-10 V
CH1_P = Net('CH1_P')
CH1_N = Net('CH1_N')
CH2_P = Net('CH2_P')
CH2_N = Net('CH2_N')

# --- Clocks ---------------------------------------------------------------------------
ADC_CLK = Net('ADC_CLK')             # X1 -> R_s1 -> U5.CLK  (no driving pin BY DESIGN)
FPGA_CLK = Net('FPGA_CLK')           # X1 -> R_s2 -> U6 GCLK  (ditto)
FIFO_CLK = Net('FIFO_CLK')           # U7.ACBUS5 (60 MHz) -> U6 GCLK

# --- ADC <-> FPGA buses and control ---------------------------------------------------
ADC_D1 = Bus('ADC_D1', 12)           # channel A, U5 -> RA1..RA3 -> U6
ADC_D2 = Bus('ADC_D2', 12)           # channel B, U5 -> RA4..RA6 -> U6
ADC_OE_N = Net('ADC_OE_N')
ADC_PDWN = Net('ADC_PDWN')

# --- FPGA <-> FT232H synchronous FIFO -------------------------------------------------
FIFO_D = Bus('FIFO_D', 8)            # ADBUS0..7, bidirectional
FIFO_RXF_N = Net('FIFO_RXF_N')
FIFO_TXE_N = Net('FIFO_TXE_N')
FIFO_RD_N = Net('FIFO_RD_N')
FIFO_WR_N = Net('FIFO_WR_N')
FIFO_OE_N = Net('FIFO_OE_N')
FIFO_SIWU = Net('FIFO_SIWU')

# --- USB and power-enable -------------------------------------------------------------
USB_DP = Net('USB_DP')
USB_DM = Net('USB_DM')
PWREN_N = Net('PWREN_N')             # U7.ACBUS8 -> U9.EN# (active low, GND-referenced)

# =====================================================================================
# Blocks — one call each, keywords exactly as the block handoffs declare, every call
# tagged for stable netlist UUIDs.
# =====================================================================================

# Power in: USB-C receptacle, ESD, VBUS bulk, CC pulldowns.
usb_c_input(v5_in=V5V_IN, usb_dp=USB_DP, usb_dm=USB_DM, gnd=GND,
            tag='usb_c_input')

# Digital rail tree behind the AP2161WG-7 load switch (U9, EN# = PWREN_N).
digital_power(v5_in=V5V_IN, v5_sw=V5V_SW, pwren_n=PWREN_N, v3v3_d=V3V3_D,
              v3v3_adcd=V3V3_ADCD, v1v2_d=V1V2_D, gnd=GND,
              tag='digital_power')

# Analog LDO + VBIAS/VREF_FE references (VBIAS driven through R22).
analog_power_ref(v5_sw=V5V_SW, v3v3_a=V3V3_A, vbias=VBIAS, vref_fe=VREF_FE, gnd=GND,
                 tag='analog_power_ref')

# Two identical front ends; `ch` selects the ref set (J2/R1xx/C1xx vs J3/R2xx/C2xx).
afe_channel(ain=AIN1, adc_in_p=CH1_P, adc_in_n=CH1_N, vbias=VBIAS, vref_fe=VREF_FE,
            vocm=VOCM, v3v3_a=V3V3_A, gnd=GND, ch=1,
            tag='afe_channel_ch1')
afe_channel(ain=AIN2, adc_in_p=CH2_P, adc_in_n=CH2_N, vbias=VBIAS, vref_fe=VREF_FE,
            vocm=VOCM, v3v3_a=V3V3_A, gnd=GND, ch=2,
            tag='afe_channel_ch2')

# Dual 12-bit 20 MSPS ADC; also the only source of VOCM.
adc_dual(in1_p=CH1_P, in1_n=CH1_N, in2_p=CH2_P, in2_n=CH2_N,
         adc_clk=ADC_CLK, adc_d1=ADC_D1, adc_d2=ADC_D2,
         adc_oe_n=ADC_OE_N, adc_pdwn=ADC_PDWN, vocm=VOCM,
         v3v3_a=V3V3_A, v3v3_adcd=V3V3_ADCD, gnd=GND,
         tag='adc_dual')

# 20 MHz XO, one output, two series-terminated branches.
clock_20m(adc_clk=ADC_CLK, fpga_clk=FPGA_CLK, v3v3_a=V3V3_A, gnd=GND,
          tag='clock_20m')

# FPGA capture core, JTAG header, trigger input, capture LED.
fpga_core(adc_d1=ADC_D1, adc_d2=ADC_D2, adc_oe_n=ADC_OE_N, adc_pdwn=ADC_PDWN,
          fpga_clk=FPGA_CLK, fifo_d=FIFO_D, fifo_rxf_n=FIFO_RXF_N,
          fifo_txe_n=FIFO_TXE_N, fifo_rd_n=FIFO_RD_N, fifo_wr_n=FIFO_WR_N,
          fifo_oe_n=FIFO_OE_N, fifo_siwu=FIFO_SIWU, fifo_clk=FIFO_CLK,
          v3v3_d=V3V3_D, v1v2_d=V1V2_D, gnd=GND,
          tag='fpga_core')

# FT232H in 245 sync FIFO mode + config EEPROM + 12 MHz crystal.
usb_bridge(usb_dp=USB_DP, usb_dm=USB_DM, fifo_d=FIFO_D, fifo_rxf_n=FIFO_RXF_N,
           fifo_txe_n=FIFO_TXE_N, fifo_rd_n=FIFO_RD_N, fifo_wr_n=FIFO_WR_N,
           fifo_oe_n=FIFO_OE_N, fifo_siwu=FIFO_SIWU, fifo_clk=FIFO_CLK,
           pwren_n=PWREN_N, v5_in=V5V_IN, gnd=GND,
           tag='usb_bridge')


def _stabilize_tags():
    """Derive every untagged part's tag from its refdes (rules/skidl-syntax.md).

    Every block call above carries its own tag, so the only object SKiDL still reports as
    untagged is the ROOT hierarchy node (name ''). Leave it alone: kicad10's
    gen_sheetpath() asserts the top level of the hierarchy is an empty string, so giving
    the root a tag makes generate_netlist() raise. The warning is cosmetic — check_tag()
    is called with create_if_missing=False for nodes, so no random tag is invented and
    two runs of unchanged code emit byte-identical netlists apart from the (date ...) line.
    """
    for part in default_circuit.parts:
        if not getattr(part, 'tag', None):
            part.tag = part.ref


if __name__ == '__main__':
    _stabilize_tags()
    ERC()
    generate_netlist(file_='outputs/dual_adc_usb.net')
    generate_xml(file_='outputs/dual_adc_usb_bom.xml')
