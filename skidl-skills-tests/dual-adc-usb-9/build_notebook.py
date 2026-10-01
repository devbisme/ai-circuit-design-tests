"""Build dual_adc_usb.ipynb from the design docs' numbers and the block .py files.

Block cells are copied from circuits/dual_adc_usb/*.py at build time (the .py files stay
the source of truth); rerun this script after any block change.
"""
import re
import sys
from pathlib import Path

import nbformat as nbf

PROJ = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent).resolve()
BLK = PROJ / 'circuits' / 'dual_adc_usb'
OUT = PROJ / 'dual_adc_usb.ipynb'

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip('\n')))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip('\n')))


def block_source(name):
    """Block file text minus its package imports (skidl is imported once in the setup cell;
    the AFE helper is defined in its own cell before the AFE blocks)."""
    src = (BLK / f'{name}.py').read_text()
    new = re.sub(r'^from (skidl|\._afe_common) import .*\n', '', src, flags=re.M)
    assert new != src, f'{name}.py: no import line removed'
    return new.strip('\n')


def main_source():
    """__main__.py adapted for a notebook: no relative imports, no __file__, no __main__ guard."""
    src = (BLK / '__main__.py').read_text()
    head, sep, tail = src.partition('# ---- Power nets')
    assert sep, '__main__.py: power-net marker not found'
    body, sep, rest = (sep + tail).partition('\n\ndef _stabilize_tags')
    assert sep, '__main__.py: _stabilize_tags not found'
    stab = 'def _stabilize_tags' + rest.split("\n\nif __name__ == '__main__':")[0]
    return body.strip('\n'), stab.strip('\n')


# =====================================================================================
md(r"""
# dual_adc_usb — two-channel 12-bit, 10 MSa/s USB digitizer

This notebook walks through the design phase by phase: requirements, architecture, component
calculations, sourcing, the SKiDL code for each block, and the top-level assembly with ERC.

**Sources.** Numbers and decisions come from the pipeline documents in this directory:
`SPEC.md`, `architecture/*.md`, `sourcing/sourced_bom.csv`, `datasheets/*_SUMMARY.md` and
`handoffs/*.md`. The block code cells are copies of `circuits/dual_adc_usb/*.py` made when the
notebook was generated. **The `.py` files are the source of truth**; if they change, regenerate
the notebook with `python build_notebook.py` rather than editing the cells here.

**Running.** Start Jupyter from the project root (the directory holding `SPEC.md`). The last
section runs ERC over the whole circuit; it needs SKiDL, the KiCad 9 symbol libraries, and the
project-local symbol library in `symbols/`.
""")

code(r"""
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import graphviz
from scipy.optimize import brentq

from skidl import *

PROJ = Path.cwd()
assert (PROJ / 'SPEC.md').exists(), 'start the notebook from the project root'

# Project-local symbol library (ADS5231, GW1NR-9, TPS22918) and footprint library (BNC).
if str(PROJ / 'symbols') not in lib_search_paths[KICAD]:
    lib_search_paths[KICAD].append(str(PROJ / 'symbols'))
if str(PROJ / 'footprints') not in footprint_search_paths[KICAD]:
    footprint_search_paths[KICAD].append(str(PROJ / 'footprints'))

# Each block file has private helpers (_r, _c, _R, ...) whose names collide across files.
# `%%block <name> [exports...]` runs a cell in its own namespace, as if it were its module,
# and exports only the block function (or the listed names) to the notebook.
from IPython.core.magic import register_cell_magic

@register_cell_magic
def block(line, cell):
    name, *exports = line.split()
    ns = {'__name__': name}
    exec('from skidl import *', ns)
    if 'build_afe_channel' in globals():
        ns['build_afe_channel'] = build_afe_channel
    exec(cell, ns)
    for e in exports or [name]:
        globals()[e] = ns[e]

# Engineering-notation helper for printed results.
def eng(x, unit='', digits=4):
    if x == 0:
        return f'0 {unit}'
    exp = int(np.floor(np.log10(abs(x)) / 3) * 3)
    exp = max(min(exp, 12), -15)
    prefix = {-15: 'f', -12: 'p', -9: 'n', -6: 'µ', -3: 'm', 0: '', 3: 'k', 6: 'M', 9: 'G', 12: 'T'}[exp]
    return f'{x / 10**exp:.{digits}g} {prefix}{unit}'
""")

# =====================================================================================
md(r"""
## 1. Requirements

Condensed from `SPEC.md`. [HARD] items came from the user; [SOFT] items were chosen by the
pipeline driver and are open to revision.

| Item | Requirement | Kind |
|---|---|---|
| Channels | 2, simultaneously sampled | HARD |
| Input range | ±10 V at the connector | HARD |
| Sample rate / resolution | 10 MSa/s per channel, 12 bit | HARD |
| Capture depth | ≥ 0.1 s at full rate → ≥ 1 M samples/channel | HARD |
| Connectors | 2 × BNC (mate with scope leads); one USB port for power and data | HARD |
| Power | USB 2.0 bus-powered; use USB-C if the USB 2.0 budget (5 V, 500 mA) is insufficient | HARD |
| Input impedance | 1 MΩ ‖ ~15–25 pF (so 1×/10× probes compensate) | SOFT |
| Bandwidth | ≥ 5 MHz with anti-alias filtering, DC coupled | SOFT |
| Overvoltage | survive ±50 V continuous | SOFT |
| Build | SMD, 4-layer, JLCPCB assembly, 0–70 °C, prototype quantity | SOFT |
""")

