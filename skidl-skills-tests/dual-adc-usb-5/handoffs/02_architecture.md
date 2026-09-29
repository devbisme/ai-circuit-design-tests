---
phase: 02_architecture
agent: circuit-architect
circuit: dual_adc_usb
written: 2026-09-21T00:00:00Z
status: complete
revision: 3
next_phase: 03_sourcing
---

# Phase 2 handoff — Architecture

**Revision 3 is a narrow rework, not a re-architecture.** It closes the two findings routed
here by `handoffs/06_erc.md` — **H-1** (the anti-alias filter is 2nd-order, not 3rd, and misses
F9 by 4.1 dB) and **M-1** (85 mV of OPA355 common-mode margin) — and fixes one documentation
defect (**N-2**, the FT232H VREGIN source). Decisions 1–16 stand unchanged; 17–20 are new.
Everything changed carries a `<!-- revised: rev3 ... -->` marker in the artifacts.

**No block signature, net interface, IC or topology changes.** Two block files need value and
wiring edits inside them; nothing else in the pipeline moves.

## Decisions


1. **ADC = ADS5231IPAGT** (C2670079, dual 12-bit 40 MSPS, simultaneous, parallel CMOS,
   3.0–3.6 V, TQFP-64, stock 154, $31.77). Over 2× AD9235BCPZ-40: one package gives one
   shared clock edge (F1 becomes a silicon property, not a layout problem), 70.7 dB SNR =
   11.4 ENOB vs F11's 10.5 requirement, and $15.89/ch vs $25.30/ch. Over 2× AD9237-40 (the
   only ≥200-stock part): AD9237's 66.5 dB leaves 0.25 ENOB of margin and costs $65.67.
2. **FPGA = GW1NR-LV9QN88PC6/I5** (C5799578, 8640 LUT4 + **64 Mbit in-package PSRAM**,
   QFN-88, stock 180, $23.31). The in-package RAM deletes a 39-signal memory bus from a
   4-layer board; that, not the logic, is what the $23 buys. Internal config flash means no
   external config memory. 45 user I/O needed of ~63 available.
3. **USB bridge = FT232HL-REEL** (C51997, LQFP-48, stock 2048, $9.72) in **245 synchronous
   FIFO** mode. No firmware. Its 60 MHz CLKOUT gives the FPGA its FIFO clock free and its
   PWREN# solves the enumeration-current problem (decisions 9 + 13).
4. **ADC clock = 20.000 MHz XO direct to the ADC** (X1, C5452685). The ADC's minimum clock
   is 20 MHz so 10 MSPS direct is impossible; sampling at 20 MSPS lets **8 MB hold 104.9 ms
   of both channels raw**, so the specified 10.0 MSPS/ch is produced by **host-side 2:1
   decimation** and **no FPGA DSP is required to meet any HARD requirement**. The 40 MHz
   alternative needs a mandatory FPGA 4:1 decimator just to reach 0.1 s, and runs PSRAM at
   ~60–80 % bandwidth instead of ~25–40 %.
5. **Front end = ÷20 passive compensated divider into a 1.20 V bias → OPA355 unity buffer →
   THS4551 FDA at G = 2.** ÷20 not ÷10 because a 2 V p-p node swing will not fit the
   buffer's common-mode window on a 3.3 V rail (`design_risks.md` R-3). The divider returns
   to `VBIAS` rather than ground because P6 forbids a negative rail — that is what performs
   the level shift. The FDA subtracts `VREF_FE` = 0.95·`VBIAS`, derived from `VBIAS` so
   their noise cancels, and takes `VOCM` from the ADC's own CM pin.
6. **Buffer = OPA355NA/3K** (C2058090, SOT-23-6, stock 489). Chosen on **3 pA input bias
   current**, not on bandwidth: the divider node is 47.5 kΩ, where any bipolar amplifier's
   µA-class bias current becomes tens of mV of drifting offset. This eliminates every
   bipolar high-speed RRIO part regardless of GBW.
7. **FDA = THS4551IRGTR** (C2869590, QFN-16-EP, stock 602). On 3.3 V it swings to 0.2 V of
   each rail, so the ADC's 1.15–2.15 V per-output window sits mid-range. AD8138 lost on
   headroom, not speed — its output range starts at ~1.0 V, exactly where ours ends.
8. **Anti-alias = 3rd-order differential, ≈6 MHz**, in the FDA feedback plus an output RC.
   Because the board samples at 20 MSPS, the alias edge is **15 MHz, not 7 MHz**; a 3rd-order
   response gives 24 dB there. This deletes the 5th-order LC elliptic (3 inductors +
   4 capacitors per channel) that direct 10 MSPS sampling would have required.
