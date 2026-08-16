#!/usr/bin/env python3
"""Fetch and generate the texts that build.py does not cover.

build.py builds the ten upanishads, the Gita, the Brahmasutra and three
pancharatna stotras from advaitasharada. This script covers the rest:

    advaitasharada      विवेकचूडामणिः, वेदान्तसारः
    sanskritdocuments   अपरोक्षानुभूतिः, अद्वैतमकरन्दः, उपदेशसारम्,
                        कौपीनपञ्चकम्, सद्दर्शनम्, पञ्चीकरणम्,
                        रामगीता, श्वेताश्वतरोपनिषद्

Re-running is safe: a <div class="playlist-links"> block already present in a
page is carried over verbatim, so hand-added playlist rows survive a rebuild.

    python3 import_texts.py            # write pages
    python3 import_texts.py --check    # report what would change, write nothing
"""

import html
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, '.cache_sources')
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')

AS = 'https://advaitasharada.sringeri.net/display/prakarana/{}/devanagari'
SD = 'https://sanskritdocuments.org/{}'

DIGITS = str.maketrans('0123456789', '०१२३४५६७८९')
dev = lambda n: str(n).translate(DIGITS)

# ── source configuration ────────────────────────────────────────────────────

# key -> (url path, folder, title, prev, next, playlist rows)
SANSKRITDOCS = {
 'aparokshanubhuti': ('doc_z_misc_shankara/aparokshaanubhuuti.html', 'prakarana',
    'अपरोक्षानुभूतिः', ('advaitamakaranda.html', 'अद्वैतमकरन्दः'),
    ('atmabodha.html', 'आत्मबोधः'), [(None, 'PL7qtWZUUoJN-gIA65OYeEmiuvNRB_YrWJ')]),
 'advaitamakaranda': ('doc_z_misc_major_works/advaitamakaranda.html', 'prakarana',
    'अद्वैतमकरन्दः', ('advaitanubhuti.html', 'अद्वैतानुभूतिः'),
    ('aparokshanubhuti.html', 'अपरोक्षानुभूतिः'),
    [('धन्योसि', 'PL7qtWZUUoJN8fhF6gzeBUFU7LqHemO_yH')]),
 'upadeshasaram': ('doc_z_misc_major_works/upadeshasAram.html', 'prakarana',
    'उपदेशसारम्', ('atmabodha.html', 'आत्मबोधः'), ('ekashloki.html', 'एकश्लोकी'),
    [('तत्त्वमसि', 'PL7qtWZUUoJN9vsBHWF85GwYFs1ij3t3Gv')]),
 'kaupinapanchakam': ('doc_z_misc_shankara/kaupiina5.html', 'prakarana',
    'कौपीनपञ्चकम्', ('kashipanchakam.html', 'काशीपञ्चकम्'),
    ('tattvabodha.html', 'तत्त्वबोधः'),
    [('तत्त्वमसि', 'PL7qtWZUUoJN8kP2k7RhI72VwYwDia75yl')]),
 'saddarshanam': ('doc_z_misc_general/saddarshanam.html', 'prakarana',
    'सद्दर्शनम्', ('vedantasara.html', 'वेदान्तसारः'),
    ('sadhanapanchakam.html', 'साधनपञ्चकम्'),
    [(None, 'PL7qtWZUUoJN_BOC6rW90M2EONiRwcd7h3')]),
 'panchikaranam': ('doc_z_misc_shankara/paJNchi.html', 'prakarana',
    'पञ्चीकरणम्', ('panchadasi.html', 'पञ्चदशी'),
    ('brahmajnanavali.html', 'ब्रह्मज्ञानावलीमाला'),
    [(None, 'PL7qtWZUUoJN_quGOT3J-HK-drYNBYO85t')]),
 'ramagita': ('doc_giitaa/raamagitaa.html', 'prakarana',
    'रामगीता', ('mayapanchakam.html', 'मायापञ्चकम्'),
    ('laghuvakyavritti.html', 'लघुवाक्यवृत्तिः'), []),
 'shvetashvatara': ('doc_upanishhat/shveta.html', 'upanishads',
    'श्वेताश्वतरोपनिषद्', ('kaivalya.html', 'कैवल्योपनिषद्'), None,
    [('धन्योसि', 'PL7qtWZUUoJN_hTmNunrfqJEoiULsc38zF')]),
}

