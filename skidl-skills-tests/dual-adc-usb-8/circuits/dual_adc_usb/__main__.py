"""dual_adc_usb — top-level assembly of 9 blocks.

Nets per architecture/net_plan.md § 1 (interface nets); block signatures per
handoffs/05_blocks/*.md. usb_bridge takes V5 (FT232H 5 V-in config, driver decision).
Run from the project root:
    KICAD9_SYMBOL_DIR="$KICAD_SYMBOL_DIR:$PWD/symbols" python -m circuits.dual_adc_usb
"""
import os

from skidl import *

from .usb_power_in import usb_power_in
from .power_digital import power_digital
from .power_analog import power_analog
from .afe_ch_a import afe_ch_a
from .afe_ch_b import afe_ch_b
from .adc import adc
from .clock import clock
from .fpga import fpga
from .usb_bridge import usb_bridge

# Project-local footprint library (ProjectLocal.pretty for J2/J3 BNC).
_PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
footprint_search_paths[KICAD9].append(os.path.join(_PROJ, 'footprints'))

# --- Supply nets (all driven; see handoff Decisions) ---
GND = Net('GND');       GND.drive = POWER
V5 = Net('V5');         V5.drive = POWER
V3V3D = Net('V3V3D');   V3V3D.drive = POWER
V1V2 = Net('V1V2');     V1V2.drive = POWER
V1V8 = Net('V1V8');     V1V8.drive = POWER
V3V3A = Net('V3V3A');   V3V3A.drive = POWER
VP_AFE = Net('VP_AFE'); VP_AFE.drive = POWER
VN_AFE = Net('VN_AFE'); VN_AFE.drive = POWER

# --- Analog signal nets (VCM driven by U8.CM OUTPUT — no drive override) ---
VCM = Net('VCM')
AIN_A_P = Net('AIN_A_P')
AIN_A_N = Net('AIN_A_N')
AIN_B_P = Net('AIN_B_P')
AIN_B_N = Net('AIN_B_N')

# --- Clocks ---
ADC_CLK = Net('ADC_CLK')
FPGA_CLK = Net('FPGA_CLK')

# --- ADC <-> FPGA ---
DA = Bus('DA', 12)
DB = Bus('DB', 12)
ADC_DVA = Net('ADC_DVA')
ADC_STPD = Net('ADC_STPD')

# --- FT232H <-> FPGA (sync-245 FIFO) ---
FT_D = Bus('FT_D', 8)
FT_RXF_N = Net('FT_RXF_N')
FT_TXE_N = Net('FT_TXE_N')
FT_RD_N = Net('FT_RD_N')
FT_WR_N = Net('FT_WR_N')
FT_SIWU_N = Net('FT_SIWU_N')
FT_CLKOUT = Net('FT_CLKOUT')
FT_OE_N = Net('FT_OE_N')

# --- USB ---
USB_DP = Net('USB_DP')
USB_DN = Net('USB_DN')

# --- Blocks ---
usb_power_in(v5=V5, usb_dp=USB_DP, usb_dn=USB_DN, gnd=GND, tag='usb_power_in')
power_digital(v5=V5, v3v3d=V3V3D, v1v2=V1V2, v1v8=V1V8, gnd=GND, tag='power_digital')
power_analog(v5=V5, v3v3a=V3V3A, vp_afe=VP_AFE, vn_afe=VN_AFE, gnd=GND, tag='power_analog')
afe_ch_a(ain_p=AIN_A_P, ain_n=AIN_A_N, vcm=VCM, v3v3a=V3V3A, vp_afe=VP_AFE,
         vn_afe=VN_AFE, gnd=GND, tag='afe_ch_a')
afe_ch_b(ain_p=AIN_B_P, ain_n=AIN_B_N, vcm=VCM, v3v3a=V3V3A, vp_afe=VP_AFE,
         vn_afe=VN_AFE, gnd=GND, tag='afe_ch_b')
adc(ain_a_p=AIN_A_P, ain_a_n=AIN_A_N, ain_b_p=AIN_B_P, ain_b_n=AIN_B_N, vcm=VCM,
    adc_clk=ADC_CLK, da=DA, db=DB, adc_dva=ADC_DVA, adc_stpd=ADC_STPD,
    v3v3a=V3V3A, gnd=GND, tag='adc')
clock(adc_clk=ADC_CLK, fpga_clk=FPGA_CLK, v3v3a=V3V3A, gnd=GND, tag='clock')
fpga(fpga_clk=FPGA_CLK, da=DA, db=DB, adc_dva=ADC_DVA, adc_stpd=ADC_STPD,
     ft_d=FT_D, ft_rxf_n=FT_RXF_N, ft_txe_n=FT_TXE_N, ft_rd_n=FT_RD_N,
     ft_wr_n=FT_WR_N, ft_siwu_n=FT_SIWU_N, ft_clkout=FT_CLKOUT, ft_oe_n=FT_OE_N,
     v3v3d=V3V3D, v1v2=V1V2, v1v8=V1V8, gnd=GND, tag='fpga')
usb_bridge(usb_dp=USB_DP, usb_dn=USB_DN, ft_d=FT_D, ft_rxf_n=FT_RXF_N,
           ft_txe_n=FT_TXE_N, ft_rd_n=FT_RD_N, ft_wr_n=FT_WR_N, ft_siwu_n=FT_SIWU_N,
           ft_clkout=FT_CLKOUT, ft_oe_n=FT_OE_N, v5=V5, gnd=GND, tag='usb_bridge')


def _stabilize_tags():
    """Derive every untagged part's tag from its refdes (rules/skidl-syntax.md § Stable netlists)."""
    for part in default_circuit.parts:
        if not getattr(part, 'tag', None):
            part.tag = part.ref
    # SKiDL 2.3 keeps hierarchy nodes in a set, so the netlist's (sheet ...) list
    # comes out in hash order and differs run to run. Emit it sorted by path.
    circ = default_circuit
    circ.get_node_names = lambda: sorted(node.hiertuple for node in circ.nodes)


if __name__ == '__main__':
    _stabilize_tags()
    ERC()
    generate_netlist(file_=os.path.join(_PROJ, 'outputs', 'dual_adc_usb.net'))
    generate_xml(file_=os.path.join(_PROJ, 'outputs', 'dual_adc_usb_bom.xml'))
