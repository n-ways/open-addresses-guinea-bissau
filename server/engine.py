"""The register in force, read from the database, and the code forms.

The parsing, the check digit, the spot grid, the Hilbert order and the numbering
rules all come from the reference engine (engine/reference/gw_codes.py). This
module only adds what a running registry needs on top of it: the frozen area
table as it stands in the database (blocks grow when an area takes a
continuation block), and the lookups that go with it.
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'engine', 'reference'))

import gw_codes as ref  # noqa: E402

COUNTRY = 'GW'
COUNTRY_NAME = 'Guinea-Bissau'
CREDIT = 'N-Ways Addressing for Guinea-Bissau, © N-WAYS LIMITED (nways.ng)'
CREDIT_URL = 'https://github.com/n-ways/open-addresses-guinea-bissau'
SPEC = 'SPEC v1.0'
BISSAU_SECTOR = 10
BISSAU_POSTCODE = '1000'  # the one postcode attested for the country (UPU, 2005), shown as context


class LookupError_(Exception):
    """A typed code that does not decode. code is the API error code."""

    def __init__(self, code, message, status=404):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def parse_blocks(text):
    """'0-499|600-699' -> [(0, 499), (600, 699)]."""
    out = []
    for part in (text or '').split('|'):
        if part:
            lo, hi = part.split('-')
            out.append((int(lo), int(hi)))
    return out


def format_blocks(blocks):
    return '|'.join(f'{lo}-{hi}' for lo, hi in blocks)


class Area:
    """One row of the frozen area table (registry/areas.csv)."""

    __slots__ = ('ref', 'sector', 'index', 'sector_key', 'plate_name', 'official_name', 'kind', 'name_key',
                 'name_id', 'blocks', 'needs_council_choice', 'aliases', 'landmass', 'lat', 'lon')

    def __init__(self, row):
        self.ref = row['area']
        self.sector = int(row['sector'])
        self.index = int(row['index'])
        self.sector_key = row['sector_key']
        self.plate_name = row['plate_name']
        self.official_name = row['official_name']
        self.kind = row['kind']
        self.name_key = row['name_key']
        self.name_id = int(row['name_id'])
        self.blocks = parse_blocks(row['blocks'])
        self.needs_council_choice = row['needs_council_choice'] == 'true'
        self.aliases = [a for a in (row['aliases'] or '').split('|') if a]
        self.landmass = row['landmass']
        self.lat = float(row['lat']) if row['lat'] else None
        self.lon = float(row['lon']) if row['lon'] else None

    def owns(self, number):
        return any(lo <= number <= hi for lo, hi in self.blocks)

    def as_candidate(self):
        """The shape the reference engine's place rule takes."""
        return {'sector': self.sector, 'index': self.index, 'lat': self.lat, 'lon': self.lon,
                'landmass': self.landmass, 'ref': self.ref}

    def summary(self):
        return {'id': self.ref, 'plate_name': self.plate_name, 'official_name': self.official_name or self.plate_name,
                'kind': self.kind, 'needs_council_choice': self.needs_council_choice}


