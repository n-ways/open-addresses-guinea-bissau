#!/usr/bin/env python3
"""Tests for the Guinea-Bissau reference engine: python3 -m unittest engine/reference/test_gw.py
(or python3 engine/reference/test_gw.py). Standard library only."""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gw_codes as g  # noqa: E402


class SelfTest(unittest.TestCase):
    def test_selftest(self):
        g.selftest()


class NationalNames(unittest.TestCase):
    """The remembered form alone is unique in the whole country."""

    def test_same_name_two_areas(self):
        a, b = g.from_remembered('Bandim 275'), g.from_remembered('Bandim 2001')
        self.assertEqual((a['sector'], a['place']), (10, 22))   # Bissau bairro
        self.assertEqual((b['sector'], b['place']), (93, 5))    # tabanca in Catió
        self.assertNotEqual(a['machine'], b['machine'])

    def test_same_name_same_sector(self):
        # two Plaque areas in Quinhamel (42): one name, two blocks, no Roman numeral invented
        x = g.ranges()[g.name_key('Plaque')]
        areas = {(bl['sector'], bl['index']) for bl in x['blocks']}
        self.assertTrue({(42, 42), (42, 39)} <= areas)
        lo = [bl for bl in x['blocks'] if (bl['sector'], bl['index']) == (42, 39)][0]['from']
        self.assertEqual(g.from_remembered(f'Plaque {lo + 1}')['place'], 39)
        self.assertEqual(g.from_remembered('Plaque 1')['place'], 42)

    def test_every_number_one_area(self):
        for rec in g.ranges().values():
            spans = sorted((bl['from'], bl['to']) for bl in rec['blocks'])
            for (a0, a1), (b0, b1) in zip(spans, spans[1:]):
                self.assertLess(a1, b0, rec['key'])
            for a0, a1 in spans:
                self.assertLessEqual(a1, g.MAX_NUMBER)

    def test_check_digit_binds_area(self):
        # 'Missira 15' (Bissau) mistyped as 'Missira 5015' would be Sonaco's block: refused
        c = g.check_digit(g.name_id(g.name_key('Missira')), 15)
        self.assertEqual(g.block_of(g.name_key('Missira'), 5015), (65, 73))
        with self.assertRaises(ValueError):
            g.from_remembered(f'Missira 5015-{c}')
        # a machine form moved to another area of the same name fails the block check
        with self.assertRaises(ValueError):
            g.parse('65-073-00015-' + str(c))

    def test_spelling_variants(self):
        self.assertEqual(g.from_remembered('Hafia 15701')['machine'], g.from_remembered('Áfià 15701')['machine'])
        self.assertEqual(g.name_key('Quelêle'), g.name_key('Quelele'))
        self.assertEqual(g.name_key('Bissorã'), g.name_key('Bissora'))

    def test_cedilla_left_out(self):
        # phone keyboards often drop the cedilla: 'Praca' must still find 'Praça'
        self.assertEqual(g.from_remembered('praca 1')['machine'], g.from_remembered('Praça 1')['machine'])
        self.assertEqual(g.from_remembered('Sincha Icaga 1')['word'], g.from_remembered('Sinchã Içaga 1')['word'])
        self.assertEqual(g.plate_key('Cacheu'), g.name_key('Cacheu'))   # a real c is untouched

    def test_spare_number_refused(self):
        with self.assertRaises(ValueError):
            g.from_remembered('Bandim 2275')


class PlateNames(unittest.TestCase):
    """The word in the code is a plate name: <= 12 characters and <= 2 words."""

    def test_long_official_name(self):
        a = g.from_remembered('Malam Baio 1')
        self.assertEqual((a['sector'], a['place']), (24, 148))
        self.assertEqual(g.places()[(24, 148)]['officialName'], 'Sinchã Malam Baio')
        self.assertEqual(g.from_remembered('Sinchã Malam Baio 1')['machine'], a['machine'])

    def test_collision_after_shortening(self):
        a, b = g.from_remembered('Ama Seidi 1'), g.from_remembered('Ama Sidi 1001')
        self.assertEqual((a['sector'], a['place']), (62, 153))   # Ama Seidi, Gabú
        self.assertEqual((b['sector'], b['place']), (72, 175))   # Missirá Ama Sidi, Farim
        self.assertEqual(g.from_remembered('Missirá Ama Sidi 1001')['machine'], b['machine'])

    def test_every_issued_plate_fits(self):
        for (s, i), t in g.places().items():
            if g.blocks_of_area(g.name_key(t['word']), s, i) and not t.get('needsCouncilChoice'):
                self.assertTrue(g.plate_names.fits(t['word'], g.LANG), t['word'])

    def test_over_limit_refused(self):
        with self.assertRaises(ValueError):
            g.check_plate('Sinchã Malam Baio')
        with self.assertRaises(ValueError):
            g.allocate([{'key': 'x', 'word': 'Ponta Manuel das Águas', 'sector': 21, 'index': 1, 'compounds': 3}])

    def test_flagged_areas_have_candidates(self):
        for t in g.places().values():
            if t.get('needsCouncilChoice'):
                self.assertLessEqual(len(t['plateCandidates']), 3)
                self.assertTrue(t['plateReason'])


