# W25Q32JVSSIQ — 32Mbit SPI NOR Flash (FPGA config, U31)

MCP data only — PDF not obtained (JLC field URL returned HTML on the one fallback attempt).
Local symbol `Memory_Flash:W25Q32JVSS` is a PREFIX match per `sourced_bom.md`.

| Spec | Value |
|------|-------|
| Package | SOIC-8, 208mil |
| Vcc / Vin range | 2.7–3.6 V |
| Key output spec | 133 MHz SPI clock, standard SPI/Dual/Quad modes |
| Max current / power | 1 µA standby |
| Operating temp | −40°C to +85°C |

## Notes
- Standard SOIC-8 SPI flash pinout (CS#, DO/IO1, WP#/IO2, GND, DI/IO0, CLK, HOLD#/IO3, VCC)
  — use the local symbol's pin names directly; not re-derived from a PDF this pass.
- Connects to XC6SLX9's Bank 2 SPI-boot-overlaid pins (D0-D15/MOSI/MISO/CCLK) per
  `XC6SLX9-2TQG144C_SUMMARY.md` — confirm WP#/HOLD# are tied appropriately (typically
  pulled high to disable those features) if not actively driven by the FPGA.
