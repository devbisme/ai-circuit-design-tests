"""dual_adc_usb — top-level assembly.

Joins the eight blocks of `architecture/block_diagram.md` by the net names of
`architecture/net_plan.md` (verbatim). Ten block instances:

    usb_front x1, power x1, analog_frontend x2, adc_channel x2,
    clocking x1, fpga_core x1, buffer_memory x1, usb_bridge x1

Run it as a module from the project root (the blocks use relative imports):

    KICAD9_SYMBOL_DIR="$KICAD_SYMBOL_DIR:$PWD/symbols" .venv/bin/python -m circuits.dual_adc_usb

Integration only — no part, value or footprint is created here.
"""

from skidl import *

from .adc_channel import adc_channel
from .analog_frontend import analog_frontend
from .buffer_memory import buffer_memory
from .clocking import clocking
from .fpga_core import fpga_core
from .power import power
from .usb_bridge import usb_bridge
from .usb_front import usb_front


def build():
    """Create every inter-block net and instantiate every block."""

    # ------------------------------------------------------------------
    # Power and reference nets  (net_plan.md § "Power and reference nets")
    # ------------------------------------------------------------------
    GND = Net('GND')
    VBUS = Net('VBUS')                  # raw 5 V from the USB-C host
    VBUS_SW = Net('VBUS_SW')            # 5 V after the TPS22919 soft-start switch
    V3V3D = Net('+3V3D')                # buck U3 out via L1
    V1V2 = Net('+1V2')                  # buck U4 out via L2
    V3V3A_ADC = Net('+3V3A_ADC')        # LDO U5 out via FB3
    V3V3A_AMP = Net('+3V3A_AMP')        # LDO U6 out via FB4
    VREF_OFF = Net('VREF_OFF')          # 1.807 V, driven by U7 unit A (a real driver)
    VCM_REF = Net('VCM_REF')            # 1.650 V, unbuffered R16/R17 divider

    # Every rail below is generated behind a passive (L1/L2/FB3/FB4) or a
    # divider, or is only consumed at top level, so no pin drives it as far as
    # ERC is concerned. VREF_OFF is deliberately NOT flagged: U7 unit A drives it
    # through R19 (the 22 ohm RNULL added in rev.6), so the driving pin now sits on
    # the internal net VREF_OFF_AMP and VREF_OFF itself is passive-only. The
    # conclusion is unchanged; flagging it would be suppression, not a fix.
    for _rail in (GND, VBUS, VBUS_SW, V3V3D, V1V2, V3V3A_ADC, V3V3A_AMP, VCM_REF):
        _rail.drive = POWER

    # ------------------------------------------------------------------
    # USB front end  (net_plan.md § "USB / front-end nets")
    # ------------------------------------------------------------------
    USB_DP = Net('USB_DP')
    USB_DM = Net('USB_DM')

    # ------------------------------------------------------------------
    # Analog front end -> ADC  (per-channel, CHn_ prefixes are net_plan's)
    # ------------------------------------------------------------------
    CH1_BNC = Net('CH1_BNC')
    CH2_BNC = Net('CH2_BNC')
    CH1_AIN_P = Net('CH1_AIN_P')
    CH1_AIN_N = Net('CH1_AIN_N')
    CH2_AIN_P = Net('CH2_AIN_P')
    CH2_AIN_N = Net('CH2_AIN_N')

    # ------------------------------------------------------------------
    # Clock tree  (net_plan.md § "clocking nets")
    # ------------------------------------------------------------------
    # CLK_ADC is X1 -> R21 -> BOTH ADCs: ONE net object for both channels.
    # SPEC F13 (<=100 ns channel-to-channel skew) is met by the shared sample
    # clock, and 12-bit SNR at 5 MHz allows only ~6.4 ps RMS jitter, so it must
    # come from X1 and never from an FPGA PLL.
    CLK_ADC = Net('CLK_ADC')
    CLK_FPGA = Net('CLK_FPGA')          # X1 -> R22 -> U8 -> R23 -> U30 GCLK

    # ------------------------------------------------------------------
    # ADC capture buses  (bit 0 = LSB throughout)
    # ------------------------------------------------------------------
    ADC1_D = Bus('ADC1_D', 12)
    ADC2_D = Bus('ADC2_D', 12)
    ADC1_OTR = Net('ADC1_OTR')
    ADC2_OTR = Net('ADC2_OTR')
    ADC_PDWN = Net('ADC_PDWN')          # one FPGA pin, both ADCs

    # ------------------------------------------------------------------
    # SDRAM interface  (fpga_core <-> buffer_memory)
    # ------------------------------------------------------------------
    SDR_DQ = Bus('SDR_DQ', 16)
    SDR_A = Bus('SDR_A', 13)
    SDR_BA = Bus('SDR_BA', 2)
    SDR_CLK = Net('SDR_CLK')            # stops at R40 pin 1 inside buffer_memory
    SDR_CKE = Net('SDR_CKE')
    SDR_CS_N = Net('SDR_CS_N')
    SDR_RAS_N = Net('SDR_RAS_N')
    SDR_CAS_N = Net('SDR_CAS_N')
    SDR_WE_N = Net('SDR_WE_N')
    SDR_LDQM = Net('SDR_LDQM')
    SDR_UDQM = Net('SDR_UDQM')

    # ------------------------------------------------------------------
    # Slave-FIFO interface  (fpga_core <-> usb_bridge)
    # SCL/SDA/EE_A0-2/FX2_RESET_N are internal to usb_bridge — not created here.
    # ------------------------------------------------------------------
    FIFO_D = Bus('FIFO_D', 8)
    FIFOADR = Bus('FIFOADR', 2)
    IFCLK = Net('IFCLK')                # driven by U50
    SLWR_N = Net('SLWR_N')
    SLRD_N = Net('SLRD_N')
    SLOE_N = Net('SLOE_N')
    PKTEND_N = Net('PKTEND_N')
    FLAGB = Net('FLAGB')                # driven by U50
    FLAGC = Net('FLAGC')                # driven by U50

    # ==================================================================
    # Block instances — signatures verbatim from handoffs/05_blocks/*.md
    # ==================================================================

    # USB-C receptacle, ESD clamp, soft-start load switch (J1, U1, U2, R1-R3, C1-C3)
    usb_front(vbus=VBUS, vbus_sw=VBUS_SW, usb_dp=USB_DP, usb_dm=USB_DM,
              gnd=GND, tag='usb_front')

    # Two bucks + two LDOs + references (U3-U7, L1/L2, FB1-FB4, R10-R18, C10-C34)
    power(vbus_sw=VBUS_SW, v3v3d=V3V3D, v1v2=V1V2, v3v3a_adc=V3V3A_ADC,
          v3v3a_amp=V3V3A_AMP, vref_off=VREF_OFF, vcm_ref=VCM_REF,
          gnd=GND, tag='power')

    # Attenuator + buffer + 4th-order AAF + FDA, one per channel
    analog_frontend(ch='CH1', bnc_in=CH1_BNC, avdd=V3V3A_AMP, vref_off=VREF_OFF,
                    vcm_ref=VCM_REF, ain_p=CH1_AIN_P, ain_n=CH1_AIN_N, gnd=GND,
                    tag='afe_ch1')
    analog_frontend(ch='CH2', bnc_in=CH2_BNC, avdd=V3V3A_AMP, vref_off=VREF_OFF,
                    vcm_ref=VCM_REF, ain_p=CH2_AIN_P, ain_n=CH2_AIN_N, gnd=GND,
                    tag='afe_ch2')

    # AD9237 12-bit ADCs — SAME CLK_ADC and ADC_PDWN objects to both instances
    adc_channel(ch='CH1', ain_p=CH1_AIN_P, ain_n=CH1_AIN_N, clk_adc=CLK_ADC,
                data=ADC1_D, otr=ADC1_OTR, pdwn=ADC_PDWN,
                avdd=V3V3A_ADC, dvdd=V3V3D, gnd=GND, tag='adc_ch1')
    adc_channel(ch='CH2', ain_p=CH2_AIN_P, ain_n=CH2_AIN_N, clk_adc=CLK_ADC,
                data=ADC2_D, otr=ADC2_OTR, pdwn=ADC_PDWN,
                avdd=V3V3A_ADC, dvdd=V3V3D, gnd=GND, tag='adc_ch2')

    # 10 MHz XO + 74LVC1G17 buffer (X1, U8, R21-R23, C30/C31)
    clocking(vdd=V3V3D, clk_adc=CLK_ADC, clk_fpga=CLK_FPGA, gnd=GND, tag='clk')

    # XC6SLX9 + config flash + JTAG + LEDs (U30, U31, J4, D30/D31, R30-R39, C40-C69)
    fpga_core(adc1_d=ADC1_D, adc2_d=ADC2_D, adc1_otr=ADC1_OTR, adc2_otr=ADC2_OTR,
              adc_pdwn=ADC_PDWN, clk_fpga=CLK_FPGA, sdr_dq=SDR_DQ, sdr_a=SDR_A,
              sdr_ba=SDR_BA, sdr_clk=SDR_CLK, sdr_cke=SDR_CKE, sdr_cs_n=SDR_CS_N,
              sdr_ras_n=SDR_RAS_N, sdr_cas_n=SDR_CAS_N, sdr_we_n=SDR_WE_N,
              sdr_ldqm=SDR_LDQM, sdr_udqm=SDR_UDQM, fifo_d=FIFO_D, ifclk=IFCLK,
              slwr_n=SLWR_N, slrd_n=SLRD_N, sloe_n=SLOE_N, pktend_n=PKTEND_N,
              fifoadr=FIFOADR, flagb=FLAGB, flagc=FLAGC, v3v3d=V3V3D, v1v2=V1V2,
              gnd=GND, tag='fpga_core')

    # 32 MB x16 SDRAM capture buffer (U40, R40, C70-C78)
    buffer_memory(sdr_dq=SDR_DQ, sdr_a=SDR_A, sdr_ba=SDR_BA, sdr_clk=SDR_CLK,
                  sdr_cke=SDR_CKE, sdr_cs_n=SDR_CS_N, sdr_ras_n=SDR_RAS_N,
                  sdr_cas_n=SDR_CAS_N, sdr_we_n=SDR_WE_N, sdr_ldqm=SDR_LDQM,
                  sdr_udqm=SDR_UDQM, v3v3d=V3V3D, gnd=GND, tag='buffer_memory')

    # FX2LP + boot EEPROM + 24 MHz crystal (U50, U51, Y1, R50-R55, C80-C93)
    usb_bridge(usb_dp=USB_DP, usb_dm=USB_DM, fifo_d=FIFO_D, ifclk=IFCLK,
               slwr_n=SLWR_N, slrd_n=SLRD_N, sloe_n=SLOE_N, pktend_n=PKTEND_N,
               fifoadr=FIFOADR, flagb=FLAGB, flagc=FLAGC,
               v3v3d=V3V3D, gnd=GND, tag='usb_bridge')


def _stabilize_tags():
    """Derive every untagged part's tag from its refdes (stable netlist UUIDs)."""
    for part in default_circuit.parts:
        if not getattr(part, 'tag', None):
            part.tag = part.ref


if __name__ == '__main__':
    build()
    _stabilize_tags()
    ERC()
    # No netlist export here — that is phase 07, gated on a clean ERC review.
