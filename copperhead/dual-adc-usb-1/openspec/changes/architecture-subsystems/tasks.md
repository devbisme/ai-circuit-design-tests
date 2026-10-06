# Tasks

- [ ] Write docs/SUBSYSTEMS.md with the block diagram, the per-subsystem sections, and the power/current tables for steady state, pre-configuration and suspend.
- [ ] Verify the current arithmetic against power.vbus_current_mA, power.preconfig_current_mA and power.suspend_current_mA, and the capacitance against power.vbus_capacitance_uF.
- [ ] Verify the jitter allocation against clock.jitter_ps_rms, the gain chain against input.voltage_range_V, and the clamp currents against input.overvoltage_V.
- [ ] Append the architecture decisions to docs/DECISIONS.md.
- [ ] Add the derived constraints (rail allocations, AON suspend allocation, I/O count) to .copperhead/constraints.json.
- [ ] Update SPEC.md §6 and docs/CHANGELOG.md.
- [ ] Run check_drift and finish. ERC is not applicable because there is no schematic yet.
