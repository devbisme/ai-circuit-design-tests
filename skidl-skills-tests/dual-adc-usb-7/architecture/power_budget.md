# Power budget — rail by rail

Answers `01_requirements.md` § Next phase must, item 6, and closes the carried-forward
question "behaviour on a 500 mA (legacy A-to-C) source".

All currents referred to the **5 V VBUS input**. Buck efficiency taken as 85 % (TLV62569 at
100–300 mA, 1.5 MHz); LDO and ferrite paths pass current 1:1.

## Rails

| Rail | Source | Loads | Rail current (nom / max) | VBUS current (nom / max) |
|---|---|---|---|---|
| `P1V2` | U11 TLV62569 buck | GW1NR-9 core | 120 / 200 mA @1.2 V | 34 / 56 mA |
| `P3V3D` | U10 TLV62569 buck | U5 VCCX (5/12 mA), U5 VCCIO1+VCCIO2 (10/20 mA), **U14 1.8 V LDO input (20/100 mA)**, ADS5231 VDRV (10/15 mA), 10 MHz XO (10/15 mA), LEDs (6 mA), EEPROM+misc (5/8 mA) | 66 / 176 mA @3.3 V | 51 / 137 mA |
| **`P1V8`** (new) | U14 LDO from `P3V3D` | U5 VCCIO3 = BANK3 = the embedded-PSRAM bank (pin 12 only) | 20 / 100 mA @1.8 V | (counted in `P3V3D`) |
| `P3V3A` | U12 RT9013-33 LDO | ADS5231 AVDD (65 mA), 2× THS4521 (2.3 mA) | 67 / 100 mA @3.3 V | 67 / 100 mA |
| `VA_POS` (+5 V) | ferrite FB1 from VBUS_SW | AD8066 (13.2 mA) + TPS60403 input (15 mA) | 28 / 33 mA | 28 / 33 mA |
| `VA_NEG` (−4.7 V) | U13 TPS60403 from VA_POS | AD8066 negative rail | 13.2 / 18 mA | (counted in VA_POS) |
| `VBUS` direct | — | FT232HL (always on, ahead of the load switch) | 70 / 90 mA | 70 / 90 mA |
| `VBUS` direct | — | regulator + switch quiescent, pull-ups | 5 / 8 mA | 5 / 8 mA |
| **Total** | | | | **255 mA (1.28 W) / 424 mA (2.12 W)** |

<!-- revised: rev.2 — P1V8 rail added; P3V3D re-itemised in place of the old 100 mA FPGA lump -->

Arithmetic for the converted rails:
- `P1V2`: 120 mA × 1.2 V = 144 mW → 144 mW / (5 V × 0.85) = **33.9 mA** from VBUS.
- `P3V3D`: 66 mA × 3.3 V = 218 mW → 218 mW / (5 V × 0.85) = **51.2 mA** from VBUS (worst case
  176 mA × 3.3 V / 4.25 V = **136.7 mA**).
- **Honest note on the drop from 306 → 255 mA typical:** none of it is an efficiency gain. The
  old row carried a single conservative 100 mA lump for "FPGA VCCIO+VCCX & PSRAM"; that lump is
  now itemised (VCCX 5 mA from DS117 Table 3-9 ICCX, VCCIO1/2 10 mA, PSRAM rail 20 mA) and adds
  to 35 mA. **The binding number is the worst case, and it barely moved: 427 → 424 mA.**

### `P1V8` rail sizing — from the PSRAM's own burst current, not a guess

The 64 Mbit embedded memory is 2 × 32 Mbit x8 self-refresh DRAM dies (DS117 §2.2.2), i.e. two
HyperRAM-class 1.8 V dies driven as x16.

- **Burst (peak):** 2 dies × 30 mA active-read/write = **60 mA**.
- **BANK3 VCCIO dynamic**, internal die-to-die interface: 16 DQ + CK + CK# + RWDS + CS# ≈ 20
  nets × 2 pF bond capacitance × 1.8 V × 50 MHz (100 MHz DDR ⇒ 50 MHz equivalent toggle)
  = 20 × 2 pF × 1.8 V × 50 MHz = **3.6 mA**.
