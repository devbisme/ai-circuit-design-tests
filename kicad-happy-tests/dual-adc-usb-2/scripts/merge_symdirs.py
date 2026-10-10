"""Merge KiCad 10 per-symbol .kicad_symdir libraries into single .kicad_sym files.

SKiDL's KiCad loader reads single-file symbol libraries only, so the libraries this
design uses are flattened into ./lib with their original names (Device, Analog_ADC...).
"""
import os, re, sys

SRC = "/home/devb/bin/kicad10-root/share/kicad/symbols"
DST = os.path.join(os.path.dirname(__file__), "..", "lib")
LIBS = """Device Analog_ADC FPGA_Lattice Memory_RAM Memory_Flash Memory_EEPROM Interface_USB
Amplifier_Operational Amplifier_Difference Regulator_Linear Regulator_Switching
Regulator_SwitchedCapacitor Power_Protection Diode Oscillator Connector Connector_Generic
Mechanical power""".split()

def body(text):
    # Strip the outer (kicad_symbol_lib ...) wrapper and its header fields; keep symbol blocks.
    i = text.index("(symbol ")
    j = text.rstrip().rindex(")")
    return text[i:j].rstrip()

for lib in LIBS:
    d = os.path.join(SRC, lib + ".kicad_symdir")
    files = sorted(f for f in os.listdir(d) if f.endswith(".kicad_sym"))
    head = open(os.path.join(d, files[0])).read()
    hdr = head[: head.index("(symbol ")].rstrip()
    out = [hdr]
    for f in files:
        out.append("\t" + body(open(os.path.join(d, f)).read()))
    out.append(")\n")
    with open(os.path.join(DST, lib + ".kicad_sym"), "w") as fh:
        fh.write("\n".join(out))
    print(lib, len(files))
