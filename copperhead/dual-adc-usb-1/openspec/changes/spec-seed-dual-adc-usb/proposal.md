# Proposal: spec-seed-dual-adc-usb

> Marker: AUTO (autonomous mode; auto-approved, reviewable after the fact)

## Why

Create pipeline stage 1: seed docs/SPEC.md for a dual-channel ±10 V, 12-bit, 10 MSPS USB-powered ADC board from the product brief. Derive budgets (data rate, buffer depth, USB power/throughput, clock jitter) and flag every unstated item as ASSUMED so later stages have a single source of truth.

## What Changes

- Add docs/SPEC.md: device description, functional requirements, interface requirements (BNC scope-lead inputs, USB 2.0 HS host link + bus power), derived budgets (40 MB/s raw data, >=4 MB capture buffer, <=2.25 W / 450 mA VBUS draw, <=100 mA pre-configuration, <=2.5 mA suspend, <=10 uF VBUS capacitance, <=5 ps rms clock jitter), decision options with recommendations (connector, capture vs streaming, buffer memory, USB bridge, USB connector type), ASSUMED defaults (input impedance, bandwidth, protection, coupling, environment, board size).
- No openspec/ workspace exists, so openspec/specs/ is not seeded.
- No schematic/board changes.
