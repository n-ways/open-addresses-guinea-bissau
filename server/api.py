"""The JSON API under /v1 (see server/openapi.yaml and docs/api.md)."""
import hmac
import json
import re
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import geo, issue as issuing
from .engine import (COUNTRY, COUNTRY_NAME, CREDIT, CREDIT_URL, SPEC, LookupError_, looks_machine, looks_spot, ref)
from .store import CODE_COLUMNS, text_key

AT_FOUND_M = 12.0     # a code's entrance or outline this close to the point is the compound there
SPOT_FOUND_M = 15.0   # a spot code names the compound whose entrance is this close to its centre
NEAR_MAX_M = 500.0
NEAR_MAX_N = 100
PAGE_MAX = 1000
BODY_MAX = 65536


class ApiError(Exception):
    def __init__(self, status, code, message, extra=None):
        super().__init__(message)
        self.status, self.code, self.message, self.extra = status, code, message, extra


class Api:
    """Request handling, independent of the HTTP plumbing (the tests call it directly)."""

    def __init__(self, store, issue_keys=(), per_day=issuing.PER_DAY):
        self.store = store
        self.reg = store.register
        self.keys = [k for k in issue_keys if k]
        self.per_day = per_day
        self.routes = [
            ('GET', r'/v1/health', self.health),
            ('GET', r'/v1/info', self.info),
            ('GET', r'/v1/find', self.find),
            ('GET', r'/v1/at', self.at),
            ('GET', r'/v1/near', self.near),
            ('GET', r'/v1/verify', self.verify),
            ('GET', r'/v1/spot', self.spot),
            ('GET', r'/v1/spot/decode', self.spot_decode),
            ('GET', r'/v1/zones', self.zones),
            ('GET', r'/v1/zones/(?P<key>[^/]+)', self.zone),
            ('GET', r'/v1/zones/(?P<key>[^/]+)/codes', self.zone_codes),
            ('GET', r'/v1/areas', self.areas),
            ('GET', r'/v1/areas/(?P<id>[^/]+)', self.area),
            ('GET', r'/v1/codes/(?P<machine>[^/]+)', self.code),
            ('POST', r'/v1/codes', self.issue),
            ('PATCH', r'/v1/codes/(?P<machine>[^/]+)', self.patch),
        ]
        self.compiled = [(m, re.compile('^' + p + '$'), h) for m, p, h in self.routes]

    # ------------------------------------------------------------------ dispatch

    def handle(self, method, path, query, headers, body):
        """-> (status, JSON-able object)."""
        try:
            path = urllib.parse.unquote(path.rstrip('/') or '/')
            allowed = []
            for m, rx, h in self.compiled:
                mt = rx.match(path)
                if not mt:
                    continue
                if m != method:
                    allowed.append(m)
                    continue
                return h(query=query, headers=headers, body=body, **mt.groupdict())
            if allowed:
                raise ApiError(405, 'method_not_allowed', f'{method} is not allowed here; use {", ".join(sorted(set(allowed)))}.')
            raise ApiError(404, 'not_found', f'There is no endpoint {path}. See /v1/info and docs/api.md.')
        except ApiError as e:
            err = {'code': e.code, 'message': e.message}
            if e.extra:
                err.update(e.extra)
            return e.status, {'error': err}
        except LookupError_ as e:
            return e.status, {'error': {'code': e.code, 'message': e.message}}
        except issuing.IssueError as e:
            err = {'code': e.code, 'message': e.message}
            if e.card is not None:
                err['card'] = e.card
            return e.status, {'error': err}

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _q(query, name, required=True):
        v = query.get(name, [''])[0].strip()
        if required and not v:
            raise ApiError(400, 'bad_request', f'The query parameter "{name}" is required.')
        return v

    def _float(self, query, name, lo, hi, default=None):
        raw = self._q(query, name, required=default is None)
        if not raw:
            return default
        try:
            v = float(raw)
        except ValueError:
            raise ApiError(400, 'bad_request', f'"{name}" must be a number.')
        if not (lo <= v <= hi):
            raise ApiError(400, 'bad_request', f'"{name}" must be between {lo:g} and {hi:g}.')
        return v

    def _point(self, query):
        return self._float(query, 'lat', -90, 90), self._float(query, 'lng', -180, 180)

    def _spot_of(self, lat, lng, sector=None):
        try:
            return ref.encode_spot(lat, lng)
        except ValueError:
            if sector is None:
                return None
            try:
                return ref.encode_spot(lat, lng, sector=sector)
            except ValueError:
                return None

    def card(self, row):
        a = self.reg.by_ref[row['area']]
        z = self.reg.zone_json(a.sector)
        lat, lng = float(row['entrance_lat']), float(row['entrance_lng'])
        number = int(row['number'])
        return {
            'country': COUNTRY,
            'machine': row['machine'],
            'home': row['home'],
            'written': row['written'],
            'spoken': ref.spoken(a.plate_name, number),
            'number': number,
            'check': int(row['check']),
            'status': row['status'],
            'issued': row['issued'],
            'issued_at': row['issued_at'],
            'area': a.summary(),
            'zone': z,
            'full_line': f"{row['home']} · {z['name']}",
            'entrance': {'lat': lat, 'lng': lng, 'kind': row['entrance_kind']},
            'spot': self._spot_of(lat, lng, a.sector),
            'plus_code': row['plus_code'],
            'building': {'class': row['class'] or None, 'use': row['use'] or None, 'kind': row['kind'] or None,
                         'structures': int(row['structures'] or 0), 'floor_area_m2': float(row['floor_area_m2'] or 0),
                         'settlement': row['settlement'] or None},
            'postcode': row['postcode'] or None,
            'record': {c: row[c] for c in CODE_COLUMNS},
            'credit': CREDIT,
            'credit_url': CREDIT_URL,
        }

    def compact(self, row, distance=None):
        out = {'machine': row['machine'], 'home': row['home'], 'area': row['area'], 'zone': row['zone'],
               'status': row['status'], 'entrance': {'lat': float(row['entrance_lat']), 'lng': float(row['entrance_lng'])}}
        if distance is not None:
            out['distance_m'] = round(distance, 1)
        return out

    def _code_at(self, lat, lng, max_m):
        """The live code at a point: an outline that holds it, else the nearest entrance or
        outline within max_m. -> (distance, row) or None."""
        best = None
        for o in self.store.outlines_near(lat, lng):
            d = geo.ring_distance_m(lat, lng, [tuple(p) for p in json.loads(o['ring'])])
            if d <= max_m and (best is None or (d, o['machine']) < (best[0], best[1]['machine'])):
                best = (d, self.store.by_machine(o['machine']))
        near = self.store.within(lat, lng, max_m)
        if near and (best is None or (near[0][0], near[0][1]['machine']) < (best[0], best[1]['machine'])):
            best = near[0]
        return best

    def _row_of(self, area, number):
        row = self.store.by_area_number(area.ref, number)
        if row is None:
            f = self.reg.forms(area, number)
            raise ApiError(404, 'not_issued', f'No compound has {f["home"]} yet: the number is in the range of '
                                              f'{area.plate_name}, {self.reg.sectors[area.sector]["name"]}, but unused.')
        return row

    def _area_json(self, a, counts=None):
        out = a.summary()
        out.update({'zone': a.sector_key, 'name_key': a.name_key, 'name_id': a.name_id,
                    'blocks': [[lo, hi] for lo, hi in a.blocks], 'aliases': a.aliases, 'landmass': a.landmass or None,
                    'lat': a.lat, 'lon': a.lon})
        if counts is not None:
            out['codes'] = counts.get(a.ref, 0)
        return out

    def _zone_of(self, key):
        s = self.reg.sector_by(key)
        if s is None:
            raise ApiError(404, 'not_found', f'There is no zone {key!r}. GET /v1/zones lists them.')
        return s

    def _auth(self, headers):
        if not self.keys:
            raise ApiError(403, 'read_only', 'This deployment is read-only: it does not issue or change codes.')
        h = headers.get('Authorization', '')
        if not h.startswith('Bearer '):
            raise ApiError(401, 'unauthorized', 'Send the issuing key as "Authorization: Bearer <key>".')
        key = h[7:].strip()
        if not any(hmac.compare_digest(key.encode(), k.encode()) for k in self.keys):
            raise ApiError(401, 'unauthorized', 'That key is not an issuing key of this deployment.')
        return key

    @staticmethod
    def _json(body):
        try:
            return json.loads(body.decode('utf-8') if body else '')
        except (ValueError, UnicodeDecodeError):
            raise ApiError(400, 'bad_request', 'The body must be JSON.')

    # ------------------------------------------------------------------ endpoints

    def health(self, **_):
        return 200, {'status': 'ok', 'country': COUNTRY, 'codes': self.store.count(),
                     'registry_exported': self.store.meta.get('exported') or None, 'issuing': bool(self.keys)}

    def info(self, **_):
        by_zone = self.store.counts_by_zone()
        return 200, {
            'country': COUNTRY, 'name': COUNTRY_NAME, 'zone_kind': 'sector',
            'zones': len(self.reg.sectors), 'areas': len(self.reg.areas), 'codes': sum(by_zone.values()),
            'by_status': self.store.counts_by_status(), 'by_zone': dict(sorted(by_zone.items())),
            'licences': {'code': 'Apache-2.0', 'data': 'ODbL-1.0', 'documents': 'CC-BY-4.0'},
            'credit': CREDIT, 'credit_url': CREDIT_URL,
            'engine': {'spec': SPEC, 'reference': 'engine/reference/gw_codes.py'},
            'registry_exported': self.store.meta.get('exported') or None,
            'issuing': {'enabled': bool(self.keys), 'per_key_per_day': self.per_day if self.keys else 0},
        }

    def code(self, machine, **_):
        a, n, sub, door = self.reg.machine(machine)
        row = self._row_of(a, n)
        out = self.card(row)
        if sub:
            out['structure'] = sub
        if door:
            out['door'] = door
        return 200, out

    def find(self, query, **_):
        q = self._q(query, 'q')
        if len(q) > 120:
            raise ApiError(400, 'bad_request', 'That is too long to be a code.')
        if looks_spot(q):
            try:
                d = ref.decode_spot(q.replace(' ', ''))
            except ValueError as e:
                code, status = ('bad_check', 422) if 'check digit' in str(e) else ('bad_code', 400)
                raise ApiError(status, code, f'{e}.'.replace("check digit fails", "The check digit does not match"))
            hit = self._code_at(d['lat'], d['lon'], SPOT_FOUND_M)
            if hit is None:
                raise ApiError(404, 'not_found', f'The spot {q} is not on a compound with a code.',
                               {'point': {'lat': d['lat'], 'lng': d['lon']}})
            return 200, {'query': q, 'kind': 'spot', 'matches': [self.card(hit[1])]}
        if looks_machine(q):
            a, n, sub, door = self.reg.machine(q)
            row = self._row_of(a, n)
            out = {'query': q, 'kind': 'machine', 'matches': [self.card(row)]}
            if sub:
                out['structure'] = sub
            if door:
                out['door'] = door
            return 200, out
        try:
            a, n, sub = self.reg.remembered(q)
        except LookupError_ as e:
            rows = self._official(q)
            if rows:
                return 200, {'query': q, 'kind': 'official', 'matches': [self.card(r) for r in rows]}
            raise e
        row = self._row_of(a, n)
        if row['status'] == 'retired':
            raise ApiError(404, 'retired', f'{row["home"]} was retired: there is no compound there any more.')
        out = {'query': q, 'kind': 'remembered', 'matches': [self.card(row)]}
        if sub:
            out['structure'] = sub
        return 200, out

    def _official(self, q):
        """An official address: the place's official name and the number ('Sinchã Adulai 1')."""
        m = re.match(r'^(.+?)\s+(\d{1,5})$', re.split(r'[,·]', q)[0].strip())
        if not m:
            return []
        return [r for r in self.store.by_official(text_key(m.group(1)), int(m.group(2))) if r['status'] != 'retired']

    def at(self, query, **_):
        lat, lng = self._point(query)
        sector = issuing.sector_at(self.reg, lat, lng)
        if sector is None:
            return 200, {'status': 'outside', 'message': 'That point is not inside a sector of Guinea-Bissau.'}
        zone = self.reg.zone_json(sector)
        hit = self._code_at(lat, lng, AT_FOUND_M)
        if hit is not None:
            return 200, {'status': 'found', 'distance_m': round(hit[0]), 'code': self.card(hit[1]), 'zone': zone}
        area = self.reg.place_for(sector, lat, lng)
        return 200, {'status': 'none', 'zone': zone, 'area': area.summary() if area else None,
                     'spot': self._spot_of(lat, lng), 'can_issue': bool(self.keys)}

    def near(self, query, **_):
        lat, lng = self._point(query)
        radius = self._float(query, 'radius', 1, NEAR_MAX_M, 100.0)
        limit = int(self._float(query, 'limit', 1, NEAR_MAX_N, 50))
        rows = self.store.within(lat, lng, radius)
        return 200, {'lat': lat, 'lng': lng, 'radius_m': radius, 'count': min(len(rows), limit),
                     'codes': [self.compact(r, d) for d, r in rows[:limit]]}

    def verify(self, query, **_):
        code = self._q(query, 'code')
        out = {'code': code, 'syntax': False, 'check': False, 'issued': False, 'valid': False,
               'status': None, 'machine': None, 'home': None}
        if not looks_machine(code) or looks_spot(code):
            out['message'] = 'Not a Guinea-Bissau machine code (SS-PPP-NNNNN-C).'
            return 200, out
        out['syntax'] = True
        try:
            a, n, sub, door = self.reg.machine(code)
        except LookupError_ as e:
            out['message'] = e.message
            if e.code == 'not_issued':
                out['check'] = True
            return 200, out
        out['check'] = True
        row = self.store.by_area_number(a.ref, n)
        if row is None:
            out['message'] = 'The code is well formed and its check digit is right, but it has not been issued.'
            return 200, out
        out.update(issued=True, status=row['status'], machine=row['machine'], home=row['home'],
                   valid=row['status'] != 'retired',
                   message='Issued and live.' if row['status'] != 'retired' else 'Issued, then retired.')
        return 200, out

    def spot(self, query, **_):
        lat, lng = self._point(query)
        try:
            code = ref.encode_spot(lat, lng)
            fine = ref.encode_spot(lat, lng, refine=True)
        except ValueError:
            raise ApiError(422, 'outside', 'That point is not inside a sector of Guinea-Bissau.')
        s = int(code[:2])
        cell = self.reg.sectors[s]['grid']['cellMetres']
        return 200, {'lat': lat, 'lng': lng, 'spot': code, 'refined': fine, 'zone': self.reg.zone_json(s),
                     'cell_m': cell, 'refined_cell_m': round(cell / 3, 2)}

    def spot_decode(self, query, **_):
        code = self._q(query, 'code')
        if not looks_spot(code):
            raise ApiError(400, 'bad_code', 'A spot code looks like 10-4327-8173 or 10-4327-8173.1.')
        try:
            d = ref.decode_spot(code.replace(' ', ''))
        except ValueError as e:
            if 'check digit' in str(e):
                raise ApiError(422, 'bad_check', 'The check digit does not match: a digit is wrong or two are swapped.')
            raise ApiError(404, 'not_found', f'{e}.')
        return 200, {'code': code, 'zone': self.reg.zone_json(d['sector']), 'lat': d['lat'], 'lng': d['lon'],
                     'cell_m': d['cellMetres']}

    def zones(self, **_):
        counts = self.store.counts_by_zone()
        out = []
        for n in sorted(self.reg.sectors):
            z = self.reg.zone_json(n)
            z['areas'] = len(self.reg.in_sector.get(n, ()))
            z['codes'] = counts.get(z['key'], 0)
            out.append(z)
        return 200, {'country': COUNTRY, 'zone_kind': 'sector', 'zones': out}

    def zone(self, key, **_):
        s = self._zone_of(key)
        counts = self.store.counts_by_area(s['key'])
        z = self.reg.zone_json(s['number'])
        areas = sorted(self.reg.in_sector.get(s['number'], ()), key=lambda a: a.index)
        z['codes'] = sum(counts.values())
        z['grid'] = s['grid']
        z['areas'] = [self._area_json(a, counts) for a in areas]
        return 200, z

    def zone_codes(self, key, query, **_):
        s = self._zone_of(key)
        after = self._q(query, 'after', required=False)
        limit = int(self._float(query, 'limit', 1, PAGE_MAX, 100))
        rows = self.store.zone_page(s['key'], after, limit)
        nxt = rows[-1]['machine'] if len(rows) == limit else None
        return 200, {'zone': s['key'], 'after': after or None, 'count': len(rows),
                     'codes': [self.compact(r) for r in rows], 'next': nxt}

    def area(self, id, **_):
        a = self.reg.by_ref.get(id.upper())
        if a is None:
            raise ApiError(404, 'not_found', f'There is no area {id!r}. Area ids look like BIS-022.')
        by_status = self.store.area_status(a.ref)
        out = self._area_json(a)
        out['zone'] = self.reg.zone_json(a.sector)
        out['codes'] = {'total': sum(by_status.values()), 'by_status': by_status}
        out['same_name'] = [x.ref for x in self.reg.families.get(a.name_key, ()) if x is not a]
        out['next_free_after'] = self.reg.high_water(a.name_key)
        return 200, out

    def areas(self, query, **_):
        name = self._q(query, 'name')
        counts = self.store.counts_by_area()
        found = self.reg.areas_named(name)
        if not found:
            raise ApiError(404, 'not_found', f'No place in Guinea-Bissau is called {name!r}.')
        return 200, {'name': name, 'name_key': ref.name_key(name), 'count': len(found),
                     'areas': [self._area_json(a, counts) for a in found]}

    def issue(self, headers, body, **_):
        key = self._auth(headers)
        data = self._json(body)
        row = issuing.issue(self.store, data, key, self.per_day, self.card)
        return 201, self.card(row)

    def patch(self, machine, headers, body, **_):
        self._auth(headers)
        data = self._json(body)
        a, n, sub, door = self.reg.machine(machine)
        if sub or door:
            raise ApiError(400, 'bad_code', 'Change the compound code itself, without a structure or door.')
        row = self._row_of(a, n)
        return 200, self.card(issuing.change(self.store, row, data))


