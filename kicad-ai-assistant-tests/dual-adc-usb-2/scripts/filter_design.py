"""Front-end design calc: 1 MOhm compensated attenuator + THS4521 differential MFB
2nd-order low-pass + output RC pole -> 3rd-order Butterworth at fc.

MFB (single-ended equivalent, per leg):  H(s) = -K / (s^2 C1 C2 R2 R3 + s C2 (R2 + R3 + R2 R3/R1) + 1)
  R1: input resistor, R2: feedback resistor, R3: node->amp input, C1: node->gnd (diff cap = C1/2),
  C2: feedback capacitor.  K = R2/R1.
"""
import math, itertools
E96 = [1.00,1.02,1.05,1.07,1.10,1.13,1.15,1.18,1.21,1.24,1.27,1.30,1.33,1.37,1.40,1.43,1.47,1.50,1.54,1.58,
       1.62,1.65,1.69,1.74,1.78,1.82,1.87,1.91,1.96,2.00,2.05,2.10,2.15,2.21,2.26,2.32,2.37,2.43,2.49,2.55,
       2.61,2.67,2.74,2.80,2.87,2.94,3.01,3.09,3.16,3.24,3.32,3.40,3.48,3.57,3.65,3.74,3.83,3.92,4.02,4.12,
       4.22,4.32,4.42,4.53,4.64,4.75,4.87,4.99,5.11,5.23,5.36,5.49,5.62,5.76,5.90,6.04,6.19,6.34,6.49,6.65,
       6.81,6.98,7.15,7.32,7.50,7.68,7.87,8.06,8.25,8.45,8.66,8.87,9.09,9.31,9.53,9.76]
E12 = [1.0,1.2,1.5,1.8,2.2,2.7,3.3,3.9,4.7,5.6,6.8,8.2]
def near(v, ser):
    d = 10**math.floor(math.log10(v)); return min((s*d for s in ser+[10.0]), key=lambda x: abs(x-v))

# --- attenuator
R_top, R_bot = 909e3, 100e3
att = R_bot/(R_top+R_bot)
C_top = 15e-12; C_bot = C_top*R_top/R_bot
print(f"Attenuator {att:.5f}, Rin={(R_top+R_bot)/1e6:.3f} Mohm, C_bot needed={C_bot*1e12:.1f} pF "
      f"(fixed 120p + 5-30p trimmer + ~6p OPA810/layout), Cin={1/(1/C_top+1/C_bot)*1e12:.1f} pF")

# --- targets
fc = 3.2e6; w = 2*math.pi*fc
K = 0.953                       # MFB gain -> +/-10 V maps to +/-0.944 V diff (2 Vpp ADC span)
Q = 1.0; w0 = w                 # 3rd-order Butterworth = real pole at wc + pair (w0=wc, Q=1)
C2 = 47e-12; C1 = 470e-12       # C1 >= 4Q^2(1+K) C2 = 7.8 C2
a = C1*C2; 
# Solve for R2 (TI SBOA? / standard): R2 = (1 +/- sqrt(1-4Q^2(1+K)C2/C1)) / (2 w0 Q C2 (1+K)) ... derive numerically
best=None
for R2e in [near(x,E96) for x in [500*1.02**i for i in range(200)]]:
    R1 = R2e/K; R3 = 1/(w0**2*C1*C2*R2e)
    q = 1/(w0*C2*(R2e+R3+R2e*R3/R1))
    err = abs(q-Q)
    if best is None or err<best[0]: best=(err,R1,R2e,R3)
_,R1,R2,R3 = best
R1s,R2s,R3s = near(R1,E96),R2,near(R3,E96)
f0 = 1/(2*math.pi*math.sqrt(C1*C2*R2s*R3s)); Qs = 1/(2*math.pi*f0*C2*(R2s+R3s+R2s*R3s/R1s))
print(f"MFB: R1={R1s:.0f} R2={R2s:.0f} R3={R3s:.0f} C2={C2*1e12:.0f}p (per leg) Cdiff=C1/2={C1/2e-12:.0f}p "
      f"-> f0={f0/1e6:.2f} MHz Q={Qs:.2f} K={R2s/R1s:.3f}")
# --- output real pole: 2 x Rout + differential C (+ ADC input ~ 5 pF)
Rout = 49.9; Cd = 1/(2*math.pi*fc*2*Rout)
print(f"Output pole: Rout={Rout} per leg, Cdiff needed={Cd*1e12:.0f} pF -> use {near(Cd,E12)*1e12:.0f} pF")
def H(f):
    s = 2j*math.pi*f
    h2 = (R2s/R1s)/(s*s*C1*C2*R2s*R3s + s*C2*(R2s+R3s+R2s*R3s/R1s) + 1)
    h1 = 1/(1+s*2*Rout*(near(Cd,E12)+5e-12))
    return abs(h2*h1)
h0=H(1)
for f in [1e6,2e6,3e6,3.2e6,4e6,5e6,6.8e6,10e6,20e6]:
    print(f"  {f/1e6:5.1f} MHz: {20*math.log10(H(f)/h0):7.2f} dB")
fs = att*R2s/R1s
print(f"Overall gain {fs:.5f}: +/-10 V -> +/-{10*fs:.3f} V diff; full scale = +/-{1/fs:.2f} V")
