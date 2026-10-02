#!/usr/bin/env python3
"""Rebuild a slim guide.xml.gz for channels.m3u from public XMLTV sources.

Usage: python3 refresh_guide.py [channels.m3u] [guide.xml.gz]
Keeps only what a TV guide shows (title, episode title, description, category,
episode number) for the next 36 hours; logos come from the playlist instead.
Python 3 standard library only.
"""
import gzip, io, os, re, sys, urllib.request
import datetime as dt
import xml.etree.ElementTree as ET

SOURCES = [
    'https://i.mjh.nz/PlutoTV/all.xml.gz',
    'https://i.mjh.nz/Plex/all.xml.gz',
    'https://i.mjh.nz/Roku/all.xml.gz',
    'https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz',
    'https://epgshare01.online/epgshare01/epg_ripper_ES1.xml.gz',
    'https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz',
    'https://epgshare01.online/epgshare01/epg_ripper_RAKUTEN1.xml.gz',
    'https://epgshare01.online/epgshare01/epg_ripper_CA2.xml.gz',
    'https://epgshare01.online/epgshare01/epg_ripper_AU1.xml.gz',
    'https://epgshare01.online/epgshare01/epg_ripper_SG1.xml.gz',
]
WINDOW_HOURS = 36
KEEP_TEXT = ('title', 'sub-title', 'desc')
# Jellyfin only files a programme under Movies/Kids/News/Sports when a category matches its
# default names exactly, so source synonyms (and Spanish labels) are mapped onto them.
SYNONYMS = {
    'Movie': {'movie', 'movies', 'film', 'films', 'feature', 'feature film', 'película', 'películas', 'pelicula', 'peliculas', 'cine'},
    'Kids': {'kids', 'children', 'infantil', 'niños', 'ninos', 'kids & family', 'animación infantil'},
    'News': {'news', 'news & information', 'noticias', 'newscast', 'informativo', 'informativos'},
    'Sports': {'sport', 'sports', 'deportes', 'deporte'},
}
# Fallback by playlist group when the source gives no usable category.
GROUP_FALLBACK = {
    'News': 'News', 'Latin America — news': 'News',
    'Movies': 'Movie', 'Cine en español': 'Movie',
    'Cartoons & kids': 'Kids', 'Dibujos y anime en español': 'Kids',
}


def parse_time(s):
    m = re.match(r'(\d{14})\s*([+-]\d{4})?', s or '')
    if not m:
        return None
    t = dt.datetime.strptime(m.group(1), '%Y%m%d%H%M%S')
    off = m.group(2) or '+0000'
    delta = dt.timedelta(hours=int(off[1:3]), minutes=int(off[3:5]))
    return (t - delta if off[0] == '+' else t + delta).replace(tzinfo=dt.timezone.utc)


def categories(prog, group):
    cats = []
    for el in prog.findall('category'):
        c = (el.text or '').strip()
        if c and c not in cats:
            cats.append(c)
    lowered = {c.lower() for c in cats}
    for name, words in SYNONYMS.items():
        if lowered & words and name not in cats:
            cats.append(name)
    if not set(cats) & set(SYNONYMS):
        fallback = GROUP_FALLBACK.get(group, 'Series')
        if fallback not in cats:
            cats.append(fallback)
    return cats


def slim(prog, group):
    out = ET.Element('programme', {k: prog.get(k) for k in ('start', 'stop', 'channel')})
    for tag in KEEP_TEXT:
        el = prog.find(tag)
        if el is not None and (el.text or '').strip():
            ET.SubElement(out, tag).text = ' '.join(el.text.split())
    cats = categories(prog, group)
    for c in cats:
        ET.SubElement(out, 'category').text = c
    eps = {e.get('system'): (e.text or '').strip() for e in prog.findall('episode-num')}
    for system in ('xmltv_ns', 'onscreen'):
        if eps.get(system):
            ET.SubElement(out, 'episode-num', {'system': system}).text = eps[system]
            break
    else:
        # Jellyfin lists a programme under Shows only when it has an episode number; ".." is
        # the XMLTV way of saying "an episode, numbering unknown".
        if not set(cats) & set(SYNONYMS):
            ET.SubElement(out, 'episode-num', {'system': 'xmltv_ns'}).text = '..'
    return out


def main():
    m3u = sys.argv[1] if len(sys.argv) > 1 else 'channels.m3u'
    out = sys.argv[2] if len(sys.argv) > 2 else 'guide.xml.gz'
    text = open(m3u, encoding='utf-8').read()
    entries = re.findall(r'tvg-id="([^"]+)" tvg-name="([^"]*)"[^\n]*?group-title="([^"]*)"', text)
    names = {cid: name for cid, name, _ in entries}
    groups = {cid: group for cid, _, group in entries}
    now = dt.datetime.now(dt.timezone.utc)
    end = now + dt.timedelta(hours=WINDOW_HOURS)

    found, progs = set(), {}
    for url in SOURCES:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            data = urllib.request.urlopen(req, timeout=300).read()
        except Exception as e:
            print(f'skip {url}: {e}', file=sys.stderr)
            continue
        claimed = set()
        for _, el in ET.iterparse(gzip.GzipFile(fileobj=io.BytesIO(data))):
            if el.tag == 'channel':
                cid = el.get('id')
                if cid in names and cid not in found:
                    claimed.add(cid)
                el.clear()
            elif el.tag == 'programme':
                cid = el.get('channel')
                if cid in claimed:
                    a, b = parse_time(el.get('start')), parse_time(el.get('stop'))
                    if a and b and b > now and a < end:
                        progs.setdefault(cid, []).append((a, slim(el, groups[cid])))
                el.clear()
        found |= claimed

    root = ET.Element('tv')
    for cid in names:
        if cid in found:
            ET.SubElement(ET.SubElement(root, 'channel', {'id': cid}), 'display-name').text = names[cid]
    count = 0
    for cid in names:
        for _, p in sorted(progs.get(cid, []), key=lambda x: x[0]):
            root.append(p)
            count += 1
    tmp = out + '.tmp'
    with open(tmp, 'wb') as raw, gzip.GzipFile(filename='', fileobj=raw, mode='wb', compresslevel=9, mtime=0) as f:
        ET.ElementTree(root).write(f, encoding='utf-8', xml_declaration=True)
    os.replace(tmp, out)
    missing = set(names) - found
    print(f'{len(found)}/{len(names)} channels, {count} programmes, {os.path.getsize(out) // 1024} KB -> {out}')
    if missing:
        print('no guide for:', ', '.join(sorted(missing)), file=sys.stderr)


if __name__ == '__main__':
    main()
