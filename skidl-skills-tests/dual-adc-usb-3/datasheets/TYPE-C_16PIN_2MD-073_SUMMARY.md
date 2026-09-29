# TYPE-C 16PIN 2MD(073) — Shenzhen Shouhan USB Type-C Receptacle, 16-Pin Mid-Mount SMD (J1)

Source: `datasheets/TYPE-C_16PIN_2MD-073.pdf` (Shouhan "Specification for Approval", 6 pages
— p.1 is the full mechanical drawing + recommended PCB layout + pin-assignment table; p.2 is
a signature cover sheet; p.3–6 are mechanical/environmental test-method tables, no further
dimensional data).

| Spec | Value |
|------|-------|
| Package | 16-pin mid-mount SMD USB Type-C receptacle, 8.94×7.35mm shell (see p.1 mechanical views), board thickness 0.80mm target |
| Vcc / Vin range | VBUS 5.0V rating |
| Key output spec | USB 2.0 only — no SuperSpeed (TX/RX) differential pairs broken out, 16 pins covers GND/VBUS/CC/SBU/D+/D– only (matches this design's FX2LP USB-2.0-only architecture) |
| Max current / power | Current rating 3.0A (spec sheet §4-1) |
| Operating temp | –25°C to +85°C |

## Pinout (16 pins, exactly as datasheet Table)

| Pin | Name | Function |
|-----|------|----------|
| A1 | GND | Ground |
| A4 | VBUS | Power |
| A5 | CC1 | Configuration Channel 1 |
| A6 | DP1 | USB 2.0 D+ (lane 1) |
| A7 | DN1 | USB 2.0 D– (lane 1) |
| A8 | SBU1 | Sideband Use 1 |
| A9 | VBUS | Power |
| A12 | GND | Ground |
| B1 | GND | Ground |
| B4 | VBUS | Power |
| B5 | CC2 | Configuration Channel 2 |
| B6 | DP2 | USB 2.0 D+ (lane 2) |
| B7 | DN2 | USB 2.0 D– (lane 2) |
| B8 | SBU2 | Sideband Use 2 |
| B9 | VBUS | Power |
| B12 | GND | Ground |

## Notes

- **Land-pattern confirmation: CONFIRMED MATCH — closes the USB-C half of `03_sourcing.md`
  gap item #3.** Checked the assigned KiCad footprint
  (`Connector_USB:USB_C_Receptacle_HCTL_HC-TYPE-C-16P-01A`, a different manufacturer —
  "HCTL" vs. this part's "Shouhan" — but the same generic 16-pin mid-mount package style)
  directly against `/usr/share/kicad/footprints/Connector_USB.pretty/`: its pad names are
  **A1/A4/A5/A6/A7/A8/A9/A12/B1/B4/B5/B6/B7/B8/B9/B12 — an exact match to this datasheet's
  pin table**, its 2 mounting holes are **Ø0.65mm non-plated through-holes**, matching the
  datasheet's "Ø0.65(2X)" callout (p.1, PCB layout view) exactly, and its pad pitch groups
  are **0.6mm pitch ×4 outer pads (VBUS/GND) + 0.3mm pitch ×8 inner pads (CC/D±/SBU)** —
  matching the datasheet's "0.60(4X)" / "0.30(8X)" pitch callouts exactly. This 16-pin
  mid-mount Type-C footprint is effectively industry-standardized across vendors (both parts
  share it) — **no footprint change needed, J1 can be placed with the sourced footprint
  as-is.**
- Since only USB 2.0 D+/D– (no SuperSpeed pairs) are broken out, this part is intentionally
  paired with the FX2LP (`CY7C68013A-56LTXC`, USB 2.0 slave FIFO) per architecture — no
  mismatch with the rest of the `usb_c_port`/`usb_controller` blocks.
- Both CC1 and CC2 are present (A5/B5) — standard practice is a 5.1kΩ pull-down resistor on
  each CC pin to GND for UFP (device) mode detection at 5V/default current (no PD
  negotiation implied by this design). Confirm `usb_c_port` block's resistor set includes
  both CC pull-downs; not itemized in `sourced_bom.md` under a distinct CC label — check for
  a generic 5.1k 0402 line item.
- Both SBU1/SBU2 (A8/B8) are typically left unconnected (NC) unless an alternate-mode analog
  signal is routed through them — no alt-mode use implied anywhere in
  `02_architecture.md`/`03_sourcing.md`, so leave NC.
