---
phase: 04_datasheets
agent: datasheet-librarian
circuit: dual_adc_usb
written: 2026-09-26T12:00:00Z
status: partial
revision: 2
next_phase: 05_coding
---

# Phase 4 handoff — Datasheets (revision 2)

Revision 2 closes the driver's three follow-ups: the FT232H power/aux wiring, the GW1NR-9 per-pin
names and PSRAM bank, and the JZ300 summary. Rev-1 content not mentioned here still stands.

## Decisions
- **REV 2 — FT232H power wiring, from the Adafruit FT232H breakout schematic.** The Eagle XML nets were parsed here; this is a **reference design, not the datasheet**.
  - Nets: VCCD + VCCIO×3 + EEPROM VCC + RESET# pull-up are on one 3.3 V net that **only VCCD drives**, so VCCD is the internal 3.3 V regulator output. VCCCORE is 1.8 V, 0.1 µF only. **VCCA has its own 0.1 µF and is not tied to VCCCORE** (this corrects rev 1). VPHY and VPLL each get ferrite + 10 µF from 3.3 V. REF is 12 k 1 % to GND, TEST to GND, RESET# has a 12 k pull-up. EEPROM: DI = EEDATA, DO → 2.2 k → EEDATA.
  - The Eagle pad map matches the KiCad `Interface_USB:FT232H` numbering on all 48 pins.
  - **Our config: VREGIN = V3V3D and VCCD = V3V3D** (3.3 V-in, as the net plan intends). Adafruit feeds VREGIN from 5 V. The 3.3 V-in variant is still UNVERIFIED (see below).
  - **`net_plan.md` correction for the coder: VCCD is NOT on FT_VCORE.** FT_VCORE = VCCCORE(38) only.
- **REV 2 — GW1NR-9 per-pin names verified from vendor data.** Sources: Gowin IDE package file `GW1NR-9-PSRAM/QFN88.json`, a GitHub mirror that `device_package.csv` maps to GW1NR-LV9QN88PC6/I5, and the Sipeed Tang Nano 9K schematic. The two agree on every pin.
  - EasyEDA was wrong on 5 pins: **3 IOT2A, 10 IOL15A/GCLKT_6, 11 IOL16B, 13 IOL21B, 15 IOL25B**.
  - **DONE and READY are not bonded on QN88P.**
  - `symbols/dual_adc_usb.kicad_sym` was corrected on those 5 names. The pin count is still 89. SKiDL loads it and `find-symbol.py` reports EXACT. UG803 itself is behind a Gowin login.
- **REV 2 — C104/C204 JZ300.** Summary added. The **TC is −1500 ± 1000 ppm/°C**, not C0G: the 23.8 pF compensation drifts −0.3…−1.5 pF over a 25 °C swing. That is an **architect FYI**, and nothing was re-decided here. Orientation: rotor → GND, hot → divider node.
- `datasheets/FT232HL-REEL.pdf` is a **wrong file** (an unrelated oscillator spec the driver downloaded). The guard hook blocks deleting it; ignore it. The JZ series drawing was not kept as a PDF (`fetch-datasheet.py` rejects it as "mostly JZ500"); the summary cites it.
- *(rev 1)* The LXRW19V330-050 escalation is **resolved by sourcing rev 2** (it was replaced by JZ300). `LXRW19V330-050_SUMMARY.md` is now obsolete.
- **U11 symbol changed.** KiCad `Memory_EEPROM:93LCxxB` is the 8-pin pinout (1 CS…4 DO, 5 GND, 8 VCC). The SOT-23-6 part is 1 DO, 2 VSS, 3 DI, 4 CLK, 5 CS, 6 VCC, so that symbol would miswire all 6 pins. Use the generated `dual_adc_usb:93LC56BT-I_OT`. The `sourced_bom.csv` symbol cell for U11 is wrong and should be routed to part-sourcer.
- **U9 pin 12 is VCCIO3 (Gowin UG119 Table 3-8), not "VCCX/VCCO0" (EasyEDA).** The generated symbol follows Gowin.
- **Gowin recommends 1 kΩ MODE pull-downs** (UG284 §MODE). R18/R19 are 10 kΩ against internal weak pull-ups. Recommend changing them to 1 kΩ (C21190 is already in the BOM). This is a driver/sourcer call.
- TLV755P family PDF: `fetch-datasheet.py` rejected it because it never names "TLV75518". It was checked by hand (the family covers the 1.8 V option) and copied in as `TLV75518PDBVR.pdf`.
- Skipped, as generic: J1, J4, J5, LEDs, and all standard R/C. Worklist numbers for C101 (250 V C0G) and R101 (1206) are covered by JLC data and are not critical.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `datasheets/<MPN>_SUMMARY.md` (20 files; JZ300 is new, LXRW is obsolete) | specs, exact pinout, load-bearing facts with source | Before coding the block that uses the part |
| `datasheets/*.pdf` (16 files) | primary docs; the Gowin docs are UG119 (as `GW1NR-LV9QN88PC6_I5.pdf`), `GW1NR-9_DS117.pdf` and `GW1NR-9_UG284.pdf` | When a summary is not enough |
| `symbols/dual_adc_usb.kicad_sym` | 7 generated symbols: ADS5231IPAGT, GW1NR-LV9QN88PC6, TPS7A2033PDBVR, TPS22919DCKR, SX3M40.000B10F20TNN, BAV199, 93LC56BT-I_OT | Coding: `Part('dual_adc_usb','<name>')`, with `symbols/` on KICAD9_SYMBOL_DIR |

