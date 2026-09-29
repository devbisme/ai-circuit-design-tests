# Architecture amendments — made by the pipeline driver

Revision 1 · 2026-09-10 · circuit `dual_adc_usb`

**Why these were not made by `circuit-architect`.** Phase 5 opened with the account's
opus subagent quota exhausted (HTTP 429, "monthly spend limit… session limit resets 5am
America/New_York"); all nine block coders and, by extension, any architect re-spawn were
dead on arrival. The user's brief forbids pausing the design. The driver therefore resolved
the three blocking issues below in the main thread, in the architect's stead, and recorded
them here rather than silently coding around them. **Each one should be re-reviewed by
`circuit-architect` when quota returns.**

Every amendment below overrides `architecture/net_plan.md` and
`architecture/ic_selection.md` where they conflict. The block files implement the amended
version.

---

## A1 — THS4551 must run on a single +4.2 V supply, not across ±4.2 V

**Severity: fatal if built as specified.** `handoffs/04_datasheets.md` Decision #2 raised it
and refused to wire it; this closes it.

The architecture wires U8 (THS4551, both `analog_frontend` instances) VS+ → `+4V2A` and
VS− → `-4V2A`. That is **8.4 V across a part whose absolute-maximum supply is 5.5 V** and
whose recommended range is 2.7–5.4 V. The part would be destroyed at power-up.

Options considered:

| # | Option | Verdict |
|---|---|---|
| 1 | VS+ = `+4V2A`, VS− = `GND` (single 4.2 V supply) | **Selected** |
| 2 | Add a dedicated ±2.5 V rail pair for the FDA | Rejected — a new regulator, new BOM lines, and more current for no functional gain |
| 3 | Swap to an FDA rated for ±5 V (ADA4940-1, THS4131) | Rejected — re-sourcing a keystone part, and the design does not need bipolar FDA rails |

**Why option 1 is correct, not just cheap.** The FDA's job here is single-ended-to-
differential conversion *and* the level shift onto the ADC's 1.5 V common mode. Its output
never needs to go below ground:

- Output: `VOCM` = 1.50 V, differential swing ±1.0 V → each output moves 1.0 V…2.0 V.
  Inside the THS4551's output range on a 4.2 V rail with >0.8 V of headroom each way.
- Input common mode: with the source referenced to GND (CM = 0 V), Rg = 1.00 k, Rf = 1.10 k
  and output CM = 1.5 V, the amplifier's input pins sit at a **constant**
  (0 V·1.10 k + 1.5 V·1.00 k)/2.10 k = **0.714 V** — comfortably inside the THS4551's
  input CM range on a single 4.2 V supply.
- `VOCM` = 1.50 V is inside its valid input window.

**The negative rail is still required** — U7 (AD8066) must swing to −0.909 V, and D3 clamps
to both rails. `-4V2A` keeps all of its other loads; only U8's VS− moves to `GND`.

Net-plan delta: `-4V2A` loses `U8/U8' THS4551 VS−`; `GND` gains it.

## A2 — GW1NR-9 QN88P I/O budget is 48 usable 3.3 V pins, not 71

**Severity: high.** `handoffs/04_datasheets.md` reported risk R1 (FPGA pin budget) as
resolved with "71 I/O available". That figure is for the GW1NR-9 die, not for the **QN88P**
package this design uses. Parsed pin-by-pin out of `datasheets/UG803_GW1NR9_Pinout.pdf`
(QN88P column, all 88 pins):

| Bank | Supply pin | QN88P voltage | User I/O in QN88P |
|---|---|---|---|
| 0 | `VCCX/VCCIO0` (64, 67, 78) | 2.375–3.6 V | **none** — auxiliary supply only |
| 1 | `VCCIO1` (58) | 1.14–3.6 V → `+3V3` | 25 |
| 2 | `VCCIO2` (23, 44) | 1.14–3.6 V → `+3V3` | 23 |
| 3 | `VCCIO3` (12) | **1.71–1.89 V, hard-tied to the PSRAM** → `+1V8` | 23, at 1.8 V only |

Usable 3.3 V I/O = **48**. Signals the architecture wants at 3.3 V = **47**
(24 ADC data + 2 OTR + CLK_FPGA + 8 FD + IFCLK + 4 SLxx/PKTEND + 2 FIFOADR + 3 FLAG +
TRIG_IO + LED_CAP_N). One spare pin, with no room for a debug pin or a bring-up jumper.

Options considered:

| # | Option | Verdict |
|---|---|---|
| 1 | Drop `ADC1_OTR` / `ADC2_OTR` (2 pins) and move `LED_CAP_N` to Bank 3 at 1.8 V | **Selected** — 45 of 48 used, 3 spare |
| 2 | Time-multiplex the two 12-bit ADC buses onto 12 lines at 20 MHz | Rejected — doubles the capture-side timing risk to save pins that option 1 frees for nothing |
| 3 | Move to LQ144P/MG100P | Rejected — changes the keystone part and its single-source risk (R2) for a budget that now fits |

`net_plan.md` already marks OTR "droppable — see R1", so option 1 spends a licence the
architecture had pre-authorised. Overrange remains detectable in firmware: an offset-binary
code of `0x000` or `0xFFF` *is* the clipping indication, which is what the OTR pin
duplicates. An LED needs no logic level, so 1.8 V drive costs nothing.

## A3 — 3.3 V→1.8 V translation on `FPGA_RST_N`, and Bank-3 pull-up references

**Severity: high (latent damage).** Falls out of A2 and was not visible before the QN88P
bank map existed.

`RECONFIG_N` is pin 9 (`IOL13B`), in **Bank 3 at 1.8 V**. `net_plan.md` drives it from
U13 (FX2LP) PA3 at **3.3 V**. GW1N I/O are not 3.3 V tolerant when VCCIO = 1.8 V, so the
FX2LP would be over-driving a 1.8 V input every time it asserts reset.

Options: a level-shifter IC (new BOM line, new part risk); a series resistor relying on the
FPGA's ESD clamp to sink the excess (bad practice — clamp current on every assertion); or a
resistive divider. **Selected: a 10 k/12 k divider** — `FPGA_RST_N` is a slow static reset,
not a timed signal, so a divider's RC is irrelevant, and 0402 resistors are already a BOM
family. 3.3 V × 12/22 = 1.80 V.

Consequent reference changes, same root cause:

- R35 (`RECONFIG_N` pull-up) → `+1V8`, **not** `+3V3`.
- R36 (`TMS` pull-up) → `+1V8`, **not** `+3V3`.
- J3 JTAG header's reference pin carries `+1V8`. The Gowin programmer must be set to
  1.8 V VCCIO. **This is a bring-up instruction, not just a netlist detail.**

## A4 — carried forward, NOT fixed here

- **J2 BNC footprint is confirmed wrong** (`handoffs/04_datasheets.md` #3): the real
  KH-BNC50-3511 uses 10.1 mm hole spacing, and the exact board-contact count could not be
  resolved from the one available drawing. The block file uses the sourced footprint string
  so the netlist is complete and validates; **a custom footprint must be built and checked
  against a physical sample before Gerbers.**
- **Exposed pads:** the AD9235 EP is 3.10 mm, and the code now uses the ADI LFCSP land
  pattern with a 3.1 mm EP (the sourced footprint's was 3.45 mm) — resolved. The GW1NR-9
  EP is 6.8 mm against the footprint's 6.74 mm, slightly *under*sized — layout should check.
- ~~**SiT1602BI pinout is unverified**~~ — **closed 2026-09-10.** The SiT1602B datasheet
  (Rev 1.08) is now in `datasheets/`. The pinout, ordering code, land pattern, and netlist
  connections all check out against it; see `outputs/EXPORT_NOTES.md` § Resolved since
  export.
