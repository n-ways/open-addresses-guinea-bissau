"""Tests for the registry server: python3 -m unittest discover -s server/tests -t .

They run on server/testdata/registry (the real codes of the Komo sector and the whole area
table) in a temporary database, and never touch a network service.
"""
import csv
import gzip
import http.client
import json
import os
import shutil
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer

from server import geo
from server.api import Api, make_handler
from server.engine import ref
from server.issue import key_id
from server.store import CODE_COLUMNS, RegistryError, Store, export_registry, import_registry

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), 'testdata')
FIXTURE = os.path.join(DATA, 'registry')
KEY = 'test-issuing-key'


def quiet(_):
    pass


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def save(obj, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f)


def read_csv(path):
    with gzip.open(path, 'rt', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def fixture_rows():
    with gzip.open(os.path.join(FIXTURE, 'KOM.csv.gz'), 'rt', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


class Fresh(unittest.TestCase):
    """Each test gets its own database, imported from the fixture."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, 'addresses.sqlite')
        import_registry(FIXTURE, self.db, log=quiet)
        self.store = Store(self.db)
        self.api = Api(self.store, [KEY], per_day=1000)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def get(self, path, **q):
        return self.api.handle('GET', path, {k: [str(v)] for k, v in q.items()}, {}, b'')

    def send(self, method, path, body, key=KEY):
        headers = {'Authorization': 'Bearer ' + key} if key else {}
        return self.api.handle(method, path, {}, headers, json.dumps(body).encode())

    def assertError(self, res, status, code):
        self.assertEqual(res[0], status, res)
        self.assertEqual(set(res[1]), {'error'}, res)
        self.assertEqual(res[1]['error']['code'], code, res)
        self.assertTrue(res[1]['error']['message'])


class ImportExport(Fresh):

    def test_counts(self):
        self.assertEqual(self.store.count(), 750)
        self.assertEqual(self.store.counts_by_zone(), {'KOM': 750})

    def test_round_trip_is_byte_identical(self):
        out = os.path.join(self.tmp.name, 'out')
        export_registry(self.db, out)
        for name in ('areas.csv.gz', 'KOM.csv.gz'):
            with gzip.open(os.path.join(FIXTURE, name)) as a, gzip.open(os.path.join(out, name)) as b:
                self.assertEqual(a.read(), b.read(), name)
        with open(os.path.join(FIXTURE, 'MANIFEST.json'), 'rb') as a, open(os.path.join(out, 'MANIFEST.json'), 'rb') as b:
            self.assertEqual(a.read(), b.read())
        with open(os.path.join(out, 'areas.csv'), 'rb') as a, gzip.open(os.path.join(out, 'areas.csv.gz')) as b:
            self.assertEqual(a.read(), b.read())
        # gzip -n: no file name, no time stamp
        with open(os.path.join(out, 'KOM.csv.gz'), 'rb') as f:
            head = f.read(10)
        self.assertEqual(head[3], 0)
        self.assertEqual(head[4:8], b'\0\0\0\0')

    def test_export_reimports(self):
        out = os.path.join(self.tmp.name, 'out')
        export_registry(self.db, out)
        db2 = os.path.join(self.tmp.name, 'again.sqlite')
        self.assertEqual(import_registry(out, db2, log=quiet), 750)

    def _copy(self):
        d = os.path.join(self.tmp.name, 'bad')
        shutil.copytree(FIXTURE, d)
        return d

    def test_refuses_wrong_sha(self):
        d = self._copy()
        man = load(os.path.join(d, 'MANIFEST.json'))
        man['sha256']['KOM.csv'] = '0' * 64
        save(man, os.path.join(d, 'MANIFEST.json'))
        with self.assertRaisesRegex(RegistryError, 'SHA-256'):
            import_registry(d, os.path.join(self.tmp.name, 'x.sqlite'), log=quiet)
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, 'x.sqlite')))

    def test_refuses_altered_row(self):
        d = self._copy()
        with gzip.open(os.path.join(d, 'KOM.csv.gz'), 'rt', encoding='utf-8', newline='') as f:
            text = f.read()
        with gzip.open(os.path.join(d, 'KOM.csv.gz'), 'wt', encoding='utf-8', newline='') as f:
            f.write(text.replace('Komo 501,Komo 501', 'Komo 502,Komo 502', 1))
        with self.assertRaisesRegex(RegistryError, 'SHA-256'):
            import_registry(d, os.path.join(self.tmp.name, 'x.sqlite'), log=quiet)

    def test_refuses_wrong_count(self):
        d = self._copy()
        man = load(os.path.join(d, 'MANIFEST.json'))
        man['codes'] = 751
        save(man, os.path.join(d, 'MANIFEST.json'))
        with self.assertRaisesRegex(RegistryError, 'manifest'):
            import_registry(d, os.path.join(self.tmp.name, 'x.sqlite'), log=quiet)

    def test_rerun_is_safe(self):
        self.assertEqual(import_registry(FIXTURE, self.db, log=quiet), 750)
        st = Store(self.db)
        self.assertEqual(st.count(), 750)
        st.close()

    def test_rerun_keeps_issued_codes(self):
        self.assertEqual(self.send('POST', '/v1/codes', {'lat': 11.1984462, 'lng': -15.3814877})[0], 201)
        with self.assertRaisesRegex(RegistryError, 'issued here'):
            import_registry(FIXTURE, self.db, log=quiet)
        self.assertEqual(import_registry(FIXTURE, self.db, force=True, log=quiet), 750)


class Reads(Fresh):

    def test_health_and_info(self):
        s, h = self.get('/v1/health')
        self.assertEqual((s, h['status'], h['country'], h['codes']), (200, 'ok', 'GW', 750))
        self.assertEqual(h['registry_exported'], load(os.path.join(FIXTURE, 'MANIFEST.json'))['exported'])
        s, i = self.get('/v1/info')
        self.assertEqual((s, i['zones'], i['codes'], i['licences']['data']), (200, 39, 750, 'ODbL-1.0'))
        self.assertIn('N-WAYS LIMITED', i['credit'])

    def test_card_has_every_column(self):
        r = fixture_rows()[0]
        s, c = self.get('/v1/codes/' + r['machine'])
        self.assertEqual(s, 200)
        self.assertEqual(c['record'], r)
        self.assertEqual(c['home'], r['home'])
        self.assertEqual(c['written'], r['home'])          # no check digit for people
        self.assertEqual(c['zone']['key'], 'KOM')
        self.assertEqual(c['area']['id'], r['area'])
        self.assertTrue(c['spot'].startswith('94-'))
        self.assertTrue(c['spoken'].startswith(c['area']['plate_name'] + ', '))

    def test_card_errors(self):
        r = fixture_rows()[0]
        bad = r['machine'][:-1] + str((int(r['machine'][-1]) + 1) % 10)
        self.assertError(self.get('/v1/codes/' + bad), 422, 'bad_check')
        self.assertError(self.get('/v1/codes/not-a-code'), 400, 'bad_code')
        self.assertError(self.get('/v1/codes/99-001-00001-0'), 404, 'unknown_sector')
        self.assertError(self.get('/v1/codes/94-099-00001-0'), 404, 'unknown_area')
        unused = 'Komo 590'
        a = self.store.register.by_ref['KOM-000']
        self.assertError(self.get('/v1/codes/' + self.store.register.forms(a, 590)['machine']), 404, 'not_issued')
        self.assertError(self.get('/v1/find', q=unused), 404, 'not_issued')

    def test_find_every_form(self):
        r = fixture_rows()[5]
        for q in (r['home'], r['home'].upper(), '  ' + r['home'].lower().replace(' ', '   ') + ' ', r['machine'],
                  r['machine'].replace('-', ' - '), r['home'] + ', Komo', r['home'] + '-' + r['check']):
            s, out = self.get('/v1/find', q=q)
            self.assertEqual(s, 200, (q, out))
            self.assertEqual(out['matches'][0]['machine'], r['machine'], q)
        spot = ref.encode_spot(float(r['entrance_lat']), float(r['entrance_lng']))
        s, out = self.get('/v1/find', q=spot)
        self.assertEqual((s, out['kind'], out['matches'][0]['machine']), (200, 'spot', r['machine']))

    def test_find_accents_and_aliases(self):
        rows = [r for r in fixture_rows() if r['area'] == 'KOM-022']   # Uncómenè
        r = rows[0]
        s, out = self.get('/v1/find', q='uncomene ' + r['number'])
        self.assertEqual(out['matches'][0]['machine'], r['machine'])
        # an official name typed instead of the plate name ('Sinchã ...' for 'Sinchã' has none here):
        tv = [r for r in fixture_rows() if r['area'] == 'KOM-001'][0]
        s, out = self.get('/v1/find', q=f"{tv['official_name']} {tv['number']}")
        self.assertEqual(out['matches'][0]['machine'], tv['machine'])

    def test_find_errors(self):
        r = fixture_rows()[0]
        self.assertError(self.get('/v1/find', q=r['home'] + '-' + str((int(r['check']) + 1) % 10)), 422, 'bad_check')
        bad = r['machine'][:-1] + str((int(r['machine'][-1]) + 3) % 10)
        self.assertError(self.get('/v1/find', q=bad), 422, 'bad_check')
        self.assertError(self.get('/v1/find', q='Nowhereville 12'), 404, 'unknown_name')
        self.assertError(self.get('/v1/find', q='hello'), 400, 'bad_code')
        self.assertError(self.get('/v1/find'), 400, 'bad_request')
        self.assertError(self.get('/v1/find', q='94-0000-0000'), 404, 'not_found')
        spot = ref.encode_spot(11.19, -15.33)
        self.assertError(self.get('/v1/find', q=spot + '-' + str((ref.damm(spot.replace('-', '')) + 1) % 10)), 422, 'bad_check')

    def test_at(self):
        r = fixture_rows()[10]
        lat, lng = float(r['entrance_lat']), float(r['entrance_lng'])
        s, out = self.get('/v1/at', lat=lat + 0.00003, lng=lng)
        self.assertEqual((s, out['status'], out['code']['machine']), (200, 'found', r['machine']))
        self.assertLessEqual(out['distance_m'], 12)
        s, out = self.get('/v1/at', lat=lat + 0.0003, lng=lng + 0.0003)
        if out['status'] == 'none':
            self.assertEqual(out['zone']['key'], 'KOM')
            self.assertTrue(out['area']['id'].startswith('KOM-'))
        s, out = self.get('/v1/at', lat=11.0, lng=-16.5)
        self.assertEqual(out['status'], 'outside')
        self.assertError(self.get('/v1/at', lat=11.0), 400, 'bad_request')
        self.assertError(self.get('/v1/at', lat='x', lng=1), 400, 'bad_request')
        self.assertError(self.get('/v1/at', lat=95, lng=1), 400, 'bad_request')

    def test_near(self):
        r = fixture_rows()[10]
        lat, lng = float(r['entrance_lat']), float(r['entrance_lng'])
        s, out = self.get('/v1/near', lat=lat, lng=lng, radius=200, limit=5)
        self.assertEqual(s, 200)
        self.assertEqual(out['codes'][0]['machine'], r['machine'])
        self.assertLessEqual(len(out['codes']), 5)
        ds = [c['distance_m'] for c in out['codes']]
        self.assertEqual(ds, sorted(ds))
        self.assertTrue(all(d <= 200 for d in ds))
        self.assertError(self.get('/v1/near', lat=lat, lng=lng, radius=501), 400, 'bad_request')
        self.assertError(self.get('/v1/near', lat=lat, lng=lng, limit=101), 400, 'bad_request')

    def test_verify(self):
        r = fixture_rows()[3]
        s, out = self.get('/v1/verify', code=r['machine'])
        self.assertEqual((out['syntax'], out['check'], out['issued'], out['valid']), (True, True, True, True))
        bad = r['machine'][:-1] + str((int(r['machine'][-1]) + 1) % 10)
        s, out = self.get('/v1/verify', code=bad)
        self.assertEqual((out['syntax'], out['check'], out['valid']), (True, False, False))
        a = self.store.register.by_ref['KOM-000']
        s, out = self.get('/v1/verify', code=self.store.register.forms(a, 590)['machine'])
        self.assertEqual((out['check'], out['issued'], out['valid']), (True, False, False))
        s, out = self.get('/v1/verify', code='Komo 501')
        self.assertFalse(out['syntax'])
        self.assertError(self.get('/v1/verify'), 400, 'bad_request')

    def test_spot(self):
        s, out = self.get('/v1/spot', lat=11.1964, lng=-15.3335)
        self.assertEqual((s, out['zone']['key']), (200, 'KOM'))
        self.assertEqual(out['spot'], ref.encode_spot(11.1964, -15.3335))
        s, back = self.get('/v1/spot/decode', code=out['refined'])
        self.assertLess(abs(back['lat'] - 11.1964) * 110574, out['cell_m'])
        self.assertError(self.get('/v1/spot', lat=11.0, lng=-16.5), 422, 'outside')
        self.assertError(self.get('/v1/spot/decode', code='nonsense'), 400, 'bad_code')
        self.assertError(self.get('/v1/spot/decode', code='99-1234-5678'), 404, 'not_found')

    def test_zones_and_areas(self):
        s, out = self.get('/v1/zones')
        self.assertEqual(len(out['zones']), 39)
        self.assertEqual({z['key']: z['codes'] for z in out['zones']}['KOM'], 750)
        s, z = self.get('/v1/zones/kom')
        self.assertEqual((z['key'], len(z['areas']), z['codes']), ('KOM', 27, 750))
        s, z2 = self.get('/v1/zones/94')
        self.assertEqual(z2['key'], 'KOM')
        self.assertError(self.get('/v1/zones/XXX'), 404, 'not_found')
        s, a = self.get('/v1/areas/KOM-012')
        self.assertEqual((a['plate_name'], a['blocks'], a['codes']['total']), ('Catame', [[50, 59]], 1))
        self.assertError(self.get('/v1/areas/KOM-999'), 404, 'not_found')
        s, f = self.get('/v1/areas', name='catunco')
        self.assertTrue({'KOM-004', 'KOM-005', 'KOM-009'} <= {x['id'] for x in f['areas']})
        s, f = self.get('/v1/areas', name='Praca')                  # typed without the cedilla
        self.assertIn('BIS-026', {x['id'] for x in f['areas']})
        self.assertError(self.get('/v1/areas', name='Nowhereville'), 404, 'not_found')

    def test_paging(self):
        seen, after = [], ''
        while True:
            s, page = self.get('/v1/zones/KOM/codes', after=after, limit=300) if after else self.get('/v1/zones/KOM/codes', limit=300)
            seen += [c['machine'] for c in page['codes']]
            if not page['next']:
                break
            after = page['next']
        self.assertEqual(sorted(seen), sorted(r['machine'] for r in fixture_rows()))
        self.assertEqual(seen, sorted(seen))
        self.assertError(self.get('/v1/zones/KOM/codes', limit=0), 400, 'bad_request')

    def test_unknown_route_and_method(self):
        self.assertError(self.get('/v1/nothing'), 404, 'not_found')
        self.assertError(self.api.handle('DELETE', '/v1/codes/94-000-00501-2', {}, {}, b''), 405, 'method_not_allowed')


class Issuing(Fresh):

    def test_parity_with_the_issuer(self):
        """The issuer's own numbers for the same requests (parity-expected.json)."""
        ops = load(os.path.join(DATA, 'parity-points.json'))['ops']
        want = load(os.path.join(DATA, 'parity-expected.json'))['results']
        self.assertEqual(len(ops), len(want))
        for op, w in zip(ops, want):
            body = {'lat': op['lat'], 'lng': op['lng']}
            if op.get('of'):
                body['of'] = op['of']
            s, c = self.send('POST', '/v1/codes', body)
            self.assertEqual(s, 201, (op, c))
            self.assertEqual((c['machine'], c['home'], c['number'], c['check'], c['area']['id'], c['spoken']),
                             (w['machine'], w['home'], w['number'], w['check'], w['area'], w['spoken']), op)
            self.assertEqual(c['spot'], w['spot'])
            self.assertEqual(c['plus_code'], w['plusCode'])
            self.assertEqual(c['status'], 'provisional')
            self.assertEqual(c['issued'], 'on-demand')
            self.assertEqual(c['entrance']['kind'], 'door' if op.get('of') else 'centre')
            self.assertEqual([list(b) for b in self.store.register.by_ref[w['area']].blocks], [list(b) for b in w['blocks']])
        # continuation blocks persist and are exported
        out = os.path.join(self.tmp.name, 'out')
        export_registry(self.db, out)
        areas = {r['area']: r for r in read_csv(os.path.join(out, 'areas.csv.gz'))}
        self.assertEqual(areas['KOM-012']['blocks'], '50-59|60-109')
        self.assertEqual(areas['KOM-006']['blocks'], '0-9')
        rows = read_csv(os.path.join(out, 'KOM.csv.gz'))
        self.assertEqual(len(rows), 750 + len(ops))
        self.assertEqual(list(rows[0]), CODE_COLUMNS)
        new = {r['machine']: r for r in rows if r['issued'] == 'on-demand'}
        self.assertEqual(set(new), {w['machine'] for w in want})
        man = load(os.path.join(out, 'MANIFEST.json'))
        self.assertEqual(man['codes'], 750 + len(ops))
        # a server restarted on the database sees the new blocks
        again = Store(self.db)
        self.assertEqual(again.register.by_ref['KOM-012'].blocks, [(50, 59), (60, 109)])
        again.close()
        # and the export imports cleanly
        self.assertEqual(import_registry(out, os.path.join(self.tmp.name, 'again.sqlite'), log=quiet), 750 + len(ops))

    def test_engine_insert_matches_issuer_rules(self):
        # a full block takes a continuation block above the name's high-water mark
        issued = [(n, 11.18333 + 0.0001 * n, -15.3) for n in range(50, 60)]
        n, block = ref.insert(94, 11.1835, -15.3, issued, [(50, 59)], 60)
        self.assertEqual((n, block), (61, (60, 109)))
        # an area with no block yet
        self.assertEqual(ref.insert(94, 11.15, -15.25, [], [], 0), (1, (0, 9)))
        # no room left below 100,000
        self.assertEqual(ref.insert(94, 11.15, -15.25, [(n, 11.15, -15.25) for n in range(99990, 100000)], [(99990, 99999)],
                                    100000), (None, None))

    def test_already_has_a_code(self):
        r = fixture_rows()[0]
        lat, lng = float(r['entrance_lat']), float(r['entrance_lng'])
        res = self.send('POST', '/v1/codes', {'lat': lat, 'lng': lng})
        self.assertError(res, 409, 'exists')
        self.assertEqual(res[1]['error']['card']['machine'], r['machine'])
        res = self.send('POST', '/v1/codes', {'lat': lat + 0.00002, 'lng': lng})   # about 2 m away
        self.assertError(res, 409, 'exists')

    def test_outline_rules(self):
        lat, lng = 11.1984462, -15.3814877
        d = 0.00005  # about 5.5 m

        def square(cx, cy, h):
            return [[cx - h, cy - h], [cx + h, cy - h], [cx + h, cy + h], [cx - h, cy + h], [cx - h, cy - h]]
        self.assertError(self.send('POST', '/v1/codes', {'lat': lat, 'lng': lng, 'outline': square(lng, lat, 0.00001)}),
                         422, 'bad_outline')
        self.assertError(self.send('POST', '/v1/codes', {'lat': lat, 'lng': lng, 'outline': square(lng, lat, 0.001)}),
                         422, 'bad_outline')
        s, c = self.send('POST', '/v1/codes', {'lat': lat, 'lng': lng, 'outline': square(lng, lat, d)})
        self.assertEqual(s, 201, c)
        self.assertEqual(c['building']['structures'], 1)
        self.assertAlmostEqual(c['building']['floor_area_m2'], geo.ring_area_m2(geo.ring_open(square(lng, lat, d))), delta=0.1)
        # a point inside that outline, 4 m from the entrance: the building has its code
        self.assertError(self.send('POST', '/v1/codes', {'lat': lat + 0.000036, 'lng': lng + 0.000036}), 409, 'exists')
        # an outline that mostly overlaps it, centred 8 m away
        res = self.send('POST', '/v1/codes', {'lat': lat, 'lng': lng + 0.00008, 'outline': square(lng + 0.00002, lat, d)})
        self.assertError(res, 409, 'exists')
        self.assertEqual(res[1]['error']['card']['machine'], c['machine'])
        # the at endpoint finds the compound from inside its outline
        s, at = self.get('/v1/at', lat=lat + 0.00004, lng=lng - 0.00004)
        self.assertEqual(at['code']['machine'], c['machine'])

    def test_doors(self):
        r = fixture_rows()[0]
        lat, lng = float(r['entrance_lat']), float(r['entrance_lng'])
        self.assertError(self.send('POST', '/v1/codes', {'lat': lat + 0.001, 'lng': lng, 'of': r['machine']}), 422, 'too_far')
        self.assertError(self.send('POST', '/v1/codes', {'lat': lat, 'lng': lng, 'of': '94-000-00999-9'}), 404, 'not_found')
        s, c = self.send('POST', '/v1/codes', {'lat': lat + 0.0002, 'lng': lng, 'of': r['machine']})
        self.assertEqual((s, c['area']['id'], c['entrance']['kind'], c['building']['kind']), (201, r['area'], 'door', 'door'))

    def test_refusals(self):
        self.assertError(self.send('POST', '/v1/codes', {'lat': 11.0, 'lng': -16.5}), 422, 'outside')
        self.assertError(self.send('POST', '/v1/codes', {'lat': 'x', 'lng': 1}), 400, 'bad_request')
        self.assertError(self.send('POST', '/v1/codes', [1, 2]), 400, 'bad_request')
        self.assertError(self.api.handle('POST', '/v1/codes', {}, {'Authorization': 'Bearer ' + KEY}, b'{'), 400, 'bad_request')
        self.assertError(self.send('POST', '/v1/codes', {'lat': 11.19, 'lng': -15.33}, key=None), 401, 'unauthorized')
        self.assertError(self.send('POST', '/v1/codes', {'lat': 11.19, 'lng': -15.33}, key='wrong'), 401, 'unauthorized')
        ro = Api(self.store, [], per_day=5)
        self.assertError(ro.handle('POST', '/v1/codes', {}, {'Authorization': 'Bearer ' + KEY}, b'{}'), 403, 'read_only')

    def test_daily_limit(self):
        api = Api(self.store, [KEY], per_day=2)
        ops = load(os.path.join(DATA, 'parity-points.json'))['ops'][:3]
        res = [api.handle('POST', '/v1/codes', {}, {'Authorization': 'Bearer ' + KEY},
                          json.dumps({'lat': o['lat'], 'lng': o['lng']}).encode()) for o in ops]
        self.assertEqual([r[0] for r in res], [201, 201, 429])
        self.assertEqual(res[2][1]['error']['code'], 'rate_limited')
        self.assertEqual(self.store.issued_since(key_id(KEY), 0), 2)

    def test_patch(self):
        r = fixture_rows()[2]
        m = r['machine']
        s, c = self.send('PATCH', '/v1/codes/' + m, {'status': 'confirmed'})
        self.assertEqual((s, c['status']), (200, 'confirmed'))
        lat, lng = float(r['entrance_lat']), float(r['entrance_lng'])
        self.assertError(self.send('PATCH', '/v1/codes/' + m, {'entrance': {'lat': lat + 0.001, 'lng': lng}}), 422, 'too_far')
        s, c = self.send('PATCH', '/v1/codes/' + m, {'entrance': {'lat': lat + 0.0003, 'lng': lng}})
        self.assertEqual((s, c['entrance']['kind'], c['entrance']['lat']), (200, 'gate', round(lat + 0.0003, 7)))
        self.assertEqual(c['plus_code'], geo.plus_code(lat + 0.0003, lng))
        self.assertError(self.send('PATCH', '/v1/codes/' + m, {'status': 'gone'}), 400, 'bad_request')
        self.assertError(self.send('PATCH', '/v1/codes/' + m, {'colour': 'red'}), 400, 'bad_request')
        s, c = self.send('PATCH', '/v1/codes/' + m, {'status': 'retired'})
        self.assertEqual(c['status'], 'retired')
        self.assertError(self.send('PATCH', '/v1/codes/' + m, {'status': 'confirmed'}), 409, 'retired')
        self.assertError(self.get('/v1/find', q=r['home']), 404, 'retired')
        # a retired number is never given again: the next code in that area skips it
        nums = [n for n, _, _ in self.store.area_numbers(r['area'])]
        self.assertIn(int(r['number']), nums)
        self.assertError(self.send('PATCH', '/v1/codes/' + m, {'status': 'confirmed'}, key=None), 401, 'unauthorized')

    def test_border_decides(self):
        """SPEC 3.1: a point more than 300 m outside the national border is outside Guinea-Bissau,
        whatever the sector outlines say. No sector outline reaches that far beyond the shipped
        border, so a border drawn through Komo stands in for it: its east edge runs 0.01 degrees
        west of a published entrance."""
        rows = fixture_rows()
        r = rows[5]
        lat, lng = float(r['entrance_lat']), float(r['entrance_lng'])
        edge = lng - 0.01
        path = os.path.join(self.tmp.name, 'border.geojson')
        sq = [[edge - 1, lat - 1], [edge, lat - 1], [edge, lat + 1], [edge - 1, lat + 1], [edge - 1, lat - 1]]
        save({'type': 'Feature', 'properties': {'maxDeviationM': 0.0},
              'geometry': {'type': 'Polygon', 'coordinates': [sq]}}, path)
        saved = ref._BORDER
        ref._BORDER = ref.Border(path)
        try:
            far = lng + 0.0003                                   # about 1.1 km beyond that edge
            self.assertIsNotNone(ref.sector_of(lat + 0.0003, far))
            self.assertError(self.send('POST', '/v1/codes', {'lat': lat + 0.0003, 'lng': far}), 422, 'outside')
            self.assertError(self.send('POST', '/v1/codes', {'lat': lat + 0.0002, 'lng': lng, 'of': r['machine']}), 422, 'outside')
            self.assertEqual(self.get('/v1/at', lat=lat, lng=lng)[1]['status'], 'outside')
            self.assertError(self.send('PATCH', '/v1/codes/' + r['machine'], {'entrance': {'lat': lat + 0.0003, 'lng': lng}}),
                             422, 'outside')
            # within 300 m of the border (less the 1 m margin) a point is still in the country
            near = edge + 200 / (ref.M_LON_EQ * ref.math.cos(ref.math.radians(lat)))
            self.assertEqual(ref._BORDER.limit, 299.0)
            self.assertIn(self.get('/v1/at', lat=lat, lng=near)[1]['status'], ('found', 'none'))
            s, c = self.send('POST', '/v1/codes', {'lat': lat, 'lng': near})
            self.assertIn(s, (201, 409), c)
            self.assertEqual(self.get('/v1/at', lat=lat, lng=edge + 320 / (ref.M_LON_EQ * ref.math.cos(ref.math.radians(lat))))[1]['status'],
                             'outside')
        finally:
            ref._BORDER = saved
        # the shipped border holds every published code of the fixture
        self.assertTrue(all(ref.border().holds(float(x['entrance_lat']), float(x['entrance_lng'])) for x in rows))
        self.assertNotEqual(self.get('/v1/at', lat=lat, lng=lng)[1]['status'], 'outside')


class Forms(unittest.TestCase):

    def test_pt_numbers(self):
        for n, want in {1: 'um', 15: 'quinze', 21: 'vinte e um', 100: 'cem', 101: 'cento e um', 275: 'duzentos e setenta e cinco',
                        1000: 'mil', 1001: 'mil e um', 1275: 'mil duzentos e setenta e cinco', 2000: 'dois mil',
                        2100: 'dois mil e cem', 21000: 'vinte e um mil',
                        99999: 'noventa e nove mil novecentos e noventa e nove'}.items():
            self.assertEqual(ref.pt_number(n), want)

    def test_plus_codes_match_the_registry(self):
        for r in fixture_rows():
            self.assertEqual(geo.plus_code(float(r['entrance_lat']), float(r['entrance_lng'])), r['plus_code'], r['machine'])

    def test_forms_match_the_registry(self):
        tmp = tempfile.TemporaryDirectory()
        try:
            db = os.path.join(tmp.name, 'a.sqlite')
            import_registry(FIXTURE, db, log=quiet)
            st = Store(db)
            reg = st.register
            st.close()
            for r in fixture_rows():
                f = reg.forms(reg.by_ref[r['area']], int(r['number']))
                self.assertEqual((f['machine'], f['home'], f['written'], str(f['check'])),
                                 (r['machine'], r['home'], r['written'], r['check']))
        finally:
            tmp.cleanup()


class Http(unittest.TestCase):
    """The HTTP layer: JSON bodies, status codes, CORS, body limit."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        db = os.path.join(cls.tmp.name, 'a.sqlite')
        import_registry(FIXTURE, db, log=quiet)
        cls.store = Store(db)
        api = Api(cls.store, [KEY], per_day=10)
        handler = make_handler(api, ['https://ministry.example'])
        handler.log_message = lambda *a: None
        cls.httpd = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.store.close()
        cls.tmp.cleanup()

    def req(self, method, path, body=None, headers=None):
        c = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        c.request(method, path, body=body, headers=headers or {})
        r = c.getresponse()
        data = r.read()
        c.close()
        return r, data

    def test_json_and_cors(self):
        r, data = self.req('GET', '/v1/health', headers={'Origin': 'https://ministry.example'})
        self.assertEqual(r.status, 200)
        self.assertEqual(r.getheader('Content-Type'), 'application/json; charset=utf-8')
        self.assertEqual(r.getheader('Access-Control-Allow-Origin'), 'https://ministry.example')
        self.assertEqual(json.loads(data)['country'], 'GW')
        r, _ = self.req('GET', '/v1/health', headers={'Origin': 'https://elsewhere.example'})
        self.assertIsNone(r.getheader('Access-Control-Allow-Origin'))
        r, _ = self.req('OPTIONS', '/v1/codes', headers={'Origin': 'https://ministry.example'})
        self.assertEqual(r.status, 204)
        self.assertIn('PATCH', r.getheader('Access-Control-Allow-Methods'))

    def test_errors_are_json(self):
        r, data = self.req('GET', '/v1/codes/94-000-00501-3')
        self.assertEqual(r.status, 422)
        self.assertEqual(json.loads(data)['error']['code'], 'bad_check')
        r, data = self.req('POST', '/v1/codes', body=b'x' * 70000, headers={'Content-Type': 'application/json'})
        self.assertEqual((r.status, json.loads(data)['error']['code']), (413, 'too_large'))
        r, data = self.req('GET', '/v1/find?q=' + 'Komo%20501')
        self.assertEqual(json.loads(data)['matches'][0]['machine'], '94-000-00501-2')
        for method in ('PUT', 'DELETE'):
            r, data = self.req(method, '/v1/codes/94-000-00501-2', headers={'Authorization': 'Bearer ' + KEY})
            self.assertEqual((r.status, json.loads(data)['error']['code']), (405, 'method_not_allowed'))
        r, data = self.req('POST', '/v1/codes', headers={'Content-Length': 'many'})
        self.assertEqual((r.status, json.loads(data)['error']['code']), (400, 'bad_request'))

    def test_issue_over_http(self):
        body = json.dumps({'lat': 11.1527644, 'lng': -15.3161732}).encode()
        r, data = self.req('POST', '/v1/codes', body=body, headers={'Authorization': 'Bearer ' + KEY,
                                                                   'Content-Type': 'application/json'})
        self.assertEqual(r.status, 201, data)
        self.assertEqual(json.loads(data)['status'], 'provisional')


if __name__ == '__main__':
    unittest.main()
