# Dual-channel ADC board: design decisions

Source of truth for the circuit: `dual_adc_usb.py` (SKiDL). The schematic in
`schematic/` is generated from it, and the board in `dual_adc_usb.kicad_pcb` is built from the
schematic netlist.

## Requirements (from `dual-adc-prompt.txt`)

| # | Requirement | How it's met |
|---|-------------|--------------|
| R1 | 2 channels, input range −10 V … +10 V | /10 attenuator (1 MΩ) plus an FDA with G = 0.953 into a 2 Vpp ADC span. Full scale is ±10.6 V, about 6 % over-range margin. |
| R2 | 10 MSPS, 12 bits | LTC2291 dual 12-bit ADC (rated to 25 MSPS), clocked at 10.000 MHz from a dedicated XO. |
| R3 | ≥ 0.1 s at max rate | 2 ch × 10 MS/s × 2 B × 0.1 s = 4 MB. The 8 MB SDRAM holds **0.2 s**. |
| R4 | Inputs mate with standard scope leads | BNC jacks. Input is 1.009 MΩ ∥ ≈20 pF and frequency-compensated, so 1× leads and 10× passive probes both work. With a 10× probe the range becomes ±100 V. |
| R5 | USB 2.0 for power + data | FT2232H (USB 2.0 High-Speed) on a USB-B receptacle, bus powered. |
| R6 | USB-C only if power is insufficient | The estimated load is ≈1.4 W (about 280 mA at 5 V) against a 2.5 W budget, so USB 2.0 is enough and USB-C isn't needed. |

## Decisions (options → choice)

### D1. Capture architecture
- **A. Stream straight to the host.** 2 × 10 MS/s × 16 b = 40 MB/s, which is at the practical limit of USB 2.0 HS bulk transfers. It depends on the host and would drop samples.
- **B. Buffer in memory on the board, upload afterwards.** The upload speed no longer matters.
- **Choice: B.** The requirement is a 0.1 s *capture*, not continuous streaming.

### D2. Buffer memory (≥ 4 MB)
- FPGA block RAM: far too small (HX4K has 80 kbit).
- Async SRAM 4 M×16: expensive, and the hand-solderable package options are poor.
- HyperRAM 8 MB: cheap, but BGA-24 and a newer controller.
- **SDR SDRAM 4 M×16 (IS42S16400J, TSOP-II-54): cheap and leaded, with mature open-source controllers.** Needs 40 MB/s, and gets 200 MB/s peak at 100 MHz.
- **Choice: IS42S16400J-7TL** (8 MB).

### D3. Controller
- MCU with an FMC + SDRAM + parallel camera interface (e.g. STM32H7): its DCMI is ≤14 bits wide and can't take two 12-bit buses.
- **FPGA**: takes both 12-bit buses directly and does deterministic SDRAM timing.
- Choice: **Lattice iCE40HX4K-TQ144**. TQFP is hand-solderable, there's an open toolchain (yosys/nextpnr/iceprog), 3520 LUTs, 2 PLLs and 107 I/O. The design needs about 90 I/O.

### D4. USB bridge
- FT232H in 245 synchronous FIFO mode (40 MB/s). Its MPSSE pins would collide with the config-flash SPI, so flash programming would need a separate header.
- Cypress FX2LP: needs custom 8051 firmware.
- MCU with a ULPI PHY: more firmware and more parts.
- **FT2232H**: channel A in MPSSE mode programs the iCE40 flash using the standard `iceprog` wiring (ADBUS0 SCK, 1 MOSI, 2 MISO, 4 CS, 6 CDONE, 7 CRESET). Channel B is a 245 **asynchronous** FIFO (≈8 MB/s) for data and commands.
- **Choice: FT2232H.** Uploading a 4 MB capture takes ≈0.5 s. With D1 = B that's acceptable, and it keeps USB-based reprogramming. ACBUS0–3 also go to the FPGA as spare lines.

### D5. ADC
Candidates found in the KiCad 10 library: LTC2290 (10 MSPS), **LTC2291 (25 MSPS)**, LTC2292 (40 MSPS), and two single-channel ADCs.
- **Choice: LTC2291IUP.** It's dual, 12-bit, and has independent CLKA/CLKB and parallel CMOS outputs. Running it at 10 MSPS leaves headroom, and the LTC2290's 10 MSPS limit would leave none. It also keeps a path open to 2× oversampling (20 MHz XO plus FPGA decimation) if the analog anti-alias filter proves inadequate.
- Configuration: SENSE = VDD (2 Vpp span), MUX = VDD (A→DA, B→DB), MODE = VDD/3 (offset binary, clock duty-cycle stabilizer on), OE = GND, SHDN under FPGA control.

