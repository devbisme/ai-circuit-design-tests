"""AFE Input — BNC jack, 1 MOhm compensated 1:11 divider, and +/-55 V clamp.
Block from: architecture/block_diagram.md (block 1, "BNC + compensated divider")
Interface nets: CH<ch>_ATT (v_att), VA_POS, VA_NEG, GND
               (ch="A": CHA_ATT via J1/R101/R102/C101/C102/C103/D101;
                ch="B": CHB_ATT via J2/R201/R202/C201/C202/C203/D201)

Instantiated twice, once per analog channel.  The `ch` argument selects the 1xx (A) or
2xx (B) reference-designator block so refs stay unique across the two instances.

NOTE ON THE PARAMETER NAME `ch`:  the work order specified this parameter as `tag`, but
SKiDL's @SubCircuit decorator *consumes* a `tag=` keyword for its own hierarchy naming
(skidl/node.py Node.__call__ pops "tag" out of kwargs before calling the wrapped
function), so a parameter named `tag` can never be filled by a keyword call.  Renamed to
`ch`, exactly as the `afe_driver` block had to do; see handoffs/05_blocks/afe_input.md.
"""
from skidl import *


@SubCircuit
def afe_input(v_att, va_pos, va_neg, gnd, ch):
    """Scope-probe-compatible input: 1 MOhm || ~17.6 pF, 1:11.0091 compensated divider.

    The BNC centre pin drives a 910 k / 90.9 k resistive divider (SPEC I2: the two
    resistors sum to 1.0009 MOhm, i.e. the 1 MOhm a 1x/10x passive probe expects).  The
    divider is frequency-compensated so the attenuation is flat instead of rolling off
    against the node capacitance: C101 (15 pF) sits *across the top resistor* R101, and
    C102 + C103 (130 pF + 15 pF) sit from the tap to GND.  With the ~5 pF node stray the
    architecture budgets, the bottom leg is 150 pF and the balance condition holds:
        R_top * C_top = 910k * 15p = 13.65 us  ~=  R_bot * C_bot = 90.9k * 150p = 13.64 us
    Those caps are C0G 2 % (1 % for C102) and are load-bearing, NOT decoupling - a
    looser or differently-placed cap makes the attenuator peak or droop (design_risks
    R-5).  The series/shunt cap pair also sets the input capacitance seen at the BNC:
    15p in series with 150p = 13.6 pF, ~17.6 pF including strays (SPEC I2).

    Survivability (SPEC I3, design_risks R-10): at +/-55 V continuous at the BNC the tap
    reaches +/-5.0 V from the divider alone; beyond that D101/D201 (BAV199, low-leakage
    double diode) conduct into the +/-5 V analog rails and hold the node one diode drop
    outside them.  The 910 kOhm top resistor limits the clamp current to ~55 uA, far
    inside the BAV199's 215 mA rating.  The BAV199's 5 nA reverse leakage is why this
    part and not an ordinary switching diode: leakage here appears directly as input
    offset across the 82.6 kOhm source impedance.

    Args:
        v_att:  OUT (driven, high-Z) - the divider tap, CHA_ATT / CHB_ATT.  Goes to the
                AD8066 +IN of `afe_buffer`.  82.6 kOhm source impedance; guard this node.
        va_pos: IN  (sensed) - +5 V analog rail, the clamp's positive reference.
                Needs .drive = POWER at top level.
        va_neg: IN  (sensed) - -4.74 V analog rail, the clamp's negative reference.
                Needs .drive = POWER at top level.
        gnd:    IN  (sensed) - ground; BNC shell and the divider's bottom leg.
                Needs .drive = POWER at top level.
        ch:     "A" or "B" - selects the refdes block (1xx / 2xx) and the internal
                CH*_IN net name.

    The BNC-side net CH*_IN is internal to this block: J1/J2 live here, and the only
    signal leaving is the attenuated tap.
    """
    ch = str(ch).upper()
    if ch not in ('A', 'B'):
        raise ValueError("afe_input: ch must be 'A' or 'B', got %r" % (ch,))

    # Refdes block: channel A -> 1xx (J1), channel B -> 2xx (J2).
    n = {'A': 100, 'B': 200}[ch]
    j_ref = {'A': 'J1', 'B': 'J2'}[ch]

    # ---- Templates (values/footprints verbatim from sourcing/sourced_bom.csv) --------
    c_0603 = Part('Device', 'C', dest=TEMPLATE,
                  footprint='Capacitor_SMD:C_0603_1608Metric')

    # ---- J1/J2 — 50 ohm right-angle BNC jack (net_plan.md CH*_IN) -------------------
    # Connector:Conn_Coaxial pins: 1 = In (centre contact), 2 = Ext (shell/shield).
    jack = Part('Connector', 'Conn_Coaxial', ref=j_ref, value='KH-BNC50-3511',
                footprint='Connector_Coaxial:BNC_Amphenol_031-6575_Horizontal')

    ch_in = Net('CH{}_IN'.format(ch))   # +/-10 V signal, +/-55 V survivable; block-local
    ch_in += jack[1]
    jack[2] += gnd

    # ---- Compensated divider (net_plan.md CH*_IN / CH*_ATT) -------------------------
    # R101/R201 = 910k substituted for the architect's 909k (sourcing decision: 909k
    # 0.1 % had <100 pcs stock); ratio becomes 11.0091 instead of 11.000, inside the
    # 1 % fallback band the architect allowed.
    r_top = Part('Device', 'R', ref='R{}'.format(n + 1), value='910k',
                 footprint='Resistor_SMD:R_0805_2012Metric')     # R101 / R201
    r_bot = Part('Device', 'R', ref='R{}'.format(n + 2), value='90.9k',
                 footprint='Resistor_SMD:R_0603_1608Metric')     # R102 / R202

    # C101/C201 is the TOP compensation cap: it goes ACROSS R101, from the BNC node to
    # the tap - not to ground.  C102/C202 + C103/C203 are the bottom leg, tap to ground.
    c_top = c_0603(ref='C{}'.format(n + 1), value='15pF')        # C101 / C201
    c_bot1 = c_0603(ref='C{}'.format(n + 2), value='130pF')      # C102 / C202
    c_bot2 = c_0603(ref='C{}'.format(n + 3), value='15pF')       # C103 / C203

    ch_in += r_top[1], c_top[1]
    v_att += r_top[2], c_top[2], r_bot[1], c_bot1[1], c_bot2[1]
    r_bot[2] += gnd
    c_bot1[2] += gnd
    c_bot2[2] += gnd

    # ---- D101/D201 — BAV199 overvoltage clamp to the analog rails -------------------
    # Symbol note (BOM drift, reported in the handoff): sourcing assigned `Diode:BAV19`,
    # which is a TWO-pin DO-35 *single* diode - it cannot be placed on the sourced
    # 3-pad SOT-23 footprint and cannot make a two-rail clamp.  `Diode:BAV99` is the
    # correct KiCad symbol for this SOT-23 series-connected double-diode pinout, which
    # is the family BAV199 belongs to (datasheets/BAV199_SUMMARY.md).
    #
    # Orientation is stated explicitly, never left to a `&` chain: the BAV99 symbol's
    # pin *names* are unreliable ("K", "A", "K"), so polarity is taken from the symbol
    # geometry, which is unambiguous - pin 1 is the anode of D1, pin 3 is the common
    # node (K1 / A2), pin 2 is the cathode of D2, i.e. conduction runs 1 -> 3 -> 2.
    # Wiring COM to the signal tap, pin 1 to VA_NEG and pin 2 to VA_POS therefore gives
    # a clamp of roughly (VA_NEG - Vf) .. (VA_POS + Vf) at the tap.
    clamp = Part('Diode', 'BAV99', ref='D{}'.format(n + 1), value='BAV199',
                 footprint='Package_TO_SOT_SMD:SOT-23')          # D101 / D201
    v_att += clamp[3]       # common node (K1/A2) on the attenuator tap
    clamp[1] += va_neg      # anode of D1 -> negative rail (clamps the node from below)
    clamp[2] += va_pos      # cathode of D2 -> positive rail (clamps the node from above)