## Summaries by block
| block_id | summary files |
|---|---|
| `usb_power_in` | `datasheets/TPS22919DCKR_SUMMARY.md`, `datasheets/USBLC6-2SC6_SUMMARY.md` |
| `power_digital` | `datasheets/TLV62569DBVR_SUMMARY.md`, `datasheets/TLV75518PDBVR_SUMMARY.md`, `datasheets/FNR3015S2R2MT_SUMMARY.md` |
| `power_analog` | `datasheets/TPS7A2033PDBVR_SUMMARY.md`, `datasheets/LM27762DSSR_SUMMARY.md` |
| `afe_ch_a`, `afe_ch_b` | `datasheets/OPA356AIDBVR_SUMMARY.md`, `datasheets/THS4551IRGTR_SUMMARY.md`, `datasheets/BAV199_SUMMARY.md`, `datasheets/KH-BNC50-3511_SUMMARY.md`, `datasheets/JZ300_SUMMARY.md` |
| `adc` | `datasheets/ADS5231IPAGT_SUMMARY.md`, `datasheets/PBY160808T-601Y-N_SUMMARY.md` |
| `clock` | `datasheets/SX3M40.000B10F20TNN_SUMMARY.md`, `datasheets/PBY160808T-601Y-N_SUMMARY.md` |
| `fpga` | `datasheets/GW1NR-LV9QN88PC6_I5_SUMMARY.md` |
| `usb_bridge` | `datasheets/FT232HL-REEL_SUMMARY.md`, `datasheets/93LC56BT-I_OT_SUMMARY.md`, `datasheets/X322512MSB4SI_SUMMARY.md` |

## Unverified keystone facts
| Part | Fact | Best available answer | What would close it |
|---|---|---|---|
| `FT232HL-REEL` | 3.3 V-in config (VREGIN = VCCD = V3V3D) is valid | Yes, from recollection of FTDI's self-powered 3.3 V figure. The Adafruit reference design shows only the 5 V-in config (VCCD = 3.3 V output). **Fallback if in doubt:** VREGIN ← V5, and VCCD feeds VCCIO/VPHY/VPLL/U11/RESET pull-up as a local FT_3V3 net | DS_FT232H §6 (browser download) |
| `FT232HL-REEL` | Sync-245 ACBUS mapping, operating current | ACBUS0 RXF#…6 OE#; 60/80 mA budget | DS_FT232H §3/§4 |
| `GW1NR-LV9QN88PC6/I5` | PSRAM on bank 3 | Bank 3. The Tang Nano 9K runs only bank 3 at 1.8 V, and QN88→QN88P changes only bank 3. Reference design plus inference; no Gowin text names the bank | UG803 / UG119 PSRAM section |
| `GW1NR-LV9QN88PC6/I5` | MODE2 (unbonded) = 0 → MODE0/1 low = AUTOBOOT | The Tang Nano 9K boots from flash with 4.7 k pull-downs on MODE0/1 (reference design) | UG803 / UG290 |
| `GW1NR-LV9QN88PC6/I5` | Dynamic power | Only static typ values are known | Gowin Power Estimator |
| `SX3M40.000B10F20TNN` | RMS jitter ≤ 3 ps | **Open question.** The datasheet has no jitter spec. Named assumption: a typical 3225 CMOS XO is 1–3 ps RMS (12 k–20 MHz), acceptable for ≤ 40 MSPS at ~60 dB SNR | SCTF phase-noise data, or an XO with a spec |
| `X322512MSB4SI` | CL = 20 pF (sets C47/C48 = 33 pF) | **Open question.** Named assumption: CL = 20 pF from two distributor fields | YXC datasheet PDF |

