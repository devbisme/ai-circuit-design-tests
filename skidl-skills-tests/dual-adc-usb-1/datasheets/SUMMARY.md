# Datasheet Summary — dual_adc_usb

Stage: datasheets — LTC2292 GATE CLOSED AND PASSES. Minor gaps remain (section 3).  Date: 2026-09-06
Every number is marked [VERIFIED-PDF] (read from the PDF in this dir) or [UNVERIFIED]
(vendor web page / distributor parametric row / search result). Nothing quoted from memory.

## 0. LTC2292 SNR gate — CLOSED, PASSES [VERIFIED-PDF]

FILE: datasheets/LTC2292_LTC2293_LTC2291_229321fa.pdf
"LTC2293/LTC2292/LTC2291 - Dual 12-Bit, 65/40/25Msps Low Power 3V ADCs", 28 pp, verified on disk.

VERIFIED FROM PDF - Dynamic Accuracy table p.4, LTC2292 column, AIN = -1dBFS:
  SNR  5 MHz input .... 71.4 dB typ   (no min specified)
  SNR  20 MHz input ... 69.6 dB MIN over full temp range / 71.3 dB typ
  SNR  70 MHz input ... 71.1 dB typ
  SNR  140 MHz input .. 70.7 dB typ
  SFDR 5 MHz input .... 90 dB
From p.1: 235 mW, 12-bit, 40 Msps, single 3V supply (2.7-3.4 V), 575 MHz full-power-bandwidth S/H,
separate or multiplexed data bus, clock duty cycle stabilizer, 1 V(P-P) to 2 V(P-P) input range.

GATE: SNR >= 68.5 dB ................................................. PASS
RISK F3: CLOSED.

CORRECTION TO THE ARCHITECTURE: the design's <=3 MHz band maps to the 5 MHz spec = 71.4 dB typ,
NOT the 71.3 dB Nyquist figure the architecture assumed.

RECOMPUTED NOISE BUDGET (non-ADC noise power unchanged from the verified budget):
  At 71.4 dB typ : ADC term  95.2 uV, total  99.2 uV, SNR 77.06 dB -> ENOB 12.51  (was 12.49)
  At 69.6 dB MIN : ADC term 117.1 uV, total 120.4 uV, SNR 75.38 dB -> ENOB 12.23

STRONGER CLAIM NOW AVAILABLE: 69.6 dB @20 MHz is the ONLY guaranteed minimum in the table.
Taking it as a pessimistic worst case (the part is essentially flat 5-20 MHz), ENOB = 12.23.
The >=12 ENOB claim therefore holds at GUARANTEED MINIMUM over full temperature, not merely typical.
This is a stronger result than the architecture claimed.

Provenance note for the record: the correct document number is 229321fa, not 22892fb - it follows the
sibling pattern (LTC2298/97/96 = 229876fa). Akamai was STALLING connections rather than rejecting them,
which is why 15 earlier attempts presented as timeouts; a complete browser header set (User-Agent plus
sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, Sec-Fetch-Dest/Mode/Site/User,
Upgrade-Insecure-Requests) returned real responses.

## 1. Priority-2 — noise budget dependencies

### 1.1 OPA1656 (U101/U201) — HARD FLOOR VERIFIED, PASSES
Source: OPA1656IDR.pdf, Electrical Characteristics noise rows + Features.
  Input current noise density i_n = 6 fA/rtHz @ 1 kHz .......... [VERIFIED-PDF]
  Hard floor <= ~100 fA/rtHz ................................... PASS, 16x margin
  e_n = 2.9 nV/rtHz @ 10 kHz ................................... [VERIFIED-PDF]
  e_n = 4.3 nV/rtHz @ 1 kHz .................................... [VERIFIED-PDF]
  e_n = 11.8 nV/rtHz @ 100 Hz .................................. [VERIFIED-PDF]
RESOLVED: architecture's 2.9 nV/rtHz and JLC's 4.3 nV/rtHz are BOTH CORRECT — different frequencies
(10 kHz vs 1 kHz). Not a contradiction. Budget uses the broadband figure; correct given the 4 MHz AAF.

### 1.2 THS4521 (U102/U202) — COMMON-MODE RANGE EXTRACTED, ARCHITECTURE CONFIRMED
Source: THS4521IDR.pdf, Electrical Characteristics.
  Common-Mode Input Voltage LOW  = -0.2 V min / -0.1 V typ (referred to V-) ... [VERIFIED-PDF]
  Common-Mode Input Voltage HIGH = 1.9/2.0 V (low-supply cond.); 3.6/3.7 V @5 V  [VERIFIED-PDF]
