#!/usr/bin/env python3
"""Builds the server's test fixture from the published registry.

  python3 server/testdata/build.py

registry/   areas.csv.gz (the whole frozen area table), KOM.csv.gz (every code of the Komo
            sector, real rows, unchanged) and a MANIFEST.json for those two files.
parity-points.json
            a sequence of issue requests in Komo: new compounds spread over the islands, a run
            next to Catame (whose block 50-59 fills and takes a continuation block), new
            compounds next to Sàmecá (an area with no block yet) and two extra doors. The
            numbers the issuer gives them are in parity-expected.json.
"""
import gzip
import hashlib
import json
import math
import os
import random
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

from server.engine import Register, ref  # noqa: E402
import csv  # noqa: E402

ZONE = 'KOM'


def main():
    src = os.path.join(REPO, 'registry')
    out = os.path.join(HERE, 'registry')
    os.makedirs(out, exist_ok=True)
    man = json.load(open(os.path.join(src, 'MANIFEST.json'), encoding='utf-8'))
    for name in ('areas.csv.gz', ZONE + '.csv.gz'):
        shutil.copyfile(os.path.join(src, name), os.path.join(out, name))
    rows = gzip.open(os.path.join(out, ZONE + '.csv.gz'), 'rt', encoding='utf-8').read().splitlines()[1:]
    fix = {'country': man['country'], 'engine': man['engine'], 'exported': man['exported'], 'codes': len(rows),
           'bySector': {ZONE: len(rows)}, 'credit': man['credit'], 'licence': man['licence'],
           'sha256': {'areas.csv': man['sha256']['areas.csv'], ZONE + '.csv': man['sha256'][ZONE + '.csv']}}
    with open(os.path.join(out, 'MANIFEST.json'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(fix, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    for name in fix['sha256']:
        assert hashlib.sha256(gzip.open(os.path.join(out, name + '.gz')).read()).hexdigest() == fix['sha256'][name]

    areas = list(csv.DictReader(gzip.open(os.path.join(out, 'areas.csv.gz'), 'rt', encoding='utf-8')))
    reg = Register(areas)
    codes = list(csv.reader(rows))
    taken = [(float(r[10]), float(r[11])) for r in codes]
    rnd = random.Random(94)
    sector = 94

    def clear(lat, lng, m=15.0):
        return all(math.hypot((lat - a) * 110574, (lng - b) * 111320 * math.cos(math.radians(lat))) > m for a, b in taken)

    ops = []

    def add(lat, lng, of=None, area=None):
        op = {'lat': round(lat, 7), 'lng': round(lng, 7)}
        if of:
            op['of'] = of
        if area:
            op['expectArea'] = area
        ops.append(op)
        taken.append((op['lat'], op['lng']))

    # new compounds anywhere on land in the sector
    x0, y0, x1, y1 = ref.sectors()[sector]['box']
    while len(ops) < 10:
        lat, lng = rnd.uniform(y0, y1), rnd.uniform(x0, x1)
        if ref.sector_of(lat, lng) == sector and ref.island_of(lat, lng) and clear(lat, lng):
            add(lat, lng)
    # a run next to Catame (block 50-59 holds one code): fills the block, then a continuation block
    for target, count in (('KOM-012', 12), ('KOM-006', 3)):
        a = reg.by_ref[target]
        got = 0
        while got < count:
            lat, lng = a.lat + rnd.uniform(-0.0012, 0.0012), a.lon + rnd.uniform(-0.0012, 0.0012)
            if ref.sector_of(lat, lng) != sector or not clear(lat, lng):
                continue
            if reg.place_for(sector, lat, lng) is not a:
                continue
            add(lat, lng, area=target)
            got += 1
    # two more doors of issued compounds, 20-40 m from their entrance
    for r in rnd.sample(codes, 2):
        lat, lng = float(r[10]), float(r[11])
        for _ in range(100):
            d, t = rnd.uniform(20, 40), rnd.uniform(0, 2 * math.pi)
            dl, dg = d * math.sin(t) / 110574, d * math.cos(t) / (111320 * math.cos(math.radians(lat)))
            if clear(lat + dl, lng + dg, 4.0):
                add(lat + dl, lng + dg, of=r[0])
                break
    with open(os.path.join(HERE, 'parity-points.json'), 'w', encoding='utf-8') as f:
        json.dump({'zone': ZONE, 'ops': ops}, f, indent=1)
        f.write('\n')
    print(len(rows), 'codes in the fixture,', len(ops), 'issue requests')


if __name__ == '__main__':
    main()
