# Guinea-Bissau addressing engine: specification

Version 1.0 (20 October 2026, first issue: 241,673 codes, one for every compound in the 39 sectors). This SPEC is normative: where `reference/gw_codes.py` and this document disagree, this document wins and the script has a bug. The N-Ways issuer's implementation reproduces `reference/vectors.json` value for value, and the registry server in [`../server/`](../server/) uses the reference implementation itself. The engine depends on no library outside the Python standard library. The reference implementation is [`reference/gw_codes.py`](reference/gw_codes.py) (Python standard library only); every rule below is implemented there and covered by its test vectors and by [`reference/test_gw.py`](reference/test_gw.py).

Why each choice was made is argued in [`../docs/model.md`](../docs/model.md). This file says exactly what the engine does.

## 1. What the engine handles

| Thing | Remembered form | Machine form | Made by |
|---|---|---|---|
| Compound (morança, quintal, walled plot, institution) | `Bandim 275` | `10-022-00275-8` | the registry (assigned once) |
| Structure inside a compound | `Bandim 275.2` | `10-022-00275.2-3` | the registry |
| Gate or door of a compound | "portão 1" | `10-022-00275-8/1` | people confirming it |
| Any point (spot) | (shared as a link) | `10-4327-8173`, refined `10-4327-8173.1` | computed on the phone, offline |

The remembered form and the machine form map 1:1, and the **remembered form alone is unique nationally**: all areas whose word has the same name key share one national number range, cut into frozen blocks (5.2), so `Bandim 275` (Bissau) and `Bandim 2001` (Catió) need no town, sector or position to be told apart. People remember and say the place word and the number. The place word is the area's **plate name**, at most 12 characters and 2 words (5.1.2); the full official name is printed small for context and is never needed. The written form is the remembered form as printed on plates and in shares, with no check digit: the check digit is for systems only, and people never see or type it. The machine form adds the sector, the place index and the check digit for forms, partner systems, links and the QR code on a plate.

## 2. Data files the engine ships

| File | What | Size | Changes |
|---|---|---|---|
| `model/sectors.json` | the 39 sectors (38 sectors + Setor Autónomo de Bissau): number, key, names, region, spot-grid frame | 12 KB | frozen at the first issue (20 October 2026) |
| `engine/data/sectors.geojson` | the sector outlines, simplified (Douglas-Peucker 0.0001°, about 11 m), 5-decimal coordinates | 405 KB | frozen with the sector table |
| `engine/data/border.geojson` | the national border (3.1): OpenStreetMap's admin_level=2 boundary of Guinea-Bissau, simplified (Douglas-Peucker 50 m), 5-decimal coordinates, with its largest deviation from the true line (`maxDeviationM`) and the limit applied (`limitM`) | 16 KB | rebuilt by `tools/build_border.py` when OpenStreetMap corrects the border |
| `model/places.json` | the place words: bairros of Bissau, towns, tabancas; sector, index, plate name (`word`), official name, plate rule and council flag, name key, aliases, point, land mass | about 1 MB | new places and aliases appended; existing entries never change index |
| `model/name-ranges.json` | per name key: the national name number (id), the words that share it, and its blocks (sector, place index, from, to, compounds at issue) | about 0.55 MB (under 0.1 MB compressed) | new names and blocks appended; an issued block never changes |
| `registry/` | every issued code: one gzip CSV per sector, one row per compound (section 7), the frozen area table `areas.csv` and `MANIFEST.json` | 7.6 MB compressed (51 MB as text) for the whole country, 1.3 MB compressed for Bissau | append-only |

Offline, a phone holds the first four files (about 1.9 MB, under 0.5 MB compressed) plus the registry slice for the sectors it uses (Bissau about 4 MB compressed to under 1 MB). With them it can make a spot code anywhere, find a place word, look up a compound from its remembered or machine form, and check any typed code, with no network.

## 3. Sectors

Codes hang off the 38 sectors (setores) and the Setor Autónomo de Bissau, from the OpenStreetMap administrative boundaries (admin_level 6 and 3), Geofabrik extract of 2026-10-17.

**Sector number** `SS` (two digits): first digit = region, second = sector inside the region in alphabetical order.

| Region digit | Region | Sectors |
|---|---|---|
| 1 | Setor Autónomo de Bissau | 10 Bissau (11-19 reserved for a future split of Bissau) |
| 2 | Bafatá | 21 Bafatá, 22 Bambadinca, 23 Contuboel, 24 Galomaro, 25 Gã-Mamudo, 26 Xitole |
| 3 | Bolama (Bijagós) | 31 Bolama, 32 Bubaque, 33 Caravela, 34 Uno |
| 4 | Biombo | 41 Prábis, 42 Quinhamel, 43 Safim |
| 5 | Cacheu | 51 Bigene, 52 Bula, 53 Cacheu, 54 Caió, 55 Canchungo, 56 São Domingos |
| 6 | Gabú | 61 Boé (Madina do Boé), 62 Gabú, 63 Pirada, 64 Pitche, 65 Sonaco |
| 7 | Oio | 71 Bissorã, 72 Farim, 73 Mansabá, 74 Mansoa, 75 Nhacra |
| 8 | Quinara | 81 Buba, 82 Empada, 83 Fulacunda, 84 Tite |
| 9 | Tombali | 91 Bedanda, 92 Cacine, 93 Catió, 94 Komo, 95 Quebo |

Each sector also has a three-letter key (`BIS`, `GAB`, `BBQ`...) used only as a label on screens and plates; it is not part of any code.

**Lookup** (`sector_of`): point-in-polygon (even-odd ray casting) against the shipped outlines, after a bounding-box test. A point in no sector (sea, abroad) has no sector and gets no spot code. The shipped outline is the definition: if OpenStreetMap or the government later moves a boundary, issued codes do not move (a new outline table would be published under a new SPEC version, and codes keep the sector they were issued in).

