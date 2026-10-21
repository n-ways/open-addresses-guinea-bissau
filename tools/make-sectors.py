#!/usr/bin/env python3
"""Freeze Guinea-Bissau's sector table (model/sectors.json, engine/data/sectors.geojson).

Input: a GeoJSON FeatureCollection of the 38 OpenStreetMap sectors
(boundary=administrative, admin_level=6) plus the Setor Autonomo de Bissau
(admin_level=3), exported with osmium from the Geofabrik extract:

  osmium tags-filter -o adm.osm.pbf guinea-bissau-latest.osm.pbf r/boundary=administrative
  osmium export -f geojsonseq --geometry-types=polygon adm.osm.pbf  (then keep levels 6 + Bissau)

Writes the frozen sector table: number, key, names, region, the spot-grid
frame (origin, reference latitude, cell size) and a simplified outline
(Douglas-Peucker, 0.0001 deg, about 11 m). Once codes are issued this table
never changes; a later boundary change makes a new table, and codes keep the
sector they were issued in. Standard library only.

  python3 tools/make-sectors.py sectors-raw.geojson
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# number: (OSM name, short key, display name, region ISO)
# First digit = region (1 Bissau, then regions in ISO order), second = sector
# in alphabetical order inside the region. 10-19 are kept for Bissau.
SECTORS = {
    10: ('Sector autónomo de Bissau', 'BIS', 'Bissau', 'GW-BS'),
    21: ('Sector de Bafatá', 'BAF', 'Bafatá', 'GW-BA'),
    22: ('Sector de Bambadinca', 'BAM', 'Bambadinca', 'GW-BA'),
    23: ('Sector de Contuboel', 'CTB', 'Contuboel', 'GW-BA'),
    24: ('Sector de Galomaro', 'GAL', 'Galomaro', 'GW-BA'),
    25: ('Sector de Gã-Mamudo', 'GAM', 'Gã-Mamudo', 'GW-BA'),
    26: ('Sector de Xitole', 'XIT', 'Xitole', 'GW-BA'),
    31: ('Sector de Bolama', 'BOL', 'Bolama', 'GW-BL'),
    32: ('Sector de Bubaque', 'BBQ', 'Bubaque', 'GW-BL'),
    33: ('Sector de Caravela', 'CAR', 'Caravela', 'GW-BL'),
    34: ('Sector de Uno', 'UNO', 'Uno', 'GW-BL'),
    41: ('Sector de Prabis', 'PRA', 'Prábis', 'GW-BM'),
    42: ('Sector de Quinhamel', 'QNH', 'Quinhamel', 'GW-BM'),
    43: ('Sector de Safim', 'SAF', 'Safim', 'GW-BM'),
    51: ('Sector de Bigene', 'BIG', 'Bigene', 'GW-CA'),
    52: ('Sector de Bula', 'BUL', 'Bula', 'GW-CA'),
    53: ('Sector de Cacheu', 'CAC', 'Cacheu', 'GW-CA'),
    54: ('Sector de Caió', 'CAI', 'Caió', 'GW-CA'),
    55: ('Sector de Canchungo', 'CAN', 'Canchungo', 'GW-CA'),
    56: ('Sector de São Domingos', 'SDO', 'São Domingos', 'GW-CA'),
    61: ('Sector de Madina do Boé', 'BOE', 'Boé (Madina do Boé)', 'GW-GA'),
    62: ('Sector de Gabu', 'GAB', 'Gabú', 'GW-GA'),
    63: ('Sector de Pirada', 'PIR', 'Pirada', 'GW-GA'),
    64: ('Sector de Pitche', 'PIT', 'Pitche', 'GW-GA'),
    65: ('Sector de Sonaco', 'SON', 'Sonaco', 'GW-GA'),
    71: ('Sector de Bissorã', 'BSR', 'Bissorã', 'GW-OI'),
    72: ('Sector de Farim', 'FAR', 'Farim', 'GW-OI'),
    73: ('Sector de Mansabá', 'MSB', 'Mansabá', 'GW-OI'),
    74: ('Sector de Mansoa', 'MSO', 'Mansoa', 'GW-OI'),
    75: ('Sector de Nhacra', 'NHA', 'Nhacra', 'GW-OI'),
    81: ('Sector de Buba', 'BUB', 'Buba', 'GW-QU'),
    82: ('Sector de Empada', 'EMP', 'Empada', 'GW-QU'),
    83: ('Sector de Fulacunda', 'FUL', 'Fulacunda', 'GW-QU'),
    84: ('Sector de Tite', 'TIT', 'Tite', 'GW-QU'),
    91: ('Sector de Bedanda', 'BED', 'Bedanda', 'GW-TO'),
    92: ('Sector de Cacine', 'CCN', 'Cacine', 'GW-TO'),
    93: ('Sector de Catió', 'CAT', 'Catió', 'GW-TO'),
    94: ('Sector de Komo', 'KOM', 'Komo', 'GW-TO'),
    95: ('Sector de Quebo', 'QBO', 'Quebo', 'GW-TO'),
}

M_PER_DEG_LAT = 110574.0   # fixed constants of the GW grid (SPEC.md "Spot grid")
M_PER_DEG_LON_EQ = 111320.0
TOL = 0.0001


def dp(pts, tol):
    """Douglas-Peucker on [lng, lat] points (ring closed)."""
    if len(pts) < 5:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        best, bi = -1, -1
        for i in range(a + 1, b):
            x, y = pts[i]
            d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / L if L else math.hypot(x - x1, y - y1)
            if d > best:
                best, bi = d, i
        if best > tol:
            keep[bi] = True
            stack += [(a, bi), (bi, b)]
    out = [p for p, k in zip(pts, keep) if k]
    return out if len(out) >= 4 else pts


def main(src):
    feats = {f['properties']['name']: f for f in json.load(open(src))['features']}
    table, outl = [], []
    for num, (osm, key, name, region) in sorted(SECTORS.items()):
        f = feats[osm]
        g = f['geometry']
        polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        simp = []
        for poly in polys:
            rings = [[[round(x, 5), round(y, 5)] for x, y in dp(r, TOL)] for r in poly]
            if len(rings[0]) >= 4:
                simp.append(rings)
        xs = [p[0] for poly in simp for p in poly[0]]
        ys = [p[1] for poly in simp for p in poly[0]]
        lon0, lat0 = math.floor(min(xs) * 1000) / 1000, math.floor(min(ys) * 1000) / 1000
        lon1, lat1 = math.ceil(max(xs) * 1000) / 1000, math.ceil(max(ys) * 1000) / 1000
        phi0 = round((lat0 + lat1) / 2, 2)
        w = (lon1 - lon0) * math.cos(math.radians(phi0)) * M_PER_DEG_LON_EQ
        h = (lat1 - lat0) * M_PER_DEG_LAT
        cell = math.ceil(max(w, h) / 10000 * 10) / 10  # metres, rounded up to 0.1 m
        table.append({
            'number': num, 'key': key, 'name': name, 'osmName': osm, 'region': region,
            'wikidata': f['properties'].get('wikidata'),
            'grid': {'lon0': lon0, 'lat0': lat0, 'phi0': phi0, 'cellMetres': cell},
            'boxKm': [round(w / 1000, 1), round(h / 1000, 1)],
        })
        outl.append({'type': 'Feature', 'properties': {'number': num, 'key': key, 'name': name},
                     'geometry': {'type': 'MultiPolygon', 'coordinates': simp}})
    meta = {
        'version': 1, 'frozen': None,
        'source': 'OpenStreetMap administrative boundaries (admin_level 6 sectors, admin_level 3 Bissau), Geofabrik extract of 2026-10-17, ODbL 1.0',
        'note': 'Sector numbers: first digit = region (1 Bissau, 2 Bafatá, 3 Bolama, 4 Biombo, 5 Cacheu, 6 Gabú, 7 Oio, 8 Quinara, 9 Tombali); 11-19 reserved for a future split of Bissau.',
        'mPerDegLat': M_PER_DEG_LAT, 'mPerDegLonAtEquator': M_PER_DEG_LON_EQ,
        'sectors': table,
    }
    json.dump(meta, open(os.path.join(REPO, 'model', 'sectors.json'), 'w'), ensure_ascii=False, indent=1)
    json.dump({'type': 'FeatureCollection', 'features': outl}, open(os.path.join(REPO, 'engine', 'data', 'sectors.geojson'), 'w'),
              ensure_ascii=False, separators=(',', ':'))
    for t in table:
        print(t['number'], t['key'], t['name'], t['boxKm'], t['grid']['cellMetres'])


if __name__ == '__main__':
    os.makedirs(os.path.join(REPO, 'engine', 'data'), exist_ok=True)
    main(sys.argv[1])
