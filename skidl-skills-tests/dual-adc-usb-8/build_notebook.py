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
    """Block file text minus `from skidl import *` (done once in the setup cell)."""
    src = (BLK / f'{name}.py').read_text()
    new = src.replace('from skidl import *\n', '')
    assert new != src, f'{name}.py: skidl import not found'
    return new.strip('\n')


def main_source():
    """__main__.py adapted for a notebook: no relative imports, no __file__, no __main__ guard."""
    src = (BLK / '__main__.py').read_text()
    head, sep, tail = src.partition("# --- Supply nets")
    assert sep, '__main__.py: supply-net marker not found'
    body, sep, _ = (sep + tail).partition('\n\ndef _stabilize_tags')
    assert sep, '__main__.py: _stabilize_tags not found'
    stab = '\ndef _stabilize_tags' + _.split("\n\nif __name__ == '__main__':")[0]
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
import os
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import graphviz
from scipy.optimize import brentq

from skidl import *

PROJ = Path.cwd()
assert (PROJ / 'SPEC.md').exists(), 'start the notebook from the project root'

# Project-local symbol library (dual_adc_usb.kicad_sym) and footprint library (BNC).
if str(PROJ / 'symbols') not in lib_search_paths[KICAD9]:
    lib_search_paths[KICAD9].append(str(PROJ / 'symbols'))
if str(PROJ / 'footprints') not in footprint_search_paths[KICAD9]:
    footprint_search_paths[KICAD9].append(str(PROJ / 'footprints'))

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
| Connectors | 2 × BNC (scope-probe compatible); USB for power and data | HARD |
| Power | USB bus-powered; use USB-C (1.5 A) if the estimated draw exceeds ~2.0 W | HARD |
| Input impedance | ≈ 1 MΩ ‖ 20 pF (so 1×/10× probes compensate) | SOFT |
| Bandwidth | ≥ 5 MHz with anti-alias filtering | SOFT |
| Overvoltage | survive ±30 V continuous | SOFT |
| Transfer | capture-to-memory, then upload (streaming not required) | SOFT |
""")

# =====================================================================================
md(r"""
## 2. Architecture

Key decisions (`architecture/ic_selection.md`, `handoffs/02_architecture.md`):

- **ADC: TI ADS5231**, dual 12-bit, 40 MSa/s, one die → the two channels are sampled on the same
  clock edge. Its PLL mode needs ≥ 20 MSa/s, so the ADC **oversamples at 40 MSa/s** and the FPGA
  **decimates ×4** to 10 MSa/s. Oversampling also moves the first alias band from 5 MHz out to
  35 MHz, which is what makes an analog anti-alias filter practical at all (§3.4).
  (The claim that the ADS5231 cannot run below 20 MSa/s was contradicted in a later run — it can
  with the PLL off — but oversampling remains the better choice for the filter.)
- **Front end** per channel: compensated 909 k / 100 k divider (≈ 1 MΩ ‖ 20 pF, ÷10.09), BAV199
  clamp to the buffer rails, OPA356 unity buffer, THS4551 fully-differential amplifier wired as a
  2-pole multiple-feedback (MFB) low-pass, and a 49.9 Ω / 56 pF output RC at the ADC pins.
- **Capture engine: Gowin GW1NR-9** FPGA with 64 Mbit (8 MB) PSRAM inside the package — no
  external memory to route.
- **USB: FTDI FT232H** in synchronous-245 FIFO mode (≈ 35 MB/s, no firmware).
- **Power:** worst-case estimate 2.03 W > 2.0 W threshold, so a USB-C receptacle with 5.1 kΩ Rd
  pull-downs. Worst-case current (≈ 450 mA as built, §3.7) still fits a legacy 500 mA port.

### 2.1 Signal flow: analog inputs → USB connector
""")

code(r"""
sig = graphviz.Digraph('signal_flow', graph_attr={'rankdir': 'LR', 'fontsize': '10', 'nodesep': '0.25', 'ranksep': '0.35'},
                       node_attr={'shape': 'box', 'style': 'rounded,filled', 'fillcolor': '#eef3fb', 'fontsize': '10'},
                       edge_attr={'fontsize': '9'})

for ch, bnc, u1, u2 in (('A', 'J2', 'U101', 'U102'), ('B', 'J3', 'U201', 'U202')):
    with sig.subgraph(name=f'cluster_afe_{ch}') as c:
        c.attr(label=f'afe_ch_{ch.lower()}', style='dashed', color='gray50')
        c.node(f'bnc{ch}', f'BNC {bnc}\n±10 V', fillcolor='#fff4d6')
        c.node(f'div{ch}', 'Compensated divider\n909k / 100k  (÷10.09)\n1 MΩ || 20 pF + trimmer')
        c.node(f'clp{ch}', 'BAV199 clamp\nto +3.29 / −2.01 V')
        c.node(f'rc1{ch}', 'RC 1 k / 8.2 pF\npole 19.4 MHz')
        c.node(f'buf{ch}', f'OPA356 {u1}\nunity buffer')
        c.node(f'fda{ch}', f'THS4551 {u2}\n2-pole MFB, G = 0.909\nf0 9.28 MHz, Q 0.77\nSE → differential')
        c.node(f'rc2{ch}', 'RC 2×49.9 Ω / 56 pF\npole 27 MHz')
        c.edges([(f'bnc{ch}', f'div{ch}'), (f'div{ch}', f'clp{ch}'), (f'clp{ch}', f'rc1{ch}'),
                 (f'rc1{ch}', f'buf{ch}'), (f'buf{ch}', f'fda{ch}'), (f'fda{ch}', f'rc2{ch}')])