### D6. Front end
- Input coupling: DC only. AC coupling isn't required, and the host can remove offset.
- Buffer: OPA810 (140 MHz, FET input, rail-to-rail I/O, 3.7 mA). The alternatives were OPA656 (14 mA) and ADA4817 (19 mA), which need more power, and LTC6268 (5 V single supply only).
- Single-ended to differential: THS4521 (1 mA, 3.3 V, negative-rail input). ADA4932 draws ~10 mA.
- Attenuator: 909 k / 100 k (0.1 %), compensated with 2.2 pF across the top resistor and 10 pF + a 3–10 pF trimmer across the bottom. A 15 pF shunt sets C_in ≈ 20 pF. A BAV99 clamps to the ±3.3 V rails, and the 909 k resistor limits fault current to ~0.1 mA per 100 V.
- Anti-alias filter: the FDA's feedback pole (953 Ω ∥ 22 pF, 7.6 MHz) plus an output RC (2 × 49.9 Ω, 330 pF differential, 4.8 MHz). **This is a 2-pole filter, so alias rejection at 5–10 MHz is modest.** It's a known limitation; see the open issues.

### D7. Power tree (VBUS 5 V)
| Rail | Source | Load (est.) |
|------|--------|-------------|
| +3V3 (digital) | TLV62569 buck (2 A) | FT2232H ~70 mA, FPGA I/O + 1V2 LDO ~60 mA, SDRAM ~100 mA, flash, XOs, LEDs: **~250 mA** |
| +1V2 | AP2112K-1.2 LDO from +3V3 | FPGA core ~30–50 mA |
| +3V3_ADC | LP5907-3.3 LDO from +5V | LTC2291 ~45 mA, 2× THS4521 2 mA |
| ±3V3A | LM27762 (LDO + inverting charge-pump LDO) | 2× OPA810, ~8 mA each rail |

Estimated 5 V input: buck ≈190 mA (90 % efficient) + LP5907 ≈50 mA + LM27762 ≈25 mA ≈ **270–300 mA (≈1.4 W)**. That's 55–60 % of the USB 2.0 500 mA allowance. **These figures are estimates.** The LTC2291 and FT2232H currents come from memory because their datasheets couldn't be downloaded.

USB compliance details:
- The total capacitance on +5V is about 8 µF nominal, under the USB 2.0 attach limit of 10 µF.
- The buffer rails stay off at power-up. The FPGA enables them through `ANA_EN`, after `FT_PWREN_N` shows the device has been configured by the host.

### D8. Clocks
- The ADC clock comes from a dedicated 10.000 MHz CMOS XO, not from the FPGA PLL. A PLL with ~300 ps of jitter would cap SNR at about 40 dB for a 5 MHz input, and 12 bits needs well under 10 ps. The XO drives the ADC CLKA/CLKB through 22 Ω and the FPGA GBIN6 through 33 Ω.
- A 25 MHz XO feeds FPGA GBIN5. The PLL makes 100 MHz for the SDRAM. The iCE40 PLL accepts 10–133 MHz in, so the 10 MHz clock would have been right at the limit.

### D9. Connector
- **USB-B (THT, OST USB-B1HSxx)** was chosen over Micro-B, Mini-B and USB-C (USB 2.0 only). The prompt prefers plain USB 2.0 when the power is sufficient, and USB-B is the most rugged for a bench instrument.

### D10. PCB
- 4 layers: F.Cu signals, In1 solid GND, In2 power, B.Cu signals.
- The ground plane is one piece. Analog and digital sections are separated by placement, not by splitting the plane.
- Layout runs left to right: BNCs and front end, then the ADC, then the FPGA, then SDRAM and USB.

### D11. Schematic generation
- **SKiDL `generate_schematic()` (schematizer, KiCad 10 target):** tried first, output kept in
  `schematizer_out/`. It **failed the connectivity check**:
  - The KiCad-exported netlist merges GND with +3V3 and drops dozens of pins from their nets.
  - KiCad ERC reports 910 violations: 345 off-grid endpoints, 77 dangling labels, 19 unflagged NC pins, and a +3V3/GND "multiple net names" error.
  - The files declare format version 20230409 (KiCad 7) and write single-level `/uuid` instance paths for symbols on child sheets.
  - Without `auto_stub` it ran for more than 30 minutes without finishing.
