# XC6SLX9-2TQG144C — Spartan-6 LX FPGA, 144-pin TQFP (KEYSTONE, FPGA core, U30)

Two datasheets obtained and used together:
- `datasheets/XC6SLX9-2TQG144C.pdf` — Xilinx **DS160** "Spartan-6 Family Overview" (11 pp,
  general architecture, device/package I/O-count tables). NOT per-pin.
- `datasheets/XC6SLX9-2TQG144C_DS162.pdf` — Xilinx **DS162** "Spartan-6 FPGA Data Sheet: DC
  and Switching Characteristics" (electrical spec tables, exact MPN mirror via octopart.com,
  verified). NOT per-pin either.
- Per-pin table (144 pins with names/banks) came from `jlc_get_pinout` (EasyEDA-sourced —
  see caveat below), **cross-checked against DS160's stated I/O totals and it matches
  exactly** (102 total User I/O for the TQG144 package — see below).

Symbol generated: `symbols/dual_adc_usb.kicad_sym:XC6SLX9-2TQG144C` (144 pins, EXACT).
Used `pdf-table.py`-equivalent manual extraction since the two Xilinx docs obtained don't
carry a raw per-pin CSV; pin names came from the EasyEDA pinout tool instead (see caveat).

| Spec | Value |
|------|-------|
| Package | TQG144, 20x20mm, 0.5mm pitch |
| Vcc / Vin range | VCCINT = 1.2 V (fixed); VCCAUX = **2.5 V or 3.3 V** (board-selectable, see Load-bearing facts); VCCO per bank = 1.2–3.3 V (board-selectable per bank) |
| Key spec | 9,152 logic cells / 1,430 slices; 102 user I/O in this package |
| Max current / power | not extracted (DS162 has full I_CC tables; not read in this pass — budget spent on the power-rail compatibility question instead, see below) |
| Operating temp | 0°C to +85°C (this is the "C" commercial grade suffix) |

## Pinout — EasyEDA-sourced, cross-checked for I/O count, NOT independently checked pin-by-pin against Xilinx's per-package pinout table

**Caveat (read before use):** Xilinx's actual per-package pin table lives in UG385
"Spartan-6 FPGA Packaging and Pinout Specification," which was **not obtained** this pass
(time/budget spent instead on confirming the power-rail question below, judged higher
value). The 144-pin table used to build the symbol came from `jlc_get_pinout` (EasyEDA
community data). Its **aggregate counts were cross-verified against DS160's own numbers**
(102 total User I/O, matches DS160 Table 2 exactly for TQG144/XC6SLX9) which gives
confidence the bank/pin-count structure is right, but individual pin *names* (e.g. which
physical ball is `IO_L44N_GCLK20_3` vs `IO_L43P_GCLK23_3`) are not independently verified
against a Xilinx primary source. **If exact clock-capable-pin or GCLK routing matters for
a specific net (e.g. which pin carries the FPGA's global clock input), re-verify against
UG385 or the Xilinx pinout .txt file before finalizing that specific net.**

**UPDATE (verification pass, 2026-09-21) — pins 124 and 56 now VERIFIED against UG385.**
Xilinx UG385 "Spartan-6 FPGA Packaging and Pinouts — Product Specification," **v2.3, May
12, 2014**, Table 2-2 "TQG144 Package—LX4 and LX9" (p.30-33 of the PDF) was obtained
(mirror: gab.wallawalla.edu, confirmed to be the genuine Xilinx document by its title page,
revision history and full 364-page structure) and diffed against the two pins this design's
clock path depends on:

| Symbol pin | Symbol name (EasyEDA) | UG385 Table 2-2 | Bank | BUFIO2 region | Match |
|---|---|---|---|---|---|
| 124 | `IO_L37P_GCLK13_0` | `IO_L37P_GCLK13_0`, Pin Number P124 | 0 | TR | **VERIFIED — exact match** |
| 56 | `IO_L30P_GCLK1_D13_2` | `IO_L30P_GCLK1_D13_2`, Pin Number P56 | 2 | BR | **VERIFIED — exact match** |

Both names contain `_GCLKn_`, and UG385 p.16 (§"Pin Descriptions", GCLK row) states
explicitly: *"GCLK — These clock pins connect to global clock buffers... These pins become
regular user I/Os when not needed for clocks"* and p.21 *"Global clock (GCLK) input pins can
connect directly to the global clock buffers (BUFGs)."* **Pin 124 (used in this design as
CLK_FPGA, `fpga_core.py` line 19) is confirmed clock-capable — it is a genuine GCLK input,
not a plain I/O**, so the capture-clock path is sound. Pin 56 (used as IFCLK, `fpga_core.py`
line 54) is also GCLK-capable, which is incidental (IFCLK is a FIFO/data-valid strobe from
the FX2LP, not routed through a Spartan-6 PLL in this design) but not a problem.

The rest of the 144-pin table (all other pin names) remains **unverified pin-by-pin** — only
these two pins, the ones flagged as unrecoverable-if-wrong, were checked this pass. UG385 is
not placed in `datasheets/` (the fetch guard correctly rejects it: it's a Xilinx family-wide
packaging spec covering 9 packages and doesn't mention "XC6SLX9" by name in its first pages,
so it fails the right-part check) — the verified excerpt is recorded here instead.

