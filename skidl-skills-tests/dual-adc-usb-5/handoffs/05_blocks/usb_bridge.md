---
phase: 05_blocks/usb_bridge
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-20T18:40:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Block handoff — usb_bridge

## Decisions

1. **Signature is UNCHANGED from the work order** (no keyword renames):
   `usb_bridge(usb_dp, usb_dm, fifo_d, fifo_rxf_n, fifo_txe_n, fifo_rd_n, fifo_wr_n,
   fifo_oe_n, fifo_siwu, fifo_clk, pwren_n, v5_in, gnd)`. `fifo_d` must be a `Bus(...,8)`.
2. **Direction map** — DRIVEN by this block: `FIFO_RXF_N`, `FIFO_TXE_N`, `FIFO_CLK`,
   `PWREN_N`. SENSED only: `FIFO_RD_N`, `FIFO_WR_N`, `FIFO_OE_N`, `FIFO_SIWU`.
   Bidirectional: `FIFO_D[7:0]`, `USB_DP`, `USB_DM`. Consumed: `+5V_IN`, `GND`.
3. **No 3.3V rail enters this block, by design.** FTDI FT_000288 v1.81 §6.1 + Table 3.1:
   with VREGIN (40) at +5V, **VCCD (39) becomes a 3.3V output** that supplies VCCIO
   (12/24/46), VPLL (8) and VPHY (3). Local net `FT232H_3V3` carries it and also feeds U8,
   the RESET# pull-up and the two FTDI-mandated pull-ups. Do **not** connect `+3V3_D` here.
4. **VCCA (37) and VCORE (38) are 1.8V LDO outputs** — datasheet: "Should not be used.
   Terminate with 0.1uF capacitor to GND". C17/C18 do only that.
5. **PWREN# is on ACBUS8 (pin 32), not ACBUS7 — deviation from `net_plan.md` line 80.**
   In SYNC 245 FIFO mode ACBUS7 is PWRSAV# only (§3.2 mode table) and Table 3.5 offers
   PWREN# on ACBUS0–6/8/9; ACBUS0–6 are all consumed by the FIFO interface. `R_pwren` 10k
   pull-up added because Table 3.5 note * makes it mandatory. ACBUS7 (31) and ACBUS9 (33)
   are `NC` (ACBUS7 has an internal ~75k pull-down; the "Suspend on ACBUS7 low" EEPROM
   option is disabled by default and must stay disabled).
6. **X2 pins 2/4 ARE tied to GND** — resolving handoff 04 item 9 the other way, with reason:
   symbol `Device:Crystal_GND24` (1/3 = electrodes, 2/4 = GND) is the standard pad map of
   the `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` footprint the part was sourced with, and
   "1,3 Crystal / 2,4 GND" in TKD's table is the ordinary way of writing that pad map
   (electrodes on the diagonal pads, metal lid bonded to the other two). Pins 1→XCSI(1)
   and 3→XCSO(2), each with its own 18pF load cap to GND. **Falsifying test**: ohmmeter
   across pads 1–3 of a physical sample — open = this wiring is right; shorted = pads 1/3
   are one electrode and the datasheet-phase reading was right, in which case rewire as
   1+3 → XCSI and 2+4 → XCSO (`Device:Crystal` 2-pin symbol, custom pad map).
7. **C13/C14 = 18pF** (2·(12 − 3) for the 12pF-load crystal), **not** FTDI's generic 27pF.
   C0G/NP0 0603.
