"""ADC Channel — 12-bit 10 MSPS ADC (AD9235BRUZ-20), one instance per channel
Block from: architecture/block_diagram.md
Interface nets: ADC_<X>_IN, ADC_<X>_VINN, CLK_ADC_<X>, ADC<X>_PDWN, V3V3_A, V3V3_D, GND,
                ADC<X>_D[11:0], ADC<X>_OTR   (<X> = A or B)

This file is instantiated TWICE by the assembler (once per channel) with ch='A' and
ch='B' -- it is written parameterised, not duplicated. Ref designators and internal net
names are built from the `ch` suffix so the two instances never collide:
    Channel A -> U110, FB10, R120-R133, C120-C132
    Channel B -> U210, FB20, R220-R233, C220-C232
"""
from skidl import *


@subcircuit
def adc_channel(adc_in, adc_vinn, adc_clk, pdwn, v3v3_a, v3v3_d, gnd, data, otr, ch='A'):
    """AD9235BRUZ-20 12-bit, 20 MSPS (used at 10 MSPS) pipelined ADC front end.

    Implements the SENSE/REFT/REFB strapping resolved in the datasheet phase
    (datasheets/AD9235BRUZ-20_SUMMARY.md, "SENSE/REFT/REFB strapping" section):
      - SENSE tied directly to AGND -> internal reference, VREF = 1.0 V ->
        2.000 V p-p full-scale differential input span (the only strap that reaches
        the required 2 V p-p span).
      - VREF/REFT/REFB are internally-generated analog nodes: bypass only, never
        driven or loaded by anything else (loading them unbalances the reference
        ladder and degrades linearity).
      - VIN- (pin 10) is DC-biased at 1.500 V. The datasheet handoff calls for a
        *dedicated* divider off REF3025 -- but this block's signature only carries
        V3V3_A (no REF2V5 net is passed in), and the work order allocates exactly
        2 spare resistors (R132/R133 or R232/R233) beyond the 12 data-line dampers.
        Judgement call (recorded in the handoff Decisions table): build the 1.500 V
        VIN- bias LOCALLY from V3V3_A (3.3 V analog rail) with a 1.8k/1.5k divider
        (1.5k/(1.8k+1.5k) * 3.3V = 1.500V exactly), then heavily decouple the node
        with the C_ref budget's 2x1uF + 1x10uF (this node absorbs sampling-instant
        charge kickback just like a real signal input).
      - MODE tied to AGND (offset binary output coding, DCS disabled -- default).
      - PDWN is driven externally by the FPGA (active-high power-down) -- passed
        in as a net parameter, not tied here.
      - OEB does not exist on this TSSOP-28 pinout (confirmed against the
        datasheet-phase pin table) -- the net_plan's "OEB -> GND" tie-off is stale
        and is intentionally NOT implemented; there is no such pin to tie.

    Args:
        adc_in: Analog signal input (ADC_<X>_IN) -- drives VIN+, already series-damped
            and charge-kickback-filtered by R_s/C_s in the upstream afe_channel block.
        adc_vinn: 1.500 V DC bias net (ADC_<X>_VINN) -- driven by this block's local
            divider (R132/R133 or R232/R233) and connected to VIN-.
        adc_clk: Sample clock input (CLK_ADC_<X>) -- from the dedicated external XO ->
            74LVC1G34 buffer chain in clock_gen. NEVER sourced from FPGA fabric.
        pdwn: Power-down control (ADC<X>_PDWN), active HIGH, driven by the FPGA.
        v3v3_a: 3.3 V analog supply (AVDD).
        v3v3_d: 3.3 V digital supply, isolated to DRVDD via ferrite bead FB10/FB20.
        gnd: Ground reference (AGND/DGND, both tied to the same board GND net).
        data: 12-bit SKiDL Bus, ADC<X>_D[11:0], series-damped by 100 ohm resistors.
        otr: Out-of-range flag output (ADC<X>_OTR), direct connection (not damped --
            the sourced BOM's R_damp x12 covers only the 12 data bits).
        ch: Instance suffix, 'A' or 'B'. Selects ref designators and internal net names.
    """
    suffix = ch.upper()
    if suffix == 'A':
        u_ref, fb_ref = 'U110', 'FB10'
        r_base, c_base = 120, 120
    else:
        u_ref, fb_ref = 'U210', 'FB20'
        r_base, c_base = 220, 220

    def r_ref(n):
        return f'R{r_base + n}'

    def c_ref(n):
        return f'C{c_base + n}'

    # --- U_adc: AD9235BRUZ-20, 12-bit 20 MSPS pipelined ADC (project-local symbol) ---
    u_adc = Part(
        'lib/dual_adc_usb.kicad_sym',
        'AD9235BRUZ-20',
        ref=u_ref,
        value='AD9235BRUZ-20',
        footprint='Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm',
        tool=KICAD9,
    )

    # --- Analog input path ---
    # VIN+ driven directly by the upstream AFE chain's final stage (already series
    # damped/charge-kickback filtered by R_s/C_s in afe_channel, per net_plan.md).
    u_adc['VIN+'] += adc_in

    # VIN- DC bias node -- see docstring. Built locally from V3V3_A since REF3025's
    # 2.5V output is not passed into this block's signature.
    u_adc['VIN-'] += adc_vinn

    # 1.500 V bias divider: V3V3_A --R_top(1.8k)--> adc_vinn --R_bot(1.5k)--> GND
    # 3.3V * 1500/(1800+1500) = 1.500V exactly.
    r_vinn_top = Part('Device', 'R', ref=r_ref(12), value='1.8k',
                       footprint='Resistor_SMD:R_0402_1005Metric')
    r_vinn_top[1] += v3v3_a
    r_vinn_top[2] += adc_vinn

    r_vinn_bot = Part('Device', 'R', ref=r_ref(13), value='1.5k',
                       footprint='Resistor_SMD:R_0402_1005Metric')
    r_vinn_bot[1] += adc_vinn
    r_vinn_bot[2] += gnd

    # Heavy decoupling on the VIN- bias node (part of the C_ref budget: the
    # remaining 2x1uF + 1x10uF after VREF/REFT/REFB each take a 100nF, per the
    # datasheet summary's C_ref allocation).
    c_vinn_1 = Part('Device', 'C', ref=c_ref(10), value='1uF',
                     footprint='Capacitor_SMD:C_0603_1608Metric')
    c_vinn_1[1] += adc_vinn
    c_vinn_1[2] += gnd

    c_vinn_2 = Part('Device', 'C', ref=c_ref(11), value='1uF',
                     footprint='Capacitor_SMD:C_0603_1608Metric')
    c_vinn_2[1] += adc_vinn
    c_vinn_2[2] += gnd

    c_vinn_bulk = Part('Device', 'C', ref=c_ref(12), value='10uF',
                        footprint='Capacitor_SMD:C_0805_2012Metric')
    c_vinn_bulk[1] += adc_vinn
    c_vinn_bulk[2] += gnd

    # --- Reference strapping: SENSE -> AGND for 2.000 Vpp full-scale span ---
    u_adc['SENSE'] += gnd

    # VREF/REFT/REFB: internally-generated, bypass only -- never drive or load.
    c_vref = Part('Device', 'C', ref=c_ref(7), value='100nF',
                   footprint='Capacitor_SMD:C_0402_1005Metric')
    c_vref[1] += u_adc['VREF']
    c_vref[2] += gnd

    c_reft = Part('Device', 'C', ref=c_ref(8), value='100nF',
                   footprint='Capacitor_SMD:C_0402_1005Metric')
    c_reft[1] += u_adc['REFT']
    c_reft[2] += gnd

    c_refb = Part('Device', 'C', ref=c_ref(9), value='100nF',
                   footprint='Capacitor_SMD:C_0402_1005Metric')
    c_refb[1] += u_adc['REFB']
    c_refb[2] += gnd

    # --- MODE: tie AGND -> offset binary output coding, DCS disabled (default) ---
    u_adc['MODE'] += gnd

    # --- PDWN: driven externally by the FPGA (active-high power-down) ---
    u_adc['PDWN'] += pdwn

    # --- Sample clock: from the dedicated external XO/74LVC1G34 buffer chain only ---
    u_adc['CLK'] += adc_clk

    # --- AVDD (analog 3.0V supply, both pins) + AGND (both pins) ---
    # NOTE (assembler fix, see handoffs/05_coding.md): `u_adc['AVDD', 1]` does NOT mean
    # "pin named AVDD, instance 1" -- SKiDL's Part.get_pins() treats each element of a
    # bracketed tuple as an INDEPENDENT OR'd search term (name-or-number), so the
    # original `u_adc['AVDD', 1] += v3v3_a` / `u_adc['AGND', 1] += gnd` calls also
    # matched pin NUMBER "1" (= OTR) and pin NUMBER "2" (= MODE) on this part, shorting
    # OTR and MODE directly onto V3V3_A and GND (dead-shorting V3V3_A to GND through
    # U110/U210's OTR pin once both channels were wired to the FPGA). Indexing by name
    # alone already returns BOTH same-named pins as a NetPinList (verified live), which
    # is the correct/intended behavior and is what every other block in this project
    # uses (see sram_buffer.py's `u8['VDD'] +=`, usb_bridge.py's `u6['VCCIO'] +=`).
    u_adc['AVDD'] += v3v3_a  # pins 7 and 12, both at once
    u_adc['AGND'] += gnd     # pins 8 and 11, both at once

    # AVDD decoupling: 4x100nF (redundant local bypass across the shared AVDD net)
    # + 1x10uF bulk, per sourced BOM C_avdd allocation.
    for i in range(1, 5):
        c_avdd = Part('Device', 'C', ref=c_ref(i - 1), value='100nF',
                       footprint='Capacitor_SMD:C_0402_1005Metric')
        c_avdd[1] += v3v3_a
        c_avdd[2] += gnd

    c_avdd_bulk = Part('Device', 'C', ref=c_ref(4), value='10uF',
                        footprint='Capacitor_SMD:C_0805_2012Metric')
    c_avdd_bulk[1] += v3v3_a
    c_avdd_bulk[2] += gnd

    # --- DRVDD (digital output driver supply), isolated from V3V3_D by FB10/FB20 ---
    # FB_drv keeps switching-noise from the digital output drivers off the shared
    # digital rail; DRVDD's own local decoupling sits on the ADC side of the bead.
    drvdd_local = Net(f'DRVDD_{suffix}')
    fb_drv = Part('Device', 'FerriteBead', ref=fb_ref, value='BLM18PG601SN1D',
                   footprint='Inductor_SMD:L_0603_1608Metric')
    fb_drv[1] += v3v3_d
    fb_drv[2] += drvdd_local

    u_adc['DRVDD'] += drvdd_local
    u_adc['DGND'] += gnd

    c_drvdd_100n = Part('Device', 'C', ref=c_ref(5), value='100nF',
                         footprint='Capacitor_SMD:C_0402_1005Metric')
    c_drvdd_100n[1] += drvdd_local
    c_drvdd_100n[2] += gnd

    c_drvdd_1u = Part('Device', 'C', ref=c_ref(6), value='1uF',
                       footprint='Capacitor_SMD:C_0603_1608Metric')
    c_drvdd_1u[1] += drvdd_local
    c_drvdd_1u[2] += gnd

    # --- Data bus D0-D11: series-damped (100 ohm each) to the FPGA-side bus ---
    for bit in range(12):
        r_damp = Part('Device', 'R', ref=r_ref(bit), value='100',
                       footprint='Resistor_SMD:R_0402_1005Metric')
        r_damp[1] += u_adc[f'D{bit}']
        r_damp[2] += data[bit]

    # --- OTR: out-of-range flag, direct connection (not damped) ---
    u_adc['OTR'] += otr
