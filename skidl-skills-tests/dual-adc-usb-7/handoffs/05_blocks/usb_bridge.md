---
phase: 05_blocks/usb_bridge
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-23T13:30:00Z
status: complete
revision: 3
next_phase: 05_coding
---

# Phase 5 handoff — block `usb_bridge`

## Decisions

1. **SIGNATURE CHANGED — `siwu_n` REMOVED.** Final, as written:
   `usb_bridge(vbus, ft_3v3, fifo_d, rxf_n, txe_n, rd_n, wr_n, oe_n, fifo_clk60, pwren_n, gnd)`
   A `siwu_n=` keyword now raises `TypeError`.
2. **`FIFO_SIWU_N` is block-internal**: U6 ACBUS4 → `R67` (10 k) → `FT_3V3`. SI/WU# is
   active-**low**, so inactive is **high** (FT232H pin table; `net_plan.md` line 143 agrees,
   3.29 V vs VIH 2.0 V). Never driven low, so no off-state case.
3. **`R66` added** — 10 k, `EE_DO` → `FT_3V3`: the FTDI Table 3.3 pull-up that sits
   *alongside* R64's 2.2 k series resistor. Closes the rev.1 gap I reported.
4. **`C610`/`C611`/`C612` added** — 100 nF on U6 VPHY (pin 3), U6 VPLL (pin 8), U7 VCC.
   All 10 supply pins in this block now have local decoupling.
5. **Unchanged from rev.1, deliberately:** U6 VCCA(37)/VCORE(38) stay on isolated
   `FT_VCCA_1V8`/`FT_VCORE_1V8` with C606/C608 to GND — they are +1.8 V LDO **outputs** and
   must not touch `FT_3V3` or the board's `P1V8`. RESET#(34) direct to `ft_3v3`. `FT_3V3`
   sourced by U6 pin 39 only. Separate 5.1 k CC1/CC2 pulldowns; both D+/D− pairs strapped.
6. **BOM symbols verified:** U7 `93LCxxBxxOT`, Y1 `Crystal_GND24` already matched rev.3. All
   24 refs' symbol/footprint/value agree with `sourced_bom.csv`, checked mechanically.
7. Drive: `vbus`, `ft_3v3` driven here; `rxf_n`, `txe_n`, `fifo_clk60`, `pwren_n` driven;
   `rd_n`, `wr_n`, `oe_n` sensed; `fifo_d` bidirectional; `gnd` consumed only.
8. **NEW rev.3 — two pin-function overrides, the fix for the 6 ERC warnings.** Exactly
   these two lines were added, immediately before the EEPROM connections:
   ```python
   U6['EECS'].func  = Pin.types.OUTPUT   # symbol pin 45
   U6['EECLK'].func = Pin.types.OUTPUT   # symbol pin 44
   ```
   Pins are addressed **by name**, so the symbol's own numbering governs. The exported
   netlist confirms it: `EE_SK` = U6.44/U7.4, `EE_CS` = U6.45/U7.5. (Note the work
   order and `05_coding.md` label 44 = EECLK's net as "EECS" and vice-versa; the names
   are what matter and both pins are fixed either way.)
   **Why:** stock `Interface_USB:FT232H` declares EECS/EECLK `INPUT`, and stock
   `Memory_EEPROM:93LCxxBxxOT` declares CS/CLK `INPUT`. In hardware the FT232H is the
   **Microwire bus master**: it drives the EEPROM's clock and chip select, and the
   93LC56B's CLK/CS are device inputs. The symbols are wrong, the netlist was always
   right. Contrast EEDATA, already `BIDIR` in the symbol, which never warned.
   **Mechanism:** with two `INPUT` pins on a net, SKiDL `erc.py:net_erc()` computes
   `net_drive = max(pin.drive) = NONE` → "No drivers", and `INPUT`'s `min_rcv = PASSIVE >
   NONE` fires "Insufficient drive current" on **each** pin. 3 warnings × 2 nets = the 6.
   Setting `func` to `OUTPUT` gives `drive = PUSHPULL` (`pin.py` `pin_info`), which clears
   all 6.
   **Why this and not `do_erc = False` or a net `.drive` override:** neither symbol library
   is edited (both stay stock), and **no check is disabled**. `EE_SK`/`EE_CS` remain fully
   ERC'd, and a second driver on either net would now raise an `OUTPUT`-vs-`OUTPUT`
   **ERROR** that the `INPUT`/`INPUT` declaration silently hid. A blanket `do_erc = False`
   would have hidden that too; a net-level `.drive = POWER` would have mislabelled a
   logic net as a power rail and left the pin types wrong in the export.
   **Side effect, intentional:** the exported netlist now records pins 44/45 as `output`
   rather than `input` — which is what the hardware does.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/usb_bridge.py` | The block, 24 parts | Assembling the circuit |

