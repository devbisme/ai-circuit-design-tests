# Why the vanilla runs cost less

The two cheapest design runs on the dual-ADC prompt are the ones with the least KiCad-specific
help: the null test (plain Claude Code) and kicad-harness (a CLI used only for checks, lookups and
renders). Both cost about $11. The runs where an MCP server, skill set or pipeline did more of the
work cost $17–61.

**Short version:** cost is set by how many API calls a session makes and how much context each
call re-reads. The vanilla runs made fewer calls, and each call carried less context. The tools
did not save calls; they added them. Claude had to learn each tool's API, work around its bugs,
and handle many small operations, and every extra call re-read a growing context.

## The numbers

From each run's `claude_cost.txt` (subagents included). "Avg context" is cache-read tokens
divided by API calls, which is roughly the size of the context each call re-read.

| Run | API calls | Cache read | Avg context / call | Output | Cost |
|---|---:|---:|---:|---:|---:|
| null test 2 | 129 | 26.7 M | 207 k | 167 k | $11.16 |
| kicad-harness 2 | 139 | 26.6 M | 191 k | 154 k | $10.87 |
| kicad-mcp-server 2 | 196 | 51.2 M | 261 k | 189 k | $16.93 |
| eda-agent 2 | 198 | 50.8 M | 257 k | 219 k | $18.47 |
| KiCad-AI-Assistant 2 | 212 | 59.5 M | 281 k | 205 k | $19.38 |
| kicad-mcp-pro 2 | 194 | 57.1 M | 294 k | 216 k | $19.42 |
| boardforge 1 | 447 | 61.7 M | 138 k | 55 k | $23.89 |
| kicad-happy 2 | 266¹ | — | 345 k¹ | — | $29.37 |
| Konnect 2 | 279 | 161.7 M | 580 k | 353 k | $61.12 |

¹ No `claude_cost.txt` in the run directory; figures come from the session log
(`~/.claude/projects/...kicad-happy-tests-dual-adc-usb-2/`).

At Opus 5.5 prices (`session_cost.py`: $0.20/M cache read, $20/M output, $4/M input with a
2× multiplier for 1-hour cache writes), the null run breaks down as cache reads $5.34, output
$3.34 and cache writes $2.47. Konnect's breaks down as $32.35, $7.07 and $21.71. Cache reads,
and the cache writes that feed them, make up most of the bill.

## The mechanism

Every API call re-reads the whole conversation so far. Tool results stay in that conversation.
If each call adds Δ tokens to a starting context of C₀, a session of N calls reads about
N·C₀ + Δ·N²/2 tokens in total. **Cost grows roughly with the square of the number of calls**,
so a session with 1.5× the calls and 1.4× the average context costs about 2× as much in cache
reads. That is what separates the vanilla runs from the middle of the pack.

Tool definitions are **not** the cause. On the first call, every run had a context of about
40–42 k tokens; kicad-mcp-pro was the outlier at 51 k. MCP tools are deferred behind
ToolSearch, so having a tool installed costs almost nothing. Using it is what costs.

## Why the tools added calls and context

Counts below come from the `tool_use` blocks in each run's session log.

1. **Batching versus small operations.** The null run wrote the whole circuit as one 625-line
   SKiDL file and ran it. Its board steps were also a few large `pcbnew` scripts plus
   Freerouting. One call did a lot of design work. Konnect went the other way: 502 MCP calls
   across 284 API calls, one small edit per call, and every result stayed in context. Its
   context reached 943 k tokens with no compaction, and that alone accounts for its $61.
2. **Learning and debugging the tool.** In the middle-of-the-pack runs, MCP calls were a minority
   (11–81), and Bash made up most of the work (101–165 calls). The tool covered only part of the
   flow. Claude spent turns reading the tool's source to learn its input format, then wrote
   scripts to fill the gaps or fix its output. kicad-mcp-pro is an example
   (`kicad-mcp-pro-tests/dual-adc-usb-2/claude_transcript.txt`): its schematic builder couldn't
   read KiCad 10's `.kicad_symdir` libraries, so they had to be flattened; it had a bug with
   multi-unit symbols; and the redundant PWR_FLAGs it added had to be pruned before ERC would
   pass. None of these costs exist when Claude uses a library it already knows (SKiDL,
   `pcbnew`).
3. **Large tool outputs.** KiCad-AI-Assistant's MCP results added up to about 0.96 MB of text,
   which stayed in context for the rest of the session.
4. **Multi-agent pipelines.** boardforge kept its average context small (138 k) by handing work to
   subagents, but it made 447 calls in total. Each subagent started cold and paid its own cache
   writes (about 1.9 M tokens of Opus cache writes, most at the 5-minute rate). Small contexts
   didn't make up for the extra calls.

kicad-harness is cheap for the same reason as the null run. Its `kh` CLI ran through Bash and
returned compact results, and Claude's own scripts did the generation. In effect, it is the
vanilla workflow plus a few checking utilities.

## Caveats

- **n = 1 per tool.** These sessions are stochastic. An earlier null-test session in the same
  directory (`70d20041…` and its continuation `c6182897…`, Oct 14–15) was driven step by step
  with many user follow-ups. It read about 92 M cache tokens, which is roughly $18 in cache
  reads alone, before output and cache writes are counted. The $11 figure is one good run, not
  a guaranteed baseline.
- **Cheap is not the same as good.** The null run routed signals through the In1 GND plane, and
  none of these designs has been validated. A tool that costs more but gives a more correct
  board could still be worth it. These numbers don't answer that.
- **User interventions vary.** Prompts such as "are you done?" or "how's the routing going?" each
  add a call that re-reads the full context. Their number was not controlled across runs.
- **The cause is inferred.** The link between turn count and cost follows from the pricing
  formula and holds firmly. Which tool behaviours caused the extra turns is my reading of the
  logs, not a controlled experiment.
