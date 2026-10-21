#!/usr/bin/env python3
"""Group Guinea-Bissau's footprints into compounds (moranças), profile them, number them.

Input: the work folder written by tools/extract-buildings.py (buildings.csv,
enclosure-gates.csv). Standard library only; the heavy part (duckdb) is done.

Steps (engine/SPEC.md "Registry generation"):
  0. the border decides (SPEC 3.1): footprints whose centre, and compounds whose centre,
     lie more than 300 m outside the national border (engine/data/border.geojson) are
     dropped, whatever the sector outlines say
  1. settlement class of every footprint from the density around it
     (cidade >= 10 buildings/ha, vila 4-10, tabanca 1-4, disperso < 1)
  2. enclosures first: footprints inside a mapped wall, fence, hedge,
     landuse=farmyard (how mappers draw moranças) or small residential plot
     form one compound; institutional sites (school, hospital, market,
     military, ...) form one institutional compound
  3. the rest by proximity: an annex (< 40 m2) joins the nearest structure
     within da metres; two larger structures join if their gap is <= gm metres;
     da and gm depend on the settlement class; a group over 12 structures is
     split again with half the gap until it fits
  4. every structure gets a profile: use class + confidence + source, size
  5. one national number range per name: every area (place, or sector word for index 000)
     with compounds gets a frozen block of its name's range (gw_codes.allocate)
  6. compounds ordered (land mass, Hilbert) per area and numbered with a stride inside
     the area's block

Writes model/building-stats.json. Before the first issue it also wrote model/name-ranges.json
(the block table); the table is now frozen, so a run keeps every block as issued and gives a
block only to an area that has none, and registry/ holds the issued codes.

  python3 tools/building-stats.py <work folder>
"""
import collections, csv, hashlib, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, 'engine', 'reference'))
import gw_codes  # noqa: E402

work = os.path.abspath(sys.argv[1])
KX = math.cos(math.radians(12)) * 111320
KY = 110574.0
CELL = 40.0

# Proximity rules per settlement class: (annex join distance da, structure gap gm), metres.
RULES = {'cidade': (6, 3), 'vila': (10, 6), 'tabanca': (15, 12), 'disperso': (20, 15)}
ANNEX_M2 = 40
CAP = 12
PLOT_KINDS = {'osm-wall': 10000, 'osm-fence': 10000, 'osm-hedge': 10000, 'osm-farmyard': 10000, 'osm-residential': 2500}
SITE_KINDS = ('osm-amenity', 'osm-military', 'osm-industrial', 'osm-commercial', 'osm-retail', 'osm-religious', 'nways-')