sig.node('xo', 'X1 40 MHz XO', shape='ellipse', fillcolor='#f3eefb')
sig.node('adc', 'ADS5231  U8\ndual 12-bit ADC\n40 MSa/s, simultaneous', fillcolor='#e3f4e3')
sig.node('fpga', 'GW1NR-9  U9\ndecimate ×4 → 10 MSa/s\n8 MB in-package PSRAM\ntrigger, capture', fillcolor='#e3f4e3')
sig.node('ft', 'FT232H  U10\nsync-245 FIFO → USB 2.0 HS', fillcolor='#e3f4e3')
sig.node('esd', 'USBLC6-2SC6  U1\nESD')
sig.node('usb', 'USB-C  J1', fillcolor='#fff4d6')

sig.edge('rc2A', 'adc', label='AIN_A_P/N\n±1.01 V diff')
sig.edge('rc2B', 'adc', label='AIN_B_P/N')
sig.edge('adc', 'fdaA', label='VCM 1.5 V', style='dotted', constraint='false')
sig.edge('adc', 'fdaB', label='VCM', style='dotted', constraint='false')
sig.edge('xo', 'adc', label='ADC_CLK', style='dashed')
sig.edge('xo', 'fpga', label='FPGA_CLK', style='dashed')
sig.edge('adc', 'fpga', label='DA[11:0], DB[11:0]\n@ 40 MSa/s')
sig.edge('fpga', 'ft', label='FT_D[7:0] @ 60 MHz\n≈ 35 MB/s')
sig.edge('ft', 'esd', label='USB_DP/DN\n480 Mb/s')
sig.edge('esd', 'usb')
sig
""")

md(r"""
### 2.2 Power distribution: USB VBUS → derived rails → consumers

All rails come from switched VBUS (`V5`). Digital loads get switching regulators; the analog
chain gets LDOs, and the clock oscillator and ADC output drivers are further isolated by ferrite
beads. The FT232H is powered from `V5` through its own internal 3.3 V regulator (as in Adafruit's
FT232H board), not from `V3V3D` — this differs from `architecture/net_plan.md` and was a driver
decision made during coding.
""")

code(r"""
pwr = graphviz.Digraph('power_tree', graph_attr={'rankdir': 'LR', 'fontsize': '10', 'nodesep': '0.2', 'ranksep': '0.45'},
                       node_attr={'shape': 'box', 'style': 'rounded,filled', 'fontsize': '10'},
                       edge_attr={'fontsize': '9'})
reg = {'fillcolor': '#fde9d9'}
rail = {'shape': 'plaintext', 'style': '', 'fontcolor': '#aa3333'}
load = {'fillcolor': '#e3f4e3'}

pwr.node('J1', 'USB-C J1\nVBUS 4.40–5.25 V', fillcolor='#fff4d6')
pwr.node('U2', 'TPS22919  U2\nsoft-start load switch', **reg)
pwr.node('V5', 'V5', **rail)
pwr.edges([('J1', 'U2'), ('U2', 'V5')])

# digital
pwr.node('U3', 'TLV62569  U3\nbuck', **reg)
pwr.node('U4', 'TLV62569  U4\nbuck', **reg)
pwr.node('U5', 'TLV75518  U5\nLDO', **reg)
pwr.node('V3V3D', 'V3V3D 3.315 V', **rail)
pwr.node('V1V2', 'V1V2 1.200 V', **rail)
pwr.node('V1V8', 'V1V8 1.800 V', **rail)
pwr.edges([('V5', 'U3'), ('U3', 'V3V3D'), ('V5', 'U4'), ('U4', 'V1V2'), ('V3V3D', 'U5'), ('U5', 'V1V8')])
pwr.node('L_fpio', 'FPGA U9\nVCCX, VCCIO0/1/2\n+ J5, power LED', **load)
pwr.node('L_fcore', 'FPGA U9 core VCC', **load)
pwr.node('L_psram', 'FPGA U9 VCCIO3\n(PSRAM bank), JTAG VREF', **load)
pwr.edges([('V3V3D', 'L_fpio'), ('V1V2', 'L_fcore'), ('V1V8', 'L_psram')])

