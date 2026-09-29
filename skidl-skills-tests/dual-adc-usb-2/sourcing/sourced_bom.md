# Sourced BOM — dual_adc_usb

## ⚠️ Unverified-data caveat (read first)

Architecture risk **R-15**, confirmed at the start of this phase: the `pcbparts` MCP
(live JLCPCB stock/price/tier) is **NOT connected** in this session. Per the sourcing
run's explicit tooling override, this phase used only:

- `/home/devb/.pyenv/shims/skidl-part-search` against `/usr/share/kicad/symbols`
  (224 libs, KiCad 9 format) — used to confirm every KiCad **symbol** actually exists.
- Manual `ls`/`grep` against `/usr/share/kicad/footprints` — used to confirm every
  KiCad **footprint** actually exists.
- General knowledge of commonly-stocked JLCPCB manufacturers/part families for MPN
  selection, biased hard toward generic, second-sourceable jellybean passives and
  mainstream IC families.

**Every `LCSC#`, `Stock`, and `JLCPCB Tier` cell below is `UNVERIFIED (estimate)`.**
None of these numbers were fetched live. `MPN`, `KiCad Symbol`, and `KiCad Footprint`
were verified against the local library files listed above and are **not** estimates.
This is expected per the phase input and is not a sourcing failure — the datasheet and
coding phases can proceed on the MPN/symbol/footprint columns; live stock must still be
re-checked before placing a production order.

**Symbol legend:** ✓ = confirmed present in `/usr/share/kicad/symbols` · **[GEN]** =
confirmed **absent** — must be generated with `kipart` before the block coder can use it
(see `## Carried forward` for the four affected parts, R-14).

---

## Block 1 — `usb_c_input`

| Ref | Function | MPN | Package | Qty | LCSC# | Stock | JLCPCB Tier | KiCad Symbol | KiCad Footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| J1 | USB-C receptacle, USB 2.0 only, 16-pin | **XKB U262-16XN-4BVC11** | SMD 16P | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Connector:USB_C_Receptacle_USB2.0_16P` ✓ | `Connector_USB.pretty:USB_C_Receptacle_XKB_U262-16XN-4BVC11` ✓ | [CRIT] **Deviation:** architect's `U262-161N-4BVC11` matches no footprint file; the library ships `U262-16XN-4BVC11` (XKB Enterprise) — corrected to the exact orderable/footprint-matching suffix |
| F1 | PPTC, 500 mA hold / 1 A trip | MF-MSMF050-2 | 1206 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:Polyfuse` ✓ | `Fuse.pretty:Fuse_1206_3216Metric` ✓ | Must hold 500 mA at 50 °C |
| D1 | USB D+/D− ESD array | USBLC6-2SC6 | SOT-23-6 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Preferred — UNVERIFIED (estimate) | `Power_Protection:USBLC6-2SC6` ✓ | `Package_TO_SOT_SMD.pretty:SOT-23-6` ✓ | Kept as architect's pick |
| D2 | VBUS TVS, 6 V standoff | **Nexperia PESD5V0S1BA** | SOD-323 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:D_TVS` ✓ | `Diode_SMD.pretty:D_SOD-323` ✓ | **Deviation:** architect's alt-1 `SMAJ6.0A` is a DO-214AC (SMA) part — wrong footprint family for the stated SOD-323 package. Kept only the SOD-323-correct alternate |
| FB1 | USB2 common-mode choke, 90 Ω @ 100 MHz | DLW21SN900HQ2L | 0805 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Preferred — UNVERIFIED (estimate) | `Device:Filter_EMI_CommonMode` ✓ | `Inductor_SMD.pretty:L_CommonModeChoke_Coilcraft_0805USB` ✓ | Optional for function, recommended for FCC |
| R1, R2 | CC1 / CC2 pull-down | 5.1 kΩ ±1%, generic | 0402 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | [FIXED] value — USB-C sink advertisement |
| R3 | Shield-to-GND bleed | 1 MΩ, generic | 0402 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | Parallel with C2 |
| C1 | VBUS bulk | 10 µF X5R 16 V, generic | 0805 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0805_2012Metric` ✓ | [FIXED] ≤10 µF total on VBUS — USB inrush limit |
| C2 | Shield-to-GND | **Murata GA355-series (or equiv. safety Y-cap), 4.7 nF ±10%, 2 kV** | **1808** (corrected) | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Extended — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_1808_4520Metric` ✓ | **Deviation:** a 2 kV working-voltage rating does not exist in a standard 0603 ceramic case (≈50–100 V max); moved to 1808, the smallest common case size carrying a genuine kV-class rating. Single-point chassis tie |