- **ICCIO static:** 2 mA (DS117 Table 3-9, GW1NR-9).
- **Peak total = 60 + 3.6 + 2 = 65.6 mA.** Specified ceiling **100 mA**, which covers running
  the interface at 166 MHz instead of 100 MHz (≈45 mA/die).
- **Typical:** the required write bandwidth is 2 ch × 2 B × 10 MSPS = 40 MB/s against
  400 MB/s available (x16 DDR @100 MHz) ⇒ **10 % bus duty**. 0.10 × (60 + 3.6) + 2 mA
  self-refresh + 2 mA ICCIO = 10.4 mA → budgeted **20 mA** typical.

### `P1V8` topology — LDO from `P3V3D`, not a third buck

| Option | VBUS cost @100 mA | Parts | Verdict |
|---|---|---|---|
| **LDO from `P3V3D`** | 100 mA × 3.3 V / 4.25 V = **77.6 mA** | 1 IC + 3 caps | **Selected** |
| LDO from `VBUS_SW` (5 V) | **100 mA** direct, 320 mW dissipated | 1 IC + 3 caps | Loses: 22 mA worse and 2× the heat |
| Third TLV62569 buck from `VBUS_SW` | 100 mA × 1.8 V / 4.25 V = **42 mA** | 1 IC + inductor + 2 R + 4 C | Loses: saves 36 mA the budget does not need, and puts a third 1.5 MHz switch node on a 12-bit instrument board (risk R-2) |

- **LDO dissipation:** (3.287 − 1.800) V × 0.100 A = **148.7 mW**. SOT-23-5 θ_JA ≈ 250 °C/W ⇒
  ΔT = 37 °C; at 70 °C ambient T_j = **107 °C**, inside a 125 °C T_j part. At the 20 mA typical
  load it is 29.7 mW ⇒ ΔT = 7 °C.
- **Ramp rate is a hard spec, not a preference.** DS117 Table 3-3: VCCIO ramp 0.1–10 mV/µs,
  monotonic. 1.8 V / 10 mV/µs ⇒ the output must take **≥180 µs** to reach regulation. A big
  output cap will not fix a fast regulator: at a 500 mA-class LDO's current limit,
  dV/dt = I/C = 0.5 A / 4.7 µF = 106 mV/µs, so the ramp is set by the internal soft-start.
  **"Built-in soft-start with t_on ≥ 180 µs" is therefore a sourcing requirement.**
- Sequencing: `P1V8` is derived from `P3V3D`, so VCCIO3 is the **last** rail up. That is why
  MODE0/MODE1 are strapped to **GND** (R54/R55) and not to a rail — a logic 0 is valid before
  VCCIO3 exists. Cross-check on the existing rails: TLV62569 soft-start ≈1 ms ⇒
  3.3 V / 1 ms = 3.3 mV/µs ✓ and 1.2 V / 1 ms = 1.2 mV/µs ✓, both inside the same window.
- `P3V3A` LDO dissipation: (5 − 3.3) V × 67 mA = **114 mW** (SOT-23-5, ~250 °C/W → +29 °C rise; acceptable at 70 °C ambient).
- `VA_NEG` level: TPS60403 R_out 15 Ω → −5 V + (13.2 mA × 15 Ω) = −4.80 V; post-filter R76 = 4.7 Ω
  drops a further 13.2 mA × 4.7 Ω = 62 mV → **−4.74 V**. AD8066 total supply = 5.0 + 4.74 =
  **9.74 V**, inside its 5–24 V range. Its input CM limit is (V+) − 2.5 V = **+2.5 V**, and the
  buffer input never exceeds ±0.909 V in range (±5 V at the ±55 V clamp limit, still inside
  the ±10 V abs-max) ✓.

## Against the constraints

| Constraint | Value | Result |
|---|---|---|
| `[HARD]` ≤ 1.5 A @5 V | 255 mA nom, 424 mA worst | ✅ 3.5× margin (28 % of the ceiling) |
| design target ≤ 1.0 A | 255 mA | ✅ 26 % of target |
| `[HARD]` pre-enumeration ≤ 150 mA | FT232HL 90 mA + quiescent 8 mA = **98 mA** | ✅ unchanged — U14 sits on `P3V3D`, behind U9 |
| **Legacy A-to-C source, 500 mA** | 424 mA worst case | ✅ **fits, with 76 mA (15 %) margin** |

