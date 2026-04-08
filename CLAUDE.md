# Microbe Hunters — Illustrated Reading Edition

## Project

An illustrated, scroll-synced reading experience of "Microbe Hunters" by Paul de Kruif for a parent reading aloud to a precocious 5-year-old. Private repo: `josephhajduk/microbehunters`.

## Architecture

```
microbe_hunters.html     — Source text from Project Gutenberg (#77842)
extract_sections.py      — Parses HTML into 83 numbered sub-sections
prepare_prompts_v2.py    — Builds LLM prompts for each section
swarm_prompt_v2.md       — Instructions for section-processing agents
style_guide.md           — Linocut print style, scientifically accurate
assemble.py              — Builds index.html from template + section HTML + segment JSON
template.html            — Two-column scrollytelling layout with CSS/JS
generate_images.py       — Batch image generation via xAI API
index.html               — Assembled output (rebuilt by assemble.py)
sections/                — 83 .html + .txt files with manifest.json
prompts/                 — 83 .json segment files + 83 _prompt.txt files
media/                   — Generated images + manifest.json
.env.1password.xai       — op:// reference for XAI_API_KEY
```

## Key Decisions

- **Style**: Linocut print — bold black outlines, flat muted colors (dusty rose, sage green, ochre), rough textured edges, hand-printed on natural paper. NOT the glossy AI slop look.
- **Scientific accuracy**: Prompts include period-correct clothing, equipment, microbe morphology, and lab techniques for each scientist's era.
- **No text in images**: AI-generated text is always garbled — all prompts explicitly exclude labels/lettering.
- **Aspect ratio**: 9:16 portrait (matches the sticky right panel).
- **Chunking**: Book's existing numbered sub-sections, further split into 250-500 word segments. 83 sections → 331 segments total.
- **Pretext**: Used for widow detection/fixing and pixel-precise scroll sync via measured segment positions.

## Generating Images

```bash
# Uses 1Password for API key via op run proxy
op run --env-file=.env.1password.xai -- python3 generate_images.py --chapter N --aspect-ratio 9:16

# Pro model ($0.07/img, better quality)
op run --env-file=.env.1password.xai -- python3 generate_images.py --chapter N --pro --aspect-ratio 9:16

# All remaining chapters
op run --env-file=.env.1password.xai -- python3 generate_images.py --aspect-ratio 9:16
```

- Standard model: `grok-imagine-image` at $0.02/img
- Pro model: `grok-imagine-image-pro` at $0.07/img
- Script skips existing images — safe to rerun
- Retries: just rerun the same command

## Image Generation Progress

| Ch | Scientist | Sections | Segments | Images | Model | Status |
|----|-----------|----------|----------|--------|-------|--------|
| 1 | Leeuwenhoek | 4 | 20 | 20 | pro | Done |
| 2 | Spallanzani | 7 | 31 | 31 | standard | Done |
| 3 | Pasteur (Microbes) | 8 | 41 | 41 | standard | Done |
| 4 | Koch | 8 | 33 | 0 | — | Pending |
| 5 | Pasteur (Mad Dog) | 7 | 26 | 0 | — | Pending |
| 6 | Roux & Behring | 4 | 18 | 0 | — | Pending |
| 7 | Metchnikoff | 8 | 26 | 0 | — | Pending |
| 8 | Theobald Smith | 7 | 17 | 0 | — | Pending |
| 9 | Bruce | 9 | 21 | 0 | — | Pending |
| 10 | Ross vs. Grassi | 8 | 30 | 0 | — | Pending |
| 11 | Walter Reed | 7 | 25 | 0 | — | Pending |
| 12 | Paul Ehrlich | 6 | 23 | 0 | — | Pending |
| **Total** | | **83** | **331** | **92** | | |

Cost so far: ~$2.84 (20 pro + 72 standard)
Remaining: 239 images × $0.02 = ~$4.78

## Rebuilding the Page

```bash
python3 assemble.py    # rebuilds index.html from template + data
```

## Serving Locally

```bash
python3 -m http.server 8000
```

## URL State

The page persists text size, line spacing, and scroll position in the URL:
```
index.html?size=bigger&spacing=relaxed#ch04_sec02_seg01
```

## Keyboard Shortcuts

- `j` / `↓` — next segment
- `k` / `↑` — previous segment
