# dual_adc_usb Design Review

**Project:** dual_adc_usb (KiCad 10.0.4; 9 sheets, i.e. root + 8 subcircuits; 4-layer PCB, 130 × 90 mm)
**Date:** 2026-10-09
**Analyzers run:** kicad-happy 2.3.1, all from run folder `analysis/2026-10-09_1309/`:
- `analyze_schematic.py`
- `analyze_pcb.py --full`
- `cross_analysis.py`
- `analyze_emc.py`
- `analyze_thermal.py`
- `analyze_gerbers.py`
- `simulate_subcircuits.py` (ngspice)
- `lifecycle_audit.py` (LCSC only)

KiCad's own ERC and DRC (`--schematic-parity`) were also run.

## Verdict
**The prototype is buildable, but not ready to order yet.** The board is complete and consistent:
- KiCad ERC: 0 violations.
- DRC: 0 errors, 0 unconnected, 0 schematic-parity issues.
- 100 % MPN coverage.
- The SKiDL netlist and the schematic netlist are identical.

Three things must happen before fabrication:
1. The two critical ICs (LTC2291, FT2232H) have to be checked against their datasheets. They couldn't be downloaded here.
2. Someone has to accept the 0.1 mm / 0.1 mm "Fine" rule on the ADC bus. It needs an advanced fab process.
3. Someone has to accept the EMC trade-offs of the 2-signal-layer stackup listed below.

