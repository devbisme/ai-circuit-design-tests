# IS61WV25616BLL-10TLI — 256K×16 async CMOS SRAM (TSOP-II-44)

SOURCE: ISSI datasheet (IS61WV25616ALL/ALS, IS61WV25616BLL/BLS, IS64WV25616BLL/BLS,
Rev. E, 11/21/07), PDF fetched successfully and read directly (pin configuration page
read as an image, transcribed pin-by-pin below — high confidence, not OCR-guessed).
**No KiCad symbol exists for this part — this pin table is the kipart input for the
coding phase.**

| Spec | Value |
|------|-------|
| Package | 44-pin TSOP (Type II) — this design uses the **-10TLI** speed/package suffix (10 ns, industrial temp, TSOP-II, lead-free/RoHS "L" tape) |
| Organization | 256K × 16 (4,194,304 bits), fully static — no clock/refresh required |
| VDD | 2.4 V – 3.6 V ("Bxx" variant); this design runs it at 3.3 V |
| Access time | 10 ns max (binding spec per architecture — capacity is not the driver) |
| Active power | 85 mW typical (high-speed "ALL/BLL" variant) |
| Standby power | 7 mW typical CMOS standby |
| Operating temp | Industrial (−40 °C to +85 °C) supported |

## Pinout (44-pin TSOP-II, top view, pin 1 = upper-left with notch/dot)

Left side, pins 1–22 (top to bottom):

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 1 | A0 | input | Address |
| 2 | A1 | input | Address |
| 3 | A2 | input | Address |
| 4 | A3 | input | Address |
| 5 | A4 | input | Address |
| 6 | CE̅ | input | Chip Enable, active LOW |
| 7 | I/O0 | bidir | Data I/O, lower byte |
| 8 | I/O1 | bidir | Data I/O, lower byte |
| 9 | I/O2 | bidir | Data I/O, lower byte |
| 10 | I/O3 | bidir | Data I/O, lower byte |
| 11 | VDD | power | Supply |
| 12 | GND | power | Ground |
| 13 | I/O4 | bidir | Data I/O, lower byte |
| 14 | I/O5 | bidir | Data I/O, lower byte |
| 15 | I/O6 | bidir | Data I/O, lower byte |
| 16 | I/O7 | bidir | Data I/O, lower byte |
| 17 | WE̅ | input | Write Enable, active LOW |
| 18 | A5 | input | Address |
| 19 | A6 | input | Address |
| 20 | A7 | input | Address |
| 21 | A8 | input | Address |
| 22 | A9 | input | Address |

Right side, pins 23–44 (bottom to top, i.e. pin 23 is physically adjacent to pin 22, pin
44 adjacent to pin 1):

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 23 | A10 | input | Address |
| 24 | A11 | input | Address |
| 25 | A12 | input | Address |
| 26 | A13 | input | Address |
| 27 | A14 | input | Address |
| 28 | NC | — | No connect |
| 29 | I/O8 | bidir | Data I/O, upper byte |
| 30 | I/O9 | bidir | Data I/O, upper byte |
| 31 | I/O10 | bidir | Data I/O, upper byte |
| 32 | I/O11 | bidir | Data I/O, upper byte |
| 33 | VDD | power | Supply |
| 34 | GND | power | Ground |
| 35 | I/O12 | bidir | Data I/O, upper byte |
| 36 | I/O13 | bidir | Data I/O, upper byte |
| 37 | I/O14 | bidir | Data I/O, upper byte |
| 38 | I/O15 | bidir | Data I/O, upper byte |
| 39 | LB̅ | input | Lower-byte control (I/O0–I/O7), active LOW |
| 40 | UB̅ | input | Upper-byte control (I/O8–I/O15), active LOW |
| 41 | OE̅ | input | Output Enable, active LOW |
| 42 | A15 | input | Address |
| 43 | A16 | input | Address |
| 44 | A17 | input | Address |

18 address lines (A0–A17) cover 256K words; 16 data lines (I/O0–I/O15) split into
lower/upper byte, independently enabled by LB̅/UB̅.

## Notes

- Fully static/asynchronous — no CLK pin exists. Drive it as a memory-mapped peripheral
  from the FPGA's own address/data bus timing (10 ns access time sets the FPGA's read/
  write state-machine timing budget).
- If both LB̅ and UB̅ are tied permanently LOW, the part behaves as a straight 16-bit-wide
  memory (typical for this "burst buffer" use case) — tie both low unless byte-lane
  control is actually used by the FPGA capture logic.
- CE̅ deselect (HIGH) puts the device into standby (ISB1/ISB2 current, ~7 mW) — useful if
  the FPGA power-gates the SRAM between captures, but not required.
- Decoupling per sourced BOM: 4× 100 nF (C41–C44, one per VDD/GND pair region — this part
  has 2 VDD/2 GND pin pairs, pins 11/12 and 33/34, each needs local 100 nF) + 10 µF bulk
  (C45) + 1 µF (C46).
- **Free upgrade noted by sourcing:** IS61WV51216BLL-10TLI (512K×16, same TSOP-II-44
  pinout/footprint) is a drop-in if more capture depth is wanted — the pin table above is
  unchanged if that substitution is made later.
- PDF retrieved via a third-party mirror (xdevs.com) — not the manufacturer's own site,
  but content confirmed against ISSI's own copyright footer/header ("Integrated Silicon
  Solution, Inc. — www.issi.com", Rev. E, 11/21/07) on the fetched pages. Full PDF not
  saved into `datasheets/` (mirror is not a stable long-term URL); pin table above is
  the durable artifact.
