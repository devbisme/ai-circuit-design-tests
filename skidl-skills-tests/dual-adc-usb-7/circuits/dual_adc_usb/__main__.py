"""dual_adc_usb — top-level assembly.

Creates every inter-block net from architecture/net_plan.md and calls each of the
eight blocks with the FINAL signature declared in its own handoffs/05_blocks/*.md.
Integration only: no parts are instantiated here.

Run from the project root, as a module (see rules/environment.md):
    KICAD9_SYMBOL_DIR="$KICAD_SYMBOL_DIR:$PWD/symbols" .venv/bin/python -m circuits.dual_adc_usb
"""
from skidl import *

from .afe_input import afe_input
from .afe_buffer import afe_buffer
from .afe_driver import afe_driver
from .adc_dual import adc_dual
from .clock_gen import clock_gen
from .fpga_core import fpga_core
from .usb_bridge import usb_bridge
from .power_tree import power_tree

# ---------------------------------------------------------------- power nets
# net_plan.md § Power nets
VBUS    = Net('VBUS')       # J4 -> U8/U6/U9; usb_bridge sources it from the connector
VBUS_SW = Net('VBUS_SW')    # U9 VOUT, loaded only inside power_tree
FT_3V3  = Net('FT_3V3')     # U6 pin 39 (FT232H internal LDO) — SINGLE source, shared
P3V3D   = Net('P3V3D')      # U10 buck via L71
P1V8    = Net('P1V8')       # U15 VOUT (slew-limited VCCIO3 rail), NOT U14's output
P1V2    = Net('P1V2')       # U11 buck via L72
P3V3A   = Net('P3V3A')      # U12 LDO VOUT
VA_POS  = Net('VA_POS')     # +5 V via FB1
VA_NEG  = Net('VA_NEG')     # -4.74 V via R76
GND     = Net('GND')        # one ground net board-wide (net_plan.md)

# Rails whose only source in power_tree is a passive (L/FB/R) pin, plus the two rails
# whose source pin is declared power_in in its symbol (FT_3V3 = U6.39, VBUS = J4).
# power_tree's handoff states P1V8 / P3V3A / VBUS_SW have real power_out pins and do
# not need this; they are deliberately left alone.
for _rail in (P3V3D, P1V2, VA_POS, VA_NEG, GND, VBUS, FT_3V3):
    _rail.drive = POWER

# ------------------------------------------------------- analog signal nets
# net_plan.md § Analog signal nets
CHA_ATT  = Net('CHA_ATT')   # divider tap, channel A (hi-Z, 82.6 k source)
CHB_ATT  = Net('CHB_ATT')
CHA_BUF  = Net('CHA_BUF')   # AD8066 follower output, channel A
CHB_BUF  = Net('CHB_BUF')
ADC_INAP = Net('ADC_INAP')  # fed from the FDA OUT- leg (polarity crossing: do not "fix")
ADC_INAN = Net('ADC_INAN')  # fed from the FDA OUT+ leg
ADC_INBP = Net('ADC_INBP')
ADC_INBN = Net('ADC_INBN')
ADC_CM   = Net('ADC_CM')    # U4 CM out -> U2/U3 VOCM. No resistive load permitted.

# --------------------------------------------------------------- clock nets
CLK10_ADC  = Net('CLK10_ADC')   # X1 -> R31 -> U4 CLK
CLK10_FPGA = Net('CLK10_FPGA')  # X1 -> R32 -> U5 clock input

# ------------------------------------------------------------ ADC <-> FPGA
ADC_DA    = Bus('ADC_DA', 12)   # U4 D0A..D11A -> U5
ADC_DB    = Bus('ADC_DB', 12)   # U4 D0B..D11B -> U5
ADC_DVA   = Net('ADC_DVA')
ADC_SEN   = Net('ADC_SEN')
ADC_SCLK  = Net('ADC_SCLK')
ADC_SDATA = Net('ADC_SDATA')
ADC_SEL   = Net('ADC_SEL')      # FPGA-driven, not a strap (SBAS295A p.19)
# ADC_OVRA / ADC_OVRB retired at architecture rev.3 — U4 pins 39/9 are NC inside adc_dual.

# -------------------------------------------------------- FPGA <-> FT232HL
FIFO_D      = Bus('FIFO_D', 8)  # U6 ADBUS0-7 <-> U5, bidirectional
FIFO_RXF_N  = Net('FIFO_RXF_N')
FIFO_TXE_N  = Net('FIFO_TXE_N')
FIFO_RD_N   = Net('FIFO_RD_N')
FIFO_WR_N   = Net('FIFO_WR_N')
FIFO_OE_N   = Net('FIFO_OE_N')
FIFO_CLK60  = Net('FIFO_CLK60')
PWREN_N     = Net('PWREN_N')    # U6 ACBUS9 -> Q1 gate in power_tree
# FIFO_SIWU_N is block-internal to usb_bridge (R67 strap) — no top-level net.