class Register:
    """Sectors (from model/sectors.json) and the area table in force (from the database)."""

    def __init__(self, area_rows):
        self.sectors = {}
        for s in ref._load(os.path.join(REPO, 'model', 'sectors.json'))['sectors']:
            self.sectors[s['number']] = {'number': s['number'], 'key': s['key'], 'name': s['name'],
                                         'region': s['region'], 'grid': s['grid']}
        self.by_key = {s['key']: s for s in self.sectors.values()}
        reg = ref._load(os.path.join(REPO, 'engine', 'data', 'register.json'))
        self.aliases = dict(reg['aliases'])          # alias name key -> plate-name key
        self.ids = dict(reg['ids'])                  # name key -> national number of the name
        self.areas = []
        self.by_ref = {}
        self.by_pair = {}
        self.in_sector = {}
        self.families = {}
        for row in area_rows:
            self.add(Area(row))
        self._sort_families()
        pairs = [(w, self.aliases.get(ref.name_key(w), a.name_key))
                 for a in self.areas for w in [a.plate_name, a.official_name] + a.aliases if w]
        self.unmarked = ref.without_cedilla(pairs)   # 'Praca' typed for 'Praça'

    def add(self, a):
        self.areas.append(a)
        self.by_ref[a.ref] = a
        self.by_pair[(a.sector, a.index)] = a
        self.in_sector.setdefault(a.sector, []).append(a)
        self.families.setdefault(a.name_key, []).append(a)
        self.ids.setdefault(a.name_key, a.name_id)

    def _sort_families(self):
        def first(a):
            return a.blocks[0][0] if a.blocks else ref.MAX_NUMBER + 1
        for fs in self.families.values():
            fs.sort(key=lambda a: (first(a), a.ref))

    def add_block(self, area, block):
        area.blocks.append(block)
        self._sort_families()

    # ------------------------------------------------------------------ lookups

    def sector(self, number):
        return self.sectors.get(number)

    def sector_by(self, key):
        """A sector by its key ('BIS') or number ('10')."""
        k = key.strip().upper()
        if k in self.by_key:
            return self.by_key[k]
        if k.isdigit():
            return self.sectors.get(int(k))
        return None

    def high_water(self, name_key):
        top = 0
        for a in self.families.get(name_key, ()):
            for lo, hi in a.blocks:
                top = max(top, hi + 1)
        return top

    def holder(self, name_key, number):
        for a in self.families.get(name_key, ()):
            if a.owns(number):
                return a
        return None

    def plate_key(self, word):
        """The plate-name key of what someone typed: the plate name itself, or an official
        name or other spelling that points to exactly one plate name."""
        k = ref.name_key(word)
        if any(a.blocks for a in self.families.get(k, ())):
            return k
        if k in self.aliases:
            return self.aliases[k]
        return self.unmarked.get(k, k)

    def areas_named(self, text):
        """Areas whose plate name, official name or alias has the name key of the text."""
        k = ref.name_key(text)
        keys = {k, self.aliases.get(k, k), self.unmarked.get(k, k)}
        out = [a for key in keys for a in self.families.get(key, ())]
        for a in self.areas:
            if a not in out and any(ref.name_key(x) == k for x in [a.official_name] + a.aliases if x):
                out.append(a)
        return sorted(out, key=lambda a: a.ref)

    def place_for(self, sector, lat, lon):
        """The area a new compound takes (SPEC 5.1), by the reference engine's rule."""
        cands = [a.as_candidate() for a in self.in_sector.get(sector, ())]
        best = ref.place_for(lat, lon, sector=sector, candidates=cands)
        return self.by_pair.get((sector, best['index']))

    # ------------------------------------------------------------------ forms

    def forms(self, area, number):
        chk = ref.check_digit(area.name_id, number)
        home = ref.remembered(area.plate_name, number)
        return {
            'machine': f'{area.sector:02d}-{area.index:03d}-{number:05d}-{chk}',
            'home': home,
            'written': home,  # plates and written forms carry no check digit
            'spoken': ref.spoken(area.plate_name, number),
            'check': chk,
        }

    # ------------------------------------------------------------------ decoding

    def machine(self, text):
        """'10-022-00537-4' (optionally '.2' for a structure, '/1' for a door) -> (area,
        number, structure, door). A wrong check digit is refused, never corrected."""
        c = text.strip().replace(' ', '')
        m = ref.ADDR.match(c)
        if not m:
            raise LookupError_('bad_code', f'{text.strip()!r} is not a Guinea-Bissau machine code (SS-PPP-NNNNN-C).', 400)
        ss, pp, n, sub, chk, door = m.groups()
        if sub is not None and sub.startswith('0'):
            raise LookupError_('bad_code', 'Structure numbers start at 1.', 400)
        s_, p_, n_ = int(ss), int(pp), int(n)
        if s_ not in self.sectors:
            raise LookupError_('unknown_sector', f'There is no sector {ss}.')
        a = self.by_pair.get((s_, p_))
        if a is None:
            raise LookupError_('unknown_area', f'There is no place {ss}-{pp}.')
        if ref.check_digit(a.name_id, n_, sub) != int(chk):
            raise LookupError_('bad_check', 'The check digit does not match: a digit is wrong or two are swapped.', 422)
        if self.holder(a.name_key, n_) is not a:
            raise LookupError_('not_issued', f'Number {n_} of {a.plate_name} does not belong to place {ss}-{pp}.')
        return a, n_, int(sub) if sub else None, int(door) if door else None

    def remembered(self, text):
        """'Bandim 537', 'bandim 537', 'Bandim 537-4', 'Sinchã Malam Baio 1, Galomaro'
        -> (area, number, structure). No town, sector or position is needed."""
        t = text.strip()
        cut = re.search(r'[,·]', t)
        if cut and cut.start() > 0:
            t = t[:cut.start()].strip()
        t = re.sub(r'\s+', ' ', t)
        m = ref.SPOKEN.match(t)
        if not m:
            raise LookupError_('bad_code', 'Say it as a place word, then the number: "Bandim 537".', 400)
        word, n, sub, chk = m.groups()
        if sub is not None and sub.startswith('0'):
            raise LookupError_('bad_code', 'Structure numbers start at 1.', 400)
        n = int(n)
        key = self.plate_key(word)
        nid = self.ids.get(key)
        if not nid:
            raise LookupError_('unknown_name', f'No place in Guinea-Bissau is called {word!r}.')
        if chk is not None and ref.check_digit(nid, n, sub) != int(chk):
            raise LookupError_('bad_check', 'The check digit does not match: a digit is wrong or two are swapped.', 422)
        a = self.holder(key, n)
        if a is None:
            raise LookupError_('not_issued', f'{word} {n} has not been issued: the number is a spare number of that name.')
        return a, n, int(sub) if sub else None

    def zone_json(self, number):
        s = self.sectors[number]
        return {'key': s['key'], 'number': s['number'], 'name': s['name'], 'region': s['region']}


def looks_spot(text):
    return bool(ref.SPOT.match(text.strip().replace(' ', '')))


def looks_machine(text):
    return bool(ref.ADDR.match(text.strip().replace(' ', '')))


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)
