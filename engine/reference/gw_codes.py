#!/usr/bin/env python3
"""N-Ways addressing for Guinea-Bissau: reference engine (standard library only).

Implements engine/SPEC.md. Two forms of every compound address, mapping 1:1:

  remembered form   <place word> <number>          "Bandim 275", "Atufa 15"  (also the written form:
                                                    plates, shares, paper; no check digit)
                    structure inside the compound   "Bandim 275.2"
                    as a system may send it         "Bandim 275-8" (with the check digit; accepted)
  machine form      SS-PPP-NNNNN-C                   10-022-00275-8  (forms, partner systems, links, QR)
                    SS = sector number, PPP = place index in the sector,
                    NNNNN = compound number (zero-padded to 5; at most 99,999),
                    C = Damm check digit over the name's national number and the compound number;
                    /p = gate or door

The place word is the area's PLATE NAME: at most 12 characters and 2 words
(plate_names.py), "Bandim", "Issa Seidi". The full official name ("Sinchã Issa Seidi")
is printed small for context and stays an alias that decodes, unless it would point to
two plate names.

Every place word with the same normalised name (name_key) draws from ONE national number
range, split into frozen blocks, one or more per area (model/name-ranges.json). So
"Bandim 275" is the Bissau bairro and "Bandim 2001" the Catió tabanca: the remembered form
alone is unique in the whole country, with no town or sector added.

Spot codes for any point, computed offline:  SS-DDDD-DDDD  (refined: SS-DDDD-DDDD.K); a trailing
Damm check digit, when a code carries one, is verified.

  python3 engine/reference/gw_codes.py                  run the test vectors
  python3 engine/reference/gw_codes.py 11.8591 -15.5793 spot code for a point
  python3 engine/reference/gw_codes.py 10-5421-9699   check and decode a machine or spot code
  python3 engine/reference/gw_codes.py "Bandim 275"    resolve a remembered form
"""
import json, math, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate_names  # noqa: E402
ENGINE = os.path.dirname(HERE)
REPO = os.path.dirname(ENGINE)

# --- Damm check digit ---------------------------------------------------------
# The totally anti-symmetric quasigroup of order 10 (H. M. Damm, 2004). Catches every
# single wrong digit and every swap of two neighbouring digits.
DAMM = [
    [0, 3, 1, 7, 5, 9, 8, 6, 4, 2],
    [7, 0, 9, 2, 1, 5, 4, 8, 6, 3],
    [4, 2, 0, 6, 8, 7, 1, 3, 5, 9],
    [1, 7, 5, 0, 9, 8, 3, 4, 2, 6],
    [6, 1, 2, 3, 0, 4, 5, 9, 7, 8],
    [3, 6, 7, 4, 2, 0, 9, 5, 8, 1],
    [5, 8, 6, 9, 7, 2, 0, 1, 3, 4],
    [8, 9, 4, 5, 3, 6, 2, 0, 1, 7],
    [9, 4, 3, 8, 6, 1, 7, 2, 0, 5],
    [2, 5, 8, 1, 4, 3, 6, 7, 9, 0],
]


def damm(digits):
    i = 0
    for d in digits:
        i = DAMM[i][int(d)]
    return i


# --- Sectors and places ---------------------------------------------------------
_SECTORS = None
_PLACES = None


def _load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def sectors():
    """number -> sector record (grid frame + outline), loaded once."""
    global _SECTORS
    if _SECTORS is None:
        meta = _load(os.path.join(REPO, 'model', 'sectors.json'))
        outl = _load(os.path.join(ENGINE, 'data', 'sectors.geojson'))
        geo = {f['properties']['number']: f['geometry']['coordinates'] for f in outl['features']}
        _SECTORS = {}
        for s in meta['sectors']:
            polys = geo[s['number']]
            xs = [p[0] for poly in polys for p in poly[0]]
            ys = [p[1] for poly in polys for p in poly[0]]
            _SECTORS[s['number']] = dict(s, polys=polys, box=(min(xs), min(ys), max(xs), max(ys)))
    return _SECTORS


def places():
    """(sector, index) -> place record from model/places.json, loaded once."""
    global _PLACES
    if _PLACES is None:
        p = os.path.join(REPO, 'model', 'places.json')
        _PLACES = {(t['sector'], t['index']): t for t in _load(p)['places']} if os.path.exists(p) else {}
    return _PLACES


def plain(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c)).lower().strip()


# --- Name keys: what counts as "the same name" (SPEC 5.1.1) ------------------------
ROMAN = {'1': 'i', '2': 'ii', '3': 'iii', '4': 'iv', '5': 'v', '6': 'vi', '7': 'vii', '8': 'viii', '9': 'ix', '10': 'x'}
_ROMANS = set(ROMAN.values())
_SMALL = {'de', 'da', 'do', 'dos', 'das', 'e', 'o', 'a', 'os', 'as'}
_ABBREV = {'sto': 'santo', 'sta': 'santa', 'sra': 'senhora'}  # plate abbreviations typed or said in full
_PREFIX = re.compile(r'^(bairro|tabanca|tabanka|aldeia|povoacao|moranca|moransa|moranza)\s+((de|da|do|dos|das)\s+)?')
_FOLDS = (('tch', 'x'), ('ch', 'x'), ('sh', 'x'), ('ck', 'k'), ('qu', 'k'), ('gu', 'g'), ('ph', 'f'), ('nh', 'n'), ('lh', 'l'))


def _fold(t):
    """Portuguese/Kriol/French spellings of one sound to one letter: Sintchã/Sinchã/Sincha,
    Quinhamel/Kinhamel, Contuboel/Kontuboel, Plack/Plaque, Bissorã/Bissora, Dulo/Dulu."""
    t = re.sub(r'que$', 'k', t)  # Plaque = Plack
    for a, b in _FOLDS:
        t = t.replace(a, b)
    t = re.sub(r'c(?=[ei])', 's', t).replace('c', 'k')
    t = t.replace('z', 's').replace('y', 'i').replace('w', 'u').replace('h', '')
    t = t.replace('e', 'i').replace('o', 'u')  # Kriol vowel spelling: Pitche/Pitchi, Bissoro/Bissoru
    return re.sub(r'(.)\1+', r'\1', t)


