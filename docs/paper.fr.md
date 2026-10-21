---
title: "Un code pour chaque morança : un modèle national d'adressage pour la Guinée-Bissau"
short-title: "Adressage N-Ways pour la Guinée-Bissau"
kind: "Article de recherche"
author:
  - "The N-Ways Addressing Group"
affiliation: "N-WAYS LIMITED (nways.ng)"
date: "21 octobre 2026"
abstract-title: "Résumé"
abstract: |
  La Guinée-Bissau n'a pas d'adresse d'usage courant en deçà du nom d'une ville, d'un bairro ou d'une tabanca : un format de code postal à quatre chiffres a été enregistré auprès de l'Union postale universelle en 2005, mais seuls deux codes sont attestés, et deux bâtiments seulement portent un numéro dans la carte ouverte du pays. Nous présentons un modèle d'adressage dans lequel chaque concession (*morança* ou *quintal*) reçoit un code formé d'un nom de lieu que les habitants emploient déjà et d'un numéro court, par exemple *Bandim 537*. Les lieux qui partagent un nom tirent leurs numéros d'une plage nationale unique pour ce nom, divisée en blocs figés, de sorte que le code prononcé désigne un seul logement dans tout le pays, sans aucun qualificatif. Les numéros suivent une courbe de Hilbert, afin que des voisins reçoivent des numéros voisins ; un chiffre de contrôle de Damm protège la forme machine ; un code de point localise tout point hors ligne. Calculé à partir de 419 593 emprises de bâtiments, le modèle a attribué 241 673 codes dans 3 336 lieux et 39 secteurs. Nous donnons l'ensemble des mathématiques, une implémentation de référence, un registre ouvert et un serveur prêt à déployer, et nous mesurons sur le registre complet l'unicité, la longueur, la détection des erreurs et l'exactitude du décodage. Des chapitres distincts estiment les bénéfices pour les citoyens, la logistique, les services d'urgence et la planification publique, avec leurs hypothèses et leurs intervalles de sensibilité.

  **Mots-clés :** adressage ; géocodage ; codes postaux ; courbe de Hilbert ; chiffres de contrôle ; emprises de bâtiments ; Guinée-Bissau.
rights: "© 2026 N-WAYS LIMITED. Texte sous licence CC BY 4.0 ; registre sous ODbL 1.0 ; code sous Apache License 2.0."
lang: fr-FR
papersize: a4
fontsize: 11pt
geometry:
  - margin=24mm
  - top=30mm
---

# Introduction

Une adresse est une infrastructure publique. Elle permet à un ménage de recevoir une lettre, un colis ou une visite ; elle permet à une ambulance de rejoindre un patient ; elle permet à un service public, une banque ou un ministère de désigner le même logement sans le décrire. L'Union postale universelle estime qu'une large part de la population mondiale vit sans adresse utilisable et considère l'adressage comme une condition préalable du service postal, de l'inclusion financière et de l'état civil [@upu2012]. L'étude de la Banque mondiale sur l'adressage des villes africaines parvient à une conclusion voisine et ajoute que les programmes d'adressage échouent lorsque les habitants ne se les approprient pas [@farvacque2005].

La Guinée-Bissau en offre un exemple net. Son format de code postal existe sur le papier, mais seuls deux codes sont attestés, tous deux à Bissau [@upu-gw2005] ; les portes ne sont pas numérotées en dehors de quelques rues centrales ; et les deux façons les plus courantes de décrire un logement sont le nom du bairro ou de la tabanca et un point de repère. Une livraison dépend d'un appel téléphonique, un équipage d'ambulance dépend de la connaissance locale, et une famille de la diaspora ne peut pas écrire une destination qu'un livreur puisse vérifier.

Cet article décrit et évalue un modèle d'adressage conçu pour ce contexte. Son unité est la concession, la *morança* ou le *quintal* clos où vit une famille. Son code est un mot de lieu que les habitants disent déjà, suivi d'un numéro court : *Bandim 537*. Ses objectifs de conception, par ordre de priorité, sont que les habitants retiennent le code et l'obtiennent sans effort ; que le code prononcé soit unique dans tout le pays à lui seul ; qu'il conduise au portail de la concession ; qu'il fonctionne hors ligne ; et qu'aucun code ne change ni ne soit jamais réutilisé.

Nos contributions sont les suivantes.

1. Une forme de code, et l'arithmétique qui la fonde, dans laquelle tous les lieux qui partagent un nom tirent leurs numéros d'une plage nationale unique pour ce nom, divisée en blocs figés. La forme prononcée se décode ainsi sans secteur, sans ville et sans position (section 4).
2. Une spécification complète de chaque étape, des emprises de bâtiments aux concessions, aux lieux, aux noms de plaque, aux clés de nom, aux blocs, à la numérotation, au chiffre de contrôle et aux codes de point, avec chaque formule et un exemple traité sur un code réel (section 4).
3. Une implémentation ouverte : un moteur de référence, des vecteurs de conformité, le registre complet de 241 673 codes et un serveur que toute institution peut déployer pour répondre aux requêtes et, si elle est désignée, émettre des codes selon les mêmes règles (section 5).
4. Une évaluation, sur le registre complet, de l'unicité, de la longueur des codes, de la couverture, de la détection des erreurs et de l'exactitude du décodage (section 6), ainsi qu'un relevé des conceptions alternatives que nous avons mesurées puis écartées (section 7).
5. Des estimations, avec hypothèses explicites et intervalles de sensibilité, de la valeur du modèle pour les citoyens, pour la logistique et le commerce, pour les services d'urgence et pour la planification publique (sections 8 à 11).

La section 2 passe en revue les systèmes existants du pays et la littérature internationale, la section 3 les données. La section 12 traite de la vie privée, de la sécurité et de la gouvernance, la section 13 des limites et des travaux futurs, et la section 14 conclut.

# Contexte et travaux connexes

## La Guinée-Bissau

La Guinée-Bissau couvre environ 36 000 km² sur la côte atlantique de l'Afrique de l'Ouest, entre le Sénégal et la Guinée. Le quatrième Recensement général de la population et de l'habitat, conduit par l'Instituto Nacional de Estatística (INE) en juin 2026, avait dénombré au 22 juin 2 213 173 personnes, plus de 600 000 logements et environ 301 000 ménages, selon des chiffres provisoires [@lusa2026]. Le recensement de 2009 comptait 1 520 830 personnes, ce qui correspond à une croissance moyenne d'environ 2,2 % par an. Le pays est divisé en huit régions et le Setor Autónomo de Bissau, et les régions en 38 secteurs [@wiki-sectors; @pcgn2024]. La capitale se trouve sur l'Ilha de Bissau, reliée au continent par la route. Au large, l'archipel des Bijagós compte quelque 88 îles et îlots, dont beaucoup ne sont accessibles qu'en bateau.

Le kriol est la langue véhiculaire, parlée par environ 90 % de la population au recensement de 2009 ; le portugais, langue officielle, par 27 % ; le peul, le balante, le mandingue, le papel et le manjaque sont les principales langues premières, et le français est parlé par environ 5 % [@wiki-languages]. Le taux d'alphabétisation des adultes était de 63,9 % en 2022 [@fred-literacy], soit 77,3 % chez les hommes et 52,2 % chez les femmes, un écart de 25,2 points [@wb-gender]. Une adresse qu'il faut lire, épeler ou écrire en portugais exclut donc une large part de la population ; une adresse faite d'un lieu familier et d'un nombre prononcé n'en exclut que très peu.

## Systèmes postaux, d'adressage et fonciers existants

Nous avons examiné les systèmes postaux, d'adressage et fonciers du pays entre le 18 et le 20 octobre 2026. Le relevé complet figure dans `docs/existing-systems.md` ; les principaux constats sont les suivants.

**Codes postaux.** La fiche d'adressage de l'UPU pour la Guinée-Bissau, datée de mars 2005, prévoit quatre chiffres à gauche du nom de la localité, avec les exemples `1000 BISSAU` et `1011 BISSAU`, ce dernier pour la Direcção Geral dos Correios [@upu-gw2005]. Nous n'avons trouvé aucun autre code, aucun répertoire et aucun service de recherche. Le domaine de l'opérateur postal, Correios da Guiné-Bissau [@correios-wiki], ne répondait pas, et GeoNames, principal jeu ouvert de codes postaux, n'a pas de fichier pour le pays [@geonames-zip]. Le courrier est distribué en boîtes postales ou retiré au guichet.

**Portes et rues.** Nous n'avons trouvé aucun programme de dénomination des rues, de numérotation des portes ou d'adresse numérique dans la presse ou les sources officielles de 2024 à 2026. Dans OpenStreetMap, qui recense 99 131 contours de bâtiments dans le pays, deux bâtiments portent un numéro et huit un nom de rue [@geofabrik-gw]. Les noms de rue de la Câmara Municipal de Bissau sont en usage à Bissau Velho, sur la Praça et dans les avenues centrales ; il n'a pas été possible de vérifier si les portes y sont numérotées selon un plan officiel.

**Recensement et foncier.** Le recensement de 2026 a été annoncé avec le géoréférencement des logements [@forbes-census] ; ses cartes de dénombrement ne sont pas publiques, mais elles constituent le jeu officiel le plus proche d'un registre d'adresses. La Lei da Terra (loi 5/98) attribue la propriété de la terre à l'État, reconnaît les droits coutumiers d'usage et accorde l'usage privé par concession [@leiterra1998] ; le cadastre de la Direcção Geral de Geografia e Cadastro (DGGC) est partiel et surtout sur papier. La loi 14/2026 sur l'aménagement du territoire et l'urbanisme entre en vigueur le 22 octobre 2026 ; elle crée un cadre de planification, non des adresses [@geocracia2026]. Les plans topographiques utilisent le système géodésique national *Bissau* (code EPSG 2095) ou le WGS 84 [@epsg2095], qui diffèrent de plusieurs dizaines de mètres.

**Protection des données.** Nous n'avons trouvé ni loi ni autorité nationale de protection des données personnelles. La Guinée-Bissau est liée en principe par l'Acte additionnel A/SA.1/01/10 de la CEDEAO relatif à la protection des données à caractère personnel [@ecowas2010], et un projet de loi sur les transactions électroniques a été soumis à consultation publique en mai 2026 [@odemocrata2026].

## Pratique internationale

