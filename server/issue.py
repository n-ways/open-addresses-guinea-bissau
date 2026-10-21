"""Issuing a code for a new compound or another door, and changing a code's status or entrance.

The rules are the issuer's, step for step (engine/SPEC.md 5.1 and 7.2):

1. The point must fall inside a sector and lie inside the national border or within 300 m
   of it (SPEC 3.1): a sector outline that spills over the border never decides.
2. A new compound (no `of`) is refused when a live code's entrance or recorded outline is
   within 3 m of the point, or when the outline given overlaps a recorded outline by more
   than half of the smaller one. An outline must enclose 6 m² to 2 ha.
3. Another door (`of`) must stand within 80 m of that code's entrance; it takes the same
   area.
4. A new compound takes the nearest place of its sector and land mass within 3 km, else
   the sector's own word (the reference engine's place rule).
5. Its number: between its two neighbours on the Hilbert curve in one of the area's
   blocks, else after the area's highest number, else the first number of a continuation
   block above the name's high-water mark (the reference engine's insert()).
6. The code is provisional and marked on-demand. Numbers are never reused, retired ones
   included.
"""
import hashlib
import json
import math
import time

from . import geo
from .engine import BISSAU_POSTCODE, BISSAU_SECTOR, format_blocks, ref

PER_DAY = 5           # new codes per key in any 24 hours, unless ISSUE_PER_DAY says otherwise
MIN_AREA_M2 = 6.0
MAX_AREA_M2 = 20000.0
EXISTS_M = 3.0        # a live code this close to the point is the building's own
DOOR_MAX_M = 80.0     # another door stands at most this far from the code's entrance
MOVE_MAX_M = 80.0     # an entrance moves at most this far


def sector_at(reg, lat, lng):
    """The sector of a point, or None outside Guinea-Bissau: in no sector, or more than 300 m
    outside the national border whatever the sector outlines say (SPEC 3.1)."""
    sector = ref.sector_of(lat, lng)
    if sector is None or reg.sector(sector) is None or not ref.border().holds(lat, lng):
        return None
    return sector


class IssueError(Exception):
    def __init__(self, status, code, message, card=None):
        super().__init__(message)
        self.status, self.code, self.message, self.card = status, code, message, card


def key_id(key):
    return hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]


def _num(v, name):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise IssueError(400, 'bad_request', f'"{name}" must be a number.')
    return float(v)


def _round1(x):
    return round(x * 10) / 10


