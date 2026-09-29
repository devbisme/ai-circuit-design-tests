---
phase: 05_blocks/afe_ch_b
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-26T17:00:00Z
status: complete
revision: 2
next_phase: 05_coding
---

# Block handoff — afe_ch_b

## Decisions
- **Rev 2 (ERC F1 fix, footprint file only):** BNC ground-lead pad moved +2.5 → **−2.5** (drawing KH-801-0038 rev B PCB view = top view, front at −y: ground lead 2.5 mm LEFT of centre; front/rear views agree). Pegs (±5.05, −2.525) and centre pad re-checked — correct (pegs symmetric, peg row forward of lead row). Fab/CrtYd now show real body: rear y=+4.475 (7.0 behind pegs), flange/panel front y=−10.025 (7.5 ahead), thread tip y=−31.025 (28.5 ahead, Ø12.8 nose); front-edge marker on F.Fab text + Dwgs.User dashed line at y=−10.025. No .py change; footprint name unchanged.
- Final signature (unchanged): `afe_ch_b(ain_p, ain_n, vcm, v3v3a, vp_afe, vn_afe, gnd)`.
- **Drives** ain_p/ain_n (U202 via R210/R211). **Senses** vcm (U202 VOCM, high-Z). **Consumes** v3v3a, vp_afe, vn_afe, gnd.
- Local nets exactly as in net_plan.md: B_BNC, B_DIV, B_BUF_IN, B_BUF_OUT, B_XP, B_XN, B_FIP, B_FIN, B_FOP, B_FON.
- **J3 symbol = `Connector:Conn_Coaxial`** (1 In = centre, 2 Ext = GND). BOM `Connector_Coaxial:BNC_Generic` does not exist in the KiCad 9 libs.
- **J3 footprint = `ProjectLocal:BNC_Kinghelm_KH-BNC50-3511_Horizontal`** (generated, `footprints/ProjectLocal.pretty/`): pad 1 centre (0, +2.525) D0.9; pad 2 ground lead (**−2.5**, +2.525) D0.9 and both shell pegs (±5.05, −2.525) D2.0. Shared with J2 (afe_ch_a).
- C204 JZ300 = `Device:C_Variable`, pin 1 (hot) → B_DIV, pin 2 (rotor) → GND. Value field `24pF` per BOM.
- U202 FB+(4)/FB−(1) pin types set to INPUT in-block so the required FB–OUT tie is not an output-output ERC conflict. PD(12) → v3v3a (active-high enable). EP(17) → GND.
- U201 and U202 wired by pin number (symbol names `~`/`+`/`-`, `~{PD}`).

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/afe_ch_b.py` | block @SubCircuit | Assembly |
| `footprints/ProjectLocal.pretty/BNC_Kinghelm_KH-BNC50-3511_Horizontal.kicad_mod` | J2/J3 custom footprint | Layout / netlist footprint path |

## Next phase must
1. skidl-assembler: `afe_ch_b(ain_p=AIN_B_P, ain_n=AIN_B_N, vcm=VCM, v3v3a=V3V3A, vp_afe=VP_AFE, vn_afe=VN_AFE, gnd=GND, tag='afe_ch_b')`.
2. `GND.drive = POWER` at top. V3V3A/VP_AFE/VN_AFE are driven by power_analog. VCM is driven by U8.CM (adc); if its pin type is not an output, set `VCM.drive = POWER` to avoid an undriven-input warning on U202 VOCM.
3. Run with `symbols/` on KICAD9_SYMBOL_DIR (D201 is `dual_adc_usb:BAV199`) and `footprints/` on the footprint path (J3 is ProjectLocal).
4. **part-sourcer / driver — BOM cell fixes:** J3 symbol → `Connector:Conn_Coaxial`; J3 footprint → `ProjectLocal:BNC_Kinghelm_KH-BNC50-3511_Horizontal`; D201 symbol → `dual_adc_usb:BAV199` (currently `SYMBOL_NEEDED`).

## Carried forward
- No NC pins. All 29 parts fully connected.
- Decoupling is all local (C206/C207, C211/C212, C214); none assumed from the assembler.
- BNC footprint verified against drawing PCB/front/rear/side views (rev 2). Body overhangs ~21 mm past the flange line (y=−10.025); place J3 with that line at the board edge. Dry-fit a real part against a 1:1 print before fab.
- Silkscreen note needed at C204: rotor end on pad 2 (footprint has no polarity mark).
- JZ300 TC −1500 ppm/°C (architect FYI from phase 4, not re-decided).

## Do not redo
- Connectivity checked by instantiating the block alone and with afe_ch_a: every net matches net_plan.md afe_ch_a with A_→B_ (net plan defines ch B by substitution); local ERC 0 errors / 0 warnings.

## Receipt
- Block afe_ch_b: 29 parts (J3, U201, U202, D201, R201–R211, C201–C214), 17 nets (10 local), py_compile OK, footprints 10/10 strings resolve (1 generated), signature changed: no.
- Rev 2: footprint-only fix (pad 2 lead −2.5; courtyard extended to thread tip); parses in pcbnew; .py untouched; signature changed: no.
