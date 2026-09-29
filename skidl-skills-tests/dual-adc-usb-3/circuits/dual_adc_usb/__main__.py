"""dual_adc_usb — assembly
Dual-channel ±10 V, 12-bit, 10 MSPS oscilloscope-style digitizer over USB 2.0.

Creates every top-level net, instantiates the nine blocks, runs ERC, and writes the
netlist and BOM. Block signatures come from handoffs/02_architecture.md's block
manifest; `analog_frontend` is written once and instantiated twice (CH1, CH2).

Read alongside:
    SPEC.md                             requirements
    architecture/net_plan.md            the net-by-net contract
    architecture/driver_amendments.md   A1-A4, which override the net plan where
                                        they conflict (THS4551 supply, FPGA I/O
                                        budget, 3.3 V->1.8 V reset translation)

Run:
    KICAD9_SYMBOL_DIR="/usr/share/kicad/symbols:$PWD/symbols" \
        PYTHONPATH="$PWD/circuits/dual_adc_usb" \
        .venv/bin/python circuits/dual_adc_usb/__main__.py
"""
from skidl import *

from analog_frontend import analog_frontend
from adc_pair import adc_pair
from aux_io import aux_io
from clock_gen import clock_gen
from fpga_capture import fpga_capture
from power_analog import power_analog
from power_digital import power_digital
from usb_c_port import usb_c_port
from usb_controller import usb_controller

# ---------------------------------------------------------------- power nets ----
# One ground for the whole board: the analog/digital plane split and its single tie
# point under the ADCs is a LAYOUT instruction (design_risks.md R12), not a netlist
# one. Creating AGND here would only produce a floating-net ERC error.
GND = Net('GND'); GND.drive = POWER
VBUS = Net('VBUS'); VBUS.drive = POWER

V3V3_AON = Net('+3V3_AON'); V3V3_AON.drive = POWER   # U1, always on
V3V3 = Net('+3V3'); V3V3.drive = POWER               # U2 buck, gated by PWR_EN
V1V2 = Net('+1V2'); V1V2.drive = POWER               # U3 buck, FPGA core
V1V8 = Net('+1V8'); V1V8.drive = POWER               # U4 LDO, FPGA PSRAM bank
VPOS = Net('+4V2A'); VPOS.drive = POWER              # U5 LM27762 positive
VNEG = Net('-4V2A'); VNEG.drive = POWER              # U5 LM27762 negative
AVDD = Net('+3V0A'); AVDD.drive = POWER              # U6 LDO, ADC analog

PWR_EN = Net('PWR_EN')            # FX2LP PA0 gates every rail except +3V3_AON

# --------------------------------------------------------------- signal nets ----
USB_DP, USB_DM = Net('USB_DP'), Net('USB_DM')

CH1_IN, CH2_IN = Net('CH1_IN'), Net('CH2_IN')
CH1_ADC_P, CH1_ADC_N = Net('CH1_ADC_P'), Net('CH1_ADC_N')
CH2_ADC_P, CH2_ADC_N = Net('CH2_ADC_P'), Net('CH2_ADC_N')
VCM = Net('VCM')                  # 1.50 V, generated in adc_pair, used by both FDAs

CLK_ADC1, CLK_ADC2, CLK_FPGA = Net('CLK_ADC1'), Net('CLK_ADC2'), Net('CLK_FPGA')

ADC1_D = Bus('ADC1_D', 12)        # [0] = LSB, offset binary
ADC2_D = Bus('ADC2_D', 12)
# ADC1_OTR / ADC2_OTR are NOT routed — amendment A2. They are still created so the
# block signatures from the architecture's manifest stay intact; each end ties its
# own pin to NC, so no net is generated.
ADC1_OTR, ADC2_OTR = Net('ADC1_OTR'), Net('ADC2_OTR')
ADC1_OTR.do_erc = False           # intentionally empty — see amendment A2
ADC2_OTR.do_erc = False

FD = Bus('FD', 8)                 # FPGA <-> FX2LP slave-FIFO data
FIFOADR = Bus('FIFOADR', 2)
IFCLK = Net('IFCLK')
SLWR_N, SLRD_N = Net('SLWR_N'), Net('SLRD_N')
SLOE_N, PKTEND_N = Net('SLOE_N'), Net('PKTEND_N')
FLAGA, FLAGB, FLAGC = Net('FLAGA'), Net('FLAGB'), Net('FLAGC')
FPGA_RST_N = Net('FPGA_RST_N')    # 3.3 V; divided to 1.8 V inside fpga_capture (A3)

