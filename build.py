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
    'अर्जुनविषादयोगः', 'साङ्ख्ययोगः', 'कर्मयोगः',
    'ज्ञानकर्मसन्न्यासयोगः', 'कर्मसन्न्यासयोगः', 'आत्मसंयमयोगः',
    'ज्ञानविज्ञानयोगः', 'अक्षरब्रह्मयोगः', 'राजविद्याराजगुह्ययोगः',
    'विभूतियोगः', 'विश्वरूपदर्शनयोगः', 'भक्तियोगः',
    'क्षेत्रक्षेत्रज्ञविभागयोगः', 'गुणत्रयविभागयोगः', 'पुरुषोत्तमयोगः',
    'दैवासुरसम्पद्विभागयोगः', 'श्रद्धात्रयविभागयोगः', 'मोक्षसन्न्यासयोगः',
]

BS_ADHYAYA_NAMES = ['समन्वयाध्यायः', 'अविरोधाध्यायः', 'साधनाध्यायः', 'फलाध्यायः']

ORDINALS = ['प्रथम', 'द्वितीय', 'तृतीय', 'चतुर्थ', 'पञ्चम', 'षष्ठ',
            'सप्तम', 'अष्टम', 'नवम', 'दशम', 'एकादश', 'द्वादश',
            'त्रयोदश', 'चतुर्दश', 'पञ्चदश', 'षोडश', 'सप्तदश', 'अष्टादश',
            'एकोनविंश', 'विंश', 'एकविंश', 'द्वाविंश', 'त्रयोविंश', 'चतुर्विंश',
            'पञ्चविंश', 'षड्विंश']

DEVANAGARI_DIGITS = str.maketrans('0123456789', '०१२३४५६७८९')


def to_dev(n):
    return str(n).translate(DEVANAGARI_DIGITS)


def ordinal(i):
    return ORDINALS[i] if i < len(ORDINALS) else to_dev(i + 1)


def clean_verse_text(vt_div):
    content = vt_div.decode_contents()
    content = html.unescape(content)
    content = re.sub(r'<br\s*/?>', '\n', content)
    content = re.sub(r'<[^>]+>', '', content)
    return content.strip()


def verse_html(text, num_label):
    lines = text.split('\n')
    inner = '<br>\n      '.join(line.strip() for line in lines if line.strip())
    return f'''  <div class="verse">
    <div class="shloka">
      {inner} <span class="verse-num">॥ {num_label} ॥</span>
    </div>
  </div>
'''


def breadcrumb_html(crumbs):
    parts = []
    for i, c in enumerate(crumbs):
        if i == len(crumbs) - 1:
            parts.append(c[1])
        else:
            parts.append(f'<a href="{c[0]}">{c[1]}</a>')
    return '<nav class="breadcrumb">\n    ' + '<span class="sep">»</span>'.join(parts) + '\n  </nav>'


def nav_html(prev_link, next_link):
    if not prev_link and not next_link:
        return ''
    prev_part = ''
    next_part = ''
    if prev_link:
        prev_part = f'<span class="nav-label">← पूर्वम्</span>\n      <a href="{prev_link[0]}">{prev_link[1]}</a>'
    if next_link:
        next_part = f'<span class="nav-label">अग्रे →</span>\n      <a href="{next_link[0]}">{next_link[1]}</a>'
    return f'''
  <nav class="page-nav">
    <div class="prev">{prev_part}</div>
    <div class="next">{next_part}</div>
  </nav>
'''


def page_html(title, breadcrumbs, body, prev_link=None, next_link=None, css_path='../css/style.css'):
    bc = breadcrumb_html(breadcrumbs)
    nav = nav_html(prev_link, next_link)
    home = '../' * css_path.count('../')
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
    <div class="site-title"><a href="{home}">ग्रन्थसङ्ग्रहः</a></div>
  </div>
</header>

<main class="container">
  {bc}
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


