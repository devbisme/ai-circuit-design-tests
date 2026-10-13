"""Grouped BOM (CSV) from design.py."""
import csv, collections, os
from design import PARTS
FP_DEFAULT = {"LTC2290xUP": "Package_DFN_QFN:QFN-64-1EP_9x9mm_P0.5mm_EP7.15x7.15mm",
              "ICE40HX4K-TQ144": "Package_QFP:TQFP-144_20x20mm_P0.5mm",
              "MT48LC16M16A2TG": "Package_SO:TSOP-II-54_22.2x10.16mm_P0.8mm",
              "W25Q32JVSS": "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm",
              "THS4521IDGK": "Package_SO:VSSOP-8_3x3mm_P0.65mm",
              "93LCxxBxxOT": "Package_TO_SOT_SMD:SOT-23-6", "USBLC6-2SC6": "Package_TO_SOT_SMD:SOT-23-6",
              "BAV99": "Package_TO_SOT_SMD:SOT-23",
              "ASE-xxxMHz": "Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm"}
groups = collections.OrderedDict()
for ref, p in sorted(PARTS.items(), key=lambda kv: (kv[0][0], int(''.join(c for c in kv[0] if c.isdigit()) or 0))):
    if p["sym"] == "MountingHole":
        continue
    fp = p["fp"] or FP_DEFAULT.get(p["sym"], "Package_TO_SOT_SMD:SOT-23-5")
    groups.setdefault((p["value"], fp), []).append(ref)
out = os.path.join(os.path.dirname(__file__), "..", "dual_adc_bom.csv")
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Qty", "Value", "Footprint", "References", "Description"])
    for (val, fp), refs in groups.items():
        w.writerow([len(refs), val, fp, " ".join(refs), PARTS[refs[0]]["desc"]])
print(len(groups), "lines,", sum(len(r) for r in groups.values()), "parts")