def issue(store, body, key, per_day, card_of, now=None):
    """Issue one code. body: {"lat", "lng", "outline"?: [[lng, lat], ...], "of"?: machine}.
    Returns the new code's row. card_of(row) builds the card for a 409 answer."""
    if not isinstance(body, dict):
        raise IssueError(400, 'bad_request', 'The body must be a JSON object with "lat" and "lng".')
    lat, lng = _num(body.get('lat'), 'lat'), _num(body.get('lng'), 'lng')
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise IssueError(400, 'bad_request', 'lat must be within ±90 and lng within ±180.')
    of = body.get('of') or ''
    if not isinstance(of, str):
        raise IssueError(400, 'bad_request', '"of" must be the machine code of the compound.')
    of = of.strip()
    outline = body.get('outline')
    if outline is not None:
        if not isinstance(outline, list) or not all(isinstance(p, list) and len(p) == 2 for p in outline):
            raise IssueError(400, 'bad_request', '"outline" must be a list of [lng, lat] pairs.')
        for p in outline:
            _num(p[0], 'outline'), _num(p[1], 'outline')
    now = time.time() if now is None else now
    kid = key_id(key)
    n = store.issued_since(kid, now - 86400)
    if n >= per_day:
        raise IssueError(429, 'rate_limited', f'This key has issued {n} new codes in the last 24 hours. Try again later.')
    reg = store.register
    with store.write_lock:
        sector = sector_at(reg, lat, lng)
        if sector is None:
            raise IssueError(422, 'outside', 'That point is outside Guinea-Bissau, so it cannot have a Guinea-Bissau code.')
        ring, area_m2 = None, 0.0
        if not of:
            near = store.within(lat, lng, EXISTS_M)
            hit = near[0][1] if near else None
            if hit is None:
                for o in store.outlines_near(lat, lng):
                    r = [tuple(p) for p in json.loads(o['ring'])]
                    if geo.ring_distance_m(lat, lng, r) <= EXISTS_M:
                        hit = store.by_machine(o['machine'])
                        break
            if hit is not None:
                raise IssueError(409, 'exists', f'This building already has its code: {hit["home"]}.', card_of(hit))
            if outline is not None and len(outline) >= 3:
                ring = geo.ring_open(outline)
                area_m2 = geo.ring_area_m2(ring)
                if len(ring) < 3 or area_m2 < MIN_AREA_M2 or area_m2 > MAX_AREA_M2:
                    raise IssueError(422, 'bad_outline', f'That outline is {area_m2:.0f} m², but a home is between 6 m² and 2 ha.')
                for o in store.outlines_near(lat, lng):
                    r = [tuple(p) for p in json.loads(o['ring'])]
                    if geo.overlap_share(ring, r) > 0.5:
                        hit = store.by_machine(o['machine'])
                        raise IssueError(409, 'exists', f'This building already has its code: {hit["home"]}.', card_of(hit))
        if of:
            row = store.by_machine(of)
            if row is None:
                raise IssueError(404, 'not_found', f'There is no code {of} to add a door to.')
            if geo.walk_m(row['lat'], row['lng'], lat, lng) > DOOR_MAX_M:
                raise IssueError(422, 'too_far', f'That door is more than 80 m from {row["home"]}.')
            area = reg.by_ref[row['area']]
        else:
            area = reg.place_for(sector, lat, lng)
        if area is None:
            raise IssueError(422, 'outside', 'There is no place name for this point.')
        issued = store.area_numbers(area.ref)
        number, block = ref.insert(area.sector, lat, lng, issued, area.blocks, reg.high_water(area.name_key))
        if number is None:
            raise IssueError(409, 'name_full', f'{area.plate_name} has used every number of its name: its sector chooses '
                                               'a qualifier before more homes there get a code.')
        f = reg.forms(area, number)
        if store.by_machine(f['machine']) is not None:
            raise IssueError(409, 'busy', 'That number was taken a moment ago. Try again.')
        if ring is not None:
            cls, structures, floor = 'residential.compound-house', 1, _round1(area_m2)
        else:
            cls, structures, floor = '', 0, 0.0
        rec = {
            'machine': f['machine'], 'home': f['home'], 'written': f['written'], 'area': area.ref,
            'official_name': area.official_name, 'number': str(number), 'check': str(f['check']),
            'status': 'provisional', 'issued': 'on-demand',
            'issued_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now)),
            'entrance_lat': '%.7f' % lat, 'entrance_lng': '%.7f' % lng, 'entrance_kind': 'door' if of else 'centre',
            'plus_code': geo.plus_code(lat, lng), 'class': cls, 'use': 'residential', 'kind': 'door' if of else 'building',
            'structures': str(structures), 'floor_area_m2': '%.1f' % floor, 'settlement': '',
            'postcode': BISSAU_POSTCODE if area.sector == BISSAU_SECTOR else '',
        }
        con = store.con()
        con.execute('BEGIN IMMEDIATE')
        try:
            new_blocks = None
            if block is not None:
                new_blocks = (format_blocks(area.blocks + [block]), area.ref)
            store.insert_code(con, rec, area.sector_key, area.name_id, number, lat, lng, ring, new_blocks, kid, now)
            con.execute('COMMIT')
        except BaseException:
            con.execute('ROLLBACK')
            raise
        if block is not None:
            reg.add_block(area, block)
        return store.by_machine(f['machine'])


STATUSES = ('provisional', 'confirmed', 'retired')


def change(store, row, body):
    """PATCH: {"status"?: "confirmed" | "provisional" | "retired", "entrance"?: {"lat", "lng"}}.
    A retired code stays retired: its number is never given to another compound."""
    if not isinstance(body, dict) or not ({'status', 'entrance'} & set(body)):
        raise IssueError(400, 'bad_request', 'Send "status" and/or "entrance".')
    extra = set(body) - {'status', 'entrance'}
    if extra:
        raise IssueError(400, 'bad_request', f'Unknown field(s): {", ".join(sorted(extra))}.')
    status = body.get('status')
    if status is not None and status not in STATUSES:
        raise IssueError(400, 'bad_request', 'status is provisional, confirmed or retired.')
    if row['status'] == 'retired':
        raise IssueError(409, 'retired', f'{row["home"]} is retired; a retired code is never brought back or reused.')
    move = body.get('entrance')
    if move is not None:
        if not isinstance(move, dict):
            raise IssueError(400, 'bad_request', '"entrance" must be {"lat", "lng"}.')
        mlat, mlng = _num(move.get('lat'), 'entrance.lat'), _num(move.get('lng'), 'entrance.lng')
        d = geo.walk_m(row['lat'], row['lng'], mlat, mlng)
        if d > MOVE_MAX_M:
            raise IssueError(422, 'too_far', f'The new entrance is {d:.0f} m away; an entrance moves at most 80 m.')
        if sector_at(store.register, mlat, mlng) is None:
            raise IssueError(422, 'outside', 'That point is outside Guinea-Bissau, so an entrance cannot move there.')
    with store.write_lock:
        con = store.con()
        con.execute('BEGIN IMMEDIATE')
        try:
            if move is not None:
                store.set_entrance(con, row, mlat, mlng, geo.plus_code(mlat, mlng))
            if status is not None and status != row['status']:
                store.set_status(con, row['machine'], status)
            con.execute('COMMIT')
        except BaseException:
            con.execute('ROLLBACK')
            raise
    return store.by_machine(row['machine'])