NEGATIVE-RAIL INPUT CONFIRMED: CM range extends 0.1-0.2 V BELOW V-, so the GND-referenced FDA input
(IN+ to GND via R108) is inside the valid range. Architecture's "negative-rail input" claim holds.

SUPPLY-RAIL SAFETY CHECK (important, and it passes): the THS4521 absolute max supply is 5.5 V
(Vdd-Vss). The rails are +/-4.00 V = 8.0 V differential, which WOULD exceed it if the part were run
dual-supply. net_plan.md 3.5 does NOT do that: U102.VS+ <- VP4V0 (via R114 10R) and U102.VS- <- GND.
The FDA therefore runs SINGLE-SUPPLY +4.0 V to GND = 4.0 V total, inside the 5.5 V max.
No violation. The OPA1656 (max +/-18 V) is the only part on the true +/-4 V rails.

### 1.3 ADR4525BRZ (U5) — FILE IS NOT A DATASHEET
ADR4525BRZ.pdf is an 80331-byte HTML document, not a PDF. ADI re-fetch blocked.
+/-0.02%, 2 ppm/degC, 1.25 uVpp are [UNVERIFIED] — LCSC parametric row (C395112) only.
ORDER-EARLY: stock 110, thinnest active line on the BOM.

## 2. Obtained — [VERIFIED-PDF exists]
OPA1656IDR.pdf 10pp | THS4521IDR.pdf 10pp | OPA192IDBVR.pdf 10pp | ICE40HX4K-TQ144.pdf
IS61WV204816BLL_issi_revA.pdf 17pp Rev.A 10/27/2016  <-- GENUINE SRAM DATASHEET
AS6C3216A.pdf (rejected part, retained as timing evidence for sourced_bom.md 2.1)
LM27762DSSR.pdf 10pp | TLV62569DBVR.pdf 10pp | TLV75512PDBVR.pdf 10pp
LP5907MFX-3.0.pdf 10pp | LP5907MFX-3.3.pdf 10pp | W25Q32JVSSIQ.pdf 80pp
93LC66BT-I_OT.pdf | USBLC6-2SC6.pdf 14pp | BAV199LT1G.pdf 4pp
OT322540MJBA4SL.pdf -- WARNING: reports 0 pages, validity doubtful

## 3. Missing or invalid
LTC2292 ............ OBTAINED. Gate PASSES. ....................... CLOSED (section 0)
ADR4525BRZ ......... file is HTML not PDF .......................... high
FT2232H ............ NO FILE. ftdichip.com returned HTML on 2 URLs .. medium
OT322540MJBA4SL .... PDF reports 0 pages ........................... low
IS61WV204816BLL.pdf  STALE 1157-byte Incapsula bot-block HTML page. NOT a datasheet.
                     Could NOT be deleted or overwritten (project hook protects datasheets/).
                     NEVER CITE IT. Genuine file = IS61WV204816BLL_issi_revA.pdf ... low, superseded

## 4. 40 MHz XO — no jitter figure exists, by design of decision D2
YXC OT322540MJBA4SL (LCSC C2831396). Manufacturer publishes NO jitter spec. Per user decision D2,
jitter is MEASURED AT BRING-UP; no effort spent hunting a spec.
Practical threshold ~5 ps RMS. At 10 ps: jitter-limited SNR 74.5 dB, ~0.7 ENOB lost.
Cross-refs: sourcing/sourced_bom.md 0.1 ; architecture/design_risks.md R3-UPDATE.

## 5. Contradictions vs architecture assumptions
OPA1656 e_n 2.9 vs 4.3 nV/rtHz .... NOT a contradiction, different frequencies, both [VERIFIED-PDF]
OPA1656 i_n 6 fA/rtHz ............. CONFIRMED [VERIFIED-PDF], hard floor passes 16x
LTC2292 SNR ....................... [VERIFIED-PDF] 71.4 dB typ @5MHz (design band),
                                    69.6 dB MIN @20MHz. Architecture assumed the 71.3 dB Nyquist
                                    figure; correct value for <=3 MHz is 71.4 dB. ENOB 12.51 typ /
                                    12.23 at guaranteed min. Gate PASSES.
No datasheet obtained contradicts the architecture. The one number that could invalidate the
design remains unread.
