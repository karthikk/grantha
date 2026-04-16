#!/usr/bin/env python3
"""
Fetches texts from advaitasharada.sringeri.net and generates HTML pages.
Run: python3 build.py
"""

import os
import html
import re
import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOURCES = {
    'isha':          'https://advaitasharada.sringeri.net/display/moola/Isha/devanagari',
    'kena':          'https://advaitasharada.sringeri.net/display/moola/Kena_pada/devanagari',
    'katha':         'https://advaitasharada.sringeri.net/display/moola/Kathaka/devanagari',
    'prashna':       'https://advaitasharada.sringeri.net/display/moola/Prashna/devanagari',
    'mundaka':       'https://advaitasharada.sringeri.net/display/moola/Mundaka/devanagari',
    'mandukya':      'https://advaitasharada.sringeri.net/display/moola/Mandukya/devanagari',
    'taittiriya':    'https://advaitasharada.sringeri.net/display/moola/Taitiriya/devanagari',
    'aitareya':      'https://advaitasharada.sringeri.net/display/moola/Aitareya/devanagari',
    'chandogya':     'https://advaitasharada.sringeri.net/display/moola/Chandogya/devanagari',
    'brihadaranyaka':'https://advaitasharada.sringeri.net/display/moola/Brha/devanagari',
    'gita':          'https://advaitasharada.sringeri.net/display/moola/Gita/devanagari',
    'brahmasutra':   'https://advaitasharada.sringeri.net/display/moola/BS/devanagari',
}

# Display names
NAMES = {
    'isha': 'ईशावास्योपनिषद्',
    'kena': 'केनोपनिषद्',
    'katha': 'कठोपनिषद्',
    'prashna': 'प्रश्नोपनिषद्',
    'mundaka': 'मुण्डकोपनिषद्',
    'mandukya': 'माण्डूक्योपनिषद्',
    'taittiriya': 'तैत्तिरीयोपनिषद्',
    'aitareya': 'ऐतरेयोपनिषद्',
    'chandogya': 'छान्दोग्योपनिषद्',
    'brihadaranyaka': 'बृहदारण्यकोपनिषद्',
    'gita': 'श्रीमद्भगवद्गीता',
    'brahmasutra': 'ब्रह्मसूत्रम्',
}

GITA_ADHYAYA_NAMES = [
    'अर्जुनविषादयोगः',
    'साङ्ख्ययोगः',
    'कर्मयोगः',
    'ज्ञानकर्मसन्न्यासयोगः',
    'कर्मसन्न्यासयोगः',
    'आत्मसंयमयोगः',
    'ज्ञानविज्ञानयोगः',
    'अक्षरब्रह्मयोगः',
    'राजविद्याराजगुह्ययोगः',
    'विभूतियोगः',
    'विश्वरूपदर्शनयोगः',
    'भक्तियोगः',
    'क्षेत्रक्षेत्रज्ञविभागयोगः',
    'गुणत्रयविभागयोगः',
    'पुरुषोत्तमयोगः',
    'दैवासुरसम्पद्विभागयोगः',
    'श्रद्धात्रयविभागयोगः',
    'मोक्षसन्न्यासयोगः',
]

BS_ADHYAYA_NAMES = [
    'समन्वयाध्यायः',
    'अविरोधाध्यायः',
    'साधनाध्यायः',
    'फलाध्यायः',
]

ORDINALS = ['प्रथम', 'द्वितीय', 'तृतीय', 'चतुर्थ', 'पञ्चम', 'षष्ठ',
            'सप्तम', 'अष्टम', 'नवम', 'दशम', 'एकादश', 'द्वादश',
            'त्रयोदश', 'चतुर्दश', 'पञ्चदश', 'षोडश', 'सप्तदश', 'अष्टादश',
            'एकोनविंश', 'विंश', 'एकविंश', 'द्वाविंश', 'त्रयोविंश', 'चतुर्विंश',
            'पञ्चविंश', 'षड्विंश']

DEVANAGARI_DIGITS = str.maketrans('0123456789', '०१२३४५६७८९')


def to_dev(n):
    """Convert number to devanagari digits."""
    return str(n).translate(DEVANAGARI_DIGITS)


