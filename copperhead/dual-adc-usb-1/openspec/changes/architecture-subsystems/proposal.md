# Proposal: architecture-subsystems

> Marker: AUTO (autonomous mode; auto-approved, reviewable after the fact)

## Why

Stage 2 of the pipeline: turn the SPEC.md requirements and budgets into a subsystem architecture (docs/SUBSYSTEMS.md) that later part-selection and schematic stages can implement. The architecture must hold every SPEC §3 budget at once. The binding ones are power.vbus_current_mA <=450 mA, power.preconfig_current_mA <=100 mA, power.suspend_current_mA <=2.5 mA, power.vbus_capacitance_uF <=10 uF, clock.jitter_ps_rms <=5 ps, input.overvoltage_V +/-30 V with 1 MOhm || 20 pF preserved, and the anti-alias requirement of >=40 dB at 7.5 MHz.

## What Changes

- NEW docs/SUBSYSTEMS.md: block diagram in prose, then one section per subsystem, each with its reasoning and key values. Subsystems: USB-C connectivity, power tree and gating, USB bridge (FT232H + EEPROM), capture/control (FPGA; there is intentionally no MCU), buffer SDRAM, clocking, analog front end (x2), ADC, UI/indicators, config/programming, calibration storage.
- Power architecture: an always-on 3V3_AON LDO from VBUS feeds only the FT232H and its EEPROM. Everything else sits behind a soft-start load switch enabled by FT232H PWREN# (asserted after configuration, deasserted in suspend). Behind the switch: a 3V3_D buck, 1V2 core and 1V8 ADC LDOs, a clock LDO, and a +/-6 V boost/inverter with +/-5 V analog LDOs that the FPGA enables (AFE_EN) after the digital rails are up.
- Per-rail current budget at VBUS=4.4 V: about 345 mA steady state (<=450 mA), about 61 mA before configuration (<=100 mA), <=1.75 mA allocated in suspend (<=2.5 mA). VBUS capacitance is <=10 uF, with downstream bulk <=100 uF behind a >=3 ms soft start.
- A bus switch (CBT class) isolates the FT232H FIFO lines from the FPGA while the gated rails are off. This prevents back-powering the FPGA through the FT232H outputs during the pre-configuration and suspend states.
- ADC clock comes from a low-jitter XO through a fanout buffer straight to the ADC, never through the FPGA. The jitter allocation RSS is about 1.6 ps, against the <=5 ps budget.
- Front end per channel: BNC, then a compensated 1 MOhm /5 divider (which also sets the ~20 pF input capacitance), then low-leakage clamps at the divider tap (to survive +/-30 V), then a JFET-input buffer, then an FDA (gain ~0.5, single-ended to differential), then a 5th-order passive LC anti-alias filter, then the ADC (2 Vpp full scale, about 5 % over-range headroom).
- Calibration constants go in the FT232H 93LC56 EEPROM user area. The FT232H EEPROM declares bus-powered operation with MaxPower = 450 mA.
- Append decisions to docs/DECISIONS.md, add a changelog entry to docs/CHANGELOG.md, and update SPEC.md §6 open items to point at SUBSYSTEMS.md. Add the new derived constraints to .copperhead/constraints.json.