9. **Rails: `+5V_IN` → U9 load switch → `+5V_SW` → {SY8089A1AAC buck → `+3V3_D` → 1.2 V LDO
   → `+1V2_D`} and {TLV75733PDRVR LDO → `+3V3_A`}.** U9 is enabled by FT232H **PWREN#**, so
   before USB configuration only the bridge is powered (~70 mA) and SPEC P4 is met properly
   rather than ignored. `+3V3_ADCD` = `+3V3_D` through **FB2** feeds the ADC's DRVDD, keeping
   24 data lines' switching current on the digital rail. **No 1.8 V rail** — nothing needs
   one. *(Amended in rev 2: the switch is an IC, not a discrete P-FET — decision 13.)*
10. **Divider compensation uses a trimmer capacitor, not a fixed C.** ~7 pF of the ~89 pF
    bottom-leg capacitance is unpredictable stray (amp + clamp + trace), worth ±0.17 dB in
    the 1–5 MHz band. **The sourcer must not substitute a fixed capacitor.**
11. **Overvoltage protection = 1 kΩ + BAV99 to the rails at the buffer input**, not a TVS at
    the BNC. A TVS at the BNC would add 50–100 pF of nonlinear capacitance across the 1 MΩ
    input. As built, ±30 V (I5) does not even make the clamp conduct; the practical limit is
    the 475 kΩ resistors' rating, ~±150 V.
12. **One `GND` net.** No `AGND`/`DGND` split, no 0 Ω stitch. The partition is copper
    placement (`design_risks.md` R-7), not a schematic net.

### New in revision 2

