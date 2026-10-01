"""dual_adc_usb — top-level assembly.

Creates every interface net from architecture/net_plan.md section 1 and calls each block
with the signature declared in its handoffs/05_blocks/<block>.md.
Run from the project root (as a module):  python -m circuits.dual_adc_usb
"""
import os

from skidl import *

from .usb_power_in import usb_power_in
from .pwr_digital import pwr_digital
from .pwr_analog import pwr_analog
from .afe_ch_a import afe_ch_a
from .afe_ch_b import afe_ch_b
from .adc_dual import adc_dual
from .clock_gen import clock_gen
from .fpga import fpga
from .usb_bridge import usb_bridge

_PROJECT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Project-local symbol library (U2, U7, U9). KICAD9_SYMBOL_DIR alone is not reliable here.
_SYM = os.path.join(_PROJECT, 'symbols')
if _SYM not in lib_search_paths[KICAD]:
    lib_search_paths[KICAD].append(_SYM)
# Project-local footprints (J2/J3 ProjectLocal:KH-BNC50-3511).
try:
    _FP = os.path.join(_PROJECT, 'footprints')
    if _FP not in footprint_search_paths[KICAD]:
        footprint_search_paths[KICAD].append(_FP)
except NameError:
    pass

# ---- Power nets -------------------------------------------------------------
GND = Net('GND'); GND.drive = POWER        # no part pin drives ground
VBUS_SW = Net('VBUS_SW')                    # driven by usb_power_in U2.VOUT (PWROUT)
V3V3D = Net('+3V3D')                        # .drive = POWER set inside pwr_digital
V1V2 = Net('+1V2')                          # .drive = POWER set inside pwr_digital
V1V8 = Net('+1V8')                          # .drive = POWER set inside pwr_digital
V3V3A = Net('+3V3A')                        # driven by pwr_analog U5.OUT (PWROUT)
VAFE_P = Net('VAFE_P')                      # driven by pwr_analog U6.OUT+ (PWROUT)
VAFE_N = Net('VAFE_N')                      # driven by pwr_analog U6.OUT- (PWROUT)

# ---- USB --------------------------------------------------------------------
USB_DP = Net('USB_DP')
USB_DM = Net('USB_DM')

# ---- Analog -----------------------------------------------------------------
ADC_AINA_P = Net('ADC_AINA_P')
ADC_AINA_N = Net('ADC_AINA_N')
ADC_AINB_P = Net('ADC_AINB_P')
ADC_AINB_N = Net('ADC_AINB_N')
ADC_VCM = Net('ADC_VCM')

# ---- Clocks -----------------------------------------------------------------
ADC_CLK = Net('ADC_CLK')
FPGA_CLK40 = Net('FPGA_CLK40')

# ---- ADC data / control -----------------------------------------------------
ADC_DA = Bus('ADC_DA', 12)
ADC_DB = Bus('ADC_DB', 12)
ADC_SEL = Net('ADC_SEL')
ADC_MSBI_SEN = Net('ADC_MSBI_SEN')
ADC_OEA_SCLK = Net('ADC_OEA_SCLK')
ADC_STPD_SDATA = Net('ADC_STPD_SDATA')
ADC_OEB = Net('ADC_OEB')

# ---- FT232H sync FIFO -------------------------------------------------------
FT_D = Bus('FT_D', 8)
FT_RXF_N = Net('FT_RXF_N')
FT_TXE_N = Net('FT_TXE_N')
FT_RD_N = Net('FT_RD_N')
FT_WR_N = Net('FT_WR_N')
FT_CLKOUT = Net('FT_CLKOUT')
FT_OE_N = Net('FT_OE_N')

# ---- Blocks -----------------------------------------------------------------
usb_power_in(vbus_sw=VBUS_SW, usb_dp=USB_DP, usb_dm=USB_DM, gnd=GND, tag='usb_power_in')

pwr_digital(vbus_sw=VBUS_SW, v3v3d=V3V3D, v1v2=V1V2, v1v8=V1V8, gnd=GND, tag='pwr_digital')

pwr_analog(vbus_sw=VBUS_SW, v3v3a=V3V3A, vafe_p=VAFE_P, vafe_n=VAFE_N, gnd=GND,
           tag='pwr_analog')

afe_ch_a(ain_p=ADC_AINA_P, ain_n=ADC_AINA_N, adc_vcm=ADC_VCM, vafe_p=VAFE_P, vafe_n=VAFE_N,
         v3v3a=V3V3A, gnd=GND, tag='afe_ch_a')

afe_ch_b(ain_p=ADC_AINB_P, ain_n=ADC_AINB_N, adc_vcm=ADC_VCM, vafe_p=VAFE_P, vafe_n=VAFE_N,
         v3v3a=V3V3A, gnd=GND, tag='afe_ch_b')

adc_dual(aina_p=ADC_AINA_P, aina_n=ADC_AINA_N, ainb_p=ADC_AINB_P, ainb_n=ADC_AINB_N,
         adc_vcm=ADC_VCM, adc_clk=ADC_CLK, adc_da=ADC_DA, adc_db=ADC_DB, adc_sel=ADC_SEL,
         adc_msbi_sen=ADC_MSBI_SEN, adc_oea_sclk=ADC_OEA_SCLK, adc_stpd_sdata=ADC_STPD_SDATA,
         adc_oeb=ADC_OEB, v3v3a=V3V3A, v3v3d=V3V3D, gnd=GND, tag='adc_dual')

clock_gen(adc_clk=ADC_CLK, fpga_clk40=FPGA_CLK40, v3v3d=V3V3D, gnd=GND, tag='clock_gen')

fpga(fpga_clk40=FPGA_CLK40, adc_da=ADC_DA, adc_db=ADC_DB, adc_sel=ADC_SEL,
     adc_msbi_sen=ADC_MSBI_SEN, adc_oea_sclk=ADC_OEA_SCLK, adc_stpd_sdata=ADC_STPD_SDATA,
     adc_oeb=ADC_OEB, ft_d=FT_D, ft_rxf_n=FT_RXF_N, ft_txe_n=FT_TXE_N, ft_rd_n=FT_RD_N,
     ft_wr_n=FT_WR_N, ft_clkout=FT_CLKOUT, ft_oe_n=FT_OE_N, v1v2=V1V2, v1v8=V1V8,
     v3v3d=V3V3D, gnd=GND, tag='fpga')

usb_bridge(usb_dp=USB_DP, usb_dm=USB_DM, ft_d=FT_D, ft_rxf_n=FT_RXF_N, ft_txe_n=FT_TXE_N,
           ft_rd_n=FT_RD_N, ft_wr_n=FT_WR_N, ft_clkout=FT_CLKOUT, ft_oe_n=FT_OE_N,
           vbus_sw=VBUS_SW, v3v3d=V3V3D, gnd=GND, tag='usb_bridge')


def _stabilize_tags():
    """Derive every untagged part's tag from its refdes (see "Stable netlists")."""
    for part in default_circuit.parts:
        if not getattr(part, 'tag', None):
            part.tag = part.ref


if __name__ == '__main__':
    _stabilize_tags()
    ERC()
    generate_netlist(file_=os.path.join(_PROJECT, 'outputs', 'dual_adc_usb.net'))
    generate_xml(file_=os.path.join(_PROJECT, 'outputs', 'dual_adc_usb_bom.xml'))