# ---------------------------------------------------------------------- HTTP plumbing

def make_handler(api, cors_origins):
    origins = [o.strip() for o in cors_origins if o.strip()]

    class Handler(BaseHTTPRequestHandler):
        server_version = 'NWaysAddressing/1.0'
        protocol_version = 'HTTP/1.1'

        def _cors(self):
            origin = self.headers.get('Origin')
            if not origin or not origins:
                return
            if '*' in origins:
                self.send_header('Access-Control-Allow-Origin', '*')
            elif origin in origins:
                self.send_header('Access-Control-Allow-Origin', origin)
                self.send_header('Vary', 'Origin')

        def _send(self, status, obj):
            body = json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store' if self.command != 'GET' else 'public, max-age=60')
            self._cors()
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(body)

        def _do(self):
            t0 = time.time()
            u = urllib.parse.urlsplit(self.path)
            try:
                n = int(self.headers.get('Content-Length') or 0)
            except ValueError:
                n = -1
            if n < 0:
                self.close_connection = True
                self._send(400, {'error': {'code': 'bad_request', 'message': 'Content-Length must be a whole number.'}})
                return
            if n > BODY_MAX:
                # the body is left unread, so the connection cannot carry another request
                self.close_connection = True
                self._send(413, {'error': {'code': 'too_large', 'message': 'The body is larger than 64 KB.'}})
                return
            body = self.rfile.read(n) if n else b''
            try:
                status, obj = api.handle(self.command if self.command != 'HEAD' else 'GET', u.path,
                                         urllib.parse.parse_qs(u.query), self.headers, body)
            except Exception as e:  # never leak a traceback to the client
                print(f'error: {self.command} {self.path}: {e!r}', file=sys.stderr)
                status, obj = 500, {'error': {'code': 'internal', 'message': 'Something went wrong on the server.'}}
            self._send(status, obj)
            self.log_message('%s %s %d %.1fms', self.command, u.path, status, (time.time() - t0) * 1000)

        # PUT and DELETE reach the router too, so they get a JSON 405 rather than the stock HTML page
        do_GET = do_POST = do_PATCH = do_HEAD = do_PUT = do_DELETE = _do

        def do_OPTIONS(self):
            self.send_response(204)
            self._cors()
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
            self.send_header('Access-Control-Max-Age', '600')
            self.send_header('Content-Length', '0')
            self.end_headers()

        def log_request(self, code='-', size='-'):
            pass  # one line per request is written by _do

        def log_message(self, fmt, *args):
            sys.stderr.write('%s %s\n' % (self.address_string(), fmt % args))

    return Handler


def serve(store, host, port, issue_keys, per_day, cors_origins):
    api = Api(store, issue_keys, per_day)
    httpd = ThreadingHTTPServer((host, port), make_handler(api, cors_origins))
    httpd.daemon_threads = True
    mode = f'issuing ({len(api.keys)} key(s), {per_day} per key per day)' if api.keys else 'read-only'
    print(f'N-Ways Addressing for {COUNTRY_NAME}: {store.count()} codes, {mode}, on http://{host}:{port}/v1/health',
          file=sys.stderr, flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