La norme S42 de l'UPU définit les composantes des adresses postales et les gabarits selon lesquels chaque pays les présente [@upu-s42]. C'est une norme de format : elle suppose que les rues, les numéros et les codes postaux existent. Là où ils n'existent pas, l'UPU et la Banque mondiale décrivent deux familles de réponses [@upu2012; @farvacque2005]. La première est l'adressage classique : nommer les rues, numéroter les portes le long de celles-ci et tenir un registre. Dans les 21 villes africaines étudiées par la Banque mondiale, seules 8 % des rues avaient un nom avant le début de l'adressage, et le coût moyen était d'environ 5,7 dollars par porte aux prix de 2005 [@farvacque2005]. La seconde est un code de grille ou de coordonnées, calculé à partir de la latitude et de la longitude et ne demandant aucun travail de terrain.

## Autres systèmes de codes et raisons de leur inadéquation

Les codes de grille comme l'Open Location Code (Plus Codes) sont ouverts, mondiaux et calculables hors ligne [@olc]. Un code tel que `7C36VC23+VX4` désigne un carré d'environ 3 m, non un logement, et mêle lettres et chiffres. Prononcée en Guinée-Bissau, chaque lettre doit être nommée par son nom portugais, que la plupart des locuteurs du kriol n'emploient pas ; et deux membres d'un même ménage, à deux coins de la cour, obtiennent deux codes différents. Les codes nationaux purement numériques évitent les lettres mais n'offrent aucune prise à la mémoire. Les codes secteur-numéro sont courts à dire, mais dans des secteurs comptant jusqu'à 14 700 concessions les numéros atteignent cinq chiffres, et beaucoup d'habitants n'emploient pas les noms de secteur au quotidien. Les adresses rue-numéro supposent des rues nommées, qui n'existent pas dans la plus grande partie du pays. Le tableau ci-dessous résume la comparaison.

| Forme | Exemple | Prononcée | Retenue | Unique seule | Suppose |
|:---------------|:----------------|:-------------|:-------------|:---------|:--------------|
| Code de grille | 7C36VC23+VX4 | lettres, un signe + | difficile | oui | rien |
| Secteur et numéro | Bissau 48213 | facile | moyenne | oui | un registre |
| Chiffres nationaux | 00228 00537 | facile | difficile | oui | un registre |
| Rue et numéro de porte | Rua 12, n.º 7 | facile | facile | avec la ville | des rues nommées, un registre |
| **Mot de lieu et numéro** | **Bandim 537** | **facile** | **facile** | **oui** | **un registre** |

: Formes de code comparées pour un usage en Guinée-Bissau.

Les Plus Codes restent néanmoins utiles comme référence universelle de coordonnées, et chaque enregistrement du registre en porte un. Le modèle décrit ici ne les remplace pas ; il y ajoute la couche que les habitants prononcent.

# Données et sources

**Emprises de bâtiments.** Le modèle part de 419 593 emprises de bâtiments, après suppression des contours de moins de 6 m². Parmi elles, 99 131 proviennent d'OpenStreetMap [@geofabrik-gw] et 320 462 sont des emprises issues de l'apprentissage automatique, de Google Open Buildings [@sirko2021] et de Microsoft [@microsoft-buildings], obtenues par le thème bâtiments d'Overture Maps [@overture], en ne gardant que celles qui ne recouvrent aucun contour d'OpenStreetMap. La figure 1 montre leur répartition par région : OpenStreetMap n'est la source principale que dans la région de Bolama-Bijagós, où des bénévoles ont tracé les îles en détail ; ailleurs dominent les emprises issues de l'apprentissage automatique. Leur attribut de hauteur est une valeur de remplissage destinée à l'affichage ; le modèle ne l'utilise jamais.

