#!/usr/bin/env python3
"""Plate names for Guinea-Bissau's place words (docs/model.md 5.4, engine/SPEC.md 5.1.2).

Every place keeps its official name (the full name from OpenStreetMap or GeoNames,
`officialName`) and gets a plate name (`word`): at most 12 characters and 2 words, the
name in the remembered code ("Bandim 275"). The rule is engine/reference/plate_names.py;
this file configures it for Guinea-Bissau:

  * language 'pt': the names are Portuguese and Kriol, with Fula, Mandinka, Balanta,
    Beafada and Bijagó spellings;
  * generic words dropped: the shared Portuguese list (Bairro, Zona, Lote ...) and a
    leading "Tabanca" when the rest is a real name ("Tabanca Bijagos" -> "Bijagos";
    "Tabanca Nova" stays);
  * settlement heads (part of the name, the first to go when it is too long, never a
    plate name alone): Sinchã/Sintchã (Fula "founded by"), Sare (Fula "village of"),
    Madina, Gã (Beafada "place of"), Ponta and its abbreviation "P." (a farm concession
    named after its holder), Barraca, Ilha, Ilhéu;
  * qualifiers (never a plate name alone; a short form that drops one goes to the
    council): the people a tabanca is named after (Balanta, Mancanha, Papel, Fula,
    Mandinga, Beafada, Nalu, Bijagó ...), as in Bambadinca Balanta / Bambadinca Mancanha;
  * country rule: a short form that keeps only the founder's personal name after
    dropping a settlement head ("Sinchã Mamadu" -> "Mamadu") goes to the council, because
    a given name alone is not a place people say;
  * avoid: the 38 sector seats, the 8 region capitals and the big towns across the
    borders that people in Guinea-Bissau know by name (Ziguinchor, Kolda, Conakry, Boké ...);
    the area's own sector seat is allowed (a bairro of Gabú may be called Gabú);
  * known: documented short forms only (none is asserted today).

  python3 tools/gw_plates.py        recompute the plate fields of model/places.json
"""
import collections, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, 'engine', 'reference'))
import gw_codes  # noqa: E402
import plate_names as pn  # noqa: E402

