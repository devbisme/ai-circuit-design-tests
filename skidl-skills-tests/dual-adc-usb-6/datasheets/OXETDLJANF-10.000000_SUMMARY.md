# TAITIEN OXETDLJANF-10.000000 — 10 MHz SMD Crystal Oscillator (KEYSTONE, X1 — R2 oscillator-jitter substitution)

**This part SUPERSEDES `sourced_bom.md`'s X1 row (SX3M10.000B10F20TNN, LCSC C5452682).**
See Decisions in the handoff for the full reasoning. LCSC C17609541.
Datasheet obtained: `datasheets/OXETDLJANF-10.000000.pdf` (TAITIEN "OX Type" datasheet,
downloaded directly from LCSC's file host and read in full — 1 page, single-source XO
family datasheet). Symbol generated: `symbols/dual_adc_usb.kicad_sym:OXETDLJANF-10.000000`
(4 pins, EXACT).

| Spec | Value |
|------|-------|
| Package | SMD3225-4P (3.2 × 2.5 × 0.95mm ceramic) — **identical footprint** to the superseded SX3M part, `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` |
| Vcc / Vin range | 3.3 V ±5% (2.97–3.63 V); 2.5 V and 1.8 V options also exist but 3.3V is what's stocked/sourced here |
| Key output spec | **RMS Phase Jitter (12 kHz–20 MHz): ≤1 psec** — see Load-bearing facts |
| Max current / power | ≤15 mA @ 3.3V, 1.25 MHz ≤ Fo < 10 MHz load condition |
| Operating temp | −40°C to +85°C |

## Pinout (standard 4-pin SMD oscillator pinout)
| Pin | Name | Function |
|-----|------|----------|
| 1 | Tri-State (OE) | Enable (high or floating) / Disable output (low) |
| 2 | GND | Ground |
| 3 | Output | CMOS clock output |
| 4 | VDD | Supply |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| RMS Phase Jitter (12 kHz–20 MHz) | ≤ 1 psec (Max column, all supply-voltage tiers) | datasheet p.1, Electrical Specification table, row "RMS Phase Jitter (12kHz to 20MHz)" — **verified**, read directly off the downloaded PDF |
| Period Jitter (Pk-Pk) | ≤ 40 psec | same table, row "Period Jitter (Pk-Pk)" — **verified** |
| Frequency stability | ±25 ppm (this reel's grade; ±20/±25/±50 ppm options exist per temp range table) | datasheet p.1 — **verified** |
| Stock at LCSC | 50 pcs (C17609541) — 5x margin over the 10 needed for a 10-board run (1/board) | `jlc_get_part` live query, 2026-09-21 |

## Why this replaces X1 (R2 — the sample-clock jitter budget)

The ADC sample clock has a ~7 ps RMS phase-jitter budget (12-bit SNR at 5 MHz input,
per architecture). The originally-sourced part, **SX3M10.000B10F20TNN**, was downloaded
and read in full this pass (`datasheets/SX3M10.000B10F20TNN.pdf`, 9 pages, SCTF Elec's
generic "MHz Crystal Oscillator" family sheet spanning grades 0C/1C/2C/3C/5C/7C, 1–160
MHz). **It publishes NO phase-jitter or period-jitter figure of any kind** — only
frequency stability (±10/±20 ppm), supply current, duty cycle, rise/fall time, and aging.
This is now **confirmed absent from a primary source**, not merely "not found" — the
entire datasheet was read page by page and no jitter spec exists for this part at any
frequency/grade.

TAITIEN's OXETDLJANF-10.000000 is a like-for-like substitute: **same package** (no
footprint change), similar price (¥1.51 vs ¥0.34 — a few cents/unit difference, negligible
at 10-board volume), in stock at JLC, and its datasheet publishes RMS phase jitter of
≤1 ps (12 kHz–20 MHz) — **7x inside the ~7 ps RMS budget**, with a comfortable margin for
the aperture-jitter and reference-clock-path contributions still to be budgeted elsewhere.

## Notes
- Pin function/count identical to the superseded part's assumed pinout (standard 4-pin
  SMD XO convention) — no schematic rework beyond swapping the MPN/symbol reference.
- Also checked ECS-2033-100-BN (LCSC C2451304, US-brand SMD2520 oscillator, also in JLC
  stock) as a second candidate — its datasheet (`datasheets/ECS-2033-100-BN.pdf`) is a
  generic family sheet with **no jitter spec published at all**; rejected in favor of
  TAITIEN's part, which does.
- Surveyed all 21 in-stock 10 MHz/3.3V CMOS oscillators at JLCPCB (`jlc_search`,
  subcategory Crystal Oscillators): all are low-cost Asian generic-family parts (TROQ,
  JGHC, JWT, Jiangsu Changjing, Interquip, YXC, TXC); none besides TAITIEN's OX-type
  publish an RMS phase-jitter figure at JLC-stocked frequencies/packages.
