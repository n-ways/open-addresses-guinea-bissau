#!/usr/bin/env python3
"""Check the proximity rule against compounds people drew: re-run the grouping
with every enclosure ignored and see how often a mapped morança or walled plot
(landuse=farmyard, barrier=wall/fence/hedge with 2+ footprints) comes out as one
compound, and how often exactly (nothing from outside added).

  python3 tools/validate-grouping.py <work folder>
"""
import collections, importlib.util, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('bs', os.path.join(HERE, 'building-stats.py'))
sys.argv = [sys.argv[0], sys.argv[1]]
bs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bs)

enc, rows = bs.load()
bs.density(rows)
truth = collections.defaultdict(list)
for k, r in enumerate(rows):
    if r['eid'] and enc[r['eid']]['kind'] in ('osm-farmyard', 'osm-wall', 'osm-fence', 'osm-hedge'):
        truth[r['eid']].append(k)
    r['eid'] = ''  # hide enclosures from the grouping
lab, _ = bs.group({}, rows)
members = collections.defaultdict(set)
for k, l in enumerate(lab):
    members[l].add(k)
res = collections.Counter()
for e, ks in truth.items():
    if len(ks) < 2:
        continue
    kind = enc[e]['kind']
    res[(kind, 'n')] += 1
    labs = {lab[k] for k in ks}
    if len(labs) == 1:
        res[(kind, 'whole')] += 1
        if members[next(iter(labs))] == set(ks):
            res[(kind, 'exact')] += 1
    elif max(sum(1 for k in ks if lab[k] == l) for l in labs) >= len(ks) - 1:
        res[(kind, 'allButOne')] += 1
out = {}
for kind in sorted({k for k, _ in res}):
    n = res[(kind, 'n')]
    out[kind] = {'enclosures': n, 'whole': round(res[(kind, 'whole')] / n, 2), 'exact': round(res[(kind, 'exact')] / n, 2),
                 'allButOneStructure': round(res[(kind, 'allButOne')] / n, 2)}
n = sum(res[(k, 'n')] for k in {k for k, _ in res})
out['all'] = {'enclosures': n, 'whole': round(sum(res[(k, 'whole')] for k in {k for k, _ in res}) / n, 2),
              'exact': round(sum(res[(k, 'exact')] for k in {k for k, _ in res}) / n, 2)}
print(json.dumps(out, indent=1))
p = os.path.join(os.path.dirname(HERE), 'model', 'building-stats.json')
d = json.load(open(p))
d['groupingValidation'] = {'method': 'proximity rule re-run with enclosures hidden, compared with OpenStreetMap-mapped moranças and walled plots of 2+ footprints',
                           'results': out}
json.dump(d, open(p, 'w'), ensure_ascii=False, indent=1)