# analog
pwr.node('U6', 'TPS7A2033  U6\nLDO', **reg)
pwr.node('U7', 'LM27762  U7\ncharge pump +\n± LDOs', **reg)
pwr.node('V3V3A', 'V3V3A 3.3 V', **rail)
pwr.node('VP', 'VP_AFE +3.288 V', **rail)
pwr.node('VN', 'VN_AFE −2.012 V', **rail)
pwr.node('FB1', 'FB1 bead', **reg)
pwr.node('FB2', 'FB2 bead', **reg)
pwr.edges([('V5', 'U6'), ('U6', 'V3V3A'), ('V5', 'U7'), ('U7', 'VP'), ('U7', 'VN'),
           ('V3V3A', 'FB1'), ('V3V3A', 'FB2')])
pwr.node('L_adc', 'ADS5231 U8 AVDD', **load)
pwr.node('L_vdrv', 'ADS5231 U8 VDRV\n(ADC_VDRV)', **load)
pwr.node('L_xo', 'X1 40 MHz XO\n(XO_VDD)', **load)
pwr.node('L_fda', 'THS4551 U102, U202', **load)
pwr.node('L_buf', 'OPA356 U101, U201\n+ BAV199 clamps', **load)
pwr.edges([('V3V3A', 'L_adc'), ('FB1', 'L_vdrv'), ('FB2', 'L_xo'), ('V3V3A', 'L_fda'),
           ('VP', 'L_buf'), ('VN', 'L_buf')])

# USB bridge
pwr.node('U10reg', 'FT232H U10\ninternal 3.3 V reg\n(VREGIN → VCCD)', **reg)
pwr.node('FT3V3', 'FT_3V3', **rail)
pwr.node('FB34', 'FB3 / FB4 beads', **reg)
pwr.node('L_ftio', 'FT232H VCCIO\n+ 93LC56 EEPROM', **load)
pwr.node('L_phy', 'FT232H VPHY / VPLL', **load)
pwr.edges([('V5', 'U10reg'), ('U10reg', 'FT3V3'), ('FT3V3', 'L_ftio'), ('FT3V3', 'FB34'), ('FB34', 'L_phy')])
pwr
""")

# =====================================================================================
md(r"""
## 3. Component calculations

Each subsection recomputes the values in the architecture documents from the component values
used in the code, so the numbers can be checked and re-run if a part changes.

### 3.1 Signal scaling and full scale

The ADS5231 full-scale input is 2.02 Vpp differential (±1.01 V) around its 1.5 V common-mode
output. The front end's gain from BNC to ADC pins is the divider ratio times the FDA gain.
""")

code(r"""
R_T, R_B = 909e3, 100e3          # R101 / R102
R1, R2 = 1.00e3, 909.0           # MFB input / feedback resistors (R104, R106)
ADC_FS_DIFF = 1.01               # ADS5231 ±full scale, differential volts
N_BITS = 12

k_div = R_B / (R_T + R_B)
k_fda = R2 / R1
k_total = k_div * k_fda
fs_in = ADC_FS_DIFF / k_total
lsb_in = 2 * fs_in / 2**N_BITS

print(f'divider ratio        : {k_div:.5f}  (÷{1/k_div:.3f})')
print(f'FDA gain R2/R1       : {k_fda:.4f}')
print(f'total gain           : {k_total:.5f} V/V')
print(f'full scale at BNC    : ±{fs_in:.2f} V   (margin over ±10 V: {100*(fs_in/10-1):.1f} %)')
print(f'LSB referred to BNC  : {eng(lsb_in, "V")}')
print(f'buffer swing at FS   : ±{fs_in*k_div:.3f} V')

# Worst-case FS with ADC gain error ±3.5 % and ~3 % resistor-ratio error (design_risks.md §2)
print(f'worst-case low FS    : ±{fs_in*(1-0.035-0.03):.2f} V  (must stay > 10 V)')
""")

md(r"""
### 3.2 Compensated input divider

A resistive divider loaded by capacitance has a frequency-dependent ratio. It is flat when both
legs have the same time constant, `R_T·C_T = R_B·C_B`. That is also what lets a 10× probe (itself a
9 MΩ ‖ C divider) be compensated against this input.

`C_B` is the sum of C102 (150 pF), C103 (15 pF), C_S (8.2 pF, seen through R_S = 1 kΩ, which is
small against the ~90 kΩ node impedance), ~3 pF of board parasitics, and the JZ300 trimmer
(5.5–30 pF).
""")

code(r"""
C_T = 22e-12                     # C101
C_B_fixed = 150e-12 + 15e-12     # C102 + C103
C_S = 8.2e-12                    # C105 (behind R103)
C_par = 3e-12                    # board parasitics (estimate)
TRIM_MIN, TRIM_MAX = 5.5e-12, 30e-12   # JZ300

C_B_needed = R_T * C_T / R_B
trim_nom = C_B_needed - C_B_fixed - C_S - C_par

