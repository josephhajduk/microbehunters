#!/usr/bin/env python3
"""
Assemble the scrollytelling HTML page from section HTMLs + segment JSONs.

Reads:
  - sections/manifest.json
  - sections/ch{NN}_sec{NN}.html (raw paragraph HTML)
  - prompts/ch{NN}_sec{NN}.json (segments with paragraph ranges + animation prompts)

Writes:
  - index.html (the full scrollytelling page)
  - media/manifest.json (list of all expected media files for generation tracking)
"""

import json
import os
import re
from html.parser import HTMLParser


CHAPTER_TITLES = {
    1: ("I", "Leeuwenhoek", "First of the Microbe Hunters"),
    2: ("II", "Spallanzani", "Microbes Must Have Parents!"),
    3: ("III", "Pasteur", "Microbes Are a Menace!"),
    4: ("IV", "Koch", "The Death Fighter"),
    5: ("V", "Pasteur", "And the Mad Dog"),
    6: ("VI", "Roux and Behring", "Massacre the Guinea-Pigs"),
    7: ("VII", "Metchnikoff", "The Nice Phagocytes"),
    8: ("VIII", "Theobald Smith", "Ticks and Texas Fever"),
    9: ("IX", "Bruce", "Trail of the Tsetse"),
    10: ("X", "Ross vs. Grassi", "Malaria"),
    11: ("XI", "Walter Reed", "In the Interest of Science\u2014and for Humanity!"),
    12: ("XII", "Paul Ehrlich", "The Magic Bullet"),
}

# Available transitions. Default is 'fade'.
TRANSITIONS = ['fade', 'slide-up', 'slide-down', 'slide-left', 'crossfade', 'dissolve', 'zoom']


class ParagraphExtractor(HTMLParser):
    """Extract <p> tags from section HTML, cleaning up page markers."""
    def __init__(self):
        super().__init__()
        self.paragraphs = []
        self.current = []
        self.in_p = False
        self.skip_span = False
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == 'p':
            self.in_p = True
            self.current = []
            self.depth = 0
        elif self.in_p:
            if tag == 'span' and 'pagenum' in attr_dict.get('class', ''):
                self.skip_span = True
            elif not self.skip_span:
                # Keep em, i, b, strong tags
                if tag in ('em', 'i', 'b', 'strong'):
                    self.current.append(f'<{tag}>')
                self.depth += 1

    def handle_endtag(self, tag):
        if tag == 'p' and self.in_p:
            self.in_p = False
            text = ''.join(self.current).strip()
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            if text:
                self.paragraphs.append(text)
            self.current = []
        elif self.in_p:
            if tag == 'span' and self.skip_span:
                self.skip_span = False
            elif not self.skip_span:
                if tag in ('em', 'i', 'b', 'strong'):
                    self.current.append(f'</{tag}>')

    def handle_data(self, data):
        if self.in_p and not self.skip_span:
            self.current.append(data)


def extract_paragraphs(html_content):
    parser = ParagraphExtractor()
    parser.feed(html_content)
    return parser.paragraphs


def pick_transition(segment_index, mood):
    """Pick a default transition based on mood. Can be overridden in JSON."""
    mood_map = {
        'wonder': 'dissolve',
        'discovery': 'zoom',
        'tension': 'slide-left',
        'humor': 'fade',
        'triumph': 'slide-up',
        'sadness': 'dissolve',
        'curiosity': 'fade',
        'adventure': 'slide-up',
    }
    return mood_map.get(mood, 'fade')


def build_chapter_nav(manifest):
    """Build chapter navigation HTML."""
    chapters_seen = set()
    nav_items = []
    for entry in manifest:
        ch = entry['chapter']
        if ch not in chapters_seen:
            chapters_seen.add(ch)
            roman, scientist, subtitle = CHAPTER_TITLES[ch]
            nav_items.append(
                f'<a href="#chapter-{ch}" class="nav-chapter">'
                f'<span class="nav-roman">{roman}</span>'
                f'<span class="nav-scientist">{scientist}</span>'
                f'</a>'
            )
    return '\n'.join(nav_items)


def build_page(manifest):
    media_manifest = []
    sections_html = []
    current_chapter = None

    for entry in manifest:
        sid = entry['id']
        ch = entry['chapter']
        sec = entry['section']

        # Chapter header
        if ch != current_chapter:
            current_chapter = ch
            roman, scientist, subtitle = CHAPTER_TITLES[ch]
            sections_html.append(f'''
    <div class="chapter-header" id="chapter-{ch}">
      <div class="chapter-number">Chapter {roman}</div>
      <h2 class="chapter-scientist">{scientist}</h2>
      <div class="chapter-subtitle">{subtitle}</div>
    </div>''')

        # Load section HTML and JSON
        html_path = entry['html_file']
        json_path = f'prompts/{sid}.json'

        with open(html_path) as f:
            section_html = f.read()
        with open(json_path) as f:
            segment_data = json.load(f)

        paragraphs = extract_paragraphs(section_html)
        segments = segment_data.get('segments', [])

        # Section wrapper
        sections_html.append(f'  <div class="section" id="{sid}">')

        for seg in segments:
            seg_idx = seg['segment_index']
            p_range = seg['paragraph_range']
            mood = seg.get('mood', seg.get('visual', {}).get('mood', 'curiosity'))
            transition = seg.get('transition', pick_transition(seg_idx, mood))
            scene_desc = seg.get('visual', {}).get('scene_description', '')
            prompt = seg.get('visual', {}).get('animation_prompt', '')

            media_id = f'{sid}_seg{seg_idx:02d}'
            media_manifest.append({
                'id': media_id,
                'chapter': ch,
                'section': sec,
                'segment': seg_idx,
                'scientist': entry['scientist'],
                'mood': mood,
                'transition': transition,
                'scene_description': scene_desc,
                'animation_prompt': prompt,
                'video_path': f'media/{media_id}.mp4',
                'image_path': f'media/{media_id}.png',
            })

            # Get paragraphs for this segment
            start = p_range[0] - 1  # 1-indexed to 0-indexed
            end = p_range[1]
            seg_paragraphs = paragraphs[start:end]

            # Build paragraph HTML
            p_html = '\n'.join(f'        <p>{p}</p>' for p in seg_paragraphs)

            sections_html.append(f'''
      <div class="segment"
           id="{media_id}"
           data-media="{media_id}"
           data-transition="{transition}"
           data-mood="{mood}">
        <div class="segment-text">
{p_html}
        </div>
      </div>''')

        sections_html.append('  </div>')  # close section

    # Save media manifest
    with open('media/manifest.json', 'w') as f:
        json.dump(media_manifest, f, indent=2)
    print(f"Media manifest: {len(media_manifest)} entries written to media/manifest.json")

    chapter_nav = build_chapter_nav(manifest)
    body_content = '\n'.join(sections_html)

    return chapter_nav, body_content, len(media_manifest)


def main():
    with open('sections/manifest.json') as f:
        manifest = json.load(f)

    chapter_nav, body_content, n_media = build_page(manifest)

    # Read the HTML template
    with open('template.html') as f:
        template = f.read()

    html = template.replace('{{CHAPTER_NAV}}', chapter_nav)
    html = html.replace('{{BODY_CONTENT}}', body_content)

    with open('index.html', 'w') as f:
        f.write(html)

    print(f"Built index.html with {n_media} segments")


if __name__ == '__main__':
    main()
