#!/usr/bin/env python3
"""Build Guinea-Bissau's place-word table (model/places.json): the bairros,
towns and tabancas whose names start every memorable code ("Bandim 1274").

Inputs (read-only, prepared beforehand in a work folder):
  osm-places.geojsonseq   OpenStreetMap place=* nodes (osmium tags-filter n/place on the
                          Geofabrik extract), ODbL
  geonames-places.csv     N-Ways geo_names rows for GW (OpenStreetMap places and GeoNames
                          localities, CC BY 4.0)
  islands.geojson         OpenStreetMap island/islet polygons (land masses)

Rules (docs/model.md "Place words"):
  * Bissau sector: bairros (OSM place=suburb/neighbourhood) plus the villages and
    localities inside the sector that the city has absorbed (they are bairro names
    today); never "Bissau" itself.
  * Other sectors: towns, villages and hamlets (OSM), then GeoNames localities that
    are not already an OSM place (no OSM place within 400 m and none of the same
    name within 1.5 km).
  * Each place gets its sector (the frozen outlines) and land mass (island polygon or
    mainland), and an index 001-999 inside its sector in Hilbert order.
  * The official name is kept as the source writes it (officialName). The word in the
    code is its plate name: at most 12 characters and 2 words (tools/gw_plates.py,
    engine/reference/plate_names.py); the official name stays an alias where it points to
    one plate name only. No suffix is invented for a repeated name: every place with the same name key (gw_codes.name_key) draws its numbers from
    ONE national range for that name, split into blocks per area (model/name-ranges.json,
    written by tools/building-stats.py), so "Missirá 15" is unique in the whole country.
    A numeral that is part of a real name ("Plaque I", "Plaque II" in Bissau) stays.

  python3 tools/make-places.py <work folder>
"""
import collections, csv, json, math, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, 'engine', 'reference'))
import gw_codes  # noqa: E402
sys.path.insert(0, HERE)
import gw_plates  # noqa: E402

work = os.path.abspath(sys.argv[1])


def plain(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c)).lower().strip()


