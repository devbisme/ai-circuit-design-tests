# dual_adc_usb — Design Review & Fab Output Summary

Date: 2026-10-16 · Tool: KiCad 10.0.4 (`/home/devb/bin/kicad10 kicad-cli`)

## What the board is

A 2-channel, 12-bit, 10 Msps USB data-acquisition board (140 × 90 mm, 4 layers, 170 parts, all on the top side):

```
BNC ─► 1MΩ/20:1 compensated divider ─► ADA4817 buffer ─► THS4521 FDA (×1.91) ─► LTC2290 dual ADC ─┐
 (×2 channels, ±4 V analog rails from LM27762)                                                     ├─► iCE40HX4K ◄─► W9812G6KH SDRAM
                                                                                                   │      ▲
USB-B ─► FT2232HL (Ch A: 245 sync FIFO to FPGA, Ch B: MPSSE SPI to config flash W25Q32) ───────────┘      │
VBUS ─► TPS62160 3.3 V buck ─► TLV755 1.2 V core LDO;  LP5907 3.0 V ADC LDO + LM27762 ±4 V (gated by PWREN#)
```

## What I did

| Step | Method | Output |
|---|---|---|
| ERC | `kicad-cli sch erc --severity-all` | `out/erc.json` |
| DRC + schematic parity | `kicad-cli pcb drc --schematic-parity` | `out/drc.json` |
| Netlist review | Exported the netlist and checked every IC pin-to-net mapping by hand against datasheet knowledge | `out/netlist.xml`, `out/pinmap.txt` |
| PCB review | Parsed `.kicad_pcb`: stackup, plane fills, track widths, via sizes, decoupling-cap-to-pin distances, connector placement | `out/pcbstat.txt` |
| Gerbers + drill | Protel extensions, no X2, soldermask subtracted from silk, Excellon (mm, decimal, PTH and NPTH merged) | `fab/gerbers/`, **`fab/dual_adc_usb_jlcpcb_gerbers.zip`** |
| BOM | JLC format: Comment / Designator / Footprint / LCSC Part # | **`fab/dual_adc_usb_bom_jlcpcb.csv`** |
| CPL | JLC format: Designator / Mid X / Mid Y / Layer / Rotation; mounting holes left out | **`fab/dual_adc_usb_cpl_jlcpcb.csv`** |
| Board image | F.Cu, B.Cu, F.Fab, F/B.SilkS and Edge.Cuts on a #3a3a3a background, 400 dpi | **`dual_adc_usb_pcb.png`** |

The source design files were not modified.

**Provenance and certainty.** Connectivity and geometry findings come directly from the project files and are high-confidence. Statements about part behaviour (pinouts, modes, recommended values) come from **my recollection of the datasheets, not from documents fetched during this review**. They are marked *(datasheet recall)* and should be checked before acting on them.

## Results at a glance

