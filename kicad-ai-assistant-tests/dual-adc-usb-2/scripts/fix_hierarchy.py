"""Post-process kcaa output: fix hierarchical instance data.

kcaa 0.2.7 add_sheet_symbol/add_symbol_to_schematic write child-sheet symbol instance
paths as "/<child-file-uuid>" and give every sheet page "1".  KiCad expects symbol paths
"/<root-uuid>/<sheet-symbol-uuid>" and sheet-symbol paths "/<root-uuid>".
Text-level rewrite so the rest of each file stays byte-identical.
"""
import os, re, sys
from sexp import parse, find, find1

PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
root_f = os.path.join(PROJ, "dual_adc.kicad_sch")
root_txt = open(root_f).read()
rt = parse(root_txt)
root_uuid = str(find1(rt, "uuid")[1])
page = 2
for sh in find(rt, "sheet"):
    suuid = str(find1(sh, "uuid")[1])
    sfile = [p[2] for p in find(sh, "property") if p[1] in ("Sheetfile", "Sheet file")][0]
    old = re.escape(f'(path "/{suuid}"') + r'\s*\(page "\d+"\)'
    root_txt, n = re.subn(old, f'(path "/{root_uuid}" (page "{page}")', root_txt)
    cf = os.path.join(PROJ, sfile)
    ct = open(cf).read()
    cuuid = str(find1(parse(ct), "uuid")[1])
    ct, m = re.subn(re.escape(f'(path "/{cuuid}"'), f'(path "/{root_uuid}/{suuid}"', ct)
    open(cf, "w").write(ct)
    print(f"{sfile}: page {page}, {m} symbol instance paths fixed, sheet path fixed={n}")
    page += 1
open(root_f, "w").write(root_txt)