# =====================================================================================
md(r"""
## 2. Architecture

Key decisions (`architecture/ic_selection.md`, `handoffs/02_architecture.md`, rev 2):

- **ADC: TI ADS5231**, dual 12-bit on one die, so both channels sample on the same clock edge.
  It needs ≥ 20 MSa/s with its PLL on, so it **oversamples at 40 MSa/s** and the FPGA
  **decimates ×4** to 10 MSa/s. Oversampling moves the first alias band out to 35 MHz, which is
  what makes an analog anti-alias filter practical (§3.4).
- **Front end** per channel: compensated 910 k / 100 k divider (1.01 MΩ ‖ ≈ 20 pF, ÷10.1) with a
  2–6 pF trimmer, BAV199 clamp to ±3.4 V rails, OPA810 FET-input unity buffer, THS4521
  fully-differential amplifier wired as a 2-pole multiple-feedback (MFB) low-pass, and a
  2 × 33 Ω / 270 pF output RC at the ADC pins (3rd pole).
- **Capture engine: Gowin GW1NR-9 (QN88P)** with 64 Mbit (8 MiB) PSRAM inside the package.
  Its bank 3 must run at 1.8 V for the PSRAM, so a third buck makes +1V8 (rev 2). Only 48 pins are
  3.3 V-capable; the ADC data-valid and over-range outputs and FT232H SIWU# were dropped to fit.
- **USB: FTDI FT232H** in synchronous-245 FIFO mode (≈ 35–40 MB/s, no firmware). Capture to
  PSRAM first, then upload — streaming 40 MB/s is at the edge of what USB 2.0 HS sustains.
  Runs in **VREGIN 5 V mode** (driver decision after the ERC gate, finding M1).
- **Power:** estimated at 1.5–1.8 W, under the 2.5 W USB 2.0 budget, so the USB-C rule did not
  fire; a USB-C receptacle (USB 2.0 wiring, 5.1 kΩ Rd) was chosen anyway. §3.7 recomputes the
  budget as built — the 5 V-mode change erodes the margin.

### 2.1 Signal flow: analog inputs → USB connector
""")

code(r"""
sig = graphviz.Digraph('signal_flow', graph_attr={'rankdir': 'LR', 'fontsize': '10', 'nodesep': '0.25', 'ranksep': '0.35'},
                       node_attr={'shape': 'box', 'style': 'rounded,filled', 'fillcolor': '#eef3fb', 'fontsize': '10'},
                       edge_attr={'fontsize': '9'})

for ch, bnc, u1, u2 in (('A', 'J2', 'U20', 'U21'), ('B', 'J3', 'U40', 'U41')):
    with sig.subgraph(name=f'cluster_afe_{ch}') as c:
        c.attr(label=f'afe_ch_{ch.lower()}', style='dashed', color='gray50')
        c.node(f'bnc{ch}', f'BNC {bnc}\n±10 V', fillcolor='#fff4d6')
        c.node(f'div{ch}', 'Compensated divider\n910k / 100k  (÷10.1)\n1.01 MΩ || 20 pF + trimmer')
        c.node(f'clp{ch}', 'BAV199 clamp\nto ±3.4 V')
        c.node(f'buf{ch}', f'OPA810 {u1}\nunity buffer')
        c.node(f'fda{ch}', f'THS4521 {u2}\n2-pole MFB, G = 0.909\nf0 8.84 MHz, Q 0.99\nSE → differential')
        c.node(f'rc2{ch}', 'RC 2×33 Ω / 270 pF\npole 8.9 MHz')
        c.edges([(f'bnc{ch}', f'div{ch}'), (f'div{ch}', f'clp{ch}'), (f'clp{ch}', f'buf{ch}'),
                 (f'buf{ch}', f'fda{ch}'), (f'fda{ch}', f'rc2{ch}')])

sig.node('xo', 'Y1 40 MHz XO\n0.7 ps rms', shape='ellipse', fillcolor='#f3eefb')
sig.node('buf', 'U8 LVC1G34\nclock buffer', shape='ellipse', fillcolor='#f3eefb')
sig.node('adc', 'ADS5231  U7\ndual 12-bit ADC\n40 MSa/s, simultaneous', fillcolor='#e3f4e3')
sig.node('fpga', 'GW1NR-9  U9\ndecimate ×4 → 10 MSa/s\n8 MiB in-package PSRAM\ntrigger, capture', fillcolor='#e3f4e3')
sig.node('ft', 'FT232H  U10\nsync-245 FIFO → USB 2.0 HS', fillcolor='#e3f4e3')
sig.node('esd', 'USBLC6-2SC6  U1\nESD')
sig.node('usb', 'USB-C  J1', fillcolor='#fff4d6')

sig.edge('rc2A', 'adc', label='AINA_P/N\n±0.90 V diff @ ±10 V')
sig.edge('rc2B', 'adc', label='AINB_P/N')
sig.edge('adc', 'fdaA', label='VCM 1.5 V', style='dotted', constraint='false')
sig.edge('adc', 'fdaB', label='VCM', style='dotted', constraint='false')
sig.edge('xo', 'adc', label='ADC_CLK (33 Ω)', style='dashed')
sig.edge('xo', 'buf', style='dashed')
sig.edge('buf', 'fpga', label='FPGA_CLK40 (33 Ω)', style='dashed')
sig.edge('adc', 'fpga', label='DA[11:0], DB[11:0]\n@ 40 MSa/s')
sig.edge('fpga', 'ft', label='FT_D[7:0] @ 60 MHz\n≈ 35–40 MB/s')
sig.edge('ft', 'esd', label='USB_DP/DM\n480 Mb/s')
sig.edge('esd', 'usb')
sig
""")

md(r"""
### 2.2 Power distribution: USB VBUS → derived rails → consumers

All rails come from switched VBUS (`VBUS_SW`). Digital loads get bucks; the analog chain gets
LDOs. The FT232H is powered from `VBUS_SW` through its own internal 3.3 V regulator (`FT_VCCD`);
only its VCCIO pins sit on `+3V3D`. This was changed after the ERC gate (finding M1) and
**differs from `architecture/net_plan.md`**, which still shows the FT232H on `+3V3D`.
""")