### 3.1 The border decides

A code is only ever issued for a building whose entrance lies inside the national border of Guinea-Bissau, OpenStreetMap's admin_level=2 boundary (`ISO3166-1=GW`), or within 300 m of it (`BORDER_M`). A point further out is in a neighbouring country and is outside Guinea-Bissau, whatever the sector rule above gives: sector outlines, and outlines from other sources (geoBoundaries, GADM and the like), may spill over the border, and they never decide.

The border ships as `engine/data/border.geojson`, made by `tools/build_border.py` from the OpenStreetMap relation: its ways joined into rings and simplified by Douglas-Peucker at 50 m, coordinates to 1e-5 degrees (16 KB). Distances to it are measured on the plane of the point's latitude, as everywhere in this engine (110,574 m per degree north, 111,320 m × cos(latitude) per degree east). The file records the largest distance between the simplified line and the true one, measured both ways (`maxDeviationM`, 50.2 m for the current file), and the limit to apply (`limitM`): 300 m less that deviation rounded up, less 1 m for the plane, 248 m. `Border` (`border()`) applies it, so a point it accepts is never more than 300 m outside the true border; a point between 248 and 300 m outside may be refused, never one in a neighbouring country accepted.

`Border.holds(lat, lon)` is true inside the border (even-odd ray casting over every ring) or within the limit of it. Registry generation drops every structure and compound beyond it (7), issuing on demand refuses such a point, and an entrance never moves there (13). `tools/build_border.py check` counts the published codes whose entrance lies beyond it: none of 241,673, and none more than 300 m outside the unsimplified border either.

## 4. Spot codes

### 4.1 Grid

Each sector has its own grid frame, stored in `model/sectors.json`:

- origin `lon0`, `lat0`: the sector's bounding box south-west corner, rounded down to 0.001°;
- reference latitude `phi0`: the box's middle latitude rounded to 0.01°;
- cell size `s` metres: the box's longer side divided by 10,000, rounded up to 0.1 m.

A point (lat, lon) maps to
```
x = (lon − lon0) · cos(phi0) · 111320 / s        i = floor(x)    0 ≤ i ≤ 9999
y = (lat − lat0) · 110574 / s                    j = floor(y)    0 ≤ j ≤ 9999
```
The constants 111,320 and 110,574 m per degree are fixed for the life of the sector table (they are not "the truth" about the ellipsoid; they only have to be the same on every phone).

Cell sizes that result: Bissau 1.7 m; Biombo sectors 2.0-3.2 m; most rural sectors 3.7-7.7 m; the two largest, Boé 8.1 m and Gabú 9.4 m. The refinement digit (4.3) divides any cell by three.

### 4.2 Digits

`i` and `j` are written as four decimal digits each and interleaved, most significant first:
```
i = i3 i2 i1 i0,  j = j3 j2 j1 j0   →   D = i3 j3 i2 j2 i1 j1 i0 j0
```
so the first two digits name a cell of 1,000·s, the first four a cell of 100·s (170 m in Bissau, 400-900 m elsewhere), the first six a cell of 10·s. Written `SS-DDDD-DDDD`, with no check digit, because a spot code is shared as a link rather than typed; a code written with a trailing Damm check digit (`SS-DDDD-DDDD-C`) still decodes and its check is verified.

### 4.3 Refinement digit

Optional ninth digit `K` = which ninth of the cell, laid out like a phone keypad, north at the top:
```
1 2 3
4 5 6
7 8 9
```
`K = 3·row + col + 1`, `col = floor(3·fx)`, `row = 2 − floor(3·fy)`, where `fx`, `fy` are the fractional parts of x and y. Written `SS-DDDD-DDDD.K` (`SS-DDDD-DDDD.K-C`, with a check digit, still decodes).

### 4.4 Decoding

The centre of the cell (or of the ninth): `lat = lat0 + (j + 0.5)·s / 110574`, `lon = lon0 + (i + 0.5)·s / (cos(phi0)·111320)`.

## 5. Compound codes

### 5.1 Place word

A compound's place word is a bairro (Bissau), town or tabanca name from `model/places.json`:

- Bissau sector: OpenStreetMap `place=suburb|neighbourhood|quarter` nodes, plus the villages and GeoNames localities inside the sector that the city has absorbed (Plaque, Jal, Bono, Quetene...): 72 place words, 49 of them nearest to at least one compound; never "Bissau" itself. 28 of the 72 are OpenStreetMap bairro nodes; the Câmara Municipal de Bissau's bairro list adds names and aliases to the frozen table without renumbering any code.
- Other sectors: OpenStreetMap `place=city|town|village|hamlet` and town bairros, then GeoNames localities that are not already an OpenStreetMap place (no OSM place within 400 m, and none of the same name within 1.5 km): 4,149 places, for 4,221 in the whole table.
- The source's name is kept whole as the **official name** (`officialName`). The word in the code is the **plate name** derived from it (5.1.2): "Bairro de X", "Tabanca de X" become "X"; "Morança X" / "Moransa X" become "X", because people say the family name; a name over 12 characters or 2 words is shortened. The official name and the source's other names and spellings are aliases, unless an alias would point to two plate names (5.1.2).
- Each place has an index `PPP` (001-999) inside its sector in Hilbert order of its point (section 6.1). Index 000 is the sector itself, used as the place word for compounds more than 3 km from any place.
- A word that repeats, in one sector or in several, is kept as it is: no suffix is invented. All areas with the same name key (5.1.1) share one national number range (5.2). A numeral that is part of the name people say ("Plack II") stays part of the word.

A compound takes the **nearest place point in the same sector and on the same land mass** (island polygon, or the mainland; Ilha de Bissau counts with the mainland because it is joined by road) within 3 km; else index 000. Once issued, the place never changes for that compound, even if a bairro boundary is disputed or the place is renamed: a new name becomes an alias that finds the same compounds.

