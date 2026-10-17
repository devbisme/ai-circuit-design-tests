"""
DSN export / SES import around Freerouting, then zone fill.

    python3.11 route.py export dual_adc.kicad_pcb dual_adc.dsn
    python3.11 route.py import dual_adc.kicad_pcb dual_adc.ses
    python3.11 route.py relink dual_adc.kicad_pcb dual_adc_sch.net
"""
import sys
import pcbnew as pn

MM = pn.FromMM
cmd, pcb, other = sys.argv[1:4]
board = pn.LoadBoard(pcb)

if cmd == "export":
    # Drop the copper pours added after routing (keep the In1 GND plane) so
    # Freerouting sees only the plane, not full-board pours on routing layers.
    for z in list(board.Zones()):
        if z.GetLayer() != pn.In1_Cu:
            board.Remove(z)
    ok = pn.ExportSpecctraDSN(board, other)
    print("exported" if ok else "EXPORT FAILED", other)

elif cmd == "relink":
    # Point each footprint at its schematic symbol (sheet path + symbol UUID)
    # using the netlist exported from the current schematic.
    from make_pcb import read_netlist
    from compare_nets import sexp, find, get
    comps, _ = read_netlist(other)
    # Symbol fields (description, datasheet, user fields) to copy onto the
    # footprints so DRC's schematic-parity check sees matching fields.
    fields = {}
    root = sexp(open(other).read())
    for c in find(find(root, "components")[0], "comp"):
        f = {"Description": get(c, "description") or "",
             "Datasheet": get(c, "datasheet") or ""}
        for fl in find(find(c, "fields")[0], "field") if find(c, "fields") else []:
            name = get(fl, "name")
            if name not in ("Footprint", "Reference", "Value"):
                f[name] = fl[2] if len(fl) > 2 else ""
        fields[get(c, "ref")] = f
    n = 0
    for fp in board.GetFootprints():
        c = comps.get(fp.GetReference())
        if c and c["ts"]:
            fp.SetPath(pn.KIID_PATH(c["sheet_ts"] + c["ts"]))
            n += 1
        for name, val in fields.get(fp.GetReference(), {}).items():
            fp.SetField(name, val)
            fld = fp.GetField(name)
            if fld is not None and name not in ("Reference", "Value"):
                fld.SetVisible(False)
    board.Save(pcb)
    print(f"relinked {n} footprints")

elif cmd == "import":
    ok = pn.ImportSpecctraSES(board, other)
    print("imported" if ok else "IMPORT FAILED", other)
    # GND pours on the outer layers and In2 to fill unused copper; In1 is
    # already a solid GND plane.
    gnd = board.FindNet("GND")
    existing = {z.GetLayer() for z in board.Zones()}
    W, H = 140.0, 95.0
    for layer, prio in ((pn.F_Cu, 1), (pn.B_Cu, 1), (pn.In2_Cu, 1)):
        if layer in existing:
            continue
        z = pn.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(gnd)
        z.SetAssignedPriority(prio)
        z.SetLocalClearance(MM(0.25))
        z.SetMinThickness(MM(0.2))
        z.SetPadConnection(pn.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(MM(0.3))
        z.SetThermalReliefSpokeWidth(MM(0.3))
        z.SetIslandRemovalMode(pn.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)):
            ol.Append(MM(x), MM(y))
        board.Add(z)
    pn.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(pcb)
    print("zones filled, saved", pcb)