code(r"""
pwr = graphviz.Digraph('power_tree', graph_attr={'rankdir': 'LR', 'fontsize': '10', 'nodesep': '0.2', 'ranksep': '0.45'},
                       node_attr={'shape': 'box', 'style': 'rounded,filled', 'fontsize': '10'},
                       edge_attr={'fontsize': '9'})
reg = {'fillcolor': '#fde9d9'}
rail = {'shape': 'plaintext', 'style': '', 'fontcolor': '#aa3333'}
load = {'fillcolor': '#e3f4e3'}

pwr.node('J1', 'USB-C J1\nVBUS 4.40–5.25 V', fillcolor='#fff4d6')
pwr.node('F1', 'F1 0.75 A PTC\nD1 SMF5.0A TVS', **reg)
pwr.node('U2', 'TPS22918  U2\nsoft-start load switch', **reg)
pwr.node('VB', 'VBUS_SW', **rail)
pwr.edges([('J1', 'F1'), ('F1', 'U2'), ('U2', 'VB')])

# digital
for u, r, v in (('U3', 'V3V3D', '+3V3D 3.327 V\n(EN delayed 2–3 ms)'), ('U4', 'V1V2', '+1V2 1.200 V'), ('U12', 'V1V8', '+1V8 1.800 V')):
    pwr.node(u, f'TLV62569  {u}\nbuck', **reg)
    pwr.node(r, v, **rail)
    pwr.edges([('VB', u), (u, r)])
pwr.node('L_fpio', 'FPGA U9 VCCX, VCCO0–2\nADC U7 VDRV, Y1, U8\nFT232H VCCIO, LEDs', **load)
pwr.node('L_fcore', 'FPGA U9 core VCC', **load)
pwr.node('L_psram', 'FPGA U9 VCCO3\n(PSRAM bank), JTAG VREF', **load)
pwr.edges([('V3V3D', 'L_fpio'), ('V1V2', 'L_fcore'), ('V1V8', 'L_psram')])

# analog
pwr.node('U5', 'TLV75733P  U5\nLDO', **reg)
pwr.node('U6', 'LM27762  U6\ncharge pump +\n± LDOs', **reg)
pwr.node('V3V3A', '+3V3A 3.3 V', **rail)
pwr.node('VP', 'VAFE_P +3.360 V', **rail)
pwr.node('VN', 'VAFE_N −3.416 V', **rail)
pwr.edges([('VB', 'U5'), ('U5', 'V3V3A'), ('VB', 'U6'), ('U6', 'VP'), ('U6', 'VN')])
pwr.node('L_adc', 'ADS5231 U7 AVDD\nTHS4521 U21, U41', **load)
pwr.node('L_buf', 'OPA810 U20, U40\n+ BAV199 clamps', **load)
pwr.edges([('V3V3A', 'L_adc'), ('VP', 'L_buf'), ('VN', 'L_buf')])

# USB bridge
pwr.node('U10reg', 'FT232H U10\ninternal 3.3 V reg\n(VREGIN → VCCD)', **reg)
pwr.node('FTV', 'FT_VCCD', **rail)
pwr.node('L_phy', 'FT232H VPHY / VPLL\n93LC56 EEPROM', **load)
pwr.edges([('VB', 'U10reg'), ('U10reg', 'FTV'), ('FTV', 'L_phy')])
pwr
""")

# =====================================================================================
md(r"""
## 3. Component calculations

Each subsection recomputes the values in the architecture documents from the component values
used in the code, so the numbers can be checked and re-run if a part changes.

### 3.1 Signal scaling and full scale

The ADS5231 full-scale input is 2.02 Vpp differential (±1.01 V) around its 1.5 V common-mode
output. The gain from BNC to ADC pins is the divider ratio times the MFB gain R25/R23.
""")

code(r"""
R_T, R_B = 910e3, 100e3          # R20 / R21
R1, R2 = 1.1e3, 1.0e3            # MFB input / feedback resistors (R23, R25)
ADC_FS_DIFF = 1.01               # ADS5231 ±full scale, differential volts
N_BITS = 12

k_div = R_B / (R_T + R_B)
k_fda = R2 / R1
k_total = k_div * k_fda
fs_in = ADC_FS_DIFF / k_total
lsb_in = 2 * fs_in / 2**N_BITS

print(f'divider ratio        : {k_div:.5f}  (÷{1/k_div:.3f}),  R_in = {eng(R_T + R_B, "Ω")}')
print(f'FDA gain R2/R1       : {k_fda:.4f}')
print(f'total gain           : {k_total:.5f} V/V   (±10 V → ±{10*k_total:.3f} V diff)')
print(f'full scale at BNC    : ±{fs_in:.2f} V   (margin over ±10 V: {100*(fs_in/10-1):.1f} %)')
print(f'LSB referred to BNC  : {eng(lsb_in, "V")}')
print(f'buffer swing at FS   : ±{fs_in*k_div:.3f} V')
# Worst case: ADC gain error −3.5 %, resistor ratio −1 % (net_plan §3)
print(f'worst-case low FS    : ±{fs_in*(1-0.035)*(1-0.01):.2f} V  (must stay > 10 V)')

# THS4521 input common mode: Vx = VOUT × R1/(R1+R2), VOUT = VCM ± half the differential swing
for vout in (1.5 - 0.45, 1.5 + 0.45):
    print(f'FDA input CM at VOUT {vout:.2f} V : {vout*R1/(R1+R2):.3f} V  (THS4521 @3.3 V: −0.1 … 1.8 V)')
""")

md(r"""
### 3.2 Compensated input divider

A resistive divider loaded by capacitance is flat only when both legs have the same time
constant, `R_T·C_T = R_B·C_B`. That is also what lets a 10× probe (itself a 9 MΩ ‖ C divider) be
compensated against this input.

`C_B` is C22 (200 pF C0G ±5 %) plus the BAV199 (≈ 2 pF), the OPA810 input (≈ 2 pF, **assumed** —
not in its summary; it sits behind R22 = 1 kΩ, small against the ~90 kΩ node impedance) and
≈ 3 pF of board parasitics. `C_T` is C20 (18 pF ±5 %) in parallel with the C21 trimmer (2–6 pF).
""")

code(r"""
C_B_fixed, C_B_tol = 200e-12, 0.05     # C22
C_diode, C_buf, C_par = 2e-12, 2e-12, 3e-12
C_T_fixed, C_T_tol = 18e-12, 0.05      # C20
TRIM_MIN, TRIM_MAX = 2e-12, 6e-12      # C21 STC3MA06

def c_t_needed(c_b):
    return R_B * c_b / R_T

c_b_nom = C_B_fixed + C_diode + C_buf + C_par
lo = c_t_needed(C_B_fixed * (1 - C_B_tol) + C_diode + C_buf + C_par - 2e-12)
hi = c_t_needed(C_B_fixed * (1 + C_B_tol) + C_diode + C_buf + C_par + 2e-12)
avail_lo = C_T_fixed * (1 - C_T_tol) + TRIM_MIN
avail_hi = C_T_fixed * (1 + C_T_tol) + TRIM_MAX
print(f'C_B nominal           : {eng(c_b_nom, "F")}')
print(f'C_T needed            : {eng(c_t_needed(c_b_nom), "F")} nominal, {eng(lo, "F")} … {eng(hi, "F")} worst case')
print(f'C20 + C21 available   : {eng(avail_lo, "F")} … {eng(avail_hi, "F")}')
print(f'headroom              : low {eng(lo - avail_lo, "F")}, high {eng(avail_hi - hi, "F")}')

c_t = c_t_needed(c_b_nom)
print(f'input impedance       : {eng(R_T + R_B, "Ω")} ‖ {eng(c_t * c_b_nom / (c_t + c_b_nom), "F")}  (+ BNC/trace ≈ 2 pF)')
print(f'tilt corner if uncompensated: {eng(1 / (2*np.pi * (R_T*R_B/(R_T+R_B)) * (c_t + c_b_nom)), "Hz")}')
""")