## Critical Findings
| Severity | Issue | Section |
|---|---|---|
| WARNING (verification gap) | LTC2291 and FT2232H pin functions, reference/VCM bypass network, MODE/SENSE levels, REF resistor and EEPROM wiring all come from KiCad symbols plus memory. The datasheets were unavailable (analog.com timed out, ftdichip.com returned 403). | [Verification basis](#verification-basis) |
| WARNING | ADC data bus uses a 0.1 mm track / 0.1 mm space net class; the minimum measured spacing is 0.118 mm. That needs an "advanced" process tier (JLCPCB 4-layer allows 0.09 mm). | [PCB](#pcb-layout) |
| WARNING | EMC pre-compliance risk is high (analyzer score 1/100). The drivers are structural: signals switch reference between the In1 GND and In2 +3V3 planes at vias, and all clocks run on outer layers. | [EMC](#emc--cross-domain) |
| WARNING | The anti-alias filter is only 2nd order (−3 dB ≈ 4–5 MHz), so content above 5 MHz will alias with little attenuation. | [Signal](#signal-chain-review) |
| WARNING | USB D+/D− are short (about 10 mm), but they aren't impedance-controlled and D− has one via. The board stackup has no impedance spec. | [PCB](#pcb-layout) |

No CRITICAL (won't-work) issues were found by the analyzers or by manual review. "Not found" isn't the same as "absent", though: see the verification gaps.

## Component Summary
| Type | Count |
|---|---|
| ICs | 15 |
| Resistors | 52 |
| Capacitors | 104 |
| Connectors | 4 (2 BNC, USB-B, 2×5 header) |
| Crystal/oscillators | 3 |
| LEDs | 3 |
| Diodes | 2 |
| Inductor / ferrites / fuse | 1 / 2 / 1 |

- 210 nets, 38 no-connects, 61 BOM lines, MPN on every line.
- Passive MPNs (Yageo RC/RT, Murata GRM) are generic suggestions. Check voltage derating when ordering.

## Power Tree
```
USB VBUS 5V ─ F1 500mA PTC ─ FB1 ─ +5V ──┬─ U1 TLV62569 buck ─ L1 2.2µH ─ +3V3 (digital, In2 plane)
                                          │      FB 453k/100k → 3.318 V (SPICE ✓)
                                          │      └─ U2 AP2112K-1.2 LDO ─ +1V2 (FPGA core)
                                          │                         └─ 100Ω+10µ+100n ─ VCCPLL0/1 (GNDPLL isolated)
                                          ├─ U3 LP5907-3.3 LDO ─ +3V3_ADC (LTC2291 VDD, THS4521 ×2)
                                          └─ U4 LM27762 (EN = ANA_EN from FPGA, 100k pull-down)
                                                 ├─ OUT+ 174k/100k → +3.288 V  (+3V3A)  SPICE ✓
                                                 └─ OUT− 169k/100k → −3.282 V  (−3V3A)  SPICE ✓
```
- Feedback math was checked against the TLV62569 (Eq. 2) and LM27762 (Eq. 1, 3) datasheets in `datasheets/`.
- Estimated 5 V load is about 280 mA. That's inference: the LTC2291 and FT2232H currents are unverified. The USB 2.0 allowance is 500 mA.

## Verification Basis
- **Datasheet-verified** (PDFs in `datasheets/`):
  - TLV62569: VFB 0.6 V, L/C table, feed-forward capacitor.
  - LM27762: equations, R2/R4 ≥ 50 k, capacitor values, EN thresholds 1.2 V.
  - THS4521: pinout, 3.3 V input common-mode range −0.1 V to 1.9 V (the design runs at 0.5–1.0 V), PD polarity.
  - OPA810: supply 4.75–27 V, unity-gain stable.
  - iCE40 HX (FPGA-TN-02006 Table 2.1/3.1, FPGA-TN-02052 Fig 5.4, FPGA-DS-02029): VPP_2V5 = 3.3 V allowed for controller SPI, VPP_FAST left unconnected, 10 k config pull-ups, VCCPLL RC filter with GNDPLL not on board ground, PLL f_IN 10–133 MHz.
  - IS42S16400J: IDD4 100 mA, 4K refresh per 64 ms.
- **Raw-file verified:**
  - The kicad-cli netlist exported from the schematic matches SKiDL's netlist, 172/172 multi-pin nets (`scripts/compare_netlists.py`).
  - PCB pads match the schematic (DRC schematic parity is 0).
  - BAV99 pin roles were checked against the symbol graphics.
- **Analyzer-derived:** the SPICE results (33 pass, 2 warn): divider ratios, buck/LDO feedback, FDA feedback pole, crystal load.
- **Inference only (not verified):**
  - LTC2291: SENSE = VDD gives the 2 Vpp span; MODE = VDD/3 gives offset binary with the duty-cycle stabilizer on; REFH/REFL bypass (0.1 µF ∥ 2.2 µF across, 1 µF to GND each); VCM 2.2 µF; VDD range 2.7–3.4 V, and the board runs it at 3.3 V.
  - FT2232H: REF = 12 kΩ; VREGOUT → VCORE; 93LC56B with 2.2 k DI/DO; channel B pins BCBUS0–4 = RXF#/TXE#/RD#/WR#/SIWU.
  - ASE oscillator jitter is adequate for 12-bit sampling at 5 MHz input.

## Signal Chain Review
- **Input:** 909 k (0.1 %) / 100 k divider, Rin = 1.009 MΩ. C_top = 2.2 pF; C_bot = 10 pF plus a 3–10 pF trimmer; 15 pF shunt. That gives ≈20 pF input capacitance, which scope probes can compensate. SPICE gives a ratio of 0.0991 (✓). Calibrate the trimmer with a 1 kHz square wave.
- **Protection:** the BAV99 clamps to ±3V3A. The 909 k resistor limits fault current to about 0.11 mA per 100 V. Neither 0603 nor 1206 resistors are rated for mains-level transients. This isn't an isolated input.
- **Buffer and FDA:**
  - OPA810 unity buffer, then THS4521 with G = 953/1000 and VOCM = ADC VCM.
  - The ADC full scale (2 Vpp differential) corresponds to ±10.6 V at the BNC.
  - The FDA feedback pole is 953 Ω ∥ 22 pF = 7.6 MHz. The output RC is 2 × 49.9 Ω with 330 pF differential, 4.8 MHz.
  - **Combined −3 dB is about 4 MHz with 2nd-order roll-off: weak anti-aliasing.** Options:
    - (a) a 4th/5th-order LC filter;
    - (b) run the LTC2291 at 20 MSPS (it's a 25 MSPS part; change the XO) and decimate by 2 in the FPGA.
- **Clocking:** a dedicated 10 MHz XO goes directly to CLKA/CLKB through 22 Ω, and a separate 33 Ω tap feeds FPGA GBIN6. The 25 MHz XO feeds GBIN5 for the PLL (100 MHz SDRAM clock).
- **Capture depth:** 8 MB SDRAM / (2 ch × 2 B × 10 MS/s) = 0.2 s, against the 0.1 s requirement.
- **Host interface:** FT2232H.
  - Channel B async FIFO, about 8 MB/s, so a 4 MB capture uploads in about 0.5 s.
  - Channel A is wired iceprog-style (ADBUS0/1/2/4 SPI, ADBUS6 CDONE, ADBUS7 CRESET) for flash programming over USB.
- **FPGA pins:** the I/O assignment was optimized for routing by `scripts/pin_swap.py`. The gateware constraint file `gateware/dual_adc_usb.pcf` is generated from the final netlist.

## PCB Layout
- **Stackup:** F.Cu signal / In1 solid GND / In2 +3V3 plane / B.Cu signal. Signals are only allowed on F/B (DSN inner layers set to `power`).
- **Routing:** 1933 segments, 437 vias. Freerouting 2.4.1 did most of it. A small A* router (`scripts/astar_fix.py`) finished the last few links, with cost-based rip-up.
- **Net classes:**
  - Default 0.15/0.15 mm.
  - Power 0.3 mm.
  - **Fine 0.1/0.1 mm for DA*/DB*/OFA/OFB.** The QFN-64 top/bottom rows can't escape on two signal layers otherwise; several 0.15 mm attempts left 2–5 links unroutable.
  - Freerouting necks tracks down at fine-pitch pads; the board minimum width is 0.1 mm.
- **Planes:** every GND/+3V3 SMD pad has its own via (232 vias, `scripts/fanout.py`). Exposed pads get a via grid.
- **USB:**
  - The FT2232H is rotated so DM/DP face J1, with the USBLC6 flow-through in between.
  - D+/D− are pre-routed at 0.2 mm, about 10 mm each.
  - Not impedance-controlled. Specify 90 Ω differential with the fab, or accept the risk for this short run.
- **Fiducials:** 3 on F.Cu and 3 on B.Cu, because 29 decoupling capacitors sit on B.Cu under the FPGA, SDRAM and FT2232H. Assembly is double-sided.
- **Remaining DRC warnings (19):**
  - silkscreen: 8 edge-clearance (the BNC and USB bodies overhang the edge by design), 6 over copper, 4 overlap;
  - 1 `lib_footprint_mismatch` on J1. KiCad compares against the globally configured footprint library, which isn't the KiCad 10 copy used here.
- **PCB analyzer:**
  - PM-002 courtyard overhang on J1/J2/J3 is by design.
  - VP-001: 2 untented vias in pad (R47.2, U5.4). Ask for tented or plugged vias.
  - TV-001: U12 has 23 thermal vias against a heuristic minimum of 25, and U4 has 4 of 5. Both parts dissipate less than 0.2 W, so this is acceptable.
  - TE-001: there are no test points. The GPIO header provides +3V3/GND; add rail test pads in a revision.

## EMC / Cross-Domain
The analyzer reports 63 findings, score 1/100. The main drivers:
- **RP-001, 19 findings:** layer changes with no adjacent GND stitching via. Signals on B.Cu reference the +3V3 plane, so return current crosses between planes through the decoupling capacitors.
- **CK-001:** clocks on outer layers. With two signal layers, every signal is on an outer layer.
- **GP-001:** partial reference-plane gaps around via fields.
- **IO-001:** no filtering on the BNC inputs. These are analog inputs behind 909 k, so the filtering is effectively there.
- **SW-001:** buck harmonics in the 30–88 MHz band.

Mitigations, in order of value:
1. A 6-layer stackup (S/G/S/S/G/P) so every signal layer has an adjacent GND.
2. GND stitching vias next to signal vias.
3. 22–33 Ω series terminations on the SDRAM clock and FIFO strobes in a revision.
4. A ferrite/RC on the USB shield.

Cross-analysis: USB_DM/DP have 85–88 % reference-plane coverage, because of the plane voids near the connector.

## Thermal
- **TS-001 and TS-002 (U2 at 132 °C, U3 at 121 °C) are false positives.** The analyzer assumed near-rated LDO currents: about 204 mA on +1V2 and 226 mA on +3V3_ADC.
- Realistic loads are about 30–60 mA (iCE40HX4K core) and about 70 mA (ADC plus FDAs). That's 0.06–0.13 W, which puts Tj near 55–60 °C in SOT-23-5. This is inference, but conservative.
- Every other part dissipates less than 0.2 W.

## Manufacturing / DFM
- 4-layer board, 1.6 mm, 0.45/0.2 mm vias, minimum track 0.1 mm, minimum space 0.1 mm on the ADC bus (advanced tier).
- Double-sided SMT. The BOTTOM side holds 0603 capacitors only.
- **Gerber analyzer:** layers are complete; GR-004 (B paste only on the 29 bottom capacitors) is expected.
- **Fab outputs in `fab/`:** Gerbers and drill (zip), position CSV, grouped BOM CSV.

## False Positives / Reviewer Overrides
| Finding | Why it's benign |
|---|---|
| PP-001 VCCPLL0/1 | Fed from +1V2 through the 100 Ω filter resistor, as Lattice recommends. The analyzer doesn't treat resistors as a DC path. |
| PP-001 FT_VCORE | Supplied by the FT2232H's internal 1.8 V regulator (VREGOUT). |
| VM-001 ANA_EN / ANA_PG_N | The LM27762 EN threshold is 1.2 V and the pins tolerate up to VIN, so 3.3 V drive is correct. PGOOD is open-drain, pulled to 3.3 V. |
| RS-001 VBUS_F, VIN_A/B | VBUS_F is VBUS after the fuse; VIN_A/B are external inputs. |
| UC-001 VBUS at J1 | The bulk capacitance sits after the fuse and ferrite. A capacitor at the jack is optional; the total is kept under 10 µF for USB inrush. |
| SPICE warnings C32/C45 | These are the deliberate 15 pF input-capacitance shunts, not decoupling. |
| GP-005, 3 ground domains | GNDPLL0/1 are isolated from board ground by design (Lattice FPGA-TN-02052). |
| TS-001 / TS-002 | Current assumption; see the thermal section. |

## Not Performed / Review Limits
- **Datasheet verification of the LTC2291, FT2232H, W25Q32JV, 93LC56B, USBLC6, BAV99, AP2112K (partial) and the ASE XOs** wasn't done: no access, or not attempted. The pin-level claims for those parts are inference only.
- **Lifecycle audit:** effectively not performed. LCSC returns no lifecycle data, and there are no DigiKey/Mouser/element14 API keys.
- **Deep Review pass** (`deep_review.json` plus gate): not performed.
- **Prior-review delta:** not applicable (first review).
- **Signal integrity:** no simulation of SDRAM timing at 100 MHz or of the USB eye. No impedance stackup was specified.
- **Gateware and host software:** not written. The `.pcf` is provided.