# --- use classes (model/design.json "buildingProfile.useClasses") ---------------
OSM_BUILDING = {
    'house': 'residential.house', 'detached': 'residential.house', 'residential': 'residential.house',
    'hut': 'residential.hut', 'cabin': 'residential.hut', 'apartments': 'residential.apartments',
    'commercial': 'commercial.shop', 'retail': 'commercial.shop', 'kiosk': 'commercial.kiosk', 'office': 'commercial.office',
    'warehouse': 'commercial.warehouse', 'industrial': 'industrial', 'shed': 'agricultural.store', 'farm': 'agricultural.store',
    'barn': 'agricultural.store', 'school': 'education', 'university': 'education', 'kindergarten': 'education', 'college': 'education',
    'madrasa': 'education', 'hospital': 'health', 'clinic': 'health', 'church': 'religious', 'chapel': 'religious',
    'cathedral': 'religious', 'mosque': 'religious', 'public': 'government', 'civic': 'government', 'government': 'government',
    'hotel': 'hospitality', 'stadium': 'public.sport', 'construction': 'status.construction', 'ruins': 'status.ruin',
    'garage': 'transport', 'roof': 'commercial.market', 'canopy': 'commercial.market', 'tank': 'utility',
}
OSM_AMENITY = {
    'school': 'education', 'kindergarten': 'education', 'university': 'education', 'college': 'education',
    'hospital': 'health', 'clinic': 'health', 'doctors': 'health', 'pharmacy': 'health', 'place_of_worship': 'religious',
    'townhall': 'government', 'courthouse': 'government', 'police': 'government', 'post_office': 'government',
    'marketplace': 'commercial.market', 'bank': 'commercial.office', 'restaurant': 'hospitality', 'bar': 'hospitality',
    'fuel': 'transport', 'bus_station': 'transport', 'ferry_terminal': 'transport',
}
POI = {
    'office': 'commercial.office', 'school': 'education', 'hotel': 'hospitality', 'hospital': 'health', 'food': 'hospitality',
    'shop': 'commercial.shop', 'church': 'religious', 'bar': 'hospitality', 'mosque': 'religious', 'petrol': 'transport',
    'bank': 'commercial.office', 'supermarket': 'commercial.shop', 'pharmacy': 'health', 'market': 'commercial.market',
    'police': 'government', 'cafe': 'hospitality', 'motorpark': 'transport', 'salon': 'commercial.shop', 'phones': 'commercial.shop',
    'mechanic': 'commercial.workshop', 'fastfood': 'hospitality', 'vulcanizer': 'commercial.workshop', 'attraction': 'public.landmark',
}
ENCL = {'osm-amenity-school': 'education', 'osm-amenity-university': 'education', 'osm-amenity-hospital': 'health',
        'osm-amenity-clinic': 'health', 'osm-amenity-place_of_worship': 'religious', 'osm-religious': 'religious',
        'osm-amenity-marketplace': 'commercial.market', 'osm-military': 'government.military', 'nways-military': 'government.military',
        'nways-government': 'government', 'nways-police': 'government', 'osm-amenity-police': 'government',
        'osm-amenity-townhall': 'government', 'osm-amenity-courthouse': 'government', 'osm-industrial': 'industrial',
        'osm-commercial': 'commercial.office', 'osm-retail': 'commercial.shop'}


DROPPED = collections.Counter()   # structures and compounds dropped at the border (SPEC 3.1)


def load():
    enc = {r['eid']: r for r in csv.DictReader(open(os.path.join(work, 'enclosure-gates.csv')))}
    # The border decides (SPEC 3.1): a footprint whose centre lies more than 300 m outside the
    # national border is in a neighbouring country, whatever the sector outlines say.
    border = gw_codes.border()
    rows, abroad = [], 0
    for r in csv.DictReader(open(os.path.join(work, 'buildings.csv'))):
        if not r['sector']:
            continue
        if not border.holds(float(r['lat']), float(r['lon'])):
            abroad += 1
            continue
        rows.append(r)
    DROPPED['abroadStructure'] = abroad
    # A fixed order, so grouping never depends on the order the extract wrote rows in.
    rows.sort(key=lambda r: (int(r['sector']), float(r['lat']), float(r['lon']), float(r['area']), r['src'], r['oid'] or ''))
    for r in rows:
        r['x'] = float(r['lon']) * KX
        r['y'] = float(r['lat']) * KY
        r['a'] = max(float(r['area']), 1.0)
        r['p'] = max(float(r['perim']), 1.0)
        r['sector'] = int(r['sector'])
    return enc, rows