8. **U8 ORG (6) tied to VCC** for ×16 organisation, per handoff 04 item 6. U8 pin 7 = `NC`.
   EEPROM wiring follows FTDI Table 3.3 exactly: EEDATA(43) → DI(3) direct; **R13 (2.2k) is
   a series resistor between EEDATA and DO(4), not a pull-up**; DO also needs a 10k pull-up
   to 3.3V (`R_eedo`, added — see below).

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/usb_bridge.py` | The block (21 parts, 32 nets) | Assembling |
| `datasheets/FT232HL-REEL_SUMMARY.md` | Pin table (numbers confirmed correct this pass) | Reviewing U7 wiring |

## Next phase must

1. **[RESOLVED by the driver — sourcing revision 2, no action left]** U8 was the wrong
   EEPROM density; it is now **93LC56BT-I/SN** (2 Kbit, 128x16, LCSC C6164, stock 2384),
   and `usb_bridge.py`'s `value=` string has been updated. Symbol, footprint and wiring
   are unchanged. Original finding, kept for the record:
   FT_000288 §4: the EEPROM "should be a 16 bit wide configuration such as a **93LC56B** or
   equivalent capable of a 1Mbit/s clock rate at VCCIO = +2.97V to 3.63V… **Please note that
   the 93LC46B is not compatible with the FT232H device**." The sourced U8 is a 1 Kbit
   93C46 — that incompatible density class (handoff 04 item 6 also mis-states it as 128×16 =
   2 Kbit; a 93C46 is 64×16 = 1 Kbit). Pinout is identical, so the fix is a pure sourcing
   swap to a 93LC56B/93LC66B-class SOIC-8 part; `usb_bridge.py` needs only its `value=`
   string changed. Raise this to the driver/sourcing — the block code is not the blocker.
2. **Call the block with keywords, exactly this:**
   ```python
   usb_bridge(usb_dp=USB_DP, usb_dm=USB_DM, fifo_d=FIFO_D, fifo_rxf_n=FIFO_RXF_N,
              fifo_txe_n=FIFO_TXE_N, fifo_rd_n=FIFO_RD_N, fifo_wr_n=FIFO_WR_N,
              fifo_oe_n=FIFO_OE_N, fifo_siwu=FIFO_SIWU, fifo_clk=FIFO_CLK,
              pwren_n=PWREN_N, v5_in=V5_IN, gnd=GND)
   ```
   `fifo_d` must be `Bus('FIFO_D', 8)`; the loop maps `fifo_d[0..7]` → ADBUS0..7 (pins 13–20).
3. **Set `.drive = POWER` at the top level on `+5V_IN` and `GND`** — this block only
   consumes them. `FT232H_3V3` is internal and driven by U7's VCCD power-out pin, so it
   needs nothing.
4. **Tell `digital_power` nothing changes**: `PWREN_N` still arrives as one net to Q1's gate;
   only which FT232H pin sources it moved (ACBUS7 → ACBUS8). The EEPROM image must assign
   PWREN# to ACBUS8 and enable the interface pull-down option (FTDI Table 3.5).

## Carried forward

- **7 parts added that no ref list contained**, all FTDI-mandated or required by the ERC
  decoupling rule. Non-numeric refs so they cannot collide with another block; **sourcing
  must add them to the BOM** (all jellybean, no availability risk):

  | ref | value | why | source |
  |---|---|---|---|
  | `R_ref` | 12k 1% 0603 | REF(5)→GND current reference | FT_000288 Table 3.2 (mandatory) |
  | `R_eedo` | 10k 0603 | EEPROM DO→3V3 pull-up | Table 3.3 (mandatory) |
  | `R_pwren` | 10k 0603 | PWREN#(ACBUS8) pull-up | Table 3.5 note * (mandatory) |
  | `C_vregin` | 100nF 0402 | VREGIN(40) decoupling | §6.1 figure |
  | `C_io24` | 100nF 0402 | VCCIO(24) decoupling | ERC rule / §6.1 |
  | `C_io46` | 100nF 0402 | VCCIO(46) decoupling | ERC rule / §6.1 |
  | `C_ee` | 100nF 0402 | U8 VCC decoupling | ERC rule |
- **No LC filter on VPHY/VPLL.** The datasheet *recommends* filtering both from VCCD with an
  LC; no inductor/ferrite ref was budgeted for this block, so both are fed directly from
  `FT232H_3V3` with a 100nF each (C20/C21). Affects USB PHY jitter only — not the ADC sample
  clock. Add a 0603 ferrite in series with each at layout if USB HS eye margin is tight.
- **No bulk cap on the VCCD 3.3V rail.** A 4.7µF near pin 39 is normal practice for the
  rail that feeds VCCIO/VPLL/VPHY; not added because no ref exists for it. Recommend adding
  one at layout/BOM reconciliation.
- **RESET# uses R14 10k + C16 100nF.** The datasheet only says RESET# "should be tied to
  VCCIO (+3.3V) if not being used"; the RC is the sourced BOM's intent and is harmless
  (~1 ms release delay). Not a datasheet-mandated value.
- **X2 pin-2/4 grounding is an engineering judgement, not a verified fact** — see Decision 6
  for the one-minute continuity test that settles it. Getting it wrong = dead USB bridge.
- **FT232H pin numbers were verified this pass** (KiCad `Interface_USB:FT232H` symbol,
  live EasyEDA pinout for C51997, and FT_000288 Tables 3.1–3.3 all agree), closing the
  "spot-check pin numbers" caveat in `FT232HL-REEL_SUMMARY.md`.

## Do not redo

- The FT232H power topology (VREGIN 5V → VCCD 3.3V output) and the 1.8V-output treatment of
  VCCA/VCORE — closed with primary-source citations.
- The PWREN# → ACBUS8 move and its 10k pull-up — closed from the mode table + Table 3.5.
- The REF 12k 1%, EEPROM 2.2k series + 10k pull-up topology — closed from Tables 3.2/3.3.
- C13/C14 = 18pF, U8 ORG → VCC — already settled upstream, re-confirmed here.

## Receipt

- block: `usb_bridge` → `circuits/dual_adc_usb/usb_bridge.py`
- parts 21, nets 32 (13 interface + 8 internal, incl. `FT232H_3V3`)
- `python -m py_compile` OK; block instantiates cleanly with the keyword call above
- footprints: 4 distinct strings, all validated present in the stock KiCad libraries
- signature changed: **no**
- flags: U8 EEPROM density incompatible per FTDI (Next phase must #1); 7 parts added to BOM
- status: complete