md(r"""
Step response of the divider (what you see when adjusting the trimmer with a 1 kHz square wave).
The edge ratio is `C_T/(C_T+C_B)`, the settled ratio is `R_B/(R_T+R_B)`, and the transition
between them has time constant `(R_T‖R_B)(C_T+C_B)`.
""")

code(r"""
t = np.linspace(0, 150e-6, 600)
fig, ax = plt.subplots(figsize=(7, 3.2))
for trim, lbl in ((TRIM_MIN, 'trimmer 2 pF (under-compensated)'),
                  (c_t - C_T_fixed, f'trimmer {(c_t - C_T_fixed)*1e12:.1f} pF (flat)'),
                  (TRIM_MAX, 'trimmer 6 pF (over-compensated)')):
    C_T = C_T_fixed + trim
    v0 = C_T / (C_T + c_b_nom)
    tau = (R_T * R_B / (R_T + R_B)) * (C_T + c_b_nom)
    v = k_div + (v0 - k_div) * np.exp(-t / tau)
    ax.plot(t * 1e6, v / k_div, label=lbl)
ax.set_xlabel('time after 1 kHz square-wave edge (µs)')
ax.set_ylabel('output / ideal')
ax.set_title('Compensated divider step response')
ax.grid(alpha=0.3); ax.legend(fontsize=8)
plt.tight_layout(); plt.show()
""")

md(r"""
### 3.3 Overvoltage protection (±50 V)

The BAV199 dual diode clamps the divider node to the ±3.4 V buffer rails. The divider already
divides by 10, so the fault current is limited by R20 (910 kΩ), not by a series resistor.
""")

code(r"""
V_fault = 50.0
VP_AFE, VN_AFE = 3.360, -3.416
V_F = 0.6

print(f'divider node at ±50 V : ±{V_fault * k_div:.2f} V (unclamped)')
print(f'clamp window          : {VN_AFE - V_F:.2f} … {VP_AFE + V_F:.2f} V')
i_f = (V_fault - VP_AFE - V_F) / R_T
print(f'fault current         : {eng(i_f, "A")} into the clamp / VAFE_P rail')
print(f'R20 dissipation       : {eng(i_f**2 * R_T, "W")}')
# Leakage at the ~90 kΩ node vs 1 LSB there
r_node = R_T * R_B / (R_T + R_B)
print(f'BAV199 5 nA × {eng(r_node, "Ω")} = {eng(5e-9 * r_node, "V")}  vs 1 LSB at node {eng(lsb_in * k_div, "V")}')
# Fast edge: capacitive coupling onto ATT before the clamp acts
print(f'50 V edge couples {V_fault * c_t / (c_t + c_b_nom):.1f} V onto ATT (caught by the clamp)')
""")

md(r"""
### 3.4 Anti-aliasing filter

The ADC samples at 40 MSa/s and the FPGA decimates by 4 to 10 MSa/s. Anything the analog filter
passes near 40 MHz ± 5 MHz folds straight into the 0–5 MHz output band before the digital filter
can act, so the analog filter must attenuate at the **alias edge, 35 MHz**, while staying flat to
5 MHz. Content between 5 and 35 MHz lands outside the output band and is removed by the
decimation filter in the FPGA.

The filter is **3rd order**:

| Stage | Parts (ch A) | Type |
|---|---|---|
| THS4521 MFB | R23/R24 1.1 kΩ (R1), R25/R26 1 kΩ (R2), R27/R28 270 Ω (R3), C25/C26 100 pF to GND (C1), C27/C28 12 pF (C2) | complex pole pair |
| ADC input RC | R29/R30 33 Ω, C30 270 pF differential | real pole |

Standard MFB low-pass relations, per half-circuit:

$$ f_0 = \frac{1}{2\pi\sqrt{R_2 R_3 C_1 C_2}}, \qquad
   Q = \frac{\sqrt{R_2 R_3 C_1 C_2}}{C_2\,(R_2 + R_3 + R_2 R_3 / R_1)}, \qquad
   H_0 = -\frac{R_2}{R_1} $$

R22 (1 kΩ) with the OPA810 input capacitance makes a further pole far above the band
(≈ 80 MHz with the assumed 2 pF).
""")

code(r"""
AAF = dict(R_T=R_T, C_T=c_t, R_B=R_B, C_B=c_b_nom - C_buf,
           R_S=1e3, C_S=C_buf,
           R1=1.1e3, R2=1.0e3, R3=270.0, C1=100e-12, C2=12e-12,
           R_O=33.0, C_O=270e-12)

def mfb_f0_q(p):
    tau = np.sqrt(p['R2'] * p['R3'] * p['C1'] * p['C2'])
    f0 = 1 / (2 * np.pi * tau)
    Q = tau / (p['C2'] * (p['R2'] + p['R3'] + p['R2'] * p['R3'] / p['R1']))
    return f0, Q

f0, Q = mfb_f0_q(AAF)
f_ro = 1 / (2 * np.pi * 2 * AAF['R_O'] * AAF['C_O'])
f_rs = 1 / (2 * np.pi * AAF['R_S'] * AAF['C_S'])
print(f'MFB f0, Q          : {eng(f0, "Hz")}, Q = {Q:.3f}   (Butterworth Q = 0.707)')
print(f'ADC-input RC pole  : {eng(f_ro, "Hz")}')
print(f'buffer-input pole  : {eng(f_rs, "Hz")}  (assumed 2 pF)')
""")

md(r"""
Two models of the complete chain from BNC to ADC pins:

1. **Ideal cascade** — the product of the stage responses above (ideal amplifiers, no loading).
2. **Nodal model** — a node-voltage (MNA) solution of the circuit as wired in the code, including
   the divider, both halves of the MFB, the OPA810 (GBW 70 MHz) and the THS4521 (GBW 145 MHz,
   A₀ = 100 dB, both assumed single-pole). The FDA is modelled by
   `Vop − Von = A(s)·(V(VIN+) − V(VIN−))` and `Vop + Von = 0` (AC, VOCM held constant).
""")

