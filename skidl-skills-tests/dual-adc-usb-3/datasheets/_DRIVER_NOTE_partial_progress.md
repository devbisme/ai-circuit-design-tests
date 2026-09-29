# Driver note — phase 4 was interrupted (not an artifact)

Written by the `/new-circuit` driver, not by the datasheet-librarian.

The first phase-4 run terminated mid-work on an account spend/rate limit
(HTTP 429) at 2026-09-09 ~23:42 local. It had already downloaded the PDFs and
`.txt` extracts present in this directory, but wrote **no `<MPN>_SUMMARY.md`
files and no `handoffs/04_datasheets.md`**, so phase 4 never passed its gate.

`UG803_raw.txt` was an in-progress extraction of the GW1NR-9 pinout table and
should be treated as untrusted scratch — re-extract rather than rely on it.

A resumed librarian should reuse the PDFs already on disk instead of
re-downloading them, and delete this note when the phase completes.