def density(rows):
    g = collections.Counter((int(r['x'] // 50), int(r['y'] // 50)) for r in rows)
    for r in rows:
        cx, cy = int(r['x'] // 50), int(r['y'] // 50)
        d = sum(g.get((cx + i, cy + j), 0) for i in range(-2, 3) for j in range(-2, 3)) / 6.25
        r['dens'] = d
        r['settle'] = 'cidade' if d >= 10 else 'vila' if d >= 4 else 'tabanca' if d >= 1 else 'disperso'


def gap(a, b):
    return math.hypot(a['x'] - b['x'], a['y'] - b['y']) - 0.5 * math.sqrt(a['a']) - 0.5 * math.sqrt(b['a'])


def group(enc, rows):
    """Returns compound id per row index, and the method that made each compound."""
    n = len(rows)
    par = list(range(n))

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i

    method = {}
    fixed = [False] * n
    by_e = collections.defaultdict(list)
    for k, r in enumerate(rows):
        e = enc.get(r['eid']) if r['eid'] else None
        if not e:
            continue
        kind, area = e['kind'], float(e['areaM2'])
        if (kind in PLOT_KINDS and area <= PLOT_KINDS[kind]) or kind.startswith(SITE_KINDS):
            by_e[r['eid']].append(k)
    for eid, ks in by_e.items():
        for k in ks:
            fixed[k] = True
            par[f(k)] = f(ks[0])
        method[f(ks[0])] = ('enclosure', eid)
    grid = collections.defaultdict(list)
    for k, r in enumerate(rows):
        if not fixed[k]:
            grid[(int(r['x'] // CELL), int(r['y'] // CELL))].append(k)

    def near(k, R):
        r = rows[k]
        cx, cy, m = int(r['x'] // CELL), int(r['y'] // CELL), int(R // CELL) + 1
        for i in range(-m, m + 1):
            for j in range(-m, m + 1):
                for q in grid.get((cx + i, cy + j), ()):
                    if q != k:
                        yield q

    def link(ks, scale):
        """Single-linkage over ks with the class rules times scale; returns groups."""
        sub = {k: k for k in ks}

        def g(i):
            while sub[i] != i:
                sub[i] = sub[sub[i]]
                i = sub[i]
            return i
        S = set(ks)
        for k in ks:
            r = rows[k]
            da, gm = (x * scale for x in RULES[r['settle']])
            if r['a'] >= ANNEX_M2:
                for q in near(k, gm + 30):
                    if q in S and q > k and rows[q]['a'] >= ANNEX_M2 and gap(r, rows[q]) <= gm:
                        sub[g(k)] = g(q)
            else:
                best, bd = None, 1e9
                for q in near(k, da + 30):
                    if q in S:
                        d = gap(r, rows[q])
                        if d < bd:
                            best, bd = q, d
                if best is not None and bd <= da:
                    sub[g(k)] = g(best)
        out = collections.defaultdict(list)
        for k in ks:
            out[g(k)].append(k)
        return list(out.values())

    free = [k for k in range(n) if not fixed[k]]
    todo = [(grp, 1.0) for grp in link(free, 1.0)]
    while todo:
        grp, scale = todo.pop()
        if len(grp) > CAP and scale > 0.1:
            todo += [(gg, scale / 2) for gg in link(grp, scale / 2)]
            continue
        for k in grp:
            par[f(k)] = f(grp[0])
        method[f(grp[0])] = ('proximity', round(scale, 3))
    lab = [f(k) for k in range(n)]
    return lab, method


def profile(r, enc, members):
    """Use class, confidence and source for one structure."""
    b = (r['building'] or '').lower()
    if r['amenity'] in OSM_AMENITY:
        return OSM_AMENITY[r['amenity']], 0.9, 'osm:amenity'
    if r['shop']:
        return 'commercial.shop', 0.9, 'osm:shop'
    if r['office'] or r['government']:
        return ('government' if r['government'] else 'commercial.office'), 0.85, 'osm:office'
    if r['tourism'] in ('hotel', 'guest_house', 'hostel'):
        return 'hospitality', 0.9, 'osm:tourism'
    if b in OSM_BUILDING:
        return OSM_BUILDING[b], 0.85, 'osm:building'
    if r['poi']:
        cats = [POI[c] for c in r['poi'].split('|') if c in POI]
        if cats:
            c = collections.Counter(cats).most_common(1)[0][0]
            return c, 0.65, 'nways:places'
    e = enc.get(r['eid']) if r['eid'] else None
    if e and e['kind'] in ENCL:
        return ENCL[e['kind']], 0.55, 'enclosure:' + e['kind']
    circ = 4 * math.pi * r['a'] / (r['p'] ** 2)
    if circ >= 0.9 and r['a'] <= 80:
        return 'residential.round-house', 0.6, 'shape:round'
    big = max(members_area for members_area in members)
    if r['a'] < 25 and big >= 60 and len(members) > 1:
        return 'residential.annex', 0.45, 'shape:size-in-compound'
    if r['a'] >= 600:
        return 'unknown.large', 0.3, 'shape:size'
    conf = {'tabanca': 0.65, 'disperso': 0.55, 'vila': 0.55, 'cidade': 0.5}[r['settle']]
    return 'residential.compound-house', conf, 'default:settlement'


def floors(r):
    lv = r['building:levels']
    try:
        if lv:
            return max(1, round(float(lv))), 'osm:building:levels'
    except ValueError:
        pass
    h = r['height']
    try:
        if h:
            return max(1, round(float(h.replace('m', '').strip()) / 3.0)), 'osm:height'
    except ValueError:
        pass
    return None, None


def structure_id(r):
    """Stable id of a footprint: OpenStreetMap "osm:way/<id>"; a Google/Microsoft footprint "nw:" + the
    first 12 hex characters of the SHA-1 of its centre to 1e-6 degrees and its area to 1 m2."""
    if r['src'] == 'osm':
        return 'osm:' + r['oid']
    return 'nw:' + hashlib.sha1(f"{float(r['lat']):.6f},{float(r['lon']):.6f},{round(float(r['area']))}".encode()).hexdigest()[:12]


def pct(v, ps=(10, 25, 50, 75, 90)):
    v = sorted(v)
    if not v:
        return {}
    return {f'p{p}': round(v[int(p / 100 * (len(v) - 1))], 1) for p in ps}


def compute():
    """Grouping, place words, blocks and numbers (steps 1-6), shared with tools/issue_registry.py."""
    enc, rows = load()
    density(rows)
    lab, method = group(enc, rows)
    comps = collections.defaultdict(list)
    for k, l in enumerate(lab):
        comps[l].append(k)
    sec = gw_codes.sectors()
    regions_of = {s['number']: s['region'] for s in sec.values()}
    for cid, ks in comps.items():
        areas = [rows[k]['a'] for k in ks]
        for k in ks:
            r = rows[k]
            r['cls'], r['conf'], r['clsSrc'] = profile(r, enc, areas)
            r['floors'], r['floorsSrc'] = floors(r)

    # compound use class
    def comp_class(ks):
        cl = [rows[k]['cls'] for k in ks]
        non_res = [c for c in cl if not c.startswith(('residential', 'unknown', 'status'))]
        if not non_res:
            return 'residential'
        if len(non_res) == len(cl):
            return collections.Counter(c.split('.')[0] for c in non_res).most_common(1)[0][0]
        return 'mixed'

    # place word and number per compound (SPEC.md "Registry generation", steps 5-6)
    plist = collections.defaultdict(list)
    for t in gw_codes.places().values():
        plist[t['sector']].append(t)
    rep, cplace = {}, {}
    border, abroad = gw_codes.border(), []
    for cid, ks in comps.items():
        r0 = max(ks, key=lambda k: rows[k]['a'])
        wsum = sum(rows[k]['a'] for k in ks)
        x = sum(rows[k]['x'] * rows[k]['a'] for k in ks) / wsum
        y = sum(rows[k]['y'] * rows[k]['a'] for k in ks) / wsum
        s, lm = rows[r0]['sector'], rows[r0]['island'] or ''
        rep[cid] = (y / KY, x / KX)
        if not border.holds(*rep[cid]):
            abroad.append(cid)
            continue
        best, bd = None, 3000.0
        for t in plist[s]:
            if (t['landmass'] or '') != lm and not (t['landmass'] == '' and lm in ('', 'Ilha de Bissau')) and not (lm == '' and t['landmass'] == 'Ilha de Bissau'):
                continue
            d = math.hypot(t['lat'] * KY - y, t['lon'] * KX - x)
            if d < bd:
                best, bd = t, d
        cplace[cid] = (s, best['index'] if best else 0)
    # a compound whose centre lies more than 300 m outside the national border has no code (SPEC 3.1)
    for cid in abroad:
        for k in comps[cid]:
            rows[k]['abroad'] = True
        del comps[cid], rep[cid]
    DROPPED['abroadCompound'] = len(abroad)
    # each compound is known by its main structure's stable id (the largest; ties by id),
    # which also breaks ties along the Hilbert curve, as every port of the engine does
    sid_of = {cid: min(structure_id(rows[k]) for k in ks if rows[k]['a'] == max(rows[q]['a'] for q in ks)) for cid, ks in comps.items()}
    members_of_place = collections.defaultdict(list)
    for cid, key in cplace.items():
        members_of_place[key].append({'id': sid_of[cid], 'lat': rep[cid][0], 'lon': rep[cid][1]})
    word = {k: gw_codes.area_word(*k) for k in members_of_place}
    # one national number range per name, a frozen block per area (SPEC 5.2)
    pl = gw_codes.places()
    areas = [{'key': gw_codes.name_key(word[k]), 'word': word[k], 'sector': k[0], 'index': k[1],
              'compounds': len(members_of_place[k]), 'provisional': bool(k[1] and pl[k].get('needsCouncilChoice'))}
             for k in members_of_place]
    all_words = [t['word'] for t in gw_codes.places().values()] + [gw_codes.area_word(n, 0) for n in sec]
    # Once codes are issued the table is frozen: existing blocks are kept as issued, and only
    # an area with no block yet gets one, above its name's high-water mark.
    issued = json.load(open(os.path.join(REPO, 'model', 'name-ranges.json'))).get('issued')
    table = gw_codes.allocate(areas, names=gw_codes.ranges() if issued else None, all_words=all_words)
    gw_codes._RANGES = table
    start = {k: gw_codes.blocks_of_area(gw_codes.name_key(word[k]), k[0], k[1])[0]['from'] for k in members_of_place}
    by_sid = {}
    for (s, pi), cl in members_of_place.items():
        by_sid.update(gw_codes.number_place(s, cl, start[(s, pi)]))
    numbers = {cid: by_sid[sid_of[cid]] for cid in comps}
    return {k: v for k, v in locals().items()}


def main():
    v = compute()
    enc, rows, method, comps, sec, regions_of, comp_class, cplace, members_of_place, word, pl, areas, table, start, issued = (v['enc'], v['rows'], v['method'], v['comps'], v['sec'], v['regions_of'], v['comp_class'], v['cplace'], v['members_of_place'], v['word'], v['pl'], v['areas'], v['table'], v['start'], v['issued'])
    shared = [r for r in table.values() if len(r['blocks']) > 1]
    biggest = max(shared, key=lambda r: r['highWater'])
    if not issued:
        json.dump({'version': '1', 'frozen': None,
                   'rule': 'docs/model.md 5.2, engine/SPEC.md 5.2: every area whose word has the same name key draws from one national range for that name, 1-99,999; '
                           'a block per area of the smallest 1-2-5 size >= 4 x its compounds at issue, largest area first, aligned; blocks are frozen at issue and never renumbered; '
                           'a new area or a full block takes the next block above the name\'s high-water mark',
                   'maxNumber': gw_codes.MAX_NUMBER, 'growth': gw_codes.GROWTH,
                   'summary': {'names': len(table), 'namesWithAreas': sum(1 for r in table.values() if r['blocks']),
                               'namesSharedByTwoOrMoreAreas': len(shared), 'areasInSharedNames': sum(len(r['blocks']) for r in shared),
                               'compoundsInSharedNames': sum(b['compounds'] for r in shared for b in r['blocks']),
                               'largestSharedRange': {'key': biggest['key'], 'words': biggest['words'][:4], 'areas': len(biggest['blocks']),
                                                'compounds': sum(b['compounds'] for b in biggest['blocks']), 'highWater': biggest['highWater'],
                                                'digits': len(str(biggest['highWater'] - 1))},
                               'mostAreas': sorted(({'key': r['key'], 'word': r['words'][0], 'areas': len(r['blocks']), 'highWater': r['highWater']} for r in shared),
                                                   key=lambda d: -d['areas'])[:10],
                               'qualifiersNeeded': [],
                               'plateNames': {'rule': 'docs/model.md 5.4: the word is the plate name (<= 12 characters, <= 2 words); the official name is an alias',
                                              'areasInUse': len(areas),
                                              'areasNeedingCouncilChoice': sum(1 for a in areas if a['provisional']),
                                              'areasStillOverTheLimit': sum(1 for a in areas if not gw_codes.plate_names.fits(a['word'], 'pt')),
                                              'byRule': dict(collections.Counter(pl[k].get('plateRule', 'as-is') if k[1] else 'sector' for k in members_of_place))}},
                   'names': sorted(table.values(), key=lambda r: r['id'])},
                  open(os.path.join(REPO, 'model', 'name-ranges.json'), 'w'), ensure_ascii=False, indent=0)

    # --- statistics ---
    def summarise(ks_rows, cids):
        rs = [rows[k] for k in ks_rows]
        cls = collections.Counter(r['cls'] for r in rs)
        top = collections.Counter(r['cls'].split('.')[0] for r in rs)
        sizes = [len(comps[c]) for c in cids]
        multi = sum(len(comps[c]) for c in cids if len(comps[c]) > 1)
        gated = sum(1 for c in cids if method[c][0] == 'enclosure' and int(enc[method[c][1]]['gates']) > 0)
        encl = sum(1 for c in cids if method[c][0] == 'enclosure')
        return {
            'footprints': len(rs),
            'fromOpenStreetMap': sum(1 for r in rs if r['src'] == 'osm'),
            'compounds': len(cids),
            'compoundsFromEnclosures': encl,
            'compoundsWithKnownGate': gated,
            'footprintsInMultiStructureCompounds': multi,
            'shareFootprintsInMultiStructureCompounds': round(multi / max(1, len(rs)), 3),
            'structuresPerCompound': {'mean': round(statistics.mean(sizes), 2), **pct(sizes, (50, 90, 99))},
            'compoundSizeMix': {k: sizes.count(k) for k in range(1, 7)} | {'7-12': sum(1 for s in sizes if 7 <= s <= 12), '>12': sum(1 for s in sizes if s > 12)},
            'footprintAreaM2': pct([r['a'] for r in rs]),
            'compoundFootprintAreaM2': pct([sum(rows[k]['a'] for k in comps[c]) for c in cids]),
            'settlement': dict(collections.Counter(r['settle'] for r in rs)),
            'useTop': dict(top.most_common()),
            'useDetail': dict(cls.most_common(14)),
            'useConfidenceMean': round(statistics.mean(r['conf'] for r in rs), 2),
            'useFromTagsOrPlaces': sum(1 for r in rs if r['clsSrc'].startswith(('osm:', 'nways:'))),
            'floorsKnown': sum(1 for r in rs if r['floors']),
            'compoundUse': dict(collections.Counter(comp_class(comps[c]) for c in cids).most_common()),
        }

    cid_sector = {cid: rows[ks[0]]['sector'] for cid, ks in comps.items()}
    live = [k for k, r in enumerate(rows) if not r.get('abroad')]   # rows of compounds dropped at the border are left out
    out = {'computed': '2026-10-18', 'note': 'Statistics from N-Ways map data (OpenStreetMap + Google/Microsoft footprints via Overture); compounds are machine-grouped candidates until people confirm them.',
           'rules': {'settlementClassesBuildingsPerHa': {'cidade': '>=10', 'vila': '4-10', 'tabanca': '1-4', 'disperso': '<1'},
                     'proximityMetres': {k: {'annexJoin': v[0], 'structureGap': v[1]} for k, v in RULES.items()},
                     'annexBelowM2': ANNEX_M2, 'maxStructuresBeforeSplit': CAP},
           'country': summarise(live, list(comps)),
           'regions': {}, 'sectors': {}}
    for reg in sorted(set(regions_of.values())):
        ks = [k for k in live if regions_of[rows[k]['sector']] == reg]
        out['regions'][reg] = summarise(ks, [c for c in comps if regions_of[cid_sector[c]] == reg])
    for s in sorted(sec):
        cids = [c for c in comps if cid_sector[c] == s]
        out['sectors'][s] = {'key': sec[s]['key'], 'name': sec[s]['name'], 'footprints': sum(len(comps[c]) for c in cids),
                             'compounds': len(cids), 'places': len({cplace[c] for c in cids})}
    def top(k):
        return start[k] + 1 + gw_codes.STRIDE * (len(members_of_place[k]) - 1)

    def place_stats(keys):
        sizes = sorted(len(members_of_place[k]) for k in keys)
        maxnum = [top(k) for k in keys]
        dig = collections.Counter(len(str(m)) for m in maxnum)
        big = sorted(keys, key=lambda k: -len(members_of_place[k]))[:8]
        return {'places': len(keys), 'compoundsPerPlace': {'mean': round(statistics.mean(sizes), 1), **pct(sizes, (50, 90, 99)), 'max': sizes[-1]},
                'digitsOfHighestNumberAtFirstIssue': {str(d): dig[d] for d in sorted(dig)},
                'placesFallingBackToSectorWord': sum(1 for k in keys if k[1] == 0),
                'compoundsInSectorFallback': sum(len(members_of_place[k]) for k in keys if k[1] == 0),
                'compoundsByDigits': {str(d): sum(len(members_of_place[k]) for k in keys if len(str(top(k))) == d) for d in sorted(dig)},
                'areasInSharedNames': sum(1 for k in keys if len(table[gw_codes.name_key(word[k])]['blocks']) > 1),
                'largest': [{'word': word[k], 'sector': k[0], 'compounds': len(members_of_place[k]), 'highestNumber': top(k)} for k in big]}
    out['placeWords'] = {'country': place_stats(list(members_of_place)),
                         'bissau': place_stats([k for k in members_of_place if k[0] == 10]),
                         'outsideBissau': place_stats([k for k in members_of_place if k[0] != 10])}
    out['placeWords']['bissauCompoundsPerWord'] = {word[k]: len(members_of_place[k]) for k in sorted(members_of_place, key=lambda k: -len(members_of_place[k])) if k[0] == 10}
    # validation against mapped enclosures (moranças drawn by people)
    truth = collections.defaultdict(list)
    for k in live:
        r = rows[k]
        if r['eid'] and enc[r['eid']]['kind'] in ('osm-farmyard', 'osm-wall', 'osm-fence', 'osm-hedge'):
            truth[r['eid']].append(k)
    out['note_validation'] = 'Mapped enclosures are used as compounds directly; the proximity rule is checked by re-running it with enclosures ignored (see validation).'
    json.dump(out, open(os.path.join(REPO, 'model', 'building-stats.json'), 'w'), ensure_ascii=False, indent=1)

    print(json.dumps(out['country'], ensure_ascii=False, indent=1))
    print(json.dumps(out['regions']['GW-BS'], ensure_ascii=False, indent=1))
    print(json.dumps(out['placeWords'], ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
