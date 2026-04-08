#!/usr/bin/env python3
"""
Prepare v2 prompt files — agents output paragraph ranges + visuals only, no text reproduction.
"""

import json
import os
import re
from html.parser import HTMLParser


class ParagraphCounter(HTMLParser):
    """Count paragraphs and extract first sentence of each."""
    def __init__(self):
        super().__init__()
        self.paragraphs = []
        self.current_text = []
        self.in_p = False

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.in_p = True
            self.current_text = []

    def handle_endtag(self, tag):
        if tag == 'p' and self.in_p:
            self.in_p = False
            text = ''.join(self.current_text).strip()
            # Remove page markers
            text = re.sub(r'\[Pg \d+\]', '', text).strip()
            if text:
                self.paragraphs.append(text)

    def handle_data(self, data):
        if self.in_p:
            self.current_text.append(data)


def load_file(path):
    with open(path, 'r') as f:
        return f.read()


def get_paragraph_summary(html_content):
    """Get paragraph count and first sentence of each for context."""
    parser = ParagraphCounter()
    parser.feed(html_content)
    lines = []
    for i, p in enumerate(parser.paragraphs, 1):
        # First ~80 chars
        preview = p[:100].replace('\n', ' ')
        if len(p) > 100:
            preview += '...'
        lines.append(f"  P{i}: \"{preview}\"")
    return len(parser.paragraphs), '\n'.join(lines)


def build_prompt(section_meta, text_content, html_content, swarm_prompt, style_guide):
    n_paragraphs, paragraph_previews = get_paragraph_summary(html_content)

    return f"""{swarm_prompt}

---

## Style Guide (key points)

### Character Descriptions (use these exact details for visual consistency)
- **Leeuwenhoek**: round face, big nose, white curled periwig, long dark wool coat, 17th-century Dutch burgher clothing, hunches over tiny hand-held single-lens microscope (brass plates the size of a large coin with glass bead lens)
- **Spallanzani**: tall thin, sharp features, black Catholic priest's cassock, 18th-century Italian, dramatic gesturing hands, works with sealed glass flasks over flames
- **Pasteur**: neat trimmed beard, round spectacles, formal black frock coat (NOT white lab coat), 19th-century French, intense focused expression, swan-neck glass flasks
- **Koch**: thick dark mustache, round wire spectacles, wool waistcoat with rolled shirtsleeves, sturdy German build, compound brass microscope, petri dishes, staining dyes
- **Roux**: gaunt face, dark pointed beard, rolled-up shirtsleeves, French, syringes and guinea pigs in cluttered Paris laboratory
- **Behring**: broad shoulders, Prussian military bearing, blond mustache, formal dress, works with serum and antitoxins
- **Metchnikoff**: wild bushy white beard, round spectacles, Russian, excitable gestures, starfish larvae and white blood cells
- **Theobald Smith**: quiet neat American, clean-shaven, modest USDA laboratory, cattle tick specimens in glass jars
- **Bruce**: British military uniform with sun helmet, African landscape with tsetse flies, field laboratory in Zululand
- **Ross**: British Indian Army officer, thin mustache, hot cramped Indian bungalow, mosquito cages and dissecting needles, sweat-stained shirt, oil lamp
- **Grassi**: dark Italian features, animated expression, Anopheles mosquitoes pinned on cards, malaria-ridden Italian village
- **Walter Reed**: US Army uniform, kind weathered face, military camp in Cuba, volunteer soldiers, wooden barracks
- **Paul Ehrlich**: messy cluttered desk covered in chemical bottles, ever-present cigar, coat stained with bright chemical dyes, test tubes of colored compounds and laboratory mice

### Microbe Depictions (scientifically accurate)
- **Bacteria**: rod-shaped bacilli (anthrax, TB) or round cocci, show cell walls, endospores where relevant, flagella on motile species
- **Protozoa**: malaria as crescent-shaped gametocytes inside red blood cells, trypanosomes as elongated with undulating membrane and flagellum
- **White blood cells / phagocytes**: large irregular cells engulfing smaller bacteria, visible nucleus
- Use circular inset to represent microscope field of view
- Include accurate staining colors where relevant (Gram stain violet/pink, methylene blue, acid-fast red)

### IMPORTANT
- NEVER include any text, words, labels, or lettering in the image description — AI-generated text is always garbled

---

## Section to Process

**Section ID:** {section_meta['id']}
**Chapter {section_meta['chapter']}:** {section_meta['scientist']} — {section_meta['subtitle']}
**Section {section_meta['section']} of this chapter**
**Word count:** {section_meta['word_count']}
**Total paragraphs:** {n_paragraphs}

### Paragraph Index (for paragraph_range references)

{paragraph_previews}

### Full Text (for understanding content — do NOT reproduce in output)

{text_content}

---

Now output the JSON for this section. Remember: valid JSON only, no markdown fencing, no commentary. Use paragraph_range [start, end] inclusive. Do NOT include any text_html field.
"""


def main():
    os.makedirs('prompts', exist_ok=True)

    manifest = json.loads(load_file('sections/manifest.json'))
    swarm_prompt = load_file('swarm_prompt_v2.md')
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


if __name__ == '__main__':
    main()