![Emprises de bâtiments par région et par source ($F$, nombre d'emprises). Les emprises de Google Open Buildings et de Microsoft fournissent 76 % du total national ; OpenStreetMap en fournit 46 % à Bissau et 67 % à Bolama.](figures/sources.svg){width=82%}

**Limites et îles.** Les 39 secteurs (38 *setores* et le Setor Autónomo de Bissau) proviennent des limites administratives d'OpenStreetMap, vérifiées avec geoBoundaries et la liste du PCGN [@pcgn2024], et ont été figés le 18 octobre 2026. Les 189 polygones d'îles et d'îlots proviennent du même extrait.

**Frontière nationale.** La frontière nationale est la limite administrative de la Guinée-Bissau de niveau 2 d'OpenStreetMap (relation 192776, `ISO3166-1=GW`), sous ODbL. C'est elle qui décide quels bâtiments appartiennent au pays : une emprise, une concession ou une entrée ne comptent que si elles se trouvent à l'intérieur de cette frontière ou à moins de 300 m de celle-ci, quoi que dise un contour de secteur ou une autre source de contours (geoBoundaries, GADM), car des contours de sources différentes peuvent déborder d'une frontière. Les 300 m tiennent compte des emprises dessinées à cheval sur la ligne et de la précision de la ligne elle-même. Tous les codes du registre ont leur entrée à l'intérieur de la frontière ou à moins de cette distance.

**Lieux.** Les points de lieu proviennent d'OpenStreetMap (bairros, villes, villages, hameaux, moranças nommées), puis de GeoNames. Une localité de GeoNames n'est conservée que si aucun lieu d'OpenStreetMap ne se trouve à moins de 400 m et aucun lieu de même nom à moins de 1,5 km. La table des lieux compte 4 221 lieux et 39 mots de secteur.

**Enceintes et portails.** Murs, clôtures, haies, contours de concession (`landuse=farmyard`, 782 dans l'extrait) et portails proviennent d'OpenStreetMap.

**Statistiques.** La population, les ménages, les langues et l'alphabétisation proviennent du recensement et des statistiques internationales citées à la section 2. Tous les décomptes de cet article qui portent sur les codes sont calculés à partir du registre publié, et les programmes qui produisent les figures se trouvent dans le dépôt (`tools/paper_figures.py`).

# Le modèle

## Principes de conception

Le modèle suit neuf principes, par ordre de priorité.

1. **Mémorisable et sans effort.** Un code est un mot de lieu que les habitants emploient déjà et un numéro court ; l'obtenir demande un geste.
2. **Unique à lui seul.** Le code prononcé désigne un logement du pays sans ville, secteur, île ni position.
3. **La concession et son portail.** L'unité est la morança ou le quintal ; ses bâtiments en sont des sous-unités ; la navigation s'arrête au portail.
4. **L'officiel d'abord.** Là où existe une adresse publique, elle est affichée en premier, telle que l'État l'écrit.
5. **Hors ligne.** Codes de point, mots de lieu et chiffres de contrôle se calculent sans réseau.
6. **Stable.** Un code ne se déplace jamais et n'est jamais réutilisé ; regroupements, changements de nom et nouvelles limites ne modifient jamais un code émis.
7. **Des lieux, jamais des personnes.** Aucun nom ni aucune donnée d'habitant n'est conservé.
8. **Ouvert et transférable.** Le moteur, le registre et les règles sont ouverts et conçus pour être remis à l'État.
9. **National.** Le modèle et son moteur sont propres à la Guinée-Bissau.

## Les formes d'un code

Un code a trois formes équivalentes. La **forme mémorisée** $P\;N$ est le nom de plaque $P$ du lieu suivi du numéro $N \in \{1, \dots, 99\,999\}$ ; c'est ce que les habitants disent, tapent et écrivent, et c'est aussi la **forme écrite** utilisée sur les plaques et les colis. La **forme machine** est

$$
\underbrace{SS}_{\text{secteur}}\;\text{-}\;\underbrace{PPP}_{\text{lieu}}\;\text{-}\;\underbrace{NNNNN}_{\text{numéro}}\;\text{-}\;c,
\qquad c = \operatorname{Damm}\!\left(F \,\|\, NNNNN\right),
\tag{1}
$$
où $SS$ est le numéro du secteur à deux chiffres, $PPP$ l'indice du lieu dans le secteur à trois chiffres, $NNNNN$ le numéro complété à cinq chiffres, $F$ le numéro national à cinq chiffres du nom du lieu (section 4.7), $\|$ la concaténation et $\operatorname{Damm}$ la fonction de contrôle de la section 4.12. Un bâtiment à l'intérieur de la concession ajoute un suffixe (`Bandim 537.2`, `10-022-00537.2-c`). Seule la forme machine porte le chiffre de contrôle : les habitants ne le voient jamais. Un **code de point** (section 4.13) désigne tout point dépourvu de concession.

| Forme | Exemple | Utilisée par |
|:--|:--|:--|
| Mémorisée et écrite | Bandim 537 | les habitants : dite, tapée, peinte sur le portail |
| Machine | 10-022-00537-4 | systèmes, codes QR, partenaires |
| Bâtiment | Bandim 537.2 | un second bâtiment de la concession |
| Point | 10-4327-9117 | tout point sans concession |

: Les formes d'un code.

## Les secteurs

Chacun des 39 secteurs possède un numéro à deux chiffres dont le premier est celui de sa région (1 Bissau, 2 Bafatá, 3 Bolama, 4 Biombo, 5 Cacheu, 6 Gabú, 7 Oio, 8 Quinara, 9 Tombali), une clé de trois lettres et sa propre grille de points (section 4.13). Bissau est le secteur 10 ; les numéros 11 à 19 sont réservés pour le cas où la ville serait divisée en arrondissements. Un point $\mathbf{p}$ appartient au secteur dont le contour le contient, par lancer de rayon, trous exclus :

$$
s(\mathbf{p}) =
\begin{cases}
\sigma & \text{si } \mathbf{p} \in \Omega_\sigma \text{ et } \delta_B(\mathbf{p}) \le 300\ \text{m}, \\
\varnothing & \text{sinon},
\end{cases}
\tag{2}
$$
où $\Omega_\sigma$ est le contour du secteur $\sigma$ et $\delta_B(\mathbf{p})$ la distance de $\mathbf{p}$ à la frontière nationale $B$, nulle à l'intérieur. Les points en mer ou à l'étranger n'ont pas de secteur. **La frontière décide :** un point situé à plus de 300 m hors de la frontière nationale n'a pas de secteur, même si un contour de secteur le contient, de sorte qu'aucun bâtiment d'un pays voisin ne reçoit de code. Le moteur emporte $B$ simplifiée par l'algorithme de Douglas–Peucker à 50 m, dont la plus grande distance à la ligne exacte est de 50,2 m, et accepte un point situé au plus à 248 m hors de celle-ci, si bien qu'aucun point accepté ne se trouve à plus de 300 m hors de la frontière exacte. Le regroupement applique le même test à chaque emprise et à chaque concession avant d'attribuer un numéro, et le serveur du registre l'applique à chaque nouveau code et à chaque entrée déplacée. La figure 2 montre les contours et la densité des concessions.

![Concessions par maille de 5 km ($c$, échelle logarithmique) et contours des 39 secteurs, en kilomètres sur une projection équirectangulaire locale. Les mailles de Bissau comptent jusqu'à 20 890 concessions ; la plus grande partie de l'est en compte de quelques dizaines à quelques centaines par maille.](figures/map.svg){width=100%}

| Région | Secteurs | Concessions |
|:----------------------|:----------------------------------------------------|--------------:|
| Setor Autónomo de Bissau | 10 Bissau | 43 850 |
| Gabú | 61 Boé, 62 Gabú, 63 Pirada, 64 Pitche, 65 Sonaco | 43 414 |
| Cacheu | 51 Bigene, 52 Bula, 53 Cacheu, 54 Caió, 55 Canchungo, 56 São Domingos | 35 431 |
| Bafatá | 21 Bafatá, 22 Bambadinca, 23 Contuboel, 24 Galomaro, 25 Gã-Mamudo, 26 Xitole | 34 427 |
| Oio | 71 Bissorã, 72 Farim, 73 Mansabá, 74 Mansoa, 75 Nhacra | 29 493 |
| Biombo | 41 Prábis, 42 Quinhamel, 43 Safim | 21 852 |
| Tombali | 91 Bedanda, 92 Cacine, 93 Catió, 94 Komo, 95 Quebo | 16 101 |
| Quinara | 81 Buba, 82 Empada, 83 Fulacunda, 84 Tite | 9 131 |
| Bolama | 31 Bolama, 32 Bubaque, 33 Caravela, 34 Uno | 7 974 |
| **Total** | **39** | **241 673** |

: Régions, secteurs et concessions du registre.

## Les concessions : regrouper les bâtiments

Un foyer familial en Guinée-Bissau se compose d'ordinaire de plusieurs bâtiments. Une morança rurale comprend une maison principale, des cuisines, des greniers et parfois des cases rondes autour d'une cour ; un quintal de Bissau est souvent clos de murs. Les emprises le reflètent : un quart mesurent moins de 33 m² et la moitié plus de 116 m², et dans la région de Gabú la médiane est de 41 m², car les concessions peules et mandingues de l'est se composent de nombreuses petites cases. Numéroter les bâtiments donnerait plusieurs codes à une même famille ; nous regroupons donc les emprises en concessions avant toute numérotation.

**Classe d'habitat.** Pour chaque emprise, la densité $\rho$ des emprises dans le carré de 250 m centré sur elle (cinq mailles de 50 m dans chaque direction) détermine une classe d'habitat :

$$
\rho = \frac{\#\{\text{emprises à } \pm 2 \text{ mailles de } 50\ \text{m}\}}{6{,}25\ \text{ha}},
\qquad
\text{classe} =
\begin{cases}
\textit{cidade} & \rho \ge 10\ \text{ha}^{-1},\\
\textit{vila} & 4 \le \rho < 10,\\
\textit{tabanca} & 1 \le \rho < 4,\\
\textit{disperso} & \rho < 1.
\end{cases}
\tag{3}
$$

**Écart entre bâtiments.** Pour deux emprises $a$ et $b$, de centroïdes $\mathbf{c}_a, \mathbf{c}_b$ et de surfaces $A_a, A_b$, nous approchons l'écart entre leurs murs par

$$
g(a, b) = \lVert \mathbf{c}_a - \mathbf{c}_b \rVert - \tfrac{1}{2}\sqrt{A_a} - \tfrac{1}{2}\sqrt{A_b}.
\tag{4}
$$

Les règles ci-dessous s'appliquent dans l'ordre. Les bâtiments sont d'abord triés par secteur, latitude, longitude, surface et identifiant, de sorte que le résultat ne dépende jamais de l'ordre d'arrivée des données cartographiques.

| Règle | Condition | Effet |
|:----------|:---------------------------------------------------|:------------------------------|
| Enceinte | centroïde à l'intérieur d'un mur, d'une clôture, d'une haie, d'une concession tracée ($\le 1$ ha), d'une parcelle résidentielle ($\le 2\,500$ m²) ou d'un site institutionnel | l'enceinte forme une concession |
| Annexe | $A < 40$ m² et $g \le d_a$ jusqu'à un bâtiment | rejoint le bâtiment le plus proche |
| Maisons | toutes deux $A \ge 40$ m² et $g \le d_g$ | liaison simple en une concession |
| Plafond | un groupe de plus de 12 bâtiments | relié de nouveau avec des distances réduites de moitié jusqu'à 12 bâtiments au plus |

: Règles de regroupement, appliquées dans l'ordre.

| Classe | $d_a$ (annexe) | $d_g$ (maisons) |
|:--|--:|--:|
| cidade | 6 m | 3 m |
| vila | 10 m | 6 m |
| tabanca | 15 m | 12 m |
| disperso | 20 m | 15 m |

: Distances de jonction par classe d'habitat.

**Résultat.** Les règles donnent 241 673 concessions à partir de 419 593 emprises : 144 820 concessions d'un bâtiment, 56 535 de deux, 21 794 de trois et 18 524 de quatre ou plus (moyenne 1,74). Parmi toutes les emprises, 65,5 % appartiennent à une concession de deux bâtiments ou plus, de 58 % à Bissau à 71 % dans l'Oio ; 763 concessions proviennent d'enceintes tracées. Avec environ 301 000 ménages au recensement, on compte environ 1,25 ménage par concession, ce qui concorde avec des concessions familiales abritant plus d'un ménage.

**Validation.** Nous avons appliqué de nouveau les règles de proximité en masquant les enceintes tracées par les contributeurs, puis comparé le résultat à ces enceintes. Sur 159 moranças rurales tracées, 58 % sont retrouvées entières et 46 % exactement, et 24 % de plus ne manquent qu'un bâtiment. Dans 53 quintais urbains clos, 13 % seulement sont retrouvés entiers : à l'intérieur d'un mur de Bissau les bâtiments sont éloignés, tandis que les voisins de l'autre côté du mur sont proches. La règle est volontairement prudente en ville, car les deux erreurs ne sont pas symétriques : fusionner deux codes plus tard ne coûte rien (l'un devient un alias), alors que scinder une fusion erronée donnerait un nouveau code à une famille.

## Les lieux et la règle du point au lieu

Le mot de lieu est un bairro de Bissau (y compris les anciens villages absorbés par la ville, devenus des noms de bairro : Plaque, Jal, Bono, Quetene, Cuntum), une ville ou l'un de ses bairros, un village, un hameau ou un groupe de moranças. Une concession $c$ du secteur $s$ située sur la masse terrestre $L$ prend le lieu le plus proche de son secteur et de sa masse terrestre à moins de 3 km, et sinon le mot propre du secteur :

$$
p(c) =
\begin{cases}
\displaystyle\operatorname*{arg\,min}_{q \in \mathcal{P}(s, L)} d(c, q) & \text{si } \displaystyle\min_{q \in \mathcal{P}(s, L)} d(c, q) \le 3\,000\ \text{m},\\[1ex]
\text{le mot du secteur (indice 000)} & \text{sinon,}
\end{cases}
\tag{5}
$$
où $\mathcal{P}(s, L)$ est l'ensemble des lieux du secteur $s$ sur la masse terrestre $L$, $d$ la distance au sol en mètres, les égalités étant tranchées en faveur de l'indice le plus bas. L'Ilha de Bissau compte avec le continent, car une route les relie ; toute autre île forme sa propre masse terrestre, si bien qu'un logement d'Orango n'est jamais numéroté dans un lieu de Bubaque.

Sur les 4 221 lieux, 3 336 comptent au moins une concession. Trente-sept secteurs emploient leur propre mot pour 5 430 concessions situées à plus de 3 km de tout lieu nommé. Un bairro contesté ou renommé ne change jamais un code : le nouveau nom devient un alias.

## Les noms de plaque

Le mot d'un code doit être assez court pour être dit avec un numéro. Nous appelons **nom de plaque** la forme courte admissible, et exigeons

$$
\operatorname{plaque}(w) \iff \bigl|\operatorname{NFC}(w)\bigr| \le 12 \;\wedge\; \bigl|\operatorname{mots}(w) \setminus \mathcal{L}\bigr| \le 2 \;\wedge\; w \text{ ne contient aucun chiffre},
\tag{6}
$$
où $|\operatorname{NFC}(w)|$ compte les caractères en forme normale C d'Unicode (une lettre accentuée compte pour un), $\operatorname{mots}(w)$ désigne les parties séparées par des espaces ou des traits d'union, et $\mathcal{L} = \{$de, da, do, das, dos, d, e, o, a, os, as, em, na, no, di, du$\}$ l'ensemble des mots de liaison.

Un nom qui ne satisfait pas l'équation (6) passe par des étapes fixes : une forme courte documentée et déjà en usage ; le nettoyage (parenthèses, « Bairro de », « Tabanca de », « Morança » et mots génériques : « Bairro Ajuda II Phase » devient *Ajuda II*) ; l'abréviation d'un préfixe de saint (*Sto António*) ; et à défaut, le choix de la suite la plus distinctive d'un ou deux mots entiers. Chaque suite candidate $r$ reçoit pour note la fréquence moyenne de ses mots parmi tous les noms de lieu du pays,

$$
\operatorname{rareté}(r) = \frac{1}{|\operatorname{mots}(r)|} \sum_{u \in \operatorname{mots}(r)} f(u),
\tag{7}
$$
où $f(u)$ est le nombre de noms de lieu contenant le mot $u$. La suite de note la plus basse est retenue, de préférence en fin de nom, seulement si elle devance la suivante d'un facteur 1,5 au moins. Ainsi « Sinchã Malam Baio » devient *Malam Baio* et « Missirá Ama Sidi » devient *Ama Sidi*. Les termes de peuplement (*Sinchã*, *Sare*, *Madina*, *Gã*, *Ponta*, *Ilhéu*) tombent les premiers et ne forment jamais seuls un nom de plaque. Les noms des peuples d'après lesquels une tabanca est nommée (balante, mancagne, papel, peul, biafada) ne sont jamais retirés automatiquement, car « Bambadinca Balanta » et « Bambadinca Mancanha » sont deux villages.

Lorsqu'aucune forme courte ne s'impose, le lieu est signalé à la Câmara Municipal à Bissau, ou à l'administration du secteur avec les *régulos* et la communauté, avec trois candidats au plus. Sur les 3 336 lieux en usage, 2 807 gardent leur nom, 17 sont nettoyés, 119 raccourcis, 37 sont des mots de secteur et 356 sont signalés, dont 28 dépassent encore la limite. Les 21 759 codes des lieux signalés ont été émis avec le nom provisoire. Le choix du conseil peut changer le mot une fois ; le nom officiel reste toujours un alias.

## La clé de nom

Deux noms qui se prononcent ou s'écrivent de façon semblable ne doivent jamais dépendre de l'oreille de l'auditeur pour être distingués ; ils partagent donc une **clé de nom** et, avec elle, une seule plage nationale de numéros. La clé d'un mot $w$ est une composition d'étapes de normalisation,

$$
\kappa(w) = \Phi\bigl(\delta(\nu(\epsilon(\pi(\tau(\alpha(w)))))))\bigr) \,\|\, \#\,n(w),
\tag{8}
$$
où $\alpha$ passe en minuscules, lit *ç* comme *s* et retire les accents ; $\tau$ remplace par une espace tout caractère autre que a–z et 0–9 ; $\pi$ retire un *Bairro*, *Tabanca*, *Aldeia*, *Povoação* ou *Morança* initial (suivi éventuellement de *de*, *da* ou *do*) ; $\epsilon$ développe les abréviations *Sto*, *Sta*, un *S.* initial et *N. Sra* ; $\nu$ met de côté un numéral final de I à X ou de 1 à 10, sous la forme du chiffre romain $n(w)$ ; $\delta$ retire les petits mots *de, da, do, dos, das, e, o, a, os, as* lorsqu'il reste autre chose ; et $\Phi$ ramène à une seule lettre les graphies d'un même son, comme suit. Un *que* final devient *k* ; *tch*, *ch* et *sh* deviennent *x* ; *ck* et *qu* deviennent *k* ; *gu* devient *g* ; *ph* devient *f* ; *nh* devient *n* ; *lh* devient *l* ; *c* devant *e* ou *i* devient *s* et tout autre *c* devient *k* ; *z* devient *s*, *y* devient *i*, *w* devient *u* ; *h* tombe ; les graphies vocaliques du kriol sont confondues (*e* avec *i*, *o* avec *u*) ; et les lettres doublées se réduisent à une. Le suffixe $\#\,n(w)$ n'apparaît que si un numéral a été mis de côté.

Ainsi *Sintchã Dulo*, *Sinchã Duló* et *Sincha Dulu* partagent la clé `sinxadulu` ; *Plack* et *Plaque* partagent `plak` ; *Áfià* et *Hafia* partagent `afia` ; tandis que *Plaque II* (`plak#ii`) est un nom à part entière. Comme un mot tapé sans sa cédille (*Praca* pour *Praça*) verrait autrement son *c* devenir *k*, tout nom contenant un *ç* se résout aussi à partir de sa graphie sans cédille (section 6.2). La réduction pèche volontairement par excès de fusion : réunir deux noms ne coûte qu'une plage plus longue, alors que séparer deux noms qui se prononcent pareil donnerait à deux logements le même code prononcé.

Appliquée aux 4 221 lieux et aux 39 mots de secteur, l'équation (8) donne 3 295 clés de nom, dont 2 704 comptent des concessions. Parmi elles, 407 noms sont partagés par deux lieux en usage ou plus, soit 1 039 lieux et 92 745 concessions (38 % du total) ; 183 noms se répètent au sein d'un même secteur. Missirá est le nom qui compte le plus de lieux (14), devant Áfià (13), Madina (12) et Amedalai (11).

## Une plage nationale par nom

Comme un nom se dit sans sa ville, tous les lieux qui partagent une clé de nom tirent leurs numéros d'une seule **plage nationale** $\{1, \dots, 99\,999\}$, divisée en un bloc par lieu. Un numéro tombe dans un seul bloc ; un nom et un numéro se décodent donc en un seul lieu.

**Taille des blocs.** Un lieu comptant $n$ concessions lors de la première émission reçoit le plus petit bloc de la série 1–2–5 qui contienne quatre fois ses concessions :

$$
b(n) = \min\bigl\{x \in \{10, 20, 50, 100, 200, 500, 1\,000, \dots, 50\,000\} : x \ge 4n \bigr\}.
\tag{9}
$$

Le facteur quatre découle de la règle de numérotation de la section 4.9 : la première émission utilise un numéro sur deux, de sorte que la moitié du bloc est occupée par les concessions initiales et les numéros intercalés ; l'autre moitié reste disponible pour la croissance du lieu.

**Placement des blocs.** Les lieux d'un même nom sont pris du plus grand au plus petit, ceux qui attendent le choix d'un nom de plaque par un conseil venant après les autres, et chaque bloc commence au plus haut niveau atteint par le nom, arrondi au multiple supérieur d'une puissance de dix adaptée à sa taille :

$$
\begin{aligned}
\operatorname{pas}(b) &= 10^{\lfloor \log_{10} b \rfloor},
&
\text{début}_i &= \operatorname{pas}(b_i)\left\lceil \frac{H_{i-1}}{\operatorname{pas}(b_i)} \right\rceil,\\
\text{fin}_i &= \text{début}_i + b_i - 1,
&
H_i &= \text{fin}_i + 1,
\end{aligned}
\tag{10}
$$
avec $H_0 = 0$. Des débuts ronds rendent les blocs lisibles : le bairro de Bandim, à Bissau, occupe 0–1 999 et la tabanca de Bandim, à Catió, 2 000–2 199.

**Exemple traité.** Bandim, bairro de Bissau (secteur 10, lieu 022), comptait $n = 452$ concessions lors de la première émission et c'est le plus grand lieu de son nom ; donc $4n = 1\,808$, $b = 2\,000$ et son bloc est 0–1 999. Quatorze lieux partagent le nom Missirá ; la figure 3 montre comment leurs blocs se partagent la plage. *Missira 101* se trouve à Bissau et *Missirá 5101* à Sonaco ; aucun des deux n'a besoin de son secteur.

![La plage nationale du nom Missirá, divisée en un bloc figé par lieu (numéro $N$ en abscisse). La partie foncée de chaque bloc contient les numéros de la première émission, de $\text{début}+1$ à $\text{début}+2n-1$ ; la partie claire est la réserve. Galomaro apparaît deux fois, car deux lieux de ce secteur portent ce nom.](figures/blocks.svg){width=96%}

| Lieu | Secteur | Concessions | Bloc |
|:--|:--|--:|:--|
| Missira | Bissau | 771 | 0–4 999 |
| Missirá | Sonaco | 81 | 5 000–5 499 |
| Missirá | Gabú | 53 | 5 500–5 999 |
| Missirá | Bafatá | 49 | 6 000–6 199 |
| Missirá | Bissorã | 44 | 6 200–6 399 |
| Missirá | Bambadinca | 30 | 6 400–6 599 |
| … huit autres | | 113 | jusqu'à 7 249 |

: Les blocs du nom Missirá.

**Horizon de croissance.** Lors de la première émission, un lieu utilise les numéros impairs jusqu'à $2n - 1$ dans un bloc d'au moins $4n$ ; il peut donc accueillir quatre fois ses concessions initiales avant d'avoir besoin d'un autre bloc. À un taux de croissance constant $r$, cela prend

$$
t = \frac{\ln 4}{\ln (1 + r)} \approx
\begin{cases}
63\ \text{ans} & r = 2{,}2\,\%\ \text{(moyenne nationale)},\\
35\ \text{ans} & r = 4\,\%\ \text{(périphéries de Bissau en forte croissance)}.
\end{cases}
\tag{11}
$$

**Table figée.** La table des blocs a été figée lors de la première émission, le 20 octobre 2026. Un bloc n'est jamais déplacé, renuméroté ni réduit. Un nouveau lieu portant un nom existant, ou un lieu dont le bloc est plein, reçoit un bloc supplémentaire au-dessus du plus haut niveau du nom, selon l'équation (10).

La plus grande plage partagée est celle d'Áfià (13 lieux, 2 560 concessions), qui s'achève à 15 719. Aucun nom n'approche 99 999 ; aucun qualificatif n'est donc nécessaire.

## La numérotation dans un lieu : la courbe de Hilbert

Dans son bloc, les concessions d'un lieu sont numérotées le long d'une courbe de Hilbert [@hilbert1891], afin que des voisins sur le terrain reçoivent des numéros voisins, comme le font les numéros de porte le long d'une rue. Parmi les courbes qui remplissent le plan, celle de Hilbert offre les meilleures propriétés de regroupement : une région compacte du plan correspond à peu de tronçons contigus de la courbe [@moon2001].

**La grille.** Chaque secteur possède un cadre de $10\,000 \times 10\,000$ mailles, de coin sud-ouest $(\varphi_S, \lambda_W)$, de latitude de référence $\varphi_r$ et de côté de maille $\Delta$ en mètres (1,7 m à Bissau, jusqu'à 9,4 m à Gabú). Un point $(\varphi, \lambda)$ se trouve dans la maille

$$
x = \operatorname{clip}\!\left(\left\lfloor \frac{(\lambda - \lambda_W)\cos\varphi_r \cdot 111\,320}{\Delta} \right\rfloor\right),
\qquad
y = \operatorname{clip}\!\left(\left\lfloor \frac{(\varphi - \varphi_S) \cdot 110\,574}{\Delta} \right\rfloor\right),
\tag{12}
$$
où $\operatorname{clip}$ borne le résultat à $0, \dots, 9\,999$, les constantes étant le nombre de mètres par degré de longitude à l'équateur et par degré de latitude.

**La courbe.** L'indice de Hilbert $h(x, y)$ sur une courbe d'ordre 14 ($2^{14} = 16\,384$ mailles de côté, englobant la grille) se calcule du bit de poids fort au bit de poids faible. Avec $h = 0$ et, pour $\sigma = 2^{13}, 2^{12}, \dots, 1$,

$$
\begin{aligned}
r_x &= \left\lfloor x / \sigma \right\rfloor \bmod 2,
\qquad
r_y = \left\lfloor y / \sigma \right\rfloor \bmod 2,
\qquad
h \leftarrow h + \sigma^2 \bigl((3 r_x) \oplus r_y\bigr),\\
(x, y) &\leftarrow
\begin{cases}
(y, x) & r_y = 0,\ r_x = 0,\\
(2^{14} - 1 - y,\ 2^{14} - 1 - x) & r_y = 0,\ r_x = 1,\\
(x, y) & r_y = 1,
\end{cases}
\end{aligned}
\tag{13}
$$
où $\oplus$ est le ou exclusif bit à bit. La figure 4 montre la courbe d'ordre 3 calculée par le moteur de référence.

![La courbe de Hilbert d'ordre 3 sur une grille $8 \times 8$, avec l'indice $h$ de chaque maille $(i, j)$, tel que le calcule le moteur de référence. Le modèle emploie la même construction à l'ordre 14.](figures/hilbert.svg){width=52%}

**Première émission.** Les $n$ concessions d'un lieu de bloc $[\text{début}, \text{fin}]$, triées selon $(h, \text{clé})$, où la clé est l'identifiant stable du bâtiment principal de la concession, reçoivent

$$
N_k = \text{début} + 1 + 2k, \qquad k = 0, 1, \dots, n - 1.
\tag{14}
$$

Les numéros pairs entre voisins restent libres pour les concessions construites plus tard entre eux.

**Exemple traité : Bandim 537.** La concession la plus proche du marché de Bandim a son point d'entrée en $\varphi = 11{,}8521485$, $\lambda = -15{,}5950371$. Dans le cadre de Bissau ($\lambda_W = -15{,}662$, $\varphi_S = 11{,}795$, $\varphi_r = 11{,}87$, $\Delta = 1{,}7$ m), l'équation (12) donne la maille $(4\,291 ;\ 3\,717)$ et l'équation (13) l'indice de Hilbert $33\,435\,700$. C'est la 269e des 452 concessions de Bandim le long de la courbe ($k = 268$) ; l'équation (14) donne donc $N = 0 + 1 + 2 \cdot 268 = 537$. La figure 5 montre l'ensemble du bairro.

![Les 452 concessions de Bandim, à Bissau, colorées selon leur numéro $N$ et reliées dans l'ordre numérique, en mètres depuis le coin sud-ouest du bairro. Les numéros progressent îlot par îlot ; Bandim 537 est signalée.](figures/bandim.svg){width=76%}

## Un nouveau logement

Une nouvelle concession située entre ses voisines de Hilbert $a$ (le numéro émis juste avant elle le long de la courbe) et $b$ (juste après), d'indices $h_a < h < h_b$, reçoit le numéro libre le plus proche de sa position proportionnelle $N^{*}$ :

$$
\begin{aligned}
N^{*} &= a + \max\Bigl(1,\ \min\Bigl(b - a - 1,\ \operatorname{round}\Bigl(\frac{h - h_a}{h_b - h_a}\,(b - a)\Bigr)\Bigr)\Bigr),\\
N_{\text{nouveau}} &= \operatorname*{arg\,min}_{a < m < b,\ m\ \text{libre}} \lvert m - N^{*} \rvert.
\end{aligned}
\tag{15}
$$

S'il n'y a aucun numéro libre entre $a$ et $b$, ou si la concession vient après la dernière, elle reçoit le plus grand numéro du lieu plus un, s'il reste dans le bloc ; sinon le bloc suivant du lieu et, si tous sont pleins, un bloc de continuation dimensionné par l'équation (9) et placé par l'équation (10). Un numéro retiré n'est jamais réutilisé.

## Décoder sans contexte

Pour décoder une forme mémorisée, les chiffres finaux forment le numéro $N$ et les mots qui les précèdent le nom $P$. La clé du nom donne la plage nationale, et le numéro donne l'unique bloc qui le contient :

$$
\operatorname{décoder}(P, N) = \bigl\{\, q : \kappa(P) \in K(q) \;\wedge\; N \in B(q) \,\bigr\},
\tag{16}
$$
où $K(q)$ est l'ensemble des clés du lieu $q$ (son nom de plaque et ses alias) et $B(q)$ ses blocs. Comme les blocs d'un même nom ne se chevauchent jamais, l'ensemble compte au plus un élément. Un numéro hors de tout bloc est refusé, jamais deviné dans un lieu voisin. Un nom de secteur tapé après une virgule est affiché, mais jamais nécessaire.

## Le chiffre de contrôle

La forme machine porte un chiffre décimal de contrôle calculé par l'algorithme de Damm [@damm2004; @damm2007] sur la charge utile $F \,\|\, N$ (dix chiffres, suivis du numéro de bâtiment s'il y a lieu) :

$$
c_0 = 0, \qquad c_k = T\bigl[c_{k-1}\bigr]\bigl[d_k\bigr], \quad k = 1, \dots, m, \qquad \operatorname{Damm}(d_1 \cdots d_m) = c_m,
\tag{17}
$$
où $d_k$ sont les chiffres de la charge utile et $T$ la table d'opération d'un quasi-groupe totalement antisymétrique d'ordre 10 :

$$
T =
\begin{pmatrix}
0 & 3 & 1 & 7 & 5 & 9 & 8 & 6 & 4 & 2\\
7 & 0 & 9 & 2 & 1 & 5 & 4 & 8 & 6 & 3\\
4 & 2 & 0 & 6 & 8 & 7 & 1 & 3 & 5 & 9\\
1 & 7 & 5 & 0 & 9 & 8 & 3 & 4 & 2 & 6\\
6 & 1 & 2 & 3 & 0 & 4 & 5 & 9 & 7 & 8\\
3 & 6 & 7 & 4 & 2 & 0 & 9 & 5 & 8 & 1\\
5 & 8 & 6 & 9 & 7 & 2 & 0 & 1 & 3 & 4\\
8 & 9 & 4 & 5 & 3 & 6 & 2 & 0 & 1 & 7\\
9 & 4 & 3 & 8 & 6 & 1 & 7 & 2 & 0 & 5\\
2 & 5 & 8 & 1 & 4 & 3 & 6 & 7 & 9 & 0
\end{pmatrix}.
$$

Chaque ligne et chaque colonne de $T$ est une permutation ; toute erreur sur un seul chiffre modifie donc le résultat. La table est totalement antisymétrique, c'est-à-dire que $T[T[c][x]][y] = T[T[c][y]][x]$ entraîne $x = y$ ; toute permutation de deux chiffres adjacents différents est donc également détectée. Ce sont les deux erreurs les plus fréquentes dans la transcription de codes décimaux [@verhoeff1969].

**Exemple traité.** Le nom Bandim a pour numéro national $F = 228$ ; la charge utile de Bandim 537 est donc `0022800537`. Les valeurs successives de $c_k$ sont 0, 0, 1, 9, 9, 2, 4, 4, 3, 4, et le chiffre de contrôle est 4 : la forme machine est `10-022-00537-4`. Un système partenaire qui reçoit `10-022-00573-4`, avec deux chiffres permutés, constate que le chiffre de contrôle de `0022800573` n'est pas 4 et refuse le code.

**Lien avec le lieu.** Le lieu ne figure pas dans la charge utile ; il découle du nom et du numéro par la table figée des blocs. Une erreur qui ferait passer le numéro dans le bloc d'un autre lieu de même nom modifie un chiffre de la charge utile et est donc toujours détectée : `10-050-05101-8` (le code de Missira 101, à Bissau, avec un chiffre modifié) est refusé. Une erreur sur les chiffres du secteur ou du lieu est refusée chaque fois qu'elle tombe sur un autre lieu du même nom ou sur aucun lieu ; elle n'est acceptée que si elle tombe sur un lieu d'un autre nom, dont tous les écrans affichent alors le mot (section 6.3).

## Les codes de point

Tout point situé dans un secteur possède un code de point, calculé hors ligne à partir de ses coordonnées sur la grille du secteur de l'équation (12). Soient $X = X_1X_2X_3X_4$ et $Y = Y_1Y_2Y_3Y_4$ les écritures décimales à quatre chiffres des coordonnées de maille $x$ et $y$. Leurs chiffres sont entrelacés,

$$
D = X_1 Y_1 X_2 Y_2 X_3 Y_3 X_4 Y_4,
\qquad
\text{code} = SS\text{-}D_1D_2D_3D_4\text{-}D_5D_6D_7D_8,
\tag{18}
$$
de sorte que les deux premiers chiffres désignent un carré de 1 000 mailles de côté et que chaque paire suivante l'affine d'un facteur dix. Un neuvième chiffre facultatif choisit un neuvième de la maille, disposé comme sur le clavier d'un téléphone, avec 1 2 3 sur la rangée nord :

$$
k = 3\bigl(2 - \lfloor 3 f_y \rfloor\bigr) + \lfloor 3 f_x \rfloor + 1,
\tag{19}
$$
où $f_x, f_y \in [0, 1)$ sont les parties fractionnaires de la position du point dans la maille. Un code de point se décode au centre de sa maille ; l'erreur de décodage est donc bornée par la moitié de la diagonale de la maille :

$$
\varepsilon \le \frac{\Delta\sqrt{2}}{2} \quad (1{,}2\ \text{m à Bissau}),
\qquad
\varepsilon \le \frac{\Delta\sqrt{2}}{6} \ \text{avec le neuvième chiffre}.
\tag{20}
$$

**Exemple traité.** Bandim 537 se trouve en $x = 4\,291{,}1$, $y = 3\,717{,}1$ dans la grille de Bissau ; donc $X = 4291$, $Y = 3717$, $D = 43279117$ et le code de point est `10-4327-9117` ; avec $f_x = f_y = 0{,}1$, l'équation (19) donne $k = 7$ et le code affiné `10-4327-9117.7`. La figure 6 montre le premier niveau de la grille sur Bissau. Les codes de point servent aux lieux sans concession (un étal de marché, un point de rendez-vous lors d'un *lumo* hebdomadaire, un débarcadère de pêche) et se partagent sous forme de liens plutôt que d'être mémorisés.

![La grille de points du secteur 10 (Bissau), en unités de 1 000 mailles ($x/1000$, $y/1000$ ; une unité vaut 1,7 km). Chaque carré porte sa première paire de chiffres $X_1Y_1$ ; les points représentent une concession sur 25. Bandim 537 se trouve dans le carré 43 et son code de point est 10-4327-9117.](figures/spot.svg){width=58%}

## Les îles et le profil du bâtiment

Une concession située sur une île ne prend un mot de lieu que sur la même île (équation (5)), et sa fiche affiche l'île comme étiquette ; le code est unique sans elle.

Chaque bâtiment porte une classe d'usage avec son degré de confiance et sa source, sa surface d'emprise, son nombre d'étages lorsqu'il est connu et un statut ; chaque concession les agrège. Les classes sont propres au pays (maison de concession, annexe, case ronde, boutique, marché, école, poste de santé, mosquée, église, caserne, entre autres) et sont déduites dans un ordre fixe : attributs d'OpenStreetMap (confiance de 0,85 à 0,9), lieux nommés situés dans l'emprise (0,65), type d'enceinte (0,55), forme (cases rondes : circularité d'au moins 0,9 et surface d'au plus 80 m²) et valeur par défaut de l'habitat. Sur les 419 593 bâtiments, 375 096 sont des maisons de concession et 37 222 des annexes ; 1 469 sont des cases rondes, 1 012 de grands bâtiments d'usage inconnu, 375 des bâtiments industriels, 331 militaires, 308 des bureaux et 236 des écoles. Le nombre d'étages n'est connu que pour 82 bâtiments. Un logement ne porte jamais de nom.

## Exemples traités

Le tableau présente des codes réels du registre : la concession la plus proche de plusieurs lieux connus.

| Près de | Mémorisée et écrite | Machine | Secteur |
|:--|:--|:--|:--|
| Marché de Bandim, Bissau | Bandim 537 | 10-022-00537-4 | Bissau |
| Bissau Velho | Bissau Velho 345 | 10-033-00345-1 | Bissau |
| Ville de Gabú | Gabu 1203 | 62-042-01203-8 | Gabú |
| Ville de Canchungo | Canchungo 1381 | 55-091-01381-7 | Canchungo |
| Ville de Bubaque | Bubaque 501 | 32-071-00501-0 | Bubaque |
| Missirá, Bissau | Missira 101 | 10-050-00101-8 | Bissau |
| Missirá, Sonaco | Missirá 5101 | 65-073-05101-5 | Sonaco |

: Codes réels du registre.

Deux situations en illustrent l'usage. Un conducteur de moto-taxi demande où aller ; le passager répond « Bandim, quinhentos e trinta e sete » ; le conducteur tape `bandim 537`, et l'application affiche la concession, son secteur et son portail. Une personne à Gabú tape `missirá 5101` ; le numéro se trouve dans le bloc 5 000–5 499, qui appartient à Missirá dans le secteur de Sonaco, et l'application s'y rend directement, tandis que `missira 101` se trouve dans 0–4 999, à Bissau. Il n'y a rien à choisir dans une liste et rien à deviner.

# Implémentation

**Moteur de référence.** `engine/reference/gw_codes.py` implémente toutes les fonctions de la section 4 (secteurs, lieux, clés de nom, noms de plaque, attribution des blocs, numérotation de Hilbert, insertion, chiffre de contrôle et codes de point) avec la seule bibliothèque standard de Python, accompagnées de leurs tests unitaires. `engine/SPEC.md` est la spécification normative, et `engine/data/register.json` contient ce dont un décodeur a besoin hors ligne : les secteurs, chaque lieu avec son nom de plaque, ses alias, sa clé de nom et ses blocs figés, ainsi que les contours des secteurs et des îles ; `engine/data/border.geojson` contient la frontière nationale de la section 4.3.

**Vecteurs de conformité.** `engine/reference/vectors.json` contient 425 clés de nom, 300 formes de code, 660 résolutions de formes mémorisées, 256 codes de point et 6 cas de numérotation. Toute implémentation doit les reproduire à l'identique. L'émetteur N-Ways a numéroté la première émission avec sa propre implémentation et aurait refusé l'opération si un seul des 241 673 numéros avait différé de celui du moteur de référence.

**Registre.** `registry/` publie tous les codes émis : un fichier CSV compressé en gzip par secteur, avec une ligne par concession (formes machine, mémorisée et écrite ; aire ; nom officiel ; numéro ; chiffre de contrôle ; statut ; date d'émission ; point et type d'entrée ; Plus Code ; classe d'usage ; bâtiments ; surface de plancher ; classe d'habitat ; code postal), la table figée des aires `areas.csv` et `MANIFEST.json`, qui donne les décomptes et l'empreinte SHA-256 de chaque fichier. Les 241 673 codes sont publiés ; aucun n'est retenu.

**Serveur et API.** `server/` est un serveur du registre écrit avec la bibliothèque standard de Python, que toute institution peut déployer en une commande (`docker compose up`). Il importe le registre dans SQLite après avoir vérifié chaque empreinte et chaque décompte, sert une API JSON sous `/v1` (état, informations, fiche complète d'un code, recherche sous toute forme, code en un point, codes proches d'un point, vérification, codage et décodage des points, secteurs, lieux et listes paginées), et réexporte le registre octet pour octet. Un déploiement fonctionne en lecture seule, sauf si l'État ou N-WAYS LIMITED le désigne comme émetteur. Il ne peut exister qu'un seul émetteur par pays, car deux émetteurs travaillant sur la même table de blocs attribueraient deux fois le même numéro. Le point d'émission applique exactement les règles des sections 4.5, 4.9 et 4.10 ; un test de parité avec l'implémentation propre de l'émetteur a concordé sur chaque numéro, forme, lieu et bloc. L'API est décrite dans `server/openapi.yaml` et, avec des requêtes et des réponses réelles, dans `docs/api.md`.

# Évaluation

Toutes les mesures de cette section sont calculées sur le registre publié complet avec le moteur de référence ; les programmes se trouvent dans le dépôt.

## Unicité et couverture

Chaque concession des 39 secteurs du pays possède exactement un code : 241 673 codes, 241 673 formes machine distinctes, et aucun couple de codes partageant la même clé de nom et le même numéro. Dans la table des aires, les blocs de chaque nom sont disjoints et s'achèvent à 99 999 ou en deçà. Toutes les entrées se trouvent à l'intérieur de la frontière nationale ou à moins de 248 m de sa ligne simplifiée, et aucune n'est à plus de 300 m hors de la frontière non simplifiée (section 4.3). Tous les codes sont provisoires jusqu'à leur confirmation par les habitants (section 12).

## Exactitude du décodage

Nous avons décodé chaque code du registre de trois manières. Les 241 673 formes machine se lisent comme leur propre lieu et leur propre numéro. Les 241 673 formes mémorisées, résolues à l'échelle nationale par l'équation (16) sans aucun contexte, renvoient leur propre forme machine. Lorsque les formes mémorisées sont tapées en minuscules et sans accents, comme le font de nombreux téléphones, les 241 673 se résolvent grâce à la règle de la cédille de la section 4.7. Avant cette règle, 681 codes (0,28 %) de sept lieux dont le nom contient un *ç* (Praça, Sinchã Içaga, Serração et quatre autres) échouaient à ce test. La règle fait correspondre la graphie sans cédille à la clé existante ; aucune clé, plage ni aucun bloc n'a changé.

## Détection des erreurs

Nous avons tiré 5 000 codes au hasard et appliqué à leurs formes machine toutes les substitutions d'un chiffre et toutes les permutations de chiffres adjacents, puis lu les résultats.

| Partie de la forme machine | Substitutions | Refusées | Acceptées sous un autre nom |
|:--|--:|--:|--:|
| Numéro (5 chiffres) | 225 000 | 100 % | 0 |
| Chiffre de contrôle | 45 000 | 100 % | 0 |
| Indice du lieu (3 chiffres) | 135 000 | 97,5 % | 2,5 % |
| Secteur (2 chiffres) | 90 000 | 98,7 % | 1,3 % |
| **Permutations adjacentes** | | | |
| Numéro | 13 041 | 100 % | 0 |
| Indice du lieu | 8 773 | 98,2 % | 1,8 % |
| Secteur | 4 669 | 98,4 % | 1,6 % |

: Détection des erreurs de transcription sur 5 000 formes machine tirées au hasard.

Toute erreur sur le numéro ou le chiffre de contrôle est refusée, comme le garantit la construction de Damm. Les erreurs sur les chiffres du secteur ou du lieu sont refusées, sauf lorsqu'elles tombent par hasard sur un numéro valide d'un lieu d'un autre nom, que l'écran nomme alors, si bien que l'erreur est visible.

Les habitants emploient la forme mémorisée sans chiffre de contrôle, et pour cette forme la détection ne peut être garantie. Sur les mêmes 5 000 codes, un chiffre erroné dans le numéro prononcé a donné, parmi les 121 981 résultats qui étaient des numéros valides, une autre concession émise du même lieu dans 59,4 % des cas, une concession d'un autre lieu du même nom dans 0,6 %, un numéro non émis (refusé par le registre) dans 34,5 % et un numéro hors de tout bloc dans 5,5 %. L'erreur au sein du même lieu est le cas courant, et l'ordre de Hilbert la maintient à proximité : un dernier chiffre erroné tombe à une distance médiane de 59 m de la concession visée, contre 523 m pour deux concessions du même lieu tirées au hasard. C'est pourquoi l'application affiche le lieu et le secteur avant de lancer la navigation, et pourquoi les systèmes échangent la forme machine.

## Longueur des codes

La figure 7 montre la répartition des concessions par lieu, et la figure 8 la longueur des numéros émis.

![Nombre de lieux $A(n)$ selon leur nombre de concessions $n$ (3 336 lieux en usage). Le lieu médian compte 31 concessions ; 79 lieux en comptent 500 ou plus.](figures/sizes.svg){width=80%}

![Concessions $C(\ell)$ selon le nombre de chiffres $\ell$ de leur numéro, avec des plages nationales par nom ($R_{\text{nat}}$, tel qu'émis) et dans la variante où chaque lieu a sa propre plage commençant à 1 ($R_{\text{own}}$).](figures/digits.svg){width=78%}

| Chiffres | Concessions | Part |
|:--|--:|--:|
| 1 | 12 866 | 5,3 % |
| 2 | 71 904 | 29,8 % |
| 3 | 99 673 | 41,2 % |
| 4 | 54 233 | 22,4 % |
| 5 | 2 997 | 1,2 % |

: Longueur des numéros émis.

Le numéro moyen compte 2,85 chiffres, et 98,8 % des logements ont quatre chiffres ou moins. Les logements ruraux ont surtout deux ou trois chiffres, ceux des villes trois ou quatre. À Bissau, 49 lieux comptent en médiane 710 concessions chacun ; le plus grand, Bono, en compte 3 274 et son numéro le plus élevé lors de la première émission est 6 547. Ailleurs, le lieu médian compte 30 concessions et le plus grand, Buba, 1 912. Dans le registre, le nom de plaque d'un code compte en moyenne 7,3 caractères ; le code mémorisé, nom et numéro, en compte 11,1. Vingt-huit lieux en usage (tous signalés à un conseil) dépassent encore la limite de plaque de l'équation (6).

## Réserve et croissance

Le taux de remplissage de chaque bloc lors de la première émission, nombre de concessions rapporté à la taille du bloc, est au plus de 0,25 par l'équation (9), avec une médiane de 0,17. Aucun bloc n'a nécessité de continuation lors de la première émission.

## Codes de point

Pour chacun des 241 673 points d'entrée, nous avons calculé le code de point puis l'avons décodé. La distance entre le point et le centre décodé a une médiane de 1,65 m, un 99e centile de 4,97 m et un maximum de 6,61 m (à Gabú, où les mailles mesurent 9,4 m). Aucun point n'a dépassé la borne de l'équation (20).

# Conceptions étudiées et écartées

La conception retenue est la dernière d'une série. Chaque changement décrit ci-dessous a été motivé par une mesure.

| Option | Exemple | Motif du rejet |
|:------------------------------|:--------------------|:----------------------------------------|
| Code de grille alphanumérique | 7C36VC23+VX4 | lettres nommées en portugais, que la plupart des locuteurs du kriol n'emploient pas |
| Chiffres nationaux seuls | 00228 00537 | dix chiffres sans aucune prise pour la mémoire |
| Secteur et numéro | Gabú 14738 | cinq chiffres dans les grands secteurs ; noms de secteur peu employés |
| Lieu et numéro, qualifiés par le secteur | Bandim 275, Catió | pas unique à lui seul ; échoue dès que le code voyage |
| Noms officiels complets | Sinchã Samba Camarà 12 | trop long à dire avec un numéro |
| **Nom de plaque et numéro dans une plage nationale par nom** | **Bandim 537** | **retenu** |

: Formes de code étudiées.

**Qualifier les noms répétés par le secteur.** Une première conception affichait le secteur à côté d'un mot répété et proposait d'abord le lieu le plus proche. Un code qui dépend du contexte échoue précisément quand il voyage : lu au téléphone, écrit sur un colis ou tapé loin du lieu. Les plages nationales suppriment cette dépendance.

**Une plage par lieu.** Donner à chaque lieu sa propre plage raccourcirait les numéros : la longueur moyenne passerait de 2,85 à 2,69 chiffres et aucun numéro n'aurait besoin de cinq chiffres (figure 8), mais 92 745 logements dans 1 039 lieux partageraient leur code prononcé avec un autre logement. Nous avons jugé 0,16 chiffre en moyenne un prix modeste pour des codes uniques.

**Les noms officiels comme mots de lieu.** Avec les noms officiels, 335 noms seraient partagés par 856 lieux ; avec les noms de plaque, 407 par 1 039, car les noms courts coïncident plus souvent. Les lieux à cinq chiffres sont passés de 21 à 25, les quatre nouveaux étant tous signalés à un conseil. Le gain de brièveté du mot prononcé l'emporte sur l'allongement des numéros dans quelques lieux.

**Trop peu de lieux à Bissau.** Avec les seuls 28 points de bairro qu'OpenStreetMap comptait pour Bissau, les plus grands lieux de la ville auraient atteint 5 833 concessions et des numéros à cinq chiffres (jusqu'à 11 665). L'ajout des anciens villages absorbés par la ville a ramené tous les numéros des lieux confirmés de Bissau à quatre chiffres ou moins.

**Caractères de contrôle.** Un caractère de contrôle qui détecte toute erreur simple et toute permutation adjacente exige soit onze symboles avec un module premier, soit un quasi-groupe comme celui de Damm [@verhoeff1969; @damm2007]. Les noms des lettres en portugais riment en deux grandes familles (*bê, cê, dê, gê, pê, quê, tê, vê, zê* ; *efe, ele, eme, ene, erre, esse*), si bien qu'une lettre serait elle-même source d'erreurs. La forme machine porte donc un chiffre décimal ; ni les plaques ni les habitants ne le voient.

**Exclure les zones officielles.** Une conception qui n'émettait aucun code là où des numéros de porte officiels pouvaient exister aurait laissé le centre de Bissau sans adresse utilisable tant que sa numérotation reste incertaine. Chaque logement a désormais un code, et l'adresse officielle, là où elle existe, est affichée en premier.

**Reporter les bairros denses.** Une conception qui attendait le tracé des murs sur l'imagerie avant de numéroter les bairros les plus denses de Bissau a été remplacée par l'émission de toutes les concessions en une fois, avec la règle urbaine prudente de la section 4.4 : lorsque les habitants signalent que deux concessions forment un seul logement, l'un des codes devient un alias et rien n'est renuméroté.

**Un regroupement dépendant de l'ordre.** Deux exécutions sur les mêmes données, avec les lignes dans un autre ordre, ont donné 241 695 et 241 713 concessions. Trier les bâtiments avant le regroupement, et départager les égalités le long de la courbe de Hilbert par l'identifiant stable de la concession, a rendu le résultat déterministe, si bien que toutes les implémentations produisent les mêmes numéros.

# Bénéfices pour les citoyens

Pour une famille de Bandim, d'une morança de Nhacra ou d'Orango, un code change quatre choses du quotidien.

**Être trouvé.** Aujourd'hui, un visiteur, un moto-taxi ou un livreur est guidé par téléphone, de repère en repère. Avec un code, la personne prononce une courte phrase et l'application conduit au portail.

**Justifier de son domicile.** Banques, agents de monnaie mobile, écoles et employeurs demandent une adresse vérifiable. Avant ce registre, deux concessions du pays avaient un numéro de porte dans les données ouvertes ; chacune a désormais un code que l'on peut dire, écrire et vérifier dans un registre ouvert.

**Recevoir des biens et des services.** Les proches de la diaspora, les commerces et les services d'eau et d'électricité peuvent adresser un envoi à un code plutôt qu'à une description, et un ménage peut demander un raccordement ou une réparation au bon portail.

**Simplicité.** Rien n'est demandé au ménage. Chaque concession déjà présente sur la carte a reçu son code le 20 octobre 2026 ; l'application l'affiche d'un geste, en portugais, en anglais ou en français. Il est gratuit, ne demande aucun document, ne conserve aucune donnée personnelle et ne constitue pas un titre foncier.

**Portée estimée.** Le nombre de personnes vivant dans des concessions dotées d'un code est

$$
P = N_c \cdot \bar{m}, \qquad \bar{m} = \frac{P_{\text{rec}}}{N_c} = \frac{2\,213\,173}{241\,673} \approx 9{,}2,
\tag{21}
$$
où $N_c$ est le nombre de concessions dotées d'un code et $\bar{m}$ le nombre moyen d'habitants par concession. Par construction, l'estimation est égale à la population recensée, soit environ 2,2 millions de personnes. L'hypothèse déterminante est que les emprises couvrent toutes les concessions habitées. S'il manque 5 à 15 % des concessions dans les données d'emprise, ce qui est plausible pour les constructions récentes en périphérie des villes, les codes atteignent d'abord 1,9 à 2,1 millions de personnes, et les autres obtiennent un code sur place grâce à « Ajouter mon logement » (section 4.10). Ceux qui en bénéficient le plus sont ceux qui disposent aujourd'hui du moins : les familles des bairros denses en périphérie de Bissau, les tabancas éloignées de tout repère, les îles, et plus d'un adulte sur trois qui lit mal, pour qui un lieu familier et un nombre sont plus faciles que des lettres.

# Logistique et commerce

En Guinée-Bissau, la livraison dépend du téléphone et, pour les îles, des bateaux. Des sources professionnelles estiment le coût d'une tentative de livraison du dernier kilomètre en Afrique à environ 2,70 dollars et font état de taux de réussite au premier passage de 60 % seulement chez la plupart des transporteurs [@nextbillion2023] ; un éditeur de logiciels d'itinéraires retient, dans un exemple de coûts pour le Moyen-Orient et l'Afrique, un taux d'échec de 5 % pour un grand opérateur [@locus2026]. Ce sont des chiffres de la profession, non des mesures publiées dans des revues à comité de lecture. Nous ne connaissons aucune mesure pour la Guinée-Bissau.

Le code apporte à une entreprise de logistique une clé stable pour chaque client, que l'on peut conserver, dédoublonner et relier aux livraisons passées ; le calcul de l'itinéraire jusqu'au portail avant le départ du livreur ; une saisie vérifiée, puisque la forme machine refuse toute erreur sur un chiffre au moment de la commande et non sur la route ; et un accès ouvert, puisque le registre, le moteur et les règles peuvent être utilisés dans n'importe quel système, hors ligne et sans paiement. Le marché de Bandim, les *lumos* régionaux et les négociants qui achètent la noix de cajou, principale exportation du pays, peuvent adresser marchandises et paiements à une concession plutôt qu'à la ville la plus proche. Les bateaux vers Bubaque, Bolama et les autres îles peuvent porter un code sur chaque colis.

**Économie estimée.** Soit $f_0$ la part des premières tentatives qui échouent avec des adresses en texte libre, $f_1$ cette part avec un code, et $c$ le coût d'une tentative. L'économie pour mille livraisons est

$$
S = 1\,000 \,(f_0 - f_1)\, c.
\tag{22}
$$

| Scénario | $f_0$ | $f_1$ | $c$ (US\$) | $S$ pour 1 000 livraisons (US\$) |
|:---------|-----:|-----:|------:|------------:|
| Bas | 0,15 | 0,10 | 2,70 | 135 |
| Central | 0,25 | 0,07 | 2,70 | 486 |
| Haut | 0,40 | 0,05 | 2,70 | 945 |

: Économies estimées sur les livraisons, avec leurs hypothèses.

Ces fourchettes sont des hypothèses éclairées par les sources ci-dessus, non des mesures faites en Guinée-Bissau. Le programme de mesure de la section 13 est conçu pour les remplacer.

# Services d'urgence

Une ambulance, des pompiers ou une patrouille de police rencontrent le problème du livreur, avec des enjeux plus lourds. Une enquête à l'échelle du continent sur les services médicaux d'urgence n'a identifié de systèmes que dans 16 des 54 pays d'Afrique, desservant moins de 9 % de sa population [@mouldmillman2017]. Là où des systèmes existent, la localisation du patient est une cause reconnue de retard : une étude qualitative menée à Kigali a montré que les équipages et les régulateurs dépendaient de la connaissance locale de l'appelant et devaient passer plusieurs appels pour établir le lieu [@hunt2023]. Nous ne connaissons aucune mesure publiée pour la Guinée-Bissau.

Un code aide un régulateur en quatre étapes. L'appelant prononce une phrase (« Missirá, cinco mil cento e um ») ; le registre renvoie une concession, à Sonaco, et non l'un des treize autres lieux nommés Missirá. Le régulateur relit le lieu et le secteur. L'équipage est envoyé au portail, et un code de point désigne tout point sans concession, par exemple un accident de la route. Tout cela fonctionne hors ligne, car le moteur et les fichiers du registre n'ont pas besoin de réseau.

**Effet estimé.** Larsen et ses collègues ont modélisé la survie après un arrêt cardiaque extrahospitalier comme diminuant de 2,3 points de pourcentage par minute avant la réanimation cardio-pulmonaire, de 1,1 par minute avant la défibrillation et de 2,1 par minute avant les soins avancés [@larsen1993]. Là où un seul équipage assure les trois, un retard $\Delta t$ dans la localisation du patient réduit la survie de

$$
\Delta S = (2{,}3 + 1{,}1 + 2{,}1)\,\Delta t = 5{,}5\,\Delta t \ \text{points de pourcentage}.
\tag{23}
$$

| Minutes gagnées pour localiser le patient, $\Delta t$ | 1 | 2 | 5 |
|:--|--:|--:|--:|
| Survie gagnée, $\Delta S$ (points) | 5,5 | 11 | 27,5 |

: Sensibilité de l'équation (23) au temps gagné.

Le modèle a été ajusté dans le comté de King, dans l'État de Washington, où les taux de survie et les délais d'intervention diffèrent fortement de ceux de la Guinée-Bissau, et il n'est linéaire que sur l'étendue de ses données ; les chiffres indiquent donc un ordre de grandeur, non une prévision. Le sens de l'effet ne fait pas de doute : là où trouver le portail prend des minutes, supprimer la recherche compte autant qu'un véhicule plus rapide.

# Coordination et planification publiques

Un code est une clé partagée. Lorsque les ministères, la Câmara Municipal, les services publics et l'INE désignent une concession par le même code, leurs fichiers peuvent être croisés sans rapprocher des noms et des descriptions. L'étude de la Banque mondiale en fait un bénéfice majeur de l'adressage pour les collectivités locales : un répertoire d'adresses recense les locaux plus complètement que le rôle fiscal et montre qui en est absent [@farvacque2005].

**Le recensement.** Le recensement de 2026 de l'INE a géoréférencé les logements. Une table de correspondance entre codes et zones de dénombrement permettrait à chaque jeu de données de servir l'autre : le recensement apporte au registre le nombre de ménages, et le registre fournit aux équipes d'enquête une base de 241 673 concessions dotées de codes stables, où tirer des échantillons et où revenir, sans conserver aucun nom.

**Planifier avec des décomptes.** Le registre dénombre les concessions par région, secteur, lieu, classe d'habitat et classe de bâtiment, et chaque décompte peut être recalculé à partir des fichiers ouverts. La loi d'aménagement de 2026 appelle des instruments cartographiques [@geocracia2026] ; le registre en est un, ouvert et disponible dès maintenant.

**Accès aux services.** Le tableau donne les distances à vol d'oiseau entre les concessions et l'équipement cartographié le plus proche de chaque type, sur un échantillon aléatoire de 20 000 concessions et les données cartographiques du 20 octobre 2026.

| Équipement | À moins de 2 km | À moins de 5 km | Distance médiane |
|:--|--:|--:|--:|
| Établissement de santé | 20,8 % | 29,4 % | 16,1 km |
| École | 27,7 % | 36,7 % | 12,7 km |
| Police | 11,4 % | 22,8 % | 28,0 km |
| Pharmacie | 14,6 % | 28,5 % | 20,4 km |

: Distance entre les concessions et l'équipement cartographié le plus proche.

Ces chiffres décrivent la carte plus que le pays : peu de postes de santé, d'écoles et de postes de police sont cartographiés hors de Bissau, si bien que les distances sont surestimées. Ils montrent où la cartographie est le plus nécessaire, et un ministère peut substituer sa propre liste d'équipements et les recalculer en quelques minutes.

**Coût évité.** L'adressage classique des mêmes concessions coûterait environ

$$
C = N_c \cdot c_d = 241\,673 \times 5{,}7\ \text{US}\$ \approx 1{,}4\ \text{million de US}\$,
\tag{24}
$$
où $c_d$ est le coût moyen par porte dans les villes africaines selon la Banque mondiale, aux prix de 2005 [@farvacque2005], avant même de nommer des rues qui n'existent pas et d'atteindre les îles. Avec $c_d$ compris entre la moitié et le double de cette moyenne, $C$ se situe entre 0,7 et 2,8 millions de dollars aux prix de 2005. Les codes ont été émis pour toutes les concessions en une seule fois, sans coût pour l'État.

**Croissance.** Les nouvelles concessions reçoivent un code à mesure qu'elles apparaissent (section 4.10), si bien que le registre montre mois après mois où le pays croît et où routes, eau, écoles et postes de santé seront nécessaires ensuite.

# Vie privée, sécurité et gouvernance

**Vie privée.** Les codes décrivent des lieux, jamais des personnes. Les concessions résidentielles ne portent ni nom ni donnée sur leurs occupants, et le nombre de ménages n'est jamais déduit. Les bâtiments commerciaux et publics portent leur nom public. Les photographies prises dans « Ajouter mon logement » ne sont conservées que pour vérification. Un ménage peut demander que sa porte soit masquée : la concession garde son code et son portail n'est plus affiché. Les partenaires ne voient un code qu'avec le consentement du client. En l'absence de loi nationale sur la protection des données, le modèle applique les principes de l'Acte additionnel de la CEDEAO [@ecowas2010], et des règles nationales plus strictes prévaudront dès leur adoption.

**Sécurité.** Les casernes et les postes de police conservent leur code et leur contour, déjà visibles sur les cartes publiques, mais aucun profil de bâtiment. Une maison sacrée de la religion traditionnelle (*baloba*) est conservée mais n'est pas publiée sans l'accord de la communauté. Un code ne prouve rien quant à la propriété ou à l'usage du sol ; l'application le rappelle chaque fois qu'un logement est ajouté.

**Confirmation.** Tout code commence provisoire. Il devient confirmé lorsque les habitants s'accordent dans l'application sur son exactitude (deux téléphones, dont au moins un au portail, avec une majorité de réponses concordantes), et les corrections du portail suivent le même consensus. Aucun code n'est revu à la main.

**Gouvernance.** Un émetteur unique par pays garantit que deux logements ne partagent jamais un code. Les secteurs, les codes émis, les clés de nom et les blocs de chaque nom ne changent jamais ; ajouter des blocs n'est pas un changement. Les profils de bâtiment évoluent sur preuve. La Câmara Municipal ou l'administration d'un secteur, avec les *régulos* et la communauté, peut renommer un lieu (l'ancien nom devient un alias et aucun numéro ne change), choisir une fois un nom de plaque provisoire ou ajouter des lieux, qui reçoivent de nouveaux blocs. Si l'État publie un système d'adresses, ses adresses sont affichées en premier et les codes deviennent des références croisées. Le dépôt, le registre et les règles peuvent être transférés à l'État ou à l'organisme qu'il désigne, l'INE, la Câmara Municipal de Bissau ou les Correios, sous les licences ouvertes et sans bifurcation du moteur.

# Limites et travaux futurs

- **Lieux.** OpenStreetMap et GeoNames couvrent le pays de façon inégale, et la liste des bairros de la Câmara Municipal est nécessaire à Bissau.
- **Noms de plaque.** 356 noms de plaque restent provisoires jusqu'au choix des conseils ; 28 n'ont encore aucune forme dans la limite.
- **Concessions.** Le regroupement est déduit. Dans les quintais urbains clos, les règles ne retrouvent entières que 13 % des concessions ; les corrections des habitants les rectifient au fil du temps.
- **Portails.** Seuls 12 portails sont cartographiés ; les points d'entrée du registre sont donc les centres des concessions jusqu'à ce que livreurs et habitants confirment les portails.
- **Hauteurs.** Les hauteurs sont inconnues pour presque tous les bâtiments ; les surfaces de plancher sont donc des estimations.
- **Équipements.** Les équipements sont peu cartographiés ; les chiffres d'accès de la section 11 sous-estiment donc l'accès.
- **Erreurs orales.** Sans chiffre de contrôle, un chiffre erroné désigne le plus souvent une autre concession réelle (section 6.3) ; seul l'affichage du lieu décodé atténue ce risque.
- **Frontières.** Les codes sont uniques en Guinée-Bissau. Un nom de lieu partagé avec le Sénégal ou la Guinée (Madina, Missirá) peut y produire le même code prononcé ; l'application affiche le pays sur chaque fiche.

Le programme de mesure ci-dessous remplacera par des données de terrain les estimations des sections 8 à 11. Il sera conduit dans trois bairros de Bissau (Bandim, Bairro Militar, Cuntum) et dans un groupe de tabancas de Biombo ou de l'Oio.

| Mesure | Méthode | Objectif |
|:----------------------------|:------------------------------|:---------------------|
| Mémorisation de son propre code après quatre semaines | habitants interrogés en kriol, sans l'application | au moins 80 % exacts |
| Réussite de la livraison au premier passage | livreurs partenaires, avec et sans code | au moins 20 points de plus avec un code |
| Temps entre l'arrivée dans le bairro et le portail | horodatage des livreurs | divisé par deux |
| Portails confirmés | habitants et livreurs | 10 000 |
| Temps de localisation des appels d'urgence | avec un service d'ambulance ou de pompiers volontaire | mesuré, puis divisé par deux |
| Mémorisation selon la forme | code, forme purement numérique et code de grille pour un même logement | mesurée pour chaque forme |

: Mesures de terrain prévues.

Les travaux futurs comprennent la comparaison des concessions avec les logements géoréférencés du recensement, si l'INE y consent ; le tracé des murs et des portails sur l'imagerie dans les bairros d'évaluation ; et la relecture, par des locuteurs natifs, des lectures en kriol et des règles de réduction de l'équation (8), qui ne peuvent fusionner des clés que par alias, jamais scinder une plage.

# Conclusion

Les logements de Guinée-Bissau peuvent recevoir une adresse sans nommer les rues ni numéroter les portes, en s'appuyant sur ce que les habitants disent déjà : le nom de leur bairro ou de leur tabanca, suivi d'un nombre. Rendre ce code unique a exigé une plage nationale de numéros par nom, divisée en blocs figés ; le rendre robuste a exigé un chiffre de contrôle dans la forme machine et une numérotation qui garde les voisins proches ; le rendre durable a exigé des règles qui ne renumérotent jamais un code émis. Sur le registre complet de 241 673 codes, le modèle est unique, court (2,85 chiffres en moyenne) et décodable sans contexte, et il refuse toute erreur sur un chiffre du numéro de sa forme machine. Ses bénéfices pour les citoyens, les livreurs, les services d'urgence et l'État dépendent de l'usage, que le programme de terrain mesurera. Le modèle, son moteur, son registre et son serveur sont ouverts et conçus pour être remis à l'État.

# Disponibilité des données et du code {-}

Le moteur, la spécification, le registre, le serveur et cet article sont publiés à l'adresse <https://github.com/n-ways/open-addresses-guinea-bissau> [@nways-gw]. Le code est sous Apache License 2.0, les données sous Open Database License 1.0 et les documents sous CC BY 4.0. Toute utilisation doit porter la mention : « N-Ways Addressing for Guinea-Bissau, © N-WAYS LIMITED (nways.ng) ». Les figures sont tracées à partir de données calculées par `tools/paper_figures.py` sur le registre publié.

# Remerciements {-}

Nous remercions les contributeurs d'OpenStreetMap qui ont cartographié les bâtiments, les moranças et les îles de la Guinée-Bissau ; Google Research et Microsoft pour la publication de leurs emprises de bâtiments, et l'Overture Maps Foundation pour leur diffusion ; GeoNames pour son répertoire toponymique ; et l'Union postale universelle pour sa documentation sur l'adressage. Les chiffres du recensement sont ceux publiés par l'Instituto Nacional de Estatística.

# Références {-}

::: {#refs}
:::