def clean_verse_text(vt_div):
    """Extract clean Devanagari text from a versetext div."""
    content = vt_div.decode_contents()
    content = html.unescape(content)
    # Replace <br/> and <br> with newline
    content = re.sub(r'<br\s*/?>', '\n', content)
    # Remove any remaining HTML tags
    content = re.sub(r'<[^>]+>', '', content)
    content = content.strip()
    return content


def verse_html(text, num_label):
    """Generate HTML for a single verse. Number at end."""
    lines = text.split('\n')
    inner = '<br>\n      '.join(line.strip() for line in lines if line.strip())
    return f'''  <div class="verse">
    <div class="shloka">
      {inner} <span class="verse-num">॥ {num_label} ॥</span>
    </div>
  </div>
'''


def page_html(title, breadcrumbs, body, prev_link=None, next_link=None, css_path='../css/style.css'):
    """Generate a full HTML page."""
    bc_html = breadcrumb_html(breadcrumbs)

    nav = ''
    if prev_link or next_link:
        prev_part = ''
        next_part = ''
        if prev_link:
            prev_part = f'<span class="nav-label">← पूर्वम्</span>\n      <a href="{prev_link[0]}">{prev_link[1]}</a>'
        if next_link:
            next_part = f'<span class="nav-label">अग्रे →</span>\n      <a href="{next_link[0]}">{next_link[1]}</a>'
        nav = f'''
  <nav class="page-nav">
    <div class="prev">
      {prev_part}
    </div>
    <div class="next">
      {next_part}
    </div>
  </nav>
'''

    return f'''<!DOCTYPE html>
<html lang="sa">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — ग्रन्थसङ्ग्रहः</title>
  <link rel="stylesheet" href="{css_path}">
</head>
<body>

<header class="site-header">
  <div class="container">
    <div class="site-title"><a href="{"../" * css_path.count("../") }">ग्रन्थसङ्ग्रहः</a></div>
  </div>
</header>

<main class="container">

  {bc_html}

  <h1>{title}</h1>

{body}
{nav}
</main>

<footer class="site-footer">
  <div class="container">ग्रन्थसङ्ग्रहः</div>
</footer>

</body>
</html>
'''


def breadcrumb_html(crumbs):
    """crumbs = [(url, label), ...] last one has no url."""
    parts = []
    for i, c in enumerate(crumbs):
        if i == len(crumbs) - 1:
            parts.append(c[1])
        else:
            parts.append(f'<a href="{c[0]}">{c[1]}</a>')
    return '<nav class="breadcrumb">\n    ' + '<span class="sep">»</span>'.join(parts) + '\n  </nav>'


def home_path(depth):
    return '../' * depth


def fetch(url):
    print(f'  Fetching {url}')
    r = requests.get(url)
    r.raise_for_status()
    return BeautifulSoup(r.text, 'html.parser')


def extract_verses(container):
    """Extract all verse divs from a container, returning list of (id, type, text)."""
    results = []
    for v in container.find_all('div', class_='verse'):
        vt = v.find('div', class_='versetext')
        if vt:
            text = clean_verse_text(vt)
            results.append((v.get('id', ''), v.get('type', ''), text))
    return results


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'    Wrote {path}')


def extract_verse_num_from_text(text):
    """The source text often has ॥ N ॥ at the end. Extract and remove it."""
    # Match patterns like ॥ १ ॥ or ॥ १.१ ॥ at end
    m = re.search(r'॥\s*([०-९\.]+)\s*॥\s*$', text)
    if m:
        num = m.group(1)
        text = text[:m.start()].rstrip()
        return text, num
    return text, None


# ─── Single-page Upanishads (Isha, Mandukya) ───

