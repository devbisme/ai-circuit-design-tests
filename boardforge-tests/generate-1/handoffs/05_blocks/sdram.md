---
phase: 05_blocks/sdram
agent: skidl-block-coder
circuit: dual_adc_10msps
written: 2026-10-17T00:00:00Z
status: complete
revision: 2
next_phase: 05_coding
---
# Block handoff - sdram

## Decisions
1. Signature unchanged: `sdram(sd_dq, sd_a, sd_ba, sd_clk, sd_cke, sd_cs_n, sd_ras_n, sd_cas_n, sd_we_n, sd_ldqm, sd_udqm, v3v3, gnd)`.
2. Buses indexed 0 = LSB: `sd_dq` 16 (U801 pins 2,4,5,7,8,10,11,13,42,44,45,47,48,50,51,53), `sd_a` 12 (A0-A9 pins 23-26,29-34; A10/AP 22; A11 35), `sd_ba` 2 (BS0 20, BS1 21).
3. Direction: senses all address/control/clock (FPGA drives them); bidirectional sd_dq; consumes v3v3, gnd.
4. SD_CLK -> R801 22R -> local `SD_CLK_M` -> U801 CLK 38 (net plan says R801 at FPGA end - place accordingly). R802 10k CKE -> GND, R803 10k CS# -> +3V3.
5. Power by pin number: VDD 1/14/27 + VDDQ 3/9/43/49 on +3V3, C801-C807 100n one per pin, C808 10u bulk; VSS 28/41/54 + VSSQ 6/12/46/52 on GND.

- Rev 2: every MPN-bearing part now also sets `fields['LCSC']` from sourcing/sourced_bom.csv (script-checked per ref: 0 mismatches); helpers that take `mpn` gained an `lcsc` param right after it.

## Artifacts
| File | Contains |
|---|---|
| `circuits/dual_adc_10msps/sdram.py` | @SubCircuit sdram, 12 parts |

## Next phase must
- Emit: `sdram(sd_dq=SD_DQ, sd_a=SD_A, sd_ba=SD_BA, sd_clk=SD_CLK, sd_cke=SD_CKE, sd_cs_n=SD_CS_N, sd_ras_n=SD_RAS_N, sd_cas_n=SD_CAS_N, sd_we_n=SD_WE_N, sd_ldqm=SD_LDQM, sd_udqm=SD_UDQM, v3v3=P3V3, gnd=GND, tag='sdram')` with `SD_DQ = Bus('SD_DQ', 16)`, `SD_A = Bus('SD_A', 12)`, `SD_BA = Bus('SD_BA', 2)`.
- `+3V3`, `GND` only consumed here: `.drive = POWER` at top level if the power blocks do not drive them.

## Carried forward
- Intentional NC: U801.36 (A12 on W9825G6KH second source - if substituted, route an FPGA spare I/O as SD_A12 to pin 36) and U801.40.
- W9812G6KH-6 pinout and VDD 3.0-3.6 V ASSUMED from the W9812G6JH datasheet (KH datasheet unobtainable); KiCad W9812G6KH-6 symbol matches JEDEC TSOP-54 x16. Unverified.
- Decoupling all in-block; assembler provides none.
- Local nets: SD_CLK_M.

## Do not redo
- MPNs/footprints/values verbatim from `sourcing/sourced_bom.csv`; pin numbers checked against the KiCad symbol pin table.

## Receipt
sdram: 12 parts (U801, R801-R803, C801-C808); 13 interface args, 1 local net; py_compile OK; footprints from CSV verbatim; signature changed: no.
