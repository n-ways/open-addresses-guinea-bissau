#!/usr/bin/env python3
"""Test vectors for every port of the engine: engine/reference/vectors.json.

Computed by the reference engine (engine/reference/gw_codes.py) on the frozen register;
every other implementation of the engine, the N-Ways issuer's included, must reproduce them
value for value.

  python3 tools/vectors.py
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, 'engine', 'reference'))
import gw_codes as gw  # noqa: E402


def main():
    rnd = random.Random(245)
    pl = list(gw.places().values())
    words = sorted({t['word'] for t in pl} | {a for t in pl for a in t.get('aliases', [])} | {t.get('officialName') or t['word'] for t in pl})
    tricky = ['Sintchã Dulo', 'Sinchã Duló', 'Sincha Dulu', 'Plack II', 'Plaque 2', 'Plaque', 'Áfià', 'Hafia', 'Bairro de Ajuda', 'Santa-Luzia',
              'Sto António', 'Santo António', 'S. Miguel', 'São Miguel', 'N. Sra da Luz', 'Nossa Senhora da Luz', 'Bissorã', 'Quinhamel', 'Kinhamel',
              'Morança Atufa', 'Tabanca de Bandim', 'Pitche', 'Pitchi', 'Bissoro', 'Çafal']
    keys = [[w, gw.name_key(w)] for w in tricky + rnd.sample(words, 400)]
    reg = json.load(open(os.path.join(REPO, 'engine', 'data', 'register.json')))
    areas = [a for a in reg['areas'] if a['blocks']]   # an area with no home yet has no block
    forms, found = [], []
    for a in rnd.sample(areas, 300):
        lo, hi = a['blocks'][0]
        n = rnd.randint(max(1, lo), hi)
        s, i = a['sector'], a['index']
        forms.append({'sector': s, 'index': i, 'number': n, 'check': gw.check_digit(a['family'], n),
                      'remembered': gw.remembered(a['word'], n), 'written': gw.checked(s, i, n), 'machine': gw.machine(s, i, n)})
        for text in (gw.remembered(a['word'], n), gw.checked(s, i, n)):
            try:
                r = gw.from_remembered(text)
                found.append({'text': text, 'machine': r['machine']})
            except ValueError as e:
                found.append({'text': text, 'error': str(e)})
    # official names and aliases typed with a number
    for a in rnd.sample([a for a in areas if a['aliases']], min(60, sum(1 for a in areas if a['aliases']))):
        n = a['blocks'][0][0] + 1
        text = f"{a['aliases'][0]} {n}"
        try:
            found.append({'text': text, 'machine': gw.from_remembered(text)['machine']})
        except ValueError as e:
            found.append({'text': text, 'error': str(e)})
    spots = []
    secs = gw.sectors()
    for _ in range(300):
        s = rnd.choice(sorted(secs))
        x0, y0, x1, y1 = secs[s]['box']
        lat, lon = rnd.uniform(y0, y1), rnd.uniform(x0, x1)
        if gw.sector_of(lat, lon) is None:
            continue
        code = gw.encode_spot(lat, lon)
        refined = gw.encode_spot(lat, lon, refine=True)
        d = gw.decode_spot(refined)
        spots.append({'lat': lat, 'lon': lon, 'sector': gw.sector_of(lat, lon), 'code': code, 'refined': refined,
                      'decoded': [d['lat'], d['lon']], 'cell': list(gw.grid_cell(gw.sector_of(lat, lon), lat, lon)),
                      'hilbert': gw.hilbert(*gw.grid_cell(gw.sector_of(lat, lon), lat, lon))})
    # numbering and insertion in a toy area
    s = 75
    lat0, lon0 = 12.040, -15.525
    comps = [{'id': f'c{k:02d}', 'lat': lat0 + rnd.uniform(0, 0.004), 'lon': lon0 + rnd.uniform(0, 0.004)} for k in range(14)]
    nums = gw.number_place(s, comps, 2000)
    issued = [(nums[c['id']], c['lat'], c['lon']) for c in comps]
    inserts = []
    for _ in range(40):
        lat, lon = lat0 + rnd.uniform(-0.001, 0.005), lon0 + rnd.uniform(-0.001, 0.005)
        n, why = gw.reserve_number(s, lat, lon, issued, (2000, 2099))
        inserts.append({'lat': lat, 'lon': lon, 'number': n, 'why': why})
    out = {'note': 'Computed by engine/reference/gw_codes.py on engine/data/register.json; every port must match.',
           'nameKeys': keys, 'forms': forms, 'found': found, 'spots': spots,
           'numbering': {'sector': s, 'from': 2000, 'compounds': comps, 'numbers': nums, 'block': [2000, 2099], 'inserts': inserts}}
    json.dump(out, open(os.path.join(REPO, 'engine', 'reference', 'vectors.json'), 'w'), ensure_ascii=False, indent=0)
    print(len(keys), 'name keys,', len(forms), 'forms,', len(found), 'decodings,', len(spots), 'spots,', len(inserts), 'inserts')


if __name__ == '__main__':
    main()
