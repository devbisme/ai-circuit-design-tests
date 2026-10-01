---
phase: 06_erc
agent: erc-reviewer
circuit: dual_adc_usb
written: 2026-09-30T23:45:00Z
status: complete
revision: 1
next_phase: export
---

# Phase 6 handoff — ERC

## Decisions
- **PASS.** ERC 0 errors / 0 warnings; footprint strings all resolve; `validate-bom.py` clean (169 parts, 0 mismatches) after the driver's 10 value-string edits.
- Accepted coder claims, each verified at the mechanism: root-node "Missing tag" warning (netlist + XML) is the `python -m` root, no part untagged; U10 VCCA retyped PWRIN (DS_FT232H: on-chip 1.8 V LDO drives VCORE and VCCA); U10 EECS/EECLK retyped OUTPUT; U6 PGOOD -> GND (LM27762 pin table); all declared NC pins confirmed absent from the netlist.
- Rejected one coder claim: "two runs diff empty apart from date" holds only by chance. Sheet order follows the Python hash seed (L1). Components and nets do not, so this is LOW, and the fix is in the export command.
- MEDIUM M1 (FT232H VREGIN 3.3 V-mode minimum vs the +3V3D tolerance band, 3.21 V worst case) is **non-blocking**. It is a recommended-operating limit, not abs max, and nominal is in spec. Raising the rail trades against U7 |AVDD-VDRV| ≤ 0.3 V abs max, so the fix is an architecture call, not a coder fix.
- U7 AVDD-before-VDRV skew (~1-3 ms) accepted: ADS5231 allows -10 ms < t3 < 10 ms. I read this from the rendered page, because pdftotext turns µ into m on that figure.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `outputs/erc_report.md` | PASS verdict, findings M1/L1/W1-2/N1-N6, checklist results | Always |
| `outputs/dual_adc_usb.net` | Regenerated netlist (PYTHONHASHSEED=0 run) | Export |
| `outputs/dual_adc_usb_bom.xml` | Regenerated XML BOM (same run) | Export |

## Next phase must
1. Export is unblocked. Regenerate deterministically from the project root:
   `PYTHONHASHSEED=0 KICAD9_SYMBOL_DIR="/usr/share/kicad/symbols:$PWD/symbols" python -m circuits.dual_adc_usb`
   (re-run once more and `diff` — only `(date …)` may differ).
2. Register fp-lib `ProjectLocal` -> `${KIPRJMOD}/footprints/ProjectLocal.pretty` in the KiCad project, or J2/J3 will not load.
3. Delete stale `outputs/run1.net`, `run1.log` and `run2.log`.
4. Driver: route M1 to `circuit-architect` for a disposition: accept, trim R6 (22k -> 21.5k gives 3.391 V), or move U10 to VREGIN 5 V mode. Any R6 change returns to `skidl-block-coder` (pwr_digital) and `part-sourcer`, and then to this gate.

## Carried forward
- M1: U10 VREGIN min 3.30 V vs +3V3D 3.21-3.45 V (TLV62569 VFB ±2 %, 1 % R5/R6). Open until the architect rules on it.
- J2/J3 `ProjectLocal:KH-BNC50-3511` is **custom-generated** from a not-to-scale drawing. Check pad positions and drill sizes against a physical part before fab.
- U9 EP pad 89 = GND unverified in Gowin docs (industry practice).
- U9 dual-purpose pins 53-57 and 59-62 are used as I/O. Enable "use as regular IO" for SSPI, MSPI, DOUT/DIN and FASTRD in the Gowin project (firmware).
- UG284 asks for a ferrite bead + 4.7 µF on U9 VCC, and the design has neither. Decide at layout or bring-up.
- Block-level items still open: C21/C41 trimmer, L1-L3, Y1 and U9 land patterns to verify at layout; keystone assumptions K3/K5/K10 (from `05_coding.md`).

## Do not redo
- ERC run and classification; footprint resolution; BOM-vs-circuit diff (all clean).
- Supply span vs abs max for every IC, signal level vs receiver rail on every inter-rail path, U9 pin -> bank -> VCCO for all 88 pins (bank 3 = 1.8 V PSRAM bank respected).
- AAF topology and values: 3rd-order Butterworth, f0 8.84 MHz, Q 0.99, RC pole 8.9 MHz, gain 0.909.
- Exposed pads (U6 13, U9 89 -> GND). Pin maps for U2, U5, U6, U7, U20/U21, D1, D20/D40, U8, Y1, U10 power pins.
- ADS5231 AVDD/VDRV sequencing.

## Receipt
- ERC: 0 errors, 0 warnings. Netlist/XML: 0 errors, 1 accepted warning each (root-node tag).
- Footprints: 27/27 resolve; J2/J3 custom (flagged). BOM: clean, 169/169.
- Findings: 1 MEDIUM (M1, U10 VREGIN tolerance, to the architect, non-blocking), 1 LOW (sheet-order seed, use PYTHONHASHSEED=0), 6 notes.
- **PASS**. outputs/ regenerated (seeded run).

## Driver addendum (2026-10-01)
- M1 dispositioned by driver: options were accept / trim R6 / FT232H VREGIN 5 V mode; chose 5 V mode (FTDI bus-powered config, removes the tolerance issue outright).
- usb_bridge rev 2 (`handoffs/05_blocks/usb_bridge.md`): VREGIN ← VBUS_SW; VCCD is internal regulator output on new net FT_VCCD feeding VPLL, VPHY, U11 VCC, R102. VCCIO stays +3V3D. No BOM change.
- `__main__.py` call updated with `vbus_sw=VBUS_SW`. Re-run (PYTHONHASHSEED=0): ERC 0 errors / 0 warnings; validate-bom 169/169 agree. outputs/ regenerated from this run.
- Not re-reviewed by erc-reviewer (localized change; driver checked FT_VCCD net membership in the netlist). architecture/net_plan.md not updated for FT_VCCD / U10 load moving from +3V3D to VBUS_SW — doc drift, TODO.
