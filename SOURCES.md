# Sources

Every source used for the Guinea-Bissau model, with the date it was read. Access date 2026-10-18 unless stated. Sources marked "N-Ways" are N-Ways' own map data and research notes, which are not public; everything derived from them that the model uses is published in this repository.

## Postal and address systems

| # | Source | URL | Used for |
|---|---|---|---|
| 1 | UPU, *Guinea-Bissau: postcode* addressing sheet (03/2005) | https://www.upu.int/UPU/media/upu/PostalEntitiesFiles/addressingUnit/gnbEn.pdf | 4-digit postcode left of the locality; examples `1000 BISSAU`, `1011 BISSAU` (Direcção Geral dos Correios) |
| 2 | Correios da Guiné-Bissau (Wikipedia) | https://en.wikipedia.org/wiki/Correios_da_Guin%C3%A9-Bissau | state postal company, UPU member since 30 May 1974 |
| 3 | `correios.gw`, `www.correios.gw` | https://correios.gw/ | do not resolve (DNS), 2026-10-18 |
| 4 | GeoNames postal-code downloads | https://download.geonames.org/export/zip/ | no `GW.zip` listed |
| 5 | Smarty, Guinea-Bissau address format | https://www.smarty.com/global-address-formatting/guinea-bissau-address-format-examples | commercial guide repeating format 9999 (not authoritative) |
| 6 | CDQ data model, GW address | https://meta.cdq.com/DataModel:CDQ/Business_Partner/Address/Country/GW | commercial validation rule "NNNN" (not authoritative) |
| 7 | N-Ways country research notes on Guinea-Bissau (addresses, regions, data protection, gaps), last checked 2026-10-17 | N-Ways | prior findings, regions and governors, data protection status |
| 8 | OpenStreetMap, Geofabrik extract `guinea-bissau-latest.osm.pbf` of 2026-10-17 | https://download.geofabrik.de/africa/guinea-bissau.html | sectors (admin_level 6), islands, place nodes, walls, fences, farmyards, gates; house-number count (2); the national border, relation 192776 (admin_level 2), read whole from an extract of the region's boundary relations of 2026-10-20 (`engine/data/border.geojson`) |

## Government, census, land

| # | Source | URL | Used for |
|---|---|---|---|
| 9 | Lusa via Correio da Manhã Canadá, 22 Jun 2026, "Guiné-Bissau prolonga por cinco dias recenseamento" | https://www.correiodamanhacanada.com/guine-bissau-prolonga-por-cinco-dias-recenseamento-da-populacao-e-habitacao/ | 4th RGPH extended to 26 June 2026; 2,213,173 people, >600,000 dwellings, ~301,000 households counted by 22 June (INE) |
| 10 | Forbes África Lusófona, "Guiné-Bissau anuncia início do Recenseamento Geral da População e Habitação para Junho" | https://forbesafricalusofona.com/guine-bissau-anuncia-inicio-do-recenseamento-geral-da-populacao-e-habitacao-para-junho/ | census 1-21 June 2026 |
| 11 | Forbes África Lusófona, "Guiné-Bissau realiza quarto recenseamento em 2025" | https://forbesafricalusofona.com/guine-bissau-realiza-quarto-recenseamento-em-2025/ | earlier plan; georeferencing of dwellings announced |
| 12 | Geocracia, 1 Oct 2026, "Nova lei redefine a base territorial dos projetos na Guiné-Bissau" | https://geocracia.com/nova-lei-redefine-a-base-territorial-dos-projetos-na-guine-bissau/ | Lei n.º 14/2026 of 24 July (land-use and urban planning), in force 22 Oct 2026 |
| 13 | Portugal Global (AICEP), Sept 2026, "Guiné-Bissau aprova nova lei de ordenamento territorial" | https://portugalglobal.pt/noticias/2026/setembro/guine-bissau-aprova-nova-lei-de-ordenamento-territorial/ | cited by 12; not opened |
| 14 | World Bank, *Guinea-Bissau: Land Tenure Issues and Policy Study* | https://openknowledge.worldbank.org/entities/publication/c3b875d2-d37a-5b49-9aef-4b56451e4449/full | cadastre recommendation (search snippet only; page refused the fetch, 403) |
| 15 | Lei n.º 5/98, Lei da Terra, of 23 April 1998, Boletim Oficial n.º 43 (supplement), 28 April 1998, pp. 41-53 (FAOLEX record, via UNEP LEAP; read 2026-10-21) | https://leap.unep.org/en/countries/gw/national-legislation/land-act-no-598 | State land, use by concession or authorisation; customary use rights; the implementing regulation is **unverified** |
| 16 | EPSG:2095, Bissau / UTM zone 28N | https://epsg.io/2095 | national datum *Bissau*, International 1924 ellipsoid, onshore Guinea-Bissau |
| 17 | UK PCGN, *Guinea-Bissau toponymic factfile* | https://www.ecoi.net/en/file/local/2136422/Guinea-Bissau_toponymic_factfile.pdf | 39 ADM2 units; DGGC as source of SALB boundaries (search snippet) |
| 18 | Wikipedia, *Sectors of Guinea-Bissau* | https://en.wikipedia.org/wiki/Sectors_of_Guinea-Bissau | sector list by region (incl. Komo) |
| 19 | geoBoundaries GNB ADM2 (gbOpen, from OpenStreetMap/Wambacher, ODbL) | https://www.geoboundaries.org/api/current/gbOpen/GNB/ADM2/ | cross-check: 39 units |