code(r"""
def h_cascade(f, p=AAF):
    s = 2j * np.pi * np.asarray(f)
    f0, Q = mfb_f0_q(p); w0 = 2 * np.pi * f0
    return (1 / (1 + s * p['R_S'] * p['C_S'])
            / (1 + s / (w0 * Q) + (s / w0)**2)
            / (1 + s * 2 * p['R_O'] * p['C_O']))


def h_nodal(f, p=AAF, gbw_buf=70e6, gbw_fda=145e6, a0=1e5):
    # Nodes: ATT, BUF_IN, BUF_OUT, MS, MR, FIP, FIN, FOP, FON, AIN_P, AIN_N
    ATT, BI, BO, MS, MR, FIP, FIN, FOP, FON, AP, AN = range(11)
    GND, SRC = -1, -2
    s = 2j * np.pi * f
    Y = np.zeros((11, 11), complex); b = np.zeros(11, complex)

    def y(i, j, yy):                      # admittance from node i to node j (KCL row i)
        Y[i, i] += yy
        if j >= 0:
            Y[i, j] -= yy
        elif j == SRC:
            b[i] += yy                    # 1 V source at the BNC

    yT, yB, yS = 1/p['R_T'] + s*p['C_T'], 1/p['R_B'] + s*p['C_B'], 1/p['R_S']
    y(ATT, SRC, yT); y(ATT, GND, yB); y(ATT, BI, yS)
    y(BI, ATT, yS); y(BI, GND, s*p['C_S'])
    Y[BO, BO], Y[BO, BI] = 1, -1 / (1 + s / (2*np.pi*gbw_buf))          # OPA810 follower
    # signal leg: BO -R1- MS, MS -C1- GND, MS -R2- FON, MS -R3- FIP, FIP -C2- FON
    # ref leg:   GND -R1- MR, MR -C1- GND, MR -R2- FOP, MR -R3- FIN, FIN -C2- FOP
    for m, fi, fo_fb, src in ((MS, FIP, FON, BO), (MR, FIN, FOP, GND)):
        y(m, src, 1/p['R1']); y(m, GND, s*p['C1']); y(m, fi, 1/p['R3']); y(m, fo_fb, 1/p['R2'])
        y(fi, m, 1/p['R3']); y(fi, fo_fb, s*p['C2'])
    A = a0 / (1 + s * a0 / (2*np.pi*gbw_fda))
    Y[FOP, :] = 0; Y[FOP, FOP], Y[FOP, FON], Y[FOP, FIP], Y[FOP, FIN] = 1, -1, -A, A
    Y[FON, :] = 0; Y[FON, FOP], Y[FON, FON] = 1, 1
    y(AP, FOP, 1/p['R_O']); y(AP, AN, s*p['C_O'])
    y(AN, FON, 1/p['R_O']); y(AN, AP, s*p['C_O'])
    v = np.linalg.solve(Y, b)
    return v[AP] - v[AN]


h_nodal_v = np.vectorize(h_nodal, excluded={'p'})
H0 = abs(h_nodal(1.0))
print(f'nodal DC gain: {H0:.5f} V/V  (hand calc {k_total:.5f})')

def db(h):
    return 20 * np.log10(np.abs(h))

def f_3db(fn):
    return brentq(lambda x: db(fn(x)) + 3, 1e6, 3e7)

hn = lambda f: h_nodal(f) / H0
print(f'-3 dB: cascade {eng(f_3db(h_cascade), "Hz")}, nodal {eng(f_3db(hn), "Hz")}')
print(f'\n{"f":>9}  {"cascade":>8}  {"nodal":>8}')
for f in (1e6, 4e6, 5e6, 10e6, 20e6, 35e6, 40e6):
    print(f'{eng(f, "Hz"):>9}  {db(h_cascade(f)):7.2f}   {db(hn(f)):7.2f}  dB')
""")

code(r"""
f = np.logspace(5, np.log10(80e6), 400)
fig, ax = plt.subplots(figsize=(8, 4))
ax.semilogx(f, db(h_cascade(f)), label='ideal cascade')
ax.semilogx(f, db(h_nodal_v(f) / H0), '--', label='nodal model (finite GBW)')
ax.axvspan(1e5, 5e6, color='tab:green', alpha=0.08, label='output band 0–5 MHz')
ax.axvspan(35e6, 45e6, color='tab:red', alpha=0.10, label='aliases into band (35–45 MHz)')
ax.axhline(-3, color='gray', lw=0.6, ls=':')
ax.set_xlim(1e5, 80e6); ax.set_ylim(-50, 3)
ax.set_xlabel('frequency (Hz)'); ax.set_ylabel('gain re DC (dB)')
ax.set_title('Anti-alias filter: BNC → ADC pins')
ax.grid(which='both', alpha=0.3); ax.legend(fontsize=8, loc='lower left')
plt.tight_layout(); plt.show()
""")

md(r"""
Tolerance check: Monte-Carlo over the filter parts (R ±1 %, C ±5 % C0G, independent for each
half of the differential MFB is not modelled — both halves share one draw) using the nodal model.
""")

code(r"""
rng = np.random.default_rng(1)
keys_r = ('R1', 'R2', 'R3', 'R_O')
keys_c = ('C1', 'C2', 'C_O')
res = []
for _ in range(200):
    p = dict(AAF)
    for k in keys_r:
        p[k] = AAF[k] * (1 + rng.uniform(-0.01, 0.01))
    for k in keys_c:
        p[k] = AAF[k] * (1 + rng.uniform(-0.05, 0.05))
    h0 = abs(h_nodal(1.0, p))
    g = lambda x: h_nodal(x, p) / h0
    res.append((f_3db(g), db(g(5e6)), db(g(35e6)), max(db(g(x)) for x in np.linspace(1e5, 5e6, 20))))
res = np.array(res)
for i, name, unit in ((0, '-3 dB frequency', 'MHz'), (1, 'gain @ 5 MHz', 'dB'),
                      (2, 'gain @ 35 MHz', 'dB'), (3, 'peaking in 0–5 MHz', 'dB')):
    col = res[:, i] / (1e6 if unit == 'MHz' else 1)
    print(f'{name:20s}: min {col.min():7.2f}  mean {col.mean():7.2f}  max {col.max():7.2f}  {unit}')
""")