- **Own label-based writer (`scripts/sch_writer.py`):** chosen. There's one sheet per SKiDL subcircuit, and each pin gets a stub ending in a power symbol, a global or local label, or a no-connect flag.
  - Connectivity is exact by construction. `scripts/compare_netlists.py` confirms the kicad-cli netlist matches SKiDL's: 172/172 multi-pin nets, identical pin sets.
  - KiCad 10 ERC: **0 violations**.
  - Trade-off: it reads like a netlist with symbols, not a hand-drawn signal-flow schematic.

### D12. Layout decisions made during routing
- **Inner layers are planes only.**
  - Option: let Freerouting use In1/In2 for signals. The first run did, and it cut the planes into islands.
  - Chosen: mark In1/In2 as `power` in the DSN, so signals go on F/B only.
- **FPGA pin swapping.**
  - Default bank-ordered assignment: the DA/DB/SDRAM/FIFO buses crossed over themselves, and routing stalled.
  - Chosen: `scripts/pin_swap.py` orders FPGA pins by angle around the package to match the partner pads. FPGA pins are just gateware constraints, so this is free.
- **ADC bus spacing.**
  - 0.15/0.15 mm: the QFN-64 top/bottom rows couldn't escape (2–5 links left on every attempt, including rip-up).
  - 6 layers: more cost.
  - Chosen: **0.1/0.1 mm net class for DA*/DB*/OF* only.** This needs an advanced process tier.
- **USB.**
  - Original orientation: D+/D− were 34–39 mm long with up to 3 vias.
  - Chosen: rotate the FT2232H 180° so DM/DP face J1, put the USBLC6 in flow-through between them, and pre-route the pair at 0.2 mm (about 10 mm each).
- **Decoupling of the large ICs.** Decoupling capacitors for the FPGA, SDRAM and FT2232H are on B.Cu under the pin rows, so assembly is double-sided. There are fiducials on both sides.

## FPGA bank plan (all VCCIO = 3.3 V; pin order within each group set by scripts/pin_swap.py, final pins in gateware/dual_adc_usb.pcf)
| Bank | Side | Use |
|------|------|-----|
| 3 | left | ADC DA[11:0], OFA, DB[11:0], OFB, ADC_SHDN; GBIN6 (pin 21) = ADC clock |
| 1 | right | SDRAM DQ, DQM, control, BA, CLK |
| 0 | top | SDRAM A[11:0] (top-right), LEDs, FT ACBUS0–3, 8-pin GPIO header |
| 2 | bottom | FT2232H ch B FIFO + control, ANA_EN / ANA_PG_N; GBIN5 (pin 49) = 25 MHz; config SPI |

## Verification status
Checked against downloaded datasheets (`datasheets/`):
- TLV62569: the 0.6 V feedback reference, the 2.2 µH / 10–22 µF combination and the 6.8 pF feed-forward capacitor.
- LM27762: the ±1.2 V / −1.22 V feedback equations, R2/R4 ≥ 50 k, and the 1 µF / 4.7 µF / 2.2 µF capacitors.
- THS4521: the pinout, the 3.3 V input common-mode range of −0.1 V to 1.9 V (the design uses 0.5–1.0 V) and PD polarity.
- OPA810: supply range 4.75–27 V (the design uses 6.6 V) and unity-gain stability.
- iCE40: VPP_2V5 at 3.3 V for controller SPI configuration, VPP_FAST left unconnected, the VCCPLL filter, the config pull-ups and the PLL input range (FPGA-TN-02006, FPGA-TN-02052, FPGA-DS-02029).
- IS42S16400J: currents and refresh.

**Not verified (datasheets couldn't be downloaded; analog.com timed out and ftdichip.com returned 403):**
- **LTC2291:** pin functions (SENSE, MODE levels, MUX), reference bypass network, VDD range 2.7–3.4 V and power.
- **FT2232H:** REF = 12 kΩ, VREGOUT/VCORE decoupling, the EEPROM wiring and the ch B async FIFO pin map.

These follow the KiCad symbols and published reference designs from memory. **Check them against the datasheets before fabrication.**

## Open issues / technical debt
- TODO: the anti-alias filter is 2nd order. For better alias rejection, either use a 4th/5th-order LC filter between the FDA and the ADC, or run the ADC at 20 MSPS and decimate in the FPGA.
- TODO: gateware (capture FSM, SDRAM controller, FIFO protocol) and host software are out of scope.
- TODO: the LTC2291 duty-cycle stabilizer may have a minimum clock rate. MODE is set by a resistor divider, so it's easy to change.
