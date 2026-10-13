# Executive summary: dual_adc_usb analysis (kicad-harness)

## The design

A two-channel, 12-bit, 10 MSPS USB digitizer. Each BNC input (1 MΩ, ±10 V) goes through a
compensated ÷20 divider, an ADA4817 buffer and a THS4521 fully differential amplifier
into an LTC2290 dual ADC. An iCE40HX4K FPGA writes the samples to a 16 MB SDR SDRAM and
streams them out through an FT2232H in sync-FIFO mode on USB 2.0 HS. The board is bus powered:
a TPS62160 buck makes 3.3 V, a TLV755 LDO makes 1.2 V, an LP5907 makes 3.0 V and an LM27762
makes ±4 V.

The PCB is 140 × 90 mm with 4 layers: signals on F.Cu and B.Cu, a GND plane on In1 and a
+3V3 plane on In2. It has 174 footprints, all on the top side, and 493 vias, all 0.6/0.3 mm.

## What was done

| Step | Tool | Result |
|---|---|---|
| Board summary, part list | `kh info`, `kh ls`, pcbnew (KiCad 10.0.4 python) | 174 parts, 214 nets, 2994 track segments |
| DRC (as saved) | `kh drc --severity all` | **0 errors**, 0 unconnected, schematic parity clean, 343 warnings |
| DRC (zones refilled) | `kh drc --refill` → 856 violations, **false** (see tool notes); rerun by hand with `kicad-cli pcb drc --refill-zones` | **0 errors**, same 343 warnings |
| ERC | `kh erc` | 0 errors; 201 library-config warnings (environment) and 2 benign pin-type warnings |
| Schematic review | `kh sview --all` (each sheet read), `kh netlist` and a pin-by-pin netlist dump of every IC | See findings |
| Layout review | `kh view`, plus pcbnew scripts for decoupling distance, via-in-pad, layer use, pair lengths and the stackup | See findings |
| Gerbers and drill | `kicad-cli pcb export gerbers/drill` (KiCad 10.0.4) | `jlcpcb/gerbers/`, `jlcpcb/dual_adc_usb_gerbers.zip` |
| BOM and CPL | `kh bom` and `kicad-cli pcb export pos`, reformatted for JLCPCB | `jlcpcb/dual_adc_usb_bom.csv`, `jlcpcb/dual_adc_usb_cpl.csv` |
| PCB picture | `kh view`, layers F/B.Cu, F/B.Fab, F/B.Courtyard, F/B.Silk and Edge.Cuts on `#333333` | `dual_adc_usb_pcb.png` |

The board file was not modified. Its md5 is unchanged after all the exports.

## Findings

Severity is my judgement. **[uncertain]** marks items I could not fully verify.

### Must handle before ordering assembly

1. **The BOM has no LCSC part numbers or MPN fields.** Many values are generic ("100nF",
   "GREEN", "BNC"). The `LCSC Part #` column in the JLCPCB BOM is empty, so JLCPCB will not
   auto-match parts. Each part needs selecting: voltage rating and dielectric for the caps,
   and 0.1 % parts for R101–R107 and R201–R207.
2. **The CPL rotations are unverified.** These are KiCad's native rotations. JLCPCB's
   footprint zero orientation often differs, typically for SOT-23/SOT-23-5/SOT-363, SOIC,
   QFP and the LEDs. Check every IC, diode and LED in JLCPCB's placement preview.
3. **There are four through-hole parts:** J101 and J201 (BNC), J501 (USB-B) and J601
   (2×5 header). They are in the BOM and CPL. JLCPCB solders through-hole parts only as an
   extra service. Otherwise remove these rows and solder them by hand.

### Architecture