md(r"""
**Result and caveats.**

- `architecture/net_plan.md` quotes −3 dB at 8.80 MHz, −0.16 dB at 5 MHz and −35.8 dB at 35 MHz.
  The ideal cascade reproduces that (8.77 MHz, −0.17 dB, −36.5 dB).
- The nodal model, with the THS4521's finite GBW, shows **≈ 0.35 dB of in-band peaking** around
  4–5 MHz and a lower −3 dB point (≈ 8.25 MHz): the amplifier's phase lag raises the MFB's
  effective Q above the designed 0.99. It also gives more rejection at 35 MHz (≈ −40 dB). The
  architecture's nodal solve evidently used ideal amplifiers. Neither model has been checked
  against SPICE or measurement; the GBW figures are single-pole approximations.
- 36–40 dB of rejection at the alias edge is ~6 bits — well short of the 74 dB a 12-bit
  converter can resolve. Energy at 35–45 MHz at the BNC aliases into the band with only that
  much rejection. This is a documented limit (design_risks A6), not a defect.
- The ADC input capacitance and the OPA810 input capacitance are assumptions.
- In-band droop is to be equalised in the FPGA decimation FIR (≥ 70 dB stopband from 6 MHz);
  that HDL does not exist yet.
""")

md(r"""
### 3.5 Data rates, capture depth and USB upload
""")

code(r"""
F_ADC = 40e6; DECIM = 4; CH = 2; BYTES = 2      # 12-bit samples stored as 16-bit words
PSRAM = 8 * 2**20                                # 64 Mbit
USB_RATE = (30e6, 40e6)                          # FT232H sync-FIFO, practical range

f_out = F_ADC / DECIM
rate_store = f_out * CH * BYTES
print(f'ADC → FPGA          : 2 × 12 bit @ {eng(F_ADC, "Sa/s")} = {eng(F_ADC*24, "b/s")} parallel')
print(f'output rate         : {eng(f_out, "Sa/s")} per channel')
print(f'PSRAM write rate    : {eng(rate_store, "B/s")}  (raw device 664 MB/s; IP efficiency unverified, K3)')
print(f'capture depth       : {PSRAM / rate_store:.4f} s at 10 MSa/s (need ≥ 0.1 s)')
need = 0.1 * rate_store
print(f'upload of 0.1 s     : {eng(need, "B")} in {need/USB_RATE[1]:.2f}–{need/USB_RATE[0]:.2f} s')
print(f'streaming instead   : needs {eng(rate_store, "B/s")} sustained — at/above USB 2.0 HS practice')
""")

md(r"""
### 3.6 Regulator output voltages

TLV62569 bucks: `Vout = 0.6 V · (1 + R_top/R_bot)` (VFB 0.588–0.612 V). LM27762: positive side
`VP = 1.2 V · (R_top + R_bot)/R_bot`, negative side `VN = −1.22 V · (R_top + R_bot)/R_bot`
(R_bot ≥ 50 kΩ required). Worst case includes the reference tolerance and 1 % resistors.
""")

code(r"""
def divider_out(vref, r_top, r_bot, sign=1, vref_tol=0.02, r_tol=0.01):
    nom = vref * (r_top + r_bot) / r_bot
    hi = vref * (1 + vref_tol) * (1 + r_top * (1 + r_tol) / (r_bot * (1 - r_tol)))
    lo = vref * (1 - vref_tol) * (1 + r_top * (1 - r_tol) / (r_bot * (1 + r_tol)))
    return sign * nom, sign * lo, sign * hi

rails = [
    ('+3V3D  (U3, R5/R6)',   0.6,  100e3, 22e3,  1, 0.02,  'FPGA VCCX/VCCIO, ADC VDRV, FT VCCIO'),
    ('+1V2   (U4, R7/R8)',   0.6,  100e3, 100e3, 1, 0.02,  'GW1NR VCC 1.14–1.26 V'),
    ('+1V8   (U12, R14/R15)', 0.6, 200e3, 100e3, 1, 0.02,  'GW1NR VCCO3 1.71–1.89 V'),
    ('VAFE_P (U6, R10/R11)', 1.2,  180e3, 100e3, 1, 0.015, 'OPA810 V+'),
    ('VAFE_N (U6, R12/R13)', 1.22, 180e3, 100e3, -1, 0.015, 'OPA810 V−'),
]
out = {}
for name, vref, rt, rb, sg, tol, note in rails:
    nom, lo, hi = divider_out(vref, rt, rb, sg, tol)
    out[name.split()[0]] = (nom, lo, hi)
    print(f'{name:22s} {nom:+.3f} V  ({lo:+.3f} … {hi:+.3f})   {note}')
print('+3V3A  (U5, fixed)     +3.300 V')

vp_hi, vn_lo = out['VAFE_P'][2], out['VAFE_N'][2]
print(f'\nOPA810 worst total supply: {vp_hi - vn_lo:.3f} V (range 4.75–27 V)')
v3d_hi = out['+3V3D'][2]
print(f'ADS5231 |AVDD − VDRV| worst: {abs(v3d_hi - 3.3*0.98):.3f} V (abs max 0.3 V, LDO ±2 % assumed)')
""")

md(r"""
### 3.7 Power budget (as built)

Load currents are from `architecture/design_risks.md` P1; several are **assumptions** (FPGA core
150 mA = K5, +1V8 100 mA = K10). P1 placed the FT232H's 112 mA (52 mA regulator + 60 mA PHY,
max) on `+3V3D` through a buck. In 5 V mode that current comes **straight from VBUS through the
FT232H's internal linear regulator**, so it is recomputed here. Linear regulators draw their output
current from VBUS; bucks draw `P_out / η`.
""")