## Next phase must
0. **Rev 2 items, which take precedence over the items below and over `net_plan.md`:**
   - **U10 FT232H:**
     - VREGIN(40), **VCCD(39)**, VCCIO(12/24/46), VPHY(3) and VPLL(8) → V3V3D.
     - **VCCCORE(38) alone** → FT_VCORE with C54 + C55. VCCA(37) → its own net `FT_VCCA` + one 0.1 µF (take it from C49–C53).
     - REF(5) → R25 12.0 k → GND. TEST(42) and AGND/GND → GND. RESET# → R26 → V3V3D.
     - U11: CS/CLK direct, DI = FT_EEDATA, DO → R27 2.2 k → FT_EEDATA.
     - **BOM gap:** VPHY and VPLL have no local cap left. They need 2× 0.1 µF more (the reference design adds ferrite + 10 µF each). Route this to the driver/sourcer; do not silently drop it.
   - **U9 GW1NR:**
     - There is **no DONE/READY pin**. Pin 10 is IOL15A/GCLKT_6, a bank-3 I/O at 1.8 V.
     - JTAG: TMS 5, TCK 6, TDI 7, TDO 8. JTAGSEL_N 4, RECONFIG_N 9 (R20 → V1V8), MODE0 88, MODE1 87 (R18/R19 1 k → GND).
     - GCLKT_4 35 ← FPGA_CLK; GCLKT_3 52 ← FT_CLKOUT. All verified against vendor data.
   - **C104/C204 JZ300** (`Device:C_Variable`): pin 1 → A_DIV/B_DIV (hot), pin 2 → GND (rotor). Item 11 below is obsolete.
1. **Symbols.** Use `dual_adc_usb:` for U8, U9, U6, U2, X1, D101/D201 and **U11**. Do not use `Memory_EEPROM:93LCxxB` or `Diode:BAV19`. Put `symbols/` on KICAD9_SYMBOL_DIR (`rules/environment.md`).
2. **U9 GW1NR-9:** reference pins **by number**.
   - VCC 1/22/45/66 → V1V2. VCCX/VCCIO0 64/67/78, VCCIO1 58 and VCCIO2 23/44 → V3V3D. **VCCIO3 12 → V1V8**.
   - VSS 2/21/24/43/46/65 and EP **89** → GND.
   - 3.3 V I/O exist only on bank 1 (48–57, 59–63, 68–77 = 25) and bank 2 (17–20, 25–42, 47 = 23), which is **48 total**. The net plan needs 44.
   - FPGA_CLK → 35; FT_CLKOUT → 52. Bank 3 (3–11, 13–16, 79–88) takes only JTAG/RECONFIG_N/MODE.
   - JTAGSEL_N (pin 4) has an internal pull-up. UG284 shows a 4.7 kΩ pull-up on RECONFIG_N to the bank voltage. R20 → V1V8 is correct. (DONE/READY are not bonded on QN88P.)
3. **U8 ADS5231:**
   - Pins as in `net_plan.md`, all verified. The complementary inputs are `~{INA}` (51) and `~{INB}` (62).
   - Tie SEL(1), OEB(6), MSBI/SEN(41) and OEA/SCLK(42) to GND explicitly. INT/EXT(56) → V3V3A.
   - REFT/REFB each take 2 Ω + 0.1 µF.
4. **U102/U202 THS4551:**
   - FB–(1) joins OUT–(11) on A_FON, and FB+(4) joins OUT+(10) on A_FOP. These are separate pins, so both must be wired.
   - Pin 12 is named `~{PD}` in the KiCad symbol but is active-HIGH enable: tie it to V3V3A.
   - EP (17) → GND.
5. **U101 OPA356:** the KiCad symbol names are `~`/`+`/`-`, so use numbers: 1 Out, 2 V–, 3 +In, 4 –In, 5 V+.
6. **U7 LM27762:**
   - The KiCad symbol pin names are `C+`(10), `C-`(9), `OUT+`, `OUT-`, `FB+`, `FB-`, `EN+`, `EN-`, `CP`, `PGOOD`, and `PAD`(13) → GND.
   - PGOOD → GND is what the datasheet directs.