def sidebar_page_html(title, breadcrumbs, sections_content, sidebar_items,
                      prev_link=None, next_link=None, css_path='../css/style.css'):
    """Page with right sidebar for section navigation.
    sections_content: the main body HTML with section anchors
    sidebar_items: list of (anchor_id, label) for sidebar links
    """
    bc = breadcrumb_html(breadcrumbs)
    nav = nav_html(prev_link, next_link)
    home = '../' * css_path.count('../')

    sidebar_links = '\n'.join(
        f'      <li><a href="#{aid}">{label}</a></li>'
        for aid, label in sidebar_items
    )

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
    <div class="site-title"><a href="{home}">ग्रन्थसङ्ग्रहः</a></div>
  </div>
</header>

<div class="page-with-sidebar">
  <div class="page-content">
    {bc}
    <h1>{title}</h1>
{sections_content}
{nav}
  </div>
  <aside class="sidebar">
    <nav>
      <ul>
{sidebar_links}
      </ul>
    </nav>
  </aside>
</div>

<footer class="site-footer">
  <div class="container">ग्रन्थसङ्ग्रहः</div>
</footer>

</body>
</html>
'''


def fetch(url):
    print(f'  Fetching {url}')
    r = requests.get(url)
    r.raise_for_status()
    return BeautifulSoup(r.text, 'html.parser')


def extract_verses(container):
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


def extract_verse_num(text, vid=''):
    """Extract ॥ N ॥ from end of text, or derive from verse ID."""
    m = re.search(r'॥\s*([०-९\.]+)\s*॥\s*$', text)
    if m:
        return text[:m.start()].rstrip(), m.group(1)
    m2 = re.search(r'_[VK](\d+)', vid)
    if m2:
        return text, to_dev(int(m2.group(1)))
    return text, ''


def verses_body(verses, num_prefix=''):
    """Build verse HTML from list of (id, type, text)."""
    body = ''
    for vid, vtype, text in verses:
        text, num = extract_verse_num(text, vid)
        label = f'{num_prefix}{num}' if num_prefix else num
        if vtype == 'kaarika':
            label = f'कारिका {num}'
        body += verse_html(text, label)
    return body


def slug(text):
    """Make a URL-safe anchor from text."""
    return re.sub(r'[^\w\u0900-\u097F]', '-', text).strip('-')


# ─── Isha (single page, no sections) ───

def build_isha(soup):
    name = NAMES['isha']
    body = verses_body(extract_verses(soup))
    write_file(os.path.join(BASE_DIR, 'upanishads', 'isha.html'),
               page_html(name,
                        [('../', 'मुख्यम्'), ('./', 'उपनिषदः'), (None, name)],
                        body, next_link=('kena.html', 'केनोपनिषद्'),
                        css_path='../css/style.css'))


# ─── Mandukya (single page, prakaranams as sections with sidebar) ───

def build_mandukya(soup):
    name = NAMES['mandukya']
    chapters = soup.find_all('div', class_='chapter')
    prakarana_names = ['आगमप्रकरणम्', 'वैतथ्यप्रकरणम्', 'अद्वैतप्रकरणम्', 'अलातशान्तिप्रकरणम्']

    # Collect all mantras (non-karika) first for the moolam section
    all_mantras = []
    for ch in chapters:
        for vid, vtype, text in extract_verses(ch):
            if vtype != 'kaarika':
                all_mantras.append((vid, vtype, text))

    body = '\n  <h2 class="section-heading" id="moolam">मूलम्</h2>\n\n'
    sidebar = [('moolam', 'मूलम्')]
    for vid, vtype, text in all_mantras:
        text, num = extract_verse_num(text, vid)
        body += verse_html(text, num)

    for ci, ch in enumerate(chapters):
        pname = prakarana_names[ci] if ci < len(prakarana_names) else ch.get('data-name', '')
        aid = slug(pname)
        sidebar.append((aid, pname))
        body += f'\n  <h2 class="section-heading" id="{aid}">{pname}</h2>\n\n'
        for vid, vtype, text in extract_verses(ch):
            text, num = extract_verse_num(text, vid)
            if vtype == 'kaarika':
                label = f'कारिका {num}'
                body += verse_html(text, label)
            else:
                label = num
                body += verse_html(text, label).replace('<div class="verse">', '<div class="verse mantra">', 1)

    write_file(os.path.join(BASE_DIR, 'upanishads', 'mandukya.html'),
               sidebar_page_html(name,
                    [('../', 'मुख्यम्'), ('./', 'उपनिषदः'), (None, name)],
                    body, sidebar,
                    prev_link=('mundaka.html', 'मुण्डकोपनिषद्'),
                    next_link=('taittiriya.html', 'तैत्तिरीयोपनिषद्'),
                    css_path='../css/style.css'))


# ─── Flat texts with sections merged into one page + sidebar ───
# Used for: Kena (khandas), Prashna (prashnas), Taittiriya (vallis), Aitareya (adhyayas)

CHAPTER_NAMES_OVERRIDE = {
    'taittiriya': ['शीक्षावल्ली', 'ब्रह्मानन्दवल्ली', 'भृगुवल्ली'],
}


def build_flat_with_sidebar(key, soup):
    """All chapters merged into one page with sidebar."""
    name = NAMES[key]
    chapters = soup.find_all('div', class_='chapter')
    overrides = CHAPTER_NAMES_OVERRIDE.get(key, [])

    body = ''
    sidebar = []
    for ci, ch in enumerate(chapters):
        cname = overrides[ci] if ci < len(overrides) else ch.get('data-name', f'{ordinal(ci)}')
        aid = f'section-{ci+1}'
        sidebar.append((aid, cname))
        body += f'\n  <h2 class="section-heading" id="{aid}">{cname}</h2>\n\n'
        body += verses_body(extract_verses(ch))

    # Determine prev/next based on upanishad order
    upanishad_order = ['isha', 'kena', 'katha', 'prashna', 'mundaka', 'mandukya',
                       'taittiriya', 'aitareya', 'chandogya', 'brihadaranyaka']
    idx = upanishad_order.index(key) if key in upanishad_order else -1
    prev_link = None
    next_link = None
    if idx > 0:
        pk = upanishad_order[idx - 1]
        prev_link = (get_upanishad_link(pk), NAMES[pk])
    if idx < len(upanishad_order) - 1:
        nk = upanishad_order[idx + 1]
        next_link = (get_upanishad_link(nk), NAMES[nk])

    write_file(os.path.join(BASE_DIR, 'upanishads', f'{key}.html'),
               sidebar_page_html(name,
                    [('../', 'मुख्यम्'), ('./', 'उपनिषदः'), (None, name)],
                    body, sidebar,
                    prev_link=prev_link, next_link=next_link,
                    css_path='../css/style.css'))


def get_upanishad_link(key):
    return f'{key}.html'


# ─── Texts with adhyaya > section: single page with 2-level sidebar ───
# Used for: Katha, Mundaka, Brihadaranyaka, Chandogya

def build_two_level_single_page(key, soup):
    """Entire text on one page. Sidebar shows adhyayas with sections nested."""
    name = NAMES[key]
    chapters = soup.find_all('div', class_='chapter')

    body = ''
    # Build 2-level sidebar HTML manually
    sidebar_html = ''

    for ci, ch in enumerate(chapters):
        cname = ch.get('data-name', f'{ordinal(ci)}ोऽध्यायः')
        ch_aid = f'ch-{ci+1}'
        body += f'\n  <h2 class="section-heading" id="{ch_aid}">{cname}</h2>\n\n'

        sidebar_html += f'      <li><a href="#{ch_aid}" class="sidebar-group-title">{cname}</a>\n'

        sections = ch.find_all('div', class_='section', recursive=False)
        if sections:
            open_class = ' class="open"' if ci == 0 else ''
            sidebar_html += f'        <ul{open_class}>\n'
            for si, sec in enumerate(sections):
                sname = sec.get('data-name', f'{ordinal(si)}')
                sec_aid = f'ch-{ci+1}-s-{si+1}'
                sidebar_html += f'          <li><a href="#{sec_aid}">{sname}</a></li>\n'
                body += f'\n  <h3 class="section-heading" id="{sec_aid}">{sname}</h3>\n\n'
                body += verses_body(extract_verses(sec))
            sidebar_html += '        </ul>\n'
        else:
            body += verses_body(extract_verses(ch))

        sidebar_html += '      </li>\n'

    # Determine prev/next
    upanishad_order = ['isha', 'kena', 'katha', 'prashna', 'mundaka', 'mandukya',
                       'taittiriya', 'aitareya', 'chandogya', 'brihadaranyaka']
    idx = upanishad_order.index(key) if key in upanishad_order else -1
    prev_link = None
    next_link = None
    if idx > 0:
        pk = upanishad_order[idx - 1]
        prev_link = (get_upanishad_link(pk), NAMES[pk])
    if idx < len(upanishad_order) - 1:
        nk = upanishad_order[idx + 1]
        next_link = (get_upanishad_link(nk), NAMES[nk])

    # Use custom sidebar HTML instead of flat sidebar_items
    bc = breadcrumb_html([('../', 'मुख्यम्'), ('./', 'उपनिषदः'), (None, name)])
    nav = nav_html(prev_link, next_link)
    css_path = '../css/style.css'
    home = '../'

    html_out = f'''<!DOCTYPE html>
