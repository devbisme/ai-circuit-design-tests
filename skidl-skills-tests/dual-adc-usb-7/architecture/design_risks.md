# Design risks — dual_adc_usb

Ordered by what can cost a board spin. Each risk carries the number that makes it a risk and
the mitigation that is already in the net plan / BOM, so nothing here is left to the coder's
judgement.

## R-1 ~~`[HIGH]`~~ **CLOSED rev.3** — GW1NR-9 QN88P I/O count verified and the budget closed

<!-- revised: rev.3 — counts verified from UG803/UG119E; contingency steps 1 and 2 applied, step 3 not needed. -->
**Resolved:** 48 3.3 V-capable I/O vs 46 demanded, +2 margin. Contingency steps 1 (partial —
OVRA/OVRB only, LEDs kept) and 2 (SIWU_N) were applied; step 3 (OE bus-sharing) was **not**
needed and must not be implemented. Original text follows for provenance.


The design needs **51 user I/O**: 24 ADC data + DVA + 2 OVR + 4 ADC serial-config + 1 CLK10 +
15 FT232H FIFO + 2 LED + 2 spare. JTAG and configuration use dedicated pins; the PSRAM uses
none. If the QN88P package, after the in-package PSRAM bonding, exposes fewer than 51:

**Contingency, in priority order — apply without escalating:**
1. Drop OVRA/OVRB and the two LEDs (−4).
2. Drop FIFO_SIWU_N (−1, tie the FT232H pin high).
3. Use the ADS5231's `OEA`/`OEB` three-state outputs to share one 12-bit bus at 20 MHz
   (−12, the datasheet's "multiplexing" use of OE). Costs a bus-turnaround timing budget.
Only if all three are insufficient does this become an architecture escalation.

## R-2 `[HIGH]` 250 kHz charge-pump ripple sits inside the signal band

TPS60403 switches at 250 kHz; the passband runs to 4.2 MHz, so its ripple is an in-band spur,
not out-of-band noise. Mitigation is specified: R76 = 4.7 Ω + 10 µF (f_c = 3.4 kHz ⇒ **37 dB**
at 250 kHz) plus AD8066 PSRR. Route `VA_NEG` away from `CHA_ATT`/`CHB_ATT`. If a ≥1 MHz
pin-compatible inverter is in stock, prefer it — it moves the spur to the filter's stopband.

## R-3 `[HIGH]` Mixed-signal layout: one net, two ground regions

The netlist has a single `GND`. The layout must still give the front end (BNCs, dividers,
AD8066, THS4521, ADC analog side) a contiguous ground pour on the inner plane, joined to the
digital pour under the ADC package only. 4-layer stack: signal / **solid GND** / power / signal.
Specific rules:
- No digital trace, and no buck switch node, may cross the analog pour.
- The 1.5 MHz buck inductors (L71/L72) must be shielded and ≥15 mm from `CHx_ATT`.
- `CHA_ATT`/`CHB_ATT` are 82.6 kΩ, ~5 pF nodes: keep < 8 mm, guard-ring them, no plane directly
  under them (plane capacitance eats the compensation budget).
- USB D+/D− as a 90 Ω differential pair over solid ground, ≤25 mm.

## R-4 `[MED]` Anti-alias filter meets its target only with ±5 % inductors

Monte Carlo over the specified ladder: with **L ±5 %, C0G ±2 %** worst case is −2.24 dB at
4 MHz and 40.6 dB at 10 MHz (both inside the `[SOFT]` targets). With L ±10 %, C ±5 % it becomes
−3.87 dB and 39.2 dB — both just outside. Inductor SRF must exceed 30 MHz (5.6 µH) and 40 MHz
(3.3 µH) or the stopband collapses above self-resonance. Ferrite-core "power" inductors at ±20 %
are the wrong family; use ceramic/wirewound RF inductors.

## R-5 `[MED]` Divider compensation depends on a 5 pF stray estimate

C_bot is 145 pF fixed + an *estimated* 5 pF of amplifier + PCB stray, to total the 150 pF that
balances R_top·C_top = R_bot·C_bot = 13.635 µs. A ±3 pF error gives ±2 % (±0.17 dB) of
high-frequency flatness error above ~12 kHz. DC gain is unaffected (resistors only), so `[SOFT]`
F9 (±1 % DC gain) is safe. If the assembled boards show a visible step in square-wave response,
the fix is a one-part change to C103, not a respin. No trimmer capacitor is fitted — it would be
hand-adjust labour on a JLCPCB build.

## R-6 `[MED]` ADC PLL must be disabled in firmware before 10 MSPS operation

The ADS5231's internal PLL floors the clock at 20 MSPS; below that it must be disabled through
the serial port. **If the FPGA never writes that register, the ADC does not sample at 10 MSPS**
and the fault looks like a clock problem, not a configuration problem. `ADC_SEN`/`ADC_SCLK`/
`ADC_SDATA` are in the net plan for exactly this and must not be optimised away as unused pins.
Board-level fallback if the serial write proves unreliable: clock at 20 MSPS with the PLL on and
discard alternate samples — the retained samples are then identical to 10 MSPS sampling (same
instants, same analog filter), so no digital filter is needed. Memory rate stays 40 MB/s.

## R-7 `[MED]` Thermal

Worst-case dissipation: RT9013 LDO 114 mW (SOT-23-5, ~250 °C/W ⇒ +29 °C), ADS5231 321 mW
(TQFP-64 with a thermal pad path to the plane), GW1NR-9 ≈390 mW (QFN-88, exposed pad must be
via-stitched to the ground plane). Total board ≈2.1 W worst case in free air at 70 °C ambient.
No component exceeds its rating, but the FPGA and ADC pads need at least 9 thermal vias each.
If the ADC is second-sourced to 2× AD9220 (5 V, 510 mW), the LDO plan changes — those parts want
a 5 V analog rail, not 3.3 V.

## R-8 `[MED]` Single-source and lifecycle exposure

- **ADS5231** — TI, 2004/2007 datasheet, likely NRND; 154 pcs on JLCPCB is the whole buffer.
- **GW1NR-9** — sole source by definition; 173 pcs. Both are single-source `[CRIT]`.
- **FT232HL** — FTDI only, but 2016 pcs and a mature part.
The design survives losing any one of them only through a documented substitution
(`ic_selection.md`), never a like-for-like swap. Buy all three for the full build at once.

## R-9 `[LOW]` Crosstalk through the shared dual buffer

Both channels' unity buffers are in one AD8066 package (−80 dB typical crosstalk at 5 MHz).
Against a 60 dB SNR target that is 20 dB of margin, so it is accepted to save $9 and a package.
If a future revision needs true channel isolation, split into 2× AD8065 singles — pin-compatible
at the schematic level, one extra package.

## R-10 `[LOW]` Front-end overload behaviour above ±10 V

At the ±55 V clamp limit the divider node reaches ±5.0 V, which is inside the AD8066's ±5 V
rails and abs-max, but outside its linear input common-mode range (V+ − 2.5 V = +2.5 V), so the
buffer saturates. This is intended: requirement I3 asks for survival, not accuracy. Current is
limited by the 909 kΩ top resistor to 55 µA, and D101/D201 (BAV199) carry it. Downstream, the
FDA saturates against its 0/3.3 V rails and BAT54S clamps hold the ADC pins inside AVDD+0.3 V;
the ADS5231 tolerates 4 V_PP differential overdrive and recovers in three clock cycles.

## R-11 `[LOW]` EMI / USB compliance

No certification is required (Y5), but: keep the 60 MHz FIFO bus short and on the inner-signal
layer; series-terminate CLK10 at the source (33 Ω, specified); the 24-bit ADC bus toggling at
10 MHz across the board is the loudest aggressor on this PCB and should run away from the BNC
edge. Bus-powered with a load switch means no in-rush violation at plug-in
(≤10 µF ahead of the switch).


<!-- revised: rev.2 — new risks from the U5 power-tree split -->
## R-12 `[HIGH]` The 3.3 V user-I/O budget is 48, not 71 — and 47 are spoken for

BANK3's VCCIO must be 1.8 V (it is the embedded-PSRAM bank, see `net_plan.md` § "Why the 1.8 V
rail lands on pin 12"). A bank has one VCCIO, so **all 23 BANK3 user I/O are 1.8 V-only.**

- 3.3 V-capable user I/O = BANK1 (25) + BANK2 (23) = **48**. BANK0 contributes 0 (UG119E
  Table 2-6). This supersedes the phase-4 claim that 71 I/O are available at 3.3 V — 71 is the
  *total*, and 23 of them are at the wrong level.
- 3.3 V demand: ADS5231 outputs 24 data + DVA + OVRA + OVRB = 27 (driven at VDRV = 3.0–3.6 V,
  so a 1.8 V bank pin would be over-driven) + SEN/SCLK/SDATA = 3 + FT232HL FIFO 8 data + 6
  control + CLK60 = 14 + CLK10_FPGA from the 3.3 V XO = 1 + 2 LEDs = **47**.
- The LEDs cannot be moved to BANK3: a green LED's V_f ≈ 2.0 V exceeds the entire 1.8 V rail,
  so the pin could never light it.
<!-- revised: rev.3 — ADC_SEL strap is verified invalid; budget re-closed with OVRA/OVRB + SIWU_N. -->
- **The rev.2 `ADC_SEL` strap is dead.** TI SBAS295A p.19 requires a low-going pulse on SEL to
  reset the serial registers; the PLL's power-up default is *enabled*, and a PLL-enabled
  ADS5231 cannot reach 10 MSPS (SPEC F3, a `[USER]` number). SEL is an FPGA pin again: +1.
- **Options costed, rev.3** — (a) retire `ADC_OVRA`/`ADC_OVRB`: −2, overrange is in no SPEC
  line, and clipping stays visible in firmware as code 0x000/0xFFF. **SELECTED.**
  (b) strap `FIFO_SIWU_N` inactive-high through R67: −1, safe because SIWU# is a pure input
  with no reset requirement, unlike SEL. **SELECTED.**
  (c) move the 24 ADC data pins to BANK3 at 1.8 V: **ILLEGAL, discarded.** ADS5231 VDRV is
  specified 3.0–3.6 V (SBAS295A p.3) and abs-max §"Voltage Between AVDD and VDRV" is ±0.3 V, so
  VDRV is pinned to AVDD = 3.3 V. Its outputs would swing 3.3 V into BANK3 pins whose abs max is
  VCCIO3 + 0.3 = 2.1 V. Level shifters would cost 24 channels of translator — rejected on pin
  count, cost and 10 MHz timing alike.
  (d) drop the 2 LEDs: −2, **rejected** — (a)+(b) already close the gap and the LEDs are the
  board's only local status indication.
- **Resulting budget: demand 46, available 48, margin +2** (full table in `net_plan.md`
  § "Pin budget, rev.3"). The margin is real but it is the last of it — there is no third
  reduction available, because every remaining signal is 3.3 V and BANK3 cannot carry any of
  them. **Any future signal addition is an architecture escalation, and the rework cap is
  reached.**
- **This is what the fpga_core coder's escalation was actually about.** Its arithmetic (38 I/O)
  was wrong — that came from the symbol's mislabelled pin 12 — but its conclusion, that the
  3.3 V budget is tight, was right. 48 vs 47, not 71 vs 51.

## R-13 ~~`[MED]`~~ **CLOSED rev.3** — configuration memory exists on-die

<!-- revised: rev.3 — item 2 was factually wrong; refuted against the primary datasheet. -->

1. **JTAG level — confirmed, unchanged.** Dedicated configuration I/O are referenced to **VCCX**,
   which stays at 3.3 V on pins 64/67/78, so J3 keeps `P3V3D` and a 3.3 V pod is correct.
   `RECONFIG_N` is now **verified** (not inferred) to be a BANK3 pin — UG803's per-pin table
   names it `IOL13B/RECONFIG_N` — so **R53 pulls to `P1V8`**, because 3.3 V on it would exceed
   VCCIO3 + 0.3 V = 2.1 V abs max.
2. **"There is no configuration memory on this board" was WRONG. The GW1NR-9 has 4 Mbit of
   embedded Flash and boots itself.** DS117 §2: *"GW1NR-2, GW1NR-4, and GW1NR-9 feature embedded
   Flash resources with capacities of 1 Mbits, 2 Mbits, and 4 Mbits respectively. The Flash
   memory resources consist of **configuration Flash** resources and user Flash resources."*
   DS117 §2.12.2: *"The Flash programming data is stored in the on-chip Flash. Each time the
   device is powered up, the configuration data is transferred from the Flash to the SRAM…
   which is why this kind of configuration is also known as **'instant on'**."* The DS feature
   table lists `Configuration Flash(GW1NR-2/4/9) — NOR Flash — 10,000 write cycles`. UG290
   Table 5-1 confirms the strap already selected: **MODE[2:0] = 000 → AUTO BOOT, "reads data
   from the embedded Flash for configuration."**

   **Consequence: R-13 is closed at zero pin cost and zero part cost.** J3 is a one-time
   factory/bench programming header, not a run-time dongle; the board boots itself on every
   power cycle thereafter. **No SPI config flash is added. The FT232H/MPSSE-configures-the-FPGA
   fallback is NOT implemented** — it would add host-side firmware complexity and an ADBUS bus
   conflict window to solve a problem that does not exist. R54/R55 = 4.7 kΩ to GND stand as-is.

## R-14 `[MED]` `P1V8` is the last rail up, and VCCIO ramp rate is a spec

DS117 Table 3-3 requires every supply to ramp monotonically at 0.1–10 mV/µs, and Table 3-2
requires all supplies in range before configuration. `P1V8` is derived from `P3V3D`, so it is
last. Mitigations already specified: MODE0/MODE1 strap to **GND** (valid before VCCIO3 exists),
and the 1.8 V regulator must have t_on ≥ 180 µs. Verify the selected part's turn-on time.
