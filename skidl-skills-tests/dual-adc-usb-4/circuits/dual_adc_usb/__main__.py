"""dual_adc_usb — top-level assembly.

Creates every inter-block net from architecture/net_plan.md, calls the nine blocks by the
signatures declared in handoffs/05_blocks/*.md, runs ERC, and writes the netlist and BOM XML.

Run from the project root, as a module:
    KICAD9_SYMBOL_DIR="$KICAD_SYMBOL_DIR:$PWD/symbols" python3 -m circuits.dual_adc_usb
"""
import os
from pathlib import Path

from skidl import *

from .usb_power_in import usb_power_in
from .power_rails import power_rails
from .bipolar_supply import bipolar_supply
from .analog_front_end import analog_front_end
from .adc import adc
from .sample_clock import sample_clock
from .usb_bridge import usb_bridge
from .fpga_core import fpga_core
from .io_expansion import io_expansion

# --- Search paths ---------------------------------------------------------------------
# SKiDL 3.0.0 appends KICAD<n>_SYMBOL_DIR as a single path (no colon split), so the
# project symbol library (dual_adc_usb) and footprint library (ProjectLocal) are appended
# explicitly. The .pretty directory itself is added: SKiDL treats a directory with no
# fp-lib-table as one footprint library whose nickname is its basename (ProjectLocal).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
_tool = get_default_tool()
for _p in (str(PROJECT_ROOT / 'symbols'),):
    if _p not in lib_search_paths[_tool]:
        lib_search_paths[_tool].append(_p)
for _p in (str(PROJECT_ROOT / 'footprints' / 'ProjectLocal.pretty'),):
    if _p not in footprint_search_paths[_tool]:
        footprint_search_paths[_tool].append(_p)

# --- Power nets (net_plan §1) ---------------------------------------------------------
# Every supply net gets drive=POWER here. The rail-producing blocks also set it on the
# rails they generate (usb_power_in: VBUS_SW; power_rails: VD_3V3/VD_1V8/VD_1V2/VA_3V3;
# bipolar_supply: VA_P2V5/VA_N2V5); GND is driven only here.
GND = Net('GND')
VBUS_SW = Net('VBUS_SW')
VD_3V3 = Net('VD_3V3')
VD_1V8 = Net('VD_1V8')
VD_1V2 = Net('VD_1V2')
VA_3V3 = Net('VA_3V3')
VA_P2V5 = Net('VA_P2V5')
VA_N2V5 = Net('VA_N2V5')
for _rail in (GND, VBUS_SW, VD_3V3, VD_1V8, VD_1V2, VA_3V3, VA_P2V5, VA_N2V5):
    _rail.drive = POWER

# --- USB (net_plan §2) ----------------------------------------------------------------
USB_DP = Net('USB_DP')
USB_DM = Net('USB_DM')

# --- Analog front end -> ADC (net_plan §4) --------------------------------------------
AIN_A_P = Net('AIN_A_P')
AIN_A_N = Net('AIN_A_N')
AIN_B_P = Net('AIN_B_P')
AIN_B_N = Net('AIN_B_N')
ADC_VCM = Net('ADC_VCM')

# --- ADC <-> FPGA (net_plan §5) -------------------------------------------------------
ADC_DA = Bus('ADC_DA', 12)          # ADC_DA0..ADC_DA11, index 0 = LSB
ADC_DB = Bus('ADC_DB', 12)          # ADC_DB0..ADC_DB11
ADC_OVRA = Net('ADC_OVRA')
ADC_OVRB = Net('ADC_OVRB')
ADC_DVA = Net('ADC_DVA')
ADC_SEL = Net('ADC_SEL')
ADC_SEN = Net('ADC_SEN')
ADC_SCLK = Net('ADC_SCLK')
ADC_SDATA = Net('ADC_SDATA')

# --- Sample clock (net_plan §6) -------------------------------------------------------
ADC_CLK = Net('ADC_CLK')
ADC_CLK_FPGA = Net('ADC_CLK_FPGA')

# --- FT232H <-> FPGA (net_plan §7) ----------------------------------------------------
FT_D = Bus('FT_D', 8)               # FT_D0..FT_D7, index 0 = LSB
FT_RXF_N = Net('FT_RXF_N')
FT_TXE_N = Net('FT_TXE_N')
FT_RD_N = Net('FT_RD_N')
FT_WR_N = Net('FT_WR_N')
FT_OE_N = Net('FT_OE_N')
FT_SIWU_N = Net('FT_SIWU_N')
FT_CLKOUT = Net('FT_CLKOUT')

# --- FPGA bank 3 <-> I/O expansion (net_plan §9) --------------------------------------
LED_STAT_1V8 = Net('LED_STAT_1V8')
LED_ACT_1V8 = Net('LED_ACT_1V8')
TRIG_OUT_1V8 = Net('TRIG_OUT_1V8')
GPIO_OUT_1V8 = Net('GPIO_OUT_1V8')
TRIG_IN_1V8 = Net('TRIG_IN_1V8')

