# Licensing

N-Ways Addressing for Guinea-Bissau is open. Build on it, and credit N-Ways.

| Part | Licence | File |
|---|---|---|
| Code: the engine, the registry server and the tools (`engine/reference/`, its test vectors, `server/`, `tools/`) | Apache License 2.0 | [LICENSE](LICENSE), [NOTICE](NOTICE) |
| Data: the registry, sectors, island outlines, place list and model (`registry/`, `model/`, `engine/data/`, and the test fixture `server/testdata/`) | Open Database License (ODbL) 1.0 | [LICENSE-DATA](LICENSE-DATA) |
| Documents: the paper, the model notes, the API reference and the review of existing systems (`docs/`), and this repository's other Markdown files | Creative Commons Attribution 4.0 (CC BY 4.0) | [LICENSE-DOCS](LICENSE-DOCS) |

Licensor: **N-WAYS LIMITED** (nways.ng). Source: https://github.com/n-ways/open-addresses-guinea-bissau

## How to credit N-Ways

Copy the line that fits. Link it to https://github.com/n-ways/open-addresses-guinea-bissau where you can.

**An app, a website or an API that shows, decodes or issues these addresses:**

> Codes by N-Ways Addressing · © N-WAYS LIMITED (nways.ng)

Put it next to the address, or on the screen that shows it, and in your about or licences screen. If you ship or change the engine, also keep [NOTICE](NOTICE) (Apache 2.0, section 4(d)).

**A map, a dataset or a database built from the data:**

> © N-WAYS LIMITED, N-Ways Addressing; contains OpenStreetMap data © OpenStreetMap contributors (ODbL) and the other sources in SOURCES.md

A database you make from it and share is shared under ODbL 1.0 too (share-alike). A map image or a printed plate made from it is a "produced work": it carries the line above, and needs no share-alike.

**A paper, an article, a slide or a translation that uses the documents:**

> N-Ways Addressing for Guinea-Bissau, © N-WAYS LIMITED (nways.ng), CC BY 4.0. https://github.com/n-ways/open-addresses-guinea-bissau

Say what you changed, if you changed anything.

## Sources inside the data

The data is built from open sources (full list in [SOURCES.md](SOURCES.md)). Their own terms travel with it, and the data credit above names them:

| Source | Licence | What you owe it |
|---|---|---|
| OpenStreetMap (buildings, places, gates and enclosures derived from it) | ODbL 1.0 | "© OpenStreetMap contributors"; share-alike, which is why the data is ODbL |
| Microsoft building footprints, via Overture Maps | ODbL 1.0 | credit Microsoft and the Overture Maps Foundation |
| Google Open Buildings, via Overture Maps | CC BY 4.0 | credit Google and the Overture Maps Foundation; compatible with redistribution inside an ODbL database |
| OpenStreetMap administrative boundaries, the source of the 39 sector outlines, and its island outlines | ODbL 1.0 | "© OpenStreetMap contributors" |
| GeoNames (localities) | CC BY 4.0 | credit GeoNames (geonames.org) |
| N-Ways places (used only to classify buildings: OSM, Overture, Foursquare OS Places, All The Places) | per source (ODbL, CDLA-Permissive-2.0, Apache-2.0, CC0) | only categories are used, no place records are redistributed |

**Postcodes.** Guinea-Bissau's postcodes exist on paper only (UPU, 2005); `1000`, the one attested for Bissau, is shown beside codes in the Setor Autónomo de Bissau as context.

**Official addresses.** Guinea-Bissau has no official door-level address. If the Câmara Municipal, Correios or a national programme publishes one, it is shown first and the codes map to it (engine/SPEC.md section 12). Official data keeps its own terms. Both licences above let the state relicense or republish the registry if it adopts it.

**Personal data.** The registry holds places, never people: no names, telephone numbers or household details (docs/model.md section 10).

## Trademarks

"N-Ways" and the N-Ways logo are trade marks of N-WAYS LIMITED. The licences above cover the code, data and documents, not the marks: you may say your product uses N-Ways Addressing, but not that it is N-Ways or is endorsed by N-Ways.
