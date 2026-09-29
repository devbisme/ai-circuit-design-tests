# GW1NR-LV9QN88PC6/I5 — Gowin GW1NR-9 LittleBee FPGA, PSRAM-embedded QN88P QFN-88 (U15)

| Spec | Value |
|------|-------|
| Package | QFN-88, 10x10mm, 0.4mm pitch, QN88P variant (1.8V PSRAM embedded in-package) |
| Vcc / Vin range | VCC (core, LV) 1.14-1.26V; VCCX (aux) 2.375-3.6V; VCCIO per-bank 1.14-3.6V |
| Key output spec | 8640 LUT4, 468kbit BSRAM, 71 user I/O (see bank budget below) |
| Max current / power | See DS117E §3 DC Characteristics (not exhaustively summarized here) |
| Operating temp | Industrial: -40°C to +100°C (Tj); this is the `/I5` speed/temp grade |

## Pinout (89 pins = 88 signal/power + EP; JLC/EasyEDA data, ONE CORRECTION applied — see Decisions)
Full 89-pin table is in the generated symbol (`symbols/dual_adc_usb.kicad_sym`, part
`GW1NR-LV9QN88PC6/I5`). Key groups:

| Pins | Group | Notes |
|---|---|---|
| 1, 22, 45, 66 | VCC | Core supply (1.14-1.26V, LV version) |
| 2, 21, 24, 43, 46, 65 | VSS | Ground |
| 64, 67, 78 | VCCX/VCCIO0 | Bank0 (Top) supply — **PSRAM-locked to 1.8V**, see below |
| 58 | VCCIO1 | Bank1 (Right) supply, user-selectable 1.2-3.3V |
| 23, 44 | VCCIO2 | Bank2 (Bottom) supply, user-selectable 1.2-3.3V |
| 12 | VCCIO3 | Bank3 (Left) supply, user-selectable 1.2-3.3V — **CORRECTED, see Decisions** |
| 87, 88 | IOT6B/MODE1, IOT5A/MODE0 | Boot mode select (sampled at power-up, then GPIO-capable) |
| 3-20 (IOL*) | Bank3 (Left) | includes JTAG: pin5=TMS, pin6=TCK, pin7=TDI, pin8=TDO; pin9=RECONFIG_N; pin10=DONE |
| 25-42 (IOB*) | Bank2 (Bottom) | general I/O |
| 47-63 (IOR*) | Bank1 (Right) | includes MSPI/configuration-shared pins (pins 53-62) |
| 68-88 (IOT*) | Bank0 (Top) | **0 usable per Gowin's own quantity table — see Decisions** |
| 89 | EP | Exposed pad, tie to GND per Gowin recommended PCB layout (Fig 4-2, UG119E) |

## Notes
- **CP, single-source, WARN stock (182 units).** Buy full 10-board qty now per architecture
  instruction #6 (unchanged from sourcing).
- **JTAG lives entirely in Bank3** (pins 5-8 = TMS/TCK/TDI/TDO), whose VCCIO3 the architecture
  already set to VD_1V8 (`net_plan.md` line 17) — consistent with this bank's I/O standard
  requirements, no conflict found.
- Datasheets downloaded: `datasheets/GW1NR-LV9QN88PC6-I5.pdf` (DS117-3.2.5E, main datasheet —
  JLC's MCP record had no datasheet URL at all, this was found via web search of Gowin's own
  CDN) and `datasheets/GW1NR-9-UG119-package.pdf` (UG119-1.8.4E, "GW1NR series of FPGA
  products Package & Pinout User Guide" — this is the correct package/mechanical-drawing
  document; the sourcing handoff's reference to "UG803" appears to be Gowin's per-device
  pinout-only companion doc, superseded here by UG119E which has the actual Figure 4-1/4-2
  mechanical/PCB-land drawings needed for footprint verification).