# Worst-case spread of the fixed parts: C_T ±1 % (×R_T/R_B), C_B1/C_B2 ±1 %, parasitics ±2 pF
spread = (R_T / R_B) * 0.01 * C_T + 0.01 * C_B_fixed + 2e-12
print(f'C_B needed            : {eng(C_B_needed, "F")}')
print(f'trimmer nominal       : {eng(trim_nom, "F")}')
print(f'trimmer needed range  : {eng(trim_nom - spread, "F")} … {eng(trim_nom + spread, "F")}'
      f'   (JZ300: {eng(TRIM_MIN, "F")} … {eng(TRIM_MAX, "F")})')
print(f'headroom at top       : {eng(TRIM_MAX - (trim_nom + spread), "F")}  <-- thin; ±5 % caps would overrun it')

R_in = R_T + R_B
C_in = C_T * (C_B_needed) / (C_T + C_B_needed)
print(f'input impedance       : {eng(R_in, "Ω")} ‖ {eng(C_in, "F")}  (+ BNC/trace ≈ 2 pF)')

# JZ300 TC is −1500 ± 1000 ppm/°C → drift of the trimmer over a 25 °C swing
for tc in (-500e-6, -2500e-6):
    print(f'trimmer drift @ {tc*1e6:.0f} ppm/°C, ΔT = 25 °C : {eng(trim_nom*tc*25, "F")}')
""")

md(r"""
Step response of the divider (what you see when adjusting the trimmer with a 1 kHz square wave).
With `C_B` total, the edge ratio is `C_T/(C_T+C_B)` and the settled ratio is `R_B/(R_T+R_B)`;
the transition between them has time constant `(R_T‖R_B)(C_T+C_B)`.
""")

code(r"""
t = np.linspace(0, 150e-6, 600)
fig, ax = plt.subplots(figsize=(7, 3.2))
for trim, lbl in ((trim_nom - 8e-12, 'trimmer low (over-compensated)'),
                  (trim_nom, f'trimmer {trim_nom*1e12:.1f} pF (flat)'),
                  (trim_nom + 5e-12, 'trimmer high (under-compensated)')):
    C_Bt = C_B_fixed + C_S + C_par + trim
    v0 = C_T / (C_T + C_Bt)
    tau = (R_T * R_B / (R_T + R_B)) * (C_T + C_Bt)
    v = k_div + (v0 - k_div) * np.exp(-t / tau)
    ax.plot(t * 1e6, v / k_div, label=lbl)
ax.set_xlabel('time after 1 kHz square-wave edge (µs)')
ax.set_ylabel('output / ideal')
ax.set_title('Compensated divider step response')
ax.grid(alpha=0.3); ax.legend(fontsize=8)
plt.tight_layout(); plt.show()
""")

md(r"""
### 3.3 Overvoltage protection (±30 V)

The BAV199 dual diode clamps the divider node to the buffer rails. Because the divider already
divides by 10, the fault current is limited by R_T, not by a series resistor.
""")

code(r"""
V_fault = 30.0
VP_AFE, VN_AFE = 3.288, -2.012
V_F = 0.5          # BAV199 forward drop at µA currents (approximate)

v_div_fault = V_fault * k_div
print(f'divider node at ±30 V : ±{v_div_fault:.2f} V (unclamped)')
print(f'clamp window          : {VN_AFE - V_F:.2f} … {VP_AFE + V_F:.2f} V')
print(f'fault current (R_T)   : {eng(V_fault / R_T, "A")}')
print(f'R_T dissipation       : {eng(V_fault**2 / R_T, "W")}')
print(f'OPA356 input CM limit : {VN_AFE - 0.1:.2f} … {VP_AFE - 1.5:.2f} V  vs normal peak ±{fs_in*k_div:.3f} V')
""")

md(r"""
### 3.4 Anti-aliasing filter

The ADC samples at 40 MSa/s and the FPGA decimates by 4 to 10 MSa/s. Anything the analog filter
passes near 40 MHz ± 5 MHz folds straight into the 0–5 MHz output band *before* the digital
filter can act, so the analog filter has to attenuate at the **alias edge, 35 MHz**, while
staying flat to ~4–5 MHz. Content between 5 and 35 MHz lands outside the output band after
sampling and is removed by the decimation filter.

The filter has four poles at distinct nodes:

| Stage | Parts (ch A) | Type |
|---|---|---|
| Buffer input RC | R103 1 kΩ, C105 8.2 pF | real pole |
| THS4551 MFB | R104/R105 1 kΩ (R1), R106/R107 909 Ω (R2), R108/R109 499 Ω (R3), C108 27 pF differential (C1), C109/C110 12 pF (C2) | complex pole pair |
| ADC input RC | R110/R111 49.9 Ω, C113 56 pF + ~3 pF ADC input | real pole |

For the MFB, the differential capacitor C108 appears as 2 × 27 pF to the virtual midpoint in each
half-circuit. Standard MFB low-pass relations per half-circuit:

