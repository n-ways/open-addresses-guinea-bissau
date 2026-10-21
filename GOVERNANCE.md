# Governance

## Who maintains this today

N-WAYS LIMITED maintains the Guinea-Bissau model, engine and registry in this public repository, and is the single issuer of codes until a Guinea-Bissau authority takes the role over. The codes were issued on 20 October 2026.

- Maintainers: the N-Ways Addressing Group.
- Decisions: a change to the code format, the check digit or the frozen tables is published as a proposal, open for comment for at least 30 days, and decided by the maintainers with the national bodies consulted; everything else follows the rules below.
- These are "endereços N-Ways" (N-Ways addresses). They are not official addresses, postcodes or land titles, and are never called that until a Guinea-Bissau authority adopts them.

## What can change, and how

| Change | Allowed? | How |
|---|---|---|
| A new compound or structure gets a code | yes, every day | the registry issues the next reserved number (SPEC.md "Registry"); people confirm it |
| A compound regrouped (two moranças found to be one, or one split) | yes | codes kept: a merge keeps both codes as aliases of one compound; a split keeps the old code on the part with the main gate and gives the others new numbers |
| A building demolished | yes | its code is retired, never reused |
| Building profile attributes (use, size, name, status) | yes | inferred automatically, corrected by people and partners (model.md "Building profile") |
| Sector table (numbers, grid frames, outlines) | **never** once issued | a boundary change makes a new table; codes keep the sector they were issued in |
| Code format, alphabet, check digit | only with a new major version | announced, with a converter; old codes stay valid for ever |
| Spot-code grid of a sector | never once issued | as for the sector table |

Every change to `model/`, `engine/` and `server/` goes through a pull request with the reference engine's vectors and every test passing ([CONTRIBUTING.md](CONTRIBUTING.md)).

## One issuer

Codes are issued by one issuer only: today N-WAYS LIMITED, later the body the State designates. A number is unique because its issuer knows every number already given in the area and every block already taken by the name; two issuers working from the same registry would give the same free number to two compounds. Any number of read-only copies of the registry may run (the server in [`server/`](server/) is read-only unless it is given issuing keys), and all give the same answers. A deployment issues codes only when the State, or N-WAYS LIMITED on its behalf, has designated it as the issuer. When the role passes to another body, the new issuer imports the last export of the outgoing one, and the outgoing deployment becomes read-only, in that order.

## Institutions in Guinea-Bissau

An address register must stay stable for decades, longer than any one administration. The work therefore relies on technical bodies whose mandates continue across changes of government, and on agreements that do not depend on any one office holder:

1. **Instituto Nacional de Estatística (INE)**: ran the June 2026 census with georeferenced dwellings; the most useful partner for checking compounds and households.
2. **Câmara Municipal de Bissau**: street names, the official bairro list, house numbers in Bissau.
3. **Correios da Guiné-Bissau**: the 4-digit postcodes, P.O. boxes, delivery.
4. **Direcção Geral de Geografia e Cadastro (DGGC)**: sector boundaries, cadastre, the Bissau datum.
5. **ARN-TIC** (telecom regulator): the data protection provisions of the Electronic Transactions bill.
6. **Emergency services** (112 / 1313, not yet reconciled), Cruz Vermelha da Guiné-Bissau, health centres.
7. Couriers, mobile-money agents (Orange Money and others), cashew buyers' cooperatives, NGOs working in tabancas.

Local knowledge enters through people, not through officials alone: régulos and *homens grandes* of tabancas, bairro committees in Bissau, and N-Ways users who confirm moranças and gates.

## Hand-over to a national body

The repository is built to be handed over whole:

- It contains everything a national body needs: the frozen sector table, the engine spec and reference script, the registry and its history, and these rules.
- On hand-over, the receiving body (for example INE, the Câmara Municipal de Bissau for the Bissau sector, or Correios da Guiné-Bissau) becomes maintainer; N-Ways stays a contributor and keeps reading the codes in its app.
- Existing codes stay valid after hand-over. The receiving body may add an official layer (for example postcodes in the postal line) without changing them.
- If two bodies want it (for example Bissau city and a national agency), the Bissau sector (number 10, with 11-19 reserved) can be handed over on its own.