An **area** is what owns numbers: a place (sector, index), or a sector's own word (sector, 000).

#### 5.1.1 Name key

`name_key(word)` decides which words are the same name. Steps, in order:

1. lowercase; `ç` → `s`; Unicode NFKD and drop combining marks (accents);
2. every run of characters other than `a-z0-9` → one space; trim;
3. drop a leading `bairro|tabanca|tabanka|aldeia|povoacao|moranca|moransa|moranza`, with a following `de|da|do|dos|das` if there is one;
   then, if two or more tokens remain, expand the plate abbreviations: a first token `s` → `sao`, `sto` → `santo`, `sta` → `santa`, `sra` → `senhora`, and `n` before `sra`/`senhora` → `nossa` (so `Sto António` = `Santo António`, `S. Miguel` = `São Miguel`);
4. if there are two or more tokens and the last is a Roman numeral `i`-`x` or `1`-`10`, it is taken off as the numeral (Arabic → Roman);
5. if two or more tokens remain, drop the small words `de da do dos das e o a os as`;
6. fold each token: final `que` → `k`; `tch ch sh` → `x`; `ck qu` → `k`; `gu` → `g`; `ph` → `f`; `nh` → `n`; `lh` → `l`; `c` before `e`/`i` → `s`, other `c` → `k`; `z` → `s`; `y` → `i`; `w` → `u`; drop `h`; `e` → `i`; `o` → `u`; collapse doubled letters;
7. join the tokens with no separator, then append `#` + numeral if step 4 found one.

Examples: `Sintchã Dulo`, `Sinchã Duló`, `Sincha Dulu` → `sinxadulu`; `Plack II`, `Plaque 2` → `plak#ii` (≠ `Plaque` → `plak`); `Áfià`, `Hafia` → `afia`; `Bairro de Ajuda` → `ajuda`; `Santa-Luzia` → `santaluzia`. The folding errs towards merging: two names wrongly merged only share a range, while two spellings left apart would make a remembered form ambiguous. Once `name-ranges.json` is frozen, the rules may only be extended by alias (a word mapped to an existing key), never so as to split a key.

**Cedilla left out.** Step 1 reads `ç` as `s`, but a bare `c` before `a`, `o` or `u` folds to `k`, so a name typed without its cedilla (`Praca` for `Praça`, as most phone keyboards produce it) would have a key of its own. Lookups therefore add, for every plate name, official name and alias that contains `ç`, the key of the same word written with `c` as an alias of its key (`without_cedilla`), unless that key is a name of its own or two names would claim it. This is a lookup alias only; no key, range or block changes.

#### 5.1.2 Plate name

The word in a code is the area's plate name. `check_plate(word)` refuses a word over the limit, and `allocate` refuses to give a block to an area whose word is over it unless the area is flagged for the council (below).

- **Limit** (`plate_names.fits`): at most 12 characters of the NFC form, every character counted once (letters, spaces, hyphens, apostrophes; an accented letter is one), and at most 2 words. A word is a part between spaces or hyphens that is not a linking word (`de da do das dos d e o a os as em na no di du`), so `Lém-Ferreira` is two words and `Chão de Papel` is two words of 13 characters. No digits.
- **Derivation** (`tools/gw_plates.py`, using `engine/reference/plate_names.py`), on the official name, in order:
  1. a documented short form people already say, with its source (`KNOWN`; none is asserted yet);
  2. clean: the make-places prefixes above; a leading `Tabanca` when the rest is a real name; text in brackets ("Sucuta (Madina Fali)" → "Sucuta"); text after a slash; a second spelling after "ou"; generic words (`Bairro`, `Zona`, `Lote`, `Loteamento`, `Condomínio`, `Povoação`, `Phase` ...), unless what is left is only weak words ("Zona Sete" and "Tabanca Nova" stay);
  3. if the cleaned name fits, it is the plate name (`as-is` or `cleaned`);
  4. a standard abbreviation of a saint prefix (`Santo` → `Sto`, `Santa` → `Sta`, `São` → `S.`, `Nossa Senhora` → `N. Sra`) if that makes it fit (`abbreviated`);
  5. otherwise every run of whole words that fits, never starting or ending on a linking word, never cutting after a binding word (`São`, `Santa`, `Luís`, `João`, `Manuel` ...), never only weak words; ranked by how rare its words are among all the country's names, with a preference for the end of the name. The best is taken (`distinctive`) only if it is clearly ahead (score ≥ 1.5 × the next), has at least 4 letters, is not a well-known town, and passes the Guinea-Bissau rules below; otherwise the area is flagged.
