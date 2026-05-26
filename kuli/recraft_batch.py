"""kuli.recraft_batch — fan out many prompts to ask-recraft in parallel.

Prompts: one per line, or split on --delimiter.
"""
import argparse
import shutil

from . import core

PROG = "ask-recraft-batch"
die = core.make_die(PROG)


def cli_path():
    path = shutil.which("ask-recraft")
    if not path:
        die("ask-recraft not found on PATH", 1)
    return path


def parse_args():
    p = argparse.ArgumentParser(prog=PROG, description="Fan out ask-recraft in parallel.")
    p.add_argument("--delimiter", "-d", help="split prompts on this line (else one per line)")
    p.add_argument("--jobs", "-j", type=int, default=4, help="parallel workers (default 4)")
    p.add_argument("--json", action="store_true", help="emit JSON array of results")
    return p.parse_args()


def main():
    args = parse_args()
    cli = cli_path()
    prompts = core.read_prompts(PROG, args.delimiter)
    jobs = [(p[:60].replace("\n", " "), [p]) for p in prompts]
    results = core.run_batch(jobs, lambda ca: [cli, "-q", *ca], args.jobs)
    core.emit_batch(results, args.json)
    core.batch_exit(results)


if __name__ == "__main__":
    main()
