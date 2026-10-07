#!/usr/bin/env python3
"""Copy every Claude Code transcript behind this design into ./transcripts/.

Sources:
  * Claude Code sessions run in this directory
    (~/.claude/projects/<slug-of-this-dir>/*.jsonl, plus subagents/).
  * copperhead's own per-run logs (.copperhead/runs/<run-id>/).
  * The Claude Code sessions copperhead spawns for its claude-code backend.
    Each turn runs in a throwaway /tmp/copperhead-cc-XXXX dir, so they land in
    ~/.claude/projects/-tmp-copperhead-cc-*/. Each one is assigned to the
    copperhead run that started most recently before its first message.
    Sessions before the first run go to copperhead/unassigned/.

Layout:
  transcripts/
    INDEX.md                         per-run table: stage, sessions, tokens, cost
    claude-code/<session>.jsonl
    copperhead/<NN>_<run-id>_<stage>/
        run_transcript.jsonl, summary.md     (copperhead's own)
        cc/<seq>_<first-timestamp>_<session>.jsonl

Files are copied, not moved; re-running overwrites transcripts/. The dollar
figures are equivalent first-party API cost (same assumptions as
session_cost.py), not what a subscription bills.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from bisect import bisect_right
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
# $/Mtok for claude-opus-5-5, matching session_cost.py; cache write 1.25x, read 0.1x input.
PRICE_IN, PRICE_OUT = 4.0, 20.0
FIELDS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


def slug(path: Path) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def scan(jsonl: Path) -> tuple[str, Counter]:
    """Return (first timestamp, usage totals) for one transcript; usage is deduped by message.id."""
    first, msgs = "", {}
    for line in jsonl.open(errors="replace"):
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = o.get("timestamp") or ""
        if ts and (not first or ts < first):
            first = ts
        m = o.get("message") or {}
        u = m.get("usage")
        if o.get("type") != "assistant" or not u:
            continue
        d = msgs.setdefault(m.get("id") or id(o), Counter())
        for f in FIELDS:
            d[f] = max(d[f], u.get(f) or 0)
    tot = Counter()
    for d in msgs.values():
        tot.update(d)
    tot["messages"] = len(msgs)
    return first, tot


def cost(t: Counter) -> float:
    return (t["input_tokens"] * PRICE_IN + t["output_tokens"] * PRICE_OUT
            + t["cache_creation_input_tokens"] * PRICE_IN * 1.25
            + t["cache_read_input_tokens"] * PRICE_IN * 0.1) / 1e6


def run_start(run_id: str) -> str:
    # 2026-10-06T11-40-17-424Z -> 2026-10-06T11:40:17.424Z (same format as transcript timestamps)
    d, t = run_id.split("T")
    h, m, s, ms = t.rstrip("Z").split("-")
    return f"{d}T{h}:{m}:{s}.{ms}Z"


def run_stage(run_dir: Path) -> str:
    s = run_dir / "summary.md"
    if s.exists():
        mo = re.search(r"\*\*Request:\*\*\s*(?:create pipeline stage:\s*)?(.+)", s.read_text())
        if mo:
            return re.sub(r"[^A-Za-z0-9]+", "-", mo.group(1)).strip("-")[:40]
    return "unknown"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cwd", type=Path, default=Path.cwd(), help="design dir (default: cwd)")
    args = ap.parse_args()
    root = args.cwd.resolve()
    out = root / "transcripts"
    if out.exists():
        shutil.rmtree(out)

    # Claude Code sessions run directly in this directory.
    main_dir = PROJECTS / slug(root)
    for f in sorted(main_dir.glob("**/*.jsonl")) if main_dir.exists() else []:
        dst = out / "claude-code" / f.relative_to(main_dir)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)

    # copperhead runs, oldest first.
    runs_dir = root / ".copperhead" / "runs"
    runs = sorted(p for p in runs_dir.glob("20*") if p.is_dir()) if runs_dir.exists() else []
    starts = [run_start(r.name) for r in runs]
    run_out = {}
    for i, r in enumerate(runs, 1):
        d = out / "copperhead" / f"{i:02d}_{r.name}_{run_stage(r)}"
        d.mkdir(parents=True)
        for name, new in (("transcript.jsonl", "run_transcript.jsonl"), ("summary.md", "summary.md")):
            if (r / name).exists():
                shutil.copy2(r / name, d / new)
        run_out[r.name] = d

    # Child sessions spawned by copperhead's claude-code backend.
    children = []
    for f in PROJECTS.glob("-tmp-copperhead-cc-*/**/*.jsonl"):
        first, tot = scan(f)
        children.append((first, f, tot))
    children.sort(key=lambda c: c[0])
    per_run: dict[str, Counter] = {}
    seq: Counter = Counter()
    for first, f, tot in children:
        i = bisect_right(starts, first) - 1
        key = runs[i].name if i >= 0 else "unassigned"
        d = run_out.get(key, out / "copperhead" / "unassigned")
        seq[key] += 1
        stamp = first.replace(":", "-") or "no-ts"
        dst = d / "cc" / f"{seq[key]:03d}_{stamp}_{f.stem}.jsonl"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
        acc = per_run.setdefault(key, Counter())
        acc.update(tot)
        acc["sessions"] += 1

    # Index.
    main_tot = Counter()
    for f in (out / "claude-code").glob("**/*.jsonl"):
        main_tot.update(scan(f)[1])
    rows = ["| # | run | stage | cc sessions | output tok | cache write | cache read | ≈API $ |",
            "|---|---|---|---|---|---|---|---|"]
    grand = Counter()
    keys = [r.name for r in runs] + (["unassigned"] if "unassigned" in per_run else [])
    for n, key in enumerate(keys, 1):
        t = per_run.get(key, Counter())
        grand.update(t)
        stage = run_stage(runs_dir / key) if key != "unassigned" else "-"
        rows.append(f"| {n} | {key} | {stage} | {t['sessions']} | {t['output_tokens']:,} | "
                    f"{t['cache_creation_input_tokens']:,} | {t['cache_read_input_tokens']:,} | {cost(t):.2f} |")
    rows.append(f"| | **copperhead total** | | {grand['sessions']} | {grand['output_tokens']:,} | "
                f"{grand['cache_creation_input_tokens']:,} | {grand['cache_read_input_tokens']:,} | **{cost(grand):.2f}** |")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    (out / "INDEX.md").write_text(
        f"# Transcripts\n\nExported {now} by export_transcripts.py. Costs are equivalent first-party API "
        f"cost (claude-opus-5-5 pricing), not subscription billing.\n\n"
        f"Claude Code sessions in this directory: {len(list((out / 'claude-code').glob('*.jsonl')))} "
        f"(≈${cost(main_tot):.2f}).\n\n## copperhead runs\n\n" + "\n".join(rows) + "\n")
    print(f"wrote {out}: {len(runs)} runs, {len(children)} copperhead sessions, "
          f"copperhead ≈${cost(grand):.2f}, direct sessions ≈${cost(main_tot):.2f}")


if __name__ == "__main__":
    main()
