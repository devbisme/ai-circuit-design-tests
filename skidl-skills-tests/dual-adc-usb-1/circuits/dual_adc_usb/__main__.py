"""Dual-channel 10 MSPS / 12-bit USB oscilloscope-input ADC board — assembled.

Run from the project root:
    KICAD9_SYMBOL_DIR=/usr/share/kicad/symbols python3 -m circuits.dual_adc_usb

Nets and inter-block wiring follow architecture/net_plan.md §1 exactly.
"""
from skidl import *

from .usb_power_input import usb_power_input
from .power_digital import power_digital
from .power_analog import power_analog
from .vref_2v5 import vref_2v5
from .afe_channel import afe_channel
from .adc_dual import adc_dual
from .clock_40m import clock_40m
from .fpga_ice40 import fpga_ice40
from .sram_buffer import sram_buffer
from .config_flash import config_flash
from .usb_bridge_ft2232h import usb_bridge_ft2232h
from .aux_io import aux_io

# ======================================================================
# 1.1 Power rails — all .drive = POWER
#
# VBUS_5V and VBUS_A5V are SEPARATE NETS joined only through the split
# ferrite inside usb_power_input. That is SPEC §3.1 "split analog/digital at
# source", and it must survive into the netlist so layout cannot merge them.
# ======================================================================
GND = Net('GND'); GND.drive = POWER
VBUS_5V = Net('VBUS_5V'); VBUS_5V.drive = POWER
VBUS_A5V = Net('VBUS_A5V'); VBUS_A5V.drive = POWER
V3V3_D = Net('V3V3_D'); V3V3_D.drive = POWER
V1V2_CORE = Net('V1V2_CORE'); V1V2_CORE.drive = POWER
V3V0_AVDD = Net('V3V0_AVDD'); V3V0_AVDD.drive = POWER
VP4V0 = Net('VP4V0'); VP4V0.drive = POWER
VN4V0 = Net('VN4V0'); VN4V0.drive = POWER

# ======================================================================
# 1.2 Reference / bias.  adcVcmA and adcVcmB MUST stay separate — the
# LTC2292 pin descriptions say "Do not connect to VCMB" / "...to VCMA".
# ======================================================================
vref1V0 = Net('vref1V0')
adcVcmA = Net('adcVcmA')
adcVcmB = Net('adcVcmB')

# 1.3 Analog signal pairs
ainAP = Net('ainAP'); ainAN = Net('ainAN')
ainBP = Net('ainBP'); ainBN = Net('ainBN')

# 1.4 Clocks. xoClkFpga is the system clock AND the ADC data-capture clock
# (falling edge) — there is no adcClkOut, see net_plan.md §1.4.1.
encClk40 = Net('encClk40')
xoClkFpga = Net('xoClkFpga')
ftClk60 = Net('ftClk60')

# 1.5 ADC parallel data
adcDataA = Bus('adcDataA', 12)
adcDataB = Bus('adcDataB', 12)
adcOfA = Net('adcOfA'); adcOfB = Net('adcOfB')
adcShdn = Net('adcShdn'); adcOeBar = Net('adcOeBar')

# 1.6 SRAM interface
sramAddr = Bus('sramAddr', 21)
sramData = Bus('sramData', 16)
sramCeBar = Net('sramCeBar')
sramOeBar = Net('sramOeBar')
sramWeBar = Net('sramWeBar')

# 1.7 FT2232H channel A — synchronous 245 FIFO
fifoData = Bus('fifoData', 8)
fifoRxfBar = Net('fifoRxfBar')
fifoTxeBar = Net('fifoTxeBar')
fifoRdBar = Net('fifoRdBar')
fifoWrBar = Net('fifoWrBar')
fifoOeBar = Net('fifoOeBar')

# 1.8 Configuration / FT2232H channel B (MPSSE)
cfgSck = Net('cfgSck')
cfgMosi = Net('cfgMosi')
cfgMiso = Net('cfgMiso')
cfgCsBar = Net('cfgCsBar')
fpgaCresetBar = Net('fpgaCresetBar')
fpgaCdone = Net('fpgaCdone')
modeStrap = Net('modeStrap')
ftResetBar = Net('ftResetBar')

# 1.9 USB
usbDp = Net('usbDp'); usbDm = Net('usbDm')

# 1.10 Auxiliary I/O
probeCompDrv = Net('probeCompDrv')
extTrig = Net('extTrig')
ledStatus = Net('ledStatus')
ledActivity = Net('ledActivity')

# ======================================================================
# 2. Block instantiation
# ======================================================================
usb_power_input(vbus_5v=VBUS_5V, vbus_a5v=VBUS_A5V, gnd=GND,
                usb_dp=usbDp, usb_dm=usbDm)

