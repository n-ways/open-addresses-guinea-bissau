# Guinea-Bissau: existing postal and address systems

Reviewed on 18 and 20 October 2026 (web sources, N-Ways map data, OpenStreetMap extract of 17 October 2026). Every source is listed with its URL in [SOURCES.md](../SOURCES.md).

## Verdict

**Postal codes exist on paper only; there is no door-level or building-level address system, official or private.**

- Guinea-Bissau's postcode format is documented by the Universal Postal Union (UPU) as "4 digits to the left of the locality name". The UPU sheet is dated 03/2005 and shows only two codes, both in the capital: `1000 BISSAU` (the example address) and `1011 BISSAU` (the Direcção Geral dos Correios at the Estação Central). No list, directory, lookup or map of codes for any other locality exists anywhere we could find.
- The postal operator, Correios da Guiné-Bissau, has no working website: `correios.gw` and `www.correios.gw` do not resolve (checked 2026-10-18). Mail is delivered to P.O. boxes (Caixa Postal) or collected at the counter.
- GeoNames, the main open postal-code dataset, has no Guinea-Bissau file (its `export/zip` directory, checked 2026-10-18, lists no `GW.zip`). Commercial address-format guides (Smarty, CDQ) repeat the UPU "NNNN" format but give no codes beyond Bissau.
- In OpenStreetMap, which N-Ways uses for the map, only **2** buildings in the whole country carry a house number and **8** a street name (count over the 99,000 OpenStreetMap buildings in N-Ways' extract); two buildings carry an `addr:postcode` tag, and one of them is a P.O. box ("C.P. 1001"), not a postcode.
- No national addressing programme, street-naming or house-numbering project, or digital address app for Guinea-Bissau was found in 2024-2026 news or government sources. The nearest things are:
  - the **4th General Population and Housing Census (RGPH)**, run by the Instituto Nacional de Estatística (INE) from 1 to 26 June 2026 (extended by five days). Lusa reported 2,213,173 people counted, "more than 600,000 dwellings" and about 301,000 households as of 22 June 2026. Earlier announcements said the census would georeference the territory to locate dwellings. INE's enumeration maps are not public.
  - the **Lei de Ordenamento do Território e Urbanismo, Lei n.º 14/2026 of 24 July** (in force 22 October 2026), which sets a national framework for land-use planning. Press coverage says its effect depends on regulations and "cartographic instruments" still to come; it does not set up addresses.
- People describe places by **bairro** (district) and landmark in Bissau ("Bandim, perto do mercado"), and by **tabanca** (village) and **morança** (family compound) in the rest of the country. OpenStreetMap mappers record moranças as named places ("Morança Atufa", "Moransa Andunke" near Apurnia) and as `landuse=farmyard` outlines (782 of them).

**Consequence for the model:** there is no official door-level system to point to. The N-Ways model sits beside the paper postcode: a Bissau address prints `1000 BISSAU` on its postal line, as the UPU format asks, and other localities print the locality name with no number, because no other code is known. If Correios da Guiné-Bissau or the government publishes postcodes or an address register, N-Ways maps its codes to them (see [model.md](model.md), "Relation to postcodes").

## What exists, in detail

| System | Who | Level | State in 2026 | Open data |
|---|---|---|---|---|
| UPU postcode format `NNNN LOCALITY` | Correios da Guiné-Bissau / UPU | locality (only Bissau attested) | documented 2005; not used in practice | none |
| P.O. boxes (Caixa Postal, "C.P.") | Correios da Guiné-Bissau | box at a post office | in use | none |
| Street names | Câmara Municipal de Bissau (colonial and post-independence names in Bissau Velho, Plateau) | street | signs in central Bissau only; few in OpenStreetMap | OpenStreetMap (ODbL) |
| House numbers | none systematic | door | 2 in OpenStreetMap nationwide | — |
| Census enumeration areas, georeferenced dwellings | INE (RGPH 2026) | dwelling | collected June 2026, not published | none |
| Sector and region boundaries | Direcção Geral de Geografia e Cadastro (supplied to UN SALB); OpenStreetMap | admin units | 8 regions + Setor Autónomo de Bissau; 38 sectors | OpenStreetMap (ODbL); geoBoundaries (ODbL, from OSM) |
| Cadastre and land concessions | Direcção Geral de Geografia e Cadastro; land commissions under the Lei da Terra | parcel | partial, paper-based, mostly Bissau and concessions; not public | none |
| Plus Codes (Open Location Code) | Google (open algorithm) | 3 m cell | works offline anywhere | Apache-2.0 algorithm |

## Data protection

No national personal-data-protection law or authority was found (re-checked 2026-10-18: the telecom regulator ARN's legislation page lists ICT and radio laws only; DLA Piper's world survey has no Guinea-Bissau entry; a 2026 academic survey of Portuguese-speaking African countries' data laws treats Guinea-Bissau as having no specific law). Guinea-Bissau is bound in principle by the **ECOWAS Supplementary Act A/SA.1/01/10 on personal data protection (2010)**, which asks each member state to adopt a law and an independent authority; ECOWAS has been reviewing the Act since 2024. An Electronic Transactions bill went to public consultation in May 2026 (ARN-TIC notice 01/CA/ARN/2026). N-Ways therefore applies the ECOWAS Act's principles and the rules in [model.md](model.md), "Privacy". *Unverified:* the absence of a law is inferred from these sources, not from an official statement.

## Land and survey (relevant to "Add my home")

- **Lei da Terra, Lei n.º 5/98 of 23 April 1998**: land is State property; customary use rights of local communities are recognised; private use is by concession (urban and rural) registered with the land administration. Its regulation and the land commissions it foresees have been put in place slowly. *Unverified:* the date and number of the implementing regulation (no primary source for it could be reached on 18 or 21 October 2026).
- **Cadastre**: held by the Direcção Geral de Geografia e Cadastro (DGGC), mostly on paper, covering urban plots in Bissau and regional towns and some rural concessions. No public parcel map or API exists.
- **Datum**: the national geodetic datum is *Bissau* (International 1924 ellipsoid); the projected system is *Bissau / UTM zone 28N* (EPSG:2095). Survey plans (plantas topográficas) are drawn in it or, increasingly, in WGS 84 / UTM 28N (EPSG:32628) from GNSS. The two differ by tens of metres, so a typed beacon list must state its datum.
- **Customary land**: outside Bissau and the towns, most compounds sit on land held under customary rules (lineage and village authorities, the *régulo* / *homem grande*). A code says where a compound is; it never says who owns the land.

## What this means for N-Ways

1. No one is asked for a postcode; `1000 BISSAU` is printed only for the Bissau sector.
2. N-Ways codes are not presented as official addresses or postcodes. They are "endereços N-Ways".
3. The institutions to work with, in order: INE (census dwelling georeferencing is the closest official dataset; a code-to-census-area table helps both), Câmara Municipal de Bissau (street names, bairro list), Correios da Guiné-Bissau (postcodes, P.O. boxes), DGGC (sector boundaries, cadastre), ARN-TIC (the data protection provisions of the Electronic Transactions bill). See [GOVERNANCE.md](../GOVERNANCE.md).