def build_single_page_upanishad(key, soup):
    name = NAMES[key]
    out_dir = os.path.join(BASE_DIR, 'upanishads')

    if key == 'mandukya':
        # Mandukya has 4 prakaranams with mantras and karikas interleaved
        body = ''
        chapters = soup.find_all('div', class_='chapter')
        prakarana_names = [
            'आगमप्रकरणम्',
            'वैतथ्यप्रकरणम्',
            'अद्वैतप्रकरणम्',
            'अलातशान्तिप्रकरणम्',
        ]
        for ci, ch in enumerate(chapters):
            pname = prakarana_names[ci] if ci < len(prakarana_names) else ch.get('data-name', '')
            body += f'\n  <h2>{pname}</h2>\n\n'
            for vid, vtype, text in extract_verses(ch):
                text, num = extract_verse_num_from_text(text)
                if not num:
                    # derive from ID like MK_C01_V07 or MK_C01_K10
                    m = re.search(r'_[VK](\d+)', vid)
                    num = to_dev(int(m.group(1))) if m else ''
                label_prefix = 'कारिका ' if vtype == 'kaarika' else ''
                body += verse_html(text, f'{label_prefix}{num}')

        write_file(os.path.join(out_dir, f'{key}.html'),
                   page_html(name,
                            [('../', 'मुख्यम्'), ('./', 'उपनिषदः'), (None, name)],
                            body,
                            prev_link=('mundaka/', 'मुण्डकोपनिषद्'),
                            next_link=('taittiriya/', 'तैत्तिरीयोपनिषद्'),
                            css_path='../css/style.css'))
    else:
        # Simple single page (Isha)
        verses = extract_verses(soup)
        body = ''
        for vid, vtype, text in verses:
            text, num = extract_verse_num_from_text(text)
            if not num:
                m = re.search(r'_V(\d+)', vid)
                num = to_dev(int(m.group(1))) if m else ''
            body += verse_html(text, num)

        write_file(os.path.join(out_dir, f'{key}.html'),
                   page_html(name,
                            [('../', 'मुख्यम्'), ('./', 'उपनिषदः'), (None, name)],
                            body,
                            next_link=('kena/', 'केनोपनिषद्'),
                            css_path='../css/style.css'))


# ─── Kena (khandas, no adhyayas) ───

def build_kena(soup):
    name = NAMES['kena']
    out_dir = os.path.join(BASE_DIR, 'upanishads', 'kena')
    chapters = soup.find_all('div', class_='chapter')

    # Index page
    items = ''
    for ci, ch in enumerate(chapters):
        cname = ch.get('data-name', f'{ORDINALS[ci]}ः खण्डः')
        items += f'    <li><a href="khanda-{ci+1}.html">{cname}</a></li>\n'
    body = f'  <ul class="text-list">\n{items}  </ul>\n'
    write_file(os.path.join(out_dir, 'index.html'),
               page_html(name,
                        [('../../', 'मुख्यम्'), ('../', 'उपनिषदः'), (None, name)],
                        body,
                        css_path='../../css/style.css'))

    # Section pages
    for ci, ch in enumerate(chapters):
        cname = ch.get('data-name', f'{ORDINALS[ci]}ः खण्डः')
        verses = extract_verses(ch)
        body = ''
        for vid, vtype, text in verses:
            text, num = extract_verse_num_from_text(text)
            if not num:
                m = re.search(r'_V(\d+)', vid)
                num = to_dev(int(m.group(1))) if m else ''
            body += verse_html(text, f'{to_dev(ci+1)}.{num}')

        prev_link = (f'khanda-{ci}.html', chapters[ci-1].get('data-name', '')) if ci > 0 else None
        next_link = (f'khanda-{ci+2}.html', chapters[ci+1].get('data-name', '')) if ci < len(chapters)-1 else None

        write_file(os.path.join(out_dir, f'khanda-{ci+1}.html'),
                   page_html(cname,
                            [('../../', 'मुख्यम्'), ('../', 'उपनिषदः'), ('./', name), (None, cname)],
                            body,
                            prev_link=prev_link,
                            next_link=next_link,
                            css_path='../../css/style.css'))


# ─── Upanishads with adhyaya > section structure (Katha, Mundaka, Taittiriya, etc.) ───

