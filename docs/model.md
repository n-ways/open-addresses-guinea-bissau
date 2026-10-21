# The Guinea-Bissau model

The design notes behind each choice of the model: the options weighed, the measurements that decided them and the rules that follow from them. The complete model, with every formula, is in the white paper ([paper.md](paper.md)); the normative algorithms are in [engine/SPEC.md](../engine/SPEC.md). Numbers here come from the N-Ways map data of 17 October 2026 and the registry issued on 20 October 2026 (`model/building-stats.json`, `model/places.json`, `model/name-ranges.json`, `model/sectors.json`); sources are in [SOURCES.md](../SOURCES.md).

This model is made for Guinea-Bissau alone. It answers one question: how does a family in a Bissau bairro, a Balanta tabanca in Oio or a fishing village on Orango get an address that they will remember, that a moto-taxi driver can find, and that costs them nothing to get?

## 1. First criterion: people remember it

The first criterion is that citizens find their code easy to remember and even easier to get. In Guinea-Bissau that rules out most of what addressing systems usually do.

### 1.1 What the country tells us

| Fact | Consequence |
|---|---|
| Kriol is spoken by about 90 % of people, Portuguese by about 27 %, French by 5 % (2009 census) | the code must be said in Kriol first; letter names are Portuguese and unfamiliar to most Kriol speakers |
| Adult literacy is about 64 % (2022), with a 27-point gap between men and women | a code people read must be short and mostly digits; nobody should need to spell |
| People already say where they live as **bairro + landmark** in Bissau and **tabanca + morança** elsewhere | the place word already exists in every head |
| Phone numbers have nine digits (since 2015) and are said in groups | people are practised at remembering short digit groups |
| Nothing below the locality is official (2 house numbers in all of OpenStreetMap) | there is nothing to conflict with, and nothing to lean on either |

### 1.2 Options compared

| Option | Example | Length to remember | Said in Kriol | Verdict |
|---|---|---|---|---|
| Alphanumeric grid code (Plus Code style) | `7FG2+QX` / `PR 7HQ2-X` | 6-8 symbols incl. letters | letters must be spelled with Portuguese names | rejected: letters are the hard part for most people here |
| Digits only, national | `10 022 00275 9` | 11 digits | easy, but nothing to hang memory on | rejected: as long as a phone number, with no meaning |
| Sector + number | `Nhacra 4127` | sector + 4-5 digits | easy | rejected: sectors hold up to 14,700 compounds, so numbers run to 5 digits, and many people do not use sector names day to day |
| **Place word + short number** | **`Bandim 275`, `Atufa 15`** | a word they already use + 1-5 digits (1-4 for 98.8 % of compounds) | easy: "Atufa kinzi" | **chosen** |

### 1.3 The arithmetic

A place word is a Bissau bairro, a town or a tabanca (section 5.1), in a short form of at most 12 characters and 2 words: its plate name (section 5.4). Every place with the same name shares one national number range, cut into a block per place (section 5.2), so the code is unique in the whole country on its own. Inside its block, a place's compounds are numbered 1, 3, 5 ... along the lanes at first issue (block start + 1, + 3 ... for a later block), so a place with *n* compounds in the block starting at *b* starts with highest number *b* + 2*n* − 1, keeping every even number free for homes built in between and the rest of the block for growth.

| | Places | Compounds per place (median / 90th pct / max) | Digits of the highest number at first issue |
|---|---|---|---|
| Bissau (sector 10) | 49 place words in use (72 in the place table) | 710 / 1,600 / 3,274 (Bono) | 1 digit in 1 place, 3 digits in 15, 4 digits in 31; 5 digits only in 2 places whose plate name waits for the Câmara |
| Rest of the country | 3,287 | 30 / 118 / 1,912 (Buba) | 1 digit: 276 places; 2 digits: 1,488; 3 digits: 1,222; 4 digits: 278; 5 digits: 23 |

So in most of the country a home's number has two or three digits ("Atufa 15"), three or four in towns, four in the big Bissau bairros, and five only in 21 small places that share a name with a big town (1,642 compounds, 0.7 %), plus 4 places whose provisional plate name is the name of a bigger place and waits for the council (1,855 compounds; section 5.4). Every confirmed Bissau place word is the largest area of its name, so Bissau keeps its numbers. Even Bono, Bissau's fullest place word, ends its first issue at 6,547, four digits, and its block (0-19,999) has room for three times as many compounds again. A place whose block ever fills gets a further block of its name's range; nothing is renumbered, and no number passes 99,999 (five digits).

