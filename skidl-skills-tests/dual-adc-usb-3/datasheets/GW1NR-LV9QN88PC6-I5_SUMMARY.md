# GW1NR-LV9QN88PC6/I5 — Gowin GW1NR-9 FPGA, QN88P package (64 Mbit PSRAM embedded)

Source: Gowin **UG119E** "GW1NR series of FPGA Products Package & Pinout User Guide"
(`datasheets/UG119E_GW1NR_Package.pdf`, rev 1.8.4E) — this is the correct mechanical/pinout
document; `UG803` (also on disk as `UG803_GW1NR9_Pinout.pdf`) is Gowin's *generic pin
function* reference only and carries no package dimensions. Core-voltage assignment
(VCC = +1V2) is an architecture decision (`02_architecture.md` Decision 2), not independently
confirmed in UG119E — cross-check against Gowin **DS117E** (GW1NR data sheet) before layout
if this matters beyond schematic capture.

| Spec | Value |
|------|-------|
| Package | QN88P — QFN-88, 10×10mm body, 0.4mm pitch, embedded 64Mbit PSRAM |
| Vcc / Vin range | VCC (core) = architecture-assigned +1V2 (not restated in UG119E — confirm vs. DS117E); VCCIO1/VCCIO2 (user I/O banks) = 1.14–3.6V, architecture uses +3V3; VCCIO3 (PSRAM bank, QN88P only) = **1.71–1.89V, architecture uses +1V8** |
| Key output spec | 71 max user I/O (QN88P/GW1NR-9) — **not 88**; PSRAM and package overhead already subtracted |
| Max current / power | Not in this document — see DS117E if needed |
| Operating temp | Per ordering code `I5` = industrial, -40 to 85°C (standard Gowin suffix; not restated in UG119E body text) |

## Pinout

Full 88-ball pin-to-signal map for QN88P is **Figure 3-8 "View of GW1NR-9 QN88P Pins
Distribution (Top View)"**, UG119E p.15 — read that page directly rather than transcribing;
which physical I/O each net uses is a coder-time placement choice (`net_plan.md` does not
pre-assign GPIO pin numbers). Fixed-function / control pins (exact names as spelled in
UG803/UG119E):

| Pin | Name | Function |
|-----|------|----------|
| — | MODE0, MODE1, MODE2 | GowinCONFIG mode select, I, internal weak pull-up. Tie per desired boot mode (embedded-flash self-boot expected here — confirm exact strap value against DS117E/UG289, not stated in UG119E). |
| — | RECONFIG_N | Global reset of GowinCONFIG logic, active-low, internal weak pull-up. Architecture wires this to FX2LP `PA3` as `FPGA_RST_N` (`02_architecture.md` Carried forward, I11). |
| — | TMS, TCK, TDO, TDI | JTAG. TMS/TDI have internal weak pull-up; TCK is a plain input; TDO is an output. Goes to the 2×3 JTAG header (`fpga_capture` block, J3). |
| — | JTAGSEL_N | Reconfigure-JTAG-download select, I, internal weak pull-up |
| — | DONE | Config-complete flag, open-drain O, internal weak pull-up |
| — | READY | Program/configure-ready, open-drain I/O, internal weak pull-up |
| — | EPAD | Exposed pad — **recommended tied to GND, not mandatory** (UG119E note under §2.3) |

## Notes

- **R1 pin budget — resolved, not tight.** QN88P/GW1NR-9 gives **71 max user I/O**
  (Table 2-6, UG119E p.6) against the architecture's ~49-signal + 4-JTAG = ~53 need. **18
  spare**, comfortably clear of the mitigation ladder the architecture set up (drop
  ADC1_OTR/ADC2_OTR, drop trigger direction, drop LED_CAP_N) — none of those droppings are
  required. Per-bank split for QN88P: Bank0 0, Bank1 25/11/4 (single-ended/diff-pair/LVDS),
  Bank2 23/11/11, Bank3 23/6/3 (Bank3 is the PSRAM bank; the 23 count already accounts for
  pins the PSRAM consumes internally — those 23 are genuinely free for user I/O).
- **PSRAM occupies Bank3 (VCCIO3) on QN88P**, confirmed directly from UG119E and cross-checked
  against `UG803_GW1NR9_Pinout.txt` line 182 ("VCCIO3 ... connected to PSRAM and provides
  power for PSRAM"). This is the `+1V8` rail's destination — route VCCIO3 to `+1V8`, VCCIO1/
  VCCIO2 to `+3V3`, per architecture Decision 2.
- **EP dimension (closes `03_sourcing.md` gap item #1, GW1NR-9 part):** Figure 4-2
  "Recommended PCB Layout QN88/QN88P", UG119E §4.1 p.23 — **D2 × E2 = 6.8 × 6.8mm** exposed
  pad, 10.00×10.00mm body, 0.40mm pitch, terminal width b=0.20mm, terminal length L=0.85mm.
  The sourced footprint (`Package_DFN_QFN:ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm`)
  is close (6.74mm vs actual 6.8mm) but not exact — **build a corrected custom footprint with
  EP = 6.8×6.8mm** rather than trusting the borrowed ArtInChip value. Two silkscreen notes on
  the Gowin drawing: A(NOM) body height is 0.85mm for the LV9 (non-P) part but **0.75mm for
  LV9...P (PSRAM) parts** — package height only, does not affect the footprint/land pattern.
- Single-source, 102 units in stock (carried from `03_sourcing.md`) — still the design's
  tightest supply risk, unrelated to this phase's findings.
- Decoupling: standard Gowin practice is one 100nF per VCC/VCCIO/VCCX pin plus bulk per rail;
  architecture's C73–C90 range on this block is sized for that — no per-pin decoupling table
  is given in UG119E (it's a pinout/package guide, not an application-circuit datasheet).