power_digital(vbus_5v=VBUS_5V, v3v3_d=V3V3_D, v1v2_core=V1V2_CORE, gnd=GND)

power_analog(vbus_a5v=VBUS_A5V, v3v0_avdd=V3V0_AVDD,
             vp4v0=VP4V0, vn4v0=VN4V0, gnd=GND)

vref_2v5(vbus_a5v=VBUS_A5V, vp4v0=VP4V0, vn4v0=VN4V0, gnd=GND,
         vref_1v0=vref1V0)

# afe_channel is the only parameterised block. The two instances differ ONLY
# in designator block and net suffix — and in which VCM output they take.
afe_channel(ch='A', vp4v0=VP4V0, vn4v0=VN4V0, gnd=GND,
            adc_vcm=adcVcmA, ain_p=ainAP, ain_n=ainAN)
afe_channel(ch='B', vp4v0=VP4V0, vn4v0=VN4V0, gnd=GND,
            adc_vcm=adcVcmB, ain_p=ainBP, ain_n=ainBN)

adc_dual(v3v0_avdd=V3V0_AVDD, v3v3_d=V3V3_D, gnd=GND,
         vref_1v0=vref1V0, adc_vcm_a=adcVcmA, adc_vcm_b=adcVcmB,
         ain_ap=ainAP, ain_an=ainAN, ain_bp=ainBP, ain_bn=ainBN,
         enc_clk40=encClk40,
         adc_data_a=adcDataA, adc_data_b=adcDataB,
         adc_of_a=adcOfA, adc_of_b=adcOfB,
         adc_shdn=adcShdn, adc_oe_bar=adcOeBar)

clock_40m(vbus_a5v=VBUS_A5V, gnd=GND,
          enc_clk40=encClk40, xo_clk_fpga=xoClkFpga)

fpga_ice40(v3v3_d=V3V3_D, v1v2_core=V1V2_CORE, gnd=GND,
           adc_data_a=adcDataA, adc_data_b=adcDataB,
           adc_of_a=adcOfA, adc_of_b=adcOfB,
           adc_shdn=adcShdn, adc_oe_bar=adcOeBar, xo_clk_fpga=xoClkFpga,
           sram_addr=sramAddr, sram_data=sramData,
           sram_ce_bar=sramCeBar, sram_oe_bar=sramOeBar,
           sram_we_bar=sramWeBar,
           fifo_data=fifoData, fifo_rxf_bar=fifoRxfBar,
           fifo_txe_bar=fifoTxeBar, fifo_rd_bar=fifoRdBar,
           fifo_wr_bar=fifoWrBar, fifo_oe_bar=fifoOeBar, ft_clk60=ftClk60,
           cfg_sck=cfgSck, cfg_mosi=cfgMosi, cfg_miso=cfgMiso,
           cfg_cs_bar=cfgCsBar,
           fpga_creset_bar=fpgaCresetBar, fpga_cdone=fpgaCdone,
           mode_strap=modeStrap,
           probe_comp_drv=probeCompDrv, ext_trig=extTrig,
           led_status=ledStatus, led_activity=ledActivity)

sram_buffer(v3v3_d=V3V3_D, gnd=GND,
            sram_addr=sramAddr, sram_data=sramData,
            sram_ce_bar=sramCeBar, sram_oe_bar=sramOeBar,
            sram_we_bar=sramWeBar)

config_flash(v3v3_d=V3V3_D, gnd=GND,
             cfg_sck=cfgSck, cfg_mosi=cfgMosi, cfg_miso=cfgMiso,
             cfg_cs_bar=cfgCsBar,
             fpga_creset_bar=fpgaCresetBar, fpga_cdone=fpgaCdone,
             mode_strap=modeStrap)

usb_bridge_ft2232h(v3v3_d=V3V3_D, gnd=GND, usb_dp=usbDp, usb_dm=usbDm,
                   fifo_data=fifoData, fifo_rxf_bar=fifoRxfBar,
                   fifo_txe_bar=fifoTxeBar, fifo_rd_bar=fifoRdBar,
                   fifo_wr_bar=fifoWrBar, fifo_oe_bar=fifoOeBar,
                   ft_clk60=ftClk60,
                   cfg_sck=cfgSck, cfg_mosi=cfgMosi, cfg_miso=cfgMiso,
                   cfg_cs_bar=cfgCsBar,
                   fpga_creset_bar=fpgaCresetBar, fpga_cdone=fpgaCdone,
                   ft_reset_bar=ftResetBar)

aux_io(v3v3_d=V3V3_D, gnd=GND,
       probe_comp_drv=probeCompDrv, ext_trig=extTrig,
       led_status=ledStatus, led_activity=ledActivity)


if __name__ == '__main__':
    ERC()