def unmangle(name):
    """UTF-8 read as Latin-1 in the source ('SanÃº' -> 'Sanú')."""
    if re.search('[ÃÂ][\x80-\xbf]', name):
        try:
            return name.encode('latin-1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return name


def clean(name):
    name = re.sub(r'\s+', ' ', unmangle(name)).strip()
    # 'Bairro de Ajuda' -> 'Ajuda', but 'Bairro Militar' stays: only a prefix + preposition is dropped
    name = re.sub(r'^(Tabanca|Tabanka|Bairro|Aldeia|Povoação)\s+(de|da|do|dos|das)\s+', '', name, flags=re.I)
    # 'Morança Atufa' -> 'Atufa': people say the family's name; the full form stays an alias
    name = re.sub(r'^(Morança|Moransa|Moranza)\s+(de\s+|da\s+|do\s+)?', '', name, flags=re.I)
    return name


def land_masses():
    out = []
    for f in json.load(open(os.path.join(work, 'islands.geojson')))['features']:
        g = f['geometry']
        polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        name = f['properties'].get('name') or ''
        xs = [p[0] for poly in polys for p in poly[0]]
        ys = [p[1] for poly in polys for p in poly[0]]
        area = (max(xs) - min(xs)) * (max(ys) - min(ys))
        out.append((area, name or f"ilhéu {f['properties'].get('@id', '')}", polys, (min(xs), min(ys), max(xs), max(ys))))
    out.sort(key=lambda t: t[0])  # smallest first: an islet inside a bigger island polygon wins
    return out


LM = None


def land_mass(lat, lon):
    global LM
    if LM is None:
        LM = land_masses()
    for _, name, polys, (x0, y0, x1, y1) in LM:
        if x0 <= lon <= x1 and y0 <= lat <= y1:
            for poly in polys:
                if gw_codes._in_ring(lon, lat, poly[0]):
                    return name
    return ''


def main():
    out = os.path.join(REPO, 'model', 'places.json')
    if os.path.exists(out) and json.load(open(out, encoding='utf-8')).get('frozen'):
        sys.exit('model/places.json is frozen (codes are issued against its indices): new places are appended, '
                 'never rebuilt')
    cands = []
    for line in open(os.path.join(work, 'osm-places.geojsonseq')):
        f = json.loads(line.strip('\x1e'))
        p = f['properties']
        kind = p.get('place')
        if kind not in ('city', 'town', 'village', 'hamlet', 'suburb', 'neighbourhood', 'quarter'):
            continue
        name = p.get('name') or p.get('name:pt')
        if not name:
            continue
        name = unmangle(name).strip()
        lon, lat = f['geometry']['coordinates']
        alias = sorted({v for k, v in p.items() if k.startswith(('name:', 'alt_name', 'old_name', 'loc_name')) and v != name} | ({name} if clean(name) != name else set()))
        cands.append({'name': clean(name), 'official': name, 'kind': kind, 'lat': lat, 'lon': lon, 'source': 'osm', 'aliases': alias})
    osm_pts = list(cands)
    for r in csv.DictReader(open(os.path.join(work, 'geonames-places.csv'))):
        if not r['id'].startswith('gn:'):
            continue
        lat, lon = float(r['st_y'] if 'st_y' in r else r[list(r)[4]]), float(r['st_x'] if 'st_x' in r else r[list(r)[3]])
        official = unmangle(r['name']).strip()
        name = clean(official)
        dup = False
        for c in osm_pts:
            d = math.hypot((c['lat'] - lat) * 110574, (c['lon'] - lon) * 108900)
            if d < 400 or (d < 1500 and plain(c['name']) == plain(name)):
                dup = True
                break
        if not dup:
            cands.append({'name': name, 'official': official, 'kind': 'locality', 'lat': lat, 'lon': lon, 'source': 'geonames', 'aliases': []})
    by_sector = collections.defaultdict(list)
    for c in cands:
        s = gw_codes.sector_of(c['lat'], c['lon'])
        if s is None:
            continue
        if s == 10 and c['kind'] in ('city', 'town'):
            continue  # Bissau: bairros, and the old villages inside the sector (Antula, Plack...), not "Bissau" itself
        if s != 10 and c['kind'] in ('suburb', 'neighbourhood', 'quarter') and c['source'] == 'osm':
            c['kind'] = 'bairro'
        c['sector'] = s
        c['landmass'] = land_mass(c['lat'], c['lon'])
        by_sector[s].append(c)
    table = []
    for s, cs in sorted(by_sector.items()):
        # one point per name per 300 m (Bissau has doubled bairro nodes)
        uniq = []
        for c in cs:
            if any(plain(c['name']) == plain(u['name']) and math.hypot((u['lat'] - c['lat']) * 110574, (u['lon'] - c['lon']) * 108900) < 300 for u in uniq):
                continue
            uniq.append(c)
        for c in uniq:
            c['h'] = gw_codes.hilbert(*gw_codes.grid_cell(s, c['lat'], c['lon']))
        uniq.sort(key=lambda c: c['h'])
        for i, c in enumerate(uniq, 1):
            table.append({'sector': s, 'index': i, 'word': c['name'], 'name': c['name'], 'officialName': c['official'], 'kind': c['kind'], 'source': c['source'],
                          'lat': round(c['lat'], 6), 'lon': round(c['lon'], 6), 'landmass': c['landmass'], 'aliases': c['aliases']})
    gw_plates.apply(table)
    # areas per name nationally (place words and the sector words of index 000)
    shared = collections.Counter(gw_codes.name_key(t['word']) for t in table)
    shared.update(gw_codes.name_key(s['name'].split(' (')[0]) for s in gw_codes.sectors().values())
    for t in table:
        t['nameKey'] = gw_codes.name_key(t['word'])
        t['areasWithThisName'] = shared[t['nameKey']]
    meta = {'version': '1', 'frozen': None,
            'sources': 'OpenStreetMap place nodes (ODbL, Geofabrik extract 2026-10-17); GeoNames localities (CC BY 4.0) via N-Ways geo_names',
            'note': 'Frozen at the first issue: a place then keeps its index for ever, and a new name becomes an alias.',
            'places': table}
    json.dump(meta, open(out, 'w'), ensure_ascii=False, indent=0)
    per = collections.Counter(t['sector'] for t in table)
    print(len(table), 'places;', 'max per sector', max(per.values()), 'Bissau bairros', per[10],
          'places sharing a name key', sum(1 for t in table if t['areasWithThisName'] > 1))


if __name__ == '__main__':
    main()