Fewer place words would mean longer numbers. With only the 28 bairro points OpenStreetMap has today, the largest Bissau places reached 5,833 compounds and five-digit numbers (11,665). Adding the absorbed villages inside the city (Plaque, Jal, Bono, Quetene ...) brought every Bissau number back to four digits or fewer. The Câmara Municipal's official bairro list is therefore the first refinement to seek (section 12).

### 1.4 The two forms

- **Remembered form**: `Bandim 275`, or `Malam Baio 15` for the tabanca whose official name is Sinchã Malam Baio (a structure inside the compound: `Bandim 275.2`). This is what people say, write on a parcel, type into the app or tell a driver.
- **Written form**: the remembered form itself, `Bandim 275`, on the plate, in every share and on paper. People never see or type a check digit.
- **Machine form**: `10-022-00275-8`, i.e. sector 10 (Bissau), place 022 (Bandim), compound 00275, check digit 8. It is used by systems: forms, partner software, links and the QR code on the plate. It maps 1:1 to the remembered form, and it is the only form that carries the check digit; nobody has to remember it.

"Bandim 275" alone names one compound in the whole country: the number says which Bandim (section 5.2). The **check digit binds the name, the number and the area**. It is the Damm digit over the name's national number and the compound number, and a code is valid only if the name's frozen block table gives that number to that area. So a mistyped machine form cannot land in another place of the same name without being noticed: the code of Missira 15 (Bissau) with its number mistyped as 5015 would point to a number of Sonaco's Missirá, and it is refused, as is every single wrong digit and every swap of two neighbouring digits in the number. In the machine form, a wrong digit in the sector or place part is refused whenever it would land in another area of the same name or nowhere. In about 3 % of cases (3.0 % in a test over the first number of every block) it lands on a place with a different name, whose word every screen shows. Spoken or written without the check digit, as people always use it, a code still decodes to exactly one area, and the app shows that area (place and sector) before it navigates. A number of a name that was never issued is refused, never guessed into a nearby area.

### 1.5 Saying it

- Kriol: place word, then the number as one number up to 99 ("Atufa kinzi"), or digit by digit for longer ones, as for phone numbers ("Bandim, dus seti sinku"). Kriol digit words follow Portuguese (*un, dus, tris, kuatru, sinku, sis, seti, oitu, nobi, zeru*; spellings to be checked with native speakers).
- Portuguese: "Bandim, duzentos e setenta e cinco" or "um dois sete quatro".
- Fula, Balanta, Mandinka, Papel, Manjaco speakers generally count in Kriol or Portuguese for numbers of this size; the place word is in whatever language the place is named in.
- The app's voice reads the number digit by digit in Kriol or Portuguese (user's choice), then repeats the place word.

### 1.6 Getting your code: no effort

| Way | Steps |
|---|---|
| N-Ways app, home already saved | 0 taps: the "Your home code" card is on the home screen |
| N-Ways app, standing at your gate | 1 tap ("This is my home") → the card |
| Share it | 2 taps: Share → WhatsApp or SMS; the message carries the remembered form and a link that opens navigation to the gate |
| No smartphone | a plate or sticker on the gate (big `BANDIM 275`, the official name in small type when it differs from the plate name, and a QR code that holds the machine form); a neighbour, a courier or a community volunteer can read it from any phone with the app |
| New home | "Add my home" (section 9): about 3 minutes at the gate |
| A courier or partner | looks up a customer's code with the customer's consent (section 10) |

There is no SMS lookup service; one is a possible later option only.

## 2. Official addresses first: the coverage mask

Where a government address exists, it is shown first, exactly as the government writes it, with the N-Ways code beside it. Every compound has an N-Ways code. The coverage mask (`model/coverage.geojson`, SPEC section 12) marks where an official address exists:

- **official**: government street names and door numbers, published or confirmed. The official address is shown first, the code beside it. Today: **none anywhere in Guinea-Bissau.**
- **mixed**: official street names, doors partly numbered. A gate with an official number shows "street + number" first; every gate has its N-Ways code. Today: **central Bissau** (Bissau Velho, Praça/Plateau and the avenues between them), where the Câmara Municipal's street names are on signs and on maps: 83 of the 157 named streets in OpenStreetMap's Bissau area fall here, and the UPU's own example is "Rua Justino Lopes 12C, 1000 BISSAU". Whether its door numbers are official and complete could not be verified; it is the first question for the Câmara.
- **n-ways**: everything else, which is nearly the whole country.

The mask only grows towards official. When the Câmara, Correios or a national programme numbers an area, its official addresses are shown first, and the codes there stay valid and resolve to them.

