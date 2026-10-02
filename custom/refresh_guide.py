#!/usr/bin/env python3
"""Rebuild guide.xml.gz for channels.m3u from the public XMLTV sources.

Usage: python3 refresh_guide.py [channels.m3u] [guide.xml.gz]
Run it every few hours (cron/systemd timer): the free guides only cover the next 15-48 hours.
Python 3 standard library only.
"""
import gzip, re, sys, io, urllib.request
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

m3u = sys.argv[1] if len(sys.argv) > 1 else 'channels.m3u'
out = sys.argv[2] if len(sys.argv) > 2 else 'guide.xml.gz'
wanted = set(re.findall(r'tvg-id="([^"]+)"', open(m3u, encoding='utf-8').read()))

root = ET.Element('tv', {'generator-info-name': 'custom-iptv'})
progs, found = [], set()
for url in SOURCES:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = urllib.request.urlopen(req, timeout=300).read()
    except Exception as e:
        print(f'skip {url}: {e}', file=sys.stderr)
        continue
    for _, el in ET.iterparse(gzip.GzipFile(fileobj=io.BytesIO(data))):
        if el.tag == 'channel':
            if el.get('id') in wanted and el.get('id') not in found:
                found.add(el.get('id'))
                root.append(el)
            else:
                el.clear()
        elif el.tag == 'programme':
            if el.get('channel') in wanted:
                progs.append(el)
            else:
                el.clear()
root.extend(progs)
tmp = out + '.tmp'
with gzip.open(tmp, 'wb') as f:
    ET.ElementTree(root).write(f, encoding='utf-8', xml_declaration=True)
import os
os.replace(tmp, out)
missing = wanted - found
print(f'{len(found)}/{len(wanted)} channels, {len(progs)} programmes -> {out}')
if missing:
    print('no guide for:', ', '.join(sorted(missing)), file=sys.stderr)
