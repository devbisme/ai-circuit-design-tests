"""Clock 40 MHz — dedicated ADC sample-clock XO with its own filtered rail, plus a
high-Z tap for the FPGA's global clock input.
Block from: architecture/block_diagram.md
Interface nets: vbus_a5v, gnd, enc_clk40, xo_clk_fpga
"""
from skidl import *

@subcircuit
def clock_40m(vbus_a5v, gnd, enc_clk40, xo_clk_fpga):
    """40 MHz LVCMOS sample clock for the dual-ADC front end.

    ==========================================================================
    THIS BLOCK IS WHAT THE ENTIRE 12-BIT CLAIM RESTS ON. Read before touching.
    (SPEC.md §2.2, architecture/design_risks.md §R3-UPDATE)
    ==========================================================================

    Architecture (net_plan.md §3.7, §2 signature):
      - U9 (40 MHz XO) is on its OWN LDO (U8), fed from vbus_a5v, filtered by
        its own ferrite (L7) + bulk/decoupling caps (C81/C82/C83). This rail
        is NOT shared with any digital 3.3 V rail in the system.
      - U9.OUT drives the ADC ENCODE input DIRECTLY through a 33R series
        termination (R40) on net `enc_clk40`. Per net_plan.md §3.7 this is
        explicitly a SINGLE LOAD with the SHORTEST POSSIBLE TRACE to
        U7.ENC+. *** LAYOUT REQUIREMENT — DO NOT LOSE THIS: place U9/R40
        as close as physically possible to the ADC ENC pin; route this
        trace before anything else on the board; no other net may share
        U9's filtered supply or ground return. ***
      - A SECOND, separate 100R series resistor (R41) taps U9.OUT to drive
        the FPGA's global clock input on net `xo_clk_fpga`. R41 is a
        HIGH-IMPEDANCE TAP by design: its job is to keep the FPGA branch
        from loading down / reflecting into the clean `enc_clk40` net.
        The two resistors fan out from the same XO pin independently —
        neither branch is allowed to load the other.
      - THE FPGA ONLY CONSUMES THIS CLOCK. IT NEVER SYNTHESISES IT.
        Explicitly REJECTED alternatives (SPEC.md §2.2):
          * An iCE40-internal PLL-derived sample clock — jitter an order
            of magnitude too high for a 12-bit claim.
          * An Si5351-class programmable clock generator — hundreds of ps
            of jitter, likewise disqualifying.
        The FPGA's `xo_clk_fpga` input must land on a GBIN (global clock
        input) pin in fpga_ice40 — it is used only as a synchronous
        system/logic clock there, never re-multiplied into the ADC path.

    Footprint choice (deliberate, load-bearing):
      U9 uses the STANDARD industry 3225 4-pad XO footprint
      (Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm — 3.2 x 2.5 mm, pin map
      1=OE/tri-state, 2=GND, 3=OUT, 4=VDD, per the OT322540MJBA4SL
      datasheet). This footprint is universal across essentially every
      3225-package 40 MHz XO on the market, so if bring-up shows the
      populated part's jitter is unacceptable (see block below), a
      jitter-specified 3225 part is a DROP-IN SWAP — no board change.

    ==========================================================================
    JITTER STATUS — UNVERIFIED. READ BEFORE BRING-UP AND BEFORE RE-SOURCING.
    ==========================================================================
    The populated XO (YXC OT322540MJBA4SL, LCSC C2831396) has NO PUBLISHED
    PHASE-JITTER SPEC. The manufacturer publishes none — sourcing searched
    all 94 in-stock-qty-5 candidates in the JLCPCB library and found zero
    with a published jitter figure (design_risks.md §R3-UPDATE).

    Expected 1-3 ps RMS (INFERENCE, NOT A DATASHEET FACT): 40 MHz here is
    fundamental-mode with no PLL multiplication, and generic parts in this
    class are typically 1-3 ps; MEMS oscillators are often worse.

    Practical threshold: ~5 ps RMS integrated phase jitter.
    SPEC's headline aperture-jitter budget is 10.6 ps RMS (SPEC.md §2.2,
    for -74 dB SNR at 3 MHz full scale) — but that 10.6 ps figure is NOT
    the operative number for this design. At 10 ps RMS jitter, jitter-
    limited SNR = 74.5 dB, i.e. ~0.7 ENOB is lost off the 12-bit budget.

    ACTION (do not close design_risks.md R3 until done): MEASURE THE
    INTEGRATED RMS PHASE JITTER AT BRING-UP. If it measures > 5 ps RMS,
    swap U9 for a jitter-specified 3225-footprint part — drop-in, no
    board change (see footprint note above).

    Refs: sourcing/sourced_bom.md §0.1, architecture/design_risks.md
    §R3-UPDATE.
    ==========================================================================

    Args:
        vbus_a5v: Filtered analog 5 V USB bus rail (post-ferrite branch,
            per net_plan.md §2 power table). Feeds U8's own dedicated LDO.
        enc_clk40: Clean 40 MHz clock to the ADC ENCODE input (adc_dual
            block). Single load, shortest trace — see layout note above.
        xo_clk_fpga: 40 MHz clock tap to the FPGA GBIN pin (fpga_ice40
            block). High-impedance tap; FPGA consumes only, never
            re-synthesises.
        gnd: Ground reference.
    """

    # ------------------------------------------------------------------
    # U8 — dedicated LDO for the XO, off vbus_a5v (net_plan.md §3.7).
    # This is the XO's OWN regulator: never shared with any other rail,
    # so switching noise / digital rail noise cannot couple onto the
    # sample clock's supply.
    # ------------------------------------------------------------------
    u8 = Part(
        "Regulator_Linear", "LP5907MFX-3.3",
        ref="U8", value="LP5907MFX-3.3/NOPB",
        footprint="Package_TO_SOT_SMD:SOT-23-5",
    )

    # Internal net: LDO output, pre-ferrite (matches net_plan.md's
    # internal net name `vXo3V3`).
    vXo3V3 = Net("vXo3V3")

    # C80: LDO input cap on vbus_a5v, at U8.IN (per net_plan.md §3.7 and
    # the LP5907 datasheet's 1 uF input-cap recommendation).
    c80 = Part(
        "Device", "C", ref="C80", value="1uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    c80[1] += vbus_a5v
    c80[2] += gnd

    u8["IN"] += vbus_a5v
    u8["GND"] += gnd
    # EN tied directly to IN: LP5907 EN has an internal pull-DOWN (off by
    # default), so tying EN to IN keeps this dedicated XO rail always on.
    u8["EN"] += vbus_a5v
    # Intentional NC pin (SOT-23-5 pin 4, no internal connection).
    u8["NC"] += NC
    u8["OUT"] += vXo3V3

    # ------------------------------------------------------------------
    # L7 — ferrite bead filtering the XO's own supply, per net_plan.md
    # §3.7: "U8.OUT -> L7 ferrite -> C81 (10uF) + C82 (100n) -> U9.VDD".
    # This is the "own filtered supply" the ADC-clock layout requirement
    # depends on: do not route any other load off the filtered side.
    # ------------------------------------------------------------------
    l7 = Part(
        "Device", "FerriteBead", ref="L7", value="600R@100MHz",
        footprint="Inductor_SMD:L_0603_1608Metric",
    )

    # Filtered rail feeding U9 (post-ferrite). Local to this block.
    vXo3V3_filt = Net("vXo3V3_filt")
    l7[1] += vXo3V3
    l7[2] += vXo3V3_filt

    # C81 (10uF bulk) + C82 (100nF) on the filtered side, per net_plan.
    c81 = Part(
        "Device", "C", ref="C81", value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    c81[1] += vXo3V3_filt
    c81[2] += gnd

    c82 = Part(
        "Device", "C", ref="C82", value="100nF",
        footprint="Capacitor_SMD:C_0402_1005Metric",
    )
    c82[1] += vXo3V3_filt
    c82[2] += gnd

    # C83: second 100 nF decoupling cap placed AT the XO's VDD pin
    # (net_plan.md: "C83 (100n) at the pin") — same electrical net as
    # C81/C82, but called out separately because its placement (hard
    # against U9 pin 4) is a layout requirement, not just a value.
    c83 = Part(
        "Device", "C", ref="C83", value="100nF",
        footprint="Capacitor_SMD:C_0402_1005Metric",
    )
    c83[1] += vXo3V3_filt
    c83[2] += gnd

    # ------------------------------------------------------------------
    # U9 — the 40 MHz XO itself. Standard 3225 4-pad pinout:
    #   pin1 = OE/tri-state, pin2 = GND, pin3 = OUT, pin4 = VDD
    # (OT322540MJBA4SL datasheet pin assignment table).
    # ------------------------------------------------------------------
    u9 = Part(
        "Oscillator", "ASE-xxxMHz",
        ref="U9", value="OT322540MJBA4SL 40MHz",
        footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    )
    u9["Vdd"] += vXo3V3_filt
    u9["GND"] += gnd
    # OE tied to vXo3V3 (pre-ferrite LDO output) per net_plan.md §3.7:
    # "U9.GND, U9.OE tied to vXo3V3 (always enabled)". OE is a logic
    # enable input (not a noise-sensitive analog node), so it is fine
    # off the unfiltered side of the dedicated LDO.
    u9["EN"] += vXo3V3  # symbol pin name "EN" = OE/tri-state input

    # Local net for the raw XO output before it fans out to the two
    # independent series-resistor branches.
    xo_out = Net("xoOut")
    u9["OUT"] += xo_out

    # ------------------------------------------------------------------
    # R40 — 33R series termination into the ADC ENCODE input. This is
    # the clean, single-load, shortest-trace branch (net `enc_clk40`).
    # ------------------------------------------------------------------
    r40 = Part(
        "Device", "R", ref="R40", value="33R",
        footprint="Resistor_SMD:R_0402_1005Metric",
    )
    r40[1] += xo_out
    r40[2] += enc_clk40

    # ------------------------------------------------------------------
    # R41 — 100R high-impedance tap feeding the FPGA GBIN input. Kept
    # electrically independent of R40 so the FPGA branch cannot disturb
    # the ADC encode net (net_plan.md §3.7, SPEC.md §2.2).
    # ------------------------------------------------------------------
    r41 = Part(
        "Device", "R", ref="R41", value="100R",
        footprint="Resistor_SMD:R_0402_1005Metric",
    )
    r41[1] += xo_out
    r41[2] += xo_clk_fpga
