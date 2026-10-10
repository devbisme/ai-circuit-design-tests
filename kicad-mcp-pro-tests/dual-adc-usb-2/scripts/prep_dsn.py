"""Prepare the KiCad-exported DSN for Freerouting.

* In1.Cu (GND plane) becomes a 'power' layer so no signals are routed on it.
* The GND net is cut down to a single pin: all GND pads already reach In1 through the
  locked fanout (exported as fixed wiring), and Freerouting does not understand planes.
Usage: prep_dsn.py in.dsn out.dsn
"""
import re, sys
t = open(sys.argv[1]).read()
t = re.sub(r'(\(layer In1\.Cu\s*\(type )signal', r'\1power', t)
m = re.search(r'\(net GND\s*\(pins ([^)]*)\)', t)
pins = m.group(1).split()
t = t[:m.start(1)] + pins[0] + t[m.end(1):]
open(sys.argv[2], 'w').write(t)
print(f'GND pins {len(pins)} -> 1; In1.Cu set to power')