def build_sectioned_upanishad(key, soup, section_label='वल्ली'):
    """For upanishads with adhyaya > section > verse structure."""
    name = NAMES[key]
    out_dir = os.path.join(BASE_DIR, 'upanishads', key)
    chapters = soup.find_all('div', class_='chapter')

    has_sections = any(ch.find('div', class_='section', recursive=False) for ch in chapters)

    if not has_sections:
        # Chapters directly contain verses (like Prashna - 6 prashnas)
        items = ''
        for ci, ch in enumerate(chapters):
            cname = ch.get('data-name', f'{ORDINALS[ci]}ः {section_label}')
            items += f'    <li><a href="section-{ci+1}.html">{cname}</a></li>\n'
        body = f'  <ul class="text-list">\n{items}  </ul>\n'
        write_file(os.path.join(out_dir, 'index.html'),
                   page_html(name,
                            [('../../', 'मुख्यम्'), ('../', 'उपनिषदः'), (None, name)],
                            body,
                            css_path='../../css/style.css'))

        for ci, ch in enumerate(chapters):
            cname = ch.get('data-name', f'{ORDINALS[ci]}ः {section_label}')
            verses = extract_verses(ch)
            body = ''
            for vid, vtype, text in verses:
                text, num = extract_verse_num_from_text(text)
                if not num:
                    m = re.search(r'_V(\d+)', vid)
                    num = to_dev(int(m.group(1))) if m else ''
                body += verse_html(text, num)

            prev_link = (f'section-{ci}.html', chapters[ci-1].get('data-name', '')) if ci > 0 else None
            next_link = (f'section-{ci+2}.html', chapters[ci+1].get('data-name', '')) if ci < len(chapters)-1 else None

            write_file(os.path.join(out_dir, f'section-{ci+1}.html'),
                       page_html(cname,
                                [('../../', 'मुख्यम्'), ('../', 'उपनिषदः'), ('./', name), (None, cname)],
                                body,
                                prev_link=prev_link,
                                next_link=next_link,
                                css_path='../../css/style.css'))
        return

    # Has adhyaya > section structure (Katha, Brihadaranyaka, etc.)
    # Check if we need 2-level navigation
    # For some texts (Katha: 2 adhyayas, 3 vallis each), sections are the leaf pages
    # For Brihadaranyaka: 6 adhyayas, each with named brahmanas

    # Build main index
    items = ''
    for ci, ch in enumerate(chapters):
        cname = ch.get('data-name', f'{ORDINALS[ci]}ोऽध्यायः')
        items += f'    <li><a href="adhyaya-{ci+1}/">{cname}</a></li>\n'
    body = f'  <ul class="text-list">\n{items}  </ul>\n'
    write_file(os.path.join(out_dir, 'index.html'),
               page_html(name,
                        [('../../', 'मुख्यम्'), ('../', 'उपनिषदः'), (None, name)],
                        body,
                        css_path='../../css/style.css'))

    # Build adhyaya pages with section listings
    for ci, ch in enumerate(chapters):
        cname = ch.get('data-name', f'{ORDINALS[ci]}ोऽध्यायः')
        sections = ch.find_all('div', class_='section', recursive=False)
        adh_dir = os.path.join(out_dir, f'adhyaya-{ci+1}')

        items = ''
        for si, sec in enumerate(sections):
            sname = sec.get('data-name', f'{ORDINALS[si]} {section_label}')
            items += f'    <li><a href="section-{si+1}.html">{sname}</a></li>\n'
        body = f'  <ul class="text-list">\n{items}  </ul>\n'
        write_file(os.path.join(adh_dir, 'index.html'),
                   page_html(cname,
                            [('../../../', 'मुख्यम्'), ('../../', 'उपनिषदः'), ('../', name), (None, cname)],
                            body,
                            css_path='../../../css/style.css'))

        # Build section pages
        for si, sec in enumerate(sections):
            sname = sec.get('data-name', f'{ORDINALS[si]} {section_label}')
            verses = extract_verses(sec)
            body = ''
            for vid, vtype, text in verses:
                text, num = extract_verse_num_from_text(text)
                if not num:
                    m = re.search(r'_V(\d+)', vid)
                    num = to_dev(int(m.group(1))) if m else ''
                body += verse_html(text, num)

            prev_link = (f'section-{si}.html', sections[si-1].get('data-name', '')) if si > 0 else None
            next_link = (f'section-{si+2}.html', sections[si+1].get('data-name', '')) if si < len(sections)-1 else None

            write_file(os.path.join(adh_dir, f'section-{si+1}.html'),
                       page_html(sname,
                                [('../../../', 'मुख्यम्'), ('../../', 'उपनिषदः'), ('../', name),
                                 ('./', cname), (None, sname)],
                                body,
                                prev_link=prev_link,
                                next_link=next_link,
                                css_path='../../../css/style.css'))