def name_key(name):
    """The normalised name: case, accents, hyphens and spaces, articles and de/da/do,
    'Bairro de'/'Tabanca de'/'Morança' prefixes and spelling variants are folded. A trailing
    numeral that is part of the name people say (Plaque I, Plaque 2) is kept, as a Roman
    numeral, so "Plaque II" is a name of its own and "Plaque 2" is the same name."""
    s = name.lower().replace('ç', 's')
    s = ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
    s = _PREFIX.sub('', re.sub(r'[^a-z0-9]+', ' ', s).strip())
    toks = s.split()
    # 'Sto António' = 'Santo António', 'S. Miguel' = 'São Miguel', 'N. Sra' = 'Nossa Senhora'
    if len(toks) > 1:
        toks = ['sao' if t == 's' and i == 0 else 'nossa' if t == 'n' and toks[i + 1:i + 2] in (['sra'], ['senhora']) else _ABBREV.get(t, t)
                for i, t in enumerate(toks)]
    num = ''
    if len(toks) > 1 and (toks[-1] in _ROMANS or toks[-1] in ROMAN):
        num, toks = ROMAN.get(toks[-1], toks[-1]), toks[:-1]
    if len(toks) > 1:
        toks = [t for t in toks if t not in _SMALL] or toks
    return ''.join(_fold(t) for t in toks) + ('#' + num if num else '')


def _in_ring(x, y, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def sector_of(lat, lon):
    """The sector number a point falls in (the frozen outlines), or None at sea / abroad."""
    for num, s in sectors().items():
        x0, y0, x1, y1 = s['box']
        if not (x0 <= lon <= x1 and y0 <= lat <= y1):
            continue
        for poly in s['polys']:
            if _in_ring(lon, lat, poly[0]) and not any(_in_ring(lon, lat, h) for h in poly[1:]):
                return num
    return None


_ISLANDS = None


def _islands():
    """Named islands as (name, box, polygon) from engine/data/islands.geojson, loaded once.
    Each part of a multipolygon is kept on its own, with the box of its outer ring."""
    global _ISLANDS
    if _ISLANDS is None:
        fc = _load(os.path.join(ENGINE, 'data', 'islands.geojson'))
        _ISLANDS = []
        for f in fc['features']:
            g = f['geometry']
            polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
            for poly in polys:
                xs = [p[0] for p in poly[0]]
                ys = [p[1] for p in poly[0]]
                _ISLANDS.append((f['properties']['name'], (min(xs), min(ys), max(xs), max(ys)), poly))
    return _ISLANDS


def island_of(lat, lon):
    """The named island a point is on, or '' on the mainland or an unnamed islet. Where
    outlines nest, the island with the smallest bounding box wins."""
    best, size = '', float('inf')
    for name, (x0, y0, x1, y1), poly in _islands():
        if not (x0 <= lon <= x1 and y0 <= lat <= y1):
            continue
        if _in_ring(lon, lat, poly[0]) and not any(_in_ring(lon, lat, h) for h in poly[1:]):
            a = (x1 - x0) * (y1 - y0)
            if a < size:
                best, size = name, a
    return best


def same_land(a, b):
    """Two land masses count as one for the place rule: Ilha de Bissau is joined to the
    mainland by road, so it counts as the mainland."""
    def norm(x):
        return '' if (x or '') == 'Ilha de Bissau' else (x or '')
    return norm(a) == norm(b)


# --- The national border (SPEC 3.1) ---------------------------------------------
BORDER_FILE = os.path.join(ENGINE, 'data', 'border.geojson')
BORDER_M = 300.0     # how far outside the national border an entrance may lie


class Border:
    """The national border (engine/data/border.geojson): OpenStreetMap's admin_level=2
    boundary of Guinea-Bissau, simplified. A building more than BORDER_M outside it is in
    a neighbouring country and never has a code, whatever the sector outlines say.

    Distances are in metres on the plane of the point's latitude (M_LAT north, M_LON_EQ
    x cos(latitude) east), as everywhere in this engine. The file records the largest
    distance between the simplified line and the true one (maxDeviationM) and the limit to
    apply (limitM): BORDER_M less that deviation rounded up, less 1 m for the plane, so a
    point it accepts is never more than BORDER_M outside the true border."""

    CELL = 0.01   # degrees

    def __init__(self, path=BORDER_FILE, limit_m=None):
        gj = _load(path)
        props = gj.get('properties') or {}
        geom = gj['geometry'] if gj.get('type') == 'Feature' else gj
        polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
        if limit_m is None:
            limit_m = props.get('limitM', BORDER_M - math.ceil(float(props.get('maxDeviationM', 0.0))) - 1)
        self.limit = float(limit_m)
        self.segs = []
        for poly in polys:
            for ring in poly:
                pts = [(float(x), float(y)) for x, y in ring]
                if pts and pts[0] == pts[-1]:
                    pts = pts[:-1]
                for i in range(len(pts)):
                    self.segs.append((pts[i - 1], pts[i]))
        c = self.CELL
        dy = self.limit / M_LAT
        self.bands = {}     # latitude band -> segments crossing it (inside test)
        self.cells = {}     # grid cell -> segments within the limit of it (distance)
        for k, ((ax, ay), (bx, by)) in enumerate(self.segs):
            for b in range(int(math.floor(min(ay, by) / c)), int(math.floor(max(ay, by) / c)) + 1):
                self.bands.setdefault(b, []).append(k)
            dx = self.limit / (M_LON_EQ * math.cos(math.radians(max(abs(ay), abs(by)) + 1)))
            for gx in range(int(math.floor((min(ax, bx) - dx) / c)), int(math.floor((max(ax, bx) + dx) / c)) + 1):
                for gy in range(int(math.floor((min(ay, by) - dy) / c)), int(math.floor((max(ay, by) + dy) / c)) + 1):
                    self.cells.setdefault((gx, gy), []).append(k)

    def inside(self, lat, lon):
        """True for a point inside the border itself (even-odd over every ring)."""
        ins = False
        for k in self.bands.get(int(math.floor(lat / self.CELL)), ()):
            (ax, ay), (bx, by) = self.segs[k]
            if (ay > lat) != (by > lat) and lon < (bx - ax) * (lat - ay) / (by - ay) + ax:
                ins = not ins
        return ins

    def outside_m(self, lat, lon):
        """0 inside the border; else the metres to it, or infinity beyond the limit."""
        if self.inside(lat, lon):
            return 0.0
        kx = M_LON_EQ * math.cos(math.radians(lat))
        best = math.inf
        for k in self.cells.get((int(math.floor(lon / self.CELL)), int(math.floor(lat / self.CELL))), ()):
            (ax, ay), (bx, by) = self.segs[k]
            ax, ay, bx, by = (ax - lon) * kx, (ay - lat) * M_LAT, (bx - lon) * kx, (by - lat) * M_LAT
            dx, dy = bx - ax, by - ay
            L = dx * dx + dy * dy
            t = 0.0 if L == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / L))
            best = min(best, math.hypot(ax + t * dx, ay + t * dy))
        return best if best <= self.limit else math.inf

    def holds(self, lat, lon):
        """True for a point inside the border or within the limit of it."""
        return self.outside_m(lat, lon) <= self.limit


