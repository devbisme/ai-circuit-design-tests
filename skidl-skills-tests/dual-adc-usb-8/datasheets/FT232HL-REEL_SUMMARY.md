# FT232HL-REEL — FTDI FT232H, USB 2.0 HS to FIFO/MPSSE bridge, LQFP-48  [KEYSTONE, U10]

**No FTDI datasheet obtained** (ftdichip.com returns 403 to scripts; LCSC/Mouser return HTML).
**`datasheets/FT232HL-REEL.pdf` is the WRONG FILE** — an unrelated oscillator spec downloaded
in the driver's attempt. The guard hook blocks deleting it. Ignore it.

Rev 2 source: the **Adafruit FT232H breakout schematic** (`adafruit/Adafruit-FT232H-Breakout-PCB`,
file `Adafruit FT232H.sch`, Eagle XML). The nets were parsed from the file here, not read off an
image. It is a **reference design, not the datasheet**. Facts from it are labelled
"REF-DESIGN" below. That is stronger than recollection, but it is not verification.

Symbol: KiCad `Interface_USB:FT232H`. Footprint: `Package_QFP:LQFP-48_7x7mm_P0.5mm`.

| Spec | Value |
|------|-------|
| Package | LQFP-48 7×7 mm |
| Supplies (LCSC field) | 1.62–1.98 V and 2.97–3.63 V |
| Current (LCSC field) | 70 mA — keep the architect's 60/80 mA budget. UNVERIFIED |
| Temp | –40…+85 °C |

## Pinout (KiCad `Interface_USB:FT232H` names; the numbers match the Adafruit Eagle pad map pin for pin)
| Pin | Name | Pin | Name |
|---|---|---|---|
| 1 | XCSI | 25–33 | ACBUS1…ACBUS9 |
| 2 | XCSO | 34 | ~{RESET} |
| 3 | VPHY | 35, 36 | GND |
| 4, 9, 41 | AGND | 37 | VCCA |
| 5 | REF | 38 | VCCCORE |
| 6 / 7 | DM / DP | 39 | VCCD |
| 8 | VPLL | 40 | VREGIN |
| 10, 11, 22, 23, 47, 48 | GND | 42 | TEST |
| 12, 24, 46 | VCCIO | 43 | EEDATA |
| 13–20 | ADBUS0…ADBUS7 | 44 | EECLK |
| 21 | ACBUS0 | 45 | EECS |

