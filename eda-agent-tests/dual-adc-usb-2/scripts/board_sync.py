"""Bring a board's footprints in line with the plan + written schematic (KiCad python).

Used by build_pcb.py on the eda-agent board, and standalone on a routed board
after the schematic is regenerated (sch_writer.py makes new UUIDs each run):

  * footprint whose lib:name differs from the plan -> swapped for the library
    copy (position, rotation and pad nets kept);
  * full lib:name FPID, value, schematic symbol path, sheet name/file;
  * KiCad's "unconnected-(...)" nets on no-connect pins;
  * symbol fields (Description, Datasheet, MPN, ...) and BOM exclusion.

usage (standalone): python3.11 board_sync.py [board.kicad_pcb]
"""

import json
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import symlib  # noqa: E402

ROOT = os.path.join(HERE, "..")
FPDIR = os.path.expanduser("~/bin/kicad10-root/share/kicad/footprints")


def symbol_paths():
    """refdes -> (path, sheetname, sheetfile) from the written schematic."""
    root = symlib.parse(open(os.path.join(ROOT, "kicad", "dual_adc.kicad_sch")).read())
    out = {}
    for sh in symlib.find(root, "sheet"):
        suid = str(symlib.find1(sh, "uuid")[1])
        props = {str(p[1]): str(p[2]) for p in symlib.find(sh, "property")}
        sub = symlib.parse(open(os.path.join(ROOT, "kicad", props["Sheetfile"])).read())
        for s in symlib.find(sub, "symbol"):
            ref = next(str(p[2]) for p in symlib.find(s, "property") if p[1] == "Reference")
            unit = int(symlib.find1(s, "unit")[1])
            if ref.startswith("#"):
                continue
            if ref not in out or unit == 1:
                out[ref] = (f"/{suid}/{symlib.find1(s, 'uuid')[1]}",
                            props["Sheetname"], props["Sheetfile"])
    return out


def replace_footprint(board, old, fpid):
    lib, name = fpid.split(":")
    new = pcbnew.FootprintLoad(os.path.join(FPDIR, lib + ".pretty"), name)
    new.SetReference(old.GetReference())
    new.SetValue(old.GetValue())
    new.SetPosition(old.GetPosition())
    new.SetOrientation(old.GetOrientation())
    netmap = {p.GetNumber(): p.GetNet() for p in old.Pads()}
    for p in new.Pads():
        if p.GetNumber() in netmap:
            p.SetNet(netmap[p.GetNumber()])
    board.Remove(old)
    new.thisown = 0             # the board owns it; Python must not free it
    board.Add(new)
    return new


def sym_fields(part):
    lib, name = part["lib_ref"].split(":")
    s = symlib.load_symbol(lib, name)
    f = {"Description": symlib.prop(s, "Description") or "",
         "Datasheet": part.get("datasheet_url") or symlib.prop(s, "Datasheet") or ""}
    if part.get("mpn"):
        f["MPN"] = part["mpn"]
    if part.get("manufacturer"):
        f["Manufacturer"] = part["manufacturer"]
    if (part.get("role") or "").startswith("tolerance"):
        f["Tolerance"] = part["role"].split()[-1]
    in_bom = symlib.find1(s, "in_bom")
    return f, (str(in_bom[1]) if in_bom else "yes") == "yes"


def sync(board, force_replace=()):
    """Returns (fps, needs_resync). After a footprint swap, KiCad 10's SWIG
    wrappers misbehave in this process (GetFields() returns a bare
    SwigPyObject), so a swap only swaps; the caller saves the board and runs
    this script in a fresh process (resync()) to finish the job."""
    plan = json.load(open(os.path.join(ROOT, "plan", "dual_adc_plan.json")))
    parts = {p["refdes"]: p for p in plan["parts"]}
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    swapped = False
    for ref, fp in list(fps.items()):
        want = parts[ref]["footprint"]
        have = str(fp.GetFPID().GetUniStringLibId())
        if ref in force_replace or (":" in have and have != want):
            replace_footprint(board, fp, want)
            swapped = True
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    if swapped:
        return fps, True
    paths = symbol_paths()
    for ref, fp in fps.items():
        lib, name = parts[ref]["footprint"].split(":")
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetValue(parts[ref].get("value", ""))
        path, sname, sfile = paths[ref]
        fp.SetPath(pcbnew.KIID_PATH(path))
        fp.SetSheetname(sname)
        fp.SetSheetfile(sfile)
        f, bom = sym_fields(parts[ref])
        for k, v in f.items():
            flds = fp.GetFields()
            if not hasattr(flds, "__iter__"):
                raise RuntimeError(f"GetFields broken on {ref} key {k}")
            have = [fl for fl in flds if fl.GetName() == k]
            if have:
                have[0].SetText(v)
            else:
                fl = pcbnew.PCB_FIELD(fp, pcbnew.FIELD_T_USER, k)
                fl.SetText(v)
                fl.SetLayer(pcbnew.F_Fab)
                fl.thisown = 0          # the footprint owns it now
                fp.Add(fl)
            for fl in fp.GetFields():
                if fl.GetName() == k:
                    fl.SetVisible(False)
        fp.SetExcludedFromBOM(not bom)
    # No-connect pins get KiCad's "unconnected-(...)" nets.
    netl = symlib.parse(open(os.path.join(ROOT, "kicad", "dual_adc.net")).read())
    for n in symlib.find1(netl, "nets")[1:]:
        name = str(symlib.find1(n, "name")[1])
        if not name.startswith("unconnected-"):
            continue
        ni = board.FindNet(name)
        if ni is None:
            ni = pcbnew.NETINFO_ITEM(board, name)
            board.Add(ni)
        for x in symlib.find(n, "node"):
            ref, pin = str(symlib.find1(x, "ref")[1]), str(symlib.find1(x, "pin")[1])
            for p in fps[ref].Pads():
                if p.GetNumber() == pin:
                    p.SetNet(ni)
    return fps, False


def resync(pcb):
    """Run the full sync on a saved board in a fresh KiCad python process."""
    import subprocess
    subprocess.run([sys.executable, os.path.abspath(__file__), pcb], check=True)


if __name__ == "__main__":
    pcb = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "kicad", "dual_adc.kicad_pcb")
    b = pcbnew.LoadBoard(pcb)
    _, again = sync(b)
    b.Save(pcb)
    print("swapped footprints; run again to sync fields" if again else "synced", pcb)
