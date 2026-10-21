#!/usr/bin/env python3
"""Data tables for the paper's figures (docs/figures/*.dat), computed from the published
registry and the model files. Standard library only; run from anywhere:

    python3 tools/paper_figures.py

Every figure in docs/figures/*.tex reads only the .dat files written here, so the figures
can be rebuilt from the repository alone and checked against the registry."""
import collections, csv, glob, gzip, json, math, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'docs', 'figures')
sys.path.insert(0, os.path.join(REPO, 'engine', 'reference'))
import gw_codes as g  # noqa: E402

# A plain equirectangular projection centred on the country, in kilometres. It is used only
# for drawing; the distortion over Guinea-Bissau's 2.5 degrees of latitude is under 1 %.
LON0, LAT0 = -16.8, 10.8
KX = math.cos(math.radians(12.0)) * 111.32
KY = 110.574


REGION = {'GW-BS': 'Bissau', 'GW-BA': 'Bafatá', 'GW-BL': 'Bolama', 'GW-BM': 'Biombo', 'GW-CA': 'Cacheu',
          'GW-GA': 'Gabú', 'GW-OI': 'Oio', 'GW-QU': 'Quinara', 'GW-TO': 'Tombali'}


def km(lat, lon):
    return (lon - LON0) * KX, (lat - LAT0) * KY


def registry():
    rows = []
    for f in sorted(glob.glob(os.path.join(REPO, 'registry', '*.csv.gz'))):
        if os.path.basename(f) == 'areas.csv.gz':
            continue
        with gzip.open(f, 'rt', encoding='utf-8') as fh:
            rows += list(csv.DictReader(fh))
    with gzip.open(os.path.join(REPO, 'registry', 'areas.csv.gz'), 'rt', encoding='utf-8') as fh:
        areas = {a['area']: a for a in csv.DictReader(fh)}
    return rows, areas


def simplify(pts, tol):
    """Douglas-Peucker on a list of (x, y)."""
    if len(pts) < 3:
        return pts
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy) or 1e-12
    best, idx = -1.0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * (x - x0) - dx * (y - y0)) / n if (dx or dy) else math.hypot(x - x0, y - y0)
        if d > best:
            best, idx = d, i
    if best <= tol:
        return [pts[0], pts[-1]]
    return simplify(pts[:idx + 1], tol)[:-1] + simplify(pts[idx:], tol)


def rings(geom):
    polys = [geom['coordinates']] if geom['type'] == 'Polygon' else geom['coordinates']
    for p in polys:
        yield p[0]                       # outer rings only: the figures draw outlines


def write(name, header, lines):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as fh:
        fh.write(header + '\n')
        for ln in lines:
            fh.write(ln + '\n')


