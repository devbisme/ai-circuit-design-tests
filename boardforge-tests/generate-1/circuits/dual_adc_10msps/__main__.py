"""dual_adc_10msps — top-level assembly.

Creates every inter-block net from architecture/net_plan.md and calls each block with the
signature declared in its handoffs/05_blocks/<block>.md. boardforge imports this package,
runs ERC and writes the outputs; no ERC()/generate_*() here.
"""
from skidl import *

from .usb_c_input import usb_c_input
from .power_digital import power_digital
from .power_analog import power_analog
from .afe_channel import afe_channel
from .adc import adc
from .clock import clock
from .sdram import sdram
from .usb_fifo import usb_fifo
from .fpga import fpga

# ---- Power rails (driven inside their source blocks; only GND is driven here) ----
GND = Net('GND')
GND.drive = POWER                 # ground reference: no block drives it
Part('power', 'PWR_FLAG', ref='#FLG001')[1] += GND   # KiCad ERC: GND has only power_in pins
V5 = Net('+5V')                   # driven + #FLG501 in usb_c_input
P3V3 = Net('+3V3')                # driven + #FLG601 in power_digital
P1V2 = Net('+1V2')                # U602 power_out in power_digital
P3V3A = Net('+3V3A')              # U701 power_out in power_analog
P4V0A = Net('+4V0A')              # U702 OUT+ power_out in power_analog
N4V0A = Net('-4V0A')              # U702 OUT- power_out in power_analog

# ---- Analog front end <-> ADC ----
VIN_A = Net('VIN_A')
VIN_B = Net('VIN_B')
AIN_AP = Net('AIN_AP')
AIN_AN = Net('AIN_AN')
AIN_BP = Net('AIN_BP')
AIN_BN = Net('AIN_BN')
ADC_CM = Net('ADC_CM')

# ---- Clocks ----
ADC_CLK = Net('ADC_CLK')
CLK10_FPGA = Net('CLK10_FPGA')

# ---- ADC <-> FPGA ----
DA = Bus('DA', 12)                # DA0..DA11, index 0 = LSB
DB = Bus('DB', 12)
ADC_DVA = Net('ADC_DVA')
ADC_OVRA = Net('ADC_OVRA')
ADC_OVRB = Net('ADC_OVRB')
ADC_SEL = Net('ADC_SEL')
ADC_SEN = Net('ADC_SEN')
ADC_SCLK = Net('ADC_SCLK')
ADC_SDATA = Net('ADC_SDATA')

# ---- SDRAM <-> FPGA ----
SD_DQ = Bus('SD_DQ', 16)
SD_A = Bus('SD_A', 12)
SD_BA = Bus('SD_BA', 2)
SD_CLK = Net('SD_CLK')
SD_CKE = Net('SD_CKE')
SD_CS_N = Net('SD_CS_N')
SD_RAS_N = Net('SD_RAS_N')
SD_CAS_N = Net('SD_CAS_N')
SD_WE_N = Net('SD_WE_N')
SD_LDQM = Net('SD_LDQM')
SD_UDQM = Net('SD_UDQM')

# ---- USB FIFO <-> FPGA ----
FT_D = Bus('FT_D', 8)
FT_RXF_N = Net('FT_RXF_N')
FT_TXE_N = Net('FT_TXE_N')
FT_RD_N = Net('FT_RD_N')
FT_WR_N = Net('FT_WR_N')
FT_OE_N = Net('FT_OE_N')
FT_CLKOUT = Net('FT_CLKOUT')

# ---- USB connector <-> FIFO ----
USB_DP = Net('USB_DP')
USB_DM = Net('USB_DM')

