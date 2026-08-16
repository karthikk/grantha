#!/usr/bin/env python3
"""Keep every page's chrome, and the home listing, in step with data/.

Owns the things that must be identical across all pages and must never drift
from the data files:

  * the body class  -- tier-<tier> cat-<collection>, which drives colour
  * the top bar     -- the way home, and the search input
  * the home page   -- the whole corpus, tier by tier; the only index there is

and converts a page to the two-pane shell if it is not already.

Everything it writes is derived from data/categories.json and data/<cat>.json,
so adding a collection is a data change. Idempotent: running twice is a no-op.

    python3 sync_shell.py           # write
    python3 sync_shell.py --check   # report, write nothing, exit 1 if stale
"""

import glob
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, 'data')

BEGIN = '<!-- shell:begin -->'
END = '<!-- shell:end -->'

HOME_BEGIN = '<!-- home:begin -->'
HOME_END = '<!-- home:end -->'


def load():
    man = json.load(open(os.path.join(DATA, 'categories.json'), encoding='utf-8'))
    order = man['categories']
    tiers = man['tiers']
    cats = {}
    for c in order:
        cats[c] = json.load(open(os.path.join(DATA, c + '.json'), encoding='utf-8'))
    return order, tiers, cats


def dev_name(cat, blob):
    """The collection's own name, in Devanagari, for the tab."""
    NAMES = {
        'upanishads': 'उपनिषदः',
        'gita': 'श्रीमद्भगवद्गीता',
        'brahmasutra': 'ब्रह्मसूत्रम्',
        'prakarana': 'प्रकरणग्रन्थाः',
        'slokas': 'श्लोकाः',
        'sahasranama': 'सहस्रनामानि',
    }
    return NAMES.get(cat, blob['label'])


DEV_DIGITS = '०१२३४५६७८९'


def dev_num(n):
    return ''.join(DEV_DIGITS[int(d)] for d in str(n))


def chapter_label(n, name):
    """'प्रथमोऽध्यायः — अर्जुनविषादयोगः' -> '१ अर्जुनविषादयोगः'.

    The ordinal half only repeats what the number already says, and eighteen
    of them set as running text is a wall. Keep the half that names the
    chapter; the full name is still the <h1> on the chapter's own page.
    """
    short = name.split('—')[-1].strip() if '—' in name else name
    return '<span class="tn">%s</span>%s' % (dev_num(n), short)


def entries(blob):
    """Every readable page in a collection, in reading order.

    A chaptered text (gita, brahmasutra) has no page of its own -- it expands
    into one entry per chapter, which is why chapterNames lives in the data.
    """
    out = []
    for t in blob['texts']:
        if t.get('chapters'):
            pre = t['chapterPrefix']
            names = t.get('chapterNames') or []
            for i in range(t['chapters']):
                n = i + 1
                label = (chapter_label(n, names[i]) if i < len(names)
                         else '<span class="tn">%s</span>' % dev_num(n))
                out.append(('%s/%s%d.html' % (blob['dir'], pre, n), label, None))
        else:
            out.append(('%s/%s.html' % (blob['dir'], t['file']),
                        t['dev'], t.get('group')))
    return out


def tlist(items, indent):
    p = ' ' * indent
    li = '\n'.join('%s  <li><a href="%s">%s</a></li>' % (p, href, dev)
                   for href, dev, _ in items)
    return '%s<ul class="tlist">\n%s\n%s</ul>' % (p, li, p)


def group(label, items, indent=8):
    """A run-in label beside its list of texts."""
    p = ' ' * indent
    return [p + '<div class="grp">',
            p + '  <span class="grp-name">%s</span>' % label,
            tlist(items, indent + 2),
            p + '</div>']


def home_body(order, tiers, cats):
    """The whole corpus, tier by tier. This page is the only index there is.

    Every tier reads the same way: a flat run of labelled groups. What the
    label names depends on whether the collection subdivides itself --

      प्रस्थानत्रयी   उपनिषदः / श्रीमद्भगवद्गीता / ब्रह्मसूत्रम्   (collections)
      प्रकरणग्रन्थाः  भगवत्पादः / विद्यारण्यः / ...                  (authors)
      स्तोत्राणि      गुरुः / शिवः / ... / सहस्रनामानि             (deities)

    -- but the shape on the page is identical, so the eye learns it once.
    """
    out = []
    for tier in tiers:
        here = [c for c in order if cats[c]['tier'] == tier['id']]
        if not here:
            continue
        out.append('      <section class="tier t-%s">' % tier['id'])
        out.append('        <h2 class="tier-name">%s</h2>' % tier['name'])
        for c in here:
            blob = cats[c]
            items = entries(blob)
            groups = blob.get('groups')
            if groups:
                for g in groups:
                    out += group(g, [i for i in items if i[2] == g])
            else:
                out += group(dev_name(c, blob), items)
        out.append('      </section>')
    return '      %s\n%s\n      %s' % (HOME_BEGIN, '\n'.join(out), HOME_END)


def chrome(up):
    """The top bar: the way home, and the way to any text.

    There was a row of collection tabs under this. The home page now lists
    every text in the corpus, so a tab that went to a collection listing had
    nothing left to show -- brand and search are the whole of it.
    """
    return f'''    {BEGIN}
    <header class="topbar">
      <div class="topbar-inner">
        <a class="brand" href="{up or './'}">ग्रन्थसङ्ग्रहः</a>
        <div class="search-home" id="search-home">
          <input
            type="text"
            class="search-input"
            aria-label="search texts"
            autocomplete="off"
            spellcheck="false"
          />
          <div class="search-list" hidden></div>
        </div>
      </div>
    </header>
    {END}
'''


