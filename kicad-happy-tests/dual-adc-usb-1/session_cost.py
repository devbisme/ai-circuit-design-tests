#!/usr/bin/env python3
"""Summarise token usage and equivalent API cost for a Claude Code session.

Claude Code does not write a cost figure to disk, but it does write every
assistant message's `usage` block to the session transcript. This adds those up
and prices them, for the main session and for any subagents it spawned.

    ./session_cost.py                          # newest session in this project
    ./session_cost.py --session <uuid>         # a specific session
    ./session_cost.py --json cost.json         # machine-readable output too
    ./session_cost.py --all                    # every session in this project

Subagent usage is NOT in the main transcript. It lives in
`<session>/subagents/*.jsonl` next to it (older versions also symlinked the files
into the scratchpad `tasks/` directory), and both places are scanned. Each file is
scanned once, whichever path reaches it. Only aggregates are printed; transcript
contents are never echoed.

Claude Code writes one JSONL line per content block of an assistant message, and
every one of those lines repeats the message's `usage`. The cache and input
fields are identical across those lines, but `output_tokens` is cumulative while
streaming, so only the last line has the true count. Usage is therefore counted once
per `message.id`, taking each field's maximum. Summing every line over-counts by about
2x; keeping only the first line under-counts output.

The dollar figure is the equivalent first-party API cost. On a Pro/Max
subscription it is NOT what you were billed — usage is included in the
subscription — so treat it as "what this would have cost on the API".
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Anthropic first-party API rates, USD per million tokens.
# Cache write = 1.25x input (5-minute TTL) or 2x (1-hour TTL); cache read = 0.1x input.
# Optional "cr": the model's cache-read price, when it isn't CACHE_READ_MULT x input.
PRICES = {
    "claude-opus-5-5":   {"in": 4.00,  "out": 20.00, "cr": 0.20},
    "claude-opus-5":     {"in": 5.00,  "out": 25.00},
    "claude-opus-4-8":   {"in": 5.00,  "out": 25.00},
    "claude-fable-5-1":  {"in": 10.00, "out": 50.00, "cr": 0.25},
    "claude-sonnet-5":   {"in": 2.00,  "out": 10.00},
    "claude-sonnet-4-6": {"in": 3.00,  "out": 15.00},
    "claude-haiku-4-5":  {"in": 1.00,  "out": 5.00},
}
CACHE_WRITE_MULT = 1.25
CACHE_WRITE_1H_MULT = 2.0
CACHE_READ_MULT = 0.10


def price_for(model: str) -> dict | None:
    if model in PRICES:
        return PRICES[model]
    # Tolerate dated suffixes; try longest keys first so "claude-opus-5-5" is not
    # priced as "claude-opus-5".
    for known in sorted(PRICES, key=len, reverse=True):
        if model.startswith(known):
            return PRICES[known]
    return None


USAGE_KEYS = ("input_tokens", "output_tokens", "cache_creation_input_tokens",
              "cache_read_input_tokens", "cache_creation_1h_tokens")


def scan(path: Path, by_id: dict) -> int:
    """Merge one JSONL transcript's usage into by_id. Returns lines with usage.

    by_id maps message id -> (model, Counter). The same id may recur in this file
    or another; each field keeps its maximum.
    """
    n = 0
    try:
        fh = path.open(errors="replace")
    except OSError:
        return 0
    with fh:
        for line in fh:
            if '"usage"' not in line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = d.get("message")
            if not isinstance(msg, dict):
                continue
            u = msg.get("usage")
            if not isinstance(u, dict):
                continue
            model = msg.get("model") or "unknown"
            if model == "<synthetic>":       # local error/stub messages, unbilled
                continue
            mid = msg.get("id") or f"{path}:{n}"   # no id: count the line on its own
            vals = {k: u.get(k) for k in USAGE_KEYS[:4]}
            cc = u.get("cache_creation")
            if isinstance(cc, dict):
                vals["cache_creation_1h_tokens"] = cc.get("ephemeral_1h_input_tokens")
            _, acc = by_id.setdefault(mid, (model, Counter()))
            for key, v in vals.items():
                if isinstance(v, int) and v > acc[key]:
                    acc[key] = v
            n += 1
    return n


def cost_of(acc: Counter, model: str) -> float | None:
    p = price_for(model)
    if p is None:
        return None
    cw_1h = acc["cache_creation_1h_tokens"]
    cw_5m = acc["cache_creation_input_tokens"] - cw_1h
    return (
        acc["input_tokens"] / 1e6 * p["in"]
        + acc["output_tokens"] / 1e6 * p["out"]
        + cw_5m / 1e6 * p["in"] * CACHE_WRITE_MULT
        + cw_1h / 1e6 * p["in"] * CACHE_WRITE_1H_MULT
        + acc["cache_read_input_tokens"] / 1e6 * p.get("cr", p["in"] * CACHE_READ_MULT)
    )


def project_dir(cwd: Path) -> Path:
    """Claude Code's transcript dir for a working directory."""
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(cwd))
    return Path.home() / ".claude" / "projects" / slug


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", help="session UUID (default: most recent with usage)")
    ap.add_argument("--all", action="store_true", help="every session in this project")
    ap.add_argument("--json", metavar="FILE", help="also write JSON here")
    ap.add_argument("--cwd", default=os.getcwd(), help="project dir (default: cwd)")
    args = ap.parse_args()

    pdir = project_dir(Path(args.cwd).resolve())
    if not pdir.is_dir():
        print(f"No transcripts for {args.cwd}\n  looked in: {pdir}", file=sys.stderr)
        return 1

    sessions = sorted(pdir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    if not sessions:
        print(f"No .jsonl transcripts in {pdir}", file=sys.stderr)
        return 1
    if args.session:
        sessions = [p for p in sessions if p.stem == args.session]
        if not sessions:
            print(f"Session {args.session} not found in {pdir}", file=sys.stderr)
            return 1
    elif not args.all:
        # Most recent session that billed anything. A short later session (a
        # resume that only printed a status line) must not hide the real one.
        with_usage = [p for p in sessions if '"usage"' in p.read_text(errors="replace")]
        sessions = (with_usage or sessions)[-1:]

    by_id: dict = {}
    seen_files: set = set()
    files = 0

    def scan_once(path: Path) -> None:
        nonlocal files
        real = os.path.realpath(path)
        if real in seen_files:
            return
        seen_files.add(real)
        files += bool(scan(path, by_id))

    slug = re.sub(r"[^A-Za-z0-9]", "-", str(Path(args.cwd).resolve()))
    for s in sessions:
        scan_once(s)
        for t in sorted((s.parent / s.stem / "subagents").glob("*.jsonl")):
            scan_once(t)
        # Older layout: subagent transcripts in the scratchpad, if it still exists.
        for t in glob.glob(f"/tmp/claude-*/*/{s.stem}/tasks/*.output"):
            scan_once(Path(t))
        for t in glob.glob(f"/tmp/claude-*/{slug}/{s.stem}/tasks/*.output"):
            scan_once(Path(t))

    per_model: dict[str, Counter] = defaultdict(Counter)
    for model, acc in by_id.values():
        per_model[model].update(acc)
        per_model[model]["messages"] += 1

    total = Counter()
    for acc in per_model.values():
        total.update(acc)
    total.pop("cache_creation_1h_tokens", None)   # already inside cache_creation
    known_cost = sum(c for c in (cost_of(a, m) for m, a in per_model.items())
                     if c is not None)
    unpriced = [m for m in per_model if price_for(m) is None]

    w = 34
    print(f"Sessions:   {len(sessions)}   transcripts scanned: {files}")
    print(f"Messages:   {total['messages']:,}")
    print()
    for model, acc in sorted(per_model.items(), key=lambda kv: -kv[1]["messages"]):
        c = cost_of(acc, model)
        print(f"{model}  ({acc['messages']:,} messages)"
              + ("" if c is None else f"   ${c:,.2f}"))
        for label, key in (("input", "input_tokens"),
                           ("output", "output_tokens"),
                           ("cache write", "cache_creation_input_tokens"),
                           ("cache read", "cache_read_input_tokens")):
            print(f"    {label:<{12}} {acc[key]:>15,}")
        if acc["cache_creation_1h_tokens"]:
            print(f"      of which 1h {acc['cache_creation_1h_tokens']:>13,}")
        if c is None:
            print("    (no price on file for this model — not costed)")
    print()
    print(f"{'TOTAL tokens':<{w}} {sum(total[k] for k in ('input_tokens','output_tokens','cache_creation_input_tokens','cache_read_input_tokens')):>15,}")
    print(f"{'Equivalent API cost':<{w}} {'$' + format(known_cost, ',.2f'):>15}")
    if unpriced:
        print(f"  (excludes unpriced models: {', '.join(unpriced)})")
    print("\nOn a Pro/Max subscription this is not what you were billed —")
    print("it is what the same tokens would cost on the first-party API.")

    if args.json:
        out = {
            "sessions": [s.stem for s in sessions],
            "transcripts_scanned": files,
            "per_model": {m: dict(a) for m, a in per_model.items()},
            "totals": dict(total),
            "equivalent_api_cost_usd": round(known_cost, 4),
            "prices_usd_per_mtok": PRICES,
            "cache_write_multiplier": CACHE_WRITE_MULT,
            "cache_read_multiplier": CACHE_READ_MULT,
            "note": "Equivalent first-party API cost; not a subscription bill.",
        }
        Path(args.json).write_text(json.dumps(out, indent=2) + "\n")
        print(f"\nWrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
