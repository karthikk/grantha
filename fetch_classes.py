#!/usr/bin/env python3
"""Write data/classes/<collection>.json: the first class of every adhikarana.

    python3 fetch_classes.py
    python3 fetch_classes.py --check
"""

import glob
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, 'data')

COLLECTIONS = ('brahmasutra',)

YT = 'https://www.youtube.com/playlist?list='
REF = re.compile(r'(\d+)\.(\d+)\.(\d+)(?:\.[\d-]+)?')
CLASS_NO = re.compile(r'class\s+([\d.]+)', re.I)
ANCHOR = re.compile(r'id="pada-(\d+)-adh-(\d+)"')


def ytdlp(args):
    r = subprocess.run(['yt-dlp'] + args, capture_output=True, text=True)
    if r.returncode != 0:
        tail = (r.stderr.strip().splitlines() or ['no output'])[-1]
        sys.exit('yt-dlp failed: ' + tail)
    return r.stdout


def playlist(list_id):
    url = YT + list_id
    count = ytdlp(['--flat-playlist', '-I', '1',
                   '--print', '%(playlist_count)s', url]).strip()
    count = int(count.splitlines()[-1])
    lines = [l for l in ytdlp(['--flat-playlist', '--print',
                               '%(id)s|%(title)s', url]).splitlines() if '|' in l]
    if len(lines) != count:
        sys.exit('%s: yt-dlp returned %d of %d videos -- it is silently '
                 'truncating the playlist; update yt-dlp' % (list_id, len(lines), count))
    return [l.split('|', 1) for l in lines]


def anchors(cat):
    found = {}
    for path in sorted(glob.glob(os.path.join(BASE, cat, 'adhyaya-*.html'))):
        page = os.path.basename(path)[:-5]
        chapter = int(page.split('-')[1])
        html = open(path, encoding='utf-8').read()
        for pada, adh in ANCHOR.findall(html):
            found[(chapter, int(pada), int(adh))] = (
                page, 'pada-%s-adh-%s' % (pada, adh))
    return found


def first_classes(items, starts):
    first, number = {}, {}
    for vid, title in items:
        if 'delete' in title.lower():
            continue
        n = CLASS_NO.search(title)
        number[vid] = n.group(1) if n else ''
        m = REF.search(title)
        if m:
            ref = tuple(int(x) for x in m.groups())
            first.setdefault(ref, vid)
    for ref, vid in starts.items():
        first[tuple(int(x) for x in ref.split('.'))] = vid
    return first, number


def collect(cat):
    blob = json.load(open(os.path.join(DATA, cat + '.json'), encoding='utf-8'))
    found = anchors(cat)
    pages = {}
    for text in blob['texts']:
        for pl in text.get('playlists') or []:
            if not pl.get('batch'):
                continue
            first, number = first_classes(playlist(pl['list']),
                                          pl.get('starts') or {})
            for ref in sorted(first):
                if ref not in found:
                    continue
                page, anchor = found[ref]
                vid = first[ref]
                pages.setdefault(page, {}).setdefault(anchor, []).append(
                    {'batch': pl['batch'], 'class': number.get(vid, ''),
                     'video': vid})
    return {'pages': dict(sorted(pages.items()))}


def main():
    check = '--check' in sys.argv
    stale = 0
    for cat in COLLECTIONS:
        data = collect(cat)
        marks = sum(len(v) for p in data['pages'].values() for v in p.values())
        path = os.path.join(DATA, 'classes', cat + '.json')
        body = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
        old = open(path, encoding='utf-8').read() if os.path.exists(path) else ''
        if body == old:
            print('  ok     %s (%d marks)' % (cat, marks))
            continue
        stale += 1
        if check:
            print('  STALE  %s' % cat)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, 'w', encoding='utf-8').write(body)
            print('  wrote  %s (%d marks)' % (cat, marks))
    if check and stale:
        sys.exit(1)


if __name__ == '__main__':
    main()