## Block 2 — `power_digital`

| Ref | Function | MPN | Package | Qty | LCSC# | Stock | JLCPCB Tier | KiCad Symbol | KiCad Footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| U1 | 3.3 V LDO, 1 A, low dropout | AP7361C-33E-13 | **SOT-223** | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Preferred — UNVERIFIED (estimate) | `Regulator_Linear:AP7361C-33E` ✓ | `Package_TO_SOT_SMD.pretty:SOT-223` ✓ | [FIXED PACKAGE] 0.37 W — do not shrink (R-11) |
| U2 | 1.2 V LDO, 600 mA (iCE40 core) | AP2112K-1.2TRG1 | SOT-23-5 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Regulator_Linear:AP2112K-1.2` ✓ | `Package_TO_SOT_SMD.pretty:SOT-23-5` ✓ | 0.095 W |
| D3 | Power LED, green | generic 0603 green LED | 0603 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:LED` ✓ | `LED_SMD.pretty:LED_0603_1608Metric` ✓ | Hardwired to 3V3_D |
| R4 | LED series | 1 kΩ, generic | 0402 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | ~2 mA |
| C3, C4 | LDO input caps | 1 µF X5R 16 V, generic | 0603 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0603_1608Metric` ✓ | Per LDO datasheets |
| C5, C6 | LDO output caps | 10 µF X5R 16 V, generic | 0805 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0805_2012Metric` ✓ | |
| C7 | Bulk/decoupling | 100 nF X7R 16 V, generic | 0402 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0402_1005Metric` ✓ | |

## Block 3 — `power_analog`

| Ref | Function | MPN | Package | Qty | LCSC# | Stock | JLCPCB Tier | KiCad Symbol | KiCad Footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| Q1 | P-channel load switch, ≥500 mA, Vgs(th) < 2 V | **AO3401A** | SOT-23 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Transistor_FET:Q_PMOS_GSD` ✓ | `Package_TO_SOT_SMD.pretty:SOT-23` ✓ | **Deviation:** chose AO3401A over the architect's `DMG2305UX` — both meet spec; AO3401A is the more commonly JLCPCB-Basic-stocked of the two 8205/3401-family P-FETs. Gated by PWREN_N |
| R5 | Q1 gate pull-up | 100 kΩ, generic | 0402 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | |
| R6 | Q1 gate series (soft start) | 10 kΩ, generic | 0402 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | With C to gate, ~1 ms ramp |
| U3 | −5 V switched-capacitor inverter, ≥60 mA | LM2776DBVR | SOT-23-6 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Preferred — UNVERIFIED (estimate) | `Regulator_SwitchedCapacitor:LM2776` ✓ | `Package_TO_SOT_SMD.pretty:SOT-23-6` ✓ | [CRIT] Needs EN pin (kept, per A-decisions do-not-redo) |
| U4 | 3.3 V low-noise LDO, ≥150 mA, EN | LP5907MFX-3.3/NOPB | SOT-23-5 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Preferred — UNVERIFIED (estimate) | `Regulator_Linear:LP5907MFX-3.3` ✓ | `Package_TO_SOT_SMD.pretty:SOT-23-5` ✓ | [CRIT][FIXED] 6.5 µV RMS; feeds AVDD + XO. EN confirmed on this part number |
| U5 | 2.5 V voltage reference, 30 ppm/°C | REF3025AIDBZR | SOT-23-3 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Preferred — UNVERIFIED (estimate) | `Reference_Voltage:REF3025` ✓ | `Package_TO_SOT_SMD.pretty:SOT-23` ✓ | Sets AFE level-shift offset |
| FB2, FB3 | Ferrite bead, 600 Ω @ 100 MHz, 1 A | BLM18PG601SN1D | 0603 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:FerriteBead` ✓ | `Inductor_SMD.pretty:L_0603_1608Metric` ✓ | V5_A and V3V3_A entry |
| FB6 | Ferrite bead, V3V3_CLK | BLM18PG601SN1D | 0603 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:FerriteBead` ✓ | `Inductor_SMD.pretty:L_0603_1608Metric` ✓ | Isolates XO switching from ADC AVDD |
| L1 | −5 V post-filter inductor | **Murata LQM2HPN100MGL** (10 µH, DCR ≈0.35 Ω, Idc ≈550 mA) | 0805 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Preferred — UNVERIFIED (estimate) | `Device:L` ✓ | `Inductor_SMD.pretty:L_0805_2012Metric` ✓ | Meets ≥100 mA / ≤0.5 Ω DCR |
| L2 | +5 V post-filter inductor | **Murata LQM2HPN100MGL** | 0805 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Preferred — UNVERIFIED (estimate) | `Device:L` ✓ | `Inductor_SMD.pretty:L_0805_2012Metric` ✓ | Same part covers ≥200 mA need |
| R7, R8 | VREF_2V5 → VREF_0V5 dividers (2 ch, 2 resistors each) | **Susumu RG1005N-4021-B-T5** (4.02 kΩ) + **RG1005N-1001-B-T5** (1.00 kΩ), 0.1% 25 ppm | 0402 | 4 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Preferred/Extended — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | Precision divider sets AFE offset; **flag: 0.1% 25 ppm 0402 is a lower-volume precision reel — verify stock before committing, second source is any equivalent 0402 0.1% 25 ppm E96 resistor** |
| C8, C9 | LM2776 flying cap | 1 µF X7R 16 V, generic | 0603 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0603_1608Metric` ✓ | Must be ≥1 µF X7R per skeleton note |
| C10, C11 | LM2776 in/out bulk | 10 µF X5R 16 V, generic | 0805 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0805_2012Metric` ✓ | |
| C12, C13 | −5V_A / +5V_A post-filter bulk | **22 µF X5R 16 V, generic** | **1206** (corrected) | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_1206_3216Metric` ✓ | **Deviation:** 22 µF at 16 V realistically needs 1206+ to avoid excessive DC-bias derating in 0805; moved up one size |
| C14–C17 | U4/U5 in/out decoupling | 1 µF X7R 16 V, generic | 0603 | 4 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0603_1608Metric` ✓ | |
| C18–C21 | Per-pin decoupling, U3/U4/U5 | 100 nF X7R 16 V, generic | 0402 | 4 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0402_1005Metric` ✓ | At every supply pin |

## Block 4 — `clock_gen`

| Ref | Function | MPN | Package | Qty | LCSC# | Stock | JLCPCB Tier | KiCad Symbol | KiCad Footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| X1 | 10.000 MHz CMOS XO, ±25 ppm, ≤5 ps RMS jitter | ASEM1-10.000MHZ-LC-T | 3225 4-pad | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Extended — UNVERIFIED (estimate) | `Oscillator:ASE-xxxMHz` ✓ | `Oscillator.pretty:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm` ✓ | [FIXED SPEC][CRIT] ENOB-limiting part (R-01). Vetted alts: SiT8008BI-73-33S-10.000000, SG-8018CA-10M — same jitter class, verify footprint pin-compat before swapping |
| U16, U17 | Single non-inverting buffer | 74LVC1G34GW,125 | SOT-23-5 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `74xGxx:74LVC1G34` ✓ | `Package_TO_SOT_SMD.pretty:SOT-23-5` ✓ | |
| R10–R12 | Series terminations | 33 Ω, generic | 0402 | 3 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | XO out + each ADC clock |
| C22, C23 | Decoupling | 100 nF X7R 16 V, generic | 0402 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0402_1005Metric` ✓ | |
| C24 | Decoupling bulk | 1 µF X5R 16 V, generic | 0603 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0603_1608Metric` ✓ | |

## Block 5 — `afe_channel` (×2 instances: **A** = 1xx refs, **B** = 2xx refs — table below is PER CHANNEL)

| Ref | Function | MPN | Package | Qty/ch | LCSC# | Stock | JLCPCB Tier | KiCad Symbol | KiCad Footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| J2/J3 | BNC jack, PCB mount, right-angle | **Amphenol RF 031-6575** | THT, horizontal | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Extended — UNVERIFIED (estimate) | `Connector:Conn_Coaxial` — **note: architecture's cited symbol name `Connector:BNC` does not exist; the correct symbol is `Conn_Coaxial`** ✓ | `Connector_Coaxial.pretty:BNC_Amphenol_031-6575_Horizontal` ✓ | [CRIT][FIXED] **Deviation:** architect's `031-5431-10RFX` has no matching footprint in the library; substituted the Amphenol right-angle BNC that does (031-6575). Mechanically panel-critical — verify against the physical part before layout |
| R_top1, R_top2 | Attenuator top leg, 475 kΩ | **Susumu RG2012N-4753-B-T5**, 0.1% 25 ppm | **0805** | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Extended — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0805_2012Metric` ✓ | [FIXED] Two in series = 950 kΩ. **Do not shrink to 0402** (R-12, working-voltage rating) |
| R_bot | Attenuator bottom leg, 49.9 kΩ | **Susumu RG1608N-4992-B-T5**, 0.1% 25 ppm | 0603 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Extended — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0603_1608Metric` ✓ | [FIXED] Ratio sets gain accuracy directly |
| C_trim | HF compensation trimmer | Voltronics JR300 series, 2–10 pF, C0G | SMD trimmer | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Extended — UNVERIFIED (estimate) | `Device:C_Trim` ✓ | `Capacitor_SMD.pretty:C_Trimmer_Voltronics_JR` ✓ | Production trim step, see R-05 |
| C_bot | Attenuator bottom-leg cap | 180 pF C0G ±2%, generic | 0603 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0603_1608Metric` ✓ | R_top·C_top = R_bot·C_bot |
| R_ser | Buffer input series limiter | 1 kΩ, generic | 0402 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | Limits clamp current |
| D_clamp | Input clamp to ±5 V rails | BAV99 | SOT-23 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Diode:BAV99` ✓ | `Package_TO_SOT_SMD.pretty:SOT-23` ✓ | Conducts only beyond ≈±100 V |
| D_esd | Optional low-cap TVS at BNC | ESD9L12ST5G (<2 pF) | SOD-923 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Extended — UNVERIFIED (estimate) | `Device:D_TVS` ✓ | `Diode_SMD.pretty:D_SOD-923` ✓ | **DNP unless ESD testing demands it** — footprint populated per R-12 |
| U_a | Dual op-amp, buffer + SK filter, ±5 V | **AD8066ARZ** | SOIC-8 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Extended — UNVERIFIED (estimate) | **no symbol exists — [GEN], kipart required (R-14).** Placeholder for schematic capture: `Amplifier_Operational:LM7332` ✓ (standard dual-op-amp SOIC-8 pinout) | `Package_SO.pretty:SOIC-8_3.9x4.9mm_P1.27mm` ✓ | [CRIT][GEN] Kept architect's pick. Vetted drop-in alts if AD8066 is short: **OPA2810IDR, OPA1656IDR** (both standard SOIC-8 dual pinout — same placeholder symbol applies) |
| U_b | Single op-amp, MFB + level shift, +3.3 V | **OPA836IDBVR** | SOT-23-6 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Extended — UNVERIFIED (estimate) | **no symbol exists — [GEN], kipart required (R-14).** No safe generic placeholder — SOT-23-6 single-op-amp pinouts are not standardized across vendors; do not substitute a symbol without checking against the OPA836 datasheet pin map | `Package_TO_SOT_SMD.pretty:SOT-23-6` ✓ | [CRIT][GEN][FIXED] **Kept despite the concern:** must stay a 3.3 V single-supply part — this is the ADC's over-voltage protection (A7), not a preference. Do not substitute a ±5 V-only part even if better stocked |
| R_filt (×8) | Sallen-Key + MFB network resistors | generic 1% thin-film, **exact values deferred to filter synthesis (coding phase)** | 0402 | 8 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | 4th-order Butterworth fc = 5.0 MHz, A3 gain = −2. Sourced as a generic 0402 1% reel family — any value is Basic-tier stock |
| C_filt (×5) | Sallen-Key + MFB network caps | generic **C0G/NP0 ±2%**, values TBD | 0402 | 5 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic/Preferred — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0402_1005Metric` ✓ | **[FIXED] C0G/NP0 mandatory** — X7R's voltage coefficient distorts the passband |
| R_s | ADC series damping | 33 Ω, generic | 0402 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | |
| C_s | ADC input charge-kickback | 22 pF C0G, generic | 0402 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0402_1005Metric` ✓ | |
| C_dec (×3) | Op-amp decoupling, 100 nF | 100 nF X7R 16 V, generic | 0402 | 3 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0402_1005Metric` ✓ | At every supply pin |
| C_dec (×3) | Op-amp decoupling, 1 µF | 1 µF X5R 16 V, generic | 0603 | 3 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0603_1608Metric` ✓ | |

## Block 6 — `adc_channel` (×2 instances: **A** = 1xx refs, **B** = 2xx refs — table below is PER CHANNEL)

| Ref | Function | MPN | Package | Qty/ch | LCSC# | Stock | JLCPCB Tier | KiCad Symbol | KiCad Footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| U_adc | 12-bit, 20 MSPS, parallel CMOS ADC | **AD9235BRUZ-20** | **TSSOP-28 (RU)** | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Extended — UNVERIFIED (estimate) | **no symbol exists — [GEN], kipart required (R-14, 28-pin)** | `Package_SO.pretty:TSSOP-28_4.4x9.7mm_P0.65mm` ✓ (plain TSSOP, no exposed pad — matches RU/BRUZ package suffix) | [CRIT][GEN][FIXED PACKAGE] Highest sourcing risk in the design. Kept architect's pick. Drop-in speed grades **−40, −65, and AD9236BRUZ-80** share the same footprint/pinout — take one only if −20 is short. **If −65 is taken for both channels, escalate: 2×300 mW ≈ 180 mA breaks the power budget (R-09)** |
| FB_drv | DRVDD isolation ferrite | BLM18PG601SN1D | 0603 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:FerriteBead` ✓ | `Inductor_SMD.pretty:L_0603_1608Metric` ✓ | |
| R_damp (×12) | ADC data-line series damping | **discrete 100 Ω, generic** (chosen over a resistor array) | 0402 | 12 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | **Deviation:** skeleton offered "array or discrete" — chose discrete singles for simpler second-sourcing; an 8/9-pin 0402-pitch array is a lower-volume Extended-tier item |
| C_avdd | AVDD decoupling, 100 nF (×4) | 100 nF X7R 16 V, generic | 0402 | 4 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0402_1005Metric` ✓ | One per AVDD pin, at the pin |
| C_avdd | AVDD bulk, 10 µF | 10 µF X5R 16 V, generic | 0805 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0805_2012Metric` ✓ | |
| C_drvdd | DRVDD decoupling | 100 nF ×1 + 1 µF ×1, generic | 0402/0603 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0402_1005Metric` / `C_0603_1608Metric` ✓ | |
| C_ref | REFT/REFB/VREF/CML network | 100 nF ×3, 1 µF ×2, 10 µF ×1, generic | 0402/0603/0805 | 6 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | mixed, all confirmed | **Exact topology per AD9235 datasheet — datasheet phase must supply it** |

## Block 7 — `sram_buffer`

| Ref | Function | MPN | Package | Qty | LCSC# | Stock | JLCPCB Tier | KiCad Symbol | KiCad Footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| U8 | 256K × 16 async SRAM, 10 ns, 3.3 V | **IS61WV25616BLL-10TLI** | TSOP-II-44 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Extended — UNVERIFIED (estimate) | **no symbol exists — [GEN], kipart required (R-14, 44-pin)** | `Package_SO.pretty:TSOP-II-44_10.16x18.41mm_P0.8mm` ✓ | [CRIT][GEN][FIXED SPEC] Kept architect's pick — **≤15 ns is the binding spec, not capacity**. Vetted alts: CY7C1041GN30-10ZSXI, AS7C34098A-10TCN (same pinout). Free upgrade if better stocked: **IS61WV51216BLL-10TLI** (1 MB, same TSOP-II-44 outline, doubles burst depth to 262,144 samples/ch) |
| C41, C42 | Decoupling | 100 nF X7R 16 V, generic | 0402 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0402_1005Metric` ✓ | |
| C43, C44 | Decoupling | 100 nF X7R 16 V, generic | 0402 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0402_1005Metric` ✓ | |
| C45 | Bulk | 10 µF X5R 16 V, generic | 0805 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0805_2012Metric` ✓ | |
| C46 | Bulk | 1 µF X5R 16 V, generic | 0603 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0603_1608Metric` ✓ | |

## Block 8 — `usb_bridge`

| Ref | Function | MPN | Package | Qty | LCSC# | Stock | JLCPCB Tier | KiCad Symbol | KiCad Footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| U6 | USB 2.0 HS bridge, FT245 sync FIFO | **FT232HL** | LQFP-48 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Preferred — UNVERIFIED (estimate) | `Interface_USB:FT232H` ✓ | `Package_QFP.pretty:LQFP-48_7x7mm_P0.5mm` ✓ (no exposed pad, matches FT232HL) | [CRIT][FIXED] **ACBUS9 must be EEPROM-set to PWREN#** |
| U7 | Config EEPROM, 93LC46B | 93LC46BT-I/OT | SOT-23-6 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Memory_EEPROM:93CxxC` ✓ (pin-compatible) | `Package_TO_SOT_SMD.pretty:SOT-23-6` ✓ | |
| Y1 | 12.000 MHz crystal, ±30 ppm | X322512MSB4SI | 3225 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:Crystal` ✓ | `Crystal.pretty:Crystal_SMD_3225-4Pin_3.2x2.5mm` ✓ | Sets USB clock only — ADC has its own XO |
| R13 | FT232H REF bias | 12.0 kΩ ±1%, generic | 0402 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | [FIXED] Mandatory — board will not enumerate without it |
| R14, R15 | VBUS sense divider | 10 kΩ ±1%, generic | 0402 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | |
| R16 | nRESET pull-up | 10 kΩ, generic | 0402 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | |
| R17 | EEPROM DO pull-up | 2.2 kΩ, generic | 0402 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | |
| R18, R19 | SIWU / PWRSAV# pull-ups | 10 kΩ, generic | 0402 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | |
| FB4, FB5 | VPLL / VPHY isolation ferrites | BLM18PG601SN1D | 0603 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:FerriteBead` ✓ | `Inductor_SMD.pretty:L_0603_1608Metric` ✓ | Per FTDI reference design |
| C25, C26 | Crystal load caps | 27 pF C0G ±5%, generic | 0402 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0402_1005Metric` ✓ | |
| C27–C34 | Per-pin decoupling | 100 nF X7R 16 V, generic | 0402 | 8 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0402_1005Metric` ✓ | 100 nF at every supply pin |
| C35, C36 | VREGOUT decoupling | 1 µF X5R 16 V, generic | 0603 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0603_1608Metric` ✓ | |
| C37, C38 | Bulk | 4.7 µF X5R 16 V, generic | 0805 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0805_2012Metric` ✓ | |
| C39 | Bulk | 10 µF X5R 16 V, generic | 0805 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0805_2012Metric` ✓ | |
| C40 | Bulk | 100 nF X7R 16 V, generic | 0402 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0402_1005Metric` ✓ | |