# =============================================================== block calls
# afe_input x2 — parameter is `ch`, NOT `tag` (SubCircuit pops tag= from kwargs)
afe_input(v_att=CHA_ATT, va_pos=VA_POS, va_neg=VA_NEG, gnd=GND, ch='A', tag='afe_input_a')
afe_input(v_att=CHB_ATT, va_pos=VA_POS, va_neg=VA_NEG, gnd=GND, ch='B', tag='afe_input_b')

# afe_buffer x1 — one AD8066 carries both channels
afe_buffer(cha_att=CHA_ATT, chb_att=CHB_ATT, cha_buf=CHA_BUF, chb_buf=CHB_BUF,
           va_pos=VA_POS, va_neg=VA_NEG, gnd=GND, tag='afe_buffer')

# afe_driver x2 — `ch` selects refdes base 100/200
afe_driver(v_buf=CHA_BUF, adc_inp=ADC_INAP, adc_inn=ADC_INAN, adc_cm=ADC_CM,
           p3v3a=P3V3A, gnd=GND, ch='A', tag='afe_driver_a')
afe_driver(v_buf=CHB_BUF, adc_inp=ADC_INBP, adc_inn=ADC_INBN, adc_cm=ADC_CM,
           p3v3a=P3V3A, gnd=GND, ch='B', tag='afe_driver_b')

# adc_dual x1 — no ovra/ovrb (retired at rev.3)
adc_dual(inap=ADC_INAP, inan=ADC_INAN, inbp=ADC_INBP, inbn=ADC_INBN,
         cm=ADC_CM, clk_adc=CLK10_ADC, da=ADC_DA, db=ADC_DB, dva=ADC_DVA,
         sen=ADC_SEN, sclk=ADC_SCLK, sdata=ADC_SDATA, sel=ADC_SEL,
         p3v3a=P3V3A, p3v3d=P3V3D, gnd=GND, tag='adc_dual')

# clock_gen x1
clock_gen(clk_adc=CLK10_ADC, clk_fpga=CLK10_FPGA, p3v3d=P3V3D, gnd=GND, tag='clock_gen')

# fpga_core x1 — no ovra/ovrb/siwu_n; gained p1v8 (U5 pin 12 = VCCIO3)
fpga_core(clk_fpga=CLK10_FPGA, da=ADC_DA, db=ADC_DB, dva=ADC_DVA, sen=ADC_SEN,
          sclk=ADC_SCLK, sdata=ADC_SDATA, sel=ADC_SEL, fifo_d=FIFO_D,
          rxf_n=FIFO_RXF_N, txe_n=FIFO_TXE_N, rd_n=FIFO_RD_N, wr_n=FIFO_WR_N,
          oe_n=FIFO_OE_N, fifo_clk60=FIFO_CLK60, p1v2=P1V2, p1v8=P1V8,
          p3v3d=P3V3D, gnd=GND, tag='fpga_core')

# usb_bridge x1 — no siwu_n (R67 straps it internally); sole source of FT_3V3
usb_bridge(vbus=VBUS, ft_3v3=FT_3V3, fifo_d=FIFO_D, rxf_n=FIFO_RXF_N,
           txe_n=FIFO_TXE_N, rd_n=FIFO_RD_N, wr_n=FIFO_WR_N, oe_n=FIFO_OE_N,
           fifo_clk60=FIFO_CLK60, pwren_n=PWREN_N, gnd=GND, tag='usb_bridge')

# power_tree x1 — gained ft_3v3 (R71 returns U9's EN pull-up to FT_3V3, SPEC P3)
power_tree(vbus=VBUS, vbus_sw=VBUS_SW, p3v3d=P3V3D, p1v8=P1V8, p1v2=P1V2,
           p3v3a=P3V3A, va_pos=VA_POS, va_neg=VA_NEG, pwren_n=PWREN_N,
           ft_3v3=FT_3V3, gnd=GND, tag='power_tree')


def _stabilize_tags():
    """Derive every untagged part's tag from its refdes (rules/skidl-syntax.md)."""
    for part in default_circuit.parts:
        if not getattr(part, 'tag', None):
            part.tag = part.ref


if __name__ == '__main__':
    _stabilize_tags()
    ERC()
#    generate_netlist(file_='outputs/dual_adc_usb.net')
#    generate_xml(file_='outputs/dual_adc_usb_bom.xml')
    generate_schematic()