_BORDER = None


def border():
    """The national border of engine/data/border.geojson, loaded once."""
    global _BORDER
    if _BORDER is None:
        _BORDER = Border()
    return _BORDER


PLACE_MAX_M = 3000.0


def place_for(lat, lon, sector=None, candidates=None, max_m=PLACE_MAX_M):
    """The place word a new compound takes (SPEC 5.1): the nearest place of the same sector
    and the same land mass strictly within max_m metres, the lower index on a tie; else the
    sector's own word (index 0). candidates: the area records to choose from (dicts with
    sector, index, lat, lon, landmass); by default the places of model/places.json."""
    sector = sector if sector is not None else sector_of(lat, lon)
    land = island_of(lat, lon)
    pool = candidates if candidates is not None else places().values()
    best, bd = None, max_m
    for t in pool:
        if t['sector'] != sector or not t['index'] or t.get('lat') is None or t.get('lon') is None:
            continue
        if not same_land(t.get('landmass'), land):
            continue
        d = math.hypot((t['lat'] - lat) * M_LAT, (t['lon'] - lon) * M_LON_EQ * math.cos(math.radians(lat)))
        if d < bd or (d == bd and best is not None and t['index'] < best['index']):
            best, bd = t, d
    if best is None:
        return {'sector': sector, 'index': 0, 'word': sectors()[sector]['name'].split(' (')[0], 'kind': 'sector'}
    return best


def area_word(sector, index):
    """The word of an area: its place word, or the sector's name for index 000."""
    if index == 0:
        return sectors()[sector]['name'].split(' (')[0]
    return places()[(sector, index)]['word']


LANG = 'pt'


def check_plate(word):
    """A plate name is at most 12 characters and 2 words, with no digits (SPEC 5.1.2)."""
    if not plate_names.fits(word, LANG):
        raise ValueError(f'plate name {word!r} is over the limit ({plate_names.plate_length(word)} characters, '
                         f'{plate_names.word_count(word, LANG)} words; at most {plate_names.MAX_CHARS} and {plate_names.MAX_WORDS})')
    return word


_ALIASES = None


def alias_keys():
    """name key of an official name or other alias -> the one plate-name key it decodes to.
    model/places.json keeps only the aliases that point to one plate name (tools/gw_plates.py)."""
    global _ALIASES
    if _ALIASES is None:
        own = {name_key(t['word']) for t in places().values()}
        claims = {}
        for t in places().values():
            for a in [t.get('officialName') or t['word']] + t.get('aliases', []):
                k = name_key(a)
                if k not in own:
                    claims.setdefault(k, set()).add(name_key(t['word']))
        _ALIASES = {k: next(iter(v)) for k, v in claims.items() if len(v) == 1}
    return _ALIASES


def without_cedilla(words):
    """Lookup keys for names typed without their cedilla. The key reads ç as s and a bare c
    before a, o or u as k, so 'Praca' (ç dropped, as on most phone keyboards) would miss
    'Praça'. words: (word, key) pairs; returns {key of the word with ç written c: key},
    keeping only spellings that are not a name of their own and point to one key."""
    claims = {}
    for w, k in words:
        if 'ç' in w.lower():
            claims.setdefault(name_key(w.lower().replace('ç', 'c')), set()).add(k)
    own = {k for _, k in words}
    return {u: next(iter(v)) for u, v in claims.items() if len(v) == 1 and u not in own}


_UNMARKED = None


def plate_key(word):
    """The name key of the plate name someone typed or said, either the plate name itself
    or an official name / alias that points to one plate name, with or without its cedilla."""
    global _UNMARKED
    k = name_key(word)
    if k in ranges() and ranges()[k]['blocks']:
        return k
    if k in alias_keys():
        return alias_keys()[k]
    if _UNMARKED is None:
        pairs = []
        for t in places().values():
            pk = name_key(t['word'])
            pairs += [(t['word'], pk)] + [(a, alias_keys().get(name_key(a), pk))
                                          for a in [t.get('officialName') or t['word']] + t.get('aliases', [])]
        _UNMARKED = without_cedilla(pairs)
    return _UNMARKED.get(k, k)


def resolve_word(word):
    """Area records (sector, index, word) whose word or alias has the same name key as what
    someone typed or said; all of them share one national number range."""
    k = plate_key(word)
    out = [t for t in places().values() if name_key(t['word']) == k]
    out += [{'sector': n, 'index': 0, 'word': area_word(n, 0), 'kind': 'sector'}
            for n in sectors() if name_key(area_word(n, 0)) == k]
    return out


# --- National number ranges per name (SPEC 5.2) ----------------------------------------
MAX_NUMBER = 99999      # numbers stay at most 5 digits
NICE = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000]
GROWTH = 4              # a block holds 4 x the compounds at issue: stride 2, then as many again
_RANGES = None


def block_size(compounds):
    """Smallest 1-2-5 size holding GROWTH x the area's compounds (at least 10)."""
    need = max(1, GROWTH * compounds)
    for n in NICE:
        if n >= need:
            return n
    raise OverflowError(f'{compounds} compounds do not fit in {MAX_NUMBER} numbers: split the area under an established qualifier')


