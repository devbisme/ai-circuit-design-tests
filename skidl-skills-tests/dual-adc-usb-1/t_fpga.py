import sys; sys.path.insert(0, "/home/devb/projects/AI/skidl-skills-test/circuits/dual_adc_usb")
from skidl import *
from fpga_ice40 import fpga_ice40
n = lambda s: Net(s)
fpga_ice40(n("V3V3_D"), n("V1V2_CORE"), n("GND"),
    Bus("adcDataA",12), Bus("adcDataB",12), n("adcOfA"), n("adcOfB"),
    n("adcShdn"), n("adcOeBar"), n("xoClkFpga"),
    Bus("sramAddr",21), Bus("sramData",16), n("sramCeBar"), n("sramOeBar"), n("sramWeBar"),
    Bus("fifoData",8), n("fifoRxfBar"), n("fifoTxeBar"), n("fifoRdBar"),
    n("fifoWrBar"), n("fifoOeBar"), n("ftClk60"),
    n("cfgSck"), n("cfgMosi"), n("cfgMiso"), n("cfgCsBar"),
    n("fpgaCresetBar"), n("fpgaCdone"), n("modeStrap"),
    n("probeCompDrv"), n("extTrig"), n("ledStatus"), n("ledActivity"))
u = default_circuit.parts[0]
used = set()
for p in u.pins:
    if p.net is not None or p.do_erc is False:
        pass
unconn = [p.num for p in u.pins if not p.is_connected()]
print("PARTS:", len(default_circuit.parts))
print("UNCONNECTED U10 pins:", unconn)
