"""ADC Dual — ADS5231 dual 12-bit pipeline ADC, both channels, serial-mode control.
Block from: architecture/block_diagram.md
Interface nets: ADC_INAP, ADC_INAN, ADC_INBP, ADC_INBN, ADC_CM, CLK10_ADC,
    ADC_DA[0:11], ADC_DB[0:11], ADC_DVA, ADC_SEN, ADC_SCLK,
    ADC_SDATA, ADC_SEL, P3V3A, P3V3D, GND
"""
from skidl import *


@SubCircuit
def adc_dual(inap, inan, inbp, inbn, cm, clk_adc, da, db, dva,
             sen, sclk, sdata, sel, p3v3a, p3v3d, gnd):
    """ADS5231 dual 12-bit 40MSPS ADC operated at 10MSPS with the PLL disabled.

    Inputs (sensed by this block):
      inap/inan  -- channel A differential analog input, 1.0-2.0V per pin about
                    VCM=1.5V (SBAS295A p.19). Driven by afe_driver tag A.
      inbp/inbn  -- channel B differential analog input, same window.
      clk_adc    -- 10MHz sample clock from clock_gen (33R series at the source).
                    With the PLL disabled the duty cycle must be held near 50%.
      sel        -- serial-interface select, FPGA-driven. Must be HIGH for serial
                    mode; a low-going pulse resets the serial registers.
      sclk/sdata -- serial clock / serial data, FPGA-driven.
      sen        -- serial write enable, FPGA-driven.
      p3v3a      -- analog supply (AVDD) and the INT/EXT# strap (internal reference).
      p3v3d      -- output-driver supply (VDRV).
      gnd        -- single board ground (AGND and GND pins both land here; the
                    analog/digital split is a layout instruction, not a net split).

    Outputs (driven by this block):
      cm         -- +1.5V common-mode reference to both FDAs. Load <= +/-2mA, and
                    no resistive load is permitted, so nothing is hung on it here.
      da[0:11]   -- channel A data, da[11] = MSB.
      db[0:11]   -- channel B data, db[11] = MSB.
      dva        -- channel A data-valid strobe.

    Assumptions:
      - SEL/SEN/SCLK/SDATA are all FPGA-driven, NOT strapped. net_plan.md line 77
        ties pins 41/42 (MSBI/OEA#) statically to GND, which is wrong: those are the
        same physical pins as SEN/SCLK once SEL=1, and serial mode is mandatory to
        disable the internal PLL (the PLL floors fs at 20MSPS; this design runs
        10MSPS). Driver decision, already ratified -- see the block handoff.
      - OEB# (pin 6) is the only genuinely separate control pin, so it is the only
        one tied statically low (channel B outputs permanently enabled).
      - DVB (pin 22) is intentionally NC: only channel A's data-valid strobe is
        used, both channels being sampled by the same clock.
      - OVRA (39) and OVRB (9) are intentionally NC: the over-range flags are no
        longer routed to the FPGA (architecture rev.3 -- BANK3's 23 I/O follow
        VCCIO3 down to 1.8V for the in-package PSRAM, leaving 48 3.3V-capable
        I/O against 51 required, and overrange appears in no SPEC line). They
        are ADC OUTPUTS, so they are left genuinely open, never tied.
        Clipping stays visible in firmware as code 0x000/0xFFF.
      - ADC_CM's bypass capacitors are C119/C219, owned by the afe_driver blocks.
      - Pins are addressed by NUMBER, not by name: the symbol's names contain regex
        metacharacters ('INA+', 'OEB#', 'INT_EXT#') that are unsafe in SKiDL's
        name lookup. Numbers below are from SBAS295A p.11 (see the summary).
    """
    u4 = Part('dual_adc_usb', 'ADS5231IPAGT', ref='U4', value='ADS5231IPAGT',
              footprint='Package_QFP:TQFP-64_10x10mm_P0.5mm')

    # --- Supplies and grounds -------------------------------------------------
    u4[3, 46, 57] += p3v3a          # AVDD  x3, analog supply
    u4[5, 8, 40, 43] += p3v3d       # VDRV  x4, output-buffer supply
    u4[2, 47, 48, 49, 55, 58, 59, 61, 64] += gnd   # AGND x9
    u4[4, 7, 23, 25, 44] += gnd                    # GND  x5 (output buffer)

    # --- Analog inputs (polarity crossed upstream; do not "fix" here) ---------
    u4[50] += inap                  # INA+
    u4[51] += inan                  # INA-
    u4[63] += inbp                  # INB+
    u4[62] += inbn                  # INB-

    # --- References -----------------------------------------------------------
    u4[52] += cm                    # CM, +1.5V common-mode out to both FDAs
    u4[56] += p3v3a                 # INT/EXT# high = internal reference

    reft = Net('ADC_REFT')          # REFT/REFB are internal to this block
    refb = Net('ADC_REFB')
    u4[53] += reft
    u4[54] += refb

    iset = Net('ADC_ISET')
    u4[60] += iset

    # --- Clock ----------------------------------------------------------------
    u4[24] += clk_adc               # CLK, 10MHz

    # --- Data buses: D0_A..D11_A = pins 27..38, D0_B..D11_B = pins 10..21 -----
    for i in range(12):
        u4[27 + i] += da[i]
        u4[10 + i] += db[i]

    # --- Status / strobes -----------------------------------------------------
    u4[26] += dva                   # DVA
    u4[22] += NC                    # DVB deliberately unused (net_plan.md)
    u4[39] += NC                    # OVRA unused -- output, left open (rev.3)
    u4[9] += NC                     # OVRB unused -- output, left open (rev.3)

    # --- Serial control interface (SEL=1 selects it on pins 41/42/45) ---------
    # Sequence per SBAS295A p.8: raise SEL, pulse it low to reset the registers,
    # then clock the 8-bit word D7..D0 = 0 0 1 1 0 0 1 0 in on SDATA to disable
    # the PLL. All four lines therefore have to be FPGA-driven, not strapped.
    u4[1] += sel                    # SEL
    u4[41] += sen                   # MSBI/SEN   -> SEN
    u4[42] += sclk                  # OEA#/SCLK  -> SCLK
    u4[45] += sdata                 # STPD/SDATA -> SDATA
    u4[6] += gnd                    # OEB# low = channel B outputs enabled

    # --- Bias-setting resistor ------------------------------------------------
    r401 = Part('Device', 'R', ref='R401', value='56.2k',
                footprint='Resistor_SMD:R_0402_1005Metric')
    iset & r401 & gnd               # ISET = 56.2k to GND, datasheet-mandated

    # --- Decoupling -----------------------------------------------------------
    # One 100nF per supply pin, at the pin, plus one 10uF bulk on AVDD.
    cap_100n = Part('Device', 'C', dest=TEMPLATE, value='100nF',
                    footprint='Capacitor_SMD:C_0402_1005Metric')

    c401 = cap_100n(ref='C401')     # AVDD pin 3
    c402 = cap_100n(ref='C402')     # AVDD pin 46
    c403 = cap_100n(ref='C403')     # AVDD pin 57
    c404 = cap_100n(ref='C404')     # VDRV pin 5
    c405 = cap_100n(ref='C405')     # VDRV pin 8
    c407 = cap_100n(ref='C407')     # REFT pin 53
    c408 = cap_100n(ref='C408')     # REFB pin 54
    c409 = cap_100n(ref='C409')     # VDRV pin 40
    c410 = cap_100n(ref='C410')     # VDRV pin 43

    c406 = Part('Device', 'C', ref='C406', value='10uF',
                footprint='Capacitor_SMD:C_0805_2012Metric')   # AVDD bulk

    for c in (c401, c402, c403, c406):
        p3v3a & c & gnd
    for c in (c404, c405, c409, c410):
        p3v3d & c & gnd

    reft & c407 & gnd               # 0.1uF at the pin, per net_plan.md
    refb & c408 & gnd
