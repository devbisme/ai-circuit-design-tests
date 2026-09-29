# 74LVC1G34GW,125 — Single non-inverting buffer (SOT-23-5)

SOURCE: model knowledge (Nexperia 74LVC1G34, common single-gate logic buffer). PDF not
downloaded this session (deferred). Pin table below is read directly from the installed
KiCad symbol `74xGxx:74LVC1G34`, confirmed present in
`/usr/share/kicad/symbols/74xGxx.kicad_sym`.

| Spec | Value |
|------|-------|
| Package | SOT-23-5 |
| Function | Single buffer/driver, non-inverting |
| Supply (VCC) | 1.65 V–5.5 V (LVC family, wide range) — this design runs it at 3.3 V |
| Propagation delay | Low-ns class (typical LVC family, ~3–5 ns) |
| Output drive | Standard LVC-family push-pull |

## Pinout (from KiCad symbol `74xGxx:74LVC1G34`)

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 1 | NC | free | No internal connection |
| 2 | A | input | Buffer input |
| 3 | GND | power in | Ground |
| 4 | Y | output | Buffer output |
| 5 | VCC | power in | Supply, 3.3 V |

(The symbol reports pins 2 and 4 generically as `~`/input and `~`/output — mapped here to
the datasheet's actual A/Y naming for this single-buffer part.)

## Notes

- U16, U17 in `clock_gen`: each buffers the terminated XO clock (via R10) out to one
  ADC channel's CLK line, each with its own 33 Ω series termination (R11, R12).
- Decoupling: shares C22/C23 (100 nF) group with X1.
- Pin 1 (NC) — leave unconnected; it has no internal bond in this single-gate SOT-23-5
  package (present only for PCB-footprint commonality with other SOT-23-5 logic parts).