$$ f_0 = \frac{1}{2\pi\sqrt{R_2 R_3 C_1 C_2}}, \qquad
   Q = \frac{\sqrt{R_2 R_3 C_1 C_2}}{C_2\,(R_2 + R_3 + R_2 R_3 / R_1)}, \qquad
   H_0 = -\frac{R_2}{R_1} $$
""")

code(r"""
AAF = dict(R_T=R_T, C_T=C_T, R_B=R_B, C_B=C_B_fixed + trim_nom + C_par,
           R_S=1e3, C_S=8.2e-12,
           R1=1e3, R2=909.0, R3=499.0, C1=27e-12, C2=12e-12,
           R_O=49.9, C_O=56e-12 + 3e-12)

def mfb_f0_q(p):
    C1h = 2 * p['C1']                          # differential cap seen per half-circuit
    tau = np.sqrt(p['R2'] * p['R3'] * C1h * p['C2'])
    f0 = 1 / (2 * np.pi * tau)
    Q = tau / (p['C2'] * (p['R2'] + p['R3'] + p['R2'] * p['R3'] / p['R1']))
    return f0, Q

f0, Q = mfb_f0_q(AAF)
f_rs = 1 / (2 * np.pi * AAF['R_S'] * AAF['C_S'])
f_ro = 1 / (2 * np.pi * 2 * AAF['R_O'] * AAF['C_O'])
print(f'buffer-input pole  : {eng(f_rs, "Hz")}')
print(f'MFB f0, Q          : {eng(f0, "Hz")}, Q = {Q:.3f}   (Butterworth Q = 0.707)')
print(f'ADC-input RC pole  : {eng(f_ro, "Hz")}')
""")

md(r"""
Two models of the complete chain from BNC to ADC pins:

1. **Ideal cascade** — the product of the three stage responses above (ideal amplifiers, no
   loading between stages).
2. **Nodal model** — a full node-voltage (MNA) solution of the circuit as wired in the code,
   including the divider, both halves of the MFB, the OPA356 (GBW ≈ 200 MHz) and the THS4551
   (GBW 135 MHz, A₀ = 100 dB) as single-pole amplifiers. The FDA is modelled by
   `Vop − Von = A(s)·(V(FIP) − V(FIN))` and `Vop + Von = 0` (AC, VCM held constant).
""")

code(r"""
def h_cascade(f, p=AAF):
    s = 2j * np.pi * np.asarray(f)
    f0, Q = mfb_f0_q(p); w0 = 2 * np.pi * f0
    return (1 / (1 + s * p['R_S'] * p['C_S'])
            / (1 + s / (w0 * Q) + (s / w0)**2)
            / (1 + s * 2 * p['R_O'] * p['C_O']))


def h_nodal(f, p=AAF, gbw_buf=200e6, gbw_fda=135e6, a0=1e5):
    # Node order: DIV, BUF_IN, BUF_OUT, XP, XN, FIP, FIN, FOP, FON, AIN_P, AIN_N
    DIV, BI, BO, XP, XN, FIP, FIN, FOP, FON, AP, AN = range(11)
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
    y(DIV, SRC, yT); y(DIV, GND, yB); y(DIV, BI, yS)
    y(BI, DIV, yS); y(BI, GND, s*p['C_S'])
    Y[BO, BO], Y[BO, BI] = 1, -1 / (1 + s / (2*np.pi*gbw_buf))          # OPA356 follower
    for x, fi, fo_same, fo_fb, src in ((XP, FIP, FOP, FON, BO), (XN, FIN, FON, FOP, GND)):
        other = XN if x == XP else XP
        y(x, src, 1/p['R1']); y(x, other, s*p['C1']); y(x, fi, 1/p['R3']); y(x, fo_fb, 1/p['R2'])
        y(fi, x, 1/p['R3']); y(fi, fo_fb, s*p['C2'])
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
half of the differential MFB) using the nodal model.
""")

code(r"""
rng = np.random.default_rng(1)
keys_r = ('R1', 'R2', 'R3', 'R_O', 'R_S')
keys_c = ('C1', 'C2', 'C_O', 'C_S')
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

- The filter gives roughly **33–35 dB of rejection at the 35 MHz alias edge** and a −3 dB
  bandwidth near 8.3–8.7 MHz, depending on the amplifier model. That is about 5–6 bits of
  alias suppression, well short of the 74 dB a 12-bit converter could resolve. The design accepts
  this as a documented limit: out-of-band energy at 35–45 MHz aliases with only ~33 dB rejection.
- `architecture/design_risks.md` quotes −3 dB at 8.86 MHz and −32.1 dB at 35 MHz from its own
  node model. The models here land within ~0.5 MHz / ~2 dB of that; the difference is in the
  amplifier and parasitic assumptions (unknown for the original model). Neither has been checked
  against SPICE or measurement.
- The ADC input capacitance (~3 pF here) is an assumption; it is not in the ADS5231 summary.
- In-band droop (≈ 0.3–0.4 dB at 5 MHz) is meant to be equalised in the FPGA decimation FIR
  (planned: pass 0–4 MHz ≤ 0.1 dB ripple, stop ≥ 60 dB from 6 MHz). That HDL does not exist yet.