<html lang="sa">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} — ग्रन्थसङ्ग्रहः</title>
  <link rel="stylesheet" href="{css_path}">
</head>
<body>

<header class="site-header">
  <div class="container">
    <div class="site-title"><a href="{home}">ग्रन्थसङ्ग्रहः</a></div>
  </div>
</header>

<div class="page-with-sidebar">
  <div class="page-content">
    {bc}
    <h1>{name}</h1>
{body}
{nav}
  </div>
  <aside class="sidebar">
    <nav>
      <ul>
{sidebar_html}
      </ul>
    </nav>
  </aside>
</div>

<footer class="site-footer">
  <div class="container">ग्रन्थसङ्ग्रहः</div>
</footer>

<script>
document.querySelectorAll('.sidebar-group-title').forEach(function(el) {{
  el.addEventListener('click', function(e) {{
    var sub = this.nextElementSibling;
    if (sub && sub.tagName === 'UL') {{
      // collapse all others
      document.querySelectorAll('.sidebar ul ul.open').forEach(function(u) {{
        if (u !== sub) u.classList.remove('open');
      }});
      sub.classList.toggle('open');
    }}
  }});
}});
</script>
</body>
</html>
'''
    write_file(os.path.join(BASE_DIR, 'upanishads', f'{key}.html'), html_out)


# ─── Gita ───

def extract_gita_verses(chapter):
    """Gita verses can have two versetext divs: an उवाच line + the actual shloka."""
    results = []
    for v in chapter.find_all('div', class_='verse'):
        vts = v.find_all('div', class_='versetext')
        for vt in vts:
            text = clean_verse_text(vt)
            if not text:
                continue
            is_uvacha = text.endswith('—') or 'उवाच' in text
            results.append((v.get('id', ''), 'uvacha' if is_uvacha else 'shloka', text))
    return results


def build_gita(soup):
    name = NAMES['gita']
    out_dir = os.path.join(BASE_DIR, 'gita')
    chapters = soup.find_all('div', class_='chapter')

    items = ''
    for ci, ch in enumerate(chapters):
        yoga = GITA_ADHYAYA_NAMES[ci] if ci < len(GITA_ADHYAYA_NAMES) else ''
        label = f'{ordinal(ci)}ोऽध्यायः — {yoga}'
        items += f'    <li><a href="adhyaya-{ci+1}.html">{label}</a></li>\n'
    body = f'  <ul class="text-list">\n{items}  </ul>\n'
    write_file(os.path.join(out_dir, 'index.html'),
               page_html(name, [('../', 'मुख्यम्'), (None, name)], body, css_path='../css/style.css'))

    for ci, ch in enumerate(chapters):
        yoga = GITA_ADHYAYA_NAMES[ci] if ci < len(GITA_ADHYAYA_NAMES) else ''
        title = f'{ordinal(ci)}ोऽध्यायः — {yoga}'

        body = ''
        for vid, vtype, text in extract_gita_verses(ch):
            if vtype == 'uvacha':
                # Speaker label — no verse number
                body += f'  <div class="verse">\n    <div class="shloka">{text}</div>\n  </div>\n'
            else:
                text, num = extract_verse_num(text, vid)
                body += verse_html(text, num)

        prev_link = (f'adhyaya-{ci}.html', GITA_ADHYAYA_NAMES[ci-1]) if ci > 0 else None
        next_link = (f'adhyaya-{ci+2}.html', GITA_ADHYAYA_NAMES[ci+1]) if ci < len(chapters)-1 else None

        write_file(os.path.join(out_dir, f'adhyaya-{ci+1}.html'),
                   page_html(title,
                            [('../', 'मुख्यम्'), ('./', name), (None, title)],
                            body, prev_link=prev_link, next_link=next_link,
                            css_path='../css/style.css'))


# ─── Brahma Sutra ───

def extract_bs_verses_with_adhikarana(section):
    """Extract sutras grouped by adhikarana."""
    results = []  # list of (adhikarana_name, adhikarana_id, [(vid, text)])
    current_adh = None
    current_sutras = []
    for v in section.find_all('div', class_='verse'):
        vt = v.find('div', class_='versetext')
        if not vt:
            continue
        text = clean_verse_text(vt)
        adh_name = v.get('data-adhikarana', '')
        adh_id = v.get('data-adhikaranaid', '')
        if adh_name != current_adh:
            if current_adh is not None:
                results.append((current_adh, current_adh_id, current_sutras))
            current_adh = adh_name
            current_adh_id = adh_id
            current_sutras = []
        current_sutras.append((v.get('id', ''), text))
    if current_adh is not None:
        results.append((current_adh, current_adh_id, current_sutras))
    return results


def build_brahmasutra(soup):
    name = NAMES['brahmasutra']
    out_dir = os.path.join(BASE_DIR, 'brahmasutra')
    chapters = soup.find_all('div', class_='chapter')

    # Index — just 4 adhyaya links
    items = ''
    for ci, ch in enumerate(chapters):
        adh_name = BS_ADHYAYA_NAMES[ci] if ci < len(BS_ADHYAYA_NAMES) else ''
        label = f'{ordinal(ci)}ोऽध्यायः — {adh_name}'
        items += f'    <li><a href="adhyaya-{ci+1}.html">{label}</a></li>\n'
    body = f'  <ul class="text-list">\n{items}  </ul>\n'
    write_file(os.path.join(out_dir, 'index.html'),
               page_html(name, [('../', 'मुख्यम्'), (None, name)], body, css_path='../css/style.css'))

    # One page per adhyaya: padas as top-level sidebar, adhikaranas nested
    for ci, ch in enumerate(chapters):
        adh_name = BS_ADHYAYA_NAMES[ci] if ci < len(BS_ADHYAYA_NAMES) else ''
        title = f'{ordinal(ci)}ोऽध्यायः — {adh_name}'
        sections = ch.find_all('div', class_='section', recursive=False)

        body = ''
        sidebar_html = ''

        for si, sec in enumerate(sections):
            sname = sec.get('data-name', f'{ordinal(si)}ः पादः')
            pada_aid = f'pada-{si+1}'
            body += f'\n  <h2 class="section-heading" id="{pada_aid}">{sname}</h2>\n\n'

            sidebar_html += f'      <li><a href="#{pada_aid}" class="sidebar-group-title">{sname}</a>\n'

            adhikaranas = extract_bs_verses_with_adhikarana(sec)
            if adhikaranas:
                open_class = ' class="open"' if si == 0 else ''
                sidebar_html += f'        <ul{open_class}>\n'
                for ai, (adh_name_inner, adh_id, sutras) in enumerate(adhikaranas):
                    adh_aid = f'pada-{si+1}-adh-{ai+1}'
                    sidebar_html += f'          <li><a href="#{adh_aid}">{adh_name_inner}</a></li>\n'
                    body += f'\n  <h3 class="section-heading" id="{adh_aid}">{adh_name_inner}</h3>\n\n'
                    for vid, text in sutras:
                        text, num = extract_verse_num(text, vid)
                        body += verse_html(text, num)
                sidebar_html += '        </ul>\n'

            sidebar_html += '      </li>\n'

        prev_link = (f'adhyaya-{ci}.html', BS_ADHYAYA_NAMES[ci-1]) if ci > 0 else None
        next_link = (f'adhyaya-{ci+2}.html', BS_ADHYAYA_NAMES[ci+1]) if ci < len(chapters)-1 else None

        bc = breadcrumb_html([('../', 'मुख्यम्'), ('./', name), (None, title)])
        nav = nav_html(prev_link, next_link)

        html_out = f'''<!DOCTYPE html>