class NewCompounds(unittest.TestCase):
    """The place rule and the number of a new compound (SPEC 5.1, 7.2)."""

    def test_island_and_mainland(self):
        self.assertEqual(g.island_of(11.2990, -15.8277), 'Ilha Bubaque')
        self.assertEqual(g.island_of(12.2830, -14.2230), '')
        self.assertTrue(g.same_land('Ilha de Bissau', ''))
        self.assertFalse(g.same_land('Ilha Bubaque', ''))

    def test_place_stays_on_its_island(self):
        p = g.place_for(11.2990, -15.8277)
        self.assertEqual(p['landmass'], 'Ilha Bubaque')
        # a point at sea far from every place takes the sector's own word
        self.assertEqual(g.place_for(11.2990, -15.8277, candidates=[])['index'], 0)

    def test_insert_fills_then_continues(self):
        issued = [(n, 12.04 + 0.0001 * n, -15.52) for n in range(50, 60)]
        self.assertEqual(g.insert(75, 12.0455, -15.52, issued[:5], [(50, 59)], 60), (55, None))
        self.assertEqual(g.insert(75, 12.0455, -15.52, issued, [(50, 59)], 60), (61, (60, 109)))
        self.assertEqual(g.insert(75, 12.0455, -15.52, [], [], 0), (1, (0, 9)))
        self.assertEqual(g.insert(75, 12.0455, -15.52, issued, [(50, 59)], 99990), (None, None))

    def test_numbers_read_aloud(self):
        for n, said in ((1, 'um'), (100, 'cem'), (275, 'duzentos e setenta e cinco'), (1001, 'mil e um'),
                        (2100, 'dois mil e cem'), (99999, 'noventa e nove mil novecentos e noventa e nove')):
            self.assertEqual(g.pt_number(n), said)
        self.assertEqual(g.spoken('Bandim', 537), 'Bandim, quinhentos e trinta e sete')


class TheBorderDecides(unittest.TestCase):
    """SPEC 3.1: no code more than 300 m outside the national border."""

    def test_shipped_border(self):
        b = g.border()
        props = g._load(g.BORDER_FILE)['properties']
        self.assertLess(os.path.getsize(g.BORDER_FILE), 1_000_000)
        self.assertEqual(props['borderM'], g.BORDER_M)
        # the limit applied is 300 m less the simplification's largest deviation, rounded up, less 1 m
        self.assertEqual(b.limit, g.BORDER_M - __import__('math').ceil(props['maxDeviationM']) - 1)
        self.assertLess(b.limit, g.BORDER_M - props['maxDeviationM'])
        self.assertTrue(b.holds(11.8636, -15.5977))      # Bissau
        self.assertTrue(b.holds(11.2990, -15.8277))      # Bubaque, an island
        self.assertTrue(b.holds(12.2830, -14.2230))      # inland, Bafatá
        self.assertFalse(b.holds(12.5833, -16.2719))     # Ziguinchor, in a neighbouring country
        self.assertFalse(b.holds(11.3167, -13.9667))     # in a neighbouring country, south-east

    def test_distance_outside(self):
        import json, math, tempfile
        sq = [[-15.0, 12.0], [-14.0, 12.0], [-14.0, 13.0], [-15.0, 13.0], [-15.0, 12.0]]
        with tempfile.NamedTemporaryFile('w', suffix='.geojson', delete=False) as f:
            json.dump({'type': 'Feature', 'properties': {'maxDeviationM': 0.0},
                       'geometry': {'type': 'Polygon', 'coordinates': [sq]}}, f)
        try:
            b = g.Border(f.name)
        finally:
            os.unlink(f.name)
        self.assertEqual(b.limit, 299.0)
        self.assertEqual(b.outside_m(12.5, -14.5), 0.0)
        m = 0.002 * g.M_LON_EQ * math.cos(math.radians(12.5))   # 0.002 degrees east of the edge
        self.assertAlmostEqual(b.outside_m(12.5, -13.998), m, places=6)
        self.assertTrue(b.holds(12.5, -13.998))
        self.assertFalse(b.holds(12.5, -13.997))
        self.assertTrue(b.holds(13.0 + 250 / g.M_LAT, -14.5))
        self.assertFalse(b.holds(13.0 + 310 / g.M_LAT, -14.5))
        self.assertEqual(b.outside_m(14.0, -14.5), math.inf)


if __name__ == '__main__':
    unittest.main()
