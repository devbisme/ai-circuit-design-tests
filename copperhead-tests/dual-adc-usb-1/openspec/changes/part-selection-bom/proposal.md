# Proposal: part-selection-bom

> Marker: AUTO (autonomous mode; auto-approved, reviewable after the fact)

## Why

Stage 3: commit concrete parts with installed KiCad symbols. The architecture candidates AD9238 and 93LC56 have no installed symbol, so substitutes are needed. Rail and part changes forced by the substitutes must be checked against power.vbus_current_mA, power.preconfig_current_mA, power.suspend_current_mA (AON allocation 1.75 mA), power.vbus_capacitance_uF, clock.jitter_ps_rms and analog.dc_accuracy.

## What Changes

- New docs/BOM.md: one row per refdes; Value = bare value; rationale, Iq/leakage check and UNVERIFIED MPN flags in the Rationale column
- ADC: LTC2290 (dual 12-bit 10 MSPS, symbol Analog_ADC:LTC2290xUP) replaces the AD9238-class candidate. It runs on 3.3 V VDD/OVDD, so the 1V8_A and 1V8_D rails are removed: 3V3_ADC (low-noise LDO) feeds VDD, 3V3_D feeds OVDD, and the FPGA ADC bank runs at 3.3 V
- EEPROM: 93LC56B on symbol Memory_EEPROM:93LCxxB
- Bus switch: 2x 74CBTLV3861 (10-bit each, 20 bits for 15 FIFO signals); no installed 16-bit CBT symbol
- Load switch TPS22917 (active-high ON) driven through a BSS138-class N-FET inverter from PWREN_N
- +/-6 V from TPS65131
- FLAG: LTC2290 datasheet offset is expected in the mV class, above the 0.9 mV allocation (analog.dc_accuracy AT RISK becomes a likely violation). Not silently accepted; needs a user decision
