# claude-ask-deepseek

Give your AI coding agent (Claude Code) a cheap **intern**: it hands well-scoped
grunt work to **DeepSeek V4** via [OpenRouter](https://openrouter.ai), then
reviews the output before anything ships.

**The intern model.** The agent is the senior; DeepSeek is the intern working
under it: the senior briefs the task and bundles the context (the intern has no
repo memory), the intern grinds (research, summarizing, drafting, extraction,
classification, brainstorming) at a fraction of the cost, and the senior
**reviews and corrects** before using the result — never merges it blind. Hard
or correctness-critical calls stay with the senior. OpenRouter prompt caching is
automatic (~0.25x for cached tokens), and the intern can `--reasoning` (thinking
mode) when a task needs real thought.

## Install — just tell your agent

Paste this to Claude Code (or any agent that can run shell + clone repos):

```
Install ini https://github.com/arielfikru/claude-ask-deepseek
```

The agent reads [`INSTALL.md`](INSTALL.md) and sets itself up. That's it.

### Manual install

> **No `npm install` / `pip install` needed.** The CLI is a single stdlib-Python
> script (Python 3.8+, zero dependencies). `install.sh` just copies it into
> `~/.claude/bin` and adds that to your PATH. The only optional dependency is the
> `mcp` package, and only if you want the [MCP server](#mcp-server-optional).

```bash
git clone --depth 1 https://github.com/arielfikru/claude-ask-deepseek.git
bash claude-ask-deepseek/install.sh
export OPENROUTER_API_KEY="sk-or-..."   # see "Getting an API key" below
ask-deepseek --flash "Reply with exactly: PONG"
```

### Getting an API key

The intern runs on [OpenRouter](https://openrouter.ai), which proxies DeepSeek V4
(so you get caching + reasoning + a single key for many models).

1. Sign up at <https://openrouter.ai>.
2. Open <https://openrouter.ai/keys> and **Create Key**. Optionally set a credit
   limit on the key (recommended — caps your spend).
3. Add a few dollars of credit (DeepSeek V4 is cheap; see [cost](#cost--rate-limits--timeouts)).
4. Export it: `export OPENROUTER_API_KEY="sk-or-..."` — persist it by uncommenting
   the line `install.sh` added to your `~/.bashrc`.

You do **not** need a key from DeepSeek directly; OpenRouter handles the upstream.

## What gets installed

| Path | What |
| ---- | ---- |
| `~/.claude/bin/ask-deepseek` | the CLI (stdlib Python, zero deps) |
| `~/.claude/skills/deepseek/SKILL.md` | the `/deepseek` skill: when/how the agent delegates |
| `~/.bashrc` (+`~/.zshrc`) | adds `~/.claude/bin` to PATH, key placeholder |

## CLI usage

```bash
ask-deepseek "summarize the tradeoffs of WAL vs rollback journaling"
cat report.md | ask-deepseek "extract every action item as a bullet"
ask-deepseek -f src/big.py "list every public function and its purpose"
ask-deepseek --flash "cheap quick task"               # v4-flash instead of v4-pro
ask-deepseek --auto "route me by size"                # small->flash, large->pro
ask-deepseek -r high "tricky logic/math problem"      # thinking mode (or -r xhigh)
ask-deepseek -r high --show-thinking "..."            # also print the reasoning
ask-deepseek -s "You are a data extractor" --json "return {name,email} from: ..."
```

### What it looks like

```console
$ ask-deepseek --flash "Reply with exactly: PONG"
PONG
[deepseek/deepseek-v4-flash | in 10 out 3 tok]

$ ask-deepseek --flash -c 5 "Capital of Australia? Reply ONLY the city."
Canberra
[deepseek/deepseek-v4-flash | in 75 out 125 tok | agreement 5/5]

$ ask-deepseek --flash -r high --show-thinking "What is 17*23? Reply ONLY the number."
<thinking>
We compute 17*23 = 391. Reply with only 391.
</thinking>

391
[deepseek/deepseek-v4-flash | in 23 out 412 tok]
```

> The stats line (model, token in/out, cache hits, vote agreement) is printed on
> **stderr**, so piping `ask-deepseek ... | next-tool` passes only the clean
> answer. Want to record a GIF for your fork? `vhs` or `asciinema` work well.

| Flag | Meaning |
| ---- | ------- |
| `--flash` | use `deepseek/deepseek-v4-flash` (cheaper) instead of `-pro` |
| `--reasoning`, `-r [high\|xhigh]` | enable thinking mode (bare = high) — big accuracy gain on hard reasoning |
| `--consistency`, `-c N` | self-consistency: sample N, majority-vote, report agreement + flag disagreement |
| `--show-thinking` | also print the reasoning process (off by default — final answer only) |
| `--timeout SEC` | HTTP timeout, default 600 (env `DEEPSEEK_TIMEOUT`) — raise for long `xhigh` runs |
| `-m SLUG` | explicit OpenRouter model slug |
| `-s TEXT` | system prompt |
| `-f FILE` | prepend file contents to the prompt |
| `-t N` | temperature (default 0.7) |
| `--max-tokens N` | max **output** tokens (default 262144, env `DEEPSEEK_MAX_TOKENS`) |
| `--json` | request a JSON object response |
| `-q` | suppress the usage/cost line on stderr |

Models: `deepseek/deepseek-v4-pro` (default), `deepseek/deepseek-v4-flash`.
Override the default via `DEEPSEEK_MODEL` env var.

> **Context vs output:** DeepSeek V4 has a **1M-token context window** — that's
> the *input* budget, so you can feed huge files via `-f`. `--max-tokens` caps
> only the **generated output** (default 262144). The cap is just a ceiling — the
> model bills every token it actually generates, so the default rarely matters
> unless a prompt makes the model produce a very long answer. Lower it
> (`--max-tokens 8192` or `DEEPSEEK_MAX_TOKENS`) to hard-limit cost.

## Auto-routing

`--auto` picks the model by estimated input size: small/simple prompts go to
`flash` (cheap), large ones to `pro` (capable). Threshold is `1500` estimated
tokens, override via `DEEPSEEK_AUTO_THRESHOLD`.

```bash
ask-deepseek --auto "Say hi"            # -> v4-flash
ask-deepseek --auto -f huge_doc.md "analyze"   # -> v4-pro
```

## Reasoning (thinking mode)

DeepSeek V4 supports a thinking mode that produces internal reasoning before the
answer — a large, measured accuracy gain on hard math/logic/analysis. Enable it
with `--reasoning`/`-r` (`high`, or `xhigh` for max effort). It costs more output
tokens (the thinking is billed), so use it only when a task genuinely needs it.

```bash
ask-deepseek -r high  "Find ordered pairs (a,b), a+b=1000, no digit 0."   # -> 738
ask-deepseek -r xhigh -f spec.md "review this design for race conditions"
```

By default only the **final answer** prints; add `--show-thinking` to also see the
reasoning (wrapped in `<thinking>…</thinking>`). The thinking is generated and
**billed** either way — the flag only controls whether it's displayed.

## Cost, rate limits & timeouts

**Reasoning makes output long.** With `--reasoning`, the model emits a long
internal thinking process before the answer, and **every thinking token is billed
as output**. In testing, one hard problem with `-r high` produced ~14k output
tokens (and `--consistency N` multiplies that by N). A normal non-reasoning call is
tiny by comparison. So:

- **Estimate before you fan out.** The stderr stats line shows `out N tok` per
  call — reasoning: assume thousands; non-reasoning: tens to hundreds.
  `--consistency N` and `ask-deepseek-batch` multiply cost by N; start with
  `--flash` and small N.
- **Cap spend at the source.** Set a credit limit on the OpenRouter key, and use
  `--max-tokens` (or `DEEPSEEK_MAX_TOKENS`) to hard-ceiling output per call.
- **Caching cuts repeat cost** — re-use the same `-s`/`-f` prefix (~0.25x, see
  [Caching](#caching)).
- **Default to the cheap intern** — `--flash`/`--auto`; reserve `-pro` + `-r xhigh`
  for genuinely hard work.

**Timeouts.** Long `xhigh` runs take a while. The CLI waits up to **600s** by
default; raise with `--timeout 900` or `DEEPSEEK_TIMEOUT`. On timeout you get a
clear error (`timed out after Ns — raise --timeout or lower --reasoning effort`),
not a hang. OpenRouter **rate limits** (HTTP 429) surface verbatim on stderr —
lower concurrency (`-j` in batch) or retry.

## Self-consistency (automatic review gate)

`--consistency N` (`-c N`) samples the answer N times (higher temperature),
majority-votes, and prints `agreement X/N` on stderr — flagging `⚠ LOW` when
there's no majority so you know to verify. This is an evidence-backed gate
(+9–15% accuracy in the literature) that works best on short / factual / numeric
answers; it's not useful for long prose (every sample differs). It costs N×
output tokens.

```bash
ask-deepseek --flash -c 5 "Capital of Australia? Reply ONLY the city."
# -> Canberra        [stderr: ... | agreement 5/5]
```

## Batch fan-out

`ask-deepseek-batch` runs many prompts in parallel, reusing one cached prefix
(shared `--system`/`--context`), so cost drops after the first call.

```bash
# one prompt per line on stdin
printf 'tldr A\ntldr B\ntldr C\n' | ask-deepseek-batch --flash -j 8

# shared context file (cached), auto-route each question
ask-deepseek-batch -c report.md --auto < questions.txt

# multiline prompts split on a delimiter line, JSON output
ask-deepseek-batch -d '---' --json < prompts.txt > out.json
```

| Flag | Meaning |
| ---- | ------- |
| `-s TEXT` | shared system prompt (cached prefix) |
| `-c FILE` | shared context file (cached prefix) |
| `-d STR` | split prompts on this delimiter line (default: one per line) |
| `-j N` | parallel workers (default 4) |
| `--flash` / `--auto` / `-r` / `-m` / `-t` / `--max-tokens` | applied to every prompt |
| `--json` | emit a JSON array of `{index, prompt, output, ok}` |

## Caching

DeepSeek caching on OpenRouter is automatic — no `cache_control` breakpoints.
Cached prompt tokens bill at ~0.25x. The cache keys on the request **prefix**, so
keep the stable part (same `-s SYSTEM` / `-f FILE`) identical and put the varying
question last (the CLI already orders system → file → prompt). The usage line
reports cache hits:

```
[deepseek/deepseek-v4-flash | in 1213 out 39 tok | cached 509 (~0.25x)]
```

## MCP server (optional)

The CLI is the engine and works in any shell. If you want the intern exposed as
**native MCP tools** (no shell spawn, typed args) in an MCP-aware client, there's
a thin wrapper in [`mcp/server.py`](mcp/server.py) that just shells out to the
same CLI — so caching, reasoning, consistency, and batch all still apply.

```bash
pip install -r mcp/requirements.txt          # needs the `mcp` package
# register in Claude Code (user scope), passing the key as env:
claude mcp add deepseek --scope user \
  -e OPENROUTER_API_KEY="sk-or-..." \
  -- python3 /abs/path/to/claude-ask-deepseek/mcp/server.py
```

Tools exposed: `ask_deepseek(prompt, model, reasoning, system, consistency,
context_file, max_tokens)` and `ask_deepseek_batch(prompts, ...)`. Prefer the CLI
for portability; reach for MCP only when an agent can't spawn a shell or you want
the harness to validate tool args.

## Requirements

- Python 3.8+ (stdlib only — no pip installs)
- An OpenRouter API key
- Optional: Claude Code, for the `/deepseek` skill auto-trigger

## License

MIT