The Adafruit part is the QFN-48 (FT232HQ). Its Eagle pad→pin map (1 OSCIN, 3 VPHY, 5 REF, 8 VPLL,
12/24/46 VCCIO, 34 RESET#, 37 VCCA, 38 VCCCORE, 39 VCCD, 40 VREGIN, 42 TEST, 43–45 EEDATA/EECLK/EECS)
is identical to the KiCad LQFP symbol above. Two independent sources agree on the numbering.

## Adafruit reference-design power/aux wiring (parsed nets)
| Pin | Adafruit net | What it shows |
|---|---|---|
| VREGIN 40 | +5V (VBUS) + 10 µF | 5 V-in configuration |
| VCCD 39 | "VCC" net with VCCIO 12/24/46, EEPROM VCC, RESET# pull-up, 10 µF + 2×0.1 µF | **Nothing else drives this net.** The AP2112 3.3 V LDO is on a separate `+3V3` net. So VCCD is the FT232H's internal **3.3 V regulator output** when VREGIN = 5 V |
| VCCCORE 38 | "1.8V" net, 0.1 µF only | 1.8 V core-regulator output; decouple only |
| VCCA 37 | own net, 0.1 µF only | **Not tied to VCCCORE.** Decouple only |
| VPHY 3 / VPLL 8 | each from the VCC (3.3 V) net through its own ferrite, with 10 µF | filtered 3.3 V |
| ~{RESET} 34 | 12 kΩ → VCC (3.3 V) | pull-up |
| REF 5 | 12 kΩ 1 % → GND | PHY bias |
| TEST 42 | GND | |
| AGND/GND/PAD | GND | |
| EEPROM 93LC56B | EECS → CS, EECLK → CLK, **EEDATA → DI directly**, **DO → 2.2 kΩ → EEDATA** | matches our R27 |
| OSCIN/OSCOUT | 12 MHz resonator (3-pin, internal caps) | not applicable to our crystal plus C47/C48 |

## Our configuration (U10) — decided here, for the coder
**3.3 V-in:** VREGIN(40) → V3V3D, **VCCD(39) → V3V3D**, and VCCIO(12, 24, 46) → V3V3D.
VPHY(3) and VPLL(8) → V3V3D, each with local decoupling. VCCCORE(38) → FT_VCORE, decouple only.
VCCA(37) → its own net FT_VCCA, 0.1 µF only.

- **Correction to `net_plan.md`:** it puts VCCD on FT_VCORE (1.8 V). **That is wrong.** In the
  reference design, VCCD is the 3.3 V node that feeds VCCIO. Putting it on 1.8 V would short
  the core regulator to a 3.3 V node or starve the I/O ring. FT_VCORE = **VCCCORE only**.
- With VREGIN at 3.3 V, the internal 5→3.3 V regulator has no headroom. Tying VCCD to the same
  3.3 V rail is FTDI's "3.3 V self-powered" arrangement (from recollection of DS_FT232H §6).
  **This exact config is UNVERIFIED.** Adafruit only demonstrates the 5 V-in config.
- Fallback that the reference design **does** demonstrate: VREGIN ← 5 V, with VCCD as a local
  3.3 V output feeding VCCIO/VPHY/VPLL/EEPROM/RESET pull-up. Its cost is a new net, since the
  FT232H I/O ring is then not V3V3D.

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Pin numbering (all 48 + PAD) | as table | KiCad symbol + Adafruit Eagle pad map agree. **REF-DESIGN**, not datasheet |
| VCCD is a 3.3 V node (regulator output when VREGIN = 5 V), never 1.8 V | 3.3 V | **REF-DESIGN** (Adafruit nets) |
| VCCD tied to 3.3 V with VREGIN = 3.3 V is a valid config | yes | **UNVERIFIED** — recollection of DS_FT232H §6 |
| VCCCORE: 1.8 V output, decouple only | 0.1 µF (Adafruit); ours 0.1 µF + 4.7 µF | **REF-DESIGN** |
| VCCA: decouple only, separate from VCCCORE | 0.1 µF | **REF-DESIGN** (this corrects rev 1, which said "tie to VCCCORE") |
| VPHY/VPLL filtering | ferrite + 10 µF each, from 3.3 V | **REF-DESIGN** |
| RESET# pull-up | 12 kΩ in the reference; our 10 kΩ is equivalent | **REF-DESIGN** |
| REF resistor | 12 kΩ 1 % → GND | **REF-DESIGN** |
| TEST | GND | **REF-DESIGN** |
| EEPROM | 93LC56B; DI = EEDATA, DO → 2.2 kΩ → EEDATA, CS/CLK direct | **REF-DESIGN** (same MPN family as our U11) |
| Sync-245 FIFO mapping | ADBUS0–7 = D0–7; ACBUS0 RXF#, 1 TXE#, 2 RD#, 3 WR#, 4 SIWU#, 5 CLKOUT 60 MHz, 6 OE# | **UNVERIFIED** — FTDI family convention |
| Operating current | ~54–70 mA | **UNVERIFIED** |

## Notes
- SKiDL names: `~{RESET}`, `VCCCORE`, `VCCA`, `VCCD`, `VREGIN`, `VPHY`, `VPLL`, `VCCIO`, `AGND`,
  `GND`, `TEST`, `REF`, `DM`, `DP`, `XCSI`, `XCSO`, `EECS`, `EECLK`, `EEDATA`, `ADBUSn`, `ACBUSn`.
  `VCCIO`, `GND` and `AGND` are multi-pin: connect every instance (use pin numbers or `u10['VCCIO']` for all).
- Decoupling count: the reference uses 8 caps on the FT232H. Our BOM has C49–C53 (5× 0.1 µF),
  C54 0.1 µF, C55 4.7 µF and C56 4.7 µF. With VCCA now on its own cap and no ferrites, VPHY and
  VPLL have **no local cap left** once VCCIO×3, VREGIN/VCCD, VCCA and VCCCORE are served. See
  the handoff: this needs 2 more 0.1 µF, with ferrites optional.
- Before layout, a human should still download DS_FT232H (FT_000288) and check §6.
