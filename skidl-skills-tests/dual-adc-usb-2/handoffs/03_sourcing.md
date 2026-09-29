---
phase: sourcing
status: complete
next_phase: 04_datasheets
circuit_name: dual_adc_usb
revision: 1
date: 2026-09-08
---

## Receipt

- Sourced all ≈70 BOM line items across all 9 blocks (11 instantiations) from
  `architecture/skeleton_bom.md` into `sourcing/sourced_bom.md`, using the architect's
  recommended MPN wherever it held up to local verification.
- **Tooling override confirmed (R-15):** the `pcbparts` MCP was not connected this
  session either. No live JLCPCB stock, tier, or price could be fetched. Every
  `LCSC#`/`Stock`/`JLCPCB Tier` cell in the sourced BOM is explicitly marked
  `UNVERIFIED (estimate)` — nothing was fabricated. `MPN`, `KiCad Symbol`, and
  `KiCad Footprint` columns, by contrast, were verified against the local library files
  (`/usr/share/kicad/symbols`, 224 libs; `/usr/share/kicad/footprints`) and are real.
- **Caught two symbol/footprint errors in the architecture handoff itself:** the BNC
  jack symbol is `Connector:Conn_Coaxial`, not `Connector:BNC` as the architecture
  handoff stated (no symbol literally named `BNC` exists in `Connector.kicad_sym`); and
  the USB-C receptacle MPN `U262-161N-4BVC11` matches no footprint file — the library
  ships `U262-16XN-4BVC11` (XKB Enterprise), which was substituted.
- **8 documented MPN/package deviations**, all same-class/same-electrical-spec swaps:
  BNC jack (031-5431-10RFX → Amphenol 031-6575, footprint availability), VBUS TVS
  package (SMAJ6.0A is the wrong case for SOD-323 → PESD5V0S1BA), the shield-bleed cap's
  voltage rating (2 kV does not exist in 0603 → moved to 1808), a 22 µF/16 V cap's case
  size (0805 → 1206), the P-FET (DMG2305UX → AO3401A, better JLCPCB availability
  expectation), the two 10 µH inductors (pinned to Murata LQM2HPN100MGL), and the ADC
  data-line damping resistors (array → discrete, per skeleton's own "array or discrete"
  option). None of these touch a `[FIXED]` spec from the architecture handoff.
- Confirmed, by direct grep against the installed KiCad 9 libraries, that **exactly the
  four parts the architecture flagged in R-14 still have no KiCad symbol**: AD9235BRUZ-20
  (28-pin), IS61WV25616BLL-10TLI (44-pin), AD8066ARZ (8-pin dual op-amp), OPA836IDBVR
  (6-pin single op-amp). All four are marked `[GEN]` in `sourced_bom.md`. Everything else
  in the BOM (including all 15 "already verified" symbols the architecture cited, one of
  which — BNC — was actually wrong) has a confirmed symbol and footprint.
- No sourcing failures. `sourcing_status: success`.

## Artifacts

| Path | What it contains | Who reads it next |
|------|------------------|-------------------|
| sourcing/sourced_bom.md | Full per-block BOM: Ref, Function, MPN, Package, Qty, LCSC#, Stock, JLCPCB Tier, KiCad Symbol, KiCad Footprint, Notes — for all 9 blocks | datasheet-librarian, then the block coders |

No `sourcing/sourcing_failures.md` was written — nothing failed.

## Parts by block

Carried forward from the architect's `## Parts by block` table (`handoffs/02_architecture.md`),
now with real MPNs. Every ref designator in `sourcing/sourced_bom.md` appears in exactly
one row below. `(×2)` blocks list refs **per instance** — instance A uses the `1xx`
series, instance B the `2xx` series; the MPN list is the same part list for both
instances (same design, duplicated).

