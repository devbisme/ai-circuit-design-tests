"""Build project library lib/dual_adc.kicad_sym with flattened (no `extends`) copies of
KiCad 10 library symbols.  kcaa 0.2.7 returns 0 pins for derived symbols, so every
symbol used in this design goes through here."""
import copy, os, sys
from sexp import parse, dump, find, find1, Q

LIBROOT = "/home/devb/bin/kicad10-root/usr/share/kicad/symbols"

def load(lib, name):
    path = f"{LIBROOT}/{lib}.kicad_symdir/{name}.kicad_sym"
    tree = parse(open(path).read())
    for s in find(tree, "symbol"):
        if s[1] == name:
            return s
    raise KeyError(name)

def flatten(lib, name):
    sym = load(lib, name)
    ext = find1(sym, "extends")
    if not ext:
        return copy.deepcopy(sym)
    base = flatten(lib, ext[1])
    out = [ "symbol", Q(name) ]
    dprops = {p[1]: p for p in find(sym, "property")}
    for e in base[2:]:
        if isinstance(e, list) and e[0] == "property" and e[1] in dprops:
            out.append(copy.deepcopy(dprops.pop(e[1])))
        elif isinstance(e, list) and e[0] == "symbol":   # unit sub-symbols
            u = copy.deepcopy(e); u[1] = Q(name + u[1][len(base[1]):]); out.append(u)
        else:
            out.append(copy.deepcopy(e))
    # derived-only properties go before the first unit
    idx = next(i for i, e in enumerate(out) if isinstance(e, list) and e[0] == "symbol")
    for p in dprops.values():
        out.insert(idx, copy.deepcopy(p)); idx += 1
    return out

SYMBOLS = [l.split() for l in """
Analog_ADC LTC2290xUP
FPGA_Lattice ICE40HX4K-TQ144
Memory_RAM MT48LC16M16A2TG
Interface_USB FT232H
Memory_EEPROM 93LCxxBxxOT
Memory_Flash W25Q32JVSS
Amplifier_Difference THS4521IDGK
Amplifier_Operational OPA810xDBV
Regulator_SwitchedCapacitor TPS60403DBV
Regulator_Switching TLV62569DBV
Regulator_Linear LP5907MFX-3.3
Regulator_Linear TLV73312PDBV
Oscillator ASE-xxxMHz
Power_Protection USBLC6-2SC6
Diode BAV99
Connector USB_B
Connector Conn_Coaxial
Connector_Generic Conn_02x05_Odd_Even
Device R
Device C
Device C_Polarized
Device C_Trim
Device L
Device FerriteBead_Small
Device Polyfuse
Device Crystal_GND24
Device LED
Mechanical MountingHole
""".strip().splitlines()]

if __name__ == "__main__":
    out = ["kicad_symbol_lib", ["version", "20251024"], ["generator", Q("flatten_symbols")],
           ["generator_version", Q("10.0")]]
    for lib, name in SYMBOLS:
        sym = flatten(lib, name)
        # kcaa 0.2.7 copies `(property private "KLC_S3.3" "...")` into schematics without
        # its value, which KiCad then refuses to load.  These are KLC notes; drop them.
        sym = [e for e in sym if not (isinstance(e, list) and len(e) > 1 and e[0] == "property"
                                      and e[1] == "private")]
        out.append(sym)
    os.makedirs("../lib", exist_ok=True)
    open("../lib/dual_adc.kicad_sym", "w").write(dump(out) + "\n")
    print(f"wrote {len(SYMBOLS)} symbols")
