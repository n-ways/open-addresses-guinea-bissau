#!/usr/bin/env python3
"""The compounds of Guinea-Bissau for issuing their codes (engine/SPEC.md section 7).

Runs the same grouping, place words, blocks and numbering as tools/building-stats.py
(its compute()) on the work folder written by tools/extract-buildings.py, and writes
one JSON line per compound (gzip), sector by sector, for the N-Ways issuer. The
issuer numbers the compounds again with its own implementation of the engine and
refuses the run if any number differs; it keeps every number already issued and only
adds new ones.

  python3 tools/issue_registry.py <work folder> <out lotes.jsonl.gz>

The border decides (SPEC 3.1): the grouping drops every footprint whose centre, and
every compound whose centre, lies more than 300 m outside the national border
(engine/data/border.geojson, from tools/build_border.py), whatever the sector outlines
say, so no building in a neighbouring country is ever listed; the counts printed at the
end show how many (abroadStructure, abroadCompound).

Each line: {"key": the main structure's stable id, "muni": sector key ("BIS"),
"zone": area ref ("BIS-022"), "sector", "index", "number", "lat", "lon" (the
compound's representative point), "anchor": [lat, lon], "anchorKind": "centre",
"gate": null, "coverage": "nways", "official": null, "enclosed", "rule":
"enclosure"|"proximity", "settlement", "structures": [{"id", "src": "osm"|"ml",
"lat", "lon", "areaM2", "perimeterM", "tags", "places", "class", "confidence",
"classSource", "floors", "floorsSource", "wkt"}]} (largest structure first: it is
structure 1, SPEC 5.3).

Structure ids are stable across map updates: OpenStreetMap "osm:way/<id>" or
"osm:relation/<id>"; a Google/Microsoft footprint "nw:" + the first 12 hex characters
of the SHA-1 of its centre to 1e-6 degrees and its area to 1 m2.
"""
import collections
import gzip
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
work, out_path = os.path.abspath(sys.argv[1]), sys.argv[2]
sys.argv = [sys.argv[0], work]
spec = importlib.util.spec_from_file_location('building_stats', os.path.join(HERE, 'building-stats.py'))
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)
gw = B.gw_codes

TAGS = ['building', 'amenity', 'shop', 'office', 'religion', 'tourism', 'healthcare', 'man_made', 'government', 'craft',
        'building:levels', 'height', 'name', 'roof:material', 'building:material']


structure_id = B.structure_id


def main():
    v = B.compute()
    rows, comps, method, cplace, rep, numbers = v['rows'], v['comps'], v['method'], v['cplace'], v['rep'], v['numbers']
    sec = gw.sectors()
    counts = collections.Counter()
    seen = set()
    by_sector = collections.defaultdict(list)
    for cid, ks in comps.items():
        by_sector[cplace[cid][0]].append(cid)
    with gzip.open(out_path, 'wt', encoding='utf-8') as out:
        for s in sorted(by_sector):
            key3 = sec[s]['key']
            cids = sorted(by_sector[s], key=lambda c: (cplace[c][1], numbers[c]))
            for cid in cids:
                ks = sorted(comps[cid], key=lambda k: (-rows[k]['a'], structure_id(rows[k])))
                sts = []
                for k in ks:
                    r = rows[k]
                    tags = {t: r[t] for t in TAGS if r.get(t)}
                    sts.append({'id': structure_id(r), 'src': r['src'], 'lat': round(float(r['lat']), 7), 'lon': round(float(r['lon']), 7),
                                'areaM2': round(float(r['area']), 1), 'perimeterM': round(float(r['perim']), 1), 'tags': tags,
                                'places': [p for p in (r['poi'] or '').split('|') if p], 'class': r['cls'], 'confidence': r['conf'],
                                'classSource': r['clsSrc'], 'floors': r['floors'], 'floorsSource': r['floorsSrc'], 'wkt': r['wkt']})
                k0 = sts[0]['id']
                if k0 in seen:
                    counts['duplicateKey'] += 1
                    continue
                seen.add(k0)
                lat, lon = rep[cid]
                _, idx = cplace[cid]
                m = method[cid]
                rec = {'key': k0, 'muni': key3, 'zone': f'{key3}-{idx:03d}', 'sector': s, 'index': idx, 'number': numbers[cid],
                       'lat': lat, 'lon': lon, 'anchor': [round(lat, 7), round(lon, 7)], 'anchorKind': 'centre',
                       'gate': None, 'coverage': 'nways', 'official': None, 'enclosed': m[0] == 'enclosure', 'rule': m[0],
                       'settlement': rows[ks[0]]['settle'], 'structures': sts}
                out.write(json.dumps(rec, ensure_ascii=False, separators=(',', ':')) + '\n')
                counts['compounds'] += 1
                counts['structures'] += len(sts)
                counts['digits:' + str(len(str(numbers[cid])))] += 1
            print(key3, len(cids), 'compounds', flush=True)
    counts.update(B.DROPPED)
    print(json.dumps(counts))


if __name__ == '__main__':
    main()
