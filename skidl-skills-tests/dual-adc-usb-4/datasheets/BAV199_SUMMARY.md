# BAV199 — Low-Leakage Double Diode, SERIES-connected pair (D2/D3)

| Spec | Value |
|------|-------|
| Package | SOT-23 (SOT23-3, 2.9x1.3x1mm body, 1.9mm pitch) |
| Vcc / Vin range | N/A (passive diode) |
| Key output spec | VR = 75V (max 85V repetitive), IR = 3pA typ leakage |
| Max current / power | IF = 140mA (double diode loaded), Pd not separately specified |
| Operating temp | -55°C to +150°C (Tj) |

## Pinout (Nexperia official datasheet, Table 2 "Pinning information" — VERIFIED)
| Pin | Name | Function |
|-----|------|----------|
| 1 | A1 | Anode of diode 1 |
| 2 | K2 | Cathode of diode 2 |
| 3 | K1_A2 | **Series junction**: cathode of diode 1 AND anode of diode 2 (common node) |

Symbol generated: `symbols/dual_adc_usb.kicad_sym`, part `BAV199` (EXACT match). Pin 3 is
named `K1_A2` in the generated symbol (the datasheet writes it "K1, A2" — comma changed to
underscore to keep it a single CSV/pin-name token; both identities point to the same physical
pin/node).

## Notes
- **Topology, confirmed from the manufacturer datasheet (Nexperia, 1 April 2023,
  assets.nexperia.com/documents/data-sheet/BAV199.pdf, downloaded to
  `datasheets/BAV199.pdf`):** the two diodes are wired in **series** through the common pin 3
  node — diode 1 runs A1(pin1)→K1(pin3), diode 2 runs A2(pin3)→K2(pin2). This is electrically
  a totally different topology from:
  - `Diode:BAV19` — single diode, wrong part count.
  - `Diode:BAV99` — two diodes in a **common-cathode** (or common-anode, depending on variant)
    parallel arrangement, not series. Confusing BAV199 for BAV99 would short what should be a
    series-limited path.
  Do not substitute either lookalike symbol for the one generated here.
- Architecture flagged this part explicitly (`02_architecture.md`) — this generation and
  verification close that flag.