| block_id | refs | MPNs |
|----------|------|------|
| `usb_c_input` | J1, F1, D1, D2, FB1, R1, R2, R3, C1, C2 | XKB U262-16XN-4BVC11, MF-MSMF050-2, USBLC6-2SC6, Nexperia PESD5V0S1BA, DLW21SN900HQ2L, R 5.1kΩ, R 1MΩ, C 10µF, C 4.7nF/2kV |
| `power_digital` | U1, U2, D3, R4, C3–C7 | AP7361C-33E-13, AP2112K-1.2TRG1, generic 0603 green LED, R 1kΩ, C 1µF/10µF/100nF |
| `power_analog` | U3, U4, U5, Q1, FB2, FB3, FB6, L1, L2, R5–R9, C8–C21 | AO3401A, LM2776DBVR, LP5907MFX-3.3/NOPB, REF3025AIDBZR, BLM18PG601SN1D, Murata LQM2HPN100MGL, Susumu RG1005N-4021-B-T5, RG1005N-1001-B-T5, generic passives |
| `clock_gen` | X1, U16, U17, R10–R12, C22–C24 | ASEM1-10.000MHZ-LC-T, 74LVC1G34GW,125, R 33Ω, C 100nF/1µF |
| `afe_channel` (×2) | A: J2, U100, U101, D100, D101, R100–R115, C100–C112 · B: J3, U200, U201, D200, D201, R200–R215, C200–C212 | Amphenol 031-6575, AD8066ARZ **[GEN]**, OPA836IDBVR **[GEN]**, BAV99, ESD9L12ST5G (DNP), Susumu RG2012N-4753-B-T5, RG1608N-4992-B-T5, Voltronics JR300 trimmer, generic R/C |
| `adc_channel` (×2) | A: U110, FB10, R120–R133, C120–C132 · B: U210, FB20, R220–R233, C220–C232 | AD9235BRUZ-20 **[GEN]**, BLM18PG601SN1D, R 100Ω ×12 (discrete), generic decoupling |
| `sram_buffer` | U8, C41–C46 | IS61WV25616BLL-10TLI **[GEN]**, generic decoupling |
| `usb_bridge` | U6, U7, Y1, R13–R19, FB4, FB5, C25–C40 | FT232HL, 93LC46BT-I/OT, X322512MSB4SI, R 12kΩ/10kΩ/2.2kΩ, BLM18PG601SN1D, generic decoupling |
| `fpga_core` | U9, U18, J4, J5, D4, D5, D6, D7, R20–R26, C47–C64 | iCE40HX4K-TQ144, W25Q32JVSSIQ, generic 2×5 1.27mm header, generic 1×2 2.54mm header, generic LEDs, BAV99, generic R/C |

**[GEN]** = no KiCad symbol exists; must be generated with `kipart` before the block
coder can place it (see `## Carried forward`).

## Key facts for the next phase

- **The four `[GEN]` parts need real KiCad symbols before any block referencing them can
  be coded:** AD9235BRUZ-20 (afe/adc boundary — `adc_channel`, ×2), IS61WV25616BLL-10TLI
  (`sram_buffer`), AD8066ARZ (`afe_channel` U_a, ×2), OPA836IDBVR (`afe_channel` U_b,
  ×2). Budget `kipart` runs for all four; for AD8066/OPA836 a generic placeholder exists
  for schematic capture (`Amplifier_Operational:LM7332` for the dual — standard SOIC-8
  dual-op-amp pinout is universal) but **OPA836's SOT-23-6 single-op-amp pinout is
  vendor-specific — do not use a placeholder for it, generate the real symbol from the
  datasheet pin map.**
