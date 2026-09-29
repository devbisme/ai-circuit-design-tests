"""Aux I/O — probe-compensation output, protected external trigger, status LEDs.
Block from: architecture/block_diagram.md
Interface nets: v3v3_d, gnd, probe_comp_drv, ext_trig, led_status, led_activity
"""
from skidl import *


@subcircuit
def aux_io(v3v3_d, gnd, probe_comp_drv, ext_trig, led_status, led_activity):
    """The board's front-panel furniture: probe comp, ext trigger, LEDs.

    PROBE COMPENSATION OUTPUT — this is not an afterthought, it is what makes
    the 10:1 attenuator usable. `afe_channel` presents 1 MOhm || ~20 pF so a
    standard passive scope probe can be compensated against it, and CV1/CV2
    trim the board side; this terminal supplies the square wave the user
    watches while doing it. The FPGA drives ~1 kHz at 3.3 V CMOS and R90/R91
    divide it to the conventional ~1 V amplitude:

        Vout = 3.30 V * 1.00 k / (2.32 k + 1.00 k) = 0.994 V p-p
        Zout = 2.32 k || 1.00 k = 699 Ohm

    A 1 % divider, not 0.1 %: this is a visual aid for adjusting a trimmer by
    eye, so amplitude accuracy is irrelevant. The 699 Ohm source impedance is
    what matters — it must stay well below the 1 MOhm probe load (so the probe
    does not drag the amplitude down) while staying high enough that a
    short to ground cannot overload an FPGA pin: 3.3 V / 2.32 k = 1.4 mA.

    EXTERNAL TRIGGER — bidirectional and therefore the most exposed pin on the
    board. It goes to a through-hole header a user will connect to arbitrary
    equipment, and it faces an FPGA pin with a 3.3 V absolute maximum, so it
    carries three independent protections:
      * R92 100 R in series      — limits fault current into the clamps to
                                   about (V_fault - 3.3 V) / 100 R and damps
                                   ringing on an unterminated flying lead
      * D10 BAT54S series pair   — Schottky clamp to V3V3_D and GND. Schottky
                                   because its ~0.3 V forward voltage clamps
                                   below the FPGA's 3.3 V + 0.5 V limit, which
                                   a silicon diode's 0.7 V would not reliably do
      * D11 PESD3V3L1BA          — the fast ESD path; the BAT54S handles
                                   sustained overvoltage, the TVS handles the
                                   nanosecond-scale strike that gets past it
    R93 10 k pulls the line DOWN so an open input reads a defined low and the
    trigger cannot free-run on noise when nothing is plugged in.

    Args:
        v3v3_d: 3.30 V digital rail (LED anodes, trigger clamp high rail).
        gnd: Ground.
        probe_comp_drv: ~1 kHz square wave from the FPGA, 3.3 V CMOS.
        ext_trig: Bidirectional trigger, FPGA I/O side of R92.
        led_status: FPGA -> green LED, active HIGH.
        led_activity: FPGA -> amber LED, active HIGH.
    """

    # Internal nets: the protected/attenuated terminal side of each network.
    probe_comp_out = Net("probeCompOut")
    ext_trig_pin = Net("extTrigPin")

    # ==================================================================
    # Probe compensation divider and terminal (net_plan.md §3.12)
    # ==================================================================
    r90 = Part("Device", "R", ref="R90", value="2.32k 1%",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r90[1] += probe_comp_drv
    r90[2] += probe_comp_out

    r91 = Part("Device", "R", ref="R91", value="1.00k 1%",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r91[1] += probe_comp_out
    r91[2] += gnd

    # J4 — 2-pin through-hole terminal: signal and ground, so a probe tip and
    # its ground clip both have something to grab (SPEC §5 permits TH here).
    j4 = Part("Connector_Generic", "Conn_01x02", ref="J4",
              value="Probe comp",
              footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical")
    j4[1] += probe_comp_out
    j4[2] += gnd

    # ==================================================================
    # External trigger — see the docstring for why each part is here
    # ==================================================================
    r92 = Part("Device", "R", ref="R92", value="100R",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r92[1] += ext_trig
    r92[2] += ext_trig_pin

    # BAT54S: series Schottky pair, pin 1 = free anode, pin 2 = free cathode,
    # pin 3 = common mid-node. Common -> the protected pin; the free cathode
    # clamps to V3V3_D (conducts when the pin rises above the rail), the free
    # anode to GND (conducts when the pin goes below ground).
    d10 = Part("Diode", "BAT54S", ref="D10", value="BAT54S",
               footprint="Package_TO_SOT_SMD:SOT-23")
    d10[3] += ext_trig_pin
    d10[2] += v3v3_d       # K -> positive clamp
    d10[1] += gnd          # A -> negative clamp

    d11 = Part("Device", "D_TVS", ref="D11", value="PESD3V3L1BA",
               footprint="Diode_SMD:D_SOD-323")
    d11[1] += ext_trig_pin
    d11[2] += gnd

    r93 = Part("Device", "R", ref="R93", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r93[1] += ext_trig_pin
    r93[2] += gnd

    # J5 — 1x3 TH header, signal plus TWO grounds. The second ground is not a
    # typo: it lets a coax pigtail or a scope ground clip land on either side
    # of the signal pin whichever way the header is approached.
    j5 = Part("Connector_Generic", "Conn_01x03", ref="J5",
              value="Ext trig",
              footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical")
    j5[1] += ext_trig_pin
    j5[2] += gnd
    j5[3] += gnd

    # ==================================================================
    # Status LEDs — driven HIGH from the FPGA, sinking to ground.
    # 1 k at 3.3 V gives (3.3 - 2.0)/1k ~ 1.3 mA green and (3.3 - 2.1)/1k
    # ~ 1.2 mA amber: dim by LED standards and deliberately so. Modern
    # 0603 LEDs are plainly visible at ~1 mA, and every milliamp here comes
    # out of the 500 mA USB budget that the analog rails also draw from.
    # ==================================================================
    r94 = Part("Device", "R", ref="R94", value="1k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r94[1] += led_status
    d12 = Part("Device", "LED", ref="D12", value="green",
               footprint="LED_SMD:LED_0603_1608Metric")
    d12["A"] += r94[2]
    d12["K"] += gnd

    r95 = Part("Device", "R", ref="R95", value="1k",
               footprint="Resistor_SMD:R_0402_1005Metric")
    r95[1] += led_activity
    d13 = Part("Device", "LED", ref="D13", value="amber",
               footprint="LED_SMD:LED_0603_1608Metric")
    d13["A"] += r95[2]
    d13["K"] += gnd
