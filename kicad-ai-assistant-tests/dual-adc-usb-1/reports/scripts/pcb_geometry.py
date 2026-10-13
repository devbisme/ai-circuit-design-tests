"""Read-only PCB geometry checks (KiCad 10 pcbnew). Usage: python pcb_geometry.py board.kicad_pcb"""
import sys, math, collections, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM
pads = []  # (ref, num, net, x, y, layerset-front?)
for f in b.GetFootprints():
    for p in f.Pads():
        if p.IsOnCopperLayer():
            q = p.GetPosition()
            pads.append((f.GetReference(), p.GetNumber(), p.GetNetname(), mm(q.x), mm(q.y)))
caps = collections.defaultdict(list)
for r, n, net, x, y in pads:
    if r.startswith('C'):
        caps[net].append((r, x, y))
supplies = {'+3V3','+3V0','+1V2','+4V','VEE','+5V','/USB/V1V8_FT','/FPGA_SDRAM/VCCPLL0','/FPGA_SDRAM/VCCPLL1'}
print("== Supply-rail pins: distance to nearest same-net capacitor pad (mm), ICs only")
for ref in sorted({p[0] for p in pads if p[0][0] in 'UX'}):
    rows = []
    for r, n, net, x, y in pads:
        if r != ref or net not in supplies or net not in caps: continue
        d, c = min((math.hypot(x - cx, y - cy), cr) for cr, cx, cy in caps[net])
        rows.append((d, n, net, c))
    if rows:
        far = [t for t in rows if t[0] > 5]
        w = max(rows)
        print(f"{ref:5} pins={len(rows):3} >5mm={len(far):3} worst={w[0]:5.1f} (pin {w[1]} {w[2]} -> {w[3]})")
print("\n== Critical nets: copper length per layer (mm) and via count")
crit = ['/ADC/AINA_P', '/ADC/AINA_N', '/ADC/AINB_P', '/ADC/AINB_N', '/AFE_A/FDA_OUTP', '/AFE_A/FDA_OUTN',
        '/AFE_B/FDA_OUTP', '/AFE_B/FDA_OUTN', '/AFE_A/DIV', '/AFE_B/DIV', '/AFE_A/IN', '/AFE_B/IN',
        '/ADC/VCMA', '/ADC/VCMB', '/USB/USB_DP', '/USB/USB_DM', '/USB/OSCI', '/USB/OSCO',
        '/ADC/OSC_OUT', '/ADC/ADC_CLK', 'CLK_10M', 'FT_CLK', '/FPGA_SDRAM/SD_CLK', '/FPGA_SDRAM/SD_CLK_SRC',
        '/Power/SW', '/Power/FB_3V3', '/Power/FB_POS', '/Power/FB_NEG']
L = collections.defaultdict(lambda: collections.defaultdict(float)); V = collections.Counter()
W = collections.defaultdict(set)
for t in b.GetTracks():
    n = t.GetNetname()
    if t.GetClass() == 'PCB_VIA':
        V[n] += 1
    else:
        L[n][t.GetLayerName()] += mm(t.GetLength()); W[n].add(round(mm(t.GetWidth()), 3))
for n in crit:
    tot = sum(L[n].values())
    print(f"{n:24} {tot:6.1f}  " + ", ".join(f"{k} {v:.1f}" for k, v in sorted(L[n].items())) +
          f"  vias={V[n]}  widths={sorted(W[n])}")
print("\n== Track widths used (mm): count")
wc = collections.Counter(round(mm(t.GetWidth()), 3) for t in b.GetTracks() if t.GetClass() != 'PCB_VIA')
print(dict(sorted(wc.items())))
vc = collections.Counter((round(mm(t.GetWidth()), 3), round(mm(t.GetDrill()), 3)) for t in b.GetTracks() if t.GetClass() == 'PCB_VIA')
print("vias (dia, drill):", dict(vc))
print("\n== Footprint attributes / sides")
attr = collections.Counter(); side = collections.Counter()
for f in b.GetFootprints():
    a = f.GetAttributes()
    attr['SMD' if a & pcbnew.FP_SMD else 'THT' if a & pcbnew.FP_THROUGH_HOLE else 'unspecified'] += 1
    side[f.GetLayerName()] += 1
print(dict(attr), dict(side))
print("\n== Silkscreen stroke widths (footprint graphics), count")
sw = collections.Counter()
for f in b.GetFootprints():
    for g in f.GraphicalItems():
        if g.GetLayerName() in ('F.Silkscreen', 'B.Silkscreen') and g.GetClass() != 'PCB_TEXT':
            sw[round(mm(g.GetWidth()), 3)] += 1
print(dict(sw))
tw = collections.Counter()
for f in b.GetFootprints():
    for t in [f.Reference()]:
        tw[(round(mm(t.GetTextHeight()), 2), round(mm(t.GetTextThickness()), 3), t.IsVisible())] += 1
print("ref text (height, thickness, visible):", dict(tw))
print("\n== U101/U201 +4V pads and tracks touching them")
for f in b.GetFootprints():
    if f.GetReference() in ('U101', 'U201'):
        for p in f.Pads():
            if p.GetNetname() == '+4V':
                q = p.GetPosition(); hits = 0
                for t in b.GetTracks():
                    if t.GetNetname() == '+4V' and t.GetClass() != 'PCB_VIA' and p.HitTest(t.GetStart()) or \
                       t.GetNetname() == '+4V' and t.GetClass() != 'PCB_VIA' and p.HitTest(t.GetEnd()):
                        hits += 1
                print(f"  {f.GetReference()}.{p.GetNumber()} at ({mm(q.x):.3f},{mm(q.y):.3f}) track ends inside pad: {hits}")