# Files whose text is followed by a commentary or a duplicate copy that
# restarts numbering at ॥१॥ -- stop the moola at that reset.
STOP_AT_RESET = {'advaitamakaranda', 'upadeshasaram'}

# Header lines the source runs into verse 1 with no blank line between.
DROP_LEAD = {
 'aparokshanubhuti': ('अपरोक्षानुभूतिः',),
 'saddarshanam': ('श्रीभगवद्रमणमहर्षि-विरचित-द्राविडग्रन्थस्य',
                  'संस्कृतानुवादात्मकम्', 'मङ्गलम्'),
 'panchikaranam': ('पञ्चीकरणं अथवा पञ्चीकरणवार्त्तिकम्', 'ॐ',
                   'श्रीमच्छङ्कराचार्यविरचितम् पञ्चीकरणम्',
                   'पञ्चीकरणवार्त्तिकम्', 'श्रीसुरेश्वराचार्यकृत'),
 'shvetashvatara': ('श्वेताश्वतरोपनिषत्',),
}

# Standalone title/attribution blocks (matched on the block's first line).
DROP_BLOCK = {
 'advaitamakaranda': {'अद्वैतमकरन्दः', 'श्रीलक्ष्मीधरकविविरचितः'},
 'kaupinapanchakam': {'कौपीनपञ्चकं अथवा यतिपञ्चकम् सार्थम्', 'कौपीन पंचकम्'},
 'saddarshanam': {'सद्दर्शनम्'},
 'upadeshasaram': {'उपदेशसारं श्रीरमणमहर्षीकृतम्', '॥ उपदेशसारम् ॥'},
 'ramagita': {'श्रीरामगीता'},
 'shvetashvatara': {'श्वेताश्वतरोपनिषत्'},
}

# पञ्चीकरणम् is Shankara's prose tract followed by Suresvara's verse vartika.
SECTIONS = {'panchikaranam': ['पञ्चीकरणम्', 'पञ्चीकरणवार्त्तिकम्']}
PROSE = {'panchikaranam'}          # first section is prose, not shlokas

TERM = re.compile(r'॥\s*([०-९]+)\s*॥?')     # ॥ २९ ॥ and the malformed ॥ २९
CHAPTER = re.compile(r'^(प्रथम|द्वितीय|तृतीय|चतुर्थ|पञ्चम|षष्ठ|सप्तम|अष्टम)ोऽध्यायः')
SPEAKER = re.compile(r'उवाच\s*[-–—]?\s*$')

# ── fetching ────────────────────────────────────────────────────────────────


def fetch(url, name):
    path = os.path.join(CACHE, name)
    if os.path.exists(path):
        return open(path, encoding='utf-8').read()
    os.makedirs(CACHE, exist_ok=True)
    print(f'  fetching {url}')
    r = requests.get(url, headers={'User-Agent': UA,
                                   'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8'})
    r.raise_for_status()
    open(path, 'w', encoding='utf-8').write(r.text)
    return r.text


def to_int(d):
    return int(''.join(str('०१२३४५६७८९'.index(c)) for c in d))


# ── parsing: sanskritdocuments <pre> ────────────────────────────────────────


def sd_units(key):
    """Yield (kind, number, lines). kind: verse|label|chapter|shanti|colophon|plain."""
    path, *_ = SANSKRITDOCS[key]
    soup = BeautifulSoup(fetch(SD.format(path), os.path.basename(path)), 'html.parser')
    text = soup.find_all('pre')[0].get_text()

    lines = []
    for ln in text.split('\n'):                     # drop English translation lines
        if not re.search(r'[ऀ-ॿ]', ln) and re.search(r'[A-Za-z]', ln):
            continue
        lines.append(re.sub(r'\s+', ' ', ln).strip())

    drop_lead = DROP_LEAD.get(key, ())
    stop = key in STOP_AT_RESET
    out, prev, started = [], 0, False
    for blk in [b.strip() for b in re.split(r'\n\s*\n', '\n'.join(lines)) if b.strip()]:
        if CHAPTER.match(blk):
            out.append(('chapter', None, [blk.rstrip(' ।')]))
            prev = 0
            continue
        if not TERM.search(blk):
            kind = 'plain'
            if 'शान्तिः' in blk or 'नाववतु' in blk:
                kind = 'shanti'
            elif blk.startswith('इति') or 'समाप्त' in blk:
                kind = 'colophon'
            out.append((kind, None, blk.split('\n')))
            continue
        pos = 0
        for m in TERM.finditer(blk):
            n = to_int(m.group(1))
            if stop and started and n < prev:
                return out
            started, prev = True, n
            seg = [l.strip() for l in blk[pos:m.start()].split('\n') if l.strip()]
            pos = m.end()
            while seg and seg[0] in drop_lead:
                seg.pop(0)
            while seg and SPEAKER.search(seg[0]):
                out.append(('label', None, [seg.pop(0)]))
            if seg:
                out.append(('verse', n, seg))
        tail = [l.strip() for l in blk[pos:].split('\n') if l.strip()]
        if tail:
            out.append(('plain', None, tail))
    return out


