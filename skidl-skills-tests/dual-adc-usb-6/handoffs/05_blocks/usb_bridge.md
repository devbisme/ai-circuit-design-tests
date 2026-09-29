---
phase: 05_blocks/usb_bridge
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-21T00:00:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Phase 5 handoff — block `usb_bridge`

## Decisions

1. **Signature is exactly as issued — unchanged.**
   `usb_bridge(usb_dp, usb_dm, fifo_d, ifclk, slwr_n, slrd_n, sloe_n, pktend_n, fifoadr, flagb, flagc, v3v3d, gnd)`
2. **Direction of every interface net.** **Driven by this block:** `ifclk` (FX2LP sources
   the 48 MHz interface clock), `flagb`, `flagc`. **Bidirectional:** `usb_dp`, `usb_dm`,
   `fifo_d`. **Sensed only:** `slwr_n`, `slrd_n`, `sloe_n`, `pktend_n`, `fifoadr` — all
   driven by `fpga_core`. **Consumed only:** `v3v3d`, `gnd`.
3. **Bus bit order: bit 0 = LSB** — `fifo_d[0]`→PB0/FD0, `fifoadr[0]`→PA4/FIOADDR0,
   matching `fpga_core`'s `_P_FIFO_D` / `_P_FIFOADR`.
4. **SCL/SDA are internal to this block**, created locally as `Net('SCL')`/`Net('SDA')`.
   `net_plan.md` scopes them "U50 <-> U51"; they are deliberately not in the signature.
5. **Y1 symbol corrected — `Device:Crystal_GND24`, not `Device:Crystal`.**
   `sourced_bom.md` pairs a 2-pin symbol with the 4-pad footprint
   `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm`, which would leave the two case pads with
   no net. `Crystal_GND24` has pins 1/3 = resonator, 2/4 = grounded case; pins 2 and 4
   are tied to GND here. **The BOM row for Y1 needs its symbol field fixed** — MPN
   (DSX321G 24 MHz), LCSC (C93235) and footprint are unchanged.
6. **The boot-EEPROM address strap — the fact this board's enumeration rests on.**
   U51 is strapped **A0=1 (via R53 to +3V3D), A1=0, A2=0 (via R54/R55 to GND)**, giving
   I2C 7-bit **0x51** / 0xA2 write. Strapping all three low (the 24LC64 default, 0x50)
   means the FX2LP never boots from it. Sources, both primary: Infineon CY7C68013A
   38-08032 Rev. AD p.16 Table 8 (names 24LC64 explicitly, 8K row = 0,0,1) and Microchip
   DS21189T p.7 §5.0/Fig. 5-1 (control byte `1010 A2 A1 A0 R/W`). Strap nets are named
   `EE_A0`/`EE_A1`/`EE_A2` so the strap is legible in the netlist, not an anonymous `N$`.
7. **R50–R55 assigned, as asked. R52 is NOT what phase 4 hypothesised.**
   | ref | value | function |
   |---|---|---|
   | R50 | 2.2 kΩ | SCL pull-up to +3V3D — confirms `sourced_bom.md`/`net_plan.md` |
   | R51 | 2.2 kΩ | SDA pull-up to +3V3D — confirms `sourced_bom.md`/`net_plan.md` |
   | **R52** | **100 kΩ** | **FX2LP ~RESET pull-up (with C89) — not a 10 kΩ EEPROM strap** |
   | R53 | 10 kΩ | U51 A0 pull-**up** to +3V3D (the 0x51 bit) |
   | R54 | 10 kΩ | U51 A1 pull-down to GND |
   | R55 | 10 kΩ | U51 A2 pull-down to GND |

   Phase 4's hypothesis was "3 address straps + 1 WP pull". Three of the four hold; the
   fourth does not. **WP is tied hard to GND** (the 24LC64 permits a direct VSS tie, and
   no write-protect jumper is wanted on a boot EEPROM the FX2 must write), which frees
   R52 for something the design genuinely cannot do without — see #8. This keeps every
   electrical requirement met **with no new ref designators**.
8. **~RESET needs a 100 kΩ/100 nF RC, not the BOM's 10 kΩ placeholder.** CY7C68013A
   datasheet Table 5 "Reset Timing Values" (38-08032 Rev. AD, p.8): with a crystal,
   TRESET ≈ **5 ms** after VCC reaches 3.0 V, so crystal and PLL can stabilise. The FX2LP
   has no adequate internal POR. Time to VIH = 2.0 V is `0.932·R·C`; 10 kΩ/100 nF gives
   **0.93 ms — 5× short**, which is exactly what the placeholder would have produced.
   100 kΩ/100 nF gives **9.3 ms**, 1.9× margin. R52 = 100 kΩ uses an MPN already in the
   BOM (`0402WGF1003TCE`, LCSC C25741, also R3/R18). **BOM row R52 needs its value
   changed from 10 kΩ to 100 kΩ.**
9. **Pin 14 RESERVED is tied to GND, not left NC.** The datasheet's pin-description
   table says verbatim "Reserved. Connect to ground."