LANG = 'pt'
FOUNDER_HEADS = {'sinchã', 'sintchã', 'sincha', 'sintcham', 'sare', 'saré', 'madina', 'gã', 'p.', 'ponta', 'ponto'}
HEADS_GW = FOUNDER_HEADS | {'barraca', 'ilha', 'ilhéu', 'ilhéus', 'ilheu', 'ponte'}
QUALIFIERS = {'balanta', 'balantas', 'mancanha', 'mancanhas', 'papel', 'pepel', 'fula', 'fulas', 'futa', 'futa-fula',
              'mandinga', 'mandinka', 'beafada', 'biafada', 'nalu', 'nalus', 'manjaco', 'manjacos', 'felupe', 'bijagó',
              'bijago', 'bijagós', 'oinca', 'saracolé', 'jacanca', 'djacanca', 'cassanga', 'banhum', 'baiote', 'sosso',
              'mansonca', 'padjadinca', 'tanda', 'bambara',
              # a generic word is never a plate name alone ("Bairro Balanta" never becomes "Bairro")
              'bairro', 'zona', 'tabanca', 'tabanka', 'aldeia', 'povoação',
              # a number word alone is not a name: "Zona Sete" stays whole
              'um', 'dois', 'três', 'tres', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove', 'dez'}
GENERIC_EXTRA = ['phase']   # "Bairro Ajuda II Phase" -> "Ajuda II": the numeral already says the phase
# Looked at by eye: automatic choices that the Câmara or the community decides instead.
# {official name: (reason, [candidates] or None for the derived ones)}
FLAG = {
    'Bairro Militar': ('dropping "Bairro" leaves an adjective alone', None),
    'Granja-Pessube': ('a hyphenated name over the limit: either part could be the plate name', ['Pessube', 'Granja']),
    'Arranja a Vida de Cima': ('a phrase name: no part of it is a name on its own', None),
    'Centro da Cidade': ('the centre of Bolama town (sector 31): the town\'s own name or "Centro"', ['Bolama', 'Centro']),
    'Ponte de Lima': ('the short form "Lima" is a well-known city elsewhere', None),
    'Formoso Curto': ('the short form "Curto" is an adjective alone', ['Formoso', 'Curto']),
    'Gadamael Fronteira': ('the short form "Fronteira" drops the name of the place', ['Gadamael', 'Fronteira']),
    'Ponta Nova de Sajà': ('a short form would keep a qualifier and drop the head of the name', ['Sajà']),
}
pn.HEADS[LANG] |= HEADS_GW   # this country's settlement heads (see the docstring)
# Documented short forms: {official name: (plate name, source)}. None is asserted yet: the
# Câmara Municipal's bairro list (docs/model.md 12) is the expected source.
KNOWN = {}
REGION_CAPITALS = ['Bafatá', 'Bolama', 'Quinhamel', 'Cacheu', 'Gabú', 'Farim', 'Buba', 'Catió', 'Bissau']
# Towns across the borders, and the capitals of the region, that people here know by name: a
# plate name equal to one would send a listener to the wrong country.
REGION_CITIES = ['Dakar', 'Ziguinchor', 'Kolda', 'Tambacounda', 'Banjul', 'Conakry', 'Boké', 'Labé', 'Praia',
                 'Mindelo', 'Bamako', 'Nouakchott', 'Lisboa', 'Madina do Boé']


def seat(sector):
    return gw_codes.sectors()[sector]['name'].split(' (')[0]


def avoid_for(sector):
    own = {gw_codes.name_key(seat(sector))}
    if sector == 61:
        own.add(gw_codes.name_key('Madina do Boé'))
    allt = [seat(n) for n in gw_codes.sectors()] + REGION_CAPITALS + REGION_CITIES
    return [a for a in allt if gw_codes.name_key(a) not in own]


def pre_clean(official):
    """What make-places.py already did before plate names existed: 'Bairro de Ajuda' ->
    'Ajuda', 'Morança Atufa' -> 'Atufa', plus a leading 'Tabanca' before a real name."""
    s = re.sub(r'\s+', ' ', official).strip()
    s = re.sub(r'^(Tabanca|Tabanka|Bairro|Aldeia|Povoação)\s+(de|da|do|dos|das)\s+', '', s, flags=re.I)
    s = re.sub(r'^(Morança|Moransa|Moranza)\s+(de\s+|da\s+|do\s+)?', '', s, flags=re.I)
    m = re.match(r'^(Tabanca|Tabanka)\s+(.+)$', s, flags=re.I)
    if m and pn._strong(m.group(2).split(' (')[0], LANG, QUALIFIERS):
        s = m.group(2)
    return s


def derive(official, sector, freq):
    pre = pre_clean(official)
    r = pn.derive(pre, LANG, freq, known=KNOWN, avoid=avoid_for(sector), generic_extra=GENERIC_EXTRA,
                  weak_extra=QUALIFIERS, avoid_key=gw_codes.name_key)
    if pre != official and r['rule'] == 'as-is':
        r['rule'] = 'cleaned'
    r['official'] = official
    # country rules for an automatic short form (docstring)
    founders = {pn.plain(h) for h in FOUNDER_HEADS}
    cl = pn.clean(pre, LANG, GENERIC_EXTRA, QUALIFIERS)[0]
    words = [pn.plain(w) for w in pn.content_words(cl, LANG)]
    pw = [pn.plain(w) for w in pn.content_words(r['plate'], LANG)]
    why = None
    if re.search(r'\d', official):
        why = 'a number in the name (a plate name has no digits)'
    elif r['rule'] == 'distinctive':
        if pw and words and pw[-1] != words[-1]:
            why = 'the short form drops the end of the name, which tells this place from others'
        elif len(pw) == 1 and words[0] in founders:
            why = 'only the founder\'s given name is left after dropping the settlement word'
        elif re.search(r'\w\s+e\s+\w', cl):
            why = 'two names joined by "e"'
    if official in FLAG:
        why, cands = FLAG[official]
        if cands:
            r['candidates'] = cands
            r['plate'] = cands[0]
    if why:
        r.update(rule='council', needsCouncilChoice=True, reason=why)
    if r['needsCouncilChoice'] and not r['candidates'] and pn.fits(r['plate'], LANG):
        r['candidates'] = [r['plate']]
    return r


def apply(table):
    """Set word (plate name), officialName and the plate fields on every place record; add
    the official name as an alias where it points to one plate name only."""
    for t in table:
        t.setdefault('officialName', t.get('name') or t['word'])
    freq = pn.word_freq([pre_clean(t['officialName']) for t in table], LANG)
    earlier = {id(t): t.pop('aliasesDropped', []) for t in table}  # a rerun starts from every name it had
    for t in table:
        r = derive(t['officialName'], t['sector'], freq)
        t['word'] = r['plate']
        t['name'] = r['plate']
        t['plateRule'] = r['rule']
        for k in ('needsCouncilChoice', 'plateCandidates', 'plateReason', 'plateSource', 'plateOverLimit'):
            t.pop(k, None)
        if r.get('source'):
            t['plateSource'] = r['source']
        if r['needsCouncilChoice']:
            t['needsCouncilChoice'] = True
            t['plateCandidates'] = r['candidates'][:3]
            t['plateReason'] = r['reason']
        if not pn.fits(t['word'], LANG):
            t['plateOverLimit'] = True
    # aliases: the official name and the source's other names, unless one would point to two plate names
    plate_keys = {gw_codes.name_key(t['word']) for t in table} | {gw_codes.name_key(seat(n)) for n in gw_codes.sectors()}
    claims = collections.defaultdict(set)
    for t in table:
        for a in [t['officialName']] + t.get('aliases', []) + earlier[id(t)]:
            claims[gw_codes.name_key(a)].add(gw_codes.name_key(t['word']))
    for t in table:
        own = gw_codes.name_key(t['word'])
        keep, drop = [], []
        for a in dict.fromkeys([t['officialName']] + t.get('aliases', []) + earlier[id(t)]):
            k = gw_codes.name_key(a)
            if k == own:
                if a != t['word']:
                    keep.append(a)  # a spelling of the plate name itself
                continue
            if len(claims[k]) > 1 or k in plate_keys:
                drop.append(a)
            else:
                keep.append(a)
        t['aliases'] = keep
        if drop:
            t['aliasesDropped'] = drop
    return table


def main():
    p = os.path.join(REPO, 'model', 'places.json')
    meta = json.load(open(p))
    apply(meta['places'])
    # name keys follow the plate names (as tools/make-places.py writes them)
    shared = collections.Counter(gw_codes.name_key(t['word']) for t in meta['places'])
    shared.update(gw_codes.name_key(seat(n)) for n in gw_codes.sectors())
    for t in meta['places']:
        t.pop('nameKey', None)
        t.pop('areasWithThisName', None)
        t['nameKey'] = gw_codes.name_key(t['word'])
        t['areasWithThisName'] = shared[t['nameKey']]
    json.dump(meta, open(p, 'w'), ensure_ascii=False, indent=0)
    print(summary(meta['places']))


def summary(table):
    c = collections.Counter(t['plateRule'] for t in table)
    return {'places': len(table), 'rules': dict(c), 'needsCouncilChoice': sum(1 for t in table if t.get('needsCouncilChoice')),
            'overLimit': sum(1 for t in table if t.get('plateOverLimit'))}


if __name__ == '__main__':
    main()
