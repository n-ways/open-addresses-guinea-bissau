#!/usr/bin/env python3
"""The register the engines ship: engine/data/register.json.

One file with what a decoder needs and nothing about any home: the 39 sectors (number,
key, name, region, spot-grid frame), every area (a place, or a sector's own word at
index 000) with its plate name, official name, aliases, name key, the national number
of its name and its frozen blocks (none yet for a place with no mapped compound), and
the alias table (the key of
an official name or other spelling -> the one plate-name key it decodes to).
Built from model/sectors.json, model/places.json and model/name-ranges.json.

  python3 tools/export_register.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, 'engine', 'reference'))
import gw_codes as gw  # noqa: E402


def main():
    sec = gw.sectors()
    pl = gw.places()
    rng = gw.ranges()
    areas = {}
    # every place and every sector word, with its blocks if it has any (an area
    # with none yet gets its first block with its first code, SPEC 5.2)
    for (s, i), t in pl.items():
        areas[(s, i)] = {'sector': s, 'index': i, 'key3': sec[s]['key'], 'word': t['word'], 'officialName': t.get('officialName') or t['word'],
                         'kind': t['kind'], 'lat': t['lat'], 'lon': t['lon'], 'landmass': t.get('landmass') or '',
                         'needsCouncilChoice': bool(t.get('needsCouncilChoice')), 'raw': t}
    for s in sec:
        areas[(s, 0)] = {'sector': s, 'index': 0, 'key3': sec[s]['key'], 'word': gw.area_word(s, 0), 'officialName': sec[s]['name'],
                         'kind': 'sector', 'lat': None, 'lon': None, 'landmass': '', 'needsCouncilChoice': False, 'raw': None}
    for a in areas.values():
        key = gw.name_key(a['word'])
        rec = rng.get(key)
        if rec is None:
            sys.exit(f"area {a['sector']}-{a['index']}: name {key} has no national number")
        t = a.pop('raw')
        a['aliases'] = [x for x in (t.get('aliases', []) if t else []) if gw.alias_keys().get(gw.name_key(x)) == key]
        a['nameKey'], a['family'] = key, rec['id']
        a['blocks'] = [[b['from'], b['to']] for b in rec['blocks'] if (b['sector'], b['index']) == (a['sector'], a['index'])]
        a['compounds'] = sum(b.get('compounds', 0) for b in rec['blocks'] if (b['sector'], b['index']) == (a['sector'], a['index']))
    areas = list(areas.values())
    areas.sort(key=lambda a: (a['sector'], a['index']))
    out = {'version': 1, 'country': 'GW',
           'note': 'N-Ways Addressing for Guinea-Bissau: the register a decoder needs (no data about any home). Blocks are frozen at first issue; later blocks are only added.',
           'sectors': [{'number': n, 'key': s['key'], 'name': s['name'], 'region': s['region'], 'grid': s['grid']} for n, s in sorted(sec.items())],
           'areas': areas,
           'aliases': dict(sorted(gw.alias_keys().items())),
           'ids': {r['key']: r['id'] for r in sorted(rng.values(), key=lambda r: r['id'])}}
    p = os.path.join(REPO, 'engine', 'data', 'register.json')
    json.dump(out, open(p, 'w'), ensure_ascii=False, separators=(',', ':'))
    print(f'{len(areas)} areas, {len(out["aliases"])} aliases, {len(out["ids"])} names -> {os.path.relpath(p, REPO)}')


if __name__ == '__main__':
    main()
