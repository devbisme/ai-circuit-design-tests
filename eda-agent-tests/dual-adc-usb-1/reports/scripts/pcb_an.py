import pcbnew, math, collections, sys
b=pcbnew.LoadBoard(sys.argv[1]); mm=pcbnew.ToMM
pads=[]
for f in b.GetFootprints():
    for p in f.Pads():
        if not p.IsOnCopperLayer(): continue
        pos=p.GetPosition(); pads.append((f.GetReference(),p.GetNumber(),p.GetNetname(),mm(pos.x),mm(pos.y),p.GetPinFunction()))
caps=collections.defaultdict(list)
for r,n,net,x,y,fn in pads:
    if r.startswith('C'): caps[net].append((r,x,y))
print('== nearest bypass cap to each IC supply pin (mm)')
rails={'+3V3','+3V0','+1V2','+4V','VEE','+5V','/USB/V1V8_FT','/FPGA_SDRAM/VCCPLL0','/FPGA_SDRAM/VCCPLL1','/ADC/REFHA','/ADC/REFLA','/ADC/REFHB','/ADC/REFLB','/ADC/VCMA','/ADC/VCMB'}
worst=collections.defaultdict(list)
for r,n,net,x,y,fn in pads:
    if r[0] in 'UX' and net in rails:
        d=min(((math.hypot(x-cx,y-cy),cr) for cr,cx,cy in caps[net]),default=(99,'-'))
        worst[r].append((round(d[0],1),n,fn,net,d[1]))
for r in sorted(worst):
    w=sorted(worst[r],reverse=True)
    print(r, 'max',w[0], '| min',w[-1][0], '| >5mm:',sum(1 for a in w if a[0]>5),'/',len(w))
print('== crystal / caps')
for ref in ['C502','C503','C401','C402','C403','C404','C405','C406','C407','C408','C409','C410','C411','C103','C203','C106','C206']:
    f=b.FindFootprintByReference(ref); 
    for p in f.Pads():
        net=p.GetNetname()
        if net=='GND': continue
        # nearest non-cap pad on same net
        ds=[(math.hypot(mm(p.GetPosition().x)-x,mm(p.GetPosition().y)-y),rr+'.'+nn) for rr,nn,nt,x,y,fn in pads if nt==net and rr[0] in 'UXYJ']
        if ds: print(ref,f.GetValue(),net,'nearest IC pad %.1f mm'%min(ds)[0],min(ds)[1])
print('== per-net routing')
tr=collections.defaultdict(lambda:collections.defaultdict(float)); vias=collections.Counter(); widths=collections.defaultdict(set)
for t in b.GetTracks():
    n=t.GetNetname()
    if t.Type()==pcbnew.PCB_VIA_T: vias[n]+=1
    else: tr[n][t.GetLayerName()]+=mm(t.GetLength()); widths[n].add(round(mm(t.GetWidth()),3))
for n in ['/USB/USB_DP','/USB/USB_DM','/ADC/AINA_P','/ADC/AINA_N','/ADC/AINB_P','/ADC/AINB_N','/AFE_A/FDA_OUTP','/AFE_A/FDA_OUTN','/AFE_B/FDA_OUTP','/AFE_B/FDA_OUTN','/AFE_A/DIV','/AFE_B/DIV','/ADC/VCMA','/ADC/VCMB','/ADC/ADC_CLK','/ADC/OSC_OUT','CLK_10M','FT_CLK','/FPGA_SDRAM/SD_CLK','/FPGA_SDRAM/SD_CLK_SRC','/USB/OSCI','/USB/OSCO','/Power/SW','+5V','+4V','VEE','+3V0','+1V2','/USB/VBUS']:
    print(n,{k:round(v,1) for k,v in tr[n].items()},'vias',vias[n],'w',sorted(widths[n]))
print('== min track width count', collections.Counter(round(mm(t.GetWidth()),3) for t in b.GetTracks() if t.Type()!=pcbnew.PCB_VIA_T))
print('== silk line widths', collections.Counter(round(mm(g.GetWidth()),3) for f in b.GetFootprints() for g in f.GraphicalItems() if g.GetLayerName() in ('F.Silkscreen','B.Silkscreen') and g.Type()==pcbnew.PCB_SHAPE_T))
th=collections.Counter()
for f in b.GetFootprints():
    for fld in [f.Reference()]:
        th[(round(mm(fld.GetTextHeight()),2),round(mm(fld.GetTextThickness()),3), fld.IsVisible(), fld.GetLayerName())]+=1
print('== ref text', th)
ec=b.GetBoardEdgesBoundingBox(); print('edge',mm(ec.GetLeft()),mm(ec.GetTop()),mm(ec.GetRight()),mm(ec.GetBottom()))
for r in ['J101','J201','J501','J601','H1','H2','H3','H4','U301','U601','U602','U502','U101','U201','U102','U202','X301','Y501','U401','U404','U403','U402']:
    f=b.FindFootprintByReference(r); bb=f.GetCourtyard(pcbnew.F_CrtYd).BBox() if hasattr(f,'GetCourtyard') else f.GetBoundingBox()
    print(r, f.GetValue(), 'pos',round(mm(f.GetPosition().x),1),round(mm(f.GetPosition().y),1),'rot',f.GetOrientationDegrees(),'side', 'B' if f.IsFlipped() else 'F','crtyd x',round(mm(bb.GetLeft()),1),round(mm(bb.GetRight()),1),'y',round(mm(bb.GetTop()),1),round(mm(bb.GetBottom()),1), 'attr', f.GetAttributes())
ds=b.GetDesignSettings(); print('mask exp',mm(ds.m_SolderMaskExpansion),'min web',mm(ds.m_SolderMaskMinWidth))