# --- Blocks (handoffs/02_architecture.md § Block manifest; signatures per 05_blocks) ---
usb_power_in(vbus_sw=VBUS_SW, usb_dp=USB_DP, usb_dm=USB_DM, gnd=GND, tag='usb_power_in')

power_rails(vbus_sw=VBUS_SW, vd_3v3=VD_3V3, vd_1v8=VD_1V8, vd_1v2=VD_1V2,
            va_3v3=VA_3V3, gnd=GND, tag='power_rails')

bipolar_supply(vbus_sw=VBUS_SW, va_p2v5=VA_P2V5, va_n2v5=VA_N2V5, gnd=GND,
               tag='bipolar_supply')

analog_front_end(ain_a_p=AIN_A_P, ain_a_n=AIN_A_N, ain_b_p=AIN_B_P, ain_b_n=AIN_B_N,
                 adc_vcm=ADC_VCM, va_3v3=VA_3V3, va_p2v5=VA_P2V5, va_n2v5=VA_N2V5,
                 gnd=GND, tag='analog_front_end')

adc(ain_a_p=AIN_A_P, ain_a_n=AIN_A_N, ain_b_p=AIN_B_P, ain_b_n=AIN_B_N,
    adc_vcm=ADC_VCM, adc_clk=ADC_CLK, adc_da=ADC_DA, adc_db=ADC_DB,
    adc_ovra=ADC_OVRA, adc_ovrb=ADC_OVRB, adc_dva=ADC_DVA, adc_sel=ADC_SEL,
    adc_sen=ADC_SEN, adc_sclk=ADC_SCLK, adc_sdata=ADC_SDATA, va_3v3=VA_3V3, gnd=GND,
    tag='adc')

sample_clock(adc_clk=ADC_CLK, adc_clk_fpga=ADC_CLK_FPGA, va_3v3=VA_3V3, gnd=GND,
             tag='sample_clock')

usb_bridge(usb_dp=USB_DP, usb_dm=USB_DM, ft_d=FT_D, ft_rxf_n=FT_RXF_N,
           ft_txe_n=FT_TXE_N, ft_rd_n=FT_RD_N, ft_wr_n=FT_WR_N, ft_oe_n=FT_OE_N,
           ft_siwu_n=FT_SIWU_N, ft_clkout=FT_CLKOUT, vd_3v3=VD_3V3, gnd=GND,
           tag='usb_bridge')

fpga_core(adc_da=ADC_DA, adc_db=ADC_DB, adc_ovra=ADC_OVRA, adc_ovrb=ADC_OVRB,
          adc_dva=ADC_DVA, adc_sel=ADC_SEL, adc_sen=ADC_SEN, adc_sclk=ADC_SCLK,
          adc_sdata=ADC_SDATA, adc_clk_fpga=ADC_CLK_FPGA, ft_d=FT_D,
          ft_rxf_n=FT_RXF_N, ft_txe_n=FT_TXE_N, ft_rd_n=FT_RD_N, ft_wr_n=FT_WR_N,
          ft_oe_n=FT_OE_N, ft_siwu_n=FT_SIWU_N, ft_clkout=FT_CLKOUT,
          led_stat_1v8=LED_STAT_1V8, led_act_1v8=LED_ACT_1V8,
          trig_out_1v8=TRIG_OUT_1V8, gpio_out_1v8=GPIO_OUT_1V8,
          trig_in_1v8=TRIG_IN_1V8, vd_3v3=VD_3V3, vd_1v8=VD_1V8, vd_1v2=VD_1V2,
          gnd=GND, tag='fpga_core')

io_expansion(led_stat_1v8=LED_STAT_1V8, led_act_1v8=LED_ACT_1V8,
             trig_out_1v8=TRIG_OUT_1V8, gpio_out_1v8=GPIO_OUT_1V8,
             trig_in_1v8=TRIG_IN_1V8, vd_3v3=VD_3V3, vd_1v8=VD_1V8, gnd=GND,
             tag='io_expansion')


def _export_sourcing_fields():
    """Copy MPN/LCSC part attributes into part.fields so they reach the netlist.

    SKiDL 3.0.0 stores an unknown Part() keyword (MPN=, LCSC=) as a plain attribute,
    not a netlist field. Fields a block already set explicitly are left untouched.
    """
    for part in default_circuit.parts:
        for key in ('MPN', 'LCSC'):
            val = getattr(part, key, None)
            if val and not part.fields.get(key):
                part.fields[key] = val


def _stabilize_tags():
    """Derive every untagged part's tag from its refdes (rules/skidl-syntax.md § Stable netlists)."""
    for part in default_circuit.parts:
        if not getattr(part, 'tag', None):
            part.tag = part.ref


if __name__ == '__main__':
    _export_sourcing_fields()
    _stabilize_tags()
    ERC()
    os.makedirs(PROJECT_ROOT / 'outputs', exist_ok=True)
    generate_netlist(file_=str(PROJECT_ROOT / 'outputs' / 'dual_adc_usb.net'))
    generate_xml(file_=str(PROJECT_ROOT / 'outputs' / 'dual_adc_usb_bom.xml'))