## Languages, literacy, telephony

| # | Source | URL | Used for |
|---|---|---|---|
| 20 | Wikipedia, *Languages of Guinea-Bissau* (2009 census table) | https://en.wikipedia.org/wiki/Languages_of_Guinea-Bissau | Kriol 90.4 %, Portuguese 27.2 %, Fula 25.7 %, Balanta 19.7 %, Mandinka 12.8 %, Papel 7.4 %, Manjak 7.3 %, French 5.1 % |
| 21 | APiCS, *Guinea-Bissau Kriyol* survey | https://apics-online.info/surveys/33 | Kriyol as the lingua franca |
| 22 | The Global Economy / FRED (UNESCO series), adult literacy | https://fred.stlouisfed.org/data/SEADTLITRZSGNB | adult literacy 63.9 % (2022) |
| 23 | World Bank, World Development Indicators: adult literacy, male and female (SE.ADT.LITR.MA.ZS, SE.ADT.LITR.FE.ZS) | https://data.worldbank.org/indicator/SE.ADT.LITR.FE.ZS?locations=GW | adult literacy 77.3 % men, 52.2 % women (2022): a 25.2-point gap |
| 24 | Wikipedia, *Telephone numbers in Guinea-Bissau* | https://en.wikipedia.org/wiki/Telephone_numbers_in_Guinea-Bissau | nine-digit national numbers, mobile 95x/96x |
| 25 | Spanish Embassy in Bissau, 2015 notice | https://www.exteriores.gob.es/Embajadas/bissau/es/Comunicacion/Noticias/Paginas/Articulos/201506_Not9.aspx | change to nine digits from November 2015 |

## Data protection

| # | Source | URL | Used for |
|---|---|---|---|
| 26 | ARN-TIC national legislation page (read 2026-10-17) | https://arn.gw/nacionais/ | no personal-data law listed |
| 27 | DLA Piper, *Data Protection Laws of the World* | https://www.dlapiperdataprotection.com/?t=law&c=GW | no Guinea-Bissau entry |
| 28 | *Res Severa Verum Gaudium* (UFRGS), 2026 article on PALOP data laws | https://seer.ufrgs.br/index.php/resseveraverumgaudium/article/download/156585/99905/713990 | Guinea-Bissau without a specific law (snippet) |
| 29 | ECOWAS, workshop on the revision of Supplementary Act A/SA.1/01/10 (21 Oct 2024) | https://www.ecowas.int/ecowas-online-workshop-on-the-review-of-the-preliminary-draft-of-the-re-vised-supplementary-act-a-sa-1-01-10-on-personal-data-protection-within-ecowas/ | Act and its review |
| 30 | O Democrata, ARN-TIC Aviso 01/CA/ARN/2026 (8 May 2026) | https://www.odemocratagb.com/?p=57171 | public consultation on the Electronic Transactions bill (Projeto de Lei das Transações Eletrónicas) |

## Map data and methods

