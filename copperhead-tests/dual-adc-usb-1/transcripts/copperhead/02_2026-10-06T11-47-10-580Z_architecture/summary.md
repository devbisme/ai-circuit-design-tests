# Run summary

- **Request:** create pipeline stage: architecture
- **Outcome:** success
- **OpenSpec change:** architecture-subsystems
- **Tokens:** 34 in / 66431 out

## Environment

- **Run:** 2026-10-06T11-47-10-580Z · create · started 2026-10-06T11:47:10.599Z · autonomous
- **Stage:** architecture (2/8)
- **Brief:** dual-adc-prompt.txt (sha256 6fda2f5a66e9…)
- **Model:** claude-code (claude-code, via env)
- **copperhead:** v0.11.0 at /home/devb/.nvm/versions/node/v22.23.3/lib/node_modules/copperhead
- **Tooling:** kicad-cli 9.0.9 · node v22.23.3 · linux-x64
- **Config:** schematic null · board null · docs docs/ · maxTurns 40 · maxRepairCycles 5 · budgets {}
- **Repo:** master@6fbce13928dec5c1afeb8989c11f258c923447c9 · dirty (1 uncommitted) · pre-commit hook absent
- **Memory:** 18 open constraint(s) · 1 prior run(s)

## Run stats

- **Exit path:** done
- **Turns:** 17 / 40
- **Repair cycles:** 0 / 5
- **Tokens:** 34 in / 66.4k out
- **Duration:** 11m36s
- **Per turn:** 1: 2/15913 · 2: 2/172 · 3: 2/37132 · 4: 2/2464 · 5: 2/1250 · 6: 2/829 · 7: 2/860 · 8: 2/858 · 9: 2/882 · 10: 2/773 · 11: 2/616 · 12: 2/625 · 13: 2/903 · 14: 2/983 · 15: 2/1252 · 16: 2/157 · 17: 2/762

## Plan

The SUBSYSTEMS.md arithmetic checks out:
- Steady state is 342 mA.
- Suspend is 1.59 mA.
- Jitter RSS is 1.53 ps.
- Offset sums to 19.2 mV.
- C_in is 20 pF.

One error: §7.2 says "the same ≈37 µA" when the rails are off. With the rails off, the tap clamps at about 0.6 V, not 5.6 V, so the current really is different: (30 − 0.6) V / 800 kΩ ≈ 37 µA. I'll fix the wording.

## Files touched

- docs/SUBSYSTEMS.md
- docs/SPEC.md
- docs/CHANGELOG.md
- docs/DECISIONS.md

## Verification

- ERC: not run
- DRC: not run
- legibility: not run
- score: not run

## Decisions