code(r"""
# (name, kind, V_out, I_max, efficiency)
loads = [
    ('+3V3A  TLV75733P LDO',        'ldo',  3.3,   92.1e-3, None),
    ('VAFE_P/N LM27762 (VIN)',      'ldo',  None,  24.4e-3, None),
    ('FT232H internal reg (5 V mode)', 'ldo', 3.3, 112e-3,  None),
    ('+3V3D  TLV62569 buck',        'buck', 3.327, 195e-3 - 112e-3, 0.88),
    ('+1V2   TLV62569 buck (K5)',   'buck', 1.2,   150e-3,  0.80),
    ('+1V8   TLV62569 buck (K10)',  'buck', 1.8,   100e-3,  0.82),
]
P_SWITCH = 0.05          # TPS22918 + PTC, W
LIMIT = 0.500
for vbus in (4.4, 5.0):
    i_lin = sum(i for _, k, _, i, _ in loads if k == 'ldo')
    p_sw = sum(v * i / e for _, k, v, i, e in loads if k == 'buck') + P_SWITCH
    i_tot = i_lin + p_sw / vbus
    print(f'VBUS {vbus:.2f} V: linear {i_lin*1e3:.0f} mA + switching {p_sw:.3f} W/{vbus} V = '
          f'{i_tot*1e3:.0f} mA ({i_tot*vbus:.2f} W);  ×1.25 margin = {1.25*i_tot*1e3:.0f} mA')

# The same budget with the FT232H on +3V3D (design_risks P1 as written, 3.3 V mode)
i_old = 92.1e-3 + 24.4e-3 + (3.327*0.195/0.88 + 0.225 + 0.220 + P_SWITCH) / 4.4
print(f'\nP1 as written (FT232H on +3V3D): {i_old*1e3:.0f} mA @4.4 V, ×1.25 = {1.25*i_old*1e3:.0f} mA')
print('→ 5 V mode costs ≈ 16 mA at 4.4 V and pushes the ×1.25 line just past 500 mA.')
print('  Without the margin factor the board stays under 500 mA; on a USB-C host advertising')
print('  1.5 A (the board has 5.1 kΩ Rd on CC) there is ample headroom.')

# LDO dissipation — the hottest small part
p5 = (5.25 - 3.3) * 92.1e-3
print(f'\nTLV75733P dissipation: {p5*1e3:.0f} mW → Tj ≈ {70 + p5*231:.0f} °C at 70 °C ambient, θJA 231 °C/W (limit 125 °C)')
""")

md(r"""
### 3.8 Miscellaneous values
""")

code(r"""
# FT232H 12 MHz crystal load caps (CL 20 pF)
c_ser = 33e-12 / 2
print(f'Y2 load: 33 pF ‖ 33 pF series = {eng(c_ser, "F")} + 3–5 pF stray = '
      f'{eng(c_ser + 3e-12, "F")} … {eng(c_ser + 5e-12, "F")}  (CL 20 pF)')

# LEDs D80/D81 through 1 kΩ from 3.3 V
print(f'LED current: (3.327 − 2.0 V) / 1 kΩ = {eng((3.327 - 2.0) / 1e3, "A")}')

# Clock-jitter budget for 12-bit-class SNR at 5 MHz
SNR_ADC = 70.7
for tj in (0.7e-12, 1e-12, 5.04e-12, 50e-12):
    snr_j = -20*np.log10(2*np.pi*5e6*tj)
    tot = -10*np.log10(10**(-SNR_ADC/10) + 10**(-snr_j/10))
    print(f'  jitter {tj*1e12:5.2f} ps rms → SNR_j {snr_j:5.1f} dB, with ADC {tot:5.2f} dB '
          f'(ENOB {(tot-1.76)/6.02:.2f})')
print('  Y1 OT322540MJBA4SL: 0.7 ps max (12 kHz–20 MHz). The FPGA PLL is kept out of the ADC clock path.')

# ADC → FPGA capture window without DVA/DVB (design_risks T4)
t_lo, t_hi = 14.8e-9, 25.0e-9
print(f'ADC data window at 40 MSa/s: {eng(t_lo, "s")} … {eng(t_hi, "s")} after CLK↑ = {eng(t_hi - t_lo, "s")}')

# Load-switch inrush (TPS22918, CT = 1 nF → tR 2.54 ms at 5 V); capacitance counted in §6.3
print('TPS22918 rise time with CT = 1 nF: 2.54 ms (datasheet) — inrush computed from the netlist in §6.3')
""")

# =====================================================================================
md(r"""
## 4. Part sourcing

All parts were sourced from JLCPCB/LCSC stock (`sourcing/sourced_bom.csv`, revision 3). The
active parts and connectors:
""")

code(r"""
import pandas as pd
bom = pd.read_csv(PROJ / 'sourcing' / 'sourced_bom.csv')
ics = bom[bom.refdes.str.match(r'^(U|Y|J)\d')][['refdes', 'mpn', 'lcsc', 'package', 'tier', 'stock', 'notes']]
display(ics.style.hide(axis='index'))
print(bom.tier.value_counts().to_string())
""")

# =====================================================================================
md(r"""
## 5. Design blocks (SKiDL)

Each block is an `@SubCircuit` function whose arguments are its interface nets. Nets local to a
block are created inside it. Each cell starts with `%%block <name>` (defined in the setup cell),
which runs it in its own namespace, as its `.py` module would be. Blocks never import each other; the top-level assembly (§6) creates
the interface nets and wires the blocks together. Execution order below follows the power path,
then the signal path.
""")

