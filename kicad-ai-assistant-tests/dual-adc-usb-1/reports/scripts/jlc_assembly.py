"""Convert KiCad BOM/pos CSVs to JLCPCB format. THT connectors and mounting holes are split out."""
import csv, sys
THT = {'J101', 'J201', 'J501', 'J601'}   # through-hole: BNC x2, USB-B, 2x5 header
skip = lambda r: r in THT or r.startswith('H')
bom_in, pos_in, out = sys.argv[1:4]
rows, tht = [], []
for r in csv.DictReader(open(bom_in)):
    refs = r['Designator'].split(',')
    smd = [x for x in refs if not skip(x)]
    tht += [(x, r['Comment'], r['Footprint']) for x in refs if x in THT]
    if smd:
        rows.append([r['Comment'], ','.join(smd), r['Footprint'].split(':')[-1], '', len(smd)])
with open(f'{out}/dual_adc_usb_BOM_JLCPCB.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #', 'Quantity']); w.writerows(rows)
n = 0
with open(f'{out}/dual_adc_usb_CPL_JLCPCB.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    for r in csv.DictReader(open(pos_in)):
        if skip(r['Ref']): continue
        w.writerow([r['Ref'], f"{float(r['PosX']):.4f}mm", f"{float(r['PosY']):.4f}mm",
                    'Top' if r['Side'] == 'top' else 'Bottom', f"{float(r['Rot']):.1f}"]); n += 1
with open(f'{out}/THT_parts_not_in_assembly.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Designator', 'Value', 'Footprint']); w.writerows(sorted(tht))
print(f"BOM lines {len(rows)}, BOM parts {sum(r[4] for r in rows)}, CPL rows {n}, THT {len(tht)}")