# ── parsing: advaitasharada ─────────────────────────────────────────────────


def as_clean(node):
    s = node.decode_contents()
    s = re.sub(r'<br\s*/?>', '\n', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = html.unescape(s).replace('\xa0', ' ')
    s = re.sub(r'[ \t]+', ' ', s)
    return '\n'.join(l.strip() for l in s.split('\n') if l.strip()).strip()


def split_num(text):
    m = re.search(r'॥\s*([०-९\.]+)\s*॥\s*$', text)
    return (text[:m.start()].rstrip(), m.group(1)) if m else (text, '')


# ── emitting ────────────────────────────────────────────────────────────────


def verse_div(lines, num, cls, ind):
    body = f'\n{ind}    <br />\n{ind}    '.join(lines)
    ns = f'\n{ind}    <span class="verse-num">॥ {num} ॥</span>' if num else ''
    return (f'{ind}<div class="{cls}">\n{ind}  <p class="shloka">\n'
            f'{ind}    {body}{ns}\n{ind}  </p>\n{ind}</div>\n')


def label_div(text, ind):
    return f'{ind}<div class="verse">\n{ind}  <p class="shloka">{text}</p>\n{ind}</div>\n'


def nav_div(prev, nxt, ind, compact=False):
    def side(cls, tgt, lbl):
        if not tgt:
            return f'{ind}  <div class="{cls}"></div>\n'
        if compact:
            return (f'{ind}  <div class="{cls}"><span class="nav-label">{lbl}</span>\n'
                    f'{ind}    <a href="{tgt[0]}">{tgt[1]}</a></div>\n')
        return (f'{ind}  <div class="{cls}">\n{ind}    <span class="nav-label">{lbl}</span>\n'
                f'{ind}    <a href="{tgt[0]}">{tgt[1]}</a>\n{ind}  </div>\n')
    if not prev and not nxt:
        return ''
    return (f'\n{ind}<nav class="page-nav">\n'
            + side('prev', prev, '← पूर्वम्') + side('next', nxt, 'अग्रे →')
            + f'{ind}</nav>\n')


def playlist_div(rows, ind):
    if not rows:
        return ''
    out = ''
    for batch, pid in rows:
        badge = f'{ind}      <span class="playlist-batch">{batch}</span>\n' if batch else ''
        out += (f'{ind}      <div class="playlist-row">\n{badge}'
                f'{ind}        <a href="https://www.youtube.com/playlist?list={pid}" '
                f'target="_blank" rel="noopener" class="playlist-link">▶</a>\n'
                f'{ind}      </div>\n')
    return (f'{ind}<div class="playlist-links">\n{ind}  <details>\n'
            f'{ind}    <summary>पाठाः ▾</summary>\n{ind}    <div class="playlist-panel">\n'
            f'{out}{ind}    </div>\n{ind}  </details>\n{ind}</div>\n')


def keep_playlists(path, rows, ind):
    """Reuse the panel already on disk so hand-added rows survive a rebuild."""
    if os.path.exists(path):
        s = open(path, encoding='utf-8').read()
        m = re.search(r'^([ \t]*)<div class="playlist-links">.*?^\1</div>\n', s, re.M | re.S)
        if m:
            return m.group(0)
    return playlist_div(rows, ind)


HEAD = '''<!doctype html>
<html lang="sa">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title} — ग्रन्थसङ्ग्रहः</title>
    <link rel="stylesheet" href="../css/style.css" />
  </head>
  <body>
    <header class="site-header">
      <div class="container">
        <div class="site-title"><a href="../">ग्रन्थसङ्ग्रहः</a></div>
      </div>
    </header>
'''

CLOSE = '''
    <footer class="site-footer">
      <div class="container">ग्रन्थसङ्ग्रहः</div>
    </footer>

    <script src="../js/script-toggle.js"></script>{extra}
    <script>
      document.addEventListener("click", function (e) {{
        document.querySelectorAll(".playlist-links details[open]").forEach(function (d) {{
          if (!d.contains(e.target)) d.removeAttribute("open");
        }});
      }});
    </script>
  </body>
</html>
'''


def flat_page(title, crumb, body, playlists, prev, nxt):
    return HEAD.format(title=title) + f'''
    <main class="container">
      <nav class="breadcrumb">
        <a href="../">मुख्यम्</a>
        <span class="sep">»</span>
        <a href="./">{crumb}</a>
        <span class="sep">»</span>
        {title}
      </nav>
      <h1>{title}</h1>
{playlists}      <article>
        <div class="group">
{body}        </div>
      </article>
{nav_div(prev, nxt, '      ', compact=True)}    </main>
''' + CLOSE.format(extra='')


def sidebar_page(title, crumb, body, sidebar, playlists, prev, nxt):
    links = '\n'.join(f'            <li><a href="#{a}">{t}</a></li>' for a, t in sidebar)
    return HEAD.format(title=title) + f'''
    <div class="page-with-sidebar">
      <div class="page-content">
        <nav class="breadcrumb">
          <a href="../">मुख्यम्</a>
          <span class="sep">»</span>
          <a href="./">{crumb}</a>
          <span class="sep">»</span>
          {title}
        </nav>
        <h1>{title}</h1>
{playlists}        <article>
          <div class="group">
{body}{nav_div(prev, nxt, '            ')}          </div>
        </article>
      </div>
      <aside class="sidebar">
        <nav>
          <ul>
{links}
          </ul>
        </nav>
      </aside>
    </div>
''' + CLOSE.format(extra='\n    <script src="../js/sidebar-mobile.js"></script>')


# ── builders ────────────────────────────────────────────────────────────────


def build_sd_flat(key):
    path, folder, title, prev, nxt, rows = SANSKRITDOCS[key]
    ind = '          '
    sections, prose = SECTIONS.get(key), key in PROSE
    body, seen_reset, last = '', False, 0
    for kind, n, lines in sd_units(key):
        if kind == 'verse':
            if sections and n == 1 and not last:
                body += f'{ind}<h2 class="section-heading" id="section-1">{sections[0]}</h2>\n'
            elif sections and n == 1 and last:
                seen_reset = True
                body += f'{ind}<h2 class="section-heading" id="section-2">{sections[1]}</h2>\n'
            last = n
            cls = 'verse prose' if (prose and not seen_reset) else 'verse'
            body += verse_div(lines, dev(n), cls, ind)
        elif kind == 'label':
            body += label_div(lines[0], ind)
        elif kind in ('colophon', 'shanti'):
            body += verse_div(lines, '', 'verse shanti', ind)
        elif lines[0] not in DROP_BLOCK.get(key, ()):
            body += verse_div(lines, '', 'verse', ind)
    out = os.path.join(BASE, folder, f'{key}.html')
    pl = keep_playlists(out, rows, '      ')
    return out, flat_page(title, 'प्रकरणग्रन्थाः', body, pl, prev, nxt)


def build_shvetashvatara():
    key = 'shvetashvatara'
    path, folder, title, prev, nxt, rows = SANSKRITDOCS[key]
    ind = '            '
    body, sidebar, ch, pending = '', [], 0, []

    def flush():
        nonlocal body, pending
        if pending:
            body += verse_div(pending, '', 'verse shanti', ind)
            pending = []

    for kind, n, lines in sd_units(key):
        if kind == 'shanti':
            pending += lines
            continue
        flush()
        if kind == 'chapter':
            ch += 1
            sidebar.append((f'section-{ch}', lines[0]))
            body += f'{ind}<h2 class="section-heading" id="section-{ch}">{lines[0]}</h2>\n'
        elif kind == 'verse':
            body += verse_div(lines, f'{dev(ch)}.{dev(n)}', 'verse', ind)
        elif kind == 'colophon':
            body += verse_div(lines, '', 'verse shanti', ind)
        elif lines[0] not in DROP_BLOCK.get(key, ()):
            body += verse_div(lines, '', 'verse', ind)
    flush()
    out = os.path.join(BASE, folder, f'{key}.html')
    pl = keep_playlists(out, rows, '        ')
    return out, sidebar_page(title, 'उपनिषदः', body, sidebar, pl, prev, nxt)


def build_vivekachudamani():
    soup = BeautifulSoup(fetch(AS.format('vivekachudamani'), 'vivekachudamani.html'),
                         'html.parser')
    ch = soup.find('div', class_='chapter')
    ind = '          '
    body = ''
    for v in ch.find_all('div', class_='verse'):
        vt = v.find('div', class_='versetext')
        if not vt:
            continue
        text, num = split_num(as_clean(vt))
        lines = [l for l in text.split('\n') if l]
        # शिष्य उवाच / श्रीगुरुरुवाच carry no number; the count still advances past them
        if not num and lines and 'उवाच' in lines[0]:
            body += label_div(lines[0], ind)
        else:
            body += verse_div(lines, num, 'verse', ind)
    al = ch.find('div', class_='authorline')
    if al:
        body += verse_div(as_clean(al).split('\n'), '', 'verse shanti', ind)
    out = os.path.join(BASE, 'prakarana', 'vivekachudamani.html')
    pl = keep_playlists(out, [('धन्योसि', 'PL7qtWZUUoJN8ErU9e2Sd8ogaQGhUE3n1u')], '      ')
    return out, flat_page('विवेकचूडामणिः', 'प्रकरणग्रन्थाः', body, pl,
                          ('vakyavritti.html', 'वाक्यवृत्तिः'),
                          ('vedantasara.html', 'वेदान्तसारः'))


def build_vedantasara():
    soup = BeautifulSoup(fetch(AS.format('vedantasara'), 'vedantasara.html'), 'html.parser')
    ch = soup.find('div', class_='chapter')
    ind = '          '
    body = ''
    for m in ch.find_all('div', class_='mangala'):
        text, num = split_num(as_clean(m))
        body += verse_div([l for l in text.split('\n') if l], num, 'verse', ind)
    # DOM order is wrong on the source (P16 sits between P05 and P06); id order
    # gives the printed sequence ॥३॥..॥३८॥ exactly.
    for p in sorted(ch.find_all('div', class_='paragraph'), key=lambda d: d.get('id', '')):
        text, num = split_num(as_clean(p))
        body += verse_div([l for l in text.split('\n') if l], num, 'verse prose', ind)
    al = ch.find('div', class_='authorline')
    if al:
        body += verse_div(as_clean(al).split('\n'), '', 'verse shanti', ind)
    out = os.path.join(BASE, 'prakarana', 'vedantasara.html')
    pl = keep_playlists(out, [('धन्योसि', 'PL7qtWZUUoJN_4B5kkH1BuzlFT1tzskxsK')], '      ')
    return out, flat_page('वेदान्तसारः', 'प्रकरणग्रन्थाः', body, pl,
                          ('vivekachudamani.html', 'विवेकचूडामणिः'),
                          ('saddarshanam.html', 'सद्दर्शनम्'))


def main():
    check = '--check' in sys.argv
    pages = [build_vivekachudamani(), build_vedantasara(), build_shvetashvatara()]
    pages += [build_sd_flat(k) for k in SANSKRITDOCS if k != 'shvetashvatara']

    changed = 0
    for path, content in pages:
        rel = os.path.relpath(path, BASE)
        old = open(path, encoding='utf-8').read() if os.path.exists(path) else None
        if old == content:
            print(f'  unchanged  {rel}')
            continue
        changed += 1
        if check:
            print(f'  WOULD CHANGE  {rel}')
        else:
            open(path, 'w', encoding='utf-8').write(content)
            print(f'  wrote      {rel}')
    print(f'\n{len(pages)} pages, {changed} changed'
          + ('  (--check: nothing written)' if check else ''))


if __name__ == '__main__':
    main()