def build_flat_sectioned_upanishad(key, soup, section_label='खण्डः'):
    """For upanishads with flat chapter structure where each chapter is a section.
    Used for Prashna, Aitareya, Taittiriya."""
    name = NAMES[key]
    out_dir = os.path.join(BASE_DIR, 'upanishads', key)
    chapters = soup.find_all('div', class_='chapter')

    items = ''
    for ci, ch in enumerate(chapters):
        cname = ch.get('data-name', f'{ORDINALS[ci]}')
        items += f'    <li><a href="section-{ci+1}.html">{cname}</a></li>\n'
    body = f'  <ul class="text-list">\n{items}  </ul>\n'
    write_file(os.path.join(out_dir, 'index.html'),
               page_html(name,
                        [('../../', 'मुख्यम्'), ('../', 'उपनिषदः'), (None, name)],
                        body,
                        css_path='../../css/style.css'))

    for ci, ch in enumerate(chapters):
        cname = ch.get('data-name', f'{ORDINALS[ci]}')
        verses = extract_verses(ch)
        body = ''
        for vid, vtype, text in verses:
            text, num = extract_verse_num_from_text(text)
            if not num:
                m = re.search(r'_V(\d+)', vid)
                num = to_dev(int(m.group(1))) if m else ''
            body += verse_html(text, num)

        prev_link = (f'section-{ci}.html', chapters[ci-1].get('data-name', '')) if ci > 0 else None
        next_link = (f'section-{ci+2}.html', chapters[ci+1].get('data-name', '')) if ci < len(chapters)-1 else None

        write_file(os.path.join(out_dir, f'section-{ci+1}.html'),
                   page_html(cname,
                            [('../../', 'मुख्यम्'), ('../', 'उपनिषदः'), ('./', name), (None, cname)],
                            body,
                            prev_link=prev_link,
                            next_link=next_link,
                            css_path='../../css/style.css'))


# ─── Chandogya: adhyaya > khanda (sections within chapters) ───

def build_chandogya(soup):
    """Chandogya has 8 prapathakas, each with khandas as sections."""
    name = NAMES['chandogya']
    out_dir = os.path.join(BASE_DIR, 'upanishads', 'chandogya')
    chapters = soup.find_all('div', class_='chapter')

    items = ''
    for ci, ch in enumerate(chapters):
        cname = ch.get('data-name', f'{ORDINALS[ci]}ः प्रपाठकः')
        items += f'    <li><a href="prapathaka-{ci+1}/">{cname}</a></li>\n'
    body = f'  <ul class="text-list">\n{items}  </ul>\n'
    write_file(os.path.join(out_dir, 'index.html'),
               page_html(name,
                        [('../../', 'मुख्यम्'), ('../', 'उपनिषदः'), (None, name)],
                        body,
                        css_path='../../css/style.css'))

    for ci, ch in enumerate(chapters):
        cname = ch.get('data-name', f'{ORDINALS[ci]}ः प्रपाठकः')
        sections = ch.find_all('div', class_='section', recursive=False)
        pdir = os.path.join(out_dir, f'prapathaka-{ci+1}')

        items = ''
        for si, sec in enumerate(sections):
            sname = sec.get('data-name', f'{ORDINALS[si] if si < len(ORDINALS) else to_dev(si+1)}ः खण्डः')
            items += f'    <li><a href="khanda-{si+1}.html">{sname}</a></li>\n'
        body = f'  <ul class="text-list">\n{items}  </ul>\n'
        write_file(os.path.join(pdir, 'index.html'),
                   page_html(cname,
                            [('../../../', 'मुख्यम्'), ('../../', 'उपनिषदः'), ('../', name), (None, cname)],
                            body,
                            css_path='../../../css/style.css'))

        for si, sec in enumerate(sections):
            sname = sec.get('data-name', f'{ORDINALS[si] if si < len(ORDINALS) else to_dev(si+1)}ः खण्डः')
            verses = extract_verses(sec)
            body = ''
            for vid, vtype, text in verses:
                text, num = extract_verse_num_from_text(text)
                if not num:
                    m = re.search(r'_V(\d+)', vid)
                    num = to_dev(int(m.group(1))) if m else ''
                body += verse_html(text, num)

            prev_link = (f'khanda-{si}.html', sections[si-1].get('data-name', '')) if si > 0 else None
            next_link = (f'khanda-{si+2}.html', sections[si+1].get('data-name', '')) if si < len(sections)-1 else None

            write_file(os.path.join(pdir, f'khanda-{si+1}.html'),
                       page_html(sname,
                                [('../../../', 'मुख्यम्'), ('../../', 'उपनिषदः'), ('../', name),
                                 ('./', cname), (None, sname)],
                                body,
                                prev_link=prev_link,
                                next_link=next_link,
                                css_path='../../../css/style.css'))


