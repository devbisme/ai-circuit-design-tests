# dual-adc-usb-1 — executive summary

## What was done

Six short prompts in one session tried out kicad-mcp-server as an **analyzer** on an existing
design. The design is the KiCad project from [Konnect run 2](../../konnect-tests/dual-adc-usb-2/).
Claude did not change it. The prompts asked Claude to:

1. Say what the design does.
2. Check the wiring against the schematic notes.
3. List risks that could make the board malfunction.
4. Generate Gerbers for JLCPCB.
5. Render a PNG of the PCB showing the top and bottom layers.
6. Change the PNG's background color.

`dual-adc-prompt.txt`, the original design prompt, was not given to Claude.

## Results

| Item | Result |
|---|---|
| Function | Correctly identified as a 2-channel, 12-bit, 10 MS/s USB digitizer: BNC → ÷20 divider → ADA4817 → THS4521 → LTC2290 → iCE40HX4K + 16 MB SDRAM → FT2232H. This came from the sheet notes and part values. |
| Wiring check | Pin-by-pin netlist check found 2 mismatches with the notes (below). Everything else matched. |
| ERC / DRC | ERC clean. DRC 0 errors, 343 warnings (cosmetic, plus 170 footprint/library mismatches). |
| Risk review | 13 items in three groups: could stop the board working, could miss spec, could damage the board or work only intermittently. |
| Fab outputs | `gerbers/` and `dual_adc_usb_jlcpcb_gerbers.zip` (JLCPCB settings). `dual_adc_usb_layers.svg/.png` (top/bottom copper, silkscreen, fab, outline). |
| Cost / time | $2.05 equivalent API cost (`claude_cost.txt`). About 8 min of model working time; 7:54 to 8:26 wall clock. |

## Main findings

These are as Claude reported them. **I have not validated them.**

- **No FPGA clock at power-up.** The 10 MHz oscillator runs from the 3.0 V rail, which only
  switches on after USB enumeration. The iCE40 has no internal oscillator. Claude said it was
  confident about this one.
- **−4 V rail is unverified.** The LM27762 negative-feedback divider TODO in `power.kicad_sch`
  is still open.
- **iCE40 PLL ground pins** (U601 pins 53, 127) are tied to board ground. Claude said it was
  ~75 % confident these are wrong, and pointed to Lattice TN1252 to check.
- **Input capacitance is ~2 pF, not the ~12 pF the notes claim.** 10× scope probes may not be
  able to compensate.
- **Analog layout noise:** the charge pump sits between the two input channels, and USB is
  next to channel A. A 50 kΩ divider node has a 39 mm trace, and the ADC inputs are routed
  next to the 3.3 V plane.
- Lower risks: USB D+/D− impedance and length mismatch, 100 MHz SDRAM timing on an HX part,
  40 MB/s streaming at the FT2232H limit, ADC overdrive above ~±38 V input, and the FPGA
  back-powering the ADC through its pull-ups.

Claude named items 1–3 and the input capacitance as the cheap fixes to make before fab. The
Gerbers reproduce the design as-is, with none of these fixed.

## How kicad-mcp-server held up

- **Used for:** netlist generation and per-component pin queries, ERC and DRC. That was 5 MCP
  calls in all.
- **Not used:** the Gerber and image exports. Claude called KiCad 10's `kicad-cli` and Inkscape
  directly, and read trace lengths and placement straight from the `.kicad_pcb` text.
- **Pinouts and limits** came from the model's memory of the datasheets, plus the KiCad symbol
  pin names for five ICs. Claude said so and listed which items to check first (−4 V divider,
  PLL grounds, ADC overdrive).
- **Version mismatch:** the system `kicad-cli` (9.0.9) can't read these KiCad 10 files. Claude
  found this and switched to the KiCad 10 binary, the same one the MCP server uses.

## Sources

`claude_transcript.txt` (findings, timestamps, number of MCP calls), `claude_cost.txt`.
