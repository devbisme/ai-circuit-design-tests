# ERC report — dual_adc_usb

**0 errors, 1 warning, 9 notes. Circuit is PASS.**

- Reviewer: erc-reviewer, 2026-09-11T11:24Z. Entry: `handoffs/05_coding.md` (modular, 9 blocks).
- Run: `KICAD9_SYMBOL_DIR="$KICAD_SYMBOL_DIR:$PWD/symbols" python3 -m circuits.dual_adc_usb` (exit 0; SKiDL 3.0.0, Python 3.14).
- Netlist: 201 parts, 168 nets. Footprints: `validate-footprints.py` found all valid (33 checked across 10 files).

## Raw output (complete)

```
ERC INFO: No errors or warnings found while running ERC.
WARNING: Missing tag on  instantiated at .../<frozen importlib._bootstrap>:491.
INFO: 1 warnings found while generating netlist.
INFO: 0 errors found while generating netlist.
INFO: 1 warnings found while generating XML.
INFO: 0 errors found while generating XML.
```

| Line | Class | Root cause | Disposition |
|---|---|---|---|
| ERC INFO: no errors/warnings | INFO | — | — |
| `Missing tag on  instantiated at <frozen importlib._bootstrap>:491` | WARNING | SKiDL's root hierarchy node: `Circuit.__init__` creates `Node(name="", tag="")` (`skidl/circuit.py:172`), and `check_tags()` then flags it. It is not a part or a block. | **False positive, accepted.** I checked the mechanism in the source. No design fix. The same warning is counted once by the netlist generator and once by the XML generator. |

## Findings, by severity

There are no CRITICAL, HIGH or MEDIUM findings. Everything below is LOW/INFO: a note for gateware, layout, documentation, or the SKiDL tool. None of it blocks export.

| # | Sev | Finding | Action |
|---|---|---|---|
| N1 | LOW | **Datasheet summaries contradict the primary sources (the netlist is correct).** (a) `GW1NR-LV9QN88PC6-I5_SUMMARY.md` puts pins 68–88 in Bank 0 and marks them unusable. UG119 Fig. 3-8 (p.15, rendered and checked against the p.7 colour legend) puts pins 68–77 in **Bank 1** (green) and 79–88 in **Bank 3** (orange). Table 2-6 gives Bank 0 zero bonded I/O in QN88P, and the counts match: B1 = 25, B2 = 23, B3 = 23. (b) `ADS5231IPAGT_SUMMARY.md` calls DVA (26) and DVB (22) "digital supply". SBAS295A p.12 says they are **Data Valid outputs**. | Correct both summaries so later reviewers are not misled. No circuit change. |
| N2 | LOW | **ADC_DVA direction.** U15.72 is BIDIR, and the fpga_core handoff calls it an output. U12.26 drives it (through RN7). | Gateware must make pin 72 an **input**. |
| N3 | LOW | **AAF is 2nd order.** From netlist values: Rf·Cf = 1 k·22 p gives 7.23 MHz, and 2·49.9 Ω·220 p gives 7.25 MHz. Combined −3 dB is **4.64 MHz** (F8: 4–5 MHz, ≥ 2nd order, met). Attenuation is −9.2 dB at 10 MHz and −14.5 dB at 15 MHz, the first band that aliases into 0–5 MHz at 20 MSPS. This is the architect's documented risk "M" (`design_risks.md`). | Accept. The half-band decimator in gateware handles 5–15 MHz. |
| N4 | LOW | **Which bank serves the PSRAM cannot be proven from the documents on disk.** DS117 §2.2.2 says the PSRAM's bank must be 1.8 V but does not name it for QN88P. The design's banks (B1 = B2 = 3.3 V, B3 = 1.8 V, VCCX/VCCIO0 = 3.3 V) are consistent with elimination: VCCIO0 shares pins with VCCX (≥ 2.375 V), so it cannot be 1.8 V. They also match the Sipeed Tang Nano 9K, which uses the same die and package. That match is **from my memory, not verified here**. | Before fab, confirm against Gowin UG803 or the Tang Nano 9K schematic. |
| N5 | LOW | **GCLK pin claims (35 = GCLKT_4, 52 = GCLKT_3) are unverified.** UG803 is not on disk. | Confirm against UG803 before layout. A wrong pin still works, but with worse clock skew. |
| N6 | LOW | J5.1 puts VD_3V3 on an external header with no series protection. A short there collapses the FPGA/FT232H rail. | Optional: add a series PTC or 10 Ω at J5.1. |
| N7 | INFO | U13 VCCA (37) and VCORE (38) share one 100 nF (C74). The pin-37 type was edited to PWRIN. This matches FTDI DS_FT232H Fig. 6.3 (p.53), where 37 and 38 are joined on VCORE. | Accepted. |
| N8 | INFO | U7 PGOOD (pin 1, open-drain) is tied to GND, which is the LM27762 summary's recommendation when PGOOD is unused. | Accepted. |
| N9 | INFO | **SKiDL tool issues, not design issues.** (a) The BOM XML is not byte-stable. `tools/kicad*/gen_xml.py:67` iterates `net.pins` unsorted, whereas `gen_netlist.py:259` uses `sorted(net.pins, key=str)`. Across runs, 22 `<node>` lines are reordered, and the sorted content is identical. (b) The root-node `tag=""` warning above. | SKiDL fix: `for p in sorted(net.pins, key=str):` in every `gen_xml_net`. Also give the root node a non-empty tag, or skip it in `check_tags()`. |