- Power architecture: two domains. (1) An always-on 3V3_AON LDO from VBUS (Iq <=50 uA) feeds only the FT232H, its 93LC56 EEPROM and the FIFO bus-switch VCC. (2) Everything else sits behind a soft-start load switch (rise >=3 ms, off-leakage <=1 uA) producing VBUS_SW, enabled by FT232H PWREN_N (default off via pull-up). Behind VBUS_SW: a 3V3_D buck, the 1V2_FPGA/1V8_A/1V8_D LDOs, a 3V3_CLK low-noise LDO, and a +/-6 V boost/inverter with +/-5V_A LDOs that the FPGA enables via AFE_EN. Options considered: (a) single always-on tree, (b) gated tree via PWREN_N, (c) MCU-managed gating. | why: Gating everything except the bridge behind PWREN_N is what makes ~61 mA pre-configuration (<=100 mA), <=1.6 mA suspend (<=2.5 mA) and <=9 uF ungated capacitance (<=10 uF) achievable, while steady state stays ~342 mA at 4.4 V (<=450 mA) with 24 % margin.
- Clocking: a 10.000 MHz low-jitter XO on a dedicated 3V3_CLK low-noise LDO drives a 1:2 fanout buffer. Output A goes point-to-point to the ADC clock pin; output B goes to an FPGA global clock pin, and the FPGA PLL derives 100 MHz for SDRAM and logic. The ADC clock never passes through FPGA fabric or the PLL. Jitter allocation: XO <=1.0, fanout <=0.3, ADC aperture <=0.5, routing/supply <=1.0 ps rms, giving ~1.53 ps RSS. Options considered: (a) ADC clock from the FPGA PLL, (b) XO direct to the ADC with the FPGA clocked from the ADC DCO, (c) XO + fanout to both. | why: FPGA PLL jitter is tens of ps, far above the <=5 ps budget. The fanout keeps the ADC clock clean while giving the FPGA a synchronous reference, and leaves ~3.4 ps of margin.
- Analog front end (x2): BNC, then a compensated 1 MOhm /5 divider (800k||25p over 200k||~100p, 0.1 %), then low-leakage clamp diodes (BAV199-class) at the divider tap to +/-5V_A, then a 1 kOhm series resistor, then a FET-input buffer (G=+1, OPA810-class), then an FDA (G=0.475, VOCM from ADC VCM, THS4551-class), then a 5th-order differential elliptic LC anti-alias filter, then the ADC (2 Vpp diff). Nominal +/-10 V uses 95 % of full scale (+/-10.53 V FS). No TVS at the BNC (intentional; DNP footprint only). Options considered: (a) /5 divider + buffer + FDA, (b) unity-gain buffer from a high-voltage op amp on +/-12 V rails, (c) programmable-gain front end. | why: The divider brings +/-10 V into +/-5 V-rail op amps with no high-voltage rails, sets 1 MOhm || 20 pF directly, and limits a +/-30 V fault to ~31-37 uA. An elliptic filter is the only 5th-order response that keeps >=40 dB at 7.5 MHz under component tolerance; Butterworth (~33 dB) fails.
- Back-powering protection: a CBT-class bus switch (>=15 bits, VCC on 3V3_AON) sits between the FT232H FIFO (D0-7, RXF#, TXE#, RD#, WR#, OE#, SIWU#, CLKOUT) and the FPGA. BUS_OE_N is pulled up to 3V3_AON, so the switch defaults to disabled, and an N-FET driven from PG_3V3D pulls it low once the gated digital rail is good. Options considered: (a) direct connection, (b) series resistors only, (c) CBT bus switch, (d) powering the FPGA I/O banks from the always-on rail. | why: The FT232H stays powered while the FPGA is off. A direct connection would back-feed the FPGA through its I/O clamp diodes, which breaks power.preconfig_current_mA and power.suspend_current_mA and risks latch-up. A CBT switch adds only ~0.25 ns, which is negligible at 60 MHz, and draws <=20 uA when disabled.
- Calibration storage and control: per-channel gain/offset constants (4 x 32-bit + CRC) go in the FT232H 93LC56 EEPROM user area (93LC66 if it is too small). There is intentionally no MCU; the FPGA (iCE40HX4K-TQ144 candidate, >=95 user I/O, one 1.8 V bank) does all capture and control and boots from SPI flash on 3V3_D, programmed through a 2x5 header. FT232H MPSSE is not used for flash programming. Options considered: (a) separate I2C/SPI EEPROM, (b) FPGA config-flash sector, (c) FT232H EEPROM user area. | why: The FT232H EEPROM is already on the always-on rail, so the host can read the constants via D2XX before the FPGA is powered, with no extra part and no added suspend load. The ADBUS pins are the FIFO bus, so MPSSE flash programming would load the FIFO lines.
- [affects] power.aon_suspend_allocation_mA affects USB bridge selection: no change needed: FT232H stays the bridge (SPEC §4.6). Its suspend current is allocated <=1.2 mA in SUBSYSTEMS.md §2.4 and is listed as a VERIFY item for part selection in SPEC §6.
- [affects] power.aon_suspend_allocation_mA affects 3V3_AON LDO selection: changed: SUBSYSTEMS.md §2.1/§2.4 now specify the 3V3_AON LDO selection limits as Iq <=50 uA (allocated <=0.1 mA), >=61 mA output and VBUS 4.4-5.25 V input. No part chosen yet (part-selection stage).
- [affects] power.aon_suspend_allocation_mA affects bus switch selection: changed: SUBSYSTEMS.md §2.7 now specifies a CBT-class bus switch, >=15 bits, VCC on 3V3_AON, ICC <=20 uA disabled, default-disabled via BUS_OE_N pull-up. Part chosen in part-selection stage.
- [affects] power.aon_suspend_allocation_mA affects input power path / load switch: changed: SUBSYSTEMS.md §2.1/§2.5 now specify the load switch as PWREN_N-enabled, default off, rise >=3 ms, off-state leakage <=1 uA (allocated <=0.01 mA with converter leakage), <=100 uF downstream bulk.
- [affects] power.rail_allocation_mA affects ADC selection: changed: SUBSYSTEMS.md §8 now gives the ADC selection limits. AVDD (1V8_A) <=60 mA and DRVDD (1V8_D) <=15 mA at 10 MSPS with both channels, plus SINAD, offset, gain and jitter limits. If a 3 V ADC is chosen, the 3V3_D load must be re-derived. No part chosen yet (part-selection stage).
- [affects] power.rail_allocation_mA affects FPGA selection: changed: SUBSYSTEMS.md §4 now gives the FPGA selection limits. 1V2_FPGA core <=30 mA, 3.3 V I/O <=25 mA, >=95 user I/O, one 1.8 V bank. iCE40HX4K-TQ144 is a candidate only.
- [affects] power.rail_allocation_mA affects buffer memory selection: changed: SUBSYSTEMS.md §5 now allocates the 256 Mbit x16 3.3 V SDR SDRAM <=70 mA average on 3V3_D. The SDRAM is unpowered before configuration and in suspend.
- [affects] power.rail_allocation_mA affects front-end op amp selection: changed: SUBSYSTEMS.md §7.3/§7.4 now cap the buffer at Iq <=4 mA and the FDA at Iq <=3 mA per channel, within +5V_A 20 mA and -5V_A 15 mA.
- [affects] power.rail_allocation_mA affects bipolar rail generation: changed: SUBSYSTEMS.md §2.1 now specifies a +/-6 V boost/inverter (eta >=75 %, f_sw >=1 MHz, AFE_EN-enabled, SYNC preferred) followed by +/-5V_A LDOs. It is allocated 66 mA at VBUS.
- [affects] power.rail_allocation_mA affects digital rail regulators: changed: SUBSYSTEMS.md §2.1 now specifies the digital rails. 3V3_D buck: eta >=88 %, 205 mA. 1V2_FPGA, 1V8_A (PSRR >=40 dB at f_sw) and 1V8_D LDOs from 3V3_D. 3V3_CLK low-noise LDO (<=10 uV rms). 3V3_AON LDO Iq <=50 uA. All must operate from VBUS_SW down to 4.3 V.
- [affects] power.rail_allocation_mA affects USB bridge selection: no change needed: the FT232H stays the bridge. Its max operating current is allocated <=60 mA on 3V3_AON (§2.3), and this is listed as a VERIFY item in SPEC §6.
