# OPA356AIDBVR — TI 200 MHz GBW CMOS RRO op-amp, SOT23-5  [KEYSTONE, U101/U201 input buffer]

Source: `datasheets/OPA356AIDBVR.pdf` (TI SBOS212A). Symbol: KiCad `Amplifier_Operational:OPA356xxDBV`. Its pins are named 1=`~` (output), 2=`V-`, 3=`+`, 4=`-`, 5=`V+`, so **use pin numbers in SKiDL**. Footprint: `Package_TO_SOT_SMD:SOT-23-5`.

| Spec | Value |
|------|-------|
| Supply | 2.7–5.5 V specified (2.5–5.5 operating); abs max 7.5 V |
| GBW | 200 MHz (G = +10); unity-gain BW 450 MHz; unity-gain stable |
| Slew / noise | 360 V/µs / 5.8 nV/√Hz |
| IQ | 8.3 typ / 11 max mA at 5 V |
| Input bias | 3 pA |

## Pinout (SOT23-5, p.2)
| Pin | Name | Function |
|-----|------|----------|
| 1 | Out | output |
| 2 | V– | negative supply |
| 3 | +In | non-inverting input |
| 4 | –In | inverting input |
| 5 | V+ | positive supply |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Input CM range | (V–) – 0.1 V to **(V+) – 1.5 V** | EC p.3 — **verified** |
| Supply span | ≤5.5 V specified | EC — **verified** (net plan worst case 5.438 V ✓) |
| Input abs max | (V–) – 0.5 V to (V+) + 0.5 V | p.2 — **verified** (BAV199 clamps to rails ±~0.7 V; R103 1 k limits current) |
| Pin order | 1 Out, 2 V–, 3 +In, 4 –In, 5 V+ | p.2 — **verified** |
| θJA SOT23-5 | 150 °C/W | p.3 — **verified** |
