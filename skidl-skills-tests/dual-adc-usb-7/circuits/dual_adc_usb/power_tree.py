"""Power Tree — VBUS load switch + 2 bucks + 2 LDOs + inverting charge pump + slew-limited 1.8 V.
Block from: architecture/block_diagram.md (block "power")
Interface nets: VBUS, VBUS_SW, P3V3D, P1V8, P1V2, P3V3A, VA_POS, VA_NEG, PWREN_N, FT_3V3, GND
"""
from skidl import *


@SubCircuit
def power_tree(vbus, vbus_sw, p3v3d, p1v8, p1v2, p3v3a, va_pos, va_neg,
               pwren_n, ft_3v3, gnd):
    """Every rail on the board, from the USB VBUS pin outward.

    SIGNATURE CHANGED vs architecture rev.3: `ft_3v3` was ADDED (between `pwren_n` and
    `gnd`).  It is not cosmetic and it is not optional -- see "R71's pull-up rail" below.
    Call this block BY KEYWORD.

    Topology, in dependency order:

        VBUS ---- U9 (TPS22918 load switch, CT=C71 -> ~2 ms ramp) ---- VBUS_SW
                     ^ ON = LS_EN, inverted from PWREN_N by Q1 + R71
        VBUS_SW -+-- U10 (TLV62569 buck, R72/R73) -- L71 -- P3V3D
                 +-- U11 (TLV62569 buck, R74/R75) -- L72 -- P1V2
                 +-- U12 (RT9013-33 LDO) -------------------- P3V3A
                 +-- FB1 (600R bead) ------------------------ VA_POS
                                                               |
                                              U13 (TPS60403 charge pump) -- VA_NEG_RAW
                                                        -- R76/C80 RC -- VA_NEG
        P3V3D ---- U14 (AP2127K-1.8 LDO) ---- P1V8_PRE ---- U15 (TPS22918) ---- P1V8

    Args:
        vbus:     IN  (sensed) - 5 V from the USB-C receptacle, always on.  Driven by
                  `usb_bridge` (J4).  U9's VIN and the C83 inrush cap hang off it here.
        vbus_sw:  OUT (driven, power_out via U9) - gated 5 V feeding both bucks, the
                  analog LDO and the analog ferrite.  Block-local as far as the rest of
                  the board is concerned; nothing outside power_tree loads it.
        p3v3d:    OUT (driven through L71, PASSIVE) - 3.287 V digital rail.  Needs
                  `.drive = POWER` at top level: its only source here is an inductor pin.
        p1v8:     OUT (driven, power_out via U15) - 1.800 V VCCIO3/PSRAM-bank rail.
                  **This is U15's OUTPUT, not U14's.**  See "The 1.8 V rail" below.
        p1v2:     OUT (driven through L72, PASSIVE) - 1.200 V FPGA core rail.  Needs
                  `.drive = POWER` at top level.
        p3v3a:    OUT (driven, power_out via U12) - low-noise 3.3 V analog rail.
        va_pos:   OUT (driven through FB1, PASSIVE) - +5 V ferrite-filtered analog rail.
                  Needs `.drive = POWER` at top level.
        va_neg:   OUT (driven through R76, PASSIVE) - approx -4.74 V analog rail.  Needs
                  `.drive = POWER` at top level.
        pwren_n:  IN  (sensed) - FT232H ACBUS9 PWREN#, ACTIVE LOW.  Drives Q1's gate.
                  Driven by `usb_bridge`; R65 (its pull-up) lives there, not here.
        ft_3v3:   IN  (sensed) - the FT232H's own 3.3 V LDO output.  Used for exactly one
                  thing here: R71, the U9 EN pull-up.  Driven by `usb_bridge` (U6 pin 39).
        gnd:      IN  (sensed) - ground.  Needs `.drive = POWER` at top level.

    ------------------------------------------------------------------------------------
    R71's pull-up rail -- why the signature had to grow a parameter
    ------------------------------------------------------------------------------------
    `net_plan.md` (§ "USB and power control", net `LS_EN`) and `sourced_bom.csv` both say
    R71 "must return to FT_3V3, never P3V3D".  That is correct and it is not negotiable:

      - P3V3D is DOWNSTREAM of U9.  A pull-up to P3V3D is a bootstrap deadlock: U9 off =>
        no P3V3D => EN never rises => U9 stays off.  The board would never start.
      - VBUS is available in the declared signature and U9's ON pin is 5.5 V tolerant, so
        it would "work" electrically -- but it breaks SPEC P3.  At plug-in, FT_3V3 does
        not exist yet, so PWREN_N is at 0 V and Q1 is OFF; a VBUS pull-up would therefore
        assert EN immediately and U9 would begin its 2 ms ramp BEFORE enumeration, drawing
        the full board current against the 150 mA pre-enumeration ceiling until the
        FT232H wakes up and drives PWREN# high.  Rejected.
      - FT_3V3 is the only correct rail: the EN pull-up and Q1's gate drive then come up
        on the SAME rail, so EN can never be pulled high in a window where Q1 has no gate
        drive to pull it back down.

    FT_3V3 is not reachable from architecture rev.3's declared parameter list, and a
    `Net('FT_3V3')` created locally would be a DIFFERENT net object (SKiDL does not merge
    nets by name -- it renames the duplicate).  So the parameter was added.  The net
    already exists at top level: `usb_bridge` takes it as `ft_3v3` and U6 pin 39 drives it.

    ------------------------------------------------------------------------------------
    Load-switch enable polarity (PWREN_N is ACTIVE LOW; U9's ON is ACTIVE HIGH)
    ------------------------------------------------------------------------------------
    One inverting stage is required, and Q1 (BSS138 NMOS, Vgs(th) 0.8 V min / 1.5 V max)
    is it: gate = PWREN_N, source = GND, drain = LS_EN, with R71 = 100 k pulling LS_EN up
    to FT_3V3.  Reasoning both ways, at both threshold extremes (power_budget.md
    § "Load-switch enable"):

      PRE-ENUMERATION: PWREN# = 3.3 V (high = not yet enumerated).  Vgs = +3.3 V, which is
      1.8 V of overdrive even against the 1.5 V max threshold => Q1 ON, Rds(on) ~3.5 ohm.
      LS_EN = 33 uA x 3.5 ohm = 0.1 mV, far below U9's V_IL of 0.5 V => U9 OFF.  Only the
      FT232H draws (90 mA) plus quiescent (8 mA) = 98 mA <= 150 mA, SPEC P3 met.

      ENUMERATED: PWREN# = 0 V.  Vgs = 0 V, below the 0.8 V MINIMUM threshold => Q1 OFF,
      leakage <= 1 uA.  LS_EN = 3.3 V - (2 uA x 100 k) = 3.1 V, well above U9's V_IH of
      1.0 V (TPS22918DBVR-FULL.pdf p.4, verified) => U9 ON, and the whole board comes up.

    Getting this backwards is not a subtle failure: a non-inverting drive would power the
    board pre-enumeration (SPEC P3 violation) and shut it down after it.

    ------------------------------------------------------------------------------------
    The 1.8 V rail -- U14 -> U15 -> VCCIO3, and the net naming that goes with it
    ------------------------------------------------------------------------------------
    Gowin DS117 Table 3-3 caps the VCCIO ramp at 10 mV/us (a real MAX, and it applies to
    VCCIO3), so the 1.8 V rail must take >= 180 us to reach regulation.  U14's soft-start
    is a FIXED INTERNAL 50 us timer (DS36478 Rev.7-2 p.7) -- 3.6x too fast.  A bigger COUT
    does not fix it (COUT is a stability/transient part, not a ramp control) and an RC on
    U14's Shutdown pin does not fix it (that pin is a binary logic enable, VIH >= 1.5 V /
    VIL <= 0.5 V, with no analog ramp behaviour).  Both were investigated and REJECTED
    with citations in handoffs/04_datasheets.md Decision 16 -- do not reach for either.

    The accepted fix, implemented here: U15, a second TPS22918, between U14's VOUT and
    VCCIO3, with C87 = 220 pF C0G on its CT pin.  TI SLVSDG1x Table 2 (VIN = 1.8 V column)
    measures a 260 us 10-90 % rise time at CT = 220 pF, i.e. 6.9 mV/us -- inside the
    10 mV/us ceiling with ~44 % margin on the 180 us floor.  C87 must stay C0G/NP0: the CT
    ramp is a capacitance-controlled timer and X7R's voltage/temperature drift would walk
    the rise time.

    NET NAMING (this is load-bearing -- it is what keeps `fpga_core` from needing a
    re-code):
      - `p1v8`, the interface net, is **U15's OUTPUT**.  It is what leaves this block and
        lands on U5 pin 12 (VCCIO3) and R53, both already wired in `fpga_core` against a
        parameter of that name.
      - `P1V8_PRE` is U14's output and U15's input, and it is INTERNAL to this block.
        C85 (100 nF) and C86 (4.7 uF) sit on it, which is exactly the >= 1 uF VIN bypass
        TI asks for on U15 (sourcing rev.4 Decision 2 checked this against the datasheet).
      - U15's output-side bypass is C511/C512/C513 in `fpga_core`, also already checked.

    ------------------------------------------------------------------------------------
    U15's ON-pin drive: tied to P1V8_PRE (its own VIN).  DECIDED HERE, flagged as a risk.
    ------------------------------------------------------------------------------------
    Sourcing left this open on purpose (rev.4 Decision 3).  The choice is constrained:

      - A pull-up needs a resistor, and the BOM is FINAL at 169 refdes with no spare R in
        this block (R71 = EN pull-up, R72-R75 = the two feedback dividers, R76 = the
        VA_NEG post-filter).  So the ON pin must be tied directly to an existing rail.
      - P3V3D would assert ON roughly 1 ms BEFORE U15's own VIN exists (U14's EN is itself
        tied to P3V3D, so P1V8_PRE only starts after P3V3D is up).
      - P1V8_PRE asserts ON exactly as VIN appears, never before it.  ON's V_IH is 1.05 V
        max, so 1.8 V drives it with 0.75 V of margin, and the pin is 5.5 V tolerant.

    Chosen: **U15.ON -> P1V8_PRE**.  It is the only option that never commands the switch
    on with a dead input, it keeps VCCIO3 as the last rail up (which is what the MODE0/
    MODE1 straps to GND in `fpga_core` depend on), and on power-down ON falls WITH VIN
    rather than ahead of it, so the switch cannot disconnect VCCIO3 while the FPGA is
    still partly powered.

    RESIDUAL RISK, stated plainly rather than buried: TPS22918's switching-characteristics
    table is explicitly scoped to "the power-up sequence where VIN is already in steady
    state condition before the ON pin is asserted high" (SLVSDG1x section 6.6 preamble).
    Tying ON to VIN is outside that scope, and so is tying it to P3V3D -- no rail on this
    board comes up after P1V8_PRE settles, so with a frozen BOM there is no in-spec
    option.  The physical argument that it still holds: U14's 50 us VIN ramp is 5x faster
    than the 260 us CT-governed gate ramp, so the pass FET cannot be enhanced before VIN
    is settled, and VOUT stays CT-slew-limited thereafter.  That argument is sound but it
    is NOT a datasheet guarantee.  Bench-verify VCCIO3's rise (>= 180 us, monotonic)
    before fab.  If it fails, the cheap fix is an RC on U15's ON pin fed from P3V3D
    (10 k + 100 nF ~ 1 ms) -- 2 new refs, which is why it was not done here.

    QOD (pin 5) is left NC on BOTH U9 and U15.  TI gives three options (external R from
    VOUT, direct tie to VOUT, or floating to disable) and specifies BOTH switches' rise
    times with "QOD = Open".  Since U9's ~2 ms inrush ramp and U15's 260 us VCCIO3 ramp
    are the two numbers this design is betting on, the characterized condition is kept.
    Consequence to accept: VBUS_SW and VCCIO3 are not actively discharged when their
    switch opens; they decay into their own loads.

    ------------------------------------------------------------------------------------
    Buck feedback dividers -- use the sourced values, do NOT recompute
    ------------------------------------------------------------------------------------
    V_FB = 0.600 V is VERIFIED from TI's electrical table (0.588-0.612 V), not a family
    default (handoffs/04_datasheets.md Decision 4).  The sourced dividers were computed
    against it:
      P3V3D: R72 = 180 k (FB->VOUT), R73 = 40.2 k (FB->GND), both E96 1 %.
             Vout = 0.600 x (1 + 180/40.2) = 3.287 V (-0.4 %), divider current 14.9 uA.
      P1V2:  R74 = R75 = 100 k.  Vout = 0.600 x (1 + 100/100) = 1.200 V exactly.
    Both bucks' EN pins tie to VBUS_SW: they are already behind U9, so U9's enable IS the
    sequencing gate and a second one would only add a bootstrap hazard.  TLV62569's
    ~1 ms soft-start gives 3.3 mV/us and 1.2 mV/us, both inside DS117's ramp window.

    ------------------------------------------------------------------------------------
    DECOUPLING AUDIT -- the sourced set is SHORT, reported not silently patched
    ------------------------------------------------------------------------------------
    net_plan.md's policy is "100 nF 0402 X7R at EVERY IC supply pin".  This block has
    7 IC supply pins and the BOM funds 4 of the 100 nF caps they need:
        U9  VIN  (VBUS)      -- NO 100 nF.  C83 (10 uF 0805) only.
        U10 VIN  (VBUS_SW)   -- NO 100 nF.  C72 (10 uF 0805) only.
        U11 VIN  (VBUS_SW)   -- NO 100 nF.  C74 (10 uF 0805) only.
        U12 VIN  (VBUS_SW)   -- C88 (100 nF 0402) at the pin.  ADDED at rev.2 on
                                erc-reviewer MED-2; see the U12 section below.
        U13 IN   (VA_POS)    -- C82 (100 nF) OK, per 04_datasheets Decision 8 / item 5.
        U14 VIN  (P3V3D)     -- C84 OK.
        U15 VIN  (P1V8_PRE)  -- C85 OK (shared with U14's VOUT, adjacent by construction).
    => 3 pins short (U9, U10, U11), and that is now the settled disposition.  The
    erc-reviewer adjudicated rev.1's argument (MED-2): AGREED for U9/U10/U11 -- U9 is a
    load switch on a DC node with no switching currents, and C72/C74 are themselves the
    hot-loop input caps TI specifies for the TLV62569, so the 10 uF dominates and the
    shortfall is at-pin HF impedance rather than a missing bypass.  DISAGREED for U12,
    which is why C88 exists; see the U12 section.  U9/U10/U11 stay bare deliberately --
    do not "complete the set".

    Also deviating from net_plan.md, deliberately: net_plan lists C81 under BOTH `VBUS_SW`
    and `VA_POS` (it cannot be both) and lists C72/C74 nowhere.  Resolved as C81 = the
    VA_POS bulk after FB1 (that rail would otherwise have no bulk at all), C72/C74 = the
    two 10 uF buck input caps on VBUS_SW that net_plan's own decoupling policy calls for
    ("buck inputs: 10 uF").  Every C71-C87 ref is used exactly once either way.
    """
    # =====================================================================================
    # Part templates
    # =====================================================================================
    R0402 = Part('Device', 'R', dest=TEMPLATE,
                 footprint='Resistor_SMD:R_0402_1005Metric')
    C0402 = Part('Device', 'C', dest=TEMPLATE,
                 footprint='Capacitor_SMD:C_0402_1005Metric')
    C0603 = Part('Device', 'C', dest=TEMPLATE,
                 footprint='Capacitor_SMD:C_0603_1608Metric')
    C0805 = Part('Device', 'C', dest=TEMPLATE,
                 footprint='Capacitor_SMD:C_0805_2012Metric')

    # =====================================================================================
    # U9 -- TPS22918 VBUS inrush / soft-start load switch, gated by PWREN_N through Q1
    # =====================================================================================
    u9 = Part('dual_adc_usb', 'TPS22918DBVR', ref='U9', value='TPS22918DBVR',
              footprint='Package_TO_SOT_SMD:SOT-23-6')

    # C83 is the VBUS-side bulk. The always-on section (FT232H + this cap) must stay at
    # or under 10 uF total to meet the USB inrush limit -- this is the whole 10 uF, so
    # nothing else may be added to VBUS. 25 V rated part (CL21A106KAYNNNE).
    c83 = C0805(ref='C83', value='10uF')
    vbus += u9['VIN'], c83[1]
    gnd += u9['GND'], c83[2]

    vbus_sw += u9['VOUT']

    # LS_CT: C71 = 1 nF sets U9's output ramp to ~2 ms. The ~60 uF of bulk sitting behind
    # U9 then inrushes at 60 uF x 5 V / 2 ms = 150 mA, and that happens AFTER enumeration
    # where the budget is 500 mA (power_budget.md § "Inrush and sequencing").
    ls_ct = Net('LS_CT')
    c71 = C0402(ref='C71', value='1nF')
    ls_ct += u9['CT'], c71[1]
    gnd += c71[2]

    # QOD open -- see the docstring. U9's 2 ms rise time is specified with QOD = Open.
    u9['QOD'] += NC

    # ---- Q1: the PWREN_N (active low) -> ON (active high) inverter ----------------------
    q1 = Part('Transistor_FET', 'BSS138', ref='Q1', value='BSS138',
              footprint='Package_TO_SOT_SMD:SOT-23')
    r71 = R0402(ref='R71', value='100k')

    ls_en = Net('LS_EN')
    ls_en += u9['ON'], q1['D'], r71[2]
    r71[1] += ft_3v3            # MUST be FT_3V3 -- never P3V3D (deadlock), never VBUS (P3)
    pwren_n += q1['G']
    gnd += q1['S']

    # =====================================================================================
    # U10 -- TLV62569 buck, VBUS_SW -> P3V3D (3.287 V)
    # =====================================================================================
    u10 = Part('Regulator_Switching', 'TLV62569DBV', ref='U10', value='TLV62569DBVR',
               footprint='Package_TO_SOT_SMD:SOT-23-5')
    l71 = Part('Device', 'L', ref='L71', value='2.2uH',
               footprint='Inductor_SMD:L_Murata_DFE201610P')
    c72 = C0805(ref='C72', value='10uF')    # buck input cap
    c73 = C0805(ref='C73', value='22uF')    # buck output bulk
    r72 = R0402(ref='R72', value='180k')    # FB -> VOUT
    r73 = R0402(ref='R73', value='40.2k')   # FB -> GND

    # EN tied to its own input rail: U10 sits behind U9, so U9's ON pin is the sequencing
    # control for this rail. A second enable here would only add a way to hang.
    vbus_sw += u10['VIN'], u10['EN'], c72[1]
    gnd += u10['GND'], c72[2]

    sw_3v3 = Net('SW_3V3')                  # switch node, block-internal, keep short
    sw_3v3 += u10['SW'], l71[1]

    p3v3d += l71[2], c73[1], r72[1]
    gnd += c73[2]

    fb_3v3 = Net('FB_3V3')                  # 0.600 V x (1 + 180/40.2) = 3.287 V
    fb_3v3 += r72[2], r73[1], u10['FB']
    gnd += r73[2]

    # =====================================================================================
    # U11 -- TLV62569 buck, VBUS_SW -> P1V2 (1.200 V, FPGA core)
    # =====================================================================================
    u11 = Part('Regulator_Switching', 'TLV62569DBV', ref='U11', value='TLV62569DBVR',
               footprint='Package_TO_SOT_SMD:SOT-23-5')
    l72 = Part('Device', 'L', ref='L72', value='2.2uH',
               footprint='Inductor_SMD:L_Murata_DFE201610P')
    c74 = C0805(ref='C74', value='10uF')
    c75 = C0805(ref='C75', value='22uF')
    r74 = R0402(ref='R74', value='100k')    # FB -> VOUT
    r75 = R0402(ref='R75', value='100k')    # FB -> GND (1:1 => exactly 2 x 0.600 V)

    vbus_sw += u11['VIN'], u11['EN'], c74[1]
    gnd += u11['GND'], c74[2]

    sw_1v2 = Net('SW_1V2')
    sw_1v2 += u11['SW'], l72[1]

    p1v2 += l72[2], c75[1], r74[1]
    gnd += c75[2]

    fb_1v2 = Net('FB_1V2')
    fb_1v2 += r74[2], r75[1], u11['FB']
    gnd += r75[2]

    # =====================================================================================
    # U12 -- RT9013-33 LDO, VBUS_SW -> P3V3A (low-noise 3.3 V analog)
    # =====================================================================================
    # An LDO, not a third buck: P3V3A feeds the ADS5231's AVDD and both THS4521s, and a
    # 1.5 MHz switch node on a 12-bit instrument's analog supply is risk R-2. Dissipation
    # (5 - 3.3) V x 67 mA = 114 mW in SOT-23-5 (~250 C/W) = +29 C, fine at 70 C ambient.
    u12 = Part('dual_adc_usb', 'RT9013-33GB', ref='U12', value='RT9013-33GB',
               footprint='Package_TO_SOT_SMD:SOT-23-5')
    c76 = C0402(ref='C76', value='1uF')     # P3V3A local bulk (>= the 1 uF COUT minimum)
    c77 = C0805(ref='C77', value='10uF')    # P3V3A rail bulk
    # C88 -- at-pin VIN cap, added at rev.2 on erc-reviewer MED-2, which REVERSES this
    # block's rev.1 disposition for U12 only (U9/U10/U11 stand as written below). U12 is
    # the analog-rail LDO: its output P3V3A feeds the ADS5231 AVDD and both THS4521 FDAs,
    # and its input node VBUS_SW is shared with two 1.5 MHz switchers (U10/U11). RT9013's
    # PSRR is ~70 dB at 1 kHz but only ~20-30 dB by 1.5 MHz, and 1 LSB = 2 V / 4096 =
    # 488 uV, so switching residue that gets through lands on the analog supply and costs
    # SNR (SPEC F10). C72/C74 are across the node, not at this pin. Already in
    # sourced_bom.csv rev.5 -- the BOM was NOT edited here.
    c88 = C0402(ref='C88', value='100nF')   # U12 VIN at-pin HF bypass

    vbus_sw += u12['VIN'], u12['EN'], c88[1]   # EN high = always on behind U9
    gnd += u12['GND'], c88[2]
    u12['NC'] += NC

    p3v3a += u12['VOUT'], c76[1], c77[1]
    gnd += c76[2], c77[2]

    # =====================================================================================
    # FB1 -- 600 ohm @ 100 MHz ferrite, VBUS_SW -> VA_POS (+5 V analog)
    # =====================================================================================
    # 0603 rather than the skeleton's 0805: no 0805 600-ohm bead in stock met the >= 1 A
    # requirement (accepted deviation, sourcing rev.3).
    fb1 = Part('Device', 'L', ref='FB1', value='600',
               footprint='Inductor_SMD:L_0603_1608Metric')
    c81 = C0805(ref='C81', value='10uF')    # VA_POS bulk, downstream side of the bead

    vbus_sw += fb1[1]
    va_pos += fb1[2], c81[1]
    gnd += c81[2]

    # =====================================================================================
    # U13 -- TPS60403 inverting charge pump, VA_POS (+5 V) -> VA_NEG (approx -4.74 V)
    # =====================================================================================
    # Rout 15 ohm: -5 V + (13.2 mA x 15) = -4.80 V at U13's output, then R76 (4.7 ohm) with
    # C80 forms the post-filter RC that mitigates risk R-2 (250 kHz charge-pump ripple on
    # the AD8066's negative rail), costing a further 62 mV => -4.74 V at VA_NEG. AD8066
    # total supply = 5.0 + 4.74 = 9.74 V, inside its 5-24 V range.
    u13 = Part('Regulator_SwitchedCapacitor', 'TPS60403DBV', ref='U13', value='TPS60403DBVR',
               footprint='Package_TO_SOT_SMD:SOT-23-5')
    c78 = C0603(ref='C78', value='1uF')     # flying cap, X7R 50 V
    c79 = C0805(ref='C79', value='10uF')    # charge-pump output bulk
    c80 = C0805(ref='C80', value='10uF')    # post-RC bulk -> sets the filter corner with R76
    c82 = C0402(ref='C82', value='100nF')   # U13 input bypass CI (04_datasheets Decision 8)
    r76 = R0402(ref='R76', value='4.7')

    va_pos += u13['IN'], c82[1]
    gnd += u13['GND'], c82[2]

    # Flying cap: pins 5 = C_FLY+, 3 = C_FLY-. Indexed by number because the symbol's pin
    # names carry LaTeX-style braces ("C_{FLY+}") that are awkward to quote reliably.
    cp_cap_p = Net('CP_CAP_P')
    cp_cap_n = Net('CP_CAP_N')
    cp_cap_p += u13[5], c78[1]
    cp_cap_n += u13[3], c78[2]

    va_neg_raw = Net('VA_NEG_RAW')          # approx -4.80 V, pre-filter
    va_neg_raw += u13['OUT'], c79[1], r76[1]
    gnd += c79[2]

    va_neg += r76[2], c80[1]
    gnd += c80[2]

    # =====================================================================================
    # U14 -- AP2127K-1.8 LDO, P3V3D -> P1V8_PRE (internal; NOT the p1v8 interface net)
    # =====================================================================================
    # LDO from P3V3D rather than from VBUS_SW or a third buck: 100 mA x 3.3 V / 4.25 V =
    # 77.6 mA of VBUS, vs 100 mA straight from the 5 V rail with twice the heat. Worst-case
    # dissipation (3.287 - 1.800) x 0.100 = 149 mW => Tj ~107 C at 70 C ambient, inside 125 C.
    u14 = Part('Regulator_Linear', 'AP2127K-1.8', ref='U14', value='AP2127K-1.8TRG1',
               footprint='Package_TO_SOT_SMD:SOT-23-5')
    c84 = C0402(ref='C84', value='100nF')   # U14 VIN decoupling, P3V3D side
    c85 = C0402(ref='C85', value='100nF')   # U14 VOUT decoupling == U15 VIN bypass
    c86 = C0603(ref='C86', value='4.7uF')   # U14 VOUT bulk == U15 VIN bulk

    # EN tied to VIN: U14 is already behind U9 and behind U10's own soft-start, so P3V3D's
    # arrival IS this rail's enable. Do NOT put an RC here -- 04_datasheets Decision 16
    # verified that AP2127K's Shutdown pin is a binary logic threshold with no ramp
    # behaviour, so an RC delays the start without changing dV/dt. U15 is the fix.
    p3v3d += u14['VIN'], u14['EN'], c84[1]
    gnd += u14['GND'], c84[2]
    u14['NC'] += NC

    p1v8_pre = Net('P1V8_PRE')              # 1.8 V, 50 us ramp -- too fast for VCCIO3 alone
    p1v8_pre += u14['VOUT'], c85[1], c86[1]
    gnd += c85[2], c86[2]

    # =====================================================================================
    # U15 -- TPS22918 slew-limited load switch, P1V8_PRE -> P1V8 (VCCIO3 / PSRAM bank)
    # =====================================================================================
    # This is the keystone of SPEC F6: p1v8 is what reaches U5 pin 12, and C87 is what
    # makes its ramp legal. See the docstring for the full chain of evidence and for why
    # ON is tied to P1V8_PRE. Load on this switch is VCCIO3 (66 mA peak) plus R53's 180 uA
    # RECONFIG_N pull-up in fpga_core; at 53 mOhm Rds(on) the drop is under 4 mV.
    u15 = Part('dual_adc_usb', 'TPS22918DBVR', ref='U15', value='TPS22918DBVR',
               footprint='Package_TO_SOT_SMD:SOT-23-6')
    c87 = C0402(ref='C87', value='220pF')   # C0G/NP0 ONLY -- X7R would drift the CT timer

    p1v8_pre += u15['VIN'], u15['ON']       # ON tied to its own VIN: see docstring
    gnd += u15['GND']

    ls2_ct = Net('LS2_CT')                  # 220 pF -> 260 us 10-90 % rise (TI Table 2)
    ls2_ct += u15['CT'], c87[1]
    gnd += c87[2]

    u15['QOD'] += NC                        # Open, matching the characterized rise-time condition

    p1v8 += u15['VOUT']                     # -> U5 pin 12 (VCCIO3), R53, C511-C513