| # | Source | Where | Licence |
|---|---|---|---|
| 31 | OpenStreetMap buildings of Guinea-Bissau, as extracted for the N-Ways map (100,458 footprints) | N-Ways, from OpenStreetMap | ODbL |
| 32 | Machine-learned building footprints of Guinea-Bissau (324,642): Google Open Buildings and Microsoft, via Overture Maps | N-Ways, from Overture Maps | CC BY 4.0 / ODbL |
| 33 | N-Ways' preparation of the footprint files | N-Ways | shows that their height column is a rendering placeholder (3.5-7 m) |
| 34 | N-Ways places in Guinea-Bissau (2,207 points of interest: OpenStreetMap, Overture Maps, Foursquare OS Places, All The Places) and its gazetteer (OpenStreetMap places, GeoNames localities) | N-Ways | per source: ODbL, CDLA-Permissive-2.0, Apache-2.0, CC0, CC BY 4.0 |
| 35 | Compounds and gates from the N-Ways routing build | N-Ways, from OpenStreetMap | ODbL |
| 36 | H. M. Damm, *Total anti-symmetrische Quasigruppen*, PhD thesis, Philipps-Universität Marburg, 2004 | — | check digit |
| 37 | Open Location Code specification | https://github.com/google/open-location-code | comparison (Apache-2.0) |
| 38 | Hilbert, D. (1891), "Ueber die stetige Abbildung einer Line auf ein Flächenstück", *Math. Annalen* 38 | — | ordering curve |

## Literature cited in the paper

The paper's bibliography is `docs/paper/references.bib`; every entry there was checked against its publisher, catalogue or web page on 21 October 2026. Besides the sources above, it cites:

| Source | Used for |
|---|---|
| UPU, *International Postal Address Components and Templates*, standard S42 | international address format standard |
| UPU, *Addressing the World: An Address for Everyone* (2012) | addressing as public infrastructure |
| C. Farvacque-Vitkovic et al., *Street Addressing and the Management of Cities*, World Bank (2005) | street-naming share, cost per doorway, benefits for local government |
| W. Sirko et al., "Continental-Scale Building Detection from High Resolution Satellite Imagery", arXiv:2107.12283 (2021) | Google Open Buildings |
| Microsoft, Global ML Building Footprints (GitHub) | Microsoft footprints |
| Overture Maps Foundation, buildings theme | distribution of the machine-learned footprints |
| H. M. Damm, "Totally anti-symmetric quasigroups for all orders n ≠ 2, 6", *Discrete Mathematics* 307(6), 715-729 (2007), doi:10.1016/j.disc.2006.05.033 | check digit |
| J. Verhoeff, *Error Detecting Decimal Codes*, Mathematical Centre Tracts 29, Amsterdam (1969) | frequency of transcription errors |
| B. Moon, H. V. Jagadish, C. Faloutsos, J. H. Saltz, "Analysis of the Clustering Properties of the Hilbert Space-Filling Curve", *IEEE TKDE* 13(1), 124-141 (2001) | locality of the Hilbert ordering |
| M. P. Larsen et al., "Predicting survival from out-of-hospital cardiac arrest: a graphic model", *Annals of Emergency Medicine* 22(11), 1652-1658 (1993) | survival model, emergency chapter |
| N.-K. Mould-Millman et al., "The State of Emergency Medical Services (EMS) Systems in Africa", *Prehospital and Disaster Medicine* 32(3), 273-283 (2017) | coverage of emergency medical services |
| M. Hunt et al., "Challenges locating the scene of emergency: a qualitative study of the EMS system in Rwanda", *Prehospital Emergency Care* (2023) | delay in locating patients without addresses (precedent) |
| S. Odeloye, D. Onajobi, "Innovations in Last-Mile Delivery", NextBillion (15 May 2023) | cost of a delivery attempt, first-attempt success (industry estimate) |
| Locus, "How to reduce failed delivery attempts across the Middle East & Africa" (20 April 2026) | failed-delivery planning benchmark (industry estimate) |

## Not reachable or not verified

- The Lei da Terra's implementing regulation and the DGGC's current cadastre coverage could not be confirmed from a primary source (the World Bank page refused access); they are marked *unverified* wherever they are used. The law's number, date and publication are confirmed by the FAOLEX record (source 15).
- Kriol number spellings in docs/model.md follow common Kriyol orthography; to be checked with native speakers before any voice prompt is recorded.
- The Bissau bairro list (28 in OpenStreetMap) is incomplete; the Câmara Municipal de Bissau's official list was not found online.
- Plate names (docs/model.md 5.4): no documented short form of a Guinea-Bissau place name was found, so none is asserted (`KNOWN` in `tools/gw_plates.py` is empty) and every short form is derived by rule or left to the council. A short form is added there only with its source (a Câmara or sector list, a census locality list, a published map), and the source is then listed in this file. The meanings of the settlement words used by the rule (*Sinchã/Sintchã*, *Sare*, *Gã*, *Ponta*) follow common usage in the place names and are to be checked with native speakers with the rest of the Kriol and Fula wording.
