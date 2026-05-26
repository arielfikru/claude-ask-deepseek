---
name: recraft
description: Generate SVG vector graphics with Recraft V4.1 Vector via the ask-recraft CLI (OpenRouter image generation). Use when the user wants an icon, logo, illustration, or other designed vector graphic produced as an .svg file — output that scales cleanly and is "designed rather than photographed." Trigger when user says "bikin logo/ikon/ilustrasi SVG", "generate vector", "pakai recraft", "/recraft". Claude stays orchestrator. NOT for photo-realistic raster images, and NOT for analyzing an existing image (use /gemini for that).
---

# recraft — SVG vector generation intern

`ask-recraft` is an image-generation intern: hand it a text prompt, it returns a
**vector SVG** (Recraft V4.1 Vector via OpenRouter) and writes it to a file,
printing the path. Output scales cleanly — good for icons, logos, simple
illustrations. It designs graphics; it does not photograph scenes.

## Tool

`ask-recraft` (at `~/.claude/bin/ask-recraft`). Needs `OPENROUTER_API_KEY`.
Writes an `.svg` file and prints its absolute path on stdout.

```bash
# generate an SVG to a chosen path
ask-recraft -o logo.svg "a minimal red fox head logo, flat geometric, two colors"

# auto-named file in the cwd if -o omitted
ask-recraft "line-art coffee cup icon, single color, rounded"

# guide output with one input image
ask-recraft -i sketch.png -o refined.svg "clean vector version of this sketch"

# batch: one prompt per line, each writes its own auto-named file
printf 'sun icon\nmoon icon\nstar icon\n' | ask-recraft-batch -j 3
```

Flags: `-o FILE` (output path; default auto-named in cwd), `-i IMAGE` (one input
image to guide the result), `--timeout SEC` (default 600; generation ~13s),
`-q`. Cost shows on the stderr stats line (image tokens — pricier than text).

## Prompting tips

- Short, concrete prompts: subject + style + color/constraints
  ("flat", "two colors", "single line", "rounded", "minimal").
- V4.1 has stronger short-prompt adherence than V4 — don't over-describe.
- It's vector-first: ask for icons/logos/illustrations, not photos.

## When to delegate
- Need a real SVG asset (icon/logo/illustration) generated from a description.
- Refining a rough sketch into clean vector art (`-i`).

## When NOT to
- Analyzing/describing an existing image → `/gemini`.
- Photo-realistic raster output → a raster image model, not recraft.
- Final brand assets → Claude/the user reviews the SVG before shipping; treat
  generated art as a draft.

## Notes
- One input image max (`-i`). Output is `data:image/svg+xml` decoded to a file.
- Related: the other KULI interns — same orchestrate-then-review discipline;
  here "review" = open the SVG and check it before using it.
