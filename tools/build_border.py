#!/usr/bin/env python3
"""The national border of Guinea-Bissau (engine/SPEC.md section 3.1), and the check that
no code lies across it.

  python3 tools/build_border.py build <extract.osm.pbf> [--full FILE]
        the OpenStreetMap admin_level=2 relation of Guinea-Bissau (ISO3166-1=GW), its
        ways joined into rings and simplified by Douglas-Peucker at 50 m
        -> engine/data/border.geojson (--full also writes the rings unsimplified, for
        `check --border FILE --limit 300`)
  python3 tools/build_border.py check [--registry registry] [--border FILE] [--limit M]
        counts the codes whose entrance lies more than the limit outside the border;
        exits non-zero if there is any

Reading the extract needs duckdb with its spatial extension (ST_ReadOSM). The extract
must hold the relation whole: a country extract clipped at its own outline usually
misses border ways, and the tool then stops with "the border does not close". Use an
extract of the region, or of the admin_level=2 relations alone
(osmium tags-filter <region>.osm.pbf r/admin_level=2).

The simplified file records how far it strays from the true line at most
(maxDeviationM, measured both ways: every vertex of the true line to the simplified
one, and the simplified line, sampled every 10 m, to the true one) and the limit the
engine applies (limitM): 300 m less that deviation rounded up, less 1 m for the plane
the engine measures on, so a point it accepts is never more than 300 m outside the
true border.
"""
import argparse
import csv
import gzip
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, 'engine', 'data', 'border.geojson')
sys.path.insert(0, os.path.join(REPO, 'engine', 'reference'))
import gw_codes as E  # noqa: E402

ISO = 'GW'
SIMPLIFY_M = 50.0
SAMPLE_M = 10.0
KX = E.M_LON_EQ * math.cos(math.radians(12.0))   # the plane the simplification runs on
KY = E.M_LAT