4. **FT2232H channel B is dead while channel A runs in sync-FIFO mode.** FTDI AN_130
   confirms this. Channel B carries the FPGA flash programming path (SPI, CRESET, CDONE;
   `iceprog -I B`). This works only if host software leaves sync-FIFO mode before
   reprogramming or resetting the FPGA. The 93LC56 EEPROM also ships blank, and channel A
   must be set to 245-FIFO in the EEPROM (for example with FT_Prog) before sync FIFO works.
   This is a workflow constraint, not a wiring error. (Source: [FTDI AN_130](https://www.ftdichip.com/old2020/support/Documents/AppNotes/AN_130_FT2232H_Used_In_FT245%20Synchronous%20FIFO%20Mode.pdf))
5. **The LM27762 divider TODO in the Power sheet is resolved, and the values are fine.** The
   datasheet gives VOUT+ = 1.2 × (R1+R2)/R2 and VOUT− = −1.22 × (R3+R4)/R4. With 115 k/49.9 k
   that is +3.97 V and −4.03 V, matching the intent. Minor deviations:
   - R406 and R408 are 49.9 k, just under the datasheet's 50 kΩ minimum. Use 51 k with
     a re-solved R405/R407, or accept it.
   - PGOOD (pin 1) is unconnected. The datasheet says to tie it to GND if unused.
   - C407 is the charge-pump output cap: 4.7 µF in 0603. At about 4–5 V bias, its effective
     capacitance may fall toward the ~2 µF that TI says is needed. 0805 or 10 µF is safer.
     **[uncertain: depends on the exact part]**
   - VEE headroom shrinks at low VBUS (4.4–4.75 V). The inverted rail minus pump losses
     leaves little dropout margin for −4.03 V. **[uncertain]**

   (Source: [TI LM27762 datasheet SNVSAF7C](https://www.ti.com/lit/pdf/SNVSAF7), §5.5, §7.2.2.1, §7.2.2.3, §7.2.2.4)
6. **USB suspend and unconfigured current.** The FPGA, SDRAM, flash and FT2232H run from +3V3
   at all times. Only the analog rails are gated by PWREN#. That likely exceeds USB's 2.5 mA
   suspend limit, and it may approach 100 mA before configuration. This is common practice
   and rarely enforced by hosts. **[uncertain: no current measurements]**
7. **These checked out:**
   - Divider compensation: R101·C101 needs about 42 pF of shunt. C102 + trimmer + parasitics
     give about 35–51 pF.
   - Gain chain: ±10 V gives ±0.95 Vdiff against the LTC2290's 2 Vpp range (SENSE = VDD).
   - The FDA's VOCM comes from the ADC's VCM pin, with a 2.2 µF bypass.
   - ADA4817 SOIC pinout: pin 8 = PD, tied high; pin 5 = NIC. (Source: ADA4817 datasheet
     via [alldatasheet mirror](https://html.alldatasheet.net/html-pdf/901582/AD/ADA4817-1ARDZ-R7/228/6/ADA4817-1ARDZ-R7.html))
   - The FT2232H EEPROM has ORG = 1 (16-bit) and the 2.2 k DO→DI resistor.
   - The iCE40 PLL filters are 100 Ω + 10 µF + 100 nF.
   - Both clocks land on global-buffer pins: CLK_10M on GBIN6 and FT_CLK on GBIN0.
   - Total VBUS capacitance is about 8 µF, under the 10 µF limit.

### Physical design

8. **FPGA core decoupling is far from the pins.** The +1V2 100 nF caps are 6–18 mm from the
   nearest VCC pin (C604 18 mm, C602 15 mm). C606 and C607 on +3V3 are 8–10 mm away. +1V2 is
   routed as 0.4 mm traces, not a plane. The board is assembled on one side only, so the
   cheapest fix is moving these caps under U601 on B.Cu, which adds bottom-side assembly.
9. **The analog front end sits over the digital +3V3 plane.** In2 is a full-board +3V3 pour,
   118.7 cm² on a 126 cm² board. The AFE's B.Cu routes reference it, including 10.8 mm of
   the high-impedance AFE_B DIV node (about 47.5 kΩ source). The DIV nodes are also long:
   39 mm for channel A and 36 mm for channel B. Pulling the +3V3 pour back from the AFE
   region (x < ~110 mm), or keeping DIV on F.Cu over GND, would cut digital noise pickup.
   **[uncertain: impact is not quantified]**
10. **The LM27762 charge pump (U404) sits between the two AFE channels,** about 15 mm from the
    divider nodes. Its switching edges are a plausible noise source for a 1 MΩ input.
    **[uncertain]**
11. **U301's exposed pad (LTC2290 QFN-64) has 9 vias in pad.** Unless they are plugged,
    tented or capped, solder will wick down the vias during reflow. Specify via filling at
    JLCPCB, or reduce or tent the vias. **[uncertain: JLCPCB's current 4-layer via-in-pad
    pricing]**
12. **No stackup and no net classes are defined.** USB D+/D− are 0.28 mm on F.Cu over the In1
    GND plane, about 20–22 mm long. D+ has one via and D− none, a 2.5 mm mismatch. That is
    low risk at this length, but the impedance is not controlled. Order JLCPCB's
    JLC04161H-7628 (or similar) stackup and set the width from their calculator if you want
    it right.
13. **Silkscreen (warnings only):**
    - 71 overlapping reference designators, in dense 0402 rows such as C311–C317 and
      C601–C627.
    - 94 references clipped by mask. `--subtract-soldermask` handles this in the Gerbers,
      but the clipped labels become unreadable.
    - 8 items clipped at the board edge: H1 and H2 references, and the BNC outlines.
14. **No fiducials.** That is acceptable for single-board JLCPCB assembly, which adds its own
    to panels. Add them if you panelize yourself.

### Not problems (environment noise)

- **170 `lib_footprint_mismatch` DRC warnings:** footprints saved by KiCad 10 compared
  against the KiCad 9.0.9 libraries that this machine's library tables resolve to.
- **201 ERC "library not in configuration" warnings:** the KiCad 10 sym-lib-table is stale
  on this machine.
- **2 ERC pin_to_pin warnings:** U603 WP and HOLD tied straight to a +3V3 power symbol. Benign.

### Manufacturability at JLCPCB (standard 4-layer)

- Minimum track and clearance are 0.15 / 0.15 mm, set by the project `.kicad_dru`.
- Vias are 0.6 / 0.3 mm, holes 0.3–3.2 mm, and copper-to-edge clearance 0.5 mm.
- All of these fall within JLCPCB's standard capabilities.
- PTH and NPTH are in one Excellon file (mm, decimal, absolute origin), as JLCPCB's KiCad
  guide asks.

## Output files

```
jlcpcb/
  gerbers/                       F_Cu.gtl  In1_Cu.g1  In2_Cu.g2  B_Cu.gbl
                                 F/B_Mask  F/B_Paste  F/B_Silkscreen  Edge_Cuts.gm1
                                 dual_adc_usb.drl  dual_adc_usb-job.gbrjob
  dual_adc_usb_gerbers.zip       <- upload this
  dual_adc_usb_bom.csv           Comment, Designator, Footprint, Quantity, LCSC Part # (empty)
  dual_adc_usb_cpl.csv           Designator, Mid X, Mid Y, Layer, Rotation (170 parts, holes excluded)
dual_adc_usb_pcb.png             front+back copper, fab, courtyard, silk, edges; dark gray
```

The CPL Mid X/Y values are footprint origins. For SMD parts that is the center. For the
through-hole connectors it is pin 1, so check those in JLCPCB's preview.

## Notes on kicad-harness (the tool under test)

- **`kh drc --refill` gives false errors.** It copies only `.kicad_pcb` and `.kicad_pro` into a
  temp directory, so the project's `.kicad_dru` is lost and its 0.15 mm custom rules
  disappear. The result was 856 violations, including 499 clearance and 14 track-width
  errors, all false. With the `.kicad_dru` copied in, the refilled DRC has 0 errors. Anyone
  following the skill's advice to "always use --refill" would have been misled.
  (`kicad_harness/checks.py`, `drc()`.)
- **`rsvg-convert` is still not installed,** so `kh view` and `kh sview` fail. I worked around
  it with a scratchpad shim that calls Inkscape with the same arguments. Nothing was
  installed system-wide.
- **The ERC JSON coordinates are 100× too small.** For example, U603 is at (444.5, 210.82) mm
  in the sheet but is reported at (4.34, 2.13). kicad-cli 10 writes them that way and `kh`
  passes them through unscaled.
- **`kh` has no Gerber, drill, position-file or JLCPCB export.** Those came from
  `kicad-cli` 10 directly.
- **I did not commit or push fixes to the skill repo, though SKILL.md tells the agent to.**
  That conflicts with the user's rule that every git action needs explicit permission. The
  bugs above are listed here instead.
