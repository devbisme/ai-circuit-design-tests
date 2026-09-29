# Export notes — dual_adc_usb

Generated 2026-09-10. ERC **PASS** (0 errors, 0 warnings), footprints **67/67**,
218 components, 136 nets. Verdict and evidence: `erc_report.md`, `handoffs/06_erc.md`.

## Files

| File | What it is |
|---|---|
| `dual_adc_usb.net` | KiCad netlist — import into a new PCB |
| `dual_adc_usb_bom.xml` | BOM in KiCad XML form |

Regenerate both with:

```bash
KICAD9_SYMBOL_DIR="/usr/share/kicad/symbols:$PWD/symbols" \
  PYTHONPATH="$PWD/circuits/dual_adc_usb" \
  .venv/bin/python circuits/dual_adc_usb/__main__.py
```

The generated netlist is reproducible: two runs differ only in the `(date ...)` header
line, and all 447 component UUIDs are stable because `_stabilize_tags()` derives each
part's tag from its refdes. That is what lets KiCad's "update PCB from schematic" keep
placement and routing across regenerations.

## Before you open KiCad

Two project-local libraries must be registered or the import will show missing symbols
and footprints:

1. **Symbols** — `symbols/dual_adc_usb.kicad_sym` (AD9235BCPZ-40, AD8066ARZ,
   GW1NR-LV9QN88PC6-I5; none exist in the stock KiCad libraries). Preferences → Manage
   Symbol Libraries → Project Specific, nickname `dual_adc_usb`.
2. **Footprints** — `footprints/Inductor_SMD_Custom.pretty` (the FNR3015S buck inductor).
   Preferences → Manage Footprint Libraries → Project Specific, nickname
   `Inductor_SMD_Custom`, path `${KIPRJMOD}/footprints/Inductor_SMD_Custom.pretty`.

## Refdes mapping for purchasing

`sourcing/sourced_bom.md` names the analog front end as `U7 ×2 / U8 ×2 / J2 ×2 /
R13–R27 / C34–C47 / D3 ×2`, from before the two channel instances were given
deterministic references. The netlist now uses a 100/200 series — **quantities and part
numbers are unchanged**, only the reference strings differ:

| BOM says | CH1 | CH2 |
|---|---|---|
| `J2` (BNC) | `J102` | `J202` |
| `U7` (AD8066) | `U107` | `U207` |
| `U8` (THS4551) | `U108` | `U208` |
| `D3` (BAV199) | `D103` | `D203` |
| `R13`–`R25` | `R113`–`R125` | `R213`–`R225` |
| `C34`–`C47` | `C134`–`C147` | `C234`–`C247` |

Two component changes since the BOM was written, both using values already sourced:

- `C39/C40` are **22 pF** (were 62 pF, which was never a BOM value) and `C41` is **30 pF**
  (was 11 pF) — the anti-alias filter fix, `handoffs/05_coding.md` Revision 2 / H1.
- **FB6** (600R@100MHz, same part as FB1–FB5) and **C106** (10 µF 0603) are new, from the
  ADC-clock fix (H2). Quantities: +1 ferrite, +1 10 µF; −1 100 kΩ (the duplicate PWR_EN
  pull-down was removed).

## Blocking before Gerbers — not before layout

**The BNC footprint is wrong.** `Connector_Coaxial:BNC_Win_364A2x95_Horizontal` is a
placeholder so the netlist validates. The real KH-BNC50-3511 uses 10.1 mm hole spacing
with Ø2.00 mm + Ø0.90 mm holes, and the exact board-contact count could not be resolved
from the one drawing available. Build a custom footprint against a physical sample.
See `datasheets/KH-BNC50-3511_SUMMARY.md` for the safe-minimum pad assumption.

## Resolved since export

- **SiT1602BI (Y1) pinout — verified, closed 2026-09-10.** The primary datasheet is now on
  disk (`datasheets/SiT1602BI-22-33E-10.000000.pdf`, SiT1602B Rev 1.08). It replaced a file
  of the same name that was an HTML 404 page saved as `.pdf`. Checked end to end:
  - **Pinout** 1 = OE, 2 = GND, 3 = OUT, 4 = VDD (Table 2, p.2), as assumed.
  - **Netlist:** Y1 pins 1/2/3/4 land on `+3V3` / `GND` / `CLK_XO` / `+3V3`.
  - **Footprint:** KiCad pads at ±1.1 × ±0.95 mm, 1.4 × 1.2 mm — an exact match to the
    recommended land pattern (p.10).
  - **Ordering code** (p.13): 3.2 × 2.5 mm, 3.3 V ±10 % (the rail is 3.318 V), Output
    Enable.
  - **Jitter:** 0.9 ps rms phase jitter max, against the architecture's 2.5 ps assumption
    and a 20 ps bar.

  No physical pin-1 check is needed any more. Details:
  `datasheets/SiT1602BI-22-33E-10.000000_SUMMARY.md`. Only `clock_gen.py`'s docstring
  changed; ERC re-run 0/0, and the netlist is unchanged apart from `SKiDL Line` source
  metadata.

## Verify before committing to fab

- **GW1NR-9 MODE0/MODE1 straps** are pulled low through R49/R50 as a defined default. The
  boot-mode truth table is in Gowin DS117E, which could not be obtained. Confirm.
- **Exposed pads**: the GW1NR-9 footprint's EP is 6.74 mm against the datasheet's 6.8 mm.
  The AD9235 now uses the correct 3.1 mm LFCSP land pattern, not the BOM's 3.45 mm.
- **JTAG is 1.8 V**, not 3.3 V — Bank 3 is tied to the PSRAM rail. Set the Gowin
  programmer to 1.8 V VCCIO.

## Layout constraints inherited from the design

- Analog/digital plane split with a single tie point under the ADCs
  (`architecture/design_risks.md` R12).
- Length-match `CLK_ADC1` and `CLK_ADC2` — the schematic can only guarantee matched
  topology, not matched delay. Channel-to-channel skew ≤100 ns is SPEC F10.
- U11 (clock buffer) now switches on the analog rail (H2 fix). Keep its ground return
  away from the ADC reference pins.
- The 10 MHz anti-alias margin is 1.4 dB, and ±5 % on C139/C141 moves it ±0.4 dB. It
  clears on paper — measure it on the prototype.