The paper postcode is not a door address, so it never makes an area official. Every address in sector 10 carries `1000 BISSAU` on its postal line. Elsewhere the locality name is printed alone until Correios publishes codes; they are then mapped per sector or place.

## 3. Why the compound, not the building

In Guinea-Bissau a home is rarely one building. Outside the centre of Bissau, a family lives in a **morança**: a compound of a main house, often long and rectangular, with separate kitchens, stores and sometimes round houses. One gate or yard entrance faces the lane, and one *homem grande* heads the family. In Bissau, many plots are walled *quintais* with a main house, an annex and sometimes a shop built into the wall. OpenStreetMap mappers already record this: 782 moranças are drawn as `landuse=farmyard`, and moranças appear as named places ("Morança Atufa", "Moransa Andunke" near Apurnia).

The data says the same thing:

- Footprint sizes are bimodal: a quarter of all footprints are under 33 m² (kitchens, stores, latrines, small round houses) and half are over 116 m² (houses).
- Grouping the 419,593 footprints with the rules in SPEC 7 gives **241,673 compounds**; **65.5 %** of footprints are in compounds of two or more structures (Bissau 57.9 %, Oio 70.9 %).
- The east is a different place: in Gabú region the median footprint is 41 m², against 167 m² in Bissau. The many small houses of Fula and Mandinka compounds would each get a code of their own if buildings were the unit.
- The 4th census (June 2026, preliminary) counted about 301,000 households. That is about 1.25 households per machine-grouped compound, consistent with family compounds of more than one household.

So the address belongs to the compound, and its structures are sub-units (`.1`, `.2`), each with its own building profile. The **gate** is the compound's primary entrance (`/1`), and a driver is sent there, not to a roof's centroid. A shop built into a compound wall with its own door to the street is its own structure with its own door. An apartment block in Bissau is one compound, with its flats as structures or unit numbers. A walled institution (school, hospital, barracks) is one institutional compound.

### 3.1 How compounds are found, and how good that is

1. **Enclosures first.** Footprints inside a mapped wall, fence, hedge, `landuse=farmyard` outline or small residential plot form one compound (763 compounds today). So do footprints inside an institutional site.
2. **Proximity for the rest.** An annex under 40 m² joins its nearest structure; houses join when the gap between them is small. The distance depends on the settlement class: 3 m in the dense city, where neighbours share walls, up to 12 m in tabancas and 15 m in dispersed settlement. A group over 12 structures is split again, so a whole tabanca never becomes one compound.
3. **People correct it.** "These buildings are one home", "this is a separate home" and "this is the gate" override the machine.

Checked against the compounds people drew (proximity rule re-run with enclosures hidden): **58 % of mapped rural moranças come out whole and 46 % exactly**, with another 24 % missing just one structure. In walled urban plots the rule finds only 13 % whole, because buildings inside a Bissau wall stand far apart while neighbours across the wall stand close. The rule therefore under-merges in town on purpose. Merging two codes later is harmless: one becomes an alias. Splitting a wrongly merged compound would give some families a new code. In the cidade class, a wall-tracing pass on imagery and door and gate confirmations by residents correct the grouping after issue; only 12 compounds in the whole country have a mapped gate today (3 in Bissau).

## 4. Hierarchy

| Level | Count | Role in the model | Why |
|---|---|---|---|
| Region | 8 + Setor Autónomo de Bissau | first digit of the sector number only | too large (Gabú 9,101 km²) to anchor a code, and its administration is appointed rather than local |
| Sector (setor) | 38 + Bissau = 39 | first two digits of the machine form; owns the spot grid | the smallest official unit with boundaries (OpenStreetMap admin_level 6, from DGGC data); small enough for 1.7-9.4 m spot cells |
| Place word | 4,221 in the place table | the word people remember, as a plate name of at most 12 characters and 2 words | already used by everyone; not official, so the code never depends on its boundary |
| Compound | 241,673 in the registry | the address | how people live |
| Structure, gate | 419,593 structures | sub-units | the building profile and the driver's destination |

Sector numbers carry the region in their first digit (1 Bissau, 2 Bafatá, 3 Bolama, 4 Biombo, 5 Cacheu, 6 Gabú, 7 Oio, 8 Quinara, 9 Tombali), so `62` reads as "Gabú region, Gabú sector". Bissau is `10`, with 11-19 reserved: if the city is ever split into districts, those districts can have their own numbers without touching anyone else. By coincidence, this matches the paper postcode `1000 BISSAU`.

## 5. Place words

### 5.1 Which layer