blocks = [
    ('usb_power_in', '5.1 USB power input',
     'USB-C receptacle (USB 2.0 data only) with 5.1 kΩ Rd on each CC, a 0.75 A PTC and SMF5.0A TVS '
     'on VBUS, USBLC6 ESD on D+/D−, and a TPS22918 load switch whose 1 nF CT gives a 2.5 ms rise to '
     'keep inrush into the downstream capacitance low (§6.3). Produces `VBUS_SW`.'),
    ('pwr_digital', '5.2 Digital power',
     'Three TLV62569 bucks make +3V3D, +1V2 (FPGA core) and +1V8 (FPGA bank 3 / PSRAM). +1V2 and '
     '+1V8 start together; +3V3D is held off 2–3 ms by an RC on its EN pin to meet the Gowin '
     'power-up rules (design_risks P3). Feedback values are checked in §3.6.'),
    ('pwr_analog', '5.3 Analog power',
     'A TLV75733P LDO makes +3V3A for the ADC and FDAs. An LM27762 (charge-pump inverter plus '
     'positive and negative LDOs) makes the ±3.4 V buffer rails, which set the clamp window.'),
    ('_afe_common', '5.4 Analog front-end helper',
     'Both channels are built by one parameterised function (refs offset by 20 for channel B). '
     'It is a plain helper, not a block: compensated divider (§3.2), clamp (§3.3), OPA810 '
     'follower, THS4521 MFB anti-alias filter (§3.4) and the output RC. The FDA output common mode '
     'tracks the ADC\'s own CM output via `ADC_VCM`. The BNC uses a **custom footprint** drawn from a '
     'not-to-scale drawing.'),
    ('afe_ch_a', '5.5 Analog front end, channel A', 'Refs J2, U20, U21, D20, R20–R30, C20–C31.'),
    ('afe_ch_b', '5.6 Analog front end, channel B', 'Refs J3, U40, U41, D40, R40–R50, C40–C51.'),
    ('adc_dual', '5.7 ADC',
     'ADS5231 in parallel-pin mode with the internal reference. REFT/REFB follow the datasheet '
     'figure (2 Ω, then 0.1 µF ‖ 2.2 µF). DVA/DVB and OVRA/OVRB are left unconnected to free FPGA '
     'pins; capture uses a phase-shifted FPGA clock and over-range shows as saturated codes.'),
    ('clock_gen', '5.8 Sample clock',
     '40 MHz CMOS oscillator (0.7 ps rms). One 33 Ω source-terminated branch feeds the ADC '
     'directly; an LVC1G34 buffer and a second 33 Ω feed the FPGA. The ADC clock never passes '
     'through the FPGA PLL.'),
    ('fpga', '5.9 FPGA capture engine',
     'GW1NR-9 with all 48 of its 3.3 V-capable I/O assigned (banks 1 and 2), wired by pin number '
     'from the pin map in `architecture/net_plan.md`. Bank 3 runs at 1.8 V for the PSRAM and '
     'carries JTAG and config straps, so the JTAG header J4 references +1V8. Also: MODE straps '
     '(auto-boot), trigger header J5, and two status LEDs.'),
    ('usb_bridge', '5.10 USB bridge',
     'FT232H in synchronous-245 FIFO mode: 8-bit bus clocked by its 60 MHz CLKOUT. **VREGIN 5 V mode** '
     '(datasheet Fig 6.1): VREGIN from `VBUS_SW`, VCCD is the internal regulator output (`FT_VCCD`) '
     'feeding VPLL, VPHY and the 93LC56 EEPROM; VCCIO stays on `+3V3D`. The EEPROM must be '
     'programmed to FIFO mode (FT_Prog) at bring-up.'),
]
for name, title, text in blocks:
    md(f'### {title}\n\n{text}')
    export = ' build_afe_channel' if name == '_afe_common' else ''
    code(f'%%block {name}{export}\n' + block_source(name))

# =====================================================================================
body, stab = main_source()
md(r"""
## 6. Top-level assembly

The assembly creates every interface net, then calls each block. Only `GND` needs
`.drive = POWER` here; the other rails are driven by regulator power-output pins or marked inside
their blocks. `reset()` clears SKiDL's default circuit so this cell can be re-run.
""")
code('reset()\n\n' + body)

md(r"""
### 6.1 Electrical rules check

`_stabilize_tags` gives every part a deterministic tag so netlists are repeatable from run to run.

Expected result: **0 errors, 0 warnings** (`outputs/erc_report.md`, plus the driver re-run after
the FT232H 5 V-mode change).
""")
code(stab + r"""


_stabilize_tags()
ERC()
print(f'{len(default_circuit.parts)} parts, {len(default_circuit.get_nets())} nets')
""")

md(r"""
### 6.2 Post-assembly checks

Values computed from the assembled circuit rather than from the documents: the capacitance hung
on `VBUS_SW` (which sets the load-switch inrush), and the parts on the FT232H's own 3.3 V net.
""")
code(r"""
import re

def farads(v):
    m = re.match(r'([\d.]+)\s*([pnuµm]?)F', v)
    return float(m.group(1)) * {'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'µ': 1e-6, 'm': 1e-3, '': 1}[m.group(2)]

def net_named(name):
    return next(n for n in default_circuit.get_nets() if n.name == name)

vb = net_named('VBUS_SW')
caps = sorted({p.part for p in vb.pins if p.part.ref.startswith('C')}, key=lambda p: p.ref)
c_tot = sum(farads(c.value) for c in caps)
print('VBUS_SW caps:', ', '.join(f'{c.ref} {c.value}' for c in caps))
print(f'total ≈ {eng(c_tot, "F")} (nominal, before DC-bias derating)')
for dv, tr in ((5.0, 2.54e-3),):
    print(f'inrush ≈ C·V/tR = {eng(c_tot * dv / tr, "A")} at {dv} V over {tr*1e3:.2f} ms')

ftv = net_named('FT_VCCD')
print('\nFT_VCCD pins:', ', '.join(f'{p.part.ref}.{p.num}({p.name})' for p in ftv.pins))
""")

md(r"""
### 6.3 Netlist (optional)

The pipeline's netlist and BOM are already in `outputs/`. Uncomment to regenerate them from the
notebook — this overwrites those files. (For byte-identical output, start the kernel with
`PYTHONHASHSEED=0`.)
""")
code(r"""
# generate_netlist(file_=str(PROJ / 'outputs' / 'dual_adc_usb.net'))
# generate_xml(file_=str(PROJ / 'outputs' / 'dual_adc_usb_bom.xml'))
""")

# =====================================================================================
md(r"""
## 7. Open items before layout

From `executive_summary.md`, `handoffs/06_erc.md` and `architecture/design_risks.md`:

- **Power margin:** with the FT232H in 5 V mode the worst case at 4.4 V is ≈ 412 mA; the ×1.25
  design margin line is ≈ 515 mA, just over 500 mA (§3.7). It rests on two unverified FPGA loads
  (K5 core ≤ 150 mA, K10 +1V8 ≤ 100 mA). Run the Gowin power analyzer; holding the ADC in
  power-down until the host opens the device is the first lever.
- **FPGA:** exposed pad = GND and PSRAM IP throughput (K3) are unverified; no spare 3.3 V I/O;
  dual-purpose pins must be set to "regular IO" in the Gowin project; UG284's ferrite + 4.7 µF on
  VCC is not fitted.
- **JTAG at 1.8 V:** needs a VREF-tracking programmer.
- **BNC footprint:** custom, from a not-to-scale drawing; dry-fit a real connector before fab.
- **Anti-alias limit:** ≈ 36 dB rejection at the 35 MHz alias edge (§3.4).
- **Stock:** ADC (235) and FPGA (182) are single-source with low stock.
- **Docs drift:** `architecture/net_plan.md` and design_risks P1 still show the FT232H on +3V3D.
- **HDL and host software:** decimation filter, capture logic and FIFO interface are not written.
""")

nb = nbf.v4.new_notebook(cells=cells, metadata={
    'kernelspec': {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'},
    'language_info': {'name': 'python'}})
nbf.write(nb, OUT)
print(f'wrote {OUT} ({len(cells)} cells)')
