#!/usr/bin/env python3
"""
Extract each numbered sub-section from microbe_hunters.html into individual files.
Output: sections/ch{NN}_sec{NN}.html (raw HTML) and sections/ch{NN}_sec{NN}.txt (plain text)
Also produces sections/manifest.json listing all sections with metadata.
"""

import re
import os
import json
from html.parser import HTMLParser


class TextExtractor(HTMLParser):
    """Strip HTML tags, keeping just text content. Removes [Pg N] markers."""
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        # Skip page number spans
        if tag == 'span' and 'pagenum' in attr_dict.get('class', ''):
            self.skip = True

    def handle_endtag(self, tag):
        if tag == 'span':
            self.skip = False
        if tag == 'p':
            self.text.append('\n\n')

    def handle_data(self, data):
        if not self.skip:
            self.text.append(data)


ROMAN = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6,
         'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12}

CHAPTER_TITLES = {
    1: ("Leeuwenhoek", "First of the Microbe Hunters"),
    2: ("Spallanzani", "Microbes Must Have Parents!"),
    3: ("Pasteur", "Microbes Are a Menace!"),
    4: ("Koch", "The Death Fighter"),
    5: ("Pasteur", "And the Mad Dog"),
    6: ("Roux and Behring", "Massacre the Guinea-Pigs"),
    7: ("Metchnikoff", "The Nice Phagocytes"),
    8: ("Theobald Smith", "Ticks and Texas Fever"),
    9: ("Bruce", "Trail of the Tsetse"),
    10: ("Ross vs. Grassi", "Malaria"),
    11: ("Walter Reed", "In the Interest of Science—and for Humanity!"),
    12: ("Paul Ehrlich", "The Magic Bullet"),
}


def extract_text(html_fragment):
    p = TextExtractor()
    p.feed(html_fragment)
    text = ''.join(p.text).strip()
    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def clean_html_section(html_fragment):
    """Clean up HTML fragment: remove page markers, keep structure."""
    # Remove pagenum spans
    html_fragment = re.sub(r'<span class="pagenum"[^>]*>\[Pg \d+\]</span>\s*', '', html_fragment)
    # Remove the section number heading itself (already captured in metadata)
    html_fragment = re.sub(r'<p class="center (?:p2 )?p1b">.*?</p>\s*', '', html_fragment, count=1)
    return html_fragment.strip()


def main():
    with open('microbe_hunters.html', 'r') as f:
        html = f.read()

    os.makedirs('sections', exist_ok=True)

    # Find chapter boundaries
    ch_pattern = r'id="CHAPTER_([IVX]+)"'
    ch_positions = {}
    for m in re.finditer(ch_pattern, html):
        ch_positions[m.group(1)] = m.start()
    chapters = sorted(ch_positions.items(), key=lambda x: x[1])

    # Find all sub-section markers
    sec_pattern = r'<p class="center (?:p2 )?p1b">(.*?)</p>'
    sec_matches = list(re.finditer(sec_pattern, html))

    manifest = []

    for ch_idx, (ch_roman, ch_pos) in enumerate(chapters):
        ch_num = ROMAN[ch_roman]
        ch_end = chapters[ch_idx + 1][1] if ch_idx + 1 < len(chapters) else html.find('id="pg-footer"')

        # Get sub-sections within this chapter
        ch_secs = [(m.group(1), m.start()) for m in sec_matches if ch_pos <= m.start() < ch_end]

        for sec_idx, (sec_roman, sec_pos) in enumerate(ch_secs):
            sec_num = ROMAN[sec_roman]

            # Section end = start of next section, or end of chapter
            if sec_idx + 1 < len(ch_secs):
                sec_end = ch_secs[sec_idx + 1][1]
            else:
                sec_end = ch_end

            raw_html = html[sec_pos:sec_end]
            clean_html = clean_html_section(raw_html)
            plain_text = extract_text(raw_html)
            word_count = len(plain_text.split())

            basename = f'ch{ch_num:02d}_sec{sec_num:02d}'
            scientist, subtitle = CHAPTER_TITLES[ch_num]

            # Write files
            with open(f'sections/{basename}.html', 'w') as f:
                f.write(clean_html)
            with open(f'sections/{basename}.txt', 'w') as f:
                f.write(plain_text)

            entry = {
                'id': basename,
                'chapter': ch_num,
                'chapter_roman': ch_roman,
                'section': sec_num,
                'section_roman': sec_roman,
                'scientist': scientist,
                'subtitle': subtitle,
                'word_count': word_count,
                'html_file': f'sections/{basename}.html',
                'text_file': f'sections/{basename}.txt',
            }
            manifest.append(entry)
            print(f'{basename}: {scientist} sec {sec_roman} ({word_count} words)')

    with open('sections/manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f'\nExtracted {len(manifest)} sections to sections/')
    print(f'Manifest: sections/manifest.json')


if __name__ == '__main__':
    main()
