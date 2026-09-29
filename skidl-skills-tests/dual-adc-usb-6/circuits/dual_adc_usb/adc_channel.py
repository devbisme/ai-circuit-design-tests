"""ADC Channel — AD9237BCPZ-40 12-bit 40 MSPS ADC clocked at 10 MSa/s
Block from: architecture/block_diagram.md
Interface nets: CHn_AIN_P, CHn_AIN_N, CLK_ADC, ADCn_D[11:0], ADCn_OTR, ADC_PDWN,
                +3V3A_ADC, +3V3D, GND
"""
from skidl import *


@SubCircuit
def adc_channel(ch, ain_p, ain_n, clk_adc, data, otr, pdwn, avdd, dvdd, gnd):
    """One 12-bit ADC channel: differential analog pair in, parallel 12-bit CMOS out.

    AD9237BCPZ-40 in internal-reference mode (SENSE = AGND -> VREF = 1.0 V), MODE2 =
    AGND (SHA gain 2) giving a 2 Vp-p differential full-scale span -- exactly what the
    analog_frontend's THS4521 delivers. MODE = AGND -> offset-binary output, duty-cycle
    stabilizer disabled (the 10 MHz XO's duty cycle is already clean and DCS buys
    nothing at 1/4 of the part's rated rate).

    Instantiated twice. `ch` selects the instance and its refdes bank: CH1 gets
    U150/R150/C150-C161, CH2 gets U250/R250/C250-C261. Topology is identical.

    Args:
        ch:       Channel selector -- 'CH1'/'CH2' (or 1/2). Sets the refdes bank
                  (base = 100*n + 50 -> 150/250) and the internal net-name prefix.
        ain_p:    [in]  CHn_AIN_P -- differential analog input, positive leg (VIN+).
        ain_n:    [in]  CHn_AIN_N -- differential analog input, negative leg (VIN-).
        clk_adc:  [in]  CLK_ADC -- 10.000 MHz sample clock, shared by BOTH channels
                  (SPEC F13: <=100 ns channel-to-channel skew). Comes straight from X1
                  through R21 in the `clocking` block -- never from an FPGA PLL, since
                  12-bit SNR at 5 MHz input allows only ~6.4 ps RMS clock jitter.
        data:     [out] ADCn_D[11:0] -- 12-bit parallel output bus, bit 0 = D0 (LSB).
                  A SKiDL Bus (or any 12-element indexable of Nets).
        otr:      [out] ADCn_OTR -- out-of-range flag, driven by the ADC.
        pdwn:     [in]  ADC_PDWN -- power-down select, driven by the FPGA. AGND = power
                  up, 1/3*AVDD = standby, AVDD = full power-down (3-level pin, but the
                  FPGA drives it as a plain active-high CMOS signal: low = run).
        avdd:     [in]  +3V3A_ADC -- 3.300 V analog rail from U5 (LDO). Consumed only.
        dvdd:     [in]  +3V3D -- 3.3 V digital rail; feeds DRVDD only. Consumed only.
        gnd:      [in]  GND -- single plane, AGND and DGND both land here.

    Assumptions (see handoffs/05_blocks/adc_channel.md):
      - DRVDD (pin 16) is fed from `dvdd` (+3V3D), not from `avdd`. net_plan.md's power
        table says "+3V3A_ADC -> U150 AVDD/DRVDD", but its own block interface list for
        adc_channel carries BOTH rails and the handed-down signature has both `avdd` and
        `dvdd` -- +3V3D is the only pin +3V3D could reach in this block.
      - MODE2 (1) and OE (3) share one strap node pulled to GND through R150/R250, so a
        single DNP keeps BOTH of them off any DC tie when an AD9235 is substituted.
      - Pins 5/6 (DNC) are left genuinely unconnected, per the datasheet.
    """
    # ---- Instance -> refdes bank -------------------------------------------------
    n = int(str(ch).upper().replace('CH', ''))   # 'CH1' -> 1, 'CH2' -> 2
    b = 100 * n + 50                             # refdes base: 150 / 250
    p = f'CH{n}'                                 # internal net-name prefix

    # ---- Part templates (values/footprints verbatim from sourcing/sourced_bom.md) --
    _r0402 = Part('Device', 'R', dest=TEMPLATE,
                  footprint='Resistor_SMD:R_0402_1005Metric')
    _c0402 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0402_1005Metric')
    _c0805 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0805_2012Metric')

    # ---- Internal nets (net_plan.md "adc_channel instance nets") -----------------
    vref  = Net(f'{p}_VREF')        # internal 1.0 V reference output (SENSE = AGND)
    reft  = Net(f'{p}_REFT')        # differential reference (+)
    refb  = Net(f'{p}_REFB')        # differential reference (-)
    strap = Net(f'{p}_MODE_STRAP')  # MODE2 + OE common strap node -> GND via R{b}

    # =============================================================================
    # 1. The ADC itself
    #    Pin map (datasheet "PIN FUNCTION DESCRIPTIONS, 32 Pin LFCSP"):
    #      1 MODE2   2 CLK    3 OE     4 PDWN   5,6 DNC   7-14 D0-D7  15 DGND
    #      16 DRVDD  17-20 D8-D11     21 OTR   22 MODE   23 SENSE   24 VREF
    #      25 REFB   26 REFT  27,32 AVDD  28,31 AGND  29 VIN+  30 VIN-  33 EP
    #    Data pins are addressed BY NUMBER: the symbol names them 'D0(LSB)' and
    #    'D11(MSB)', which are awkward strings to key on.
    # =============================================================================
    U = Part('dual_adc_usb', 'AD9237BCPZ-40', ref=f'U{b}', value='AD9237BCPZ-40',
             footprint='Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.3x3.3mm')

    # Analog input pair
    ain_p += U[29]                  # VIN+
    ain_n += U[30]                  # VIN-

    # Clock, power-down, flags
    clk_adc += U[2]                 # CLK -- shared low-jitter net, both channels
    pdwn += U[4]                    # PDWN -- FPGA-driven, low = power up
    otr += U[21]                    # OTR -- out-of-range flag, ADC drives it

    # 12-bit parallel data out, LSB first
    for bit, pin in enumerate((7, 8, 9, 10, 11, 12, 13, 14, 17, 18, 19, 20)):
        data[bit] += U[pin]

    # Supplies and grounds
    avdd += U[27], U[32]            # AVDD  <- +3V3A_ADC (clean LDO rail)
    dvdd += U[16]                   # DRVDD <- +3V3D  (see docstring assumption)
    gnd += U[28], U[31]             # AGND
    gnd += U[15]                    # DGND -- single plane, joined at the ADC
    gnd += U[33]                    # EP -- must be soldered to the ground plane

    # Pins 5 and 6 are DNC on both AD9237 and AD9235 -- deliberately left unconnected.

    # =============================================================================
    # 2. Static mode straps
    #    MODE2 = AGND  -> SHA gain 2; with VREF = 1.0 V that is a 2 Vp-p span, which
    #                     is the span net_plan.md specifies and what the FDA delivers.
    #    OE    = AGND  -> outputs permanently enabled (one dedicated bus per ADC).
    #    MODE  = AGND  -> offset binary, duty-cycle stabilizer disabled.
    #    SENSE = AGND  -> internal 1.0 V reference.
    #
    #    MODE2 and OE are the ONLY two pins that differ from the AD9235 second source
    #    (there they are DNC). They share ONE strap node so that de-populating the
    #    single allocated resistor R{b} leaves both of them off any DC tie -- see the
    #    handoff's "named assumption" on AD9235 DNC tolerance. MODE and SENSE are real
    #    pins on both parts, so they tie to GND directly with no DNP resistor.
    # =============================================================================
    R_strap = _r0402(ref=f'R{b}', value='10k')   # DNP for an AD9235 build

    strap += U[1], U[3], R_strap[1]
    gnd += R_strap[2]
    gnd += U[22]                    # MODE
    gnd += U[23]                    # SENSE

    # =============================================================================
    # 3. Reference decoupling (net_plan: "U150.VREF + 0.1 uF",
    #    "U150.REFT/REFB decoupling 0.1 uF + 10 uF")
    # =============================================================================
    C_vref  = _c0402(ref=f'C{b + 3}', value='100nF')
    C_reft  = _c0402(ref=f'C{b + 4}', value='100nF')
    C_refb  = _c0402(ref=f'C{b + 5}', value='100nF')
    C_refd  = _c0402(ref=f'C{b + 6}', value='100nF')    # REFT-REFB differential
    C_reftb = _c0805(ref=f'C{b + 10}', value='10uF')    # REFT bulk
    C_refbb = _c0805(ref=f'C{b + 11}', value='10uF')    # REFB bulk

    vref += U[24], C_vref[1]
    gnd += C_vref[2]
    reft += U[26], C_reft[1], C_reftb[1], C_refd[1]
    gnd += C_reft[2], C_reftb[2]
    refb += U[25], C_refb[1], C_refbb[1], C_refd[2]
    gnd += C_refb[2], C_refbb[2]

    # =============================================================================
    # 4. Supply decoupling -- 100 nF at every supply pin + local bulk on each rail.
    #    100 nF = CL05B104KB54PNC (0402), 10 uF = CL21A106KAYNNNE (0805).
    # =============================================================================
    C_av27 = _c0402(ref=f'C{b + 0}', value='100nF')     # AVDD pin 27
    C_av32 = _c0402(ref=f'C{b + 1}', value='100nF')     # AVDD pin 32
    C_dv16 = _c0402(ref=f'C{b + 2}', value='100nF')     # DRVDD pin 16
    C_aent = _c0402(ref=f'C{b + 7}', value='100nF')     # +3V3A_ADC block entry
    C_avb  = _c0805(ref=f'C{b + 8}', value='10uF')      # AVDD local bulk
    C_dvb  = _c0805(ref=f'C{b + 9}', value='10uF')      # DRVDD local bulk

    for c in (C_av27, C_av32, C_aent, C_avb):
        avdd += c[1]
        gnd += c[2]
    for c in (C_dv16, C_dvb):
        dvdd += c[1]
        gnd += c[2]
