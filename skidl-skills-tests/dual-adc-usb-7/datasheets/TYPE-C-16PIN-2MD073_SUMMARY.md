# TYPE-C 16PIN 2MD(073) — USB-C receptacle (usb_bridge, J4)

| Spec | Value |
|------|-------|
| Package | SMD, right-angle, 16-pin |
| Key spec | 3A current rating, 5V, 10k cycle connect/disconnect life |
| Operating temp | −25°C to +85°C |

## Notes on footprint verification (sourcing flagged this as unverified)
Sourcing assigned `Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` and
flagged it as the closest 16-pin horizontal match, not dimensionally confirmed. **The downloaded
datasheet (`TYPE-C-16PIN-2MD073.pdf`) is also largely graphical** — pdftotext recovered only
solder-process notes (dip depth/temperature), not the pad-spacing table. **Carried forward: the
coder/reviewer should visually confirm pad positions in `datasheets/TYPE-C-16PIN-2MD073.pdf`
against the GCT USB4105 footprint before layout.** 16-pin USB-C receptacles (with dual CC) are
reasonably standardized industry-wide, so risk is low-to-moderate, not zero.
- Confirmed 16-pin body (not 6-pin, which would lack the second CC) — sourcing's `[PKG]` note.