def convert_layout(s, is_index):
    """Old markup -> shell. No-op if already converted."""
    if 'class="shell-body"' in s:
        return s
    rail = '' if is_index else '\n      <nav class="rail" id="rail"></nav>'
    if 'page-with-sidebar' in s:
        s = re.sub(r'[ \t]*<aside class="sidebar">.*?</aside>\n', '', s, flags=re.S)
        s = s.replace('<div class="page-with-sidebar">',
                      '<div class="shell-body">' + rail)
        s = s.replace('<div class="page-content">', '<main class="reading">')
        s = re.sub(r'(\n\s*)</div>(\s*\n\s*</div>\s*\n\s*<footer)', r'\1</main>\2', s, count=1)
    elif '<main class="container">' in s:
        s = s.replace('<main class="container">',
                      '<div class="shell-body">' + rail + '\n      <main class="reading">')
        s = re.sub(r'(\n\s*)</main>(\s*\n\s*<footer)', r'\1</main>\n    </div>\2', s, count=1)
    return s


def sync(path, order, tiers, cats):
    rel = os.path.relpath(path, BASE)
    d = rel.split(os.sep)[0]
    here = d if d in cats else None
    up = '' if os.sep not in rel else '../'

    s = open(path, encoding='utf-8').read()
    orig = s

    is_index = os.path.basename(path) == 'index.html'
    s = convert_layout(s, is_index)

    # an index page IS the list of texts, so a rail repeating it is noise
    if is_index:
        s = re.sub(r'[ \t]*<nav class="rail" id="rail"></nav>\n', '', s)

    # a right-hand aside for this text's sections, filled by js/rail.js
    if not is_index and 'class="onpage"' not in s and 'class="shell-body"' in s:
        s = re.sub(r'(\n\s*</main>)(\s*\n\s*</div>)',
                   r'\1\n      <aside class="onpage" id="onpage"></aside>\2',
                   s, count=1)

    # The breadcrumb is gone. It read "Home » उपनिषदः » कठोपनिषद्": the last
    # crumb repeats the <h1> directly beneath it, the middle one lost its
    # page when the collection listings went, and the brand in the top bar is
    # already the way home. Nothing was left for it to say.
    s = re.sub(r'[ \t]*<nav class="breadcrumb">.*?</nav>\n', '', s, flags=re.S)

    # body class: tier drives colour, collection is kept for the rail
    cls = 'cat-home' if here is None else f'tier-{cats[here]["tier"]} cat-{here}'
    cls += ' shell'
    if is_index:
        cls += ' is-index'
    s = re.sub(r'<body[^>]*>', f'<body class="{cls}">', s, count=1)

    # An earlier layout left a second, brandless top bar sitting outside the
    # markers on a couple of pages, which this script never looked at -- so
    # they rendered two search boxes. Only the managed block may carry one.
    if BEGIN in s:
        head, tail = s.split(END, 1)
        tail = re.sub(r'[ \t]*<header class="topbar">.*?</header>\n\s*\n',
                      '', tail, flags=re.S)
        s = head + END + tail

    # chrome block, replaced wholesale so it can never drift
    block = chrome(up)
    if BEGIN in s:
        # the file already carries the indentation before BEGIN, so the
        # replacement must not bring its own
        s = re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END) + r'\n',
                   block.lstrip(' '), s, flags=re.S)
    else:
        s = re.sub(r'(<body class="[^"]*">\n)', r'\1' + block, s, count=1)

    # the home page's listing, generated so it can never drift from data/
    if rel == 'index.html':
        body = home_body(order, tiers, cats)
        if HOME_BEGIN in s:
            # the file already carries the indentation before the marker, so
            # the replacement must not bring its own -- otherwise every run
            # pushes the block four spaces further right
            pat = re.escape(HOME_BEGIN) + r'.*?' + re.escape(HOME_END)
            rep = body.lstrip(' ')
        else:
            pat = r'(?<=<main class="reading">\n).*?(?=\n\s*</main>)'
            rep = body
        s = re.sub(pat, lambda m: rep, s, count=1, flags=re.S)

    # scripts
    if 'js/rail.js' not in s:
        s = s.replace(f'<script src="{up}js/search.js"></script>',
                      f'<script src="{up}js/rail.js"></script>\n'
                      f'    <script src="{up}js/search.js"></script>')
    return (s, s != orig)


def main():
    check = '--check' in sys.argv
    order, tiers, cats = load()
    pages = sorted(glob.glob(os.path.join(BASE, '*', '*.html')) +
                   glob.glob(os.path.join(BASE, '*.html')))
    stale = 0
    for p in pages:
        out, changed = sync(p, order, tiers, cats)
        if not changed:
            continue
        stale += 1
        rel = os.path.relpath(p, BASE)
        if check:
            print(f'  STALE  {rel}')
        else:
            open(p, 'w', encoding='utf-8').write(out)
            print(f'  wrote  {rel}')
    print(f'\n{len(pages)} pages, {stale} {"stale" if check else "updated"}')
    if check and stale:
        sys.exit(1)


if __name__ == '__main__':
    main()