## Decisions
1. **`⚠️ CUSTOM FP NEEDED (verify first)` RESOLVED — footprint CONFIRMED, no custom footprint
   needed.** Gowin's own QN88/QN88P Package Outline (UG119E §4.1, Figure 4-1/4-2, p.22-23) gives:
   D=10.00mm, E=10.00mm (body), **D2=6.8mm, E2=6.8mm (exposed pad)**, e=0.40mm (pitch),
   P=9.90mm (pin span), L=0.85mm (lead length), b=0.20mm (lead width). The candidate KiCad
   footprint `Package_DFN_QFN:ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm` has an EP of
   6.74x6.74mm against Gowin's nominal 6.8x6.8mm — a 60µm per-side difference, well within
   normal EP-pad-shrink practice (PCB EP copper is routinely drawn 5-15% smaller than the
   package's nominal EP to reduce solder voiding under the thermal pad). Body size (10x10mm)
   and pitch (0.4mm) match exactly. **Use the ArtInChip footprint as-is — it is not a custom
   footprint problem, it is a correctly-executed EP shrink.** No custom footprint was built.
2. **Pin 12 corrected from `VCCX/VCCO0` (JLC/EasyEDA label) to `VCCIO3`** in the generated
   symbol. Gowin's own UG119E Table 3-8 "Other pins in GW1NR-9 QN88P" lists VCCX/VCCIO0 only
   at pins 64, 67, 78, and VCCIO3 at pin 12 alone — matching pin 12's physical position inside
   the IOL (Bank3/Left) pin cluster (pins 3-20), not the IOT (Bank0/Top) cluster (pins 68-88)
   where the other VCCX/VCCIO0 pins sit. JLC's EasyEDA-derived symbol data mislabels this one
   pin; trust Gowin's own table. This is exactly the kind of pin-name error the coder cannot
   catch downstream — flagging per the "pinouts must be right" mandate.
3. **All 6 `⚠️ SYMBOL NEEDED` parts closed.** Symbols generated in
   `symbols/dual_adc_usb.kicad_sym`; all 6 verified `EXACT` via `find-symbol.py` (run with
   `KICAD9_SYMBOL_DIR` including `symbols/`).

## Carried forward
- **I/O budget — READ THIS BEFORE ASSIGNING ANY U15 PIN.** Gowin's own DS117E §2.4.3 Table 2-6
  "Quantity of GW1NR-9 Pins" for the **QN88P** package column gives, per bank (single-ended /
  differential-pair / true-LVDS):
  - **Bank0 (Top, IOT-prefixed pins 68-88): 0/0/0 — ZERO usable general-purpose I/O.** This
    bank's table entry is 0 even though the EasyEDA/JLC pin table lists ordinary-looking names
    (IOT42B, IOT12A, etc.) for these pins with no "reserved" marking. Gowin's note on p.10 says
    "the I/O Bank voltage that connects to the PSRAM needs to be 1.8V" — Bank0/VCCX-VCCIO0 is
    the PSRAM-locked bank for the embedded-PSRAM QN88P package. **Do not assign any IOT-prefixed
    pin (68-88, excluding the two MODE pins 87/88) to a user net without independently
    re-confirming against Figure 3-8 "View of GW1NR-9 QN88P Pins Distribution" (a graphic, not
    text-extractable) in `datasheets/GW1NR-9-UG119-package.pdf` p.15** — this datasheet
    librarian could not resolve the apparent contradiction between the named pins and the 0-count
    table within budget, and getting this wrong on a single-source, WARN-stock, custom-footprint
    FPGA is the single costliest place for it to go unnoticed (per this agent's own operating
    mandate). Treat Bank0/IOT pins as **not available for user I/O** until the coder confirms
    otherwise from the figure.
  - **Bank1 (Right, IOR-prefixed): 25 single-ended / 11 diff-pair / 4 true-LVDS.**
  - **Bank2 (Bottom, IOB-prefixed): 23 single-ended / 11 diff-pair / 11 true-LVDS.**
  - **Bank3 (Left, IOL-prefixed, includes JTAG): 23 single-ended / 6 diff-pair / 3 true-LVDS.**
  - Total Max User I/O = 71 (matches JLC's stock listing "TQFP-64... 71 (11)" style figures
    elsewhere, and matches sourcing's own "71 usable" note) — **but the 71 all come from Banks
    1-3 only; the architecture/coder must not budget any of it against Bank0.**
- **Table 3-8 pin numbers for VCC/VCCIO/VSS/MODE are now authoritative** (used to build/correct
  the symbol, see Decisions #2) — use them, not the raw JLC labels, if there is ever a conflict.
