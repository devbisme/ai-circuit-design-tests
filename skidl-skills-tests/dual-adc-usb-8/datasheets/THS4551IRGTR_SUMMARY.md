# THS4551IRGTR — TI low-noise precision 150 MHz fully-differential amplifier, VQFN-16 3×3  [KEYSTONE, U102/U202]

Source: `datasheets/THS4551IRGTR.pdf` (TI SBOS778D). Symbol: KiCad `Amplifier_Difference:THS4551xRGT` (17 pins incl. EP=17). **The symbol names pin 12 `~{PD}`**, but the datasheet PD is active-HIGH-enable. Footprint: `Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm`.

| Spec | Value |
|------|-------|
| Supply | 2.7–5.4 V total |
| GBW | 135 MHz |
| IQ | 1.31 typ / 1.84 max mA at 3 V |
| Output swing | (VS–)+0.2 … (VS+)–0.2 V |

## Pinout (RGT, Table 6-1)
| Pin | Name | Function |
|-----|------|----------|
| 1 | FB– | inverting output **feedback** pin (internally the OUT– sense) |
| 2 | IN+ | non-inverting input |
| 3 | IN– | inverting input |
| 4 | FB+ | non-inverting output feedback pin |
| 5, 6, 7, 8 | VS+ | positive supply |
| 9 | VOCM | output common-mode input |
| 10 | OUT+ | non-inverting output |
| 11 | OUT– | inverting output |
| 12 | PD | **high = on**, low = power-down |
| 13–16 | VS– | negative supply |
| EP (17) | thermal pad | isolated from die; must connect to a plane (GND) |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Input CM range, 3 V supply | (VS–) – 0.1 V … (VS+) – 1.3 V over –40…125 °C (→ –0.1…2.0 V on 3.3 V) | §7.6 — **verified**; the 0.52–1.05 V need ✓ |
| PD thresholds | on above (VS–)+1.15 V, off below (VS–)+0.55 V | §7.6 — **verified** |
| FB± pins | separate pins 1/4; **FB– (1) must join OUT– (11) and FB+ (4) must join OUT+ (10)** at the feedback network | Table 6-1 — **verified** |
| EP | electrically isolated; connect to a plane | Table 6-1 note — **verified** |
