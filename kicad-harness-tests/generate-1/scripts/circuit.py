"""Tiny netlist DSL: parts with pin->net maps, grouped into schematic sheets."""
from sexp import load_symbol, symbol_pins

FP = dict(
    R0603="Resistor_SMD:R_0603_1608Metric",
    R1206="Resistor_SMD:R_1206_3216Metric",
    C0603="Capacitor_SMD:C_0603_1608Metric",
    C0805="Capacitor_SMD:C_0805_2012Metric",
    C1206="Capacitor_SMD:C_1206_3216Metric",
    L0805="Inductor_SMD:L_0805_2012Metric",
    LED0603="LED_SMD:LED_0603_1608Metric",
    RARR="Resistor_SMD:R_Array_Convex_4x0603",
)


class Part:
    def __init__(self, ref, lib_id, value, footprint, sheet, pins, nc=(), fields=None):
        self.ref, self.lib_id, self.value, self.footprint, self.sheet = ref, lib_id, value, footprint, sheet
        self.pins = {str(k): v for k, v in pins.items()}   # pin number -> net name
        self.fields = fields or {}
        self.sym = load_symbol(lib_id)
        self.libpins = symbol_pins(self.sym)
        nums = {p["number"] for p in self.libpins}
        bad = set(self.pins) - nums
        if bad:
            raise ValueError(f"{ref}: pins {bad} not in {lib_id}")
        for p in self.libpins:
            n = p["number"]
            if n in self.pins:
                continue
            if p["type"] == "no_connect" or n in nc:
                self.pins[n] = None        # explicit no-connect
            else:
                raise ValueError(f"{ref}: pin {n} ({p['name']}) of {lib_id} unassigned")


class Circuit:
    def __init__(self):
        self.parts = []
        self.sheet = "Root"
        self.group = None      # placement cluster name for parts added next
        self._cnt = {}

    def ref(self, prefix):
        self._cnt[prefix] = self._cnt.get(prefix, 0) + 1
        return f"{prefix}{self._cnt[prefix]}"

    def add(self, prefix, lib_id, value, footprint, pins, nc=(), **fields):
        p = Part(self.ref(prefix), lib_id, value, footprint, self.sheet, pins, nc, fields)
        p.group = self.group or self.sheet
        self.parts.append(p)
        return p

    # two-terminal helpers -------------------------------------------------
    def R(self, value, a, b, fp="R0603", **kw):
        return self.add("R", "Device:R", value, FP.get(fp, fp), {1: a, 2: b}, **kw)

    def C(self, value, a, b="GND", fp="C0603", **kw):
        return self.add("C", "Device:C", value, FP.get(fp, fp), {1: a, 2: b}, **kw)

    def FB(self, a, b, value="600R@100MHz"):
        return self.add("FB", "Device:FerriteBead_Small", value, FP["L0805"], {1: a, 2: b})

    def LED(self, anode, cathode, value):
        return self.add("D", "Device:LED", value, FP["LED0603"], {1: cathode, 2: anode})

    def decap(self, net, values):
        for v in values:
            self.C(v, net, "GND", fp="C0805" if v in ("10u", "22u", "4.7u") else "C0603")

    def nets(self):
        d = {}
        for p in self.parts:
            for n, net in p.pins.items():
                if net:
                    d.setdefault(net, []).append((p.ref, n))
        return d