### Explicit answer on the 500 mA legacy source

**The answer is unchanged by the new rail: the design still fits inside 500 mA; no
current-capability detection, CC sensing or load-shedding mode is implemented.** The board draws
255 mA typical / 424 mA worst case (was 306 / 427), so a legacy
A-to-C cable (Rp = default, 500 mA) powers it fully. Type-C with 5.1 kΩ CC pulldowns is kept
because requirement 8 is `[HARD]` and listed under "do not redo" — but note honestly that the
budget that originally justified it (>2.5 W) did not materialise: the real draw is 1.5 W, which
a Type-B port would also have carried. The Type-C receptacle is now margin, not necessity.
Do not re-open it; re-deciding the connector costs a cycle and buys nothing.

### Inrush and sequencing

- Always-on section (FT232HL) carries ≤ 10 µF of bulk capacitance, per the USB inrush limit.
- All other bulk (≈ 60 µF) sits behind U9 (TPS22918), whose CT pin sets the ramp.
  With C_T = 1 nF the output ramp is ≈ 2 ms: I_inrush = 60 µF × 5 V / 2 ms = **150 mA**,
  which occurs *after* enumeration where the budget is 500 mA ✓.
- U9 conduction loss: 0.33 A² × 53 mΩ = 5.8 mW, drop 17.5 mV ✓.

### Load-switch enable — gate drive, both states, both threshold extremes

FT232HL ACBUS9 = PWREN# (EEPROM-configured), 3.3 V logic, **active low after enumeration**.
TPS22918 EN is **active high**, so one inverting stage is required: Q1 = BSS138 (logic-level,
V_GS(th) 0.8 V min / 1.5 V max), R71 = 100 kΩ pull-up to P3V3D.

| State | PWREN# | V_GS(Q1) | Q1 | EN node | Switch |
|---|---|---|---|---|---|
| Pre-enumeration | 3.3 V | +3.3 V — overdrive ≥ 3.3 − 1.5 = **1.8 V** even at the max threshold | ON, R_DS(on) ≈ 3.5 Ω | 33 µA × 3.5 Ω = **0.1 mV** ≤ V_IL 0.4 V | **OFF** ✓ |
| Enumerated | 0 V | 0 V — below the **0.8 V minimum** threshold | OFF, ≤1 µA | 3.3 V − (2 µA × 100 kΩ) = **3.1 V** ≥ V_IH 1.05 V | **ON** ✓ |

A P-FET driven directly from 3.3 V logic was rejected: with its source at VBUS, a 3.3 V gate
gives V_GS = −1.7 V, which is inside the threshold window of most P-FETs — the switch would
never fully turn off.

### Buck feedback dividers (computed from the TLV62569 0.6 V reference, not a family default)

- 3.3 V rail: R72 = 180 kΩ (FB→VOUT), R73 = 40.2 kΩ (FB→GND), both E96 1 %.
  V_OUT = 0.600 × (1 + 180/40.2) = 0.600 × 5.4776 = **3.287 V** (−0.4 %), divider current 14.9 µA.
- 1.2 V rail: R74 = R75 = 100 kΩ. V_OUT = 0.600 × (1 + 100/100) = **1.200 V** (exact).
- Inductor, both rails: 2.2 µH. Ripple on the 3.3 V rail:
  ΔI = (5 − 3.287) × 0.657 / (2.2 µH × 1.5 MHz) = **0.34 A pk-pk**; with 22 µF out,
  ΔV = 0.34 / (8 × 1.5 MHz × 22 µF) = **1.3 mV** ✓.
- ⚠ The 0.6 V reference is taken from the TLV62569 output range (600 mV … 5.5 V) and TI's
  TLV6256x family feedback voltage. **Datasheet phase must confirm V_FB before layout** —
  a wrong V_FB here puts 4.4 V onto 3.3 V parts.