## Coder's false-positive / NC claims

Every declared NC is backed by a specific mechanism, and each one matches **exactly** the set of footprint pads that have no net. I checked this by comparing every footprint's pads to its netlist pins:

- J1 A8/B8 (SBU1/2)
- RN7 pads 4/5
- U12.22 (DVB)
- U13.32/33 (ACBUS8/9)
- U15 pins 3, 10, 11, 13–16, 84–86
- U17.1
- U4/U5/U6 pin 4

Every one is accepted.

The forced-drive rails ADC_AVDD, ADC_VDRV, OSC_VDD, FT_VPHY, CP_VIN, VBUS and VBUS_F are each physically fed, through FB6, FB5, FB7, FB8, FB2, J1 and FB1 respectively. The pin-type edits agree with the datasheets: U12 CLK is an input, DVA/DVB are outputs (SBAS295A p.12), and U13.37 follows FTDI Fig. 6.3.

## Checklist — defects that pass ERC

| Check | Result |
|---|---|
| **Supply span vs abs max** | Pass. U8/U10 OPA354: +2.484 V to −2.501 V = 4.99 V (op. max 5.5 V). LM27762 dividers verified (R6/R7 = 107k/100k, R8/R9 = 105k/100k). U12: AVDD and VDRV both come from VA_3V3 through ferrites, so ΔAVDD–VDRV ≈ 0 (abs max ±0.3 V). U2, U3, U6 and U7 take 5 V VBUS (≤ 5.5 V). All other ICs run at 3.3, 1.8 or 1.2 V, within range. |
| **Signal level vs receiver rail** | Pass. X1 3.3 V → U12 CLK (VIH 2.2 V, AVDD 3.3 V) and U15.35 (Bank 2, 3.3 V). U12 outputs (VDRV 3.3 V) → Banks 1/2 (3.3 V). Bank 1 → U12 SEL/SEN/SCLK/SDATA (3.3 V). FT232H ↔ Bank 1 at 3.3 V. Bank 3 (1.8 V) → U16 LV4T125 at 3.3 V (VIH 1.35 V, TI SCLS749C). U17 (VCC 1.8 V) → U15.83 (Bank 3). Pull-ups: R72/R74 go to 1.8 V on Bank 3 pins, and R61–R63/R65/R67 go to 3.3 V on FT232H pins. U9/U11 outputs → ADC through 49.9 Ω (≥ 25 Ω, as SBAS295A note 2 requires when the input can exceed 3.3 V). |
| **FPGA bank voltages** | Pass. Every U15 signal pin was mapped to its bank using UG119 Fig. 3-8. B1 (VCCIO1 = 58 → VD_3V3): 48–57, 59–63, 68–77, all 3.3 V signals. B2 (23/44 → VD_3V3): 17–20, 25–42, 47, all 3.3 V. B3 (12 → VD_1V8): 4–9, 79–83, 87/88, all 1.8 V / straps. VCCX/VCCIO0 (64/67/78) → VD_3V3. VCC → VD_1V2. For the PSRAM, see N4. |
| **Active filter topology** | Pass. Traced from U9/U11: Cf (C34/C35, C44/C45) sits across Rf (R16/R17, R26/R27), from OUT− to IN+ and from OUT+ to IN−, so both carry feedback current. C36/C46 sit differentially after R18/R19 and R28/R29. The attenuator top is C30 + VC1 (17–21 pF) and needs ≈ 18.2 pF against C31 + parasitics (≈ 165 pF). Input C is ≈ 16–19 pF (F7: 15–25 pF). No dead capacitor. Overload at ±50 V: TAP clamps near ±3 V through BAV199, OPA354 input current is limited by R13, and the FDA outputs stay ≤ 2.6 V. |
| **Exposed pads** | Pass. U7 WSON-12 EP pin 13 → GND. U15 QFN-88 EP pin 89 → GND. No other part has an EP. |
| **Reproducibility** | Pass. I ran it 3 times, and the netlists are identical apart from the `(date …)` line. They also match the assembler's pre-gate `outputs/dual_adc_usb.net`, date aside. No `_1`-suffixed refdes. |
| **Footprints** | Pass. The script found all valid. All 201 netlist footprints resolve to a `.kicad_mod`, and pads match pins (only the declared NCs are unconnected). Custom: `ProjectLocal:BNC_cntitle_BNC-KWE-6_Horizontal` (J2, J3) and `ProjectLocal:C_Trimmer_SEHWA_STC3M` (VC1, VC2). |

## Summary

| Metric | Value |
|---|---|
| ERC errors | 0 |
| ERC warnings | 0 |
| Netlist/XML warnings | 1 (root-node tag, false positive) |
| Notes | 9 (N1–N9, none blocking) |
| Footprint validation | Clean (33/33 script; 201/201 pad cross-check) |
| Checklist | 6/6 pass |
| Netlist stable | Yes (3 runs) |
| **Verdict** | **PASS** |
