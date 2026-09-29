# Sourced BOM — dual_adc_usb (revision 4)

Data source: pcbparts MCP (`jlc_get_part`, `jlc_search`), live JLCPCB mirror, 2026-09-25
(rev 1); 2026-09-26 (rev 2 — C104/C204 trimmer, U11 symbol, R18/R19 value, per phase-4
findings; rev 3 — FT232H VPHY/VPLL ferrite+10µF+0.1µF added, VCCA cap confirmed, per
phase-4 rev-2 BOM-gap flag; rev 4 — reconciled symbol/footprint/note cells against the
block coders' actual code in `circuits/dual_adc_usb/*.py`, per block-coder escalation).
No new part lookups in rev 4 — every change below is a BOM correction to match code
already using a generated symbol, a resolvable footprint, or a corrected net/value; no
MPN, stock, price, or tier changed. Cache disabled (no lookups needed).
Symbols: `find-symbol.py` against the local KiCad 9 symbol index. Footprints: resolved
against `/usr/share/kicad/footprints` with `validate-footprints.py`.

All parts below are JLCPCB **Extended** tier unless noted **Basic**/**Preferred** — this
whole design carries the Extended-tier per-part assembly setup fee except where flagged.

## Active parts and connectors

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| U1 | USBLC6-2SC6 | C2827654 | 106827 | $0.0445 | SOT-23-6 | Extended | Power_Protection:USBLC6-2SC6 | Package_TO_SOT_SMD:SOT-23-6 | Manufacturer TECH PUBLIC (clone/2nd-source of the ST part); ST original C7519 (45792 stock) is the fallback if provenance matters |
| U2 | TPS22919DCKR | C2149796 | 68311 | $0.1249 | SC-70-6 | Extended | dual_adc_usb:TPS22919DCKR | Package_TO_SOT_SMD:SOT-363_SC-70-6 | Generated symbol confirmed in code (`usb_power_in.py`); no stock symbol existed for this SC-70-6 pinout |
| U3, U4 | TLV62569DBVR | C141836 | 241177 | $0.0761 | SOT-23-5 | Extended | Regulator_Switching:TLV62569DBV | Package_TO_SOT_SMD:SOT-23-5 | VFB confirmed 0.6V on datasheet (per architect); ×2 same MPN |
| U5 | TLV75518PDBVR | C2877863 | 9868 | $0.2076 | SOT-23-5 | Extended | Regulator_Linear:TLV75518PDBV | Package_TO_SOT_SMD:SOT-23-5 | |
| U6 | TPS7A2033PDBVR | C2862740 | 230939 | $0.2154 | SOT-23-5 | Extended | dual_adc_usb:TPS7A2033PDBVR | Package_TO_SOT_SMD:SOT-23-5 | Generated symbol confirmed in code (`power_analog.py`); no stock symbol existed |
| U7 | LM27762DSSR | C473398 | 40112 | $1.0085 | WSON-12-EP(2x3) | Extended | Regulator_SwitchedCapacitor:LM27762 | Package_SON:WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65 | **Custom-footprint flag retired**: `Package_SON:WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65` resolves in the standard KiCad footprint library — no generation needed after all |
| U8 | ADS5231IPAGT | C2670079 | **154 (WARN)** | $31.70 | TQFP-64(10x10) | Extended | dual_adc_usb:ADS5231IPAGT | Package_QFP:TQFP-64_10x10mm_P0.5mm | ★ critical, single-source (TI), no pin-compatible 2nd source. Generated symbol confirmed in code (`adc.py`); no stock symbol existed. Stock dropped from 235 (architecture) to 154 — still >100 but tightening. Re-check before placing the order |
| U9 | GW1NR-LV9QN88PC6/I5 | C5799578 | **173 (WARN)** | $23.26 | QFN-88 10x10 0.4mm | Extended | dual_adc_usb:GW1NR-LV9QN88PC6 | Package_DFN_QFN:ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm | ★ critical. Generated symbol confirmed in code (`fpga.py`); no stock symbol existed. Only QFN-88/10x10/0.4mm footprint in the library is vendor-labeled ArtInChip (unrelated IC) but matches pin count/pitch/body; **confirm exposed-pad size (6.74×6.74mm) against the Gowin mechanical drawing** before layout |
| U10 | FT232HL-REEL | C51997 | 3224 | $9.362 | LQFP-48(7x7) | Extended | Interface_USB:FT232H | Package_QFP:LQFP-48_7x7mm_P0.5mm | ★ critical |
| U11 | 93LC56BT-I/OT | C190271 | 11173 | $0.4385 | SOT-23-6 | Extended | dual_adc_usb:93LC56BT-I_OT | Package_TO_SOT_SMD:SOT-23-6 | Generated symbol required — `Memory_EEPROM:93LCxxB` is the 8-pin DIP/SOIC pinout and would miswire all 6 pins of this SOT-23-6 part (datasheet phase escalation) |
| U101, U201 | OPA356AIDBVR | C183100 | 1382 | $1.2342 | SOT-23-5 | Extended | Amplifier_Operational:OPA356xxDBV | Package_TO_SOT_SMD:SOT-23-5 | Do not substitute — CM headroom math in `ic_selection.md` §4 depends on this exact part |
| U102, U202 | THS4551IRGTR | C2869590 | **469 (WARN)** | $4.3457 | QFN-16-EP(3x3) | Extended | Amplifier_Difference:THS4551xRGT | Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm | Stock dropped from 765 (architecture) to 469 — now below the 500 WARN line. Second source ADA4940-1ACPZ-R7 exists (637 stock, 2.5× cost) if this drops further |
| X1 | SX3M40.000B10F20TNN | C5452689 | 2334 | $0.3232 | SMD3225-4P | Extended | dual_adc_usb:SX3M40.000B10F20TNN | Oscillator:Oscillator_SMD_SeikoEpson_SG8002CE-4Pin_3.2x2.5mm | ★ critical. Generated symbol confirmed in code (`clock.py`); no stock symbol existed. Footprint is a generic vendor-labeled 4-pad 3225 pattern substituted for pad match (no SCTF-labeled footprint exists) — confirm against the SX3M40 datasheet pad diagram before layout |
| Y1 | X322512MSB4SI | C9002 | 71028 | $0.0947 | SMD3225-4P | **Basic** | Device:Crystal_GND24 | Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm | CL = 20pF confirmed from datasheet spec field — fixes C47/C48 = 33pF as the architect assumed. **Symbol corrected to `Device:Crystal_GND24`** (4-pin, pins 2/4 case-ground) to match `usb_bridge.py`; the previous `Device:Crystal` (2-pin) row was wrong for this part |
| J1 | TYPE-C-31-M-12 | C165948 | 89676 | $0.1855 | USB-C SMD 16P | Extended | Connector:USB_C_Receptacle_USB2.0_16P | Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12 | **Symbol corrected to `Connector:USB_C_Receptacle_USB2.0_16P`** to match the pin-by-number mapping in `usb_power_in.py` (A4/A9/B4/B9 VBUS, A1/A12/B1/B12/S1 GND, A5 CC1, B5 CC2, A6/B6 DP, A7/B7 DN, A8/B8 NC) — the generic USB-C symbol family, not a vendor-specific one. Footprint unchanged, exact vendor match |
| J2, J3 | KH-BNC50-3511 | C2837587 | 5979 | $0.9306 | THT right-angle BNC | Extended | Connector:Conn_Coaxial | ProjectLocal:BNC_Kinghelm_KH-BNC50-3511_Horizontal | **Custom-footprint flag retired**: a project-local footprint `ProjectLocal:BNC_Kinghelm_KH-BNC50-3511_Horizontal` was generated (in `footprints/ProjectLocal.pretty/`) and is now wired in `afe_ch_a.py`/`afe_ch_b.py`. HARD requirement (THT for mechanical retention) is met by this footprint |
| J4 | 2.54mm header 2x5 THT | C492422 | 109374 | $0.071 | THT | Extended | Connector_Generic:Conn_02x05_Odd_Even | Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical | JTAG, VREF=1.8V |
| J5 | 2.54mm header 1x6 THT | C37208 | 306850 | $0.0415 | THT | Extended | Connector_Generic:Conn_01x06 | Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical | Aux: TRIG_IN/OUT, GPIO1/2, 3V3, GND |
| D101, D201 | BAV199 | C5184419 | 77581 | $0.0138 | SOT-23 | Extended | dual_adc_usb:BAV199 | Package_TO_SOT_SMD:SOT-23 | Generated symbol confirmed in code (`afe_ch_a.py`/`afe_ch_b.py`) — 3-pin series-pair pinout. `find-symbol.py` had PREFIX-matched this to `Diode:BAV19`, a **single** diode, which was rejected as wrong topology |
| D1, D2, D3 | LED green 0603 | C22371297 | 394695 | $0.0146 | 0603 | Extended | Device:LED | LED_SMD:LED_0603_1608Metric | 517–527nm, 3.1V Vf, 10mA |
| FB1, FB2, FB3, FB4 | 600Ω@100MHz ferrite bead | C108301 (Chilisin PBY160808T-601Y-N) | 709763 | $0.0113 | 0603 | Extended | Device:FerriteBead | Inductor_SMD:L_0603_1608Metric | 1A rated, 200mΩ DCR — meets ≥500mA. FB2 feeds X1's XO_VDD supply from V3V3A (`clock.py`) — the clock block's own local decoupling, not part of the ADC/FPGA rail set. **FB3/FB4 added (rev 3)**: FT232H VPHY/VPLL ferrites per phase-4 BOM-gap flag, same MPN reused |
| L1, L2 | 2.2µH power inductor | C167747 (Changjiang FNR3015S2R2MT) | 62192 | $0.0431 | SMD 3x3mm | Extended | Device:L | Inductor_SMD:L_Changjiang_FNR3015S | 2A Isat/rated, 78mΩ DCR (spec: Isat ≥1A, DCR ≤0.1Ω ✓). Exact vendor-matched footprint |
| C104, C204 | Knowles JZ300 ceramic piston trimmer (5.5–30pF, 125V) | C3273397 | **123 (WARN)** | $4.4366 | SMD 4.5x3.2mm | Extended | Device:C_Variable | Capacitor_SMD:C_Trimmer_Voltronics_JZ | **Replaces LXRW19V330-050** (that part is a voltage-tuned varactor, not a hand trimmer — see `## Decisions`). True mechanical ceramic trimmer; 5.5–30pF range covers the 23.8pF attenuator-compensation target with margin. Footprint resolves exactly (Knowles acquired Voltronics; the JZ-series body/pad geometry matches the KiCad `C_Trimmer_Voltronics_JZ` land pattern — 2 SMD pads at 3.9mm pitch). Stock 123 is WARN (just above the 100 FAIL line) — re-check before order; single-source at this LCSC listing |

## Signal-path passives (per channel; ×2 — ch A / ch B)

| Function | MPN | LCSC# | Stock | Package | Refs | Notes |
|---|---|---|---|---|---|---|
| Divider top R_T 909kΩ 1% | FRC1206F9093TS | C2933765 | 36497 | 1206 | R101/R201 | Exact 909k, not 910k |
| Divider top C_T 22pF C0G 1% | GQM1875C2E220FB12D (Murata) | C2360437 | 5645 | **0603** | C101/C201 | **Deviation:** architect specified 0805/≥100V; the only 0805/100V option had 37 stock (FAIL). Substituted a 0603/250V/±1% part — smaller package (preferred) and higher voltage margin, same electrical value |
| Divider bottom R_B 100kΩ 1% | 0603WAF1003T5E | C25803 | 22.9M | 0603 | R102/R202 | Basic tier |
| Divider bottom C_B1 150pF C0G 1% | 06035A151FAT2A | C597138 | 4009 | 0603 | C102/C202 | Only 1% C0G option with usable stock; Extended |
| Divider bottom C_B2 15pF C0G 2% | 0603CG150G500NT | C2836768 | 8727 | 0603 | C103/C203 | |
| Buffer series R_S 1.00kΩ 1% | 0603WAF1001T5E | C21190 | 23.9M | 0603 | R103/R203 | Basic tier |
| Buffer input C_S 8.2pF C0G | FCC0603N8R2C500CT (Fenghua) | C1685 | 95293 | 0603 | C105/C205 | **Preferred** tier |
| MFB R1a/R1b 1.00kΩ 0.1% | FRH0603B1001TS | C49196685 | 421261 | 0603 | R104,R105/R204,R205 | Matched pair — buy from one reel/lot for CMRR |
| MFB R2a/R2b 909Ω 1% | FRC0603F9090TS | C2933265 | 35730 | 0603 | R106,R107/R206,R207 | Exact 909Ω, not 910Ω |
| MFB R3a/R3b 499Ω 1% | RC0603FR-07499RL | C137714 | 768935 | 0603 | R108,R109/R208,R209 | |
| MFB C1 (diff) 27pF C0G 5% | FCC0603N270J500CT | C5137568 | 94323 | 0603 | C108/C208 | |
| MFB C2a/C2b 12pF C0G 5% | CL10C120JB8NNNC (Samsung) | C38523 | 634511 | 0603 | C109,C110/C209,C210 | Basic tier |
| ADC series R 49.9Ω 1% | 0402WGF499JTCE | C25120 | 1.5M | 0402 | R110,R111/R210,R211 | Basic tier |
| ADC diff C 56pF C0G | FCC0402N560J500AT | C5137588 | 31532 | 0402 | C113/C213 | |
| Decoupling 0.1µF X7R | CL05B104KB54PNC | C307331 | 11.7M | 0402 | C106,C107,C111,C114/C206,C207,C211,C214 | Basic tier — used for all 0.1µF X7R 0402 refs project-wide |
| Decoupling 1µF X7R | TCC0402X7R105K160AT | C49210445 | 34184 | 0402 | C112/C212 | 16V rated |

## Power, reference and misc passives

| Function | MPN | LCSC# | Stock | Package | Refs | Notes |
|---|---|---|---|---|---|---|
| USB-C CC Rd 5.1kΩ 1% | 0603WAF5101T5E | C23186 | 26.2M | 0603 | R1, R2 | Basic tier |
| VBUS pre-switch cap 4.7µF 10V X7R | TCC0603X7R475K100CT | C18185770 | 222530 | 0603 | C1 | |
| V5 bulk 10µF / HF 0.1µF | C19702 (10µF) / C307331 (0.1µF) | C19702 / C307331 | 11.3M / 11.7M | 0603 / 0402 | C2, C3 | Basic tier both |
| Buck 3V3 in/out 10µF/22µF | C19702 / C45783 | C19702 / C45783 | 11.3M / 4.3M | 0603 / 0805 | C4 / C5 | Basic tier both |
| Buck 3V3 FB top 100kΩ 1% | 0603WAF1003T5E | C25803 | 22.9M | 0603 | R3 | Basic tier |
| Buck 3V3 FB bottom 22.1kΩ 1% | FRC0603F2212TS | C2960862 | 492491 | 0603 | R4 | Exact 22.1k |
| Buck 1V2 in/out 10µF/22µF | same as above | C19702 / C45783 | — | 0603 / 0805 | C6 / C7 | |
| Buck 1V2 FB top/bottom 100kΩ 1% | 0603WAF1003T5E | C25803 | 22.9M | 0603 | R5, R6 | Basic tier, same part both places |
| 1V8 LDO in/out 1µF | TCC0402X7R105K160AT | C49210445 | 34184 | 0402 | C8, C9 | |
| Power LED R 1kΩ | 0603WAF1001T5E | C21190 | 23.9M | 0603 | R7 | Basic tier |
| 3V3A LDO in/out/bulk 1µF/1µF/10µF | C49210445 / C49210445 / C19702 | — | — | 0402/0402/0603 | C10 / C11 / C12 | |
| LM27762 CIN/C1/CP/COUT+/COUT- | 2.2µF/1µF/4.7µF/2.2µF/2.2µF X7R | C99228 / C49210445 / C18185770 / C99228 / C99228 | 496374 / 34184 / 222530 / — / — | 0603 | C13/C14/C15/C16/C17 | |
| LM27762 FB+ top 174kΩ 1% | 0603WAF1743T5E | C22890 | 36603 | 0603 | R8 | |
| LM27762 FB+ bottom 100kΩ 1% | 0603WAF1003T5E | C25803 | 22.9M | 0603 | R9 | Basic tier |
| LM27762 FB− top 64.9kΩ 1% | FRC0603F6492TS | C2960807 | 163367 | 0603 | R10 | |
| LM27762 FB− bottom 100kΩ 1% | 0603WAF1003T5E | C25803 | 22.9M | 0603 | R11 | Basic tier |
| ADC ISET 56.2kΩ 1% | FRC0603F5622TS | C2930117 | 195526 | 0603 | R12 | Exact 56.2k, not 56k |
| ADC REFT/REFB series 2.0Ω 1% | 0603WAF200KT5E | C22977 | 1.14M | 0603 | R13, R14 | Basic tier |
| ADC REFT/REFB cap 0.1µF | C307331 | C307331 | 11.7M | 0402 | C18, C19 | Basic tier |
| ADC CM caps 0.1µF/1µF | C307331 / C49210445 | — | — | 0402 | C20, C21 | |
| ADC AVDD decoupling 0.1µF×3, 10µF | C307331 ×3 / C19702 | — | — | 0402 / 0603 | C22–C25 | |
| ADC VDRV decoupling 0.1µF×4, 10µF | C307331 ×4 / C19702 | — | — | 0402 / 0603 | C26–C30 | |
| ADC STPD pull-down 10kΩ | 0603WAF1002T5E | C25804 | 23.1M | 0603 | R15 | Basic tier |
| XO decoupling 0.1µF/1µF | C307331 / C49210445 | — | — | 0402 | C31, C32 | |
| Clock series R 33Ω 1% | 0603WAF330JT5E | C23140 | 5.8M | 0603 | R16, R17 | Basic tier |
| FPGA decoupling 0.1µF ×11 | C307331 | C307331 | 11.7M | 0402 | C33–C43 | Basic tier |
| FPGA bulk 10µF/10µF/4.7µF | C19702 / C19702 / C18185770 | — | — | 0603 | C44, C45, C46 | |
| FPGA MODE0/1 pull-down 1kΩ | 0603WAF1001T5E | C21190 | 23.9M | 0603 | R18, R19 | **Changed from 10kΩ per Gowin UG284** MODE-pin guidance (datasheet phase finding); same MPN as R7/R21/R22. Basic tier |
| FPGA RECONFIG_N pull-up 10kΩ | 0603WAF1002T5E | C25804 | 23.1M | 0603 | R20 | Basic tier |
| LED resistors 1kΩ | 0603WAF1001T5E | C21190 | 23.9M | 0603 | R21, R22 | Basic tier |
| Trigger series R 100Ω 1% | 0603WAF1000T5E | C22775 | 12.4M | 0603 | R23, R24 | Basic tier |
| FT232H crystal load caps 33pF C0G | 0402CG330J500NT | C1562 | 1.1M | 0402 | C47, C48 | Basic tier; confirmed by Y1's 20pF CL spec |
| FT232H decoupling 0.1µF×6, 4.7µF×2 | C307331 ×6 / C18185770 ×2 | — | — | 0402 / 0603 | C49–C54, C55, C56 | **Corrected per `usb_bridge.py` (FT232H now runs the 5 V-in config, driver decision: VREGIN ← V5, VCCD is the internal 3.3 V regulator output feeding local net FT_3V3)**: C49 0.1µF is on VREGIN/V5, not VCCD; C50/C51/C52 0.1µF are the three VCCIO pins (FT_3V3); C53 0.1µF is VCCA (its own cap, confirmed not shared with VCCCORE per phase-4 rev-2 finding); C54 0.1µF + C55 4.7µF are VCCCORE; **C56 4.7µF is on FT_3V3 (the VCCD regulator output bulk cap)**, not a second VCCCORE cap |
| FT232H VPHY/VPLL ferrite 600Ω@100MHz | PBY160808T-601Y-N (Chilisin) | C108301 | 709763 | 0603 | FB3, FB4 | **New (rev 3)**: closes phase-4 BOM gap; reuses FB1/FB2 MPN; 1A/200mΩ meets ≥200mA |
| FT232H VPHY/VPLL bulk 10µF X5R 10V | C19702 | C19702 | 11.3M | 0603 | C57, C59 | **New (rev 3)**: reuses V5-bulk/buck part, ≥6.3V spec met |
| FT232H VPHY/VPLL local 0.1µF X7R | CL05B104KB54PNC | C307331 | 11.7M | 0402 | C58, C60 | **New (rev 3)**: reuses project-wide 0.1µF MPN |
| FT232H REF 12.0kΩ 1% | 0603WAF1202T5E | C22790 | 1.3M | 0603 | R25 | Basic tier |
| FT232H RESET# pull-up 10kΩ | 0603WAF1002T5E | C25804 | 23.1M | 0603 | R26 | Basic tier |
| EEPROM DO series 2.2kΩ | FRC0603J222 TS | C2907117 | 2.69M | 0603 | R27 | 5% — value not tolerance-critical |

## Status

No part failed to source. Every ref designator above appears once (or once per matched
pair) in `sourced_bom.csv`. Rev 3 adds FB3, FB4, C57, C58, C59, C60 for the FT232H
VPHY/VPLL supply filtering (phase-4 BOM gap) — all new lines reuse existing MPNs. See
`handoffs/03_sourcing.md` for the WARN-stock, custom-footprint and symbol-needed
carry-forward list.
