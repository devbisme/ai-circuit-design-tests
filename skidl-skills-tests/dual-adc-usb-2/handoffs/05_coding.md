---
phase: coding
status: complete
next_phase: 06_erc
circuit_name: dual_adc_usb
revision: 1
date: 2026-09-09
---

## Receipt

- Wrote `circuits/dual_adc_usb/__init__.py` (empty) and `circuits/dual_adc_usb/__main__.py`,
  wiring all 9 completed block files (11 instantiations — `afe_channel` and `adc_channel`
  each called twice, `ch='A'`/`ch='B'`) into one assembled circuit per
  `architecture/net_plan.md` and each block's own `handoffs/05_blocks/*.md` signature.
- All 9 block function signatures matched the prompt's stated signatures exactly (verified
  against each block's own `.py` file, not just its handoff) — no signature reconciliation
  was needed.
- Found and fixed **one genuine internal defect inside `adc_channel.py`** (not an assembly
  issue — see Decisions #1): a pin-indexing bug that dead-shorted each AD9235's `OTR` and
  `MODE` pins onto `V3V3_A` and `GND`, which only became ERC-visible once both channel
  instances and `fpga_core` were wired together (see Decisions for why the block's own
  isolated ERC never caught it).
- Fixed a second issue confined to `__main__.py` itself: SKiDL 3.0.0's `Circuit.ERC()`
  returns `None`, not an `(errors, warnings)` tuple — the template's `num_errors, num_warnings
  = ERC()` line raised `TypeError`. Replaced with a read of `skidl.logger.erc_logger.error.count`
  / `.warning.count` after the call.
- Ran the assembled circuit. Full-circuit ERC: **0 errors, 33 warnings**. Every warning was
  individually triaged (see `## Next phase must`) — all 33 are expected artifacts of either
  (a) 16 intentionally-spare FPGA GPIO pins, or (b) a rail fed only through a passive
  component (ferrite bead/resistor) which SKiDL's default ERC pin-type model doesn't
  recognize as an active "power source," or (c) two benign net-name merges, or (d) one
  deliberate tie (W25Q32 `~WP`/`~HOLD` → `V3V3_D`) already justified in `fpga_core`'s own
  handoff, or (e) an EEPROM CS/CLK pair whose generic KiCad symbols type both ends as
  `INPUT` even though the FT232H genuinely drives them. None required a code change.
- Because ERC reported 0 errors, exported the netlist and BOM: `outputs/dual_adc_usb.net`
  (268,276 bytes) and `outputs/dual_adc_usb_bom.xml` (76,958 bytes).

## Artifacts

| Path | What it contains | Who reads it next |
|------|------------------|--------------------|
| circuits/dual_adc_usb/__init__.py | Empty package marker | erc-reviewer |
| circuits/dual_adc_usb/__main__.py | Top-level nets/buses, all 11 block instantiations, ERC + export gate | erc-reviewer |
| circuits/dual_adc_usb/adc_channel.py | Block file — **patched** (AVDD/AGND pin-indexing fix, see Decisions #1) | erc-reviewer |
| outputs/dual_adc_usb.net | Exported KiCad netlist (post-ERC-clean) | layout / erc-reviewer |
| outputs/dual_adc_usb_bom.xml | Exported BOM XML (post-ERC-clean) | erc-reviewer |

## Key facts for the next phase

- **Run command:**
  ```
  cd /home/devb/projects/AI/skidl-skills-tests/dual-adc-usb-2 && \
  KICAD9_SYMBOL_DIR=/usr/share/kicad/symbols \
  KICAD9_FOOTPRINT_DIR=/usr/share/kicad/footprints \
  python3 -m circuits.dual_adc_usb
  ```
- **ERC result: 0 errors, 33 warnings.** All 33 triaged and justified below — see
  `## Next phase must`. Netlist/BOM already exported (gated on 0 errors, per the assembler's
  own instructions).
- **Circuit totals** (measured directly on `default_circuit` after full assembly, not
  estimated): **238 parts, 203 nets.**
- **Top-level nets created in `__main__.py`** match `architecture/net_plan.md` verbatim:
  power (`VBUS, GND, V3V3_D, V1V2, V5_A, VN5_A, V3V3_A, V3V3_CLK, VREF_0V5_A, VREF_0V5_B,
  PWREN_N`), USB (`USB_DP, USB_DM`), analog signal (`BNC_A_SIG, BNC_B_SIG, ADC_A_IN,
  ADC_B_IN, ADC_A_VINN, ADC_B_VINN`), clock (`CLK_ADC_A, CLK_ADC_B, CLK_10M, CLK60`), ADC
  status (`ADCA_OTR, ADCA_PDWN, ADCB_OTR, ADCB_PDWN`), SRAM control (`SRAM_CE_N, SRAM_OE_N,
  SRAM_WE_N, SRAM_UB_N, SRAM_LB_N`), FIFO control (`FIFO_RXF_N, FIFO_TXE_N, FIFO_RD_N,
  FIFO_WR_N, FIFO_OE_N`), FPGA housekeeping (`EXT_TRIG, LED_USB_N, LED_CAP_N`). Buses:
  `ADCA_D`/`ADCB_D` (12), `SRAM_A` (18), `SRAM_D` (16), `FIFO_D` (8) — widths verified
  against every consuming block's docstring.
- `.drive = POWER` is set on `VBUS` and `GND` explicitly in `__main__.py` (neither has an
  active regulator/driver pin of its own at the point they're created — `VBUS` is fed
  through a fuse, `GND` has no single source pin). `V3V3_D`/`V1V2` are set inside
  `power_digital.py`; `V3V3_A`/`V3V3_CLK`/`V5_A`/`VN5_A`/`VREF_0V5_A`/`VREF_0V5_B` are set
  inside `power_analog.py` — both on the same `Net` objects the assembler passes in, so
  no duplicate `.drive` assignment was needed in `__main__.py` for those six.
- No net was renamed and no signature disagreement existed between any two blocks —
  every block's final signature (per its own `handoffs/05_blocks/*.md`) matched the
  prompt's stated signature exactly, so the 11 calls in `__main__.py` use those signatures
  verbatim.

## Decisions

| # | Decision | Options considered | Chosen | Why |
|---|----------|--------------------|--------|-----|
| 1 | `adc_channel.py` shorted OTR/MODE to V3V3_A/GND via `u_adc['AVDD', 1]` / `u_adc['AGND', 1]` etc. | (a) Leave it — not the assembler's job to touch block internals (b) Patch the four lines to plain `u_adc['AVDD'] +=` / `u_adc['AGND'] +=` | **(b) Patch it — this is a genuine block-internal defect, not an integration/wiring choice** | SKiDL's `Part.get_pins()` treats every element of a bracketed tuple as an *independent* OR'd search term across BOTH pin names and pin numbers — `u_adc['AVDD', 1]` does not mean "pin named AVDD, disambiguated by index 1"; it means "any pin named AVDD OR numbered 1". On this part, pin 1 = OTR and pin 2 = MODE, so the original code additionally wired OTR→V3V3_A, OTR→GND, MODE→V3V3_A, MODE→GND — a dead short between the V3V3_A and GND rails through U110/U210's OTR pin. This is invisible to ERC in isolation (OUTPUT-vs-POWER-IN and POWER-IN-vs-POWER-IN aren't flagged as conflicts by SKiDL's default pin-compatibility matrix — the two rails just silently merge into one net), which is why `adc_channel`'s own standalone ERC reported 0 errors. It only surfaced once channel A and channel B were both wired to the same `fpga_core`, where the two `AD9235`'s `OTR` OUTPUT pins collided on the resulting merged net (`OUTPUT connected to OUTPUT` — a real ERC error). Verified live in a Python REPL that plain `u_adc['AVDD']` (no second arg) already returns *both* aliased AVDD pins as one `NetPinList`, exactly as the sourced BOM/datasheet intended, matching the pattern every other block already uses (`sram_buffer.py`'s `u8['VDD'] +=`, `usb_bridge.py`'s `u6['VCCIO'] +=`). **Attribute any rework or re-review of this fix to `adc_channel`, ref designators U110/U210 (per `handoffs/03_sourcing.md` → Parts by block).** |
| 2 | `ERC()` returning `None` in SKiDL 3.0.0 broke the template's `num_errors, num_warnings = ERC()` line | (a) Wrap in try/except and re-run without unpacking (b) Read counts from `skidl.logger.erc_logger.error.count`/`.warning.count` after the call | **(b)** | Confirmed by reading `skidl/circuit.py`: `Circuit.ERC()` pushes `erc_logger` as the active logger, resets its `error`/`warning` `CountCalls` wrappers, runs the checks, and pops back — it never returns a value. `erc_logger.error`/`.warning` are the same `CountCalls` objects the active logger used during the run (verified: `ActiveLogger.set()` copies attributes by reference), so their `.count` after `ERC()` returns holds the true tallies. This is purely a `__main__.py`-local fix, no block file involved. |
| 3 | `VBUS`/`GND` `.drive` at the top level | (a) Leave undriven, rely on implicit pin typing (b) Set `.drive = POWER` explicitly on both | **(b)** | `usb_c_input.py`'s own handoff flags this exact scenario ("if the assembler's own ERC flags `vbus` as undriven... set `.drive = POWER` there as a safe override"). In practice neither ended up needed to avoid an ERC error (F1's fuse pin and the dozens of GND pins across the design were sufficient drivers once merged), but setting both explicitly is the documented-safe, zero-downside choice and matches how every other power rail in this design is handled. |

## Carried forward

**ERC errors: none (0/0).** Nothing to route back to a block for a rework cycle on
correctness grounds.

**Residual ERC warnings (33 total), triaged and attributed — see `## Next phase must`
below for the full per-warning breakdown with block attribution.** None require a code
change; all are either intentional design choices already justified in a block's own
handoff, or artifacts of SKiDL's default ERC pin-type model that don't reflect a real
electrical problem.

**Two known open items carried forward verbatim from the orchestrator's own task
instructions (not ERC-visible, need a human/reviewer decision, both attributed to
`afe_channel`, refs in the 1xx/2xx range per `handoffs/03_sourcing.md`):**
1. `afe_channel` C_trim: attenuator compensation computes to ~18.9 pF nominal
   (R_top2·C_trim = R_bot·C_bot) but the sourced Voltronics JR300 trimmer is only 2–10 pF.
   Either the part or the compensation topology (R_top2/R_bot/C_bot values) needs revisiting.
   Already flagged in `handoffs/05_blocks/afe_channel.md` Decision B4 and design_risks.md R-05.
2. `afe_channel` OPA836 `PD` pin polarity: tied to `v3v3_a` (assumed active-low = enabled).
   `datasheets/OPA836IDBVR_SUMMARY.md` flags this as low-confidence — verify against the TI
   datasheet before board spin. If active-high, the amplifiers are currently tied disabled.

## Escalation

none

---

## Next phase must

**Run command** (also under `## Key facts`):
```
cd /home/devb/projects/AI/skidl-skills-tests/dual-adc-usb-2 && \
KICAD9_SYMBOL_DIR=/usr/share/kicad/symbols \
KICAD9_FOOTPRINT_DIR=/usr/share/kicad/footprints \
python3 -m circuits.dual_adc_usb
```

**All 33 ERC warnings — pre-classified as expected/false-positive, with justification and
block attribution (ref designators mapped through `handoffs/03_sourcing.md` → Parts by
block).** The erc-reviewer should confirm this triage, not re-derive it from scratch:

1. **16× "Unconnected pin" on `ICE40HX4K-TQ144`/U9** (pins 121,122,124,125,128,130,
   134–139,141–144) — **attributed to `fpga_core`**. These are the exact 16 intentionally
   spare GPIO pins documented in `handoffs/05_blocks/fpga_core.md` ("Spare GPIO... available
   for a future revision"). Not a defect.
2. **7× "Insufficient drive current"** on nets fed only through a passive component (a
   ferrite bead or resistor, whose pins aren't typed `POWER-OUT` by SKiDL's default ERC
   model even though they carry real current):
   - `V3V3_A_PRE` (U4 LP5907 `IN`) — fed through Q1's FET-switch drain — **`power_analog`**,
     explicitly flagged in its own handoff as an expected isolation-test artifact.
   - `FT_VPHY` (U6 `VPHY`), `FT_VPLL` (U6 `VPLL`) — each fed through FB4/FB5 — **`usb_bridge`**.
   - `DRVDD_A` (U110 `DRVDD`), `DRVDD_B` (U210 `DRVDD`) — each fed through FB10/FB20 —
     **`adc_channel`**, explicitly flagged in its own docstring/handoff.
   - `ICE40_VCCPLL_FILT` ×2 (U9 `VCCPLL0`, `VCCPLL1`) — fed through R26 — **`fpga_core`**,
     Decision F7 ("one shared filtered node").
3. **6× EEPROM `EE_CS`/`EE_SK` ("no drivers" ×2 + "insufficient drive current" ×4)** —
   **attributed to `usb_bridge`** (U6 FT232H ↔ U7 93CxxC, both internal to this block).
   The generic `Interface_USB:FT232H` and `Memory_EEPROM:93CxxC` KiCad symbols type both
   ends of the CS and CLK lines as `INPUT`, even though the FT232H's internal EEPROM
   controller genuinely drives `EECS`/`EECLK` during EEPROM access — a symbol pin-typing
   limitation, not a wiring defect. Not previously called out by name in `usb_bridge.md`'s
   Carried Forward, but consistent with its "44 isolation warnings" note (these two nets
   are internal to the block, not interface nets, so they'd have appeared in that count
   regardless of assembly).
4. **2× "Pin conflict on net V3V3_D" (BIDIRECTIONAL ↔ POWER-OUT)** between U18
   (W25Q32JVSS, pins 3/`~WP`/`IO2` and 7/`~HOLD`/`IO3`) and U1 (AP7361C-33E `VO`) —
   **attributed to `fpga_core`**, Decision F3: `~WP`/`~HOLD` are deliberately tied directly
   to `V3V3_D` (standard practice for a single/dual-SPI-only design that never uses
   quad-mode). SKiDL's default ERC flags any `BIDIRECTIONAL`-typed pin tied straight to a
   `POWER-OUT` pin, regardless of whether that's the intended, safe, standard tie-off it is
   here.
5. **2× "Merging two named nets"** — both benign net-name bookkeeping, not electrical
   errors: `VREF_0V5_TAP`↔`VREF_0V5_A` (**`power_analog`**, Decision DA2's shared-divider
   tap) and `clk_10m_xo`↔`CLK_10M` (**`clock_gen`**, explicitly flagged in its own handoff
   as "expected/benign, not an error").

**Two non-ERC open items carried forward for design review** (see `## Carried forward`
above): `afe_channel` C_trim range mismatch, `afe_channel` OPA836 PD pin polarity.

## Receipt

- **Block count:** 9 blocks, 11 instantiations (afe_channel ×2, adc_channel ×2).
- **Total parts:** 238. **Total nets:** 203 (measured on `default_circuit` post-assembly).
- **ERC:** 0 errors, 33 warnings (all triaged above).
- **Export:** `outputs/dual_adc_usb.net`, `outputs/dual_adc_usb_bom.xml` — both written
  (ERC gate passed).
- **PASS.**