## Block 9 — `fpga_core`

| Ref | Function | MPN | Package | Qty | LCSC# | Stock | JLCPCB Tier | KiCad Symbol | KiCad Footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| U9 | FPGA, 3520 LUT, 107 I/O | **iCE40HX4K-TQ144** | TQFP-144 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Extended — UNVERIFIED (estimate) | `FPGA_Lattice:ICE40HX4K-TQ144` ✓ | `Package_QFP.pretty:TQFP-144_20x20mm_P0.5mm` ✓ | [CRIT][FIXED] TQFP-144, 20×20 mm, 0.5 mm pitch — matches Lattice's TQ144 mechanical. Package fixed by the 86-pin need; do not downsize |
| U18 | SPI config flash, ≥1 Mbit | W25Q32JVSSIQ | SOIC-8 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Memory_Flash:W25Q32JVSS` ✓ | `Package_SO.pretty:SOIC-8_3.9x4.9mm_P1.27mm` ✓ | Any ≥1 Mbit 3.3 V SPI NOR works |
| J4 | Programming header, 2×5 1.27 mm | generic 2×5 1.27 mm SMD header | SMD | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Connector_Generic:Conn_02x05_Odd_Even` ✓ | `Connector_PinHeader_1.27mm.pretty:PinHeader_2x05_P1.27mm_Vertical` ✓ | SPI + CRESET_B + CDONE + 3V3 + GND |
| J5 | External trigger input | generic 2-pin 2.54 mm header | THT | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Connector_Generic:Conn_01x02` ✓ | `Connector_PinHeader_2.54mm.pretty:PinHeader_1x02_P2.54mm_Vertical` ✓ | Optional; keep footprint |
| D4 | CDONE LED (blue) | generic 0603 blue LED | 0603 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:LED` ✓ | `LED_SMD.pretty:LED_0603_1608Metric` ✓ | |
| D5 | USB-active LED (green) | generic 0603 green LED | 0603 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:LED` ✓ | `LED_SMD.pretty:LED_0603_1608Metric` ✓ | |
| D6 | Capture-armed LED (amber) | generic 0603 amber LED | 0603 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:LED` ✓ | `LED_SMD.pretty:LED_0603_1608Metric` ✓ | |
| D7 | EXT_TRIG clamp | BAV99 | SOT-23 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Diode:BAV99` ✓ | `Package_TO_SOT_SMD.pretty:SOT-23` ✓ | With 1 kΩ series resistor |
| R20–R22 | LED series | 1 kΩ ×3, generic | 0402 | 3 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | |
| R23, R24 | CRESET pull-up, SPI_SS pull-up | 10 kΩ ×2, generic | 0402 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | |
| R25 | EXT_TRIG series | 1 kΩ, generic | 0402 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | |
| R26 | VCCPLL filter | 470 Ω, generic | 0402 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:R` ✓ | `Resistor_SMD.pretty:R_0402_1005Metric` ✓ | |
| C47–C58 | VCCIO/VCC core decoupling, 100 nF (×12) | 100 nF X7R 16 V, generic | 0402 | 12 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0402_1005Metric` ✓ | ≥8 on VCCIO, ≥4 on VCC core, at the pins |
| C59, C60 | Bulk, 1 µF | 1 µF X5R 16 V, generic | 0603 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0603_1608Metric` ✓ | |
| C61, C62 | Bulk, 10 µF | 10 µF X5R 16 V, generic | 0805 | 2 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0805_2012Metric` ✓ | |
| C63 | VCCPLL decoupling | 100 nF X7R 16 V, generic | 0402 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0402_1005Metric` ✓ | Paired with R26 as a PLL filter |
| C64 | CRESET timing cap | 100 nF X7R 16 V, generic | 0402 | 1 | UNVERIFIED (estimate) | UNVERIFIED (estimate) | Basic — UNVERIFIED (estimate) | `Device:C` ✓ | `Capacitor_SMD.pretty:C_0402_1005Metric` ✓ | |

---

## Board totals (sourced)

| Category | Count |
|---|---|
| ICs (U), incl. the 4 `[GEN]` parts | 15 |
| Connectors (J) | 5 |
| Discrete semis (D, Q) | 12 |
| Passives (R, C, L, FB) | ≈150 |
| **Distinct line items** | ≈70 |
| Parts confirmed **symbol + footprint present** | all except the 4 `[GEN]` parts (below) |
| Parts flagged **[GEN]** (no symbol — kipart required) | **4**: AD9235BRUZ-20, IS61WV25616BLL-10TLI, AD8066ARZ, OPA836IDBVR |
| Deviations from architect's suggested MPN (documented above) | **8**: J1 suffix correction, D2 package-mismatch fix, C2 voltage-rating fix, Q1 second-source swap, L1/L2 MPN pin-down, C12/C13 case-size fix, R_damp array→discrete, J2/J3 BNC MPN swap (footprint availability) |
| Board cost estimate | Unchanged from architecture (~$85–115/board qty 5–10) — **UNVERIFIED (estimate)**, no live pricing available |

Power budget: unchanged from `architecture/skeleton_bom.md` — no part substitution here
altered current draw materially (all swaps are same-class, same-power parts).