- **Bissau**: bairros (OpenStreetMap `place=suburb/neighbourhood`) plus the old villages inside the sector that the city has absorbed and that are bairro names today (Plaque, Jal, Bono, Quetene, Cuntum ...). Never "Bissau" itself, which would mean nothing inside Bissau.
- **Elsewhere**: towns and their bairros, villages and hamlets (OpenStreetMap), then GeoNames localities that OpenStreetMap lacks. The place table has 4,221 places; 3,336 are the nearest place of at least one compound.
- A compound takes the **nearest place in its sector and on its land mass** within 3 km. The 5,430 compounds more than 3 km from any named place (in 37 sectors) take the sector's name as their word ("Boé 12") until a nearer place is named.

### 5.2 Same name in many places: one national number range per name

Guinea-Bissau repeats place names everywhere: there are Bandims in Bissau and in Catió, and homes in fourteen places called Missirá and thirteen called Áfià. The code people remember must therefore be **unique in the whole country on its own**. It must never need the town, the sector, the island or the phone's position to tell two places apart. A design that showed the sector beside a repeated word and put the nearer place first was considered and rejected: a code that depends on context fails exactly when it travels, read over the phone, written on a parcel or typed far from the place.

**What counts as the same name.** Two words are the same name when their *name key* is the same (SPEC 5.1.1). The key folds:

- letter case, accents and the cedilla (Gabu/Gabú, Quelele/Quelêle, Bissorã/Bissora);
- hyphens and spaces (Santa-Luzia/Santa Luzia);
- articles and the small words *de, da, do, dos, das, e*, and a leading "Bairro", "Tabanca", "Aldeia" or "Povoação" (with or without *de*) and "Morança" (Bairro de Ajuda/Ajuda, Morança Atufa/Atufa);
- the plate-name abbreviations *Sto, Sta, S., N. Sra* (Sto António/Santo António);
- Portuguese, Kriol and French spellings of one sound: *tch/ch/x*, *qu/c/k* with final *-que = -ck*, *ç/s/z*, *y/i*, *w/u*, a silent *h*, double letters, and the Kriol vowel spellings *o/u* and *e/i*. So Sintchã Dulo = Sinchã Duló = Sincha Dulu, Plack = Plaque, Áfià = Hafia, Quinhamel = Kinhamel, Contuboel = Kontuboel.

A numeral that people say as part of the name is kept, as a Roman numeral. People already say "Plack I / Plack II" at the edge of Bissau, and OpenStreetMap has "Plack II" in Safim: that is a name of its own, apart from "Plaque", and "Plaque 2" is the same name as "Plack II". The key errs towards merging. Two different names folded together only share a range, which can make some numbers longer. Two spellings of one name left apart would make "X 15" ambiguous, so that error is the one to avoid.

**One range, frozen blocks.** All areas with one name key draw their numbers from **one national range for that name, 1 to 99,999**, cut into blocks. An area is a place word, or a sector word used for compounds far from any place.

- Each area gets a block when its first code is issued. The block's size is the smallest of 10, 20, 50, 100, 200, 500, 1,000 ... 50,000 that holds **four times its compounds at issue**. The stride-2 first issue fills half of it, and as many new compounds again fit before the block is full.
- Blocks are laid out largest area first, so most homes keep the shortest numbers. Each block starts at a round number. Bandim: the Bissau bairro (452 compounds) has 0-1,999 and its homes are "Bandim 1" to "Bandim 903". The tabanca in Catió (27 compounds) has 2,000-2,199, so its homes are "Bandim 2001" to "Bandim 2053".
- A repeated name inside one sector is handled the same way: two areas, two blocks. No Roman numeral is invented to tell them apart; doing so would have created 297 numerals that nobody says.
- **Stability.** Blocks are frozen when issued and never renumbered, moved or shrunk. A new area with an existing name gets the next block above the name's high-water mark (the end of its last block). So does a place whose block fills: its earlier numbers stay, and its new numbers continue in the new block.
- The block table is `model/name-ranges.json`. It ships with the place table, so a phone resolves "Missira 5001" to Sonaco with no network.

So "Name NNNN" decodes to exactly one area and one compound anywhere in the country. Bandim 275 is in Bissau and Bandim 2001 is in Catió, and nobody has to say which.

**The extra parts are labels.** The island shown with a Bijagós code ("Ambeduco 23 · Orango", section 7) and the sector the app shows beside an address are display only. They are never needed to decode, and a code is never different with or without them.

**The real counts** (place table with plate names, machine-grouped compounds, `model/name-ranges.json`; in brackets the same count with the official names as words, before plate names):