| Bank | User I/O count | Notes |
|------|------|-------|
| Bank 0 | 26 (incl. dual-purpose HSWAPEN on pin 144) | GCLK12-19 clock-capable pins present |
| Bank 1 | 24 | GCLK4-11 clock-capable pins present |
| Bank 2 | 26 (incl. config pins PROGRAM_B, DONE, CMPCS_B not counted in the 26) | Shares pins with SPI/BPI configuration (D0-D15, MOSI, MISO, CCLK) — **this design's W25Q32JVSSIQ SPI flash almost certainly attaches here** |
| Bank 3 | 26 | GCLK20-27 clock-capable pins present |
| **Total user I/O** | **102** | Matches DS160 Table 2 exactly — cross-check passed |
| Dedicated (not counted in banks) | TDO, TMS, TCK, TDI (JTAG), SUSPEND, DONE, PROGRAM_B, CMPCS_B | |

Full per-pin CSV: `datasheets/xc6slx9_kipart.csv` (used to build the symbol; same content,
one row per physical pin, in the project directory for the coder to reference directly).

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| VCCINT | 1.2 V, fixed | DS160 p.1 Features list ("High performance 1.2V core voltage") — **verified**. Matches `sourced_bom.md`'s +1V2 rail exactly |
| VCCAUX | **Either 2.5 V or 3.3 V** is an explicitly valid Recommended Operating Condition (not just an absolute-max excursion) — Table 2 lists both as separate rows with their own full spec range | DS162 (exact-MPN mirror), Table 2 "Recommended Operating Conditions" — **verified**. This resolves what looked like a missing-rail problem: this design's power block only budgets +3V3D and +1V2 (no separate 2.5V rail, per `sourced_bom.md` decision #1) — **VCCAUX must be tied to +3V3D (the 3.3V option), not left floating or assumed to need a nonexistent 2.5V rail** |
| VCCO per bank | Configurable per bank: "Includes VCCO of 1.2V, 1.5V, 1.8V, 2.5V, and 3.3V" | DS162 Table 2 note 3 — **verified**. All 4 banks in this design almost certainly tie to +3V3D (SDRAM at 3.3V, SPI flash at 3.3V, JTAG/LEDs at 3.3V) — but this is an inference from the rest of the BOM, not read off a per-bank net assignment in `net_plan.md` |
| VCCAUX=2.5V-only restriction | Only applies to "-1L" (low-power) speed-grade devices using certain LVDS I/O standards | DS162-adjacent web search of the same document family — **UNVERIFIED against the DS162 PDF text directly** (found via search snippet, not confirmed by reading the relevant DS162 section this pass). This part is speed grade "-2" (XC6SLX9**-2**TQG144C), not -1L, so likely doesn't apply — flagged rather than asserted |
| Pin 124 = `IO_L37P_GCLK13_0` (Bank 0, GCLK-capable) — used as `CLK_FPGA` | Confirmed | UG385 v2.3 (May 2014), Table 2-2 "TQG144 Package—LX4 and LX9", p.30 — **verified** |
| Pin 56 = `IO_L30P_GCLK1_D13_2` (Bank 2, GCLK-capable) — used as `IFCLK` | Confirmed | UG385 v2.3 (May 2014), Table 2-2 "TQG144 Package—LX4 and LX9", p.32 — **verified** |

## Notes — the highest-value findings for the coder

1. **Tie VCCAUX to +3V3D.** This is not optional and not obvious from the BOM alone —
   Spartan-6's VCCAUX is a separate named supply pin group from VCCINT and VCCO, and if the
   coder assumes it needs a dedicated 2.5V rail (the "textbook" Spartan-6 default), they'll
   either invent a rail that doesn't exist in this design's power block or leave VCCAUX
   unconnected. Per DS162 Table 2, 3.3V is an equally valid, fully-specified recommended
   operating point — tie all VCCAUX pins to +3V3D.
2. **Bank 2 carries the SPI flash boot interface** (D0-D15/MOSI/MISO/CCLK pin overlays,
   see pinout table) — the W25Q32JVSSIQ (U31) almost certainly connects here. Its VCCO_BANK2
   should match the flash's 2.7-3.6V supply (3.3V).
3. **R30, R34–R39** (`fpga_core` block, flagged unallocated in `sourced_bom.md`) are very
   plausibly config-pin pull resistors: M0/M1 mode-select straps (select the boot mode —
   Master SPI, given the flash on bank 2), PROGRAM_B pull-up, INIT_B pull-up, DONE pull-up,
   and/or HSWAPEN strap (pin 144, dual-purpose with IO_L1P). That's 5-7 candidate config
   pins against 7 unallocated resistors (R30+R34..R39) — a strong fit, but **not confirmed**:
   the exact Xilinx config-mode pin table (in UG380 "Configuration User Guide," not
   obtained this pass) is needed to assign M0/M1 to the correct boot mode and confirm which
   pins need external pulls vs. having adequate internal pull resistors already. Flag this
   explicitly to the coder as an open config-strapping question, not a placeholder to
   silently accept at 10 kΩ.
4. JTAG pins (TDO/TMS/TCK/TDI, pins 106/107/109/110) are dedicated — not part of the 102 I/O
   budget, and connect directly to the JTAG header (J4, HX PZ1.27-2x3P).
5. **(Verification pass)** Pins 124 (`CLK_FPGA`, `fpga_core.py` line 19) and 56 (`IFCLK`,
   `fpga_core.py` line 54) are confirmed against UG385 v2.3 Table 2-2: pin 124 =
   `IO_L37P_GCLK13_0` (Bank 0, GCLK-capable), pin 56 = `IO_L30P_GCLK1_D13_2` (Bank 2,
   GCLK-capable). Both names and numbers match the symbol exactly. No code change needed.
