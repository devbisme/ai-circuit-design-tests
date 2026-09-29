# Coding brief — `dual_adc_usb`

Written 2026-09-07. Resume point for the coding stage after the previous agent was
stopped. Read this together with `SPEC.md`, `architecture/`, and `sourcing/sourced_bom.md`.

## D3 — CLKOUT escalation: RESOLVED

**The error.** `architecture/net_plan.md` §3.6 defined net `adcClkOut` as
`U7.CLKOUT → fpga_ice40 GBIN`, "data-capture clock, guarantees setup/hold".
**The LTC2292 has no CLKOUT pin.** Verified: zero occurrences of "CLKOUT" across all
28 pages of `datasheets/LTC2292_LTC2293_LTC2291_229321fa.pdf`. The part has CLKA
(pin 8) and CLKB (pin 9) as clock *inputs* only. The claim was inherited from
`ic_selection.md` while the datasheet was unobtainable and specs came from ADI's
product page — the same gap that produced the 71.3 vs 71.4 dB SNR discrepancy.

**User's decision:** clock the FPGA's input registers from the same 40 MHz XO that
drives CLKA/CLKB. The sample clock is NOT routed through the FPGA — that would
violate the Q7 constraint that the FPGA never synthesizes the sample clock.

### Required changes
- Delete net `adcClkOut` from `net_plan.md` §3.6 and the pin tables.
- Remove the CLKOUT claim from `ic_selection.md`'s LTC2292 feature list.
- FPGA capture clock is `xoClkFpga`, which already exists.
  `circuits/dual_adc_usb/clock_40m.py` is already written with the right signature:
  `clock_40m(vbus_a5v, gnd, enc_clk40, xo_clk_fpga)`.
- The XO now drives **three** loads: CLKA, CLKB, and the FPGA GBIN. Verify drive
  strength and series termination; add a fanout buffer if needed rather than
  silently overloading it.
- `xoClkFpga` must land on a GBIN global clock input.

### Timing — from the datasheet, Digital Interface table p.6, LTC2292 column, C_L = 5 pF
(● denotes full operating temperature range)

| Symbol | Parameter | Min | Typ | Max |
|---|---|---|---|---|
| t_D | CLK to DATA delay | 1.4 ns | 2.7 ns | 5.4 ns |
| — | Data access time | — | 4.3 ns | 10 ns |
| t_AP | Aperture delay | 0 ns | | |
| t_JITTER | Aperture jitter | | 0.2 ps RMS | |

t_JITTER = 0.2 ps RMS is negligible, confirming the XO dominates the jitter budget —
consistent with decision D2.

### Capture edge — IMPLEMENT FALLING EDGE

At 40 MHz, T = 25 ns. Sample N's data is fully valid from t_D(max) = 5.4 ns after its
launching edge until the next edge + t_D(min) = 26.4 ns. **Valid window = [5.4, 26.4] ns**, 21 ns wide.

- Rising-edge capture at t = 25 ns: setup 19.6 ns but **hold only 1.4 ns** — that is
  t_D(min) itself, before subtracting iCE40 input-register hold and clock skew. Too tight. Rejected.
- **Falling-edge capture at t = 12.5 ns: setup 7.1 ns, hold 13.9 ns.** Near the centre
  of the window, comfortable both sides, and needs no PLL. **Use this.**

Document the 7.1 / 13.9 ns margins in `net_plan.md` and in the `adc_dual` block
comments so the edge choice is traceable.

A PLL phase shift on the *capture* clock would also be legal — the ADC encode clock
still comes straight from the XO, so Q7 is not violated — but it is unnecessary here.

## Coding state at resume

`coding_mode: "modular"`, 12 blocks. Written and compiling clean (5):
`usb_power_input`, `power_digital`, `power_analog`, `clock_40m`, `sram_buffer`.
Remaining (7): `vref_2v5`, `afe_channel` (×2, the only parameterized block),
`adc_dual`, `fpga_ice40`, `config_flash`, `usb_bridge_ft2232h`, `aux_io`.

No `__init__.py` / `__main__.py` yet — the assembler has not run, so there is nothing
instantiated and **ERC has not been run**. That is correct for this state; do not run
ERC on the partial package to silence the stop hook. Assemble first, then ERC for real.

## Still open (non-blocking)

- **XO jitter unverified by design of D2** — measure at bring-up, ~5 ps practical
  threshold, ~0.7 ENOB lost at 10 ps. Drop-in swap on the 3225 footprint.
- `datasheets/ADR4525BRZ.pdf` is an 80 KB HTML file, not a PDF — accuracy/tempco/noise
  unverified. Retry with full browser headers (see below).
- FT2232H datasheet missing; ftdichip.com returned HTML.
- THS4521 PDF present but ±4 V common-mode range not extracted — the ±4.00 V rail
  decision depends on it.
- ADR4525BRZ stock 110, thinnest active line — order early.
- `datasheets/IS61WV204816BLL.pdf` is a 1157-byte bot-block page. A hook blocks
  deleting/overwriting it. Never cite it; the genuine file is
  `IS61WV204816BLL_issi_revA.pdf`.

### Fetching datasheets past Akamai
analog.com stalls connections rather than rejecting them, so attempts look like network
failures. A complete browser header set gets real responses: `User-Agent`, `sec-ch-ua`,
`sec-ch-ua-mobile`, `sec-ch-ua-platform`, `Sec-Fetch-Dest/Mode/Site/User`,
`Upgrade-Insecure-Requests`. Document numbers follow a sibling pattern — LTC2298/97/96
is `229876fa`, so LTC2293/92/91 is `229321fa` (not `22892fb`, which was tried 15 times).