- **ERC:** 0 errors. 155 library-symbol mismatch warnings and 2 benign pin-type warnings (W25Q32 WP#/HOLD# tied to +3V3).
- **DRC:** 0 errors, 0 unconnected items. 170 footprint-library mismatches, 94 silk-over-copper, 71 silk-overlap and 8 silk-clipped-by-edge warnings.
- **Parity:** 170 "Datasheet field differs" (cosmetic) and 4 mounting holes (H1–H4) that are not in the schematic (expected).
- Passing DRC/ERC does **not** mean the board works. The findings below are things DRC cannot see.

## Findings

### High

1. **Input clamp diodes are wired so they do nothing (D101, D201, BAV199DW).**
   - The divider node `/AFE_x/DIV` goes to pin 6 (K3A4), the midpoint of diode pair B.
   - Pair B's ends, pins 4 (A3) and 5 (K4), are no-connect.
   - Pair A's ends go to VEE and +4V, but its midpoint (pin 3, K1A2) floats.
   - Result: no overvoltage clamping of the ADA4817 input.
   - Fix: move DIV to pin 3, or connect pins 4 and 5 to VEE and +4V.
   - Certainty: high for the netlist error as drawn. Separately, verify that the symbol's pin numbering matches the real BAV199DW package.
2. **Decoupling capacitors sit far from the pins they serve.** Shortest pad-to-pad distance to a same-net capacitor:
   - LTC2290 (U301): 5.6–10.8 mm on every VDD/OVDD pin.
   - iCE40 (U601): up to 22 mm (pin 6). VCC core pins are 6–13 mm.
   - SDRAM (U602): pins 1, 3, 9, 14 and 27 are 8–14 mm away. All its caps (C615–C622) are on the opposite side of the package.
   - FT2232H (U502): VCORE pins 12 and 64 are 14–16 mm away.
   - LM27762 (U404): VEE and +4V output caps are 8–10 mm away. *(datasheet recall)* This charge pump has internal LDOs whose output caps should sit right at the pins, so stability as well as noise is at risk.
   - Of everything here, this is the most likely to hurt ADC SNR and SDRAM reliability.
3. **FPGA has no clock until USB enumerates.**
   - The 10 MHz oscillator X301 runs from +3V0, and +3V0 comes from LP5907 U403, which is gated by `AN_EN` (FT2232H PWREN#).
   - Before USB configuration, during suspend, and with the FTDI unpowered, `CLK_10M` is dead.
   - `FT_CLK` (60 MHz) only runs in sync-FIFO mode *(datasheet recall)*.
   - So the FPGA cannot run reset logic, LEDs or any clocked logic until the host configures the device.
   - Fix: power X301 from +3V3, or give it its own rail.

### Medium

4. **FT2232H mode conflict *(datasheet recall, moderate confidence)*.** Channel A is wired for 245 synchronous FIFO, and channel B for MPSSE SPI flash and FPGA configuration. In sync-FIFO mode, channel B is not available. So flash or FPGA reprogramming works only while channel A is out of sync-FIFO mode, which means a mode switch or reset in the host software. This is workable, but it should be a deliberate choice. Also note: `iceprog` defaults to interface A, so it needs `-I B`.
5. **USB high-speed pair is not impedance-controlled.**
   - D+/D− use mixed 0.20, 0.25 and 0.28 mm widths and are not routed as a KiCad diff pair.
   - D+ changes to B.Cu (2 vias) and D− does not.
   - Length mismatch is about 2.5 mm (22.0 vs 19.5 mm).
   - The run is short, so it will probably work, but it is not 90 Ω. Use JLC's impedance calculator for its 4-layer stackup.
6. **Back-powering of the unpowered ADC.** When `AN_EN` is low, the LTC2290 (OVDD = +3V0) is off. Its 26 data outputs connect directly to the iCE40 3.3 V bank, where the I/O pull-ups are on during configuration *(datasheet recall)*. Current flows into OVDD through the ADC's ESD diodes. The current is small (on the order of 1 mA), but power-up behaviour becomes undefined. Fix: keep the FPGA pins tri-stated with pull-ups off, or don't gate the ADC rail.
7. **The LM27762 charge pump (U404) sits between the two AFE channels.** It is at (85, 92), with channel A at y≈70 and channel B at y≈112. Its switching currents run right next to the high-impedance divider nodes. Consider moving it toward the digital side.
8. **USB bus-power budget.** Only the analog section is gated by PWREN#. FT2232H, iCE40, SDRAM, flash and the buck converter are always on, so unconfigured and suspend current very likely exceeds USB limits (100 mA unconfigured, 2.5 mA suspend). This is not measured, only an estimate. It matters only if USB compliance matters.

### Low

9. The anti-alias filter (49.9 Ω + 49.9 Ω + 220 pF) is a single pole at about 7.2 MHz. Nyquist at 10 Msps is 5 MHz, so attenuation at Nyquist is small. This may be intentional.
10. The ADC's OVDD (digital output supply) shares the LP5907 with the analog VDD. Output switching noise lands on the analog rail.
11. The ADA4817 exposed pads (U101/U201, tied to VEE) have no vias. Dissipation is about 150 mW, so this is thermally acceptable, but it gives a weaker supply connection.
12. Header J601 GPIO/TRIG pins go straight to FPGA pins, with no series resistors or ESD protection.
13. The BNC footprints overhang the board edge by about 21 mm, which is why their silk is clipped. Confirm the enclosure or panel fits.
14. Silkscreen: 94 silk-over-pad and 71 overlapping-silk warnings. Many reference designators are unreadable (C311–C317, C601–C608, C510–C514; see the PNG). JLC clips silk on pads. There is no board name or revision text.
15. Housekeeping: symbols and footprints differ from the installed libraries (an update-from-library pass is needed), and the `Datasheet` field is out of sync between schematic and PCB.

### Checked and found OK
- Divider compensation: 953k × 2.2 pF = 2.1 µs needs 42 pF on the bottom leg. C102 (27 pF) plus the trimmer (4.5–20 pF) gives 31.5–47 pF, which covers it.
- Input full scale: the ADC's ±1 V (SENSE = VDD) maps to about ±10.5 V at the BNC.
- FDA feedback polarity, Vocm from the ADC's VCMx, and the FDA input common-mode (about 0.2–0.85 V) are within range for a single 4 V supply.
- Regulator setpoints: the buck gives 0.8 × (1 + 316/100) = 3.33 V, and the LM27762 gives ±1.2 × (1 + 115/49.9) ≈ ±3.97 V. The ±4 V figure assumes the negative feedback works like the positive one *(datasheet recall)*.
- LTC2290 configuration:
  - MODE = 2/3·VDD (two's complement, duty-cycle stabilizer on).
  - SHDN and OE# held low (powered and outputs enabled).
  - REFH/REFL and VCM decoupling values look right.
- FT2232H support circuitry: the 93LC56 EEPROM wiring (DO via 2.2k, ORG high) and the 12k REF resistor match FTDI's reference design.
- iCE40 SPI master configuration: SS pulled up; SDO → flash DI and SDI ← flash DO; CRESET and CDONE pulled up. The clocks land on GBIN pins (CLK_10M on 21, FT_CLK on 129, TRIG on 49).
- SDRAM pinout matches the standard JEDEC TSOP-II-54 x16 pinout.
- Planes: In1 is solid GND and In2 is solid +3V3, each a single island covering about 95% of the board.

## Fabrication notes (JLCPCB)

- Geometry fits JLC's standard 4-layer process: minimum track and clearance 0.15 mm, vias 0.6/0.3 mm, 1.6 mm board thickness. All SMD parts are on the top side.
- **The BOM has no LCSC part numbers.** The `LCSC Part #` column is empty, so every line must be matched in JLC's tool. Many of the active parts (LTC2290, ADA4817, THS4521, LM27762, iCE40HX4K-TQ144, W9812G6KH, FT2232HL, SiT8008) are likely extended, out-of-stock or consignment parts at JLC. I have not checked availability.
- The CPL includes the through-hole parts (J101, J201, J501, J601). Either order through-hole assembly or exclude those parts.
- KiCad and JLC define zero rotation differently for many packages (SOT-23, QFP, QFN and others). Check every part in JLC's placement preview before ordering.

## Recommended next steps (in priority order)
1. Fix the D101/D201 clamp wiring.
2. Re-place decoupling capacitors at the pins of U301, U601, U602, U502 and U404.
3. Power X301 from an always-on rail.
4. Decide how the FT2232H channel A/B modes will be used.
5. Route USB as a 90 Ω diff pair.
6. Clean up the silkscreen and add LCSC part numbers, then regenerate the fab files.