""")

md(r"""
### 3.5 Data rates, capture depth and USB upload
""")

code(r"""
F_ADC = 40e6; DECIM = 4; CH = 2; BYTES = 2      # 12-bit samples stored as 16-bit words
PSRAM = 8 * 2**20                                # 64 Mbit
USB_RATE = 35e6                                  # FT232H sync-FIFO, practical

f_out = F_ADC / DECIM
rate_store = f_out * CH * BYTES
print(f'ADC → FPGA          : 2 × 12 bit @ {eng(F_ADC, "Sa/s")} = {eng(F_ADC*24, "b/s")} parallel')
print(f'output rate         : {eng(f_out, "Sa/s")} per channel')
print(f'PSRAM write rate    : {eng(rate_store, "B/s")}')
print(f'capture depth       : {PSRAM / rate_store:.3f} s at 10 MSa/s (need ≥ 0.1 s)')
print(f'raw 40 MSa/s depth  : {PSRAM / (F_ADC*CH*BYTES):.3f} s')
need = 0.1 * rate_store
print(f'upload of 0.1 s     : {eng(need, "B")} in {need/USB_RATE:.3f} s at {eng(USB_RATE, "B/s")}')
""")

md(r"""
### 3.6 Regulator output voltages

TLV62569 bucks: `Vout = 0.6 V · (1 + R_top/R_bot)`. LM27762: positive side
`VP = 1.2 V · (R_top + R_bot)/R_bot`, negative side `VN = −1.22 V · (R_top + R_bot)/R_bot`
(datasheet requires R_bot ≥ 50 kΩ). Worst case includes the reference tolerance and 1 % resistors.
""")

code(r"""
def divider_out(vref, r_top, r_bot, sign=1, vref_tol=0.02, r_tol=0.01):
    nom = vref * (r_top + r_bot) / r_bot
    hi = vref * (1 + vref_tol) * (1 + r_top * (1 + r_tol) / (r_bot * (1 - r_tol)))
    lo = vref * (1 - vref_tol) * (1 + r_top * (1 - r_tol) / (r_bot * (1 + r_tol)))
    return sign * nom, sign * lo, sign * hi

rails = [
    ('V3V3D (U3, R3/R4)', 0.6, 100e3, 22.1e3, 1, 0.02, 'FPGA VCCIO, logic 3.3 V'),
    ('V1V2  (U4, R5/R6)', 0.6, 100e3, 100e3, 1, 0.02, 'GW1NR VCC 1.14–1.26 V'),
    ('VP_AFE (U7, R8/R9)', 1.2, 174e3, 100e3, 1, 0.015, 'OPA356 V+'),
    ('VN_AFE (U7, R10/R11)', 1.22, 64.9e3, 100e3, -1, 0.015, 'OPA356 V−'),
]
out = {}
for name, vref, rt, rb, sg, tol, note in rails:
    nom, lo, hi = divider_out(vref, rt, rb, sg, tol)
    out[name.split()[0]] = (nom, lo, hi)
    print(f'{name:22s} {nom:+.3f} V  ({lo:+.3f} … {hi:+.3f})   {note}')
print('V3V3A (U6, fixed)       +3.300 V;  V1V8 (U5, fixed) +1.800 V')

vp_hi, vn_lo = out['VP_AFE'][2], out['VN_AFE'][2]
print(f'\nOPA356 worst total supply: {vp_hi - vn_lo:.3f} V (max 5.5 V)')
""")

md(r"""
### 3.7 Power budget (as built)

Load currents are from `architecture/design_risks.md`; many are **estimates** (FPGA core and I/O,
FT232H, PSRAM) pending the Gowin power estimator. That table assumed the FT232H ran from `V3V3D`;
the code feeds it from `V5` through its internal regulator, so it is recomputed here.
Linear regulators draw their output current from V5; bucks draw `P_out / η`.
""")

code(r"""
V5_TYP, V5_MAX = 5.0, 5.25
# (name, kind, V_out, I_typ, I_max, eff_typ, eff_max)
loads = [
    ('V3V3A  TPS7A2033 LDO',       'ldo',  3.3,   110.2e-3, 139.1e-3, None, None),
    ('VP/VN_AFE LM27762 (VIN)',    'ldo',  None,  38.2e-3,  54.0e-3,  None, None),
    ('FT232H internal reg',        'ldo',  3.3,   60.5e-3,  81.0e-3,  None, None),
    ('V3V3D  TLV62569 buck',       'buck', 3.315, 49.4e-3,  109.9e-3, 0.90, 0.85),
    ('V1V2   TLV62569 buck',       'buck', 1.2,   50e-3,    150e-3,   0.80, 0.75),
]
tot_t = tot_m = 0
print(f'{"rail":28s} {"typ mW":>8} {"max mW":>8}')
for name, kind, v, it, im, et, em in loads:
    if kind == 'ldo':
        pt, pm = V5_TYP * it, V5_MAX * im
    else:
        pt, pm = v * it / et, v * 1.02 * im / em
    tot_t += pt; tot_m += pm
    print(f'{name:28s} {pt*1e3:8.0f} {pm*1e3:8.0f}')