13. **The load switch is `U9` = AP2161WG-7 (C176957), not a discrete P-FET.** Rev 1's Q1
    (HL2301A) **could not turn off**: its source sat on `+5V_IN`, and PWREN# — a 3.3 V CBUS
    output pulled up to 3V3 — gave a best-case "off" Vgs of −1.5…−1.7 V against a
    −0.4…−1.0 V threshold, so the whole rail tree came up at plug-in and SPEC P4 was unmet.
    AP2161's EN is **active-low and GND-referenced** (VIH 2.0 V min, VIL 0.8 V max) and
    PWREN# is active-low, so PWREN# drives it **directly — no inverter, no level shift, no
    polarity trap**; 3.3 V = off, 0 V = on. It also brings what the bare FET lacked: a
    1.1/1.5/1.9 A over-load limit bracketing the 485 mA worst-case load, a 0.6 ms controlled
    rise time (≈167 mA of inrush into the ~20 µF behind it), reverse-current blocking, UVLO
    and thermal limiting — at 95 mΩ, within 5 mΩ of the FET it replaces. **`Power_Management:AP2161W`
    already exists in the stock KiCad library** at the SOT-23-5 footprint the design already
    uses, so nothing has to be generated. Losers and why, in `ic_selection.md` § load switch:
    an active-high switch + 2-transistor level shift (3 parts, 3 refs, 2 symbols, no
    electrical gain); a P-FET with |Vgs(th)| > 2 V (fails the same arithmetic from the other
    end — with 3.3 V on the gate and 5 V on the source, the *on*-state Vgs is −1.7 V);
    and deleting the P4 gating altogether (defensible — P4 is CLAUDE-tagged — but it costs
    3.7 unit loads of USB non-compliance to save one $0.21 part, and strands both the EEPROM
    PWREN# setting and the R-9 bring-up escape).
14. **`Q1` is retired as a ref designator; the switch is `U9`.** An IC carrying a `Q`
    designator is how a BOM row gets mis-assembled. `R3` (the 100 k gate pull-up) is
    **deleted** — `usb_bridge`'s existing 10 kΩ pull-up to 3V3 on `PWREN_N` (`R_pwren`)
    already holds EN high = OFF from the instant VBUS appears and through FT232H reset.
    **`R6` stays**: as a DNP 0 Ω from `PWREN_N` to `GND` it now pulls EN *low* = switch ON,
    which is exactly the bring-up escape `design_risks.md` R-9 asks for.
15. **U1's feedback reference is verified, and its divider does not change.**
    `datasheets/SY8089A1AAC.pdf` (Silergy AN_SY8089A1, obtained in rev 2) gives
    `VOUT = 0.6 × (1 + RH/RL)` and **VREF = 591 / 600 / 609 mV**. R4 = 45.3 k / R5 = 10.0 k
    → **3.318 V** (3.268–3.368 V over VREF tolerance alone). The 0.8 V scenario that would
    have produced 4.4 V and killed every 3.3 V part is **ruled out from a primary source**;
    `datasheets/SY8089A1AAC_SUMMARY.md`'s "unverified" flag is closed.
16. **`R22` = 10 Ω isolates U4A's output from `VBIAS`.** `VBIAS` carries 200–250 pF (both
    channels' 82 pF `C_bot` plus stray) and is the front end's AC ground; a 10 MHz-GBW RRIO
    op-amp driving that bare loses phase margin and rings on the one node the measurement
    references. U4A now drives a local net `VBIAS_DRV`, feedback is taken there (inside
    R22), and R22 bridges `VBIAS_DRV` → `VBIAS`. Isolation zero ≈64 MHz; 10 Ω against the
    50 kΩ `R_bot` is −74 dB in the AC-ground role; DC drop at ~2.4 µA is 24 nV. New risk
    **R-11**.


### New in revision 3

17. **F9 and F10 are renegotiated, and these are the numbers this board is held to.** Both are
    SOFT/CLAUDE — my own upstream choices, not the user's — and as written they are mutually
    unachievable (together n ≈ 7; F9's two clauses alone n ≈ 5). Final:
    - **F9 → ≤ 0.5 dB droop to 4.0 MHz, −3 dB at 6.1 MHz.** Delivered: **−0.15 dB at
      4.0 MHz** nominal, ≤0.40 dB worst case over ±5 % C0G / ±1 % R. **The original
      "−3 dB ≤ 5 MHz" clause is deleted**: it was written assuming direct 10 MSPS sampling, and
      at 20 MSPS the analog Nyquist is 10 MHz, so capping the bandwidth at 5 MHz buys nothing
      and costs the passband. Passband flatness is the clause that is a real performance number,
      and it goes from **missed by 4.1 dB to met with margin**.
    - **F10 → ≥ 25 dB above 16.0 MHz** (22.7 dB worst case), ≥13 dB at 10 MHz, genuinely
      3rd-order. **16 MHz, not 15** — it is the exact frequency above which 20 MSPS sampling
      folds energy into the 0–4 MHz measurement band (|f − 20| ≤ 4). 25 dB at **7 MHz** from
      analog alone is unreachable with F9 attached and is abandoned.
    - Authority and arithmetic: `design_risks.md` R-5, R-12 and § Requirements this
      architecture knowingly deviates from (now the authority — **SPEC.md's F9/F10 rows are
      superseded**, and carry a pointer to it).
18. **Anti-alias = 2nd-order MFB around the FDA + one output RC = 3rd-order Butterworth,
    −3 dB at 6.1 MHz.** The rev-1/2 network silently lost an order: `C_cm` and `C_diff` sit on
    the same node behind the same `R_o`, so differentially they merge into one pole. **More RC
    sections cannot fix it** — for a cascade of *real* poles, D dB of droop at 4 MHz caps
    attenuation at 16 MHz at 16·D, so 0.5 dB buys ≤8 dB *at any order*. (This is why the ERC
    review's "split the CM caps behind their own resistors" is rejected: +6 parts for ~2 dB.)
    Complex poles are mandatory ⇒ the filter must run through the FDA's feedback. Cost:
    **+3 parts per channel** (`R_mfb` ×2 at 499 Ω, one differential `C_mfb` 68 pF), no
    inductors, so rev 1's rejection of the LC elliptic still holds. Exact values and the
    realized response table: `net_plan.md` § Anti-alias filter. **DC is untouched** — no DC
    current flows in `R_mfb`, so the gain is still `R_f/R_g` = 2.004 and every DC number the ERC
    review verified carries over.
19. **`VBIAS` = 1.100 V, not 1.200 V** (R8 = 22.0 kΩ, R9 = 11.0 kΩ; 3.3·11/33 = 1.1000 V
    exactly). OPA355's VCM ceiling is (V+) − 1.5 V = 1.800 V, 1.734 V with the rail 2 % low;
    +10 V full scale put the buffer at 1.639 V — **85 mV** worst case, spent exactly where F11's
    ENOB is measured. 1.100 V gives **1.544 V ⇒ ≈180 mV, 2.1×**. **I checked the ERC review's
    R8 = 23.0 kΩ / R9 = 10.0 kΩ and am not taking it**: the VBIAS arithmetic is right
    (1.000 V, 285 mV), but (a) **23.0 kΩ is not an E96, E24 or E192 value** — it is
    unsourceable as a 1 % part, (b) 1.000 V pushes the −30 V overrange case (SPEC I5) to
    −0.547 V, past the OPA355's (V−) − 0.5 V abs max, so the BAV99 would have to conduct in
    spec'd operation, and (c) it drops the FDA summing node to 0.967 V toward a THS4551
    input-CM floor **nobody in this pipeline has ever read from a datasheet**. 1.100 V takes
    most of the margin for none of the risk, on two E24 jellybeans. Gain, zero-offset and input
    impedance are untouched — they depend on ratios only. Detail: `design_risks.md` R-3.
20. **New requirement S1 [HARD, DERIVED] — the host's 2:1 decimation must include a real
    digital low-pass** (≥40 dB above 5.0 MHz, ≤0.1 dB ripple to 4.0 MHz; a ~33-tap FIR at
    20 MSPS suffices). **Answering the ERC review's question directly: the 16 MHz alias-edge
    argument does *not* depend on the host — that one is pure 20 MSPS arithmetic — but the
    delivered 10 MSPS stream does.** Everything the ADC legitimately digitises between 5 and
    10 MHz folds into 0–5 MHz if the host just drops samples, and no achievable analog filter
    can prevent it (≥25 dB at 5 MHz with −0.5 dB at 4 MHz needs n ≈ 9). Naïve sample-dropping
    makes the board fail F9/F10 **in software, with no hardware symptom**. Risk **R-12**, and
    the only new blocking item in this revision.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `architecture/net_plan.md` | Every net, type, connected refs. **rev 3: new § Anti-alias filter (the exact pole plan + response table), new § VBIAS = 1.100 V, `<ch>_MFBP`/`<ch>_MFBN` nodes, VBIAS/VREF_FE rows** | Always — before writing any code |
| `architecture/design_risks.md` | R-1…R-12. **rev 3: R-5 rewritten and closed, R-3 rewritten, R-12 new (host decimation filter = S1), F9/F10/I4 deviation rows restated** | Sourcing, layout, and before touching the AFE |
| `architecture/skeleton_bom.md` | function \| MPN \| package \| qty \| notes. **rev 3: MFB rows, C_f/C_diff/C_cm values, R8/R9** | Sourcing |
| `architecture/ic_selection.md` | Candidates, winners, why losers lost. **rev 3: the FDA is now load-bearing for the filter — substitution condition added** | Before substituting anything |
| `architecture/block_diagram.md` | Mermaid block/signal flow. **rev 3: FDA block label, signal-chain steps 1/3/6** | Orientation before coding |
| `erc_report.md` § H-1, M-1 | The measured as-built response and the common-mode arithmetic this revision answers | Before touching `afe_channel` |
| `datasheets/FT232HL-REEL_SUMMARY.md` | **rev 3: VREGIN corrected to `+5V_IN` (was `+3V3_D`), with the FT_000288 §6.1 citation and why it is load-bearing** | Any FT232H work |

## Block manifest

**Unchanged from rev 1 and rev 2 — every signature and interface-net list still holds
verbatim.** Rev 3 changes only values and internal wiring inside `afe_channel` and
`analog_power_ref`.

| block_id | block_name | function_signature | interface_nets |
|---|---|---|---|
| `usb_c_input` | USB-C input + protection | `usb_c_input(v5_in, usb_dp, usb_dm, gnd)` | `+5V_IN, USB_DP, USB_DM, GND` |
| `digital_power` | Digital power tree + load switch | `digital_power(v5_in, v5_sw, pwren_n, v3v3_d, v3v3_adcd, v1v2_d, gnd)` | `+5V_IN, +5V_SW, PWREN_N, +3V3_D, +3V3_ADCD, +1V2_D, GND` |
| `analog_power_ref` | Analog LDO + bias references | `analog_power_ref(v5_sw, v3v3_a, vbias, vref_fe, gnd)` | `+5V_SW, +3V3_A, VBIAS, VREF_FE, GND` |
| `afe_channel` | Analog front end (instantiate ×2) | `afe_channel(ain, adc_in_p, adc_in_n, vbias, vref_fe, vocm, v3v3_a, gnd)` | ch1: `AIN1, CH1_P, CH1_N, VBIAS, VREF_FE, VOCM, +3V3_A, GND` · ch2: `AIN2, CH2_P, CH2_N, VBIAS, VREF_FE, VOCM, +3V3_A, GND` |
| `adc_dual` | Dual 12-bit ADC | `adc_dual(in1_p, in1_n, in2_p, in2_n, adc_clk, adc_d1, adc_d2, adc_oe_n, adc_pdwn, vocm, v3v3_a, v3v3_adcd, gnd)` | `CH1_P, CH1_N, CH2_P, CH2_N, ADC_CLK, ADC_D1[11:0], ADC_D2[11:0], ADC_OE_N, ADC_PDWN, VOCM, +3V3_A, +3V3_ADCD, GND` |
| `clock_20m` | Low-jitter sample clock | `clock_20m(adc_clk, fpga_clk, v3v3_a, gnd)` | `ADC_CLK, FPGA_CLK, +3V3_A, GND` |
| `fpga_core` | FPGA, JTAG, LED, trigger | `fpga_core(adc_d1, adc_d2, adc_oe_n, adc_pdwn, fpga_clk, fifo_d, fifo_rxf_n, fifo_txe_n, fifo_rd_n, fifo_wr_n, fifo_oe_n, fifo_siwu, fifo_clk, v3v3_d, v1v2_d, gnd)` | `ADC_D1[11:0], ADC_D2[11:0], ADC_OE_N, ADC_PDWN, FPGA_CLK, FIFO_D[7:0], FIFO_RXF_N, FIFO_TXE_N, FIFO_RD_N, FIFO_WR_N, FIFO_OE_N, FIFO_SIWU, FIFO_CLK, +3V3_D, +1V2_D, GND` |
| `usb_bridge` | FT232H + EEPROM + crystal | `usb_bridge(usb_dp, usb_dm, fifo_d, fifo_rxf_n, fifo_txe_n, fifo_rd_n, fifo_wr_n, fifo_oe_n, fifo_siwu, fifo_clk, pwren_n, v5_in, gnd)` | `USB_DP, USB_DM, FIFO_D[7:0], FIFO_RXF_N, FIFO_TXE_N, FIFO_RD_N, FIFO_WR_N, FIFO_OE_N, FIFO_SIWU, FIFO_CLK, PWREN_N, +5V_IN, GND` |

8 blocks, 9 instances → **modular coding mode**.

## Parts by block

Only the two `afe_channel` rows move in rev 3 (**+3 refs per channel**). Everything else is as
built and verified in the ERC review's netlist.

| block_id | refs |
|---|---|
| `usb_c_input` | J1, R1, R2, R12, D1, D2, FB1, C1, C2, C15 |
| `digital_power` | U9, U1, U2, L1, FB2, R4, R5, R6, R7, R20, R21, D4, C3–C7 |
| `analog_power_ref` | U3, U4, FB3, R8, R9, R10, R11, R19, R22, C8–C12 |
| `afe_channel` (ch1) | J2, U_buf1, U_fda1, D_clamp1, **R101–R112** (was R101–R110), C_top1, C_bot1, **C101–C111** (was C101–C110) |
| `afe_channel` (ch2) | J3, U_buf2, U_fda2, D_clamp2, **R201–R212**, C_top2, C_bot2, **C201–C211** |
| `adc_dual` | U5, RA1–RA6, C41–C55 (incl. REFT/REFB and C_vocm) |
| `clock_20m` | X1, R_s1, R_s2, FB4, C56, C57 |
| `fpga_core` | U6, J4, J5, D5, R13, R15, R16, R17, R18, C23–C40 |
| `usb_bridge` | U7, U8, X2, R14, R_pwren, R_eedo, C13, C14, C16, C17–C22, C_ee, C_vregin |

New refs allocated: **R111, R112, C111** (ch1) and **R211, R212, C211** (ch2). All six were
verified free against every block file. `R22` is still the highest plain-numbered `R`; `U9` the
highest `U`.

## Next phase must

Three dispatchable work orders. **Nothing else in the pipeline moves** — the other seven block
files, all sourcing outside WO-3, and every datasheet except the FT232H summary all stand.

### WO-1 — `afe_channel` block coder: one file, `circuits/dual_adc_usb/afe_channel.py`

Signature **unchanged**: `afe_channel(ain, adc_in_p, adc_in_n, vbias, vref_fe, vocm, v3v3_a,
gnd, ch=1)`. Do not touch any other file. Do not re-derive any value — they are synthesised in
`net_plan.md` § Anti-alias filter and reproduced here so you need not open it to code.

1. **Delete every inline comment that states a filter number.** "poles 2 and 3 of the 3rd-order
   ~6 MHz filter", "2×33 ohm with 470 pF → 5.1 MHz", "33 ohm with 220 pF → 22 MHz", "24 dB at
   15 MHz", "1.00k || 27 pF → ~5.9 MHz" — **all wrong** (ERC H-1 measured the real response
   from the netlist). Replace them with the numbers in item 4.
2. **Rewire the gain network into a 2nd-order MFB.** Add two local nets
   `mfb_p = Net('CH%d_MFBP' % ch)` and `mfb_n = Net('CH%d_MFBN' % ch)`. Per leg the chain
   becomes — signal leg first, reference leg identical:
   - `bufout → R_g1 (R105, 499) → mfb_p`; `vref_fe → R_g2 (R106, 499) → mfb_n`
   - `mfb_p → R_f_p (R107, 1.00k) → u_fda[11]` (**OUT−**); `mfb_n → R_f_n (R108, 1.00k) →
     u_fda[10]` (**OUT+**). *`R_f` moves off the FB pin onto the MFB node — this is the
     whole change.* Keep the existing crosswise sense: the leg driven from `bufout` feeds back
     from the **opposite** output, exactly as rev 2 did.
   - **NEW** `mfb_p → R_mfb_p (R111, 499) → u_fda[2]` (**IN+**); `mfb_n → R_mfb_n (R112, 499)
     → u_fda[3]` (**IN−**).
   - `C_f` stays on the FB pins: `C103 (C_f_p)` from `fda_fbp`/`u_fda[4]` (**FB+**) to
     `u_fda[10]`; `C104 (C_f_n)` from `fda_fbn`/`u_fda[1]` (**FB−**) to `u_fda[11]`. `fda_fbp`
     and `fda_fbn` now carry **only** the FB pin and its `C_f` — `R_f` is no longer on them.
   - **NEW** one differential `C_mfb (C111, 68 pF)` between `mfb_p` and `mfb_n`. **One cap
     between the two nodes — not two caps to GND**; a cap to real ground here couples into the
     FDA's common-mode loop.
3. **Values.** `R105/R106 = 499`, `R107/R108 = 1.00k`, **`R111/R112 = 499` (new)**,
   **`C103/C104 = 10pF` (was 27 pF)**, **`C111 = 68pF` (new)**, `R109/R110 = 33` unchanged,
   **`C105 (C_diff) = 330pF` (was 470)**, **`C106/C107 (C_cm) = 100pF` (was 220)**. All 0603;
   caps C0G ±5 %. ch2 = the same with the `2xx` refs.
4. **The comment block you should write instead** (these are the numbers, do not recompute):
   MFB section f₀ = 5.93 MHz, Q = 1.012 (C_f includes THS4551's +0.6 pF internal ⇒ 10.6 pF);
   output RC differential pole 6.35 MHz (`R_o` 33 Ω into `C_cm` + 2·`C_diff` = 760 pF), CM pole
   48 MHz; together a **3rd-order Butterworth, −3 dB at 6.1 MHz**: **−0.15 dB at 4.0 MHz**,
   −1.0 dB at 5 MHz, −5.25 dB at 7 MHz, −13.3 dB at 10 MHz, **−25.3 dB at 16 MHz**, −31.1 dB at
   20 MHz. Worst case ±5 % C0G / ±1 % R: ≤0.40 dB at 4 MHz, ≥22.7 dB at 16 MHz.
5. **DC does not change and must not drift.** No DC current flows in `R_mfb`, so the MFB node
   sits at the summing node's potential and DC gain is still `R_f/R_g` = 2.004. After your
   edit, re-confirm: ±10 V in → **2.0 V p-p differential**; zero differential out at 0 V in.
   Everything else in the ERC review's § Signal-chain arithmetic must still hold.
6. **`VBIAS` is now 1.100 V and `VREF_FE` 1.0453 V** (WO-2). Update the docstring's DC
   operating point: tap at AIN = 0 is 1.0452 V, buffer input spans 0.546…1.544 V over ±10 V.
   **Change no resistor in the divider** — the ÷20 ratio is untouched.
7. **L-1 while you are in the file (optional, cheap):** add one more 100 nF 0402 on `+3V3_A`
   for `u_fda`'s second supply-pin pair (TI's RGT layout guidance wants one per pair). If you
   add it, it needs a new ref — use **C112/C212** and say so; if you skip it, leave a TODO.
8. Re-run the block smoke test and `scripts/validate-footprints.py`. All new parts use
   footprints already in the file (`_FP_R0603`, `_FP_C0603`).

### WO-2 — `analog_power_ref` block coder: two values, `circuits/dual_adc_usb/analog_power_ref.py`

Signature unchanged. Two lines of real change; everything else in the file is correct as built.

1. **`R8` = 21.0k → `22.0k`; `R9` = 12.0k → `11.0k`.** `VBIAS` = 3.3·11.0/33.0 = **1.1000 V**
   exactly. Sum stays 33 kΩ, so divider current and source impedance are unchanged.
2. **Do not touch `R19`/`R11`/`R10`/`C12`/`R22`/`U4`/`U3`/`FB3`/`C8`–`C11`.** `VREF_FE` follows
   automatically to 0.95025 × 1.100 = **1.0453 V**, which is what the front end needs — the
   zero-input match depends on the *ratio*, not on the absolute value.
3. **Update the docstring's ASCII divider diagram and both numbers** (1.2000 V → 1.1000 V,
   1.1403 V → 1.0453 V) and record *why*: OPA355's VCM ceiling is (V+) − 1.5 V = 1.800 V and
   +10 V full scale was reaching 1.639 V, 85 mV worst case (ERC M-1, `design_risks.md` R-3).
   The old comment's "12/33 is the exact 1.2/3.3 ratio, both E96" becomes "11/33 = 1/3 exactly,
   both E24".
4. Nothing else in the pipeline is affected: `VBIAS`/`VREF_FE` are sensed, never driven, by
   `afe_channel`, and no other block touches them.

### WO-3 — part-sourcer: five value changes and one quantity, nothing else

Re-open `sourcing/sourced_bom.md` and change **only** these. Do not re-source, re-price or
re-verify any other row; do not touch the critical-path five. **Four values are new to the
BOM** — that is the whole reason this WO exists. All four verified in live JLCPCB stock today,
all Basic-or-Preferred (**no assembly fee**), all 0603 C0G ±5 % 50 V, same Samsung `CL10C`
family as the outgoing parts, so the footprint and symbol rows are unchanged:

| Ref(s) | Was | **Now** | MPN | LCSC | Tier | Stock | $ea | Qty |
|---|---|---|---|---|---|---|---|---|
| C103/104, C203/204 (`C_f`) | 27 pF (C5137568) | **10 pF** | CL10C100JB8NNNC | **C1634** | Basic+Preferred | 1.56 M | 0.0076 | 4 |
| **C111, C211 (`C_mfb`, new)** | — | **68 pF** | CL10C680JB8NNNC | **C28262** | Preferred | 155 k | 0.0188 | 2 |
| C105, C205 (`C_diff`) | 470 pF (C27694) | **330 pF** | CL10C331JB8NNNC | **C1664** | Basic+Preferred | 917 k | 0.0180 | 2 |
| C106/107, C206/207 (`C_cm`) | 220 pF (C27675) | **100 pF** | CL10C101JB8NNNC | **C14858** | Basic+Preferred | 3.27 M | 0.0085 | 4 |

Plus, needing **no new part number**:

1. **`R111/R112`, `R211/R212` (new, 4 pieces): 499 Ω ±0.1 %, same MPN as `R105/R106` —
   `PTFR0603B499RP9`, C478882.** Quantity on that row goes **4 → 8**. ±0.1 % is not strictly
   needed (they carry no DC current) but reusing the existing line is free and keeps the two
   legs matched.
2. **`R8` = 22.0 kΩ and `R9` = 11.0 kΩ.** The row is already "generic 1 % 0603, sourcer's
   discretion", so it needs no new MPN — but if you want concrete parts from the same Uniroyal
   `0603WAF` line the rest of the board uses: **22 kΩ = 0603WAF2202T5E, C31850** (Basic+
   Preferred, 3.80 M, $0.0041) and **11 kΩ = 0603WAF1102T5E, C25950** (Preferred, 354 k,
   $0.0035). **Do not substitute 23.0 kΩ** — it is not an E96/E24/E192 value and the design
   does not want it (decision 19).
3. **Delete nothing else.** C5137568 / C27694 / C27675 (27 pF / 470 pF / 220 pF) leave the BOM;
   no other row changes. Net part count **+6** (four 499 Ω, two 68 pF), net cost ≈ **+$0.08**
   per board. Q3's ≈$85.7 estimate is unaffected at two decimal places.

### Follow-up, no work order needed

- **`datasheets/FT232HL-REEL_SUMMARY.md` is already fixed here** (ERC N-2): VREGIN now reads
  `+5V_IN` with the FT_000288 §6.1 citation and the deadlock explanation. `usb_bridge.py` was
  right; no code change.
- **S1 belongs to whoever writes the host software.** It is not a hardware work order, but it
  is a HARD requirement now — see Carried forward.

## Carried forward

- **S1 (new, blocking for F9/F10 to mean anything):** the host's 2:1 decimation **must** include
  a digital low-pass (≥40 dB above 5.0 MHz, ≤0.1 dB ripple to 4.0 MHz). Naïve sample-dropping
  folds 5–10 MHz into the measurement band with **no hardware symptom**. Risk **R-12**.
- **R-5 is closed but not simulated.** The 3rd-order response is computed analytically from the
  MFB transfer function and ignores the FDA's ≈65 MHz closed-loop pole (harmless below 10 MHz).
  Confirm on the bench with a network analyser before a second spin. The MFB node is now
  filter-critical: keep `R_g`/`R_f`/`R_mfb`/`C_mfb` tight and the two legs symmetric.
- **THS4551's input common-mode range has never been read from a datasheet** — phase 04 could
  not obtain the PDF, and the ERC review asserted the FDA summing node was "comfortably" in
  range without a source. Rev 3 moves that node from 1.093–1.426 V to **1.030–1.363 V**. Almost
  certainly fine, and it is one of the three reasons `VBIAS` = 1.100 V beats 1.000 V, but
  **get SBOS778's input-CM spec before the board spin.**
- **Requirement questions resolved by architecture** (all CLAUDE-tagged; reasoning in
  `design_risks.md` § Requirements this architecture knowingly deviates from): **Q3** $70 →
  ≈$85.7; **Q4** stock ≥200 → >100 for U5/U6; **F9** → ≤0.5 dB to 4.0 MHz, −3 dB at 6.1 MHz,
  the "≤5 MHz" clause deleted (**rev 3**); **F10** → ≥25 dB above **16 MHz** analog, 5–10 MHz
  to S1 (**rev 3**, was "above 15 MHz"); **I4** 1 MΩ to GND → 1 MΩ to a **1.100 V** buffered
  bias, BNC sources 1.1 µA into the DUT; **P5** the 1.8 V rail is dropped. **P4 is met.**
- **F3 is delivered by oversampling**: hardware samples 20 MSPS/ch, the host decimates 2:1.
  Must not be "corrected" to a 10 MHz oscillator — the ADC's minimum clock is 20 MHz.
- **X1's phase jitter is unverified.** Budget 14 ps RMS (F14); no JLCPCB oscillator record
  publishes jitter. Confirm ≤5 ps RMS or substitute a SiTime SiT8008 / Epson SG-210 class part.
  At 30 ps the board fails F11 (R-4).
- **PWREN# must be enabled in the FT232H EEPROM image** (U8) on **ACBUS8**, with "suspend on
  ACBUS7 low" left disabled, or the board looks dead — R-9, still the most likely bring-up
  surprise. `R6` is the DNP 0 Ω escape (pulls U9's EN# low = switch ON).
- **Risks that still constrain sourcing**: single-source/lifecycle on U5 and U6 (R-1);
  thermal-pad packages mandatory on U2/U3 (R-8); the trimmer must stay a trimmer (R-2); the
  buffer must stay CMOS-input **and clear 1.65 V input CM on 3.3 V** (R-3); U9's EN polarity and
  current-limit bracket (R-9); **and now the FDA must stay unity-gain stable with ≥100 MHz GBW,
  because its feedback network is part of the filter** (decision 18). THS4551IRUNR remains the
  vetted second source — same die, so the MFB transfers unchanged.
- **Footprints still unverified** (unchanged from rev 2): the C101/C201 trimmer's custom
  `Capacitor_Trimmer_SEHWA` footprint; U6's QFN-88 exposed-pad size vs Gowin's drawing;
  J2/J3's BNC pad/shell geometry vs KH-BNC50-3511.
- **ERC LOWs left open deliberately**: L-2 (R44/R45 10 kΩ vs the FPGA's config-time pull-ups —
  2.2 kΩ removes the doubt, benign either way), L-3 (trigger header has series R, no clamp —
  outside I5's scope), L-4 (SMF5.0CA 5.0 V standoff on a 5.25 V-max rail — leakage only).
  None is mine to fix and none blocks fabrication.
- **No AEC-Q100/Q200 requirement** — SPEC H4 sets no automotive or regulatory scope.
- **Firmware and USB descriptors remain out of scope**; host software now owes S1.

## Do not redo

- Everything under rev 2's `## Do not redo` still stands, and everything under
  `handoffs/06_erc.md` § Do not redo — the 19 benign ERC warnings, netlist reproducibility,
  footprint validation, the FPGA bank voltages (QN88 = SDR SDRAM, all four VCCIOx at 3.3 V is
  **required**), no net merges, supply-vs-abs-max, exposed pads, SPEC F14's clock path.
- **Decisions 1–16.** ADC and FPGA choice, in-package memory, parallel CMOS, 20 MSPS with host
  decimation, ÷20 not ÷10, the OPA355/THS4551 pair, the rail topology and U9 load switch, U1's
  and U2's dividers, the `VREF_FE` divider ordering (R19 = 1.00 kΩ top), the single `GND`, R22.
- **The AFE's DC design and gain chain.** Rev 3 changes `VBIAS`'s absolute value and the AC
  network only; ±10 V → 2.0 V p-p differential, zero differential out at zero input, 999.9 kΩ
  input (I4) and ±30 V survival (I5) are all preserved **and must stay preserved**.
- **The 2nd-order-vs-3rd-order finding itself.** H-1's measurement is arithmetic on netlist
  values, not an opinion: two capacitors on one node behind one resistor are one pole. Do not
  re-open it by re-reading `afe_channel.py`'s old comments, which are wrong.
- **The real-pole bound.** Do not propose "just add another RC section" — 0.5 dB of droop at
  4 MHz caps you at ~8 dB at 16 MHz at any order (R-5). Complex poles or nothing.
- **`VBIAS` = 1.100 V, and specifically not 23.0 kΩ / 1.000 V.** The arithmetic behind both is
  in decision 19 and R-3.

## Receipt

- **8 blocks, 9 instances**; signatures, interface nets and IC selection **all unchanged**.
- **H-1 closed:** anti-alias re-specified as a **2nd-order MFB + output RC = 3rd-order
  Butterworth, −3 dB 6.1 MHz** — **−0.15 dB at 4.0 MHz** (was −4.55) and **−25.3 dB at
  16 MHz** (was −21.4). Strictly better at every frequency that matters, for **+6 parts** and
  **≈+$0.08**/board. No inductors.
- **F9/F10 settled on my own authority** (both SOFT/CLAUDE): F9 → ≤0.5 dB to 4.0 MHz, −3 dB at
  6.1 MHz, the "≤5 MHz" clause **deleted**; F10 → ≥25 dB above **16 MHz**, 7 MHz abandoned as
  unreachable. The 16 MHz edge is pure 20 MSPS arithmetic and does **not** depend on the host;
  the delivered 10 MSPS stream does ⇒ new **S1 [HARD]** host decimation filter, risk **R-12**.
- **M-1 closed, with the reviewer's values rejected on three grounds:** `VBIAS` 1.200 → **1.100 V**
  (R8 = 22.0 k, R9 = 11.0 k), margin 85 mV → **≈180 mV**. R8 = 23.0 kΩ is **not an
  E96/E24/E192 value**, 1.000 V breaks the −30 V abs-max case, and it pushes the FDA summing
  node toward an unverified floor.
- **N-2 fixed in place:** `datasheets/FT232HL-REEL_SUMMARY.md` VREGIN = `+5V_IN` per
  FT_000288 §6.1, with the PWREN# deadlock spelled out. Code was already right.
- **12 open risks** R-1…R-12: R-5 **closed**, R-3 improved, **R-12 new and blocking** (software).
- **3 work orders**: WO-1 (`afe_channel`, 1 file), WO-2 (`analog_power_ref`, 2 values),
  WO-3 (sourcer — **4 new cap values**, all Basic/Preferred and verified in stock, + 1 quantity).
- **Ref delta +6**: R111/R112/C111 (ch1), R211/R212/C211 (ch2). Nothing deleted.
- revision: 3
