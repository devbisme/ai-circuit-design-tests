# PESD5V0S1BA — Bidirectional ESD/TVS protection diode (SOD-323)

SOURCE: Nexperia PESD5V0S1BA/BB/BL datasheet, facts confirmed via WebSearch (breakdown/
clamping specs quoted from distributor listings citing the datasheet). PDF not
downloaded this session (low incremental value for a 2-pin passive TVS — deferred).

| Spec | Value |
|------|-------|
| Package | SOD-323, 2-pin |
| Type | Single-element, bidirectional TVS |
| Reverse standoff voltage (V_RWM) | 5.0 V |
| Breakdown voltage | 5.5 V – 9.5 V |
| Max clamping voltage (V_C) | 14 V |
| Peak pulse current | 12 A |
| Peak pulse power | 130 W |
| ESD rating | > 30 kV (contact/air, per datasheet marketing spec) |

## Pinout (from KiCad symbol `Device:D_TVS`)

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 1 | A1 | passive | Terminal 1 |
| 2 | A2 | passive | Terminal 2 |

Bidirectional device — no polarity marking required for placement; both terminals behave
symmetrically (A1/A2 naming is the generic KiCad symbol's convention, not anode/cathode).

## Notes

- D2 in `usb_c_input`: placed across VBUS-to-GND, post-fuse (F1), pre-regulator (U1), for
  transient/ESD suppression on the incoming USB VBUS rail.
- **Deviation carried from sourcing:** architect's alternate `SMAJ6.0A` is a DO-214AC
  (SMA) package — physically incompatible with the stated SOD-323 footprint. This part
  (PESD5V0S1BA) is the SOD-323-correct choice; do not substitute SMAJ6.0A without also
  changing the footprint.
- No decoupling/external components needed — passive shunt device.