def _aligned(high_water, size):
    step = 10 ** (len(str(size)) - 1)
    return -(-high_water // step) * step


def allocate(areas, names=None, all_words=()):
    """Blocks for every area, frozen once given.
    areas: [{'key','word','sector','index','compounds'}] (compounds at first issue, > 0).
    names: the frozen table so far ({key: record}); existing blocks are never touched.
    all_words: every place word (and sector word); each new name gets its national number
    (id) in alphabetical order of its key, so the ids exist before any block does.
    A word must be a plate name that fits (check_plate); an area flagged for the council
    ('provisional': True) may keep an over-long name until the council chooses; its codes
    are issued with that provisional name.
    A new area of an existing name gets a block above the name's high-water mark; within a
    call, a name's new areas are placed largest first (most homes keep the shortest numbers),
    areas still waiting for the council's plate-name choice after the others.
    Returns {key: {'key','id','words','blocks':[{'sector','index','from','to'}],'highWater'}}."""
    names = {k: dict(v, blocks=[dict(b) for b in v['blocks']], words=list(v['words'])) for k, v in (names or {}).items()}
    nxt = max((v['id'] for v in names.values()), default=0) + 1
    for key in sorted({name_key(w) for w in all_words} - set(names)):
        names[key] = {'key': key, 'id': nxt, 'words': [], 'blocks': [], 'highWater': 0}
        nxt += 1
    for w in all_words:
        if w not in names[name_key(w)]['words']:
            names[name_key(w)]['words'].append(w)
    by = {}
    for a in areas:
        if not a.get('provisional'):
            check_plate(a['word'])
        by.setdefault(a['key'], []).append(a)
    for key in sorted(by):
        rec = names.get(key)
        if rec is None:
            rec = names[key] = {'key': key, 'id': nxt, 'words': [], 'blocks': [], 'highWater': 0}
            nxt += 1
        have = {(b['sector'], b['index']) for b in rec['blocks']}
        # largest first; an area whose plate name waits for the council (provisional) comes
        # after the confirmed areas of the name, so it never takes a town's short numbers
        for a in sorted(by[key], key=lambda a: (bool(a.get('provisional')), -a['compounds'], a['sector'], a['index'])):
            if a['word'] not in rec['words']:
                rec['words'].append(a['word'])
            if (a['sector'], a['index']) in have:
                continue
            size = block_size(a['compounds'])
            start = _aligned(rec['highWater'], size)
            if start + size - 1 > MAX_NUMBER:
                raise OverflowError(f'{key}: blocks pass {MAX_NUMBER}; give this name an established qualifier')
            rec['blocks'].append({'sector': a['sector'], 'index': a['index'], 'from': start, 'to': start + size - 1,
                                  'compounds': a['compounds']})
            rec['highWater'] = start + size
    return names


def continuation(names, key, sector, index, compounds):
    """An area whose block is full gets a further block from its name's spare space
    (same size rule); its earlier numbers never change."""
    rec = names[key]
    size = block_size(compounds)
    start = _aligned(rec['highWater'], size)
    if start + size - 1 > MAX_NUMBER:
        raise OverflowError(f'{key}: no spare space left below {MAX_NUMBER + 1}')
    rec['blocks'].append({'sector': sector, 'index': index, 'from': start, 'to': start + size - 1, 'compounds': compounds})
    rec['highWater'] = start + size
    return rec['blocks'][-1]


def ranges():
    """name key -> frozen name record from model/name-ranges.json, loaded once."""
    global _RANGES
    if _RANGES is None:
        p = os.path.join(REPO, 'model', 'name-ranges.json')
        _RANGES = {r['key']: r for r in _load(p)['names']} if os.path.exists(p) else {}
    return _RANGES


def name_id(key, table=None):
    rec = (table if table is not None else ranges()).get(key)
    if rec is None:
        raise ValueError(f'no national number range for the name {key!r}')
    return rec['id']


def block_of(key, number, table=None):
    """The one area (sector, index) that owns this number of this name, or None (spare)."""
    rec = (table if table is not None else ranges()).get(key)
    for b in (rec or {}).get('blocks', ()):
        if b['from'] <= number <= b['to']:
            return b['sector'], b['index']
    return None


def blocks_of_area(key, sector, index, table=None):
    rec = (table if table is not None else ranges()).get(key) or {'blocks': []}
    return [b for b in rec['blocks'] if (b['sector'], b['index']) == (sector, index)]


# --- Spot grid ----------------------------------------------------------------
M_LAT = 110574.0
M_LON_EQ = 111320.0
SIDE = 10000  # cells per side: 4 digits per axis


def _frame(num):
    g = sectors()[num]['grid']
    return g['lon0'], g['lat0'], math.cos(math.radians(g['phi0'])), g['cellMetres']


def _interleave(i, j):
    a, b = f'{i:04d}', f'{j:04d}'
    return ''.join(a[k] + b[k] for k in range(4))


def encode_spot(lat, lon, refine=False, sector=None):
    num = sector if sector is not None else sector_of(lat, lon)
    if num is None:
        raise ValueError('point is not inside a Guinea-Bissau sector')
    lon0, lat0, k, s = _frame(num)
    x = (lon - lon0) * k * M_LON_EQ / s
    y = (lat - lat0) * M_LAT / s
    i, j = int(math.floor(x)), int(math.floor(y))
    if not (0 <= i < SIDE and 0 <= j < SIDE):
        raise ValueError('point is outside the sector grid')
    d = _interleave(i, j)
    body = f'{num:02d}{d}'
    text = f'{num:02d}-{d[:4]}-{d[4:]}'
    if refine:
        fx, fy = x - i, y - j
        col, row = min(2, int(fx * 3)), 2 - min(2, int(fy * 3))  # phone keypad: 1 2 3 is the north row
        kd = str(3 * row + col + 1)
        body += kd
        text += '.' + kd
    # A spot code is shared as a link, so it carries no check digit; parse() still verifies
    # one when a code is written with it.
    return text


SPOT = re.compile(r'^(\d{2})-(\d{4})-(\d{4})(?:\.([1-9]))?(?:-(\d))?$')
ADDR = re.compile(r'^(\d{2})-(\d{3})-(\d{5})(?:\.(\d{1,2}))?-(\d)(?:/(\d{1,2}))?$')
SPOKEN = re.compile(r'^(.+?)\s+(\d{1,5})(?:\.(\d{1,2}))?(?:\s*-\s*(\d))?$')


def parse(code):
    """Machine form -> parts; raises ValueError on a bad form or a failed check digit."""
    c = code.strip().replace(' ', '')
    m = SPOT.match(c)
    if m:
        ss, a, b, k, chk = m.groups()
        if int(ss) not in sectors():
            raise ValueError(f'unknown sector {ss}')
        if chk is not None and damm(ss + a + b + (k or '')) != int(chk):
            raise ValueError(f'check digit fails: {code!r}')
        return {'kind': 'spot', 'sector': int(ss), 'digits': a + b, 'refine': int(k) if k else None}
    m = ADDR.match(c)
    if m:
        ss, pp, n, sub, chk, door = m.groups()
        s_, p_, n_ = int(ss), int(pp), int(n)
        if s_ not in sectors():
            raise ValueError(f'unknown sector {ss}')
        if p_ and (s_, p_) not in places():
            raise ValueError(f'no place {ss}-{pp}')
        key = name_key(area_word(s_, p_))
        if check_digit(name_id(key), n_, sub) != int(chk):
            raise ValueError(f'check digit fails: {code!r}')
        if block_of(key, n_) != (s_, p_):
            raise ValueError(f'number {n_} of {area_word(s_, p_)} does not belong to area {ss}-{pp}: {code!r}')
        if sub is not None and sub.startswith('0'):
            raise ValueError('structure numbers start at 1')
        return {'kind': 'structure' if sub else 'compound', 'sector': s_, 'place': p_, 'number': n_,
                'structure': int(sub) if sub else None, 'door': int(door) if door else None,
                'word': area_word(s_, p_), 'nameId': name_id(key)}
    raise ValueError(f'not a GW machine code: {code!r}')


def decode_spot(code):
    p = parse(code)
    if p['kind'] != 'spot':
        raise ValueError('a compound code is looked up in the registry, not computed')
    d = p['digits']
    i, j = int(d[0::2]), int(d[1::2])
    lon0, lat0, k, s = _frame(p['sector'])
    fx = fy = 0.5
    size = s
    if p['refine']:
        r, c = divmod(p['refine'] - 1, 3)
        fx, fy = (c + 0.5) / 3, (2 - r + 0.5) / 3
        size = s / 3
    lat = lat0 + (j + fy) * s / M_LAT
    lon = lon0 + (i + fx) * s / (k * M_LON_EQ)
    return {'sector': p['sector'], 'lat': round(lat, 7), 'lon': round(lon, 7), 'cellMetres': round(size, 2)}


def check_digit(nid, number, structure=None):
    """Damm over the name's national number (5 digits) and the compound number (5 digits),
    then the structure. The area is bound through the frozen block table: a number of a name
    belongs to exactly one area, so a single wrong digit or a swap anywhere in the number is
    always caught, whether it would have stayed in the area or jumped to a same-named one."""
    return damm(f'{nid:05d}{number:05d}' + (str(structure) if structure else ''))


def machine(sector, place, number, structure=None, door=None, table=None):
    key = name_key(area_word(sector, place))
    if block_of(key, number, table) != (sector, place):
        raise ValueError(f'{number} is not in a block of area {sector:02d}-{place:03d}')
    c = check_digit(name_id(key, table), number, structure)
    return f'{sector:02d}-{place:03d}-{number:05d}' + (f'.{structure}' if structure else '') + f'-{c}' + (f'/{door}' if door else '')


def remembered(word, number, structure=None, check=None):
    return f'{word} {number}' + (f'.{structure}' if structure else '') + (f'-{check}' if check is not None else '')


def checked(sector, place, number, structure=None, table=None):
    """The remembered form with its check digit, 'Bandim 275-8', as a system may exchange it.
    Plates and written forms show the name and number only."""
    key = name_key(area_word(sector, place))
    return remembered(area_word(sector, place), number, structure, check_digit(name_id(key, table), number, structure))


def from_remembered(text):
    """'Bandim 275' or 'Bandim 275-8' -> the one area and machine form, nationally.
    No town, sector or position is needed: the name's blocks say which area owns the number.
    With the check digit given, any single wrong digit or swap is refused."""
    m = SPOKEN.match(text.strip())
    if not m:
        raise ValueError('say it as: place word, then the number')
    word, n, sub, chk = m.groups()
    n = int(n)
    key = plate_key(word)
    if key not in ranges():
        raise ValueError(f'no place word {word!r}')
    if chk is not None and check_digit(name_id(key), n, sub) != int(chk):
        raise ValueError(f'check digit fails: {text!r}')
    area = block_of(key, n)
    if area is None:
        raise ValueError(f'{word} {n} has not been issued (spare numbers of this name)')
    s_, p_ = area
    return {'word': area_word(s_, p_), 'sector': s_, 'sectorName': sectors()[s_]['name'], 'place': p_, 'number': n,
            'structure': int(sub) if sub else None, 'machine': machine(s_, p_, n, int(sub) if sub else None)}


# --- Registry ordering --------------------------------------------------------
def hilbert(i, j, order=14):
    """Distance of cell (i, j) along a Hilbert curve over a 2^order square."""
    n = 1 << order
    d, s = 0, n >> 1
    x, y = i, j
    while s > 0:
        rx = 1 if x & s else 0
        ry = 1 if y & s else 0
        d += s * s * ((3 * rx) ^ ry)
        if ry == 0:
            if rx == 1:
                x, y = n - 1 - x, n - 1 - y
            x, y = y, x
        s >>= 1
    return d


def grid_cell(sector, lat, lon):
    lon0, lat0, k, s = _frame(sector)
    return (min(SIDE - 1, max(0, int((lon - lon0) * k * M_LON_EQ / s))),
            min(SIDE - 1, max(0, int((lat - lat0) * M_LAT / s))))


STRIDE = 2


def number_place(sector, compounds, start=0):
    """First issue in one area: compounds (dicts with id, lat, lon = gate or representative
    point) in Hilbert order get start+1, start+3, start+5, ... inside the area's block (start
    = the block's 'from'); the even numbers stay free for compounds built in between, and the
    rest of the block is free for the area's growth."""
    keyed = sorted(((hilbert(*grid_cell(sector, c['lat'], c['lon'])), c['id']) for c in compounds))
    return {cid: start + 1 + STRIDE * k for k, (h, cid) in enumerate(keyed)}


def reserve_number(sector, lat, lon, issued, block=(0, MAX_NUMBER)):
    """'Add my home': the provisional number for a new compound whose gate is at lat, lon,
    in an area whose compounds are issued = [(number, lat, lon), ...] inside block = (from, to).
    Between its two Hilbert neighbours, the free number nearest its proportional position;
    if they are consecutive (no gap left) or it falls after the last, the next number after
    the highest issued. Returns (number, 'gap' | 'end'), or (None, 'full') when the block has
    no number left: the registry then gives the area a continuation block (continuation())."""
    lo, hi = block
    taken = {n for n, _, _ in issued}
    h = hilbert(*grid_cell(sector, lat, lon))
    keyed = sorted((hilbert(*grid_cell(sector, a, b)), n) for n, a, b in issued)
    before = [(hh, n) for hh, n in keyed if hh <= h]
    after = [(hh, n) for hh, n in keyed if hh > h]
    if after:
        ha, na = before[-1] if before else (0, lo)
        hb, nb = after[0]
        if nb - na > 1:
            want = na + max(1, min(nb - na - 1, round((h - ha) / max(1, hb - ha) * (nb - na))))
            for step in range(nb - na):
                for cand in (want - step, want + step):
                    if na < cand < nb and cand not in taken and cand >= 1:
                        return cand, 'gap'
    nxt = max(taken) + 1 if taken else max(1, lo + 1)
    return (nxt, 'end') if nxt <= hi else (None, 'full')


def insert(sector, lat, lon, issued, blocks, high_water):
    """'Add my home' across all of an area's blocks (SPEC 7.2). issued = [(number, lat, lon),
    ...] for every number the area holds, retired ones included (a number is never reused);
    blocks = [(from, to), ...] in the order they were given; high_water = the end of the
    name's last block plus one, over every area of the name.
    Each block is tried in turn with reserve_number(). When all are full, the area takes a
    continuation block sized for its compounds plus this one, above the name's high-water
    mark, and the new compound gets its first number.
    Returns (number, new block or None), or (None, None) when the name has no room left
    below 100,000 (the area then needs an established qualifier)."""
    for lo, hi in blocks:
        inside = [c for c in issued if lo <= c[0] <= hi]
        n, _ = reserve_number(sector, lat, lon, inside, block=(lo, hi))
        if n is not None:
            return n, None
    try:
        size = block_size(len(issued) + 1)
    except OverflowError:
        return None, None
    start = _aligned(high_water, size)
    if start + size - 1 > MAX_NUMBER:
        return None, None
    return start + 1, (start, start + size - 1)


# --- Numbers read aloud (Portuguese) ----------------------------------------------
_PT_ONES = ['zero', 'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove', 'dez', 'onze', 'doze',
            'treze', 'catorze', 'quinze', 'dezasseis', 'dezassete', 'dezoito', 'dezanove']
_PT_TENS = ['', '', 'vinte', 'trinta', 'quarenta', 'cinquenta', 'sessenta', 'setenta', 'oitenta', 'noventa']
_PT_HUNDREDS = ['', 'cento', 'duzentos', 'trezentos', 'quatrocentos', 'quinhentos', 'seiscentos', 'setecentos',
                'oitocentos', 'novecentos']


def _pt999(n):
    if n < 20:
        return _PT_ONES[n]
    if n < 100:
        return _PT_TENS[n // 10] + ('' if n % 10 == 0 else ' e ' + _PT_ONES[n % 10])
    if n == 100:
        return 'cem'
    if n % 100 == 0:
        return _PT_HUNDREDS[n // 100]
    return _PT_HUNDREDS[n // 100] + ' e ' + _pt999(n % 100)


def pt_number(n):
    """A number read aloud in Portuguese, as a door number is (1-99,999): 275 'duzentos e
    setenta e cinco', 1275 'mil duzentos e setenta e cinco', 2100 'dois mil e cem'."""
    if n < 1000:
        return _pt999(n)
    th, rest = divmod(n, 1000)
    head = 'mil' if th == 1 else _pt999(th) + ' mil'
    if rest == 0:
        return head
    if rest < 100 or rest % 100 == 0:
        return head + ' e ' + _pt999(rest)
    return head + ' ' + _pt999(rest)


def spoken(word, number):
    """The code as it is read aloud: 'Bandim, quinhentos e trinta e sete'."""
    return f'{word}, {pt_number(number)}'


# --- Test vectors ---------------------------------------------------------------
EXAMPLES = [
    ('Bissau Velho, Praça / Fortaleza area', 11.8591, -15.5793),
    ('Mercado de Bandim, Bissau', 11.8521, -15.5951),
    ('Bairro Militar, Bissau', 11.8738, -15.6156),
    ('Bafatá, Praça', 12.1645, -14.6643),
    ('Gabú town', 12.2830, -14.2230),
    ('Canchungo town', 12.0670, -16.0330),
    ('Bubaque town (Ilha de Bubaque)', 11.2990, -15.8277),
    ('Bolama town (Ilha de Bolama)', 11.5783, -15.4735),
    ('Catió town', 11.2830, -15.2500),
    ('Madina do Boé', 11.7470, -14.2160),
]


def selftest():
    out = []
    for name, lat, lon in EXAMPLES:
        num = sector_of(lat, lon)
        code = encode_spot(lat, lon)
        fine = encode_spot(lat, lon, refine=True)
        back = decode_spot(code)
        fb = decode_spot(fine)
        assert back['sector'] == num
        assert abs(back['lat'] - lat) * M_LAT <= sectors()[num]['grid']['cellMetres']
        assert encode_spot(back['lat'], back['lon'], sector=num) == code
        assert encode_spot(fb['lat'], fb['lon'], refine=True, sector=num) == fine
        pl = place_for(lat, lon, num) if places() else {'word': '?', 'index': 0}
        out.append({'place': name, 'lat': lat, 'lon': lon, 'sector': num, 'key': sectors()[num]['key'],
                    'placeWord': pl['word'], 'placeIndex': pl['index'],
                    'spot': code, 'refined': fine, 'cellMetres': back['cellMetres'], 'decoded': [back['lat'], back['lon']]})
    # a spot code written with a check digit still decodes, and with it every single-digit
    # error and every adjacent swap is caught
    total = 0
    sample = out[0]['spot'] + '-' + str(damm(out[0]['spot'].replace('-', '')))
    assert decode_spot(sample) == decode_spot(out[0]['spot'])
    for pos in [i for i, ch in enumerate(sample) if ch.isdigit()]:
        for d in '0123456789':
            if d != sample[pos]:
                total += 1
                _refused(sample[:pos] + d + sample[pos + 1:])
    _swaps_refused(sample)
    # ... and on a machine form: in the number and check digit always; in SS-PPP always when
    # it would land in another area of the same name (or nowhere)
    addr = machine(10, 22, 275)
    cross_name = 0
    for pos in [i for i, ch in enumerate(addr) if ch.isdigit()]:
        for d in '0123456789':
            if d == addr[pos]:
                continue
            bad = addr[:pos] + d + addr[pos + 1:]
            total += 1
            try:
                p = parse(bad)
            except ValueError:
                continue
            assert pos < 6 and name_key(p['word']) != name_key('Bandim'), 'not caught: ' + bad
            cross_name += 1  # lands on a differently named place: its other word is shown
    _swaps_refused(addr, allow_other_name=True)
    forms = [addr, machine(10, 22, 275, structure=2), machine(10, 22, 275, door=1), machine(75, 39, 15)]
    for c in forms:
        parse(c)
    same_name = same_name_vectors() + plate_vectors()
    alloc = allocation_vectors()
    # first issue and 'Add my home' in a toy area of 12 compounds along a lane in Apurnia (Nhacra, 75)
    toy = [{'id': f'c{k}', 'lat': 12.0400 + 0.00025 * k, 'lon': -15.5220 + 0.00004 * (k % 3)} for k in range(12)]
    nums = number_place(75, toy)
    issued = [(nums[c['id']], c['lat'], c['lon']) for c in toy]
    new = (12.0400 + 0.00025 * 4.5, -15.5220 + 0.00004)  # a new gate between c4 and c5
    gap = reserve_number(75, *new, issued, block=(0, 49))
    last = max(toy, key=lambda c: nums[c['id']])  # the compound furthest along the curve
    end = reserve_number(75, last['lat'], last['lon'], issued, block=(0, 49))
    full = [(n, 12.04 + 0.00025 * n, -15.5220) for n in range(1, 13)]  # consecutive numbers: no gap left
    nogap = reserve_number(75, 12.04 + 0.00025 * 5.5, -15.5220, full, block=(0, 49))
    assert gap == (12, 'gap') and end == (24, 'end') and nogap == (13, 'end'), (gap, end, nogap)
    # the same toy area as the second block of its name (2000-2199): numbers 2001, 2003 ...
    nums2 = number_place(75, toy, start=2000)
    issued2 = [(nums2[c['id']], c['lat'], c['lon']) for c in toy]
    gap2 = reserve_number(75, *new, issued2, block=(2000, 2199))
    end2 = reserve_number(75, last['lat'], last['lon'], issued2, block=(2000, 2199))
    blockfull = reserve_number(75, last['lat'], last['lon'], issued, block=(0, 23))
    assert sorted(nums2.values())[0] == 2001 and gap2 == (2012, 'gap') and end2 == (2024, 'end') and blockfull == (None, 'full'), (gap2, end2, blockfull)
    addhome = {'issued': sorted(nums.values()), 'newGateBetween': [nums['c4'], nums['c5']], 'provisional': gap,
               'newGateAfterLast': end, 'whenNoGap': nogap, 'secondBlock': {'issuedFrom': 2001, 'provisional': gap2, 'end': end2},
               'whenBlockFull': blockfull}
    return out, forms, addhome, total, cross_name, same_name, alloc


def _refused(code):
    try:
        parse(code)
    except ValueError:
        return
    raise AssertionError('not caught: ' + code)


def _swaps_refused(code, allow_other_name=False):
    ds = [i for i, ch in enumerate(code) if ch.isdigit()]
    for a, b in zip(ds, ds[1:]):
        if b == a + 1 and code[a] != code[b]:
            sw = code[:a] + code[b] + code[a] + code[b + 1:]
            try:
                p = parse(sw)
            except ValueError:
                continue
            assert allow_other_name and p.get('word') and a < 6, 'swap not caught: ' + sw


# Two or more areas with the same name, decoding to different places with no context.
SAME_NAME = [
    # (remembered form, sector, place index, word of that area)
    ('Bandim 275', 10, 22, 'Bandim'),      # the Bissau bairro, block 0-1999
    ('Bandim 2001', 93, 5, 'Bandim'),      # the tabanca in Catió, block 2000-2199
    ('Missira 15', 10, 50, 'Missira'),     # Bissau, block 0-4999
    ('Missirá 5001', 65, 73, 'Missirá'),   # Sonaco, block 5000-5499
    ('missira 6001', 21, 92, 'Missirá'),   # Bafatá, block 6000-6199, typed without the accent
    ('Afia 1', 43, 16, 'Hafia'),           # Safim (written Hafia): the largest shared range, 13 areas, 0-15719
    ('Hafia 15701', 62, 105, 'Áfià'),      # Gabú (written Áfià), the last block of that range; any spelling
]


def same_name_vectors():
    rows = []
    for text, s, p, w in SAME_NAME:
        r = from_remembered(text)
        assert (r['sector'], r['place']) == (s, p), (text, r)
        assert name_key(r['word']) == name_key(w)
        n = r['number']
        chk = check_digit(name_id(name_key(w)), n)
        assert from_remembered(f'{text}-{chk}')['machine'] == r['machine']
        _refused_remembered(f'{text}-{(chk + 1) % 10}')
        # every single wrong digit in the (5-digit) number, with the plate's check digit, is refused,
        # including the ones that would land in another area of the same name
        word = text.rsplit(' ', 1)[0]
        ns = f'{n:05d}'
        for i in range(5):
            for d in '0123456789':
                n2 = int(ns[:i] + d + ns[i + 1:])
                if d != ns[i] and n2 > 0:
                    _refused_remembered(f'{word} {n2}-{chk}')
        for i in range(4):
            sw = ns[:i] + ns[i + 1] + ns[i] + ns[i + 2:]
            if sw != ns and int(sw) > 0:
                _refused_remembered(f'{word} {int(sw)}-{chk}')
        rows.append({'remembered': text, 'written': f"{r['word']} {n}-{chk}", 'machine': r['machine'], 'sector': f"{s} {r['sectorName']}"})
    # the unchecked remembered forms of the vectors differ, and so do their machine forms
    assert len({r['machine'] for r in rows}) == len(rows)
    # a spare number of a name is refused, never guessed into a nearby area
    _refused_remembered('Bandim 2275')
    # spelling variants are one name, one range
    assert name_key('Sintchã Dulo') == name_key('Sinchã Duló') == name_key('Sincha Dulu')
    assert name_key('Plack II') == name_key('Plaque 2') != name_key('Plaque')
    assert name_key('Bairro de Ajuda') == name_key('Ajuda') and name_key('Santa-Luzia') == name_key('santa luzia')
    return rows


# Plate names (SPEC 5.1.2): (a) a long official name -> its plate name, and typing the
# official name still decodes; (b) two areas whose names differ officially but collide after
# shortening share one range and decode to different places.
PLATES = [
    # (official name, plate name, sector, place index, a number of that area)
    ('Sinchã Malam Baio', 'Malam Baio', 24, 148, 1),       # Galomaro: settlement word dropped
    ('Bairro Ajuda II Phase', 'Ajuda II', 10, 12, 1),      # Bissau: generic words dropped
    ('Ama Seidi', 'Ama Seidi', 62, 153, 1),                # Gabú: as is, block 0-999
    ('Missirá Ama Sidi', 'Ama Sidi', 72, 175, 1001),       # Farim: shortened, same name key, block 1000-1099
]


def plate_vectors():
    rows = []
    for official, plate, s, p, n in PLATES:
        t = places()[(s, p)]
        assert t['officialName'] == official and t['word'] == plate, (t['officialName'], t['word'])
        check_plate(plate)
        r = from_remembered(f'{plate} {n}')
        assert (r['sector'], r['place']) == (s, p), (plate, r)
        if official != plate:
            assert not plate_names.fits(official, LANG) or name_key(official) != name_key(plate)
            assert from_remembered(f'{official} {n}')['machine'] == r['machine']  # the official name decodes too
        chk = check_digit(name_id(name_key(plate)), n)
        rows.append({'remembered': f'{plate} {n}', 'written': f'{plate} {n}-{chk}', 'machine': r['machine'],
                     'sector': f"{s} {sectors()[s]['name']}", 'official': official})
    # (b): 'Ama Seidi' and 'Missirá Ama Sidi' are different names officially, one plate name after shortening
    assert name_key('Ama Seidi') == name_key('Ama Sidi') != name_key('Missirá Ama Sidi')
    assert from_remembered('Ama Seidi 1')['machine'] != from_remembered('Ama Sidi 1001')['machine']
    # the engine refuses a plate name over the limit
    for bad in ('Sinchã Malam Baio', 'Ponta Manuel das Águas', 'Zona 7'):
        try:
            check_plate(bad)
            raise AssertionError('over-long plate name accepted: ' + bad)
        except ValueError:
            pass
    try:
        allocate([{'key': name_key('Sinchã Malam Baio'), 'word': 'Sinchã Malam Baio', 'sector': 24, 'index': 148, 'compounds': 5}])
        raise AssertionError('over-long plate name allocated')
    except ValueError:
        pass
    # an abbreviated plate name decodes from the full form typed
    assert name_key('Sto António') == name_key('Santo António') and name_key('S. Miguel') == name_key('São Miguel')
    return rows


def _refused_remembered(text):
    try:
        from_remembered(text)
    except ValueError:
        return
    raise AssertionError('not caught: ' + text)


def allocation_vectors():
    """Blocks are frozen at issue: a later area of the same name gets a new block above the
    name's high-water mark and nobody else's numbers move; a full block gets a continuation."""
    first = allocate([{'key': 'kumura', 'word': 'Cumura', 'sector': 43, 'index': 7, 'compounds': 310},
                      {'key': 'kumura', 'word': 'Cumura', 'sector': 75, 'index': 12, 'compounds': 40},
                      {'key': 'atufa', 'word': 'Atufa', 'sector': 75, 'index': 39, 'compounds': 34}])
    t1 = [(b['sector'], b['index'], b['from'], b['to']) for b in first['kumura']['blocks']]
    assert t1 == [(43, 7, 0, 1999), (75, 12, 2000, 2199)], t1
    later = allocate([{'key': 'kumura', 'word': 'Cúmura', 'sector': 22, 'index': 3, 'compounds': 600}], names=first)
    t2 = [(b['sector'], b['index'], b['from'], b['to']) for b in later['kumura']['blocks']]
    assert t2[:2] == t1 and t2[2] == (22, 3, 3000, 7999), t2
    assert later['atufa']['id'] == first['atufa']['id'] and later['kumura']['id'] == first['kumura']['id']
    cont = continuation(later, 'kumura', 75, 12, 40)
    assert (cont['from'], cont['to']) == (8000, 8199)
    assert block_of('kumura', 2150, later) == (75, 12) and block_of('kumura', 8001, later) == (75, 12)
    assert block_of('kumura', 2250, later) is None
    try:
        allocate([{'key': 'x', 'word': 'X', 'sector': 10, 'index': 1, 'compounds': 30000}])
        raise AssertionError('overflow not refused')
    except OverflowError:
        pass
    return {'first': t1, 'afterNewArea': t2, 'continuation': [cont['from'], cont['to']]}


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 2:
        lat, lon = float(a[0]), float(a[1])
        print(encode_spot(lat, lon), encode_spot(lat, lon, refine=True), place_for(lat, lon).get('word'))
    elif len(a) == 1 and re.match(r'^\d', a[0]):
        p = parse(a[0])
        print(json.dumps(p), json.dumps(decode_spot(a[0])) if p['kind'] == 'spot' else '(registry lookup)')
    elif len(a) == 1:
        print(json.dumps(from_remembered(a[0]), ensure_ascii=False))
    else:
        out, forms, addhome, total, cross_name, same_name, alloc = selftest()
        for r in out:
            print(f"{r['place']:<38} {r['lat']:>8.4f} {r['lon']:>9.4f}  {r['key']} {r['spot']:<16} {r['refined']:<18} "
                  f"cell {r['cellMetres']:>4} m  place word: {r['placeWord']} ({r['sector']}-{r['placeIndex']:03d})")
        print('machine forms:', ', '.join(forms))
        print('same name, different areas:')
        for r in same_name:
            print(f"  {r['remembered']:<14} {r['written']:<16} {r['machine']:<16} {r['sector']}" + (f"  (official: {r['official']})" if r.get('official') else ''))
        print('block allocation:', json.dumps(alloc))
        print('add my home:', json.dumps(addhome))
        print(f'check digit: {total} single-digit errors tried; all caught except {cross_name} in SS-PPP that land on a '
              f'differently named place; every adjacent swap in the number caught')
        print('all test vectors pass')