def main():
    os.makedirs(OUT, exist_ok=True)
    rows, areas = registry()

    # 1. Sector outlines and compound density (map.tex)
    sec = json.load(open(os.path.join(REPO, 'engine', 'data', 'sectors.geojson'), encoding='utf-8'))
    out = []
    for f in sec['features']:
        for r in rings(f['geometry']):
            pts = simplify([km(lat, lon) for lon, lat in r], 0.35)
            if len(pts) < 4:
                continue
            out += [f'{x:.2f} {y:.2f}' for x, y in pts] + ['nan nan']
    write('sectors.dat', 'x y', out)
    cells = collections.Counter()
    step = 5.0                           # 5 km cells
    for r in rows:
        x, y = km(float(r['entrance_lat']), float(r['entrance_lng']))
        cells[(int(x // step), int(y // step))] += 1
    write('density.dat', 'x y n', [f'{(i + .5) * step:.1f} {(j + .5) * step:.1f} {n}'
                                   for (i, j), n in sorted(cells.items())])

    # 2. Compounds per area (sizes.tex): areas in logarithmic bins
    per_area = collections.Counter(r['area'] for r in rows)
    edges = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
    hist = collections.Counter()
    for n in per_area.values():
        for k in range(len(edges) - 1):
            if edges[k] <= n < edges[k + 1]:
                hist[k] += 1
                break
    label = [str(e) if n - e == 1 else f'{e}--{n - 1}' for e, n in zip(edges, edges[1:])]
    write('sizes.dat', 'bin label areas', [f'{k} {label[k]} {hist[k]}' for k in range(len(edges) - 1)])

    # 3. One place numbered along the Hilbert curve (bandim.tex): Bandim, Bissau (BIS-022)
    pts = sorted(((int(r['number']), float(r['entrance_lat']), float(r['entrance_lng']))
                  for r in rows if r['area'] == 'BIS-022'))
    lat0 = min(p[1] for p in pts)
    lon0 = min(p[2] for p in pts)
    k = math.cos(math.radians(11.85))
    write('bandim.dat', 'x y n', [f'{(lon - lon0) * k * 111320:.1f} {(lat - lat0) * 110574:.1f} {n}'
                                  for n, lat, lon in pts])

    # 4. One name's national range (blocks.tex): every area called Missirá
    key = g.name_key('Missirá')
    lines = []
    for a in sorted((a for a in areas.values() if a['name_key'] == key and a['blocks']),
                    key=lambda a: int(a['blocks'].split('-')[0])):
        lo, hi = map(int, a['blocks'].split('-'))
        n = per_area[a['area']]
        sector = g.sectors()[int(a['sector'])]['name'].replace(' ', '~')
        lines.append(f'{lo} {hi} {n} {lo + 2 * n} {sector}')
    write('blocks.dat', 'from to compounds firstissue sector', lines)

    # 5. Length of the number (digits.tex): national ranges against one range per area
    nat, own = collections.Counter(), collections.Counter()
    for r in rows:
        nat[len(r['number'])] += 1
    by_area = collections.defaultdict(list)
    for r in rows:
        by_area[r['area']].append(int(r['number']))
    for a, nums in by_area.items():
        # with a range of its own, an area numbered 1, 3, 5 ... would end at 2n - 1
        for k_, _ in enumerate(sorted(nums)):
            own[len(str(1 + 2 * k_))] += 1
    write('digits.dat', 'digits national own', [f'{d} {nat[d]} {own[d]}' for d in range(1, 6)])

    # 6. Bissau's spot grid (spot.tex): sector outline and compounds in grid units of 1,000 cells
    lon0, lat0, kk, s = g._frame(10)
    out = []
    for f in sec['features']:
        if f['properties'].get('number') != 10:
            continue
        for r in rings(f['geometry']):
            pts_ = simplify([((lon - lon0) * kk * g.M_LON_EQ / s / 1000, (lat - lat0) * g.M_LAT / s / 1000)
                             for lon, lat in r], 0.02)
            if len(pts_) >= 4:
                out += [f'{x:.3f} {y:.3f}' for x, y in pts_] + ['nan nan']
    write('bissau.dat', 'x y', out)
    bis = [r for r in rows if r['machine'].startswith('10-')]
    write('bissau-codes.dat', 'x y', [
        f'{(float(r["entrance_lng"]) - lon0) * kk * g.M_LON_EQ / s / 1000:.3f} '
        f'{(float(r["entrance_lat"]) - lat0) * g.M_LAT / s / 1000:.3f}'
        for i, r in enumerate(bis) if i % 25 == 0])

    # 7. Footprint sources by region (sources.tex)
    regs = json.load(open(os.path.join(REPO, 'model', 'regions.json'), encoding='utf-8'))
    lines = []
    for r in sorted(regs, key=lambda r: -r['buildings']['total']):
        name = REGION[r['iso']]
        lines.append(f'{{{name}}} {r["buildings"]["openstreetmap"]} {r["buildings"]["ml"]}')
    write('sources.dat', 'region osm ml', lines)
    # 8. The ordering curve itself (hilbert.tex): order 3, by the engine's own function
    cells = sorted((g.hilbert(i, j, order=3), i, j) for i in range(8) for j in range(8))
    write('hilbert.dat', 'x y d', [f'{i} {j} {d}' for d, i, j in cells])
    print('figure data written to', os.path.relpath(OUT, REPO))


if __name__ == '__main__':
    main()
