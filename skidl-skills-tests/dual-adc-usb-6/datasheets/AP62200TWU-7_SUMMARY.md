# AP62200TWU-7 — 4.2–18V, 2A Synchronous Buck Converter (KEYSTONE, power, U3/U4)

Replaces `SY8089AAC` (rev.3 re-source — SY8089AAC was NRND at Silergy, no datasheet
obtainable, failed SPEC R4; see `## Unverified keystone facts` history). Datasheet
obtained by the sourcer and read in full this pass: `datasheets/AP62200TWU-7.pdf`
(Diodes Incorporated DS41957 Rev. 6-2, "AP62200/AP62201/AP62200T, 4.2V TO 18V INPUT, 2A
LOW IQ SYNCHRONOUS BUCK CONVERTER", July 2023, 23pp — verified exact part match via the
Ordering Information table, p.20: `AP62200TWU-7` = TSOT26 (Standard) package, PFM/PWM
operation mode, VFB = 0.763 V, package code `WU`, marking `TN`).

**Two instances (U3, U4): +3V3D and +1V2**, same MPN, different FB-divider resistors set
the two output voltages (see Load-bearing facts).

| Spec | Value |
|------|-------|
| Package | TSOT26 (Standard), 6-pin — KiCad footprint `Package_TO_SOT_SMD:TSOT-23-6` per `sourced_bom.md` |
| Vcc / Vin range | 4.2 V to 18 V (VIN). Recommended Operating Condition VOUT: 0.8–7.0 V |
| Key output spec | 2 A continuous output, COT (constant on-time) control, PFM at light load, 750 kHz switching (VIN=12V, VOUT=5V, CCM) |
| Max current / power | High-side FET 90 mΩ, low-side FET 65 mΩ (integrated); valley current limit 2.0–2.8 A |
| Operating temp | −40°C to +125°C (junction) |

## Pinout (TSOT26, Standard, Top View)
| Pin | Name | Function |
|-----|------|----------|
| 1 | GND | Power ground |
| 2 | SW | Switching node — power output to the output LC filter |
| 3 | VIN | Power input, 4.2–18 V, bypass to GND close to the pin |
| 4 | FB | Feedback sense input — connect to the resistive divider tap |
| 5 | EN | Enable input, active-high, 1.2 V typ threshold; internal 1.5 µA pull-up to VCC auto-enables if left floating |
| 6 | BST | High-side gate-drive bootstrap — 100 nF cap required from BST to SW (330 nF if VOUT > 3 V) |

