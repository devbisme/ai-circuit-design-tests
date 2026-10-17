"""
Post-process the schematizer output: blank the dummy ":" footprint that SKiDL
gives PWR_FLAG symbols (avoids KiCad 'footprint_link_issues' ERC warnings).
"""
import glob

for path in glob.glob("dual_adc*.kicad_sch"):
    s = open(path).read()
    t = s.replace('(property "Footprint" ":"', '(property "Footprint" ""')
    if t != s:
        open(path, "w").write(t)
        print("fixed", path)
