# Documentation defects — netlist NOT affected, for the final review pass

Recorded by the driver so they are not lost. None of these change the netlist; the code
uses the correct values in every case. Fixing them is a documentation task, not a design task.

| Artifact | Defect | Found by | Truth |
|---|---|---|---|
| `architecture/net_plan.md` line 17 | FT232H supply pins listed as VCCIO 13/24/33, VPHY 16, VPLL 20 | usb_bridge coder, rev 2 | Symbol `Interface_USB:FT232H` has VCCIO 12/24/46, VPHY 3, VPLL 8. Pins 13/16/20/33 are ADBUS0/ADBUS3/ADBUS7/ACBUS9 |
| `sourcing/sourced_bom.csv` C610/C611 note | copies the same wrong pin numbers | usb_bridge coder, rev 2 | as above |
| `sourcing/sourced_bom.csv` U5 note | says "free-I/O count (need >=51) still unverified" | driver | Superseded: phase 4 rev 5 verified 48 3.3 V-capable I/O; architecture rev 3 uses 46 with +2 margin |
| `symbols/dual_adc_usb.kicad_sym` U5 pin 12 | labelled `VCCX_VCCO0` | phase 4 rev 5 / architect rev 2 | Gowin UG803 Table 3-8: pin 12 is **VCCIO3**, an independent rail. **This one is in a real artifact the coder consumes — see the fpga_core work order** |

## Bench-verify items — accepted design risks, NOT defects

| Item | Risk | Fallback if it fails |
|---|---|---|
| **U15 ON tied to P1V8_PRE (its own VIN)** | TI SLVSDG1x §6.6 scopes the whole switching table — including the 260 µs CT rise time — to "VIN already in steady state before ON is asserted." Neither available rail satisfies that. Physical argument is sound (U14's 50 µs VIN ramp is 5× faster than the 260 µs gate ramp) but is not a datasheet guarantee. No spare resistor existed in the frozen BOM for the alternative | **Bench-verify VCCIO3 rises ≥180 µs monotonic.** If it fails: RC on U15.ON from P3V3D (10 kΩ + 100 nF), cost 2 new refdes |
| **BAT54S clamp headroom** | 3.7 V worst case against AVDD+0.3 V = 3.6 V absolute max. Accepted in architecture risk register R-10 | Reviewer should re-examine; negative margin against an abs-max rating |
| **Decoupling, 5th instance** | U9/U10/U11/U12 VIN pins have no at-pin 100 nF (only C82/C84/C85 funded). Each has ≥10 µF on its net, so this is HF impedance rather than a missing bypass. U12 is the one worth arguing — analog-rail LDO sharing an input node with two 1.5 MHz switchers | Reviewer's call; add 4 × 100 nF if wanted |
| **J4 USB-C footprint** | "closest 16P horizontal match"; mechanical drawing not cross-checked | Verify against the connector drawing before layout |
| **J1/J2 BNC footprint** | pin spacing not cross-checked vs datasheet | Same |