7. **U6 TPS7A2033 (generated):** 1 IN, 2 GND, 3 EN, 4 N/C, 5 OUT. EN has an internal 500 kΩ pull-down, so tie it to V5.
8. **U2 TPS22919 (generated):** 1 IN, 2 GND, 3 ON, 4 NC (leave open), 5 QOD, 6 VOUT.
9. **X1 (generated):** 1 `Tri-State` (tie to XO_VDD; open also works), 2 GND, 3 `Output`, 4 `Vdd`.
10. **D101/D201 BAV199 (generated):** 1 `A` → VN_AFE, 2 `K` → VP_AFE, 3 `COM` → A_DIV. Verified.
11. *(obsolete: LXRW was replaced by JZ300, see item 0)*

## Carried forward
- **No PDF obtained:**
  - FT232HL-REEL (keystone): still no FTDI PDF. Rev 2 works from the Adafruit reference schematic. `datasheets/FT232HL-REEL.pdf` is a WRONG file; ignore it.
  - X322512MSB4SI: LCSC links return HTML.
  - USBLC6-2SC6 (TECH PUBLIC), FNR3015S2R2MT and PBY160808T-601Y-N: ordinary parts, JLC data only. USBLC6's "0.35 pF" is suspect (ST's part is ~2.5–3.5 pF), but it is harmless for USB HS.
- **Custom footprints (mechanical data captured):**
  - U7 WSON-12 DSS 2×3 mm: see the mechanical pages in `LM27762DSSR.pdf`.
  - J2/J3 BNC: 2×Ø2.0 pegs 10.1 mm apart and 2×Ø0.9 leads 2.5 mm apart, 5.05 mm behind the pegs (`KH-BNC50-3511_SUMMARY.md`, drawing p.1).
  - C104/C204: JZ300 uses the stock `C_Trimmer_Voltronics_JZ` footprint. The drawing's land is 0.9×1.4 mm at 3.9 mm pitch, which matches it.
- **U9 EP confirmed.** Package EP is 6.64/6.74/6.84 mm and the recommended land is 6.8 mm (UG119 p.22–23), so the ArtInChip 6.74 mm EP footprint (pad "89") is OK.
- **X1 footprint confirmed.** The SeikoEpson SG8002CE 3225 lands (1.4×1.2 at 2.4×1.9 pitch) cover the SCTF pads (0.9×0.65; recommended land 1.2×0.95 at 2.2×1.75, p.4). Pin 1 is at the same corner, so the footprint is OK.
- TPS7A2033 θJA (DBV) is 187.1 °C/W, which gives TJ ≈ 101 °C at TA 50 °C (0.271 W worst case). That is under 125 °C, so there is no need to move X1.
- The kipart MCP server failed to connect. Symbols were generated with the `kipart` 2.8.0 CLI (CSV in the session scratchpad, not kept).

## Do not redo
- All 7 generated symbols. Pin counts were verified (177 pins total), all load in SKiDL, `find-symbol.py` reports EXACT, and name lookups (`INA` vs `~{INA}`, `GND` vs `AGND`) resolve exactly.
- Verified pinouts: ADS5231, OPA356, THS4551, LM27762, TLV62569, TLV75518P, TPS7A20, TPS22919, BAV199, 93LC56B OT, SX3M, and the GW1NR power/bank map.
- VFB values: TLV62569 0.600 V ±2 %; LM27762 +1.200 / –1.220 V. The architecture's dividers stand.

## Receipt
- Rev 2 (closing pass only): 1 summary added (JZ300), 2 rewritten (FT232H, GW1NR). The GW1NR symbol was corrected on 5 pin names and re-verified: 89 pins, EXACT, loads in SKiDL.
- Closed: GW1NR JTAG/JTAGSEL_N/RECONFIG_N/MODE/GCLK names (vendor data plus reference design). DONE/READY are shown to be unbonded.
- FT232H pin numbering and aux wiring now come from a reference design, not the datasheet.
- Unverified keystone facts: 8 → 7. The FT232H row is narrowed to the 3.3 V-in config; X1 jitter and Y1 CL are left as named assumptions.
- New flags: the net_plan VCCD/FT_VCORE error, 2 missing 0.1 µF caps (VPHY/VPLL), and the JZ300 TC of −1500 ppm/°C (architect FYI).
- Keystone PDFs: 11 with, 2 without (FT232HL-REEL, X322512MSB4SI). Cache disabled. `status: partial`.