| | Count |
|---|---|
| Name keys in the place table (4,221 places + 39 sector words) | 3,295 (3,477); 577 of them are shared by two or more entries (1,542 entries) |
| Names in use (an area with at least one compound) | 2,704 (2,815), across 3,336 areas |
| **Names shared by two or more areas in use** | **407 names in 1,039 areas** (335 in 856), holding 92,745 compounds (38 % of all; 33 % with the official names) |
| of which repeated inside one sector | 183 names (137) |
| Most areas per name | Missirá 14; Áfià/Afia/Hafia 13; Madina 12; Amedalai 11; Ponta Nova 10; Darsalame 9; Bambadinca 8 (3 of them flagged); Dando 8 |
| **Largest shared range** | **Áfià: 13 areas, 2,560 compounds, blocks 0-15,719: five digits** (unchanged) |
| Top of the range of each shared name | 2 digits: 21 names; 3 digits: 261; 4 digits: 115; 5 digits: 10 |
| Names whose blocks would pass 99,999 | none |

**Lengths, before and after.** These are the digits of each area's highest number at first issue. With no shared ranges: 1 digit 401 areas, 2 digits 1,846, 3 digits 1,010, 4 digits 79. With national ranges and plate names: 277, 1,488, 1,237, 309, and 25 areas with 5 digits (with the official names as words it was 305, 1,536, 1,192, 282 and 21). By compound, 731 have 1 digit, 35,890 have 2, 111,322 have 3, 90,233 have 4 and 3,497 have 5. The mean goes from 3.14 to 3.25 digits (3.23 with the official names). These lengths are those of each area's highest number; the numbers actually issued are shorter, 2.85 digits on average (paper, section 6.4).

- Bissau's confirmed place words do not change. 10 of its 49 place words share a name; the two that get five digits, Bambadinca Balanta and Cuntum Madina, are flagged for the Câmara because their provisional plate names (Bambadinca, Cuntum) belong to bigger areas.
- Of the 1,039 shared areas, 449 keep their length, 336 gain one digit, 215 two, 36 three and 3 four.
- The 21 five-digit areas with a confirmed plate name are the same as before plate names: Áfià's 11 smaller tabancas and the second areas of names whose first area is a big town (Bafatá: Mansabá's Bafatá and the Bafatá sector word; Buba, Bissorã, Quebo, Jal, Pefiné and Embalocunda). The other 4 are flagged areas.

**Qualifiers.** No name in Guinea-Bissau needs one today: the largest range, Áfià's, ends at 15,719. If a name's blocks would ever pass 99,999, its areas take one established qualifier that people already say, decided once per name and listed in `model/name-ranges.json` (`qualifiersNeeded`, empty today). That would be the ethnic or family qualifier of the tabanca, as the official names "Bambadinca Balanta" and "Bambadinca Mancanha" have it, in a form that fits the plate-name limit (section 5.4). The qualified name is then a name of its own, with its own range.

### 5.3 Spellings, renaming

- Named moranças are said by the family name: "Morança Atufa" becomes the word **Atufa**, with the long form as an alias.
- Spellings vary (Plack/Plaque, Quelele/Quelêle, Gabu/Gabú, Bissorã/Bissora). Every variant with the same name key gives the same code. Other variants, such as old names, are aliases.
- A disputed or renamed bairro never changes a code. The compound keeps the place it was issued in. The new name becomes an alias that finds it, and it does not get a range of its own.

### 5.4 Plate names

Many official names are too long to remember with a number: 746 of the 4,221 places are over 12 characters or 2 words ("Sinchã Samba Camarà", "Ponta Manuel das Águas", "Bambadinca Balanta"). Every area therefore has a **plate name**: at most 12 characters (every letter, space, hyphen or apostrophe counts one; an accented letter is one) and at most 2 words (*de, da, do* and the other small words do not count; a hyphen separates words). The remembered code is the plate name and the number ("Malam Baio 15", "Bandim 275"). The **official name** is kept as well. It is printed in small type on the card and the plate when it differs, for context only; nobody has to say it. Typed, it still finds the area when it points to one plate name only.

How the plate name is made (`tools/gw_plates.py`, with the rule in `engine/reference/plate_names.py`; exact steps in SPEC 5.1.2):