# ─── Gita ───

def build_gita(soup):
    name = NAMES['gita']
    out_dir = os.path.join(BASE_DIR, 'gita')
    chapters = soup.find_all('div', class_='chapter')

    items = ''
    for ci, ch in enumerate(chapters):
        yoga = GITA_ADHYAYA_NAMES[ci] if ci < len(GITA_ADHYAYA_NAMES) else ''
        label = f'{ORDINALS[ci]}ोऽध्यायः — {yoga}'
        items += f'    <li><a href="adhyaya-{ci+1}.html">{label}</a></li>\n'
    body = f'  <ul class="text-list">\n{items}  </ul>\n'
    write_file(os.path.join(out_dir, 'index.html'),
               page_html(name,
                        [('../', 'मुख्यम्'), (None, name)],
                        body,
                        css_path='../css/style.css'))

    for ci, ch in enumerate(chapters):
        yoga = GITA_ADHYAYA_NAMES[ci] if ci < len(GITA_ADHYAYA_NAMES) else ''
        title = f'{ORDINALS[ci]}ोऽध्यायः — {yoga}'
        verses = extract_verses(ch)
        body = ''
        for vid, vtype, text in verses:
            text, num = extract_verse_num_from_text(text)
            if not num:
                m = re.search(r'_V(\d+)', vid)
                num = to_dev(int(m.group(1))) if m else ''
            body += verse_html(text, num)

        prev_link = (f'adhyaya-{ci}.html', GITA_ADHYAYA_NAMES[ci-1] if ci > 0 else '') if ci > 0 else None
        next_link = (f'adhyaya-{ci+2}.html', GITA_ADHYAYA_NAMES[ci+1] if ci+1 < len(GITA_ADHYAYA_NAMES) else '') if ci < len(chapters)-1 else None

        write_file(os.path.join(out_dir, f'adhyaya-{ci+1}.html'),
                   page_html(title,
                            [('../', 'मुख्यम्'), ('./', name), (None, title)],
                            body,
                            prev_link=prev_link,
                            next_link=next_link,
                            css_path='../css/style.css'))


# ─── Brahma Sutra ───

