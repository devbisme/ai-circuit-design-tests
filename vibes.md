# Vibes

Here I'll record various thoughts about the tools I'm testing.

* `skidl-skills` seems to do the best up-front design but it stops after creating the netlist and doesn't create a PCB.

* `konnect` is the best end-to-end tool since it can go all the way to a placed and routed PCB.

* `skidl-skills` did a better job at designing the anti-aliasing filters than `konnect`.
  `konnect` did try to re-engineer the filters after the initial schematic was done, but this seemed
  to waste tokens in having to make room by moving components and wires around to avoid collisions and establish connections.

* Combining `skidl-skills` up-front design with `konnect` backend PCB design looks like it might be the best of
  both worlds. You could probably also use `konnect` schematic design skills to create a schematic from the netlist
  output by `skidl-skills`.

* Both `skidl-skills` and `konnect` produced markedly different designs each time they were run.
  This can be an advantage because it exposes alternate ideas for a design.
  It's relatively easy to lock down desired aspects of a design just by entering constraints in the initial prompt
  (e.g., "Use an external SDRAM").

* Even if a tool doesn't give you a perfect finished board, it will show you options and constraints that you may
  not have considered. This would be especially valuable if you were designing for an application where you
  didn't have much experience.

* `skidl-tools` was able to source parts from both the installed KiCad libraries and also from
  JLCPCB, Mouser, and DigiKey using [`pcbparts-mcp`](https://github.com/Averyy/pcbparts-mcp).
  `konnect` and `copperhead` only sourced from the KiCad libraries. As a result, they missed using the
  `GW1NR-LV9QN88` FPGA with an internal SRAM large enough to buffer the signal samples and opted for
  external SDRAMs instead. `pcbparts-mcp` could probably be easily integrated into any of these tools.

* `copperhead` completed an architectural design but never produced a schematic or PCB. I stopped the test after it expended its token
  allowance over three consecutive five-hour windows. I'm not sure if this is a fault with the tool or
  if I didn't install or configure it correctly.