# ---- Blocks ----
usb_c_input(v5=V5, usb_dp=USB_DP, usb_dm=USB_DM, gnd=GND, tag='usb_c_input')
power_digital(v5=V5, v3v3=P3V3, v1v2=P1V2, gnd=GND, tag='power_digital')
power_analog(v5=V5, v3v3a=P3V3A, vp4a=P4V0A, vn4a=N4V0A, gnd=GND, tag='power_analog')
afe_channel(ch="A", vin=VIN_A, ain_p=AIN_AP, ain_n=AIN_AN, adc_cm=ADC_CM,
            vp4a=P4V0A, vn4a=N4V0A, v3v3a=P3V3A, gnd=GND, tag='afe_ch_a')
afe_channel(ch="B", vin=VIN_B, ain_p=AIN_BP, ain_n=AIN_BN, adc_cm=ADC_CM,
            vp4a=P4V0A, vn4a=N4V0A, v3v3a=P3V3A, gnd=GND, tag='afe_ch_b')
adc(ain_ap=AIN_AP, ain_an=AIN_AN, ain_bp=AIN_BP, ain_bn=AIN_BN, adc_cm=ADC_CM,
    adc_clk=ADC_CLK, da=DA, db=DB, adc_dva=ADC_DVA, adc_ovra=ADC_OVRA, adc_ovrb=ADC_OVRB,
    adc_sel=ADC_SEL, adc_sen=ADC_SEN, adc_sclk=ADC_SCLK, adc_sdata=ADC_SDATA,
    v3v3a=P3V3A, v3v3=P3V3, gnd=GND, tag='adc')
clock(v3v3=P3V3, adc_clk=ADC_CLK, clk10_fpga=CLK10_FPGA, gnd=GND, tag='clock')
sdram(sd_dq=SD_DQ, sd_a=SD_A, sd_ba=SD_BA, sd_clk=SD_CLK, sd_cke=SD_CKE, sd_cs_n=SD_CS_N,
      sd_ras_n=SD_RAS_N, sd_cas_n=SD_CAS_N, sd_we_n=SD_WE_N, sd_ldqm=SD_LDQM,
      sd_udqm=SD_UDQM, v3v3=P3V3, gnd=GND, tag='sdram')
usb_fifo(usb_dp=USB_DP, usb_dm=USB_DM, ft_d=FT_D, ft_rxf_n=FT_RXF_N, ft_txe_n=FT_TXE_N,
         ft_rd_n=FT_RD_N, ft_wr_n=FT_WR_N, ft_oe_n=FT_OE_N, ft_clkout=FT_CLKOUT,
         v3v3=P3V3, gnd=GND, tag='usb_fifo')
fpga(clk10_fpga=CLK10_FPGA, da=DA, db=DB, adc_dva=ADC_DVA, adc_ovra=ADC_OVRA,
     adc_ovrb=ADC_OVRB, adc_sel=ADC_SEL, adc_sen=ADC_SEN, adc_sclk=ADC_SCLK,
     adc_sdata=ADC_SDATA, sd_dq=SD_DQ, sd_a=SD_A, sd_ba=SD_BA, sd_clk=SD_CLK,
     sd_cke=SD_CKE, sd_cs_n=SD_CS_N, sd_ras_n=SD_RAS_N, sd_cas_n=SD_CAS_N,
     sd_we_n=SD_WE_N, sd_ldqm=SD_LDQM, sd_udqm=SD_UDQM, ft_d=FT_D, ft_rxf_n=FT_RXF_N,
     ft_txe_n=FT_TXE_N, ft_rd_n=FT_RD_N, ft_wr_n=FT_WR_N, ft_oe_n=FT_OE_N,
     ft_clkout=FT_CLKOUT, v3v3=P3V3, v1v2=P1V2, gnd=GND, tag='fpga')


def _stabilize_tags():
    """Derive every untagged part's tag from its refdes (rules/skidl-syntax.md § Stable netlists)."""
    for part in default_circuit.parts:
        if not getattr(part, 'tag', None):
            part.tag = part.ref


_stabilize_tags()   # at import time: boardforge imports this module, it doesn't run __main__