def build_brahmasutra(soup):
    name = NAMES['brahmasutra']
    out_dir = os.path.join(BASE_DIR, 'brahmasutra')
    chapters = soup.find_all('div', class_='chapter')

    # Index with adhyayas and padas
    body = ''
    for ci, ch in enumerate(chapters):
        adh_name = BS_ADHYAYA_NAMES[ci] if ci < len(BS_ADHYAYA_NAMES) else ''
        body += f'\n  <h2>{ORDINALS[ci]}ोऽध्यायः — {adh_name}</h2>\n'
        sections = ch.find_all('div', class_='section', recursive=False)
        body += '  <ul class="text-list">\n'
        for si, sec in enumerate(sections):
            sname = sec.get('data-name', f'{ORDINALS[si]}ः पादः')
            body += f'    <li><a href="{ci+1}-{si+1}.html">{sname}</a></li>\n'
        body += '  </ul>\n'

    write_file(os.path.join(out_dir, 'index.html'),
               page_html(name,
                        [('../', 'मुख्यम्'), (None, name)],
                        body,
                        css_path='../css/style.css'))

    # Build flat list of all padas for prev/next linking
    all_padas = []
    for ci, ch in enumerate(chapters):
        sections = ch.find_all('div', class_='section', recursive=False)
        for si, sec in enumerate(sections):
            sname = sec.get('data-name', f'{ORDINALS[si]}ः पादः')
            all_padas.append((ci, si, sec, sname))

    for pi, (ci, si, sec, sname) in enumerate(all_padas):
        adh_name = BS_ADHYAYA_NAMES[ci] if ci < len(BS_ADHYAYA_NAMES) else ''
        title = f'{ORDINALS[ci]}ोऽध्यायः {sname}'
        verses = extract_verses(sec)
        body = ''
        for vid, vtype, text in verses:
            text, num = extract_verse_num_from_text(text)
            if not num:
                m = re.search(r'_V(\d+)', vid)
                num = to_dev(int(m.group(1))) if m else ''
            body += verse_html(text, num)

        prev_link = None
        next_link = None
        if pi > 0:
            pci, psi = all_padas[pi-1][0], all_padas[pi-1][1]
            prev_link = (f'{pci+1}-{psi+1}.html', all_padas[pi-1][3])
        if pi < len(all_padas) - 1:
            nci, nsi = all_padas[pi+1][0], all_padas[pi+1][1]
            next_link = (f'{nci+1}-{nsi+1}.html', all_padas[pi+1][3])

        write_file(os.path.join(out_dir, f'{ci+1}-{si+1}.html'),
                   page_html(title,
                            [('../', 'मुख्यम्'), ('./', name), (None, title)],
                            body,
                            prev_link=prev_link,
                            next_link=next_link,
                            css_path='../css/style.css'))


# ─── Main ───

def main():
    print('Fetching texts from advaitasharada.sringeri.net...\n')

    soups = {}
    for key, url in SOURCES.items():
        soups[key] = fetch(url)

    print('\nGenerating HTML pages...\n')

    # Isha - single page
    print('Building Isha...')
    build_single_page_upanishad('isha', soups['isha'])

    # Kena - 4 khandas
    print('Building Kena...')
    build_kena(soups['kena'])

    # Katha - 2 adhyayas, 3 vallis each (has sections)
    print('Building Katha...')
    build_sectioned_upanishad('katha', soups['katha'], section_label='वल्ली')

    # Prashna - 6 prashnas (flat chapters, no sections within)
    print('Building Prashna...')
    build_flat_sectioned_upanishad('prashna', soups['prashna'], section_label='प्रश्नः')

    # Mundaka - 3 mundakas, 2 khandas each (has sections)
    print('Building Mundaka...')
    build_sectioned_upanishad('mundaka', soups['mundaka'], section_label='खण्डः')

    # Mandukya - single page with karikas
    print('Building Mandukya...')
    build_single_page_upanishad('mandukya', soups['mandukya'])

    # Taittiriya - 3 vallis (flat chapters)
    print('Building Taittiriya...')
    build_flat_sectioned_upanishad('taittiriya', soups['taittiriya'], section_label='वल्ली')

    # Aitareya - 3 adhyayas (flat chapters)
    print('Building Aitareya...')
    build_flat_sectioned_upanishad('aitareya', soups['aitareya'], section_label='अध्यायः')

    # Chandogya - 8 prapathakas with khandas
    print('Building Chandogya...')
    build_chandogya(soups['chandogya'])

    # Brihadaranyaka - 6 adhyayas with brahmanas
    print('Building Brihadaranyaka...')
    build_sectioned_upanishad('brihadaranyaka', soups['brihadaranyaka'], section_label='ब्राह्मणम्')

    # Gita
    print('Building Gita...')
    build_gita(soups['gita'])

    # Brahma Sutra
    print('Building Brahma Sutra...')
    build_brahmasutra(soups['brahmasutra'])

    print('\nDone!')


if __name__ == '__main__':
    main()