p_sw = (tot_m / 4.75)**2 * 0.09
tot_m += p_sw
print(f'{"TPS22919 switch loss":28s} {0:8.0f} {p_sw*1e3:8.0f}')
print(f'{"TOTAL":28s} {tot_t*1e3:8.0f} {tot_m*1e3:8.0f}   → USB-C chosen (> 2.0 W worst case)')
print(f'worst-case VBUS current at 4.75 V: {tot_m/4.75*1e3:.0f} mA (legacy port limit 500 mA)')

# LDO dissipation — the hottest small part
i6 = 139.1e-3
p6 = (V5_MAX - 3.3) * i6
print(f'\nTPS7A2033 dissipation: {p6*1e3:.0f} mW → ΔT ≈ {p6*200:.0f} °C at ~200 °C/W (est.) → '
      f'Tj ≈ {50 + p6*200:.0f} °C at 50 °C ambient (limit 125 °C)')
""")

md(r"""
### 3.8 Miscellaneous values
""")

code(r"""
# FT232H 12 MHz crystal load caps (CL = 20 pF is UNVERIFIED — distributor field only)
CL, C_stray = 20e-12, 3.5e-12
c_load = 2 * (CL - C_stray)
print(f'Y1 load caps: 2·(CL − Cstray) = {eng(c_load, "F")} → 33 pF (C47, C48); '
      f'actual CL = {eng(33e-12/2 + C_stray, "F")}')

# LEDs
for ref, v in (('D1', 3.315), ('D2/D3', 3.3)):
    print(f'{ref} current: ({v} − 2.0 V) / 1 kΩ = {eng((v - 2.0) / 1e3, "A")}')

# Clock levels: XO VOH/VOL vs ADS5231 CLK thresholds
VOH, VOL, VIH, VIL = 0.9 * 3.3, 0.1 * 3.3, 2.2, 0.6
print(f'XO VOH {VOH:.2f} V ≥ VIH {VIH} V: {VOH >= VIH};  VOL {VOL:.2f} V ≤ VIL {VIL} V: {VOL <= VIL}')

# Clock-jitter budget for 12-bit-class SNR at 5 MHz
for tj in (1e-12, 3e-12, 10e-12, 50e-12):
    print(f'  jitter {tj*1e12:4.0f} ps rms → SNR limit {-20*np.log10(2*np.pi*5e6*tj):.1f} dB at 5 MHz')

# ADC bias resistor
print(f'ISET R12 = 56.2 kΩ (datasheet value); USB PHY REF R25 = 12.0 kΩ 1 % (FT232H requirement)')
""")

# =====================================================================================
md(r"""
## 4. Part sourcing

All parts were sourced from JLCPCB/LCSC stock (`sourcing/sourced_bom.csv`). The critical ICs:
""")

code(r"""
import pandas as pd
bom = pd.read_csv(PROJ / 'sourcing' / 'sourced_bom.csv')
ics = bom[bom.refdes.str.match(r'^(U|X|Y|J)\d')][['refdes', 'mpn', 'lcsc', 'package', 'tier', 'stock', 'notes']]
display(ics.style.hide(axis='index'))
print(bom.tier.value_counts().to_string())
""")

# =====================================================================================
md(r"""
## 5. Design blocks (SKiDL)

Each block is an `@SubCircuit` function whose arguments are its interface nets. Nets local to a
block are created inside it. Blocks never import each other; the top-level assembly (§6) creates
the interface nets and wires the blocks together. Ref designators follow the architecture's
numbering (1xx = channel A, 2xx = channel B).