1. A short form people already say, documented with a source, wins. None is asserted yet: the Câmara's bairro list is the expected source for Bissau.
2. Clean: drop "Bairro de", "Tabanca de", "Morança"; a leading "Tabanca" before a real name; text in brackets ("Sucuta (Madina Fali)" → Sucuta); text after a slash; generic words (Bairro, Zona, Phase ...: "Bairro Ajuda II Phase" → Ajuda II). A generic word stays when what is left is not a name on its own ("Zona Sete", "Tabanca Nova").
3. If it fits, that is the plate name. A saint prefix may be abbreviated (Sto, Sta, S.): "Santo António" → Sto António, and the full form typed still decodes.
4. Otherwise the most distinctive run of one or two whole words is taken, with a preference for the end of the name, and never a word cut in two: "Sinchã Malam Baio" → Malam Baio, "Nhabijão Bulobate" → Bulobate, "Ilha de Orango" → Orango.

Guinea-Bissau's own word lists decide what may be dropped. *Sinchã/Sintchã* ("founded by", Fula), *Sare* ("village of"), *Madina*, *Gã*, *Ponta* (a farm concession named after its holder, also written "P."), *Barraca*, *Ilha* and *Ilhéu* are settlement words: the first to go, never a plate name alone. The peoples a tabanca is named after (Balanta, Mancanha, Papel, Fula, Mandinga, Beafada, Nalu, Manjaco ...) are qualifiers. A short form that drops one is never taken automatically, because "Bambadinca Balanta" and "Bambadinca Mancanha" are two villages.

**When the machine does not choose.** An area is flagged for the council (`needsCouncilChoice`, with up to 3 candidates and the reason) when no short form is clearly best, or when the best one would:

- drop a qualifier or the end of the name ("Cuntum Madina" → Cuntum, "Chão de Papel" → Chão);
- keep only a founder's given name ("Sinchã Mamadu" → Mamadu);
- equal a sector seat, a region capital or a big city of the region (Bambadinca, Bolama, Ziguinchor ...; a place may carry the name of its own sector's seat);
- or come from a name with a number in it ("14 de Novembro").

544 places are flagged, 356 of the 3,336 areas in use. The first candidate is the provisional plate name, and the flagged area's block comes after the confirmed areas of its name. Every compound in a flagged area has its code, issued with the provisional plate name (21,759 codes in the 356 flagged areas in use). The council chooses the final plate name: the Câmara Municipal in Bissau, elsewhere the sector administration with the régulos and the community. The number never changes. 28 areas in use have no candidate that fits ("Ponta José da Silva", "Madina Mandinga", "Tabanca Bijagos", "Bambadincazinho") and keep their cleaned name provisionally, over the limit; the engine refuses such a word for any area not flagged.

**Results.** 3,474 places keep their name as it is, 17 are cleaned, 1 is abbreviated, 185 are shortened automatically and 544 are flagged (45 still over the limit). Shortening makes some different names one plate name: they then share one national range like any repeated name ("Ama Seidi 1" is in Gabú, "Ama Sidi 1001", official name Missirá Ama Sidi, in Farim). Names shared by two or more areas in use go from 335 to 407, and five-digit areas from 21 to 25 (the 4 new ones are flagged). The longest remembered code with a confirmed plate name is "São Domingos 6027" (17 characters).

**Aliases.** The official name and the source's other spellings stay aliases. An alias that is itself another area's plate name, or that two plate names would claim, is dropped as an alias and listed under `aliasesDropped` in `model/places.json` (8 places; for example "Sintchã Demba" and "Sinchã Demba" are official names of two places with different plate names, so neither decodes as an alias).

## 6. Spot codes

Any point in a sector has a spot code, computed on the phone with no network: `SS-DDDD-DDDD`, the sector's 10,000 × 10,000 grid with the two coordinates' digits interleaved. Cells follow the settlement pattern, because sectors were drawn small where people are many: **1.7 m in Bissau**, 2.0-3.2 m in Biombo's peri-urban sectors, 3.7-7.7 m in most rural sectors, 8.1 m in Boé and 9.4 m in Gabú. Where that is too coarse (a market stall, a landing beach), a ninth digit picks one ninth of the cell, laid out like a phone keypad with 1 2 3 on the north row. Spot codes are for places with no compound: a stall at Bandim, a meeting point at a *lumo* (weekly market), a fishing landing at Cacheu. They are shared as links, not remembered.

## 7. Islands: the Bijagós and others

The Bolama region is an archipelago of some 88 islands and islets (189 island and islet polygons in OpenStreetMap, including Ilha de Bissau and Ilha do Rei), and boats are the only link between many of them. A compound on an island only ever takes a place word on the same island, so an Orango home is never numbered as if it were on Bubaque. Its address shows the island ("Ambeduco 23 · Orango") as a label; the code is unique without it (section 5.2). Komo (Tombali) and the Cacheu islands (Jeta, Pecixe) follow the same rule. Ilha de Bissau counts with the mainland, because a road links them.

## 8. Building profile

Every structure and compound carries a profile (schema in SPEC 8). Its use classes are Guinea-Bissau's own: the *casa de morança*, the round *palhota*, the kitchen or granary annex, Bissau's single houses and few apartment blocks, *loja*, *barraca*, the markets (Bandim, Caracol) and the eastern *lumo*, cashew warehouses, fish-smoking sheds in the Bijagós and Cacheu, mosques and churches, and the *baloba* (a sacred house of traditional religion). A *baloba* is stored but never published without the community's agreement.

### 8.1 How attributes are inferred, and how sure we are

| Signal | Share of footprints it decides (country) | Confidence |
|---|---|---|
| OpenStreetMap tags (amenity, shop, building=school/mosque/...) and N-Ways places at the footprint | 3,567 (0.85 %) | 0.65-0.90 |
| Enclosure kind (school, hospital, military, market site) | part of the above | 0.55 |
| Round shape (circularity ≥ 0.9, OpenStreetMap outlines only) | 1,469 round houses | 0.60 |
| Small annex beside a main house | 37,222 | 0.45 |
| Large, use unknown (≥ 600 m²) | 1,012 | 0.30 |
| Default: compound house | the rest (375,096) | 0.50-0.65 |

Mean confidence is 0.55 country-wide and 0.51 in Bissau. The honest reading: today the map knows *that* almost every structure is a home or a home's annex, *where* it is, and *how big* its footprint is. It rarely knows what a non-residential building is for, and it almost never knows height. Only 82 buildings have `building:levels` in OpenStreetMap. The height column of the machine-learned footprint files is a rendering placeholder (3.5-7 m derived from the footprint's identifier), so the model never uses it. Floors and floor area stay *unknown* until OpenStreetMap, the household or a partner says.