10. **Pin 44 WAKEUP (active low) is tied to +3V3D** = deasserted. Tying it low would
    inhibit USB suspend and blow the suspend-current budget; floating is indeterminate.
11. **C92/C93 = 12 pF each is correct and is Cypress's own number**, not a misread of
    the crystal's 12 pF CL: 38-08032 Rev. AD p.4 asks for a 24 MHz parallel-resonant
    fundamental-mode crystal with "12-pF (5% tolerance) load capacitors".
12. **EP (pin 57) is tied to GND** and matches pad 57 of the QFN-56-1EP footprint
    (verified: the footprint has pads 1..57).

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/usb_bridge.py` | The block — U50, U51, Y1, R50–R55, C80–C93 | Assembling the circuit |

## Next phase must

1. Emit exactly this call in `__main__.py`:
   ```python
   usb_bridge(usb_dp=USB_DP, usb_dm=USB_DM, fifo_d=FIFO_D, ifclk=IFCLK,
              slwr_n=SLWR_N, slrd_n=SLRD_N, sloe_n=SLOE_N, pktend_n=PKTEND_N,
              fifoadr=FIFOADR, flagb=FLAGB, flagc=FLAGC,
              v3v3d=V3V3D, gnd=GND, tag='usb_bridge')
   ```
2. Create `FIFO_D` as `Bus('FIFO_D', 8)` and `FIFOADR` as `Bus('FIFOADR', 2)`. Widths are
   load-bearing — the block indexes 0..7 and 0..1.
3. **Set `V3V3D.drive = POWER` and `GND.drive = POWER` at the top level.** This block
   consumes both rails and drives neither.
4. Do **not** create top-level nets named `SCL`, `SDA`, `EE_A0/1/2` or `FX2_RESET_N` —
   they are internal to this block and will collide by name if duplicated.
5. `MCU_Cypress:CY7C68013A-56LTX`, `Memory_EEPROM:24LC64` and `Device:Crystal_GND24` all
   come from the **stock** KiCad libraries; this block needs no entry from
   `symbols/dual_adc_usb.kicad_sym`.

## Carried forward

- **Three BOM corrections this block requires** (all flagged above, none applied by me —
  `sourcing/sourced_bom.md` is not mine to edit):
  1. Y1 symbol `Device:Crystal` → **`Device:Crystal_GND24`** (Decision #5).
  2. R52 value 10 kΩ → **100 kΩ**; MPN `0402WGF1002TCE` → **`0402WGF1003TCE`**, LCSC
     C25744 → **C25741** (both already in the BOM as R3/R18) — Decision #8.
  3. C92/C93 are used by this block although the work order's ref list stops at C91.
     `sourced_bom.md` labels them "(Y1 load caps)" and Y1 is this block's part, so no
     other block can own them. **Flagged rather than silently absorbed**, per the work
     order's instruction about ref designators.
- **No ferrite isolation on U50's AVCC/AGND.** FB1–FB4 belong to the analog/power
  blocks; this block's ref list has none. AVCC goes straight to +3V3D with its own
  100 nF (plus C91 as the AVCC-side bulk). The FX2LP's analog section is the USB PHY, not
  a precision converter, so this is acceptable — but if USB HS eye-diagram margin turns
  out tight on the built board, a ferrite here is the first thing to add.
- **No discharge diode across R52.** On a fast power-cycle C89 may not fully discharge,
  shortening the next power-on reset. For a bus-powered device that always cold-starts
  from a USB plug event this is not worth a part, but it is a known limitation of the
  plain-RC approach.
- **PD0–PD7 (FD8–FD15) left NC** — the FIFO is 8 bits wide per architecture decision #4.
  Widening to 16 bits later is a block edit, not a rewiring of the interface.
- **CTL0/FLAGA, PA0, PA1, PA3, PA7/~SLCS and CLKOUT are explicit `NC`.** Deliberate, not
  forgotten. `~SLCS` unused means the slave FIFO is permanently chip-selected, which is
  the normal single-master configuration.
- **FX2LP is commercial temp grade (0–70 °C)**, carried over from
  `CY7C68013A-56LTXC_SUMMARY.md` — unchanged by this block, repeated so it is not lost.

## Do not redo

- The 0x51 / (A2,A1,A0)=(0,0,1) strap — verified from two primary datasheets in phase 4
  and implemented here. Do not "simplify" it to an all-GND strap.
- MPNs and footprints for U50, U51, Y1, R50/R51 and the C80–C93 passive buckets — taken
  verbatim from `sourcing/sourced_bom.md`.
- The 8-bit slave FIFO topology and the FX2LP-sources-IFCLK direction — architecture
  decision #4 and `net_plan.md`.

## Receipt

- block_id: `usb_bridge`; file `circuits/dual_adc_usb/usb_bridge.py`
- parts: 23 (U50, U51, Y1, R50–R55, C80–C93); nets: 29 in an isolated smoke build
- compile OK (`py_compile`); block instantiates and connects cleanly under SKiDL 3.0.0
- footprints: **valid**, 12 checked, `validate-footprints.py` exit 0
- signature changed: **no**; 3 BOM corrections raised (Y1 symbol, R52 value, C92/C93 refs)
