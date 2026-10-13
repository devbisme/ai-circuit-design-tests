"""Dump each non-passive part's pin->net map from a KiCad XML netlist."""
import sys, collections, xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
pins = collections.defaultdict(list)
for net in root.iter('net'):
    nn = net.get('name')
    nodes = net.findall('node')
    for n in nodes:
        pins[n.get('ref')].append((n.get('pin'), n.get('pinfunction') or '', nn, len(nodes)))
vals = {c.get('ref'): c.findtext('value') for c in root.iter('comp')}
key = lambda p: (int(p[0]) if p[0].isdigit() else 999, p[0])
for ref in sorted(pins):
    if ref[0] in 'UQXYJD' or ref.startswith('FB'):
        print(f"== {ref} {vals.get(ref)}")
        for p in sorted(pins[ref], key=key):
            print(f"   {p[0]:>4} {p[1]:<22} {p[2]}  ({p[3]})")
print("\n== passives")
for ref in sorted(pins):
    if ref[0] in 'RCL' and not ref.startswith('FB'):
        print(f"{ref:6} {vals.get(ref):<14} " + " | ".join(f"{p[2]}" for p in sorted(pins[ref], key=key)))