TRIG_IO = Net('TRIG_IO')
LED_CAP_N = Net('LED_CAP_N')

# ------------------------------------------------------------------- blocks ----
usb_c_port(vbus=VBUS, gnd=GND, usb_dp=USB_DP, usb_dm=USB_DM, tag='usb_c_port')

power_digital(vbus=VBUS, gnd=GND, pwr_en=PWR_EN, v3v3_aon=V3V3_AON,
              v3v3=V3V3, v1v2=V1V2, v1v8=V1V8, tag='power_digital')

power_analog(vbus=VBUS, gnd=GND, pwr_en=PWR_EN, vpos=VPOS, vneg=VNEG,
             avdd=AVDD, tag='power_analog')

# One block file, two channels. Amendment A1: the FDA inside runs single-supply from
# VPOS to GND; VNEG still feeds the AD8066 buffer, which must swing below ground.
analog_frontend(bnc_in=CH1_IN, adc_p=CH1_ADC_P, adc_n=CH1_ADC_N,
                vcm=VCM, vpos=VPOS, vneg=VNEG, gnd=GND, ch=1, tag='afe_ch1')
analog_frontend(bnc_in=CH2_IN, adc_p=CH2_ADC_P, adc_n=CH2_ADC_N,
                vcm=VCM, vpos=VPOS, vneg=VNEG, gnd=GND, ch=2, tag='afe_ch2')

adc_pair(ch1_p=CH1_ADC_P, ch1_n=CH1_ADC_N, ch2_p=CH2_ADC_P, ch2_n=CH2_ADC_N,
         clk_adc1=CLK_ADC1, clk_adc2=CLK_ADC2, adc1_d=ADC1_D, adc2_d=ADC2_D,
         adc1_otr=ADC1_OTR, adc2_otr=ADC2_OTR, avdd=AVDD, v3v3=V3V3,
         vcm=VCM, gnd=GND, tag='adc_pair')

# avdd powers the fanout buffer so CLK_ADC* stays inside the AD9235's abs max (H2)
clock_gen(v3v3=V3V3, gnd=GND, clk_adc1=CLK_ADC1, clk_adc2=CLK_ADC2,
          clk_fpga=CLK_FPGA, avdd=AVDD, tag='clock_gen')

fpga_capture(v3v3=V3V3, v1v2=V1V2, v1v8=V1V8, gnd=GND, clk_fpga=CLK_FPGA,
             adc1_d=ADC1_D, adc2_d=ADC2_D, adc1_otr=ADC1_OTR, adc2_otr=ADC2_OTR,
             fd=FD, ifclk=IFCLK, slwr_n=SLWR_N, slrd_n=SLRD_N, sloe_n=SLOE_N,
             fifoadr=FIFOADR, flaga=FLAGA, flagb=FLAGB, flagc=FLAGC,
             pktend_n=PKTEND_N, fpga_rst_n=FPGA_RST_N, trig_io=TRIG_IO,
             led_cap_n=LED_CAP_N, tag='fpga_capture')

usb_controller(v3v3_aon=V3V3_AON, gnd=GND, usb_dp=USB_DP, usb_dm=USB_DM,
               fd=FD, ifclk=IFCLK, slwr_n=SLWR_N, slrd_n=SLRD_N, sloe_n=SLOE_N,
               fifoadr=FIFOADR, flaga=FLAGA, flagb=FLAGB, flagc=FLAGC,
               pktend_n=PKTEND_N, pwr_en=PWR_EN, fpga_rst_n=FPGA_RST_N,
               tag='usb_controller')

aux_io(v3v3=V3V3, v3v3_aon=V3V3_AON, gnd=GND, trig_io=TRIG_IO,
       led_cap_n=LED_CAP_N, tag='aux_io')


def _stabilize_tags():
    """Give every part a deterministic tag, derived from its refdes.

    ERC-REVIEW FIX (handoffs/06_erc.md): SKiDL builds each component's netlist
    timestamp/UUID from its `tag`, and invents a RANDOM one when the tag is unset.
    That makes every run emit a different netlist, so KiCad's "update PCB from
    schematic" sees the whole board as new parts and discards their placement and
    routing. Deriving the tag from the refdes means a part keeps its identity for as
    long as its refdes does, which is the property the PCB flow actually needs.
    """
    for part in default_circuit.parts:
        if not getattr(part, 'tag', None):
            part.tag = part.ref


if __name__ == '__main__':
    _stabilize_tags()
    ERC()
    generate_netlist(file_='outputs/dual_adc_usb.net')
    generate_xml(file_='outputs/dual_adc_usb_bom.xml')
