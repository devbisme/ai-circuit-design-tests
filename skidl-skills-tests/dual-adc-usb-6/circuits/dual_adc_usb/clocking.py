"""Clocking — 10.000 MHz low-jitter sample-clock oscillator + isolation buffer
Block from: architecture/block_diagram.md
Interface nets: +3V3D, CLK_ADC, CLK_FPGA, GND
"""
from skidl import *


@SubCircuit
def clocking(vdd, clk_adc, clk_fpga, gnd):
    """The board's single clock source and its two fan-out legs.

    X1 (TAITIEN OXETDLJANF-10.000000, RMS phase jitter <=1 ps, 12 kHz-20 MHz) drives
    CLK_XO. That node splits two ways:

      * R21 (33 ohm) -> CLK_ADC   -- the low-jitter leg, straight to BOTH ADCs.
      * R22 (100 ohm) -> U8 (SN74LVC1G17 Schmitt buffer) -> R23 (33 ohm) -> CLK_FPGA.

    HARD CONSTRAINT (phase 1): CLK_ADC must come from X1 directly. 12-bit SNR at a
    5 MHz input allows only ~6.4 ps RMS aperture+clock jitter, so the ADC clock must
    never originate from, or pass through, an FPGA PLL. U8 exists precisely so that
    the FPGA's input capacitance and any reflections off its pin stay on the far side
    of R22 and cannot load or corrupt the ADC leg. Do not re-route CLK_ADC through U8,
    and do not feed CLK_ADC back from the FPGA.

    SPEC F13 (<=100 ns channel-to-channel skew) is met by both ADCs sharing this one
    CLK_ADC net -- the `adc_channel` block takes it as a single shared parameter.

    Args:
        vdd:      [in]  +3V3D -- 3.3 V digital rail, supplies X1 and U8. Consumed only.
        clk_adc:  [out] CLK_ADC -- 10.000 MHz sample clock to U150.CLK and U250.CLK,
                  driven through R21. Passive series element, so ERC will see no
                  driving pin on this net (see the block handoff).
        clk_fpga: [out] CLK_FPGA -- buffered 10 MHz copy to the FPGA GCLK input,
                  driven through R23. Same ERC note applies.
        gnd:      [in]  GND -- single plane.
    """
    # ---- Part templates (values/footprints verbatim from sourcing/sourced_bom.md) --
    _r0402 = Part('Device', 'R', dest=TEMPLATE,
                  footprint='Resistor_SMD:R_0402_1005Metric')
    _c0603 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0603_1608Metric')
    _c0402 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0402_1005Metric')

    # ---- Internal nets (net_plan.md "clocking nets") -----------------------------
    clk_xo  = Net('CLK_XO')       # X1 output, the one low-jitter source node
    clk_buf = Net('CLK_BUF_IN')   # R22 -> U8 input
    clk_out = Net('CLK_BUF_OUT')  # U8 output -> R23

    # =============================================================================
    # 1. X1 -- 10.000 MHz XO, SMD3225-4P
    #    Pins: 1 = OE (tri-state, high or floating = enabled), 2 = GND,
    #          3 = OUT, 4 = VDD.
    #    OE is tied HIGH explicitly rather than left floating -- a floating enable on
    #    the board's only clock source is not worth the one net it saves.
    # =============================================================================
    X = Part('dual_adc_usb', 'OXETDLJANF-10.000000', ref='X1',
             value='OXETDLJANF-10.000000',
             footprint='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm')

    vdd += X['VDD'], X['OE']
    gnd += X['GND']
    clk_xo += X['OUT']

    # =============================================================================
    # 2. Fan-out
    #    R21 is the ADC leg. Keep it short and keep it the quiet one.
    #    R22 is deliberately the larger value (100 ohm) -- it is the isolation
    #    element that stops the FPGA branch from reflecting back into CLK_XO.
    # =============================================================================
    R21 = _r0402(ref='R21', value='33R')      # [calc] X1 -> CLK_ADC
    R22 = _r0402(ref='R22', value='100R')     # X1 -> U8, edge control / isolation
    R23 = _r0402(ref='R23', value='33R')      # [calc] U8 -> CLK_FPGA

    clk_xo += R21[1], R22[1]
    clk_adc += R21[2]
    clk_buf += R22[2]

    # =============================================================================
    # 3. U8 -- SN74LVC1G17 single Schmitt-trigger buffer, SOT-23-5
    #    The KiCad symbol 74xGxx:74LVC1G17 names the signal pins '~', so every pin is
    #    addressed BY NUMBER. This matches TI's DBV pinout for the 1G17:
    #      1 = NC   2 = A (in)   3 = GND   4 = Y (out)   5 = VCC
    #    Pin 1 is a true NC on this package and is left unconnected.
    # =============================================================================
    U8 = Part('74xGxx', '74LVC1G17', ref='U8', value='SN74LVC1G17DBVR',
              footprint='Package_TO_SOT_SMD:SOT-23-5')

    clk_buf += U8[2]          # A
    clk_out += U8[4]          # Y
    vdd += U8[5]              # VCC
    gnd += U8[3]              # GND

    clk_out += R23[1]
    clk_fpga += R23[2]

    # =============================================================================
    # 4. Local supply decoupling -- one cap per device, at its own supply pin.
    #    C30/C31 are 100 nF X7R 0402 (CL05B104KB54PNC) per sourced_bom.md rev.5.
    #    These replace the earlier 1 uF 0603 rows: X1 is the 10 MHz sample clock and
    #    the whole 12-bit SNR budget rests on its <=1 ps RMS jitter, so supply noise
    #    converts directly into jitter. HF impedance at the pin matters more here than
    #    bulk, and a 0402 sits closer. Note 100 nF C0G does not exist in 0402 anywhere
    #    in the JLC catalogue (max 0402 C0G is 470 pF), so X7R is the best available.
    # =============================================================================
    C30 = _c0402(ref='C30', value='100nF')    # X1 VDD decoupling
    C31 = _c0402(ref='C31', value='100nF')    # U8 VCC decoupling

    for c in (C30, C31):
        vdd += c[1]
        gnd += c[2]