<html lang="sa">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — ग्रन्थसङ्ग्रहः</title>
  <link rel="stylesheet" href="../css/style.css">
</head>
<body>

<header class="site-header">
  <div class="container">
    <div class="site-title"><a href="../">ग्रन्थसङ्ग्रहः</a></div>
  </div>
</header>

<div class="page-with-sidebar">
  <div class="page-content">
    {bc}
    <h1>{title}</h1>
{body}
{nav}
  </div>
  <aside class="sidebar">
    <nav>
      <ul>
{sidebar_html}
      </ul>
    </nav>
  </aside>
</div>

<footer class="site-footer">
  <div class="container">ग्रन्थसङ्ग्रहः</div>
</footer>

<script>
document.querySelectorAll('.sidebar-group-title').forEach(function(el) {{
  el.addEventListener('click', function(e) {{
    var sub = this.nextElementSibling;
    if (sub && sub.tagName === 'UL') {{
      document.querySelectorAll('.sidebar ul ul.open').forEach(function(u) {{
        if (u !== sub) u.classList.remove('open');
      }});
      sub.classList.toggle('open');
    }}
  }});
}});
</script>
</body>
</html>
'''
        write_file(os.path.join(out_dir, f'adhyaya-{ci+1}.html'), html_out)


# ─── Main ───

def main():
    print('Fetching texts from advaitasharada.sringeri.net...\n')

    soups = {}
    for key, url in SOURCES.items():
        soups[key] = fetch(url)

    print('\nGenerating HTML pages...\n')

    # Single page upanishads
    print('Building Isha...')
    build_isha(soups['isha'])

    # Flat texts -> single page with sidebar
    print('Building Kena...')
    build_flat_with_sidebar('kena', soups['kena'])

    print('Building Prashna...')
    build_flat_with_sidebar('prashna', soups['prashna'])

    print('Building Taittiriya...')
    build_flat_with_sidebar('taittiriya', soups['taittiriya'])

    print('Building Aitareya...')
    build_flat_with_sidebar('aitareya', soups['aitareya'])

    # Mandukya - single page with prakaranam sidebar
    print('Building Mandukya...')
    build_mandukya(soups['mandukya'])

    # Two-level texts -> single page with 2-level sidebar
    print('Building Katha...')
    build_two_level_single_page('katha', soups['katha'])

    print('Building Mundaka...')
    build_two_level_single_page('mundaka', soups['mundaka'])

    print('Building Chandogya...')
    build_two_level_single_page('chandogya', soups['chandogya'])

    print('Building Brihadaranyaka...')
    build_two_level_single_page('brihadaranyaka', soups['brihadaranyaka'])

    # Gita
    print('Building Gita...')
    build_gita(soups['gita'])

    # Brahma Sutra
    print('Building Brahma Sutra...')
    build_brahmasutra(soups['brahmasutra'])

    print('\nDone!')


if __name__ == '__main__':
    main()
