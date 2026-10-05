import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
ok = pcbnew.ImportSpecctraSES(b, sys.argv[2])
print('import', ok)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[3], b)
print('tracks', len(b.GetTracks()))