## Next phase must

0. **Nothing to change in the assembler.** The rev.3 fix is two lines inside this block;
   the signature, the call and every net name are untouched.
1. Emit exactly this call — **no `siwu_n` argument**:
   ```python
   usb_bridge(vbus=VBUS, ft_3v3=FT_3V3, fifo_d=FIFO_D, rxf_n=FIFO_RXF_N,
              txe_n=FIFO_TXE_N, rd_n=FIFO_RD_N, wr_n=FIFO_WR_N, oe_n=FIFO_OE_N,
              fifo_clk60=FIFO_CLK60, pwren_n=PWREN_N, gnd=GND, tag='usb_bridge')
   ```
   `FIFO_D = Bus('FIFO_D', 8)`. Set `.drive = POWER` on `VBUS`, `FT_3V3`, `GND` at top level:
   U6 pin 39 is declared `power_in` in the KiCad symbol even though it is the LDO output, so
   `FT_3V3` needs the top-level drive to satisfy ERC.
2. Do **not** create a top-level `FIFO_SIWU_N`, and do **not** add a second `FT_3V3` source.
3. `validate-bom.py` now runs post-assembly and **exits 0**; this block contributes no mismatch.

## Carried forward

- **For the ERC reviewer, verifying Decision 8:** the claim is checkable in three places —
  `circuits/dual_adc_usb/usb_bridge.py` (the two `.func` assignments and their comment),
  SKiDL `erc.py:net_erc()` lines 126–136 (the `net_drive`/`min_rcv` logic), and
  `pin.py:pin_info` (`INPUT.drive = NONE`, `INPUT.min_rcv = PASSIVE`,
  `OUTPUT.drive = PUSHPULL`). No `do_erc` flag is set anywhere in this block; grep it.
  Full-circuit ERC after the change: **0 errors, 0 warnings.**
- **`net_plan.md` line 17 has the wrong FT232H supply pins; the rev.3 BOM note for C610/C611
  copies it** ("VPHY pin16, VPLL pin20"). The symbol gives VCCIO **12/24/46**, VPHY **3**,
  VPLL **8**; 13/16/20/33 are ADBUS0/3/7 and ACBUS9. Code follows the symbol — docs defect only.
- Intentional `NC` (the 3 pins on `__NOCONNECT`): J4 A8/B8 (SBU1/2), U6 ACBUS8.
- `PWREN_N` drives Q1's gate in `power_tree`; R65 pulls it up here — no second pull-up there.
- FT232H Fig 6.1 *recommends* an LC filter on VPHY/VPLL; no inductors sourced. C610/C611
  alone is the accepted compromise.
- J4 vs GCT USB4105 mechanical footprint check still open from phase 4.

## Do not redo

- U6 pin mapping (all 48 accounted for), the ACBUS 245-sync-FIFO assignment, J4 orientation
  strapping, the CC pulldown pair, VCCA/VCORE isolation — settled rev.1, re-confirmed here.

## Receipt

- rev.3: 24 parts (U6, U7, U8, J4, Y1, R61–R67, C601–C612), 32 signal nets +
  `__NOCONNECT`. **No part, net or connection changed vs rev.2** — the only edit is the
  two `Pin.types.OUTPUT` overrides on U6 pins 44/45 (Decision 8).
- `py_compile` OK; full-circuit ERC **0 errors, 0 warnings** (was 0/6, all 6 from this
  block); `validate-bom.py` **exit 0**.
- **Signature changed: no** at rev.3 (`siwu_n` was removed back at rev.2 and stays removed).
- Open: `net_plan.md` FT232H pin numbering (docs only); the stock `Interface_USB:FT232H`
  symbol's EECS/EECLK pin types are still wrong upstream — worth a KiCad bug report, but
  **not** to be fixed by editing the local library.