def read_relation(pbf):
    """(relation id, [(role, [(lon, lat), ...]) per member way, in member order])."""
    sql = f"""
LOAD spatial;
CREATE TABLE o AS SELECT kind, id, tags, refs, ref_roles, ref_types, lat, lon FROM ST_ReadOSM('{pbf}');
CREATE TABLE r AS SELECT id, refs, ref_roles, ref_types FROM o
  WHERE kind = 'relation' AND tags['boundary'] = 'administrative' AND tags['admin_level'] = '2' AND tags['ISO3166-1'] = '{ISO}';
CREATE TABLE m AS SELECT r.id AS rid, unnest(generate_series(1, len(r.refs))) AS pos, unnest(r.refs) AS wid,
  unnest(r.ref_roles) AS role, unnest(r.ref_types) AS t FROM r;
CREATE TABLE w AS SELECT m.rid, m.pos, m.role, unnest(generate_series(1, len(o.refs))) AS k, unnest(o.refs) AS nid
  FROM m JOIN o ON o.kind = 'way' AND o.id = m.wid WHERE m.t = 'way';
COPY (SELECT w.rid, w.pos, w.role, w.k, n.lon, n.lat FROM w JOIN o n ON n.kind = 'node' AND n.id = w.nid
      ORDER BY w.pos, w.k) TO '/dev/stdout' (HEADER, DELIMITER ',');
"""
    r = subprocess.run(['duckdb', '-csv'], input=sql, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('duckdb failed: ' + r.stderr[-3000:])
    rows = list(csv.DictReader(r.stdout.splitlines()))
    if not rows:
        sys.exit(f'no admin_level=2 relation with ISO3166-1={ISO} in {pbf}')
    rids = {row['rid'] for row in rows}
    if len(rids) != 1:
        sys.exit(f'expected one border relation, found {sorted(rids)}')
    ways = {}
    for row in rows:
        ways.setdefault(int(row['pos']), (row['role'] or 'outer', []))[1].append((float(row['lon']), float(row['lat'])))
    return rids.pop(), [ways[p] for p in sorted(ways)]


def join_rings(parts):
    """Member ways joined end to end into closed rings."""
    open_, rings = [list(p) for p in parts if len(p) > 1], []
    while open_:
        ring = open_.pop(0)
        while ring[0] != ring[-1]:
            for i, p in enumerate(open_):
                if p[0] == ring[-1]:
                    ring += p[1:]
                elif p[-1] == ring[-1]:
                    ring += p[-2::-1]
                elif p[-1] == ring[0]:
                    ring = p[:-1] + ring
                elif p[0] == ring[0]:
                    ring = p[:0:-1] + ring
                else:
                    continue
                open_.pop(i)
                break
            else:
                sys.exit(f'the border does not close: a ring stops at {ring[-1]}')
        rings.append(ring)
    return rings


def _seg_d(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def douglas_peucker(pts, tol):
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        best, k = -1.0, None
        for m in range(i + 1, j):
            d = _seg_d(pts[m], pts[i], pts[j])
            if d > best:
                best, k = d, m
        if k is not None and best > tol:
            keep[k] = True
            stack += [(i, k), (k, j)]
    return [p for p, f in zip(pts, keep) if f]


def simplify_ring(ring, tol):
    """A closed ring of (lon, lat) simplified on the plane, split at its first vertex and
    the vertex farthest from it so both halves are open lines."""
    pts = [(x * KX, y * KY) for x, y in ring[:-1]]
    far = max(range(len(pts)), key=lambda i: math.hypot(pts[i][0] - pts[0][0], pts[i][1] - pts[0][1]))
    a = douglas_peucker(pts[:far + 1], tol)
    b = douglas_peucker(pts[far:] + [pts[0]], tol)
    out = a + b[1:]
    if len(out) < 4:
        return ring
    out = [[round(x / KX, 5), round(y / KY, 5)] for x, y in out]
    return out + [out[0]]


class Lines:
    """Segments of (lon, lat) rings; dist() is the engine's metres from a point to the
    nearest of them, on the plane of the point's latitude (as gw_codes.Border measures)."""

    def __init__(self, rings, cell=0.005):
        self.cell, self.segs, self.grid = cell, [], {}
        for ring in rings:
            for i in range(1, len(ring)):
                self.segs.append((tuple(ring[i - 1]), tuple(ring[i])))
        for k, (a, b) in enumerate(self.segs):
            for gx in range(int(math.floor(min(a[0], b[0]) / cell)), int(math.floor(max(a[0], b[0]) / cell)) + 1):
                for gy in range(int(math.floor(min(a[1], b[1]) / cell)), int(math.floor(max(a[1], b[1]) / cell)) + 1):
                    self.grid.setdefault((gx, gy), []).append(k)

    def dist(self, p):
        lon, lat = p
        kx = E.M_LON_EQ * math.cos(math.radians(lat))
        step = self.cell * min(kx, E.M_LAT)
        gx, gy = int(math.floor(lon / self.cell)), int(math.floor(lat / self.cell))
        best = math.inf
        for r in range(1, 400):
            best = math.inf
            for x in range(gx - r, gx + r + 1):
                for y in range(gy - r, gy + r + 1):
                    for k in self.grid.get((x, y), ()):
                        (ax, ay), (bx, by) = self.segs[k]
                        best = min(best, _seg_d((0.0, 0.0), ((ax - lon) * kx, (ay - lat) * E.M_LAT),
                                                ((bx - lon) * kx, (by - lat) * E.M_LAT)))
            if best <= (r - 0.5) * step:   # nothing beyond the searched square can be nearer
                return best
        return best


def deviation(true_rings, simple_rings):
    t, s = Lines(true_rings), Lines(simple_rings)
    worst = max(s.dist(p) for ring in true_rings for p in ring)
    for ring in simple_rings:
        for i in range(1, len(ring)):
            a, b = ring[i - 1], ring[i]
            n = max(1, int(math.hypot((b[0] - a[0]) * KX, (b[1] - a[1]) * KY) // SAMPLE_M))
            for j in range(n + 1):
                worst = max(worst, t.dist((a[0] + (b[0] - a[0]) * j / n, a[1] + (b[1] - a[1]) * j / n)))
    return worst


def build(pbf, full=None):
    rid, members = read_relation(os.path.abspath(pbf))
    roles = {r for r, _ in members}
    if roles - {'outer', 'inner'}:
        sys.exit(f'unexpected member roles {sorted(roles)}')
    outer = join_rings([p for r, p in members if r == 'outer'])
    inner = join_rings([p for r, p in members if r == 'inner'])
    s_out = [simplify_ring(r, SIMPLIFY_M) for r in outer]
    s_in = [simplify_ring(r, SIMPLIFY_M) for r in inner]
    # Each inner ring goes with the outer ring holding it.
    polys = [[r] for r in s_out]
    fpolys = [[[list(p) for p in r]] for r in outer]
    for h, hs in zip(inner, s_in):
        x, y = h[0]
        for k, r in enumerate(outer):
            if E._in_ring(x, y, r):
                polys[k].append(hs)
                fpolys[k].append([list(p) for p in h])
                break
        else:
            sys.exit(f'an inner ring at {h[0]} lies in no outer ring')
    dev = round(deviation(outer + inner, s_out + s_in), 1)
    vertices = sum(len(r) for p in polys for r in p)
    limit = E.BORDER_M - math.ceil(dev) - 1
    doc = {'type': 'Feature',
           'properties': {'country': ISO, 'source': f'OpenStreetMap relation/{rid} (boundary=administrative, admin_level=2), '
                                                    'ODbL, © OpenStreetMap contributors',
                          'simplifiedM': SIMPLIFY_M, 'maxDeviationM': dev, 'borderM': E.BORDER_M, 'limitM': limit},
           'geometry': {'type': 'MultiPolygon', 'coordinates': polys}}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, separators=(',', ':'))
        f.write('\n')
    if full:
        with open(full, 'w', encoding='utf-8') as f:
            json.dump({'type': 'Feature', 'properties': {'country': ISO, 'source': f'OpenStreetMap relation/{rid}',
                                                         'maxDeviationM': 0, 'limitM': E.BORDER_M},
                       'geometry': {'type': 'MultiPolygon', 'coordinates': fpolys}}, f, separators=(',', ':'))
    print(f'relation {rid}: {len(outer)} outer and {len(inner)} inner rings, '
          f'{sum(len(r) for r in outer + inner)} vertices -> {vertices}, largest deviation {dev:.1f} m, '
          f'limit {limit:.0f} m, {os.path.getsize(OUT):,} bytes')


def check(registry, border, limit=None):
    b = E.Border(border or E.BORDER_FILE, limit_m=limit)
    files = sorted(fn for fn in os.listdir(registry) if fn.endswith('.csv.gz') and fn != 'areas.csv.gz')
    total = abroad = 0
    worst, first = 0.0, []
    for fn in files:
        with gzip.open(os.path.join(registry, fn), 'rt', encoding='utf-8', newline='') as f:
            for row in csv.DictReader(f):
                total += 1
                lat, lon = float(row['entrance_lat']), float(row['entrance_lng'])
                d = b.outside_m(lat, lon)
                if d > b.limit:
                    abroad += 1
                    if len(first) < 10:
                        first.append(row['machine'])
                else:
                    worst = max(worst, d)
    print(f'{abroad} of {total:,} codes have their entrance more than {b.limit:.0f} m outside the border'
          + (f' (first: {", ".join(first)})' if first else '')
          + f'; the farthest accepted entrance is {worst:.0f} m outside it')
    return abroad


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('build')
    p.add_argument('pbf')
    p.add_argument('--full')
    c = sub.add_parser('check')
    c.add_argument('--registry', default=os.path.join(REPO, 'registry'))
    c.add_argument('--border', help='a border file (default engine/data/border.geojson)')
    c.add_argument('--limit', type=float, help='metres outside the border allowed (default the file\'s limitM)')
    a = ap.parse_args()
    if a.cmd == 'build':
        build(a.pbf, a.full)
    else:
        sys.exit(1 if check(a.registry, a.border, a.limit) else 0)


if __name__ == '__main__':
    main()