- **Guinea-Bissau word lists.** Settlement heads, part of the name but the first words to go and never a plate name alone: `Sinchã`/`Sintchã` (Fula, "founded by"), `Sare` (Fula, "village of"), `Madina`, `Gã`, `Ponta` and its abbreviation `P.`, `Ponto`, `Barraca`, `Ilha`, `Ilhéu`, `Ponte` (with the Portuguese landform heads `Porto`, `Monte`, `Vale` ...). Qualifiers, never a plate name alone, and a short form that drops one is flagged: the peoples a tabanca is named after (`Balanta`, `Mancanha`, `Papel`/`Pepel`, `Fula`, `Futa-Fula`, `Mandinga`, `Beafada`, `Nalu`, `Manjaco`, `Felupe`, `Bijagó`, `Jacanca`, `Sosso` ...), number words (`um` ... `dez`) and the generic words themselves.
- **Guinea-Bissau rules** for an automatic short form; each sends the area to the council instead: it drops the end of the name, which tells the place from others ("Cuntum Madina" → "Cuntum", "Gadamael Porto" → "Gadamael"); it keeps only a founder's given name after dropping a settlement head ("Sinchã Mamadu" → "Mamadu"); it comes from two names joined by "e"; the official name contains a number ("14 de Novembro"). A few choices looked at by eye are flagged with their reason in `FLAG` ("Bairro Militar", "Granja-Pessube", "Centro da Cidade" in Bolama ...).
- **Avoid** (a plate name may not equal one): the 38 sector seats, the 8 region capitals, Bissau and the big cities of the region (Dakar, Ziguinchor, Conakry, Banjul, Praia ...), compared by name key; the area's own sector seat is allowed.
- **Council** (`needsCouncilChoice: true`, `plateCandidates` ≤ 3, `plateReason`): the Câmara Municipal (Bissau) or the sector administration with the régulos and the community chooses the plate name. Until then the first candidate is the provisional plate name and the area's codes are issued with it; the chosen name changes the word, never the number. An area with no candidate that fits keeps its cleaned name (`plateOverLimit: true`). `allocate` places a flagged area's block after the confirmed areas of its name.
- **Aliases.** The official name and the source's other names stay aliases of the area when their name key points to one plate name only. An alias whose key is another area's plate name, or that two plate names would claim, is moved to `aliasesDropped` and does not decode. `plate_key(word)` resolves what was typed: the plate name's own key if that name has blocks, else the key of the one plate name the alias points to.

Result (`tools/gw_plates.py`, 4,221 places): 746 official names are over the limit (744 over 12 characters, 179 over 2 words). 3,474 places keep their name as it is, 17 are cleaned, 1 is abbreviated (`Sto António`), 185 are shortened automatically and 544 are flagged for the council, 45 of them still over the limit provisionally. Of the 3,336 areas in use, 2,807 keep their name, 17 are cleaned, 119 are shortened, 37 are sector words and 356 are flagged (28 still over the limit).

### 5.2 Number: one national range per name, a frozen block per area

Every name key has **one national range, 1 to 99,999** (`MAX_NUMBER`), and a national name number `id` (assigned in alphabetical order of key when the place table was built; later names are appended). The range is cut into blocks `[from, to]`; each block belongs to exactly one area, and no two blocks of one name overlap. `name-ranges.json` is the table.

**Block size.** `size = min { n ∈ 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000 : n ≥ 4 · c }`, where `c` is the area's compounds at first issue (`GROWTH = 4`: the stride-2 issue fills half the block, and as many new compounds again fit).

**Allocation** (`allocate`). For a name, the areas to be given blocks are taken confirmed plate names first, then those flagged for the council (5.1.2), each in order of compounds descending, then sector, then index. Each block starts at the name's high-water mark (the end of its last block + 1; 0 at first) rounded up to a multiple of `10^(digits(size) − 1)`, and `to = from + size − 1`. If `to` would pass 99,999 the name cannot take the area: the area's word must take an established qualifier (5.2.1). An area with no compounds at first issue gets no block until its first code.

**Numbering inside a block.** At first issue, along the Hilbert curve (6.1) of their representative points: `from + 1, from + 3, from + 5 ...` (stride 2). Even numbers stay free for compounds built in between later; the rest of the block is free for the area's growth. Number 0 is never used.

**Stability** (frozen at issue). An issued block is never renumbered, moved, shrunk or reassigned. A new area with an existing name key gets a new block above the name's high-water mark. An area whose block has no free number left gets a **continuation block** the same way (`continuation`), sized by its current compounds; its earlier numbers keep their block. A name's high-water mark only rises.

**Decoding** (`block_of(key, n)`): the one area whose block holds `n`, or none (a spare number: refused, never guessed).

Result (`model/name-ranges.json`, plate names): 3,295 name keys; 2,704 with compounds in 3,336 areas; **407 names shared by two or more areas in use, in 1,039 areas** (92,745 compounds), 183 of them repeated inside one sector. The largest shared range is still **Áfià/Afia/Hafia**: 13 areas, 2,558 compounds, blocks 0-15,719 (five digits); the name with most areas is Missirá (14). The highest number at first issue has 1 digit in 276 areas, 2 in 1,492, 3 in 1,234, 4 in 309 and 5 in 25 (4 of them flagged for the council). With the official names as words it was 3,477 keys and 335 shared names in 856 areas; 1-5 digits in 305, 1,536, 1,192, 282 and 21 areas.

#### 5.2.1 Qualifiers

When a name's blocks would pass 99,999, its areas take one established qualifier people already say. It is decided once per name and listed in `name-ranges.json` → `summary.qualifiersNeeded`, and the qualified word is a name key of its own. The list is empty in the first issue. The qualifier would be the tabanca's ethnic or family qualifier, as the official names "Bambadinca Balanta" and "Bambadinca Mancanha" have it, in a form that fits the plate-name limit (5.1.2).

### 5.3 Structures and doors

Structures inside a compound are numbered 1, 2, 3 ... by footprint area, largest first, at first issue (so `.1` is the main house); later structures take the next number. A compound with one structure has no structure suffix. Gates and doors are `/1`, `/2` ...; `/1` is the primary gate, where a driver is sent.

### 5.4 Machine form and check digit

```
SS-PPP-NNNNN[.k]-C[/p]
```
`NNNNN` is the number padded to five digits. `C = Damm(id₅ ‖ NNNNN ‖ k)`: the Damm check digit over the name's national number padded to five digits, then the five number digits, then the structure digits if any (`check_digit`). Damm uses one 10×10 table (the totally anti-symmetric quasigroup of order 10, H. M. Damm 2004; in `gw_codes.py`); `interim = 0; for d in digits: interim = T[interim][d]`; the check digit is the final interim. The door suffix is outside the check (it is short and confirmed on the spot).

**The check binds name, number and area.** A machine form is valid only if (1) `SS-PPP` is an area, (2) `C` matches the area's name and the number, and (3) `block_of(name key of SS-PPP, NNNNN)` is that same area (`parse`). The area is deliberately not a Damm input: it is a function of name and number through the frozen block table. Keeping it out lets the Damm property cover every digit of the number when a system sends the check with a written code. So:

