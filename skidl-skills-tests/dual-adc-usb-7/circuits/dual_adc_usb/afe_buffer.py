"""AFE Buffer — dual JFET-input unity-gain buffer (AD8066) for both channels.
Block from: architecture/block_diagram.md (block 2, "JFET buffer")
Interface nets: CHA_ATT, CHB_ATT -> CHA_BUF, CHB_BUF; VA_POS, VA_NEG, GND

One AD8066 holds both channels, so this block is instantiated ONCE (unlike afe_input
and afe_driver, which are per-channel).
"""
from skidl import *


@SubCircuit
def afe_buffer(cha_att, chb_att, cha_buf, chb_buf, va_pos, va_neg, gnd):
    """Unity-gain (follower) buffer that turns the 82.6 kOhm divider tap into a
    low-impedance source for the FDA stage.

    Both halves of one AD8066 are wired as followers: output shorted straight back to
    the inverting input, no feedback resistor (net_plan.md, CH*_BUF: "unity-gain
    feedback is a direct short"). A resistor there would form a pole against the JFET
    input capacitance and buy nothing at G=1.

    The part choice is load-bearing and single-sourced [CRIT]: 6 pA input bias current
    is what lets the divider keep a 1 MOhm / 82.6 kOhm source impedance without the
    bias current showing up as offset, and 145 MHz GBW keeps the follower flat well past
    the 4.23 MHz anti-alias corner downstream (datasheets/AD8066ARZ-R7_SUMMARY.md).

    PINOUT WARNING (04_datasheets.md decision 3): JLC/EasyEDA's pinout for this exact
    LCSC# returns only 5 of 8 pins and is missing the entire second channel.  The
    symbol used here, `dual_adc_usb:AD8066ARZ-R7` from symbols/dual_adc_usb.kicad_sym,
    was generated from ADI's own datasheet pin diagram:
        1 VOUT1  2 -IN1  3 +IN1  4 -VS  5 +IN2  6 -IN2  7 VOUT2  8 +VS
    Do not re-derive it from a stock library or an online source.

    Supplies are +/-5 V (VA_POS / VA_NEG), i.e. the dual-supply mode of the part.  At
    the +/-55 V input overload limit the divider tap reaches +/-5.0 V, which is inside
    the AD8066's absolute maximum but outside its linear common-mode range: the buffer
    saturates and recovers.  That is intentional survival behaviour per SPEC I3 /
    design_risks R-10, not an accuracy claim.

    Args:
        cha_att: IN  (sensed) - channel A divider tap from `afe_input` (CHA_ATT).
        chb_att: IN  (sensed) - channel B divider tap from `afe_input` (CHB_ATT).
        cha_buf: OUT (driven)  - buffered channel A, feeds `afe_driver` ch='A'.
        chb_buf: OUT (driven)  - buffered channel B, feeds `afe_driver` ch='B'.
        va_pos:  IN  (sensed) - +5 V analog rail.  Needs .drive = POWER at top level.
        va_neg:  IN  (sensed) - -4.74 V analog rail.  Needs .drive = POWER at top level.
        gnd:     IN  (sensed) - ground.  Needs .drive = POWER at top level.

    Rail bypassing for this block is three caps per rail:
        VA_POS: C15 (100 nF HF, at pin 8) + C11 (1 uF) + C12 (10 uF)
        VA_NEG: C16 (100 nF HF, at pin 4) + C13 (1 uF) + C14 (10 uF)
    C15/C16 were added by sourcing rev.3 (sourced_bom.csv row 67) after this block's
    rev.1 reported that U1 had no HF bypass at all; net_plan.md rev.3 mandates them
    ("U1 (AD8066): C15 = 100 nF on VA_POS, C16 = 100 nF on VA_NEG, at the pins").
    Each goes from ITS OWN supply pin to GND -- one per rail, NOT a single cap bridging
    VA_POS to VA_NEG.  On a bipolar-supply op amp the HF return current of each output
    half flows back through the rail that is sourcing or sinking it, so each rail needs
    its own low-inductance path to the ground plane; a rail-to-rail cap shorts the two
    rails together at HF but leaves neither referenced to the ground the load returns to.
    """
    # ---- U1 — AD8066 dual JFET op-amp ----------------------------------------------
    VOUT1, INN1, INP1, VSN, INP2, INN2, VOUT2, VSP = 1, 2, 3, 4, 5, 6, 7, 8
    u1 = Part('dual_adc_usb', 'AD8066ARZ-R7', ref='U1', value='AD8066ARZ-R7',
              footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')

    # Supplies (both pins are power_in on the generated symbol).
    va_pos += u1[VSP]
    va_neg += u1[VSN]

    # ---- Followers: output tied directly to -IN, +IN on the attenuator tap ----------
    cha_att += u1[INP1]
    cha_buf += u1[VOUT1], u1[INN1]      # net_plan.md: CHA_BUF = U1 OUT A + U1 -IN A
    chb_att += u1[INP2]
    chb_buf += u1[VOUT2], u1[INN2]      # net_plan.md: CHB_BUF = U1 OUT B + U1 -IN B

    # ---- Rail bypassing (values/footprints verbatim from sourced_bom.csv) -----------
    c11 = Part('Device', 'C', ref='C11', value='1uF',
               footprint='Capacitor_SMD:C_0402_1005Metric')      # VA_POS local
    c12 = Part('Device', 'C', ref='C12', value='10uF',
               footprint='Capacitor_SMD:C_0805_2012Metric')      # VA_POS bulk
    c13 = Part('Device', 'C', ref='C13', value='1uF',
               footprint='Capacitor_SMD:C_0402_1005Metric')      # VA_NEG local
    c14 = Part('Device', 'C', ref='C14', value='10uF',
               footprint='Capacitor_SMD:C_0805_2012Metric')      # VA_NEG bulk

    # C15/C16 -- 100 nF HF bypass, one per supply pin, added at sourcing rev.3.
    # C15 sits at U1 pin 8 (+VS) and C16 at U1 pin 4 (-VS), each returning to GND.
    # Not a single VA_POS-to-VA_NEG cap: see the docstring.
    c15 = Part('Device', 'C', ref='C15', value='100nF',
               footprint='Capacitor_SMD:C_0402_1005Metric')      # +VS (pin 8) HF
    c16 = Part('Device', 'C', ref='C16', value='100nF',
               footprint='Capacitor_SMD:C_0402_1005Metric')      # -VS (pin 4) HF

    va_pos += c15[1], c11[1], c12[1]    # HF first, then 1 uF, then 10 uF bulk
    va_neg += c16[1], c13[1], c14[1]    # negative rail: caps still return to GND
    c11[2] += gnd
    c12[2] += gnd
    c13[2] += gnd
    c14[2] += gnd
    c15[2] += gnd
    c16[2] += gnd