- **Symbols that actually exist, verbatim** (use these names, not the architecture
  handoff's list — one entry there was wrong): `FPGA_Lattice:ICE40HX4K-TQ144`,
  `Interface_USB:FT232H`, `Memory_Flash:W25Q32JVSS`, `Memory_EEPROM:93CxxC`,
  `Regulator_Linear:AP7361C-33E`, `Regulator_Linear:AP2112K-1.2`,
  `Regulator_Linear:LP5907MFX-3.3`, `Regulator_SwitchedCapacitor:LM2776`,
  `Reference_Voltage:REF3025`, `Power_Protection:USBLC6-2SC6`, `Diode:BAV99`,
  `74xGxx:74LVC1G34`, `Oscillator:ASE-xxxMHz`, `Connector:Conn_Coaxial` (**not** `BNC`),
  `Connector:USB_C_Receptacle_USB2.0_16P`.
- All electrical numbers from `architecture/skeleton_bom.md` and `handoffs/02_architecture.md`
  (rail voltages/currents, ADC span, attenuator ratio, filter order, jitter budget, burst
  depth, power budget) are unchanged — no substitution here altered any of them.
- Filter R/C exact values are still deferred to the coding phase (per architecture); the
  sourcer only pinned the part *class*: 0402 1% thin-film generic for `R_filt`, 0402
  C0G/NP0 ±2% generic for `C_filt`.

## Decisions

| # | Decision | Options considered | Chosen | Why |
|---|---|---|---|---|
| S1 | BNC jack MPN | Amphenol 031-5431-10RFX (architect's pick, no footprint file) / Amphenol 031-6575 / TE 1478035 / TE 1478204 / Amphenol B6252HB-NPP3G-50 | **Amphenol 031-6575** | Only right-angle/horizontal BNC in the library whose footprint file actually exists; matches the "PCB mount, right angle" spec |
| S2 | BNC symbol name | `Connector:BNC` (as the architecture handoff stated) / `Connector:Conn_Coaxial` (grep-verified) | **`Conn_Coaxial`** | The literal symbol `BNC` does not exist in `Connector.kicad_sym`; `Conn_Coaxial` is the generic coax symbol KiCad ships and is what the architecture handoff's own claim actually pointed at |
| S3 | USB-C receptacle MPN | `U262-161N-4BVC11` (architect's, no footprint match) / `U262-16XN-4BVC11` (footprint-verified) | **U262-16XN-4BVC11** | Only suffix that resolves to an actual footprint file in the library |
| S4 | VBUS TVS | SMAJ6.0A (DO-214AC, wrong case for stated SOD-323) / PESD5V0S1BA (SOD-323, correct) | **PESD5V0S1BA** | Architect's primary suggestion used a package family (SMA) that does not physically match the SOD-323 the skeleton BOM specified; the alternate does |
| S5 | Shield-bleed cap package | 0603 (as skeleton stated) / 1808 | **1808** | A 2 kV working-voltage rating does not exist in a 0603 ceramic chip cap (≈50–100 V ceiling); 1808 is the smallest common case genuinely rated to kV-class |
| S6 | 22 µF/16 V bulk cap package | 0805 (as skeleton stated) / 1206 | **1206** | 22 µF at 16 V in 0805 X5R suffers heavy DC-bias derating; 1206 is the realistic minimum case size at this value/voltage |
| S7 | P-FET load switch | DMG2305UX (architect's) / AO3401A | **AO3401A** | Both meet the ≥500 mA / Vgs(th)<2 V spec; AO3401A is the more commonly Basic-tier-stocked of the two families at JLCPCB (estimate, unverified live) |
| S8 | ADC data-line damping (×12) | Resistor array / discrete singles | **Discrete 0402** | Skeleton itself offered both; discrete singles are the more commonly second-sourceable option |

## Carried forward

- **Four parts still need `kipart`-generated symbols before the block coders can place
  them (R-14), unchanged from architecture, now confirmed by direct grep rather than
  inferred:** `AD9235BRUZ-20` (28-pin, `adc_channel` ×2), `IS61WV25616BLL-10TLI`
  (44-pin, `sram_buffer`), `AD8066ARZ` (8-pin dual op-amp, `afe_channel` U_a ×2),
  `OPA836IDBVR` (6-pin single op-amp, `afe_channel` U_b ×2). Budget this work in the
  datasheet phase (pin lists) and the coding phase (symbol generation + placement).
- **Single-sourced / precision items worth a second look before ordering:** the 0.1%
  25 ppm resistors (R7, R8, R_top1/2, R_bot — Susumu RG-series MPNs given as a plausible
  family/format, not a live-catalog lookup); the trimmer cap `C_trim` (Voltronics JR
  series); the 10 MHz XO `X1` (jitter-spec-bound, R-01, already flagged Extended-tier by
  the architecture). All four are estimated **Extended tier** — verify live before
  committing to a production run.
- **Every stock/tier/price figure in `sourced_bom.md` is an estimate**, not a
  verification — R-15 is still open in the sense that nobody has hit a real JLCPCB API
  this pipeline run. Re-run this phase (or a stock-check pass) once `pcbparts` is
  connected, before ordering hardware.
- **Mechanically critical, unresolved:** J2/J3 (BNC, now Amphenol 031-6575) and J1
  (USB-C, now XKB U262-16XN-4BVC11) sit on the panel edge — verify the physical
  footprint against a real part in hand before layout, per the architecture handoff.

## Escalation

none