- when a system sends the check digit with a written code (`Bandim 275` with 8), every single wrong digit of the number or the check and every swap of two neighbouring number digits is refused, **including those that would land in another area of the same name** (0 undetected in the selftest's exhaustive check of the vectors; `Missira 15` → `Missira 5015`, a Sonaco number, is refused);
- in the machine form, a wrong digit or swap in `NNNNN` or `C` is always refused; a wrong digit in `SS-PPP` is always refused when it would land in another area of the same name (rule 3) or on no area. In a test over the first number of every block, 3.0 % of wrong `SS-PPP` digits land on an area with a **different** name where the number also exists and the check also matches. The decoded word then differs from the one on the document, and every screen shows it.

### 5.5 Remembered and written forms

```
<word> <number>[.<structure>]            remembered (spoken) and written (plates, shares)
<word> <number>[.<structure>]-<C>        as a system may send it, with the check digit
```
Resolution (`from_remembered`), with no position, town or sector: `plate_key` of the word (5.1.1, 5.1.2; the plate name, or an official name or alias that points to one plate name); if the check digit is given, verify `C` (5.4); then `block_of(key, number)` gives the **one** area; a spare number (in no block) is refused. The result is the area's word, its sector (shown as a label) and the machine form. The island or sector the app shows beside an address ("Ambeduco 23 · Orango", "Bandim 2001 · Catió") is display only and never an input. Without the check digit, as people say and write a code, a single wrong digit can still name a real compound elsewhere, so the app shows the decoded area (place and sector) before navigating, and the person sees at once whether it is the place they meant.

## 6. Ordering

### 6.1 Hilbert curve

`hilbert(i, j)` is the distance of grid cell (i, j) of the sector's spot grid along a Hilbert curve of order 14 (16,384 × 16,384, covering the 10,000 × 10,000 grid); standard iterative xy→d conversion (in `gw_codes.py`). Nearby compounds get nearby numbers; one place's numbers run along its lanes block by block rather than in random order.

### 6.2 Land masses

Places and compounds on an island (OpenStreetMap `place=island|islet` polygons, 189 in the extract) only take place words on the same island. A Bijagós compound on Orango is never numbered in a place on Bubaque.

## 7. Registry generation

**Determinism.** Before grouping, structures are sorted by (sector, latitude, longitude, area, source, OpenStreetMap id), so the compounds never depend on the order the extract writes rows in. A compound's key is its main structure's stable id (the largest structure; ties by id). Along the Hilbert curve, ties between compounds in one cell break on that key. Every port numbers the same compounds the same way; the issuer checks every number of a first issue against the reference's before writing any.


Order of operations, run once per sector for the first issue (`tools/extract-buildings.py`, `tools/building-stats.py`), and incrementally afterwards:

1. **Footprints.** OpenStreetMap buildings plus Google/Microsoft footprints that OpenStreetMap lacks (as N-Ways' map already merges them). Area and perimeter in UTM 28N (EPSG:32628). Footprints under 6 m² are dropped as noise.
2. **Sector** by centroid (section 3). **The border decides** (3.1): a footprint whose centroid lies more than 300 m outside the national border is dropped, whatever the sector outlines say.
3. **Settlement class** by density in a 250 m window: cidade ≥ 10 buildings/ha, vila 4-10, tabanca 1-4, disperso < 1.
4. **Group structures into compounds, before any numbering:**
   1. *Enclosures first.* A footprint whose centroid is inside a mapped wall, fence or hedge, a `landuse=farmyard` outline (how OpenStreetMap mappers draw moranças) of up to 1 ha, or a `landuse=residential` plot of up to 2,500 m², joins that enclosure's compound. Institutional sites (schools, hospitals, markets, military, police, government, religious and industrial sites; N-Ways' routing compounds) make one institutional compound.
   2. *Proximity for the rest.* An annex (< 40 m²: kitchen, store, latrine) joins the nearest structure within `da`; two larger structures join if the gap between them (centroid distance minus half the square root of each area) is at most `gm`. `da`/`gm` by settlement class: cidade 6/3 m, vila 10/6 m, tabanca 15/12 m, disperso 20/15 m.
   3. *Cap.* A group of more than 12 structures is re-linked with half the distances, repeatedly, until every group is at most 12 (a whole tabanca must not become one compound).
   4. *People override.* A confirmed "these buildings are one home", "this is a separate home" or a gate position replaces the machine grouping.
5. **Representative point** of the compound: the confirmed primary gate if there is one; otherwise the footprint-area-weighted centroid. A compound whose representative point lies more than 300 m outside the national border (3.1) is dropped before any place or number is given.
6. **Place word** (5.1); **blocks** for every area with compounds (5.2, `allocate`, written to `model/name-ranges.json`); **number** inside the area's block; then **structure numbers** (5.3).
7. **Profiles** for every structure and compound (section 8).
8. Write the registry row per compound (`registry/<SECTOR>.csv.gz`): machine form, remembered and written forms, area, official name, number, check digit, status, issue kind and time, entrance point and kind, Plus Code, the compound's profile (class, use, kind, number of structures, floor area, settlement class) and postcode. Rows are ordered by the name's national number, then the compound number.

### 7.1 Stability rules

- A code never moves to another compound and is never reused. A demolished structure's code is retired; a compound whose every structure is gone is retired.
- **Merge** (people say two compounds are one home): the compound keeps the code of the part with the primary gate; the other code becomes an alias that still resolves.
- **Split** (people say one machine compound is two homes): the part with the primary gate (or the largest structure) keeps the code; the other part takes a new number by the "Add my home" rule (7.2), in the same place.
- **New structure** in an existing compound: next structure number.
- Rebuilt footprint (new imagery, slightly different outline) at the same place: same structure, same code.
- Blocks (5.2) are never renumbered. A new area with an existing name, and an area whose block is full, get new blocks above the name's high-water mark.

### 7.2 "Add my home": choosing the provisional number

When someone adds a new compound (docs/model.md, "Add my home"), the registry, or the phone if offline for a provisional display only, chooses the number as follows (`insert`, which applies `reserve_number` to each block):

1. Place word: 5.1, from the gate position. If the area has no block yet (its first compound), it gets one now (5.2).
2. The area's blocks are tried in the order they were given. In a block `[from, to]`, let `h` = Hilbert index of the gate, and find the issued numbers of that block immediately before (`na`, `ha`) and after (`nb`, `hb`) along the curve (with no predecessor, `na = from`). Retired numbers count as issued: a number is never reused.
3. If there is a successor and `nb − na > 1`: the wanted number is `na + round((h − ha)/(hb − ha) · (nb − na))`, clamped to `na+1 … nb−1`; take the free number nearest to it.
4. Otherwise (no successor, or no free number between): the block's highest issued number + 1, if it is still ≤ `to`; else the next block is tried.
5. If every block is full: the area takes a continuation block (5.2), sized by the block rule for all its numbers plus this one and starting at the name's high-water mark rounded up; the number is its `from + 1`. If that block would pass 99,999, nothing is issued and the name needs a qualifier.

The code is **provisional** until confirmed (docs/model.md); a provisional code is never given to anyone else, and the confirmed code is the same code. Only the registry issues numbers: a phone offline shows the spot code at once and the compound code when it reconnects, so two homes can never take the same number.

**Test vectors** (`selftest`, toy area of 12 compounds along a lane in Apurnia, sector 75, block 0-49): first issue gives 1, 3, 5 ... 23; a new gate between the compounds numbered 11 and 13 gets **12** ("gap"); a new gate past the last compound gets **24** ("end"); in an area where 1-12 are all taken, a new gate between 5 and 6 gets **13** ("end"). The same area as the second block of its name (2000-2199) is issued 2001, 2003 ... and gets **2012** and **2024**; with a block of 0-23 the gate past the last compound gets **full** (continuation block). Allocation vectors: Cumura with 310 and 40 compounds gets 0-1,999 and 2,000-2,199; a later Cumura area of 600 compounds gets 3,000-7,999 and the first two blocks are unchanged; a continuation for the 40-compound area is 8,000-8,199.

## 8. Building profile

Every structure and every compound in the registry carries a profile. Schema (also in `model/design.json` → `buildingProfile`):

### 8.1 Structure

| Field | Type | Public? | Source |
|---|---|---|---|
| `code`, `remembered` | string | yes | registry |
| `compound`, `structure` | string, int | yes | registry |
| `footprint.id`, `footprint.source` | string | yes | `osm:way/…`, `google-open-buildings`, `microsoft` |
| `size.footprintM2`, `size.perimeterM` | number | yes | computed from the polygon (UTM 28N) |
| `size.circularity` | number | yes | 4πA/P²; ≥ 0.9 marks a round house (OpenStreetMap outlines only: the machine-learning outlines are rectangles) |
| `size.heightM`, `size.heightSource` | number or null | yes | OpenStreetMap `height` only. The height column of the machine-learned footprint files is a rendering placeholder (3.5-7 m derived from the footprint's identifier) and is never used. |
| `size.floors`, `size.floorsSource` | int or null | yes | OpenStreetMap `building:levels`, else `height`/3, else null; people and partners can add it |
| `size.floorAreaM2` | number or null | yes | footprint × floors, only when floors are known |
| `use.class` | enum (8.3) | yes, except `religious.shrine` (8.4) | inference (8.3) |
| `use.confidence` | 0-1 | yes | inference |
| `use.source`, `use.rule` | string | yes | which signal decided |
| `use.lastConfirmed` | date or null | yes | last person or partner confirmation |
| `name` | string or null | only for businesses and public buildings | OpenStreetMap, N-Ways places, the business or institution |
| `status` | `existing`, `under-construction`, `ruin`, `retired`, `unknown` | yes | tags, imagery, people |
| `entrances` | list | yes for gates and business doors; a home's doors are private on request | people |
| `lastSeen` | date | yes | newest imagery or confirmation |

### 8.2 Compound

| Field | Type | Public? |
|---|---|---|
| `code`, `remembered`, `place`, `number`, `sector` | | yes |
| `kind` | `residential` (one household), `residential-multi` (family compound / morança with several households), `mixed`, `commercial`, `institutional`, `unknown` | yes |
| `groupedBy`, `groupingConfidence` | `enclosure:<id>` (0.9), `proximity` (0.5-0.7 by class), `person` (1.0 once confirmed), `partner` | yes |
| `plotAreaM2` | enclosure or the outline given by the household; null otherwise | yes |
| `structures`, `footprintM2Total`, `floorAreaM2Known` | | yes |
| `gates` | list of {n, lat, lon, kind, confirmations, lastConfirmed} | yes (the gate is where people arrive) |
| `households` | int, only if the household declares it | aggregate only, never per name |
| `status` | `provisional`, `confirmed`, `retired`; `aliases` (merged codes) | yes |
| `issued`, `confirmed` | dates | yes |

### 8.3 Use classes and inference

Classes (dotted: family.detail): `residential.compound-house`, `residential.round-house`, `residential.annex`, `residential.house`, `residential.apartments`, `residential.hut`; `commercial.shop`, `commercial.kiosk`, `commercial.market`, `commercial.warehouse`, `commercial.office`, `commercial.workshop`; `government`, `government.military`; `education`; `health`; `religious`, `religious.shrine`; `industrial`; `agricultural.store`; `fishing`; `hospitality`; `transport`; `utility`; `public.sport`, `public.landmark`; `mixed`; `status.construction`, `status.ruin`; `unknown.large`; `unknown`. Their Guinea-Bissau meanings are in docs/model.md.

Inference order, first match wins:

| # | Signal | Confidence |
|---|---|---|
| 1 | OpenStreetMap `amenity`, `shop`, `office`/`government`, `tourism` on the footprint | 0.85-0.90 |
| 2 | OpenStreetMap `building=*` with a specific value (house, hut, school, mosque, church, hospital, warehouse, construction, ruins …) | 0.85 |
| 3 | An N-Ways place (POI) inside the footprint or within 4 m of it, by its category | 0.65 |
| 4 | The enclosure it stands in (school, hospital, market, military, religious, industrial site) | 0.55 |
| 5 | Shape: circularity ≥ 0.9 and ≤ 80 m² → `residential.round-house` | 0.60 |
| 6 | Size in its compound: < 25 m² beside a structure ≥ 60 m² → `residential.annex` | 0.45 |
| 7 | Size alone: ≥ 600 m² → `unknown.large` (warehouse, market hall, school or church: asked first) | 0.30 |
| 8 | Default: `residential.compound-house`; confidence tabanca 0.65, disperso/vila 0.55, cidade 0.50 | 0.50-0.65 |

A person's or partner's confirmation sets confidence to 1.0 for that attribute with `use.source = person|partner` and `use.lastConfirmed`; three agreeing visitors (arrivals at the gate, deliveries) confirm without review, as N-Ways settles map corrections everywhere.

### 8.4 Privacy in the profile

- Residential structures and compounds never carry occupant data: no names, no phone numbers, no household composition, no photos of people or interiors.
- `name` is published only for businesses and public buildings, and only the name the business, the institution or OpenStreetMap publishes.
- `religious.shrine` (a *baloba* or a sacred grove house) is stored but **not published** unless the community responsible agrees; it is shown on the map only as `unknown`.
- A household can mark its home's doors private; the compound code and gate stay (they are what a visitor needs).
- Military and police compounds keep their code and outline (they are on the public map) but no structure profiles.

## 9. Capacity and limits

- Places per sector: at most 999 (maximum at the first issue: 234).
- Numbers per name (shared by all its areas): 1-99,999, five digits at most. At the first issue, the highest high-water mark of a shared name: 15,720 (Áfià); of any block: 19,999 (Bono, one area).
- Name keys: national name numbers up to 99,999 (3,295 at the first issue).
- Plate names: at most 12 characters and 2 words (5.1.2).
- Structures per compound: up to 99 (`.1`-`.99`).
- Spot grid: 10,000 × 10,000 cells per sector.

## 10. Validation of input

`parse()` accepts a machine form with or without spaces; rejects an unknown sector or place, a wrong length, a structure number starting with 0, a failed check digit, or a number whose block belongs to another area. `from_remembered()` accepts "word number[.structure][-check]" in any letter case, with or without accents, in any spelling with the same name key, and with the official name or an alias in place of the plate name when it points to one plate name; it rejects an unknown name, a failed check digit and a spare number. `check_plate()` rejects a plate name over 12 characters or 2 words, or with a digit.

## 11. Test vectors

Run `python3 engine/reference/gw_codes.py`. Real points (cell sizes from the frozen grid):

| Place | lat, lon | Sector | Spot | Refined | Place word |
|---|---|---|---|---|---|
| Bissau Velho | 11.8591, −15.5793 | 10 BIS | `10-5421-9699` | `10-5421-9699.8` | Bissau Velho (10-033) |
| Mercado de Bandim | 11.8521, −15.5951 | 10 BIS | `10-4327-8173` | `10-4327-8173.1` | Bandim (10-022) |
| Bairro Militar | 11.8738, −15.6156 | 10 BIS | `10-2591-7235` | `10-2591-7235.5` | Militar (10-059; council to confirm) |
| Bafatá, Praça | 12.1645, −14.6643 | 21 BAF | `21-0195-4839` | `21-0195-4839.5` | Nema (21-008) |
| Gabú town | 12.2830, −14.2230 | 62 GAB | `62-3779-4218` | `62-3779-4218.4` | Gabu (62-042) |
| Canchungo (55-091) | 12.0670, −16.0330 | 55 CAN | `55-4447-6534` | `55-4447-6534.2` | Canchungo (55-091) |
| Bubaque | 11.2990, −15.8277 | 32 BBQ | `32-3771-6328` | `32-3771-6328.6` | Bubaque (32-071) |
| Bolama | 11.5783, −15.4735 | 31 BOL | `31-6463-3238` | `31-6463-3238.5` | Bolama (31-054, official name Centro da Cidade; council to confirm) |
| Catió | 11.2830, −15.2500 | 93 CAT | `93-5231-7258` | `93-5231-7258.5` | Priame (93-045) |
| Madina do Boé | 11.7470, −14.2160 | 61 BOE | `61-2296-7027` | `61-2296-7027.5` | Boé (61-011) |

Machine forms: `10-022-00275-8` = Bandim 275 (compound), `10-022-00275.2-3` = Bandim 275.2 (structure 2), `10-022-00275-8/1` (its primary gate), `75-039-00015-0` = Atufa 15 (official name Morança Atufa).

Same name, different areas (decoded with no context; `SAME_NAME` in the script):

| Remembered | Written | Machine form | Area |
|---|---|---|---|
| `Bandim 275` | `Bandim 275` | `10-022-00275-8` | Bissau, bairro Bandim (block 0-1,999) |
| `Bandim 2001` | `Bandim 2001` | `93-005-02001-3` | Catió, tabanca Bandim (block 2,000-2,199) |
| `Missira 15` | `Missira 15` | `10-050-00015-0` | Bissau (block 0-4,999) |
| `Missirá 5001` | `Missirá 5001` | `65-073-05001-7` | Sonaco (block 5,000-5,499) |
| `missira 6001` | `Missirá 6001` | `21-092-06001-8` | Bafatá (block 6,000-6,199), typed without the accent |
| `Afia 1` | `Hafia 1` | `43-016-00001-8` | Safim, written Hafia there (block 0-4,999 of the largest shared range) |
| `Hafia 15701` | `Áfià 15701` | `62-105-15701-2` | Gabú, written Áfià there (block 15,700-15,719): any spelling of the name works |

Plate names (`PLATES` in the script):

| Official name | Remembered | Written | Machine form | Area |
|---|---|---|---|---|
| Sinchã Malam Baio | `Malam Baio 1` | `Malam Baio 1` | `24-148-00001-9` | Galomaro; a long official name and its plate name; `Sinchã Malam Baio 1` decodes to the same compound |
| Bairro Ajuda II Phase | `Ajuda II 1` | `Ajuda II 1` | `10-012-00001-4` | Bissau; generic words dropped, the numeral kept |
| Ama Seidi | `Ama Seidi 1` | `Ama Seidi 1` | `62-153-00001-7` | Gabú (block 0-999) |
| Missirá Ama Sidi | `Ama Sidi 1001` | `Ama Sidi 1001` | `72-175-01001-4` | Farim (block 1,000-1,099): its plate name collides with Ama Seidi only after shortening, so the two share one range and decode to different places |

The script also checks that `check_plate` refuses `Sinchã Malam Baio`, `Ponta Manuel das Águas` and `Zona 7`, that `allocate` refuses an over-long word for an area not flagged for the council, and that `Sto António` and `Santo António` have one name key.

For each vector, every single wrong digit in the five-digit number and every adjacent swap, with the vector's check digit, is refused, including `Missira 5015`; `Bandim 2275` (spare) is refused. The script also checks that every single-digit change and every swap of neighbouring digits in a spot code is rejected, that in the address code every such change is rejected except a wrong `SS-PPP` digit that lands on an area of a different name (5.4), that every spot decodes back to itself, and the "Add my home" vectors in 7.2. Place indices come from the place table, frozen at the first issue.

## 12. Official addresses first

**Every compound has an N-Ways code**, and where a government address exists, that address is shown first, exactly as the government writes it, with the code beside it. The code is never withdrawn; it stays valid and leads to the same gate.

In Guinea-Bissau no official door-level address was found anywhere (checked at the first issue, 20 October 2026). Central Bissau (Bissau Velho, Praça/Plateau and the avenues between them) has the Câmara Municipal's street names; whether its door numbers are official and complete is *unverified* and is the first question for the Câmara. `model/coverage.geojson` keeps that area for when the Câmara publishes or confirms numbering: from then on the card shows "street + number" first for each compound whose official number is known (from the authority's data or from people confirming the number on the gate), and the N-Ways code beside it.

Postcodes: the UPU's paper 4-digit postcode is a locality code, not a door address. Codes in sector 10 carry `1000` (`postcode`, shown as `1000 BISSAU`, context only); other sectors carry none until Correios publishes codes, which are then added per sector or per place.

## 13. "Add my home": what the engine receives and checks

A person building or moving into a compound adds it from the app (docs/model.md describes the flow). The engine receives:

| Input | How | Kept |
|---|---|---|
| Gate | GPS averaged for 10-20 s while standing at the gate, plus one photo of the gate | the gate point and the photo (no people; blurred if a face is detected) |
| Outline (one of) | (a) corners tapped on satellite imagery; (b) the boundary walked inside the wall with the camera (ARKit/ARCore world tracking, anchored by GPS averaged over the walk, then snapped to imagery and nearby footprints); (c) a survey plan's beacon coordinates, typed or photographed, with their datum stated | the outline polygon only: no video, no interior |
| Description | households (a number), structures, floors, use | the counts and the use class |

Datum for (c): Guinea-Bissau plans use the *Bissau* datum, *Bissau / UTM zone 28N* (EPSG:2095), or, from GNSS, WGS 84 / UTM 28N (EPSG:32628). The app asks which; coordinates in EPSG:2095 are transformed to WGS 84 with the published EPSG transformation for the Bissau datum before any check (the shift is tens of metres, so the datum is never guessed).

Checks before a provisional code is shown (any failure: the code is not issued, and the app says why):

1. The outline is a closed loop, not self-intersecting, between 20 m² and 2 ha (a larger plot is an estate or a field: asked again).
2. The gate is on the outline (within 3 m of it).
3. For a walked outline, the AR track and the GPS track agree (mean offset under 8 m after the best shift).
4. No overlap of more than 10 % with an existing compound's outline or with a footprint of another compound: an overlap is *flagged* for the neighbours and the registry, never issued.
5. The gate is inside a sector, and inside the national border or within 300 m of it (3.1). In an `official` area of the coverage mask the official address is shown first, with the code beside it.

The registry applies its own checks to every request it receives, whatever the app did before: a live code within 3 m of the point, or an outline overlapping a recorded one by more than half of the smaller, means the building already has its code; an outline must enclose 6 m² to 2 ha; another door of a compound must stand within 80 m of its entrance; a point more than 300 m outside the national border is refused, and an entrance never moves there (3.1, `server/README.md`).

Then: place word (5.1) from the gate, number by 7.2, status `provisional`. Offline, the phone shows the gate's spot code at once and queues the request; the compound code is issued by the registry, the single source of numbers, on the next connection.

Confirmation turns `provisional` into `confirmed`, same code: three arrivals or deliveries at the gate on different days, or new imagery or footprints matching the outline, with no dispute from a neighbour in 30 days. A dispute freezes the code (it still resolves) until people on both sides agree or the overlap is removed.

A compound code is an address. It is not a land title, a concession or proof of any right to the land, and the flow says so before the person starts.
