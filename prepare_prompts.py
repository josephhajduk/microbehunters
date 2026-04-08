#!/usr/bin/env python3
"""
Prepare one prompt file per section for external processing.
Output: prompts/ch{NN}_sec{NN}_prompt.txt — ready to pipe into `claude -p` or any LLM.
"""

import json
import os


def load_file(path):
    with open(path, 'r') as f:
        return f.read()


def build_prompt(section_meta, text_content, html_content, swarm_prompt, style_guide):
    return f"""{swarm_prompt}

---

## Style Guide

{style_guide}

---

## Section to Process

**Section ID:** {section_meta['id']}
**Chapter {section_meta['chapter']}:** {section_meta['scientist']} — {section_meta['subtitle']}
**Section {section_meta['section']} of this chapter**
**Word count:** {section_meta['word_count']}

### Plain Text

{text_content}

### Raw HTML

{html_content}

---

Now output the JSON for this section. Remember: valid JSON only, no markdown fencing, no commentary.
"""


def main():
    os.makedirs('prompts', exist_ok=True)

    manifest = json.loads(load_file('sections/manifest.json'))
    swarm_prompt = load_file('swarm_prompt.md')
    style_guide = load_file('style_guide.md')

    for section in manifest:
        sid = section['id']
        text_content = load_file(section['text_file'])
        html_content = load_file(section['html_file'])
        prompt = build_prompt(section, text_content, html_content, swarm_prompt, style_guide)

        output_path = f"prompts/{sid}_prompt.txt"
        with open(output_path, 'w') as f:
            f.write(prompt)

        print(f"{sid}_prompt.txt ({len(prompt):,} chars)")

    print(f"\n{len(manifest)} prompt files written to prompts/")
    print(f"\nTo process one:  claude -p \"$(cat prompts/ch01_sec01_prompt.txt)\" --output-format text > prompts/ch01_sec01.json")
    print(f"To process all:  for f in prompts/*_prompt.txt; do id=$(basename $f _prompt.txt); claude -p \"$(cat $f)\" --output-format text > prompts/$id.json; done")


if __name__ == '__main__':
    main()