**Verified** directly from the downloaded PDF's "Pin Descriptions" table (p.3) and pin
assignment diagram — TSOT26 column: VIN=3, SW=2, GND=1, BST=6, EN=5, FB=4. Cross-checked
against the pin-assignment figure's Top View pin order (1=GND, 2=SW, 3=VIN, 4=FB, 5=EN,
6=BST) — identical, both read from the same primary document.

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Feedback reference VFB (this exact part, the "T" sub-variant) | **0.763 V typ**, full temp range 0.747–0.778 V (0.755–0.770 V at TA=25°C, CCM) | datasheet p.5, Electrical Characteristics table, row "AP62200T: CCM" / "AP62200T: TA=+25°C, CCM" — **verified**. Note: the base AP62200/AP62201 (non-T) parts in the same datasheet family are **0.800 V** — do not use that figure for this MPN |
| EN pin polarity and behavior | Active-high. VEN_H (logic-high threshold, turn-on) = 1.20 V typ / 1.25 V max. VEN_L (logic-low, turn-off) = 1.04 V min / 1.10 V typ. An **internal 1.5 µA pull-up current source from the internal LDO-regulated VCC to EN** means a floating EN pin auto-enables the device once its own VIN/VCC rail is up — EN is NOT a safe "leave it disconnected to keep it off" pin | datasheet p.5 (Electrical Characteristics, VEN_H/VEN_L/IEN rows) and p.13 §3 "Enable" — **verified**: "An internal 1.5µA pull-up current source connected from the internal LDO-regulated VCC to the EN pin guarantees that if EN is left floating, the device still automatically enables once the voltage reaches the EN logic high threshold." |
| BST bootstrap requirement | 100 nF ceramic cap from BST to SW (mandatory for high-side FET drive); use 330 nF if VOUT > 3 V — applies to the +3V3D instance (VOUT ≈ 3.3 V), 100 nF is acceptable for +1V2 | datasheet p.18 §13 "Bootstrap Capacitor" — **verified** |
| FB divider values (from sourcing, cross-checked against datasheet Table 1 methodology) | **+3V3D instance: R_top=33.2 kΩ, R_bot=10.0 kΩ → VOUT ≈ 3.296 V.** **+1V2 instance: R_top=5.76 kΩ, R_bot=10.0 kΩ → VOUT ≈ 1.202 V.** Both computed from R1 = R2·(VOUT/VFB − 1), Eq. 8, using VFB=0.763V | `sourced_bom.md` (sourcer's figures) — **verified against datasheet Eq. 8 and Table 1** (Table 1's R1 values for 3.3V/AP62200T = 33.2kΩ and closest tabulated row for ~1.2V is not directly listed, but the sourcer's 5.76kΩ/10.0kΩ pair independently satisfies Eq. 8 for VOUT=1.2V, VFB=0.763V: R1 = 10k·(1.2/0.763 − 1) = 5.75kΩ ≈ 5.76kΩ — **recomputed and confirmed correct this pass**) |
| Rail sequencing (EN wiring, from architecture) | `+1V2` instance: EN tied **directly to VBUS_SW** (no delay — comes up first). `+3V3D` instance: EN driven through an **R18 (100 kΩ) / C22 (100 nF) RC delay ≈ 2.74 ms** (comes up second) — i.e. **FPGA core (+1V2) leads I/O rail (+3V3D)** by design | `handoffs/02_architecture.md` decision #12, `sourced_bom.md` R18 note — **verified as the existing architecture decision**, not re-derived this pass. See Notes below for an interaction this part's internal EN pull-up has with that RC network |
| VIN margin vs. USB VBUS worst case | VIN range 4.2–18 V vs. architecture's 4.4 V worst-case USB VBUS droop figure — **only 0.2 V margin**, tighter than SY8089AAC's 2.7–5.5 V range | `sourced_bom.md` sourcer's note — **carried forward as a flagged risk**, not re-verified against USB-PD/VBUS-drop specifics this pass |

## Notes
- **EN pull-up interacts with the +3V3D RC sequencing delay.** The internal 1.5 µA EN
  pull-up sources current onto the EN node in addition to whatever the external R18/C22
  network drives. For the `+1V2` instance (EN tied directly to VBUS_SW, a low-impedance
  rail) this pull-up is irrelevant. For the `+3V3D` instance (EN driven through a 100 kΩ/
  100 nF RC from VBUS_SW), the extra 1.5 µA adds to the RC charging current on C22,
  which will make the **actual EN turn-on delay somewhat shorter than the simple-RC 2.74 ms
  figure** computed in architecture (which likely assumed pure RC charging with no internal
  current source). The direction of the correction (faster, not slower) does not break the
  "+1V2 leads +3V3D" ordering, but the coder/reviewer should not treat 2.74 ms as exact —
  it is an upper bound, not the real number. Not recomputed here (would need the RC network's
  exact topology — is R18 from VBUS_SW to EN with C22 EN-to-GND, per the typical Eq. 3
  delay-cap arrangement — confirm against `net_plan.md` before relying on a specific number
  in phase 5).
- **R10–R13 in `sourced_bom.md` still hold stale SY8089A-era divider values (VFB=0.6V
  assumption)** per the sourcer's own note — these **must** be replaced with the
  AP62200TWU-7 divider pairs above (33.2 kΩ/10.0 kΩ for +3V3D, 5.76 kΩ/10.0 kΩ for +1V2)
  before the `power` block is coded. This is carried forward as a required fix, not
  optional.
- Both instances need an inductor (per Table 1: 3.3 µH for +3V3D, sized per Eq. 9/Table 1
  row nearest 1.2V for +1V2 — check `sourced_bom.md`/`net_plan.md` for the actual chosen
  inductor MPN, not re-derived here), an input cap (≥10 µF ceramic, low ESR), and an output
  cap (2×22 µF per Table 1, or per Eq. 11/12 sizing) — standard COT buck application circuit
  per datasheet Figure 1.
- VOUT range 0.8–7.0 V per Recommended Operating Conditions is **above** the AP62200T
  variant's own VFB (0.763V) minimum achievable VOUT — not a conflict, since VOUT is set by
  the external divider ratio, not by VFB directly; 1.2V and 3.3V are both comfortably inside
  range.
- Symbol generated this pass: `dual_adc_usb:AP62200TWU-7` in
  `symbols/dual_adc_usb.kicad_sym`, verified `EXACT` via `find-symbol.py`. Pin
  types/sides: VIN=power_in/left, FB=input/left, EN=input/left, SW=output/right,
  BST=passive/right, GND=power_in/bottom.