### 8.2 Sample statistics

| Region | Structures | Compounds | In multi-structure compounds | Median footprint |
|---|---|---|---|---|
| Bissau (GW-BS) | 69,255 | 43,850 | 57.9 % | 167 m² |
| Bafatá | 60,980 | 34,427 | 67.6 % | 109 m² |
| Bolama-Bijagós | 14,157 | 7,974 | 66.1 % | 69 m² |
| Biombo | 36,224 | 21,852 | 61.0 % | 152 m² |
| Cacheu | 62,777 | 35,431 | 67.2 % | 119 m² |
| Gabú | 73,519 | 43,414 | 66.1 % | 41 m² |
| Oio | 56,783 | 29,493 | 70.9 % | 132 m² |
| Quinara | 17,011 | 9,131 | 67.7 % | 138 m² |
| Tombali | 28,887 | 16,101 | 67.3 % | 108 m² |

Structures, compounds and shares are counted in the registry (each code's `structures`, by the region digit of its sector number); the median footprint, and the counts by use class below, come from `model/building-stats.json`.

Bissau in detail: 63,288 compound houses, 4,382 annexes, 411 large buildings of unknown use, 278 industrial (the port and the industrial zone), 164 education, 127 military, 112 office, 92 hospitality, 73 shops, 37 market, 38 under construction. Compounds: 43,520 residential, 176 mixed (home and shop), 64 commercial, 35 hospitality, 18 education, 15 religious. Compounds group 1.58 structures on average (90th percentile 3). Footprint area: median 167 m², 90th percentile 299 m².

### 8.3 How people and partners correct it

- In the app, anyone at a building can answer one question at a time ("Is this a shop?", "Are these one home?", "Where is the gate?"). Three agreeing answers, or the same household twice, settle it without manual review.
- Arrivals and deliveries confirm gates and keep `lastConfirmed` fresh.
- Partners (couriers, health programmes, utilities, cashew buyers) can send attribute corrections through the partner API. Each carries the partner as its source, and people's answers can overturn it.
- A business or a public institution can publish its building's name. A home's occupants are never asked for.

## 9. Add my home

Guinea-Bissau builds fast at the edges of Bissau and the towns, and no footprint map can keep up, so a family with a new home makes its own code:

1. **At the gate**: the phone averages GPS for 10-20 seconds; one photo of the gate.
2. **The plot**, one of three ways: tap the corners on satellite imagery; walk the boundary inside the wall with the camera (AR tracking gives the shape to centimetres, GPS averaged over the walk anchors it, and it is checked against imagery and nearby footprints, because phone GPS alone is 3-10 m off); or type or photograph the beacons of a survey plan.
3. **Describe it**: households, structures, floors, use.
4. **A provisional code at once**: the next free number of that place in the curve's order (SPEC 7.2), so it can go on the gate the same day.
5. **Confirmed** by three arrivals or deliveries, no dispute from a neighbour, or new imagery matching the outline.

Safeguards: overlaps with an existing compound are flagged, never issued. The gate must be on the outline, the size plausible and the loop closed, and the AR and GPS tracks must agree. Only the outline and the gate photo are kept (no video, no interior). Offline, the spot code shows at once and the compound code comes from the registry on the next connection. The registry is the single source of codes, so no two homes can share one.

**Land.** Under the Lei da Terra (Lei n.º 5/98), land in Guinea-Bissau belongs to the State. Communities hold customary use rights, and private use is by concession. Most compounds outside Bissau stand on customary land. Cadastre and concessions are held, mostly on paper, by the Direcção Geral de Geografia e Cadastro (DGGC); there is no public parcel map. Survey plans use the *Bissau* datum (Bissau / UTM zone 28N, EPSG:2095) or WGS 84 / UTM 28N from GNSS, and the app asks which before accepting beacons, because the two differ by tens of metres. The flow says plainly: **a code is an address, not a land title**, and it proves nothing about who owns or may use the land. *Unverified:* the land law's implementing regulation and current cadastre coverage (the sources could not be reached when this was checked on 18 October 2026).

## 10. Privacy

Guinea-Bissau has no personal-data-protection law or authority (re-checked 2026-10-18; see existing-systems.md). The ECOWAS Supplementary Act A/SA.1/01/10 applies in principle, and an Electronic Transactions bill went to public consultation in May 2026. The model therefore protects people by design, not because a regulator asks:

- Codes describe places, never people. Residential profiles carry no occupant data: no names, phone numbers, household members or photos of people or interiors. "Households" is a count, given only by the household itself, and is published only in aggregate.
- Published: codes, outlines, footprint size, use class (except shrines), gates, the names of businesses and public buildings, status.
- Private: a home's doors on request (the compound code and gate stay), gate photos (kept to confirm, not published), the Add-my-home description.
- A partner can look up a customer's code only with that customer's consent (the customer shares it, or approves the lookup in the app).
- Military and police compounds keep their code and outline (both already on the public map) but no structure profiles.
- When Guinea-Bissau adopts a data protection law, its rules replace these where they are stricter.

## 11. Governance

N-Ways maintains the model and can hand it over whole: to INE, to the Câmara Municipal de Bissau for sector 10 alone, or to Correios. The arrangement rests on technical institutions and on agreements that outlast changes of government, because an address register must stay stable for decades. Details are in [GOVERNANCE.md](../GOVERNANCE.md).

## 12. Refinements with the institutions

The codes are issued. These steps refine them with the institutions concerned; none of them renumbers a code.

1. The Câmara Municipal de Bissau's bairro list (merging, splitting and naming the 72 Bissau place words, and choosing the plate names flagged in Bissau, such as Militar for Bairro Militar), and its answer on door numbering in central Bissau (coverage mask).
2. The plate names flagged for the council elsewhere (356 areas in use), chosen with the sector administrations and the régulos.
3. INE: comparing machine-grouped compounds with the 2026 census's georeferenced dwellings and households, if INE agrees.
4. A wall and gate pass on imagery for the evaluation bairros.
5. Native-speaker review of the Kriol readings and of the name-key folding rules. `sectors.json`, `places.json`, `name-ranges.json` (name keys, national name numbers and blocks) and the coverage mask were frozen at the first issue, so a folding change may only merge keys by alias, never split a range.

## 13. Field evaluation and memorability test

The field evaluation runs in three Bissau bairros (Bandim, Bairro Militar, Cuntum) and one tabanca cluster in Biombo or Oio:

- **Recall**: one week and four weeks after a household gets its plate, ask (in Kriol) for the home's code without looking. Target: 80 % correct after four weeks.
- **Entry errors**: spoken (to a driver on the phone), typed in the app, and handwritten on a parcel, scored against the registry. Each one is counted separately when it lands in another area of the same name, which the check digit should reduce to zero.
- **Shared names**: whether people in a tabanca that shares its name with a bigger place (Bandim in Catió: "Bandim 2001") remember the longer number as well as a short one.
- **Format comparison**: in a sample of households, offer the remembered form, a digits-only form (`10-022-00275`) and an alphanumeric grid code for the same home; measure recall and errors for each.
- **Use**: first-time delivery success and time from the lane to the gate, with and without a code.
