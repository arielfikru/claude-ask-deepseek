#!/usr/bin/env python3
"""ask-deepseek-batch — fan out many prompts to DeepSeek in parallel.

Each prompt is sent via `ask-deepseek`, so a shared `--system`/`--context`
prefix is cached after the first call (~0.25x for cached tokens).

Usage:
  printf 'tldr A\ntldr B\ntldr C\n' | ask-deepseek-batch --flash
  ask-deepseek-batch -c report.md -j 8 < questions.txt
  ask-deepseek-batch --delimiter '---' < multiline_prompts.txt
  ask-deepseek-batch --auto --json < prompts.txt > out.json

Prompts: one per line (default), or split on --delimiter line. Shared opts
(--system, --context, --flash, --auto, -m, -t, --max-tokens) apply to all.
"""
import argparse
import concurrent.futures
import json
import subprocess
import sys
from pathlib import Path

CLI = str(Path(__file__).resolve().parent / "ask-deepseek")


def parse_args():
    p = argparse.ArgumentParser(description="Fan out prompts to DeepSeek in parallel.")
    p.add_argument("--system", "-s", help="shared system prompt (cached prefix)")
    p.add_argument("--context", "-c", help="shared context file (cached prefix)")
    p.add_argument("--delimiter", "-d", help="split prompts on this line (else one per line)")
    p.add_argument("--jobs", "-j", type=int, default=4, help="parallel workers (default 4)")
    p.add_argument("--flash", action="store_true", help="use v4-flash for all")
    p.add_argument("--auto", action="store_true", help="auto-route each by size")
    p.add_argument("--model", "-m", help="explicit model slug for all")
    p.add_argument("--temperature", "-t", type=float)
    p.add_argument("--max-tokens", type=int)
    p.add_argument("--json", action="store_true", help="emit JSON array of results")
    return p.parse_args()


def read_prompts(delimiter):
    raw = sys.stdin.read()
    if delimiter:
        chunks = raw.split(f"\n{delimiter}\n" if "\n" not in delimiter else delimiter)
    else:
        chunks = raw.splitlines()
    prompts = [c.strip() for c in chunks if c.strip()]
    if not prompts:
        print("ask-deepseek-batch: no prompts on stdin", file=sys.stderr)
        sys.exit(1)
    return prompts


def shared_flags(args):
    flags = ["-q"]
    if args.system:
        flags += ["-s", args.system]
    if args.context:
        flags += ["-f", args.context]
    if args.flash:
        flags.append("--flash")
    if args.auto:
        flags.append("--auto")
    if args.model:
        flags += ["-m", args.model]
    if args.temperature is not None:
        flags += ["-t", str(args.temperature)]
    if args.max_tokens is not None:
        flags += ["--max-tokens", str(args.max_tokens)]
    return flags


def run_one(index, prompt, flags):
    proc = subprocess.run(
        [CLI, *flags, prompt], capture_output=True, text=True
    )
    if proc.returncode != 0:
        return index, prompt, f"ERROR: {proc.stderr.strip()}", False
    return index, prompt, proc.stdout.rstrip("\n"), True


def run_batch(prompts, flags, jobs):
    results = [None] * len(prompts)
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        futs = {pool.submit(run_one, i, p, flags): i for i, p in enumerate(prompts)}
        for fut in concurrent.futures.as_completed(futs):
            i, prompt, out, ok = fut.result()
            results[i] = {"index": i, "prompt": prompt, "output": out, "ok": ok}
    return results


def emit(results, as_json):
    if as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    for r in results:
        snippet = r["prompt"][:60].replace("\n", " ")
        print(f"=== [{r['index']}] {snippet} ===")
        print(r["output"])
        print()


def main():
    args = parse_args()
    prompts = read_prompts(args.delimiter)
    results = run_batch(prompts, shared_flags(args), args.jobs)
    emit(results, args.json)
    if any(not r["ok"] for r in results):
        sys.exit(2)


if __name__ == "__main__":
    main()
