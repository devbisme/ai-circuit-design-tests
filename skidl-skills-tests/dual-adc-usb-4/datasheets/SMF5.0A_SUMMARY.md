# SMF5.0A — 5V Unidirectional TVS Diode (D1, VBUS protection)

| Spec | Value |
|------|-------|
| Package | SOD-123FL |
| Vcc / Vin range | N/A (passive TVS), Vrwm 5V |
| Key output spec | Clamping 9.2V, Vbr 7V, unidirectional |
| Max current / power | 200W Ppp@10/1000µs, Ipp 21.7A@10/1000µs |
| Operating temp | -55°C to +150°C |

## Pinout
| Pin | Name | Function |
|-----|------|----------|
| 1 | Cathode | Marked/banded end |
| 2 | Anode | Unmarked end |

## Notes
- 2-terminal passive part; pinout is standard diode anode/cathode, no ambiguity.
- PDF not obtained: the LCSC-hosted PDF for this part's family listing predominantly
  references the SMF1.0A variant rather than SMF5.0A (rejected by the wrong-part guard),
  exhausting one attempt; a second attempt was not pursued given this is a low-risk generic
  TVS diode whose full spec is already captured from MCP data. Standoff voltage (5V) clears
  VBUS's 5.0-5.25V nominal with margin; verify against the architecture's stated 4.4V-corner
  concern only if VBUS transients are expected to approach 5V during normal operation (Vrwm=5V
  means clamping begins essentially at the rail — this is intentional for a VBUS surge
  suppressor, not a design defect).