Execution order below follows the power path, then the signal path.
""")

blocks = [
    ('usb_power_in', '5.1 USB power input',
     'USB-C receptacle (USB 2.0 data only), CC pull-downs so any USB-C source supplies default '
     'power, USBLC6 ESD on D+/D−/VBUS, and a TPS22919 load switch whose controlled rise keeps the '
     'inrush from the >100 µF of downstream capacitance within USB limits. Produces `V5`.'),
    ('power_digital', '5.2 Digital power',
     'Two TLV62569 bucks make 3.3 V (logic, FPGA I/O) and 1.2 V (FPGA core). A TLV75518 LDO off '
     '3.3 V makes 1.8 V for FPGA bank 3, which also powers the in-package PSRAM. Feedback values '
     'are checked in §3.6.'),
    ('power_analog', '5.3 Analog power',
     'A TPS7A2033 LDO makes a quiet 3.3 V for the ADC, FDAs and clock. An LM27762 (charge-pump '
     'inverter plus positive and negative LDOs) makes the asymmetric +3.29 V / −2.01 V buffer rails, '
     'chosen so the OPA356 (5.5 V max total) can swing ±1.11 V with headroom.'),
    ('afe_ch_a', '5.4 Analog front end, channel A',
     'Compensated divider (§3.2), clamp (§3.3), OPA356 buffer, and the THS4551 MFB anti-alias '
     'filter / single-ended-to-differential converter (§3.4). The FDA output common mode tracks the '
     'ADC\'s own CM output via `VCM`.'),
    ('afe_ch_b', '5.5 Analog front end, channel B',
     'Identical to channel A with 2xx refs and `B_` local nets. (It is a copy rather than a second '
     'call of one parameterised function — a DRY violation carried from the pipeline, which '
     'required one file per block.)'),
    ('adc', '5.6 ADC',
     'ADS5231 in parallel-pin mode (no SPI), internal reference, offset-binary outputs always '
     'enabled. `STPD` is FPGA-controlled with a pull-down so the ADC runs by default. VDRV is fed '
     'from V3V3A through a bead so AVDD and VDRV cannot differ by more than the 0.3 V abs-max.'),
    ('clock', '5.7 Sample clock',
     '40 MHz CMOS oscillator on its own filtered supply. Two 33 Ω source-terminated branches feed '
     'the ADC and the FPGA separately; the ADC clock never passes through the FPGA (whose PLL '
     'jitter (50–100 ps) would cost 25–30 dB of SNR — see §3.8).'),
    ('fpga', '5.8 FPGA capture engine',
     'GW1NR-9 with every one of its 48 usable 3.3 V I/O assigned (banks 1 and 2). Bank 3 runs at '
     '1.8 V for the PSRAM and carries only JTAG and config straps. Also: JTAG header J4, trigger / '
     'GPIO header J5, and two status LEDs. The pin map lives in `fpga_pinmap.md`.'),
    ('usb_bridge', '5.9 USB bridge',
     'FT232H in synchronous-245 FIFO mode: 8-bit bus clocked by its own 60 MHz CLKOUT. Powered from '
     'V5 via its internal regulator. A 93LC56 EEPROM holds the configuration that selects FIFO '
     'mode. **Unverified:** the ACBUS FIFO pin mapping and the crystal\'s load capacitance.'),
]
for name, title, text in blocks:
    md(f'### {title}\n\n{text}')
    code(block_source(name))

# =====================================================================================
body, stab = main_source()
md(r"""
## 6. Top-level assembly

The assembly creates every interface net (supply nets are marked as driven, because regulators
that feed them through inductors or beads present only passive pins to ERC), then calls each block.
`reset()` clears SKiDL's default circuit so this cell can be re-run.
""")
code('reset()\n\n' + body)

md(r"""
### 6.1 Electrical rules check

`_stabilize_tags` gives every part a deterministic tag so netlists are repeatable from run to run.

Expected result: **0 errors, 6 warnings**. The warnings are all on `FT_EECS` / `FT_EECLK`: the KiCad
FT232H symbol types its EEPROM pins as inputs, so ERC sees no driver. They were reviewed and accepted
in `erc_report.md` (W1–W6).
""")
code(stab + r"""


_stabilize_tags()
ERC()
print(f'{len(default_circuit.parts)} parts, {len(default_circuit.get_nets())} nets')
""")

md(r"""
### 6.2 Netlist (optional)

The pipeline's netlist and BOM are already in `outputs/`. Uncomment to regenerate them from the
notebook — this overwrites those files.
""")
code(r"""
# generate_netlist(file_=str(PROJ / 'outputs' / 'dual_adc_usb.net'))
# generate_xml(file_=str(PROJ / 'outputs' / 'dual_adc_usb_bom.xml'))
""")

# =====================================================================================
md(r"""
## 7. Open items before layout

From `executive_summary.md` and `architecture/design_risks.md`:

- **FT232H:** FIFO-mode pin mapping and crystal CL unverified against the datasheet.
- **FPGA:** bank / boot assumptions come from reference designs, not a Gowin document; no spare
  3.3 V I/O remain. FPGA and FT232H power figures are estimates.
- **JTAG header:** pinout and 1.8 V level unchecked against the Gowin cable.
- **Oscillator:** no published jitter spec; the ≤ 3 ps budget cannot be confirmed.
- **Anti-alias limit:** only ~33 dB rejection at the 35 MHz alias edge (§3.4).
- **JZ300 trimmer:** thin headroom at the top of its range (§3.2) and 0.3–1.5 pF drift over 25 °C.
- **BNC footprint:** custom-made; dry-fit a real connector before fabrication.
- **Stock:** low for the ADC, FPGA and THS4551; single-source ADC.
- **HDL:** decimation filter, capture logic and FIFO interface are not written.
""")

nb = nbf.v4.new_notebook(cells=cells, metadata={
    'kernelspec': {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'},
    'language_info': {'name': 'python'}})
nbf.write(nb, OUT)
print(f'wrote {OUT} ({len(cells)} cells)')
