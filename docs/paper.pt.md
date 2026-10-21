---
title: "Um código para cada morança: um modelo nacional de endereçamento para a Guiné-Bissau"
short-title: "Endereçamento N-Ways para a Guiné-Bissau"
kind: "Artigo de investigação"
author:
  - "The N-Ways Addressing Group"
affiliation: "N-WAYS LIMITED (nways.ng)"
date: "21 de outubro de 2026"
abstract-title: "Resumo"
abstract: |
  A Guiné-Bissau não tem uma morada de uso corrente abaixo do nome de uma vila, de um bairro ou de uma tabanca: um formato de código postal de quatro algarismos foi registado na União Postal Universal em 2005, mas só dois códigos estão atestados, e no mapa aberto do país apenas dois edifícios têm número de porta. Apresentamos um modelo de endereçamento em que cada morança ou quintal recebe um código formado por um nome de lugar que as pessoas já usam e um número curto, como *Bandim 537*. Os lugares que partilham um nome tiram os seus números de uma única faixa nacional desse nome, dividida em blocos fixos, de modo que o código dito identifica uma só casa em todo o país, sem qualquer qualificativo. Os números seguem uma curva de Hilbert, para que vizinhos recebam números vizinhos; um algarismo de controlo de Damm protege a forma máquina; um código de ponto localiza qualquer ponto sem rede. Calculado a partir de 419 593 implantações de edifícios, o modelo atribuiu 241 673 códigos em 3 336 lugares e 39 setores. Apresentamos a matemática completa, uma implementação de referência, um registo aberto e um servidor pronto a instalar, e medimos sobre o registo completo a unicidade, o comprimento, a deteção de erros e a exatidão da descodificação. Capítulos próprios estimam os benefícios para os cidadãos, a logística, os serviços de emergência e o planeamento do Estado, com os pressupostos e os intervalos de sensibilidade.

  **Palavras-chave:** endereçamento; geocodificação; códigos postais; curva de Hilbert; algarismos de controlo; implantações de edifícios; Guiné-Bissau.
rights: "© 2026 N-WAYS LIMITED. Texto sob licença CC BY 4.0; registo sob ODbL 1.0; código sob a Apache License 2.0."
lang: pt-PT
papersize: a4
fontsize: 11pt
geometry:
  - margin=24mm
  - top=30mm
---

# Introdução

Uma morada é uma infraestrutura pública. Permite a um agregado receber uma carta, uma encomenda ou uma visita; permite a uma ambulância chegar a um doente; permite a uma empresa de serviços, a um banco ou a um ministério referirem-se à mesma habitação sem a descrever. A União Postal Universal estima que uma grande parte da população mundial vive sem morada utilizável e considera o endereçamento uma condição prévia do serviço postal, da inclusão financeira e do registo civil [@upu2012]. O estudo do Banco Mundial sobre o endereçamento em cidades africanas chegou a uma conclusão semelhante e acrescenta que os programas de endereçamento falham quando os moradores não os adotam [@farvacque2005].

A Guiné-Bissau é um caso claro. O seu formato de código postal existe no papel, mas só dois códigos estão atestados, ambos em Bissau [@upu-gw2005]; as portas não estão numeradas fora de algumas ruas centrais; e as duas formas mais comuns de descrever uma casa são o nome do bairro ou da tabanca e um ponto de referência. Uma entrega depende de um telefonema, uma equipa de ambulância depende do conhecimento local, e uma família na diáspora não consegue escrever um destino que um estafeta possa verificar.

Este artigo descreve e avalia um modelo de endereçamento construído para esta realidade. A sua unidade é a morança, ou o quintal murado, onde uma família vive. O seu código é uma palavra de lugar que as pessoas já dizem, seguida de um número curto: *Bandim 537*. Os objetivos do desenho, por ordem, são que as pessoas memorizem o código e o obtenham sem esforço; que o código dito seja único em todo o país por si só; que leve ao portão da morança; que funcione sem rede; e que nenhum código mude ou seja reutilizado.

As nossas contribuições são as seguintes.

1. Uma forma de código, e a aritmética que a sustenta, em que todos os lugares que partilham um nome tiram os números de uma única faixa nacional desse nome, dividida em blocos fixos. A forma dita dispensa assim setor, vila ou posição para ser descodificada (secção 4).
2. Uma especificação completa de cada etapa, das implantações de edifícios às moranças, aos lugares, aos nomes de placa, às chaves de nome, aos blocos, à numeração, ao algarismo de controlo e aos códigos de ponto, com cada fórmula e um exemplo resolvido sobre um código real (secção 4).
3. Uma implementação aberta: um motor de referência, vetores de conformidade, o registo completo de 241 673 códigos e um servidor que qualquer instituição pode instalar para responder a consultas e, se for designada, emitir códigos pelas mesmas regras (secção 5).
4. Uma avaliação, sobre o registo completo, da unicidade, do comprimento dos códigos, da cobertura, da deteção de erros e da exatidão da descodificação (secção 6), e o registo dos desenhos alternativos que medimos e rejeitámos (secção 7).
5. Estimativas, com pressupostos explícitos e intervalos de sensibilidade, do valor do modelo para os cidadãos, para a logística e o comércio, para os serviços de emergência e para o planeamento do Estado (secções 8 a 11).

A secção 2 passa em revista os sistemas existentes no país e a literatura internacional, e a secção 3 os dados. A secção 12 trata da privacidade, da segurança e da governação, a secção 13 dos limites e do trabalho futuro, e a secção 14 conclui.

# Enquadramento e trabalhos relacionados

## A Guiné-Bissau

A Guiné-Bissau ocupa cerca de 36 000 km² na costa atlântica da África Ocidental, entre o Senegal e a Guiné. O 4.º Recenseamento Geral da População e Habitação, realizado pelo Instituto Nacional de Estatística (INE) em junho de 2026, tinha contado 2 213 173 pessoas, mais de 600 000 alojamentos e cerca de 301 000 agregados até 22 de junho, segundo números preliminares [@lusa2026]. O recenseamento de 2009 contou 1 520 830 pessoas, o que corresponde a um crescimento médio de cerca de 2,2 % ao ano. O país divide-se em oito regiões e no Setor Autónomo de Bissau, e as regiões em 38 setores [@wiki-sectors; @pcgn2024]. A capital fica na Ilha de Bissau, ligada ao continente por estrada. Ao largo, o arquipélago dos Bijagós reúne cerca de 88 ilhas e ilhéus, muitos deles acessíveis apenas de barco.

O kriol é a língua franca, falada por cerca de 90 % da população no recenseamento de 2009; o português, língua oficial, por 27 %; fula, balanta, mandinga, papel e manjaco são as primeiras línguas mais faladas, e o francês é falado por cerca de 5 % [@wiki-languages]. A taxa de alfabetização dos adultos era de 63,9 % em 2022 [@fred-literacy]: 77,3 % nos homens e 52,2 % nas mulheres, uma diferença de 25,2 pontos percentuais [@wb-gender]. Uma morada que tenha de ser lida, soletrada ou escrita em português exclui portanto uma grande parte da população; uma morada feita de um lugar conhecido e de um número dito exclui muito poucos.

## Sistemas postais, de endereçamento e fundiários existentes

Entre 18 e 20 de outubro de 2026 analisámos os sistemas postais, de endereçamento e fundiários do país. O registo completo está em `docs/existing-systems.md`; as principais conclusões são as seguintes.

**Códigos postais.** A ficha de endereçamento da UPU para a Guiné-Bissau, datada de março de 2005, prevê quatro algarismos à esquerda do nome da localidade, com os exemplos `1000 BISSAU` e `1011 BISSAU`, este último para a Direção Geral dos Correios [@upu-gw2005]. Não encontrámos nenhum outro código, nenhuma lista e nenhum serviço de consulta. O domínio do operador postal, Correios da Guiné-Bissau [@correios-wiki], não respondia, e o GeoNames, principal conjunto aberto de códigos postais, não tem ficheiro para o país [@geonames-zip]. O correio é entregue em apartados ou levantado ao balcão.

**Portas e ruas.** Não encontrámos nenhum programa de toponímia, de numeração de portas ou de morada digital em notícias ou fontes oficiais de 2024 a 2026. No OpenStreetMap, que regista 99 131 contornos de edifícios no país, dois edifícios têm número de porta e oito têm nome de rua [@geofabrik-gw]. Os nomes de rua da Câmara Municipal de Bissau estão em uso em Bissau Velho, na Praça e nas avenidas centrais; não foi possível verificar se as portas aí estão numeradas segundo um plano oficial.

**Recenseamento e terra.** O recenseamento de 2026 foi anunciado com georreferenciação dos alojamentos [@forbes-census]; os seus mapas de recenseamento não são públicos, mas são o conjunto oficial mais próximo de um registo de moradas. A Lei da Terra (Lei n.º 5/98) atribui a propriedade da terra ao Estado, reconhece os direitos consuetudinários de uso e concede o uso privado por concessão [@leiterra1998]; o cadastro da Direção Geral de Geografia e Cadastro (DGGC) é parcial e sobretudo em papel. A Lei n.º 14/2026, de ordenamento do território e urbanismo, entra em vigor a 22 de outubro de 2026 e cria um quadro de planeamento, não moradas [@geocracia2026]. As plantas topográficas usam o datum nacional *Bissau* (EPSG:2095) ou o WGS 84 [@epsg2095], que diferem em dezenas de metros.

**Proteção de dados.** Não encontrámos nenhuma lei nem autoridade nacional de proteção de dados pessoais. A Guiné-Bissau está vinculada, em princípio, ao Ato Adicional A/SA.1/01/10 da CEDEAO sobre a proteção de dados pessoais [@ecowas2010], e um projeto de lei sobre transações eletrónicas foi submetido a consulta pública em maio de 2026 [@odemocrata2026].

## A prática internacional

A norma S42 da UPU define os componentes das moradas postais e os modelos pelos quais cada país as apresenta [@upu-s42]. É uma norma de formato: pressupõe que existam ruas, números e códigos postais. Onde não existem, a UPU e o Banco Mundial descrevem duas famílias de resposta [@upu2012; @farvacque2005]. A primeira é o endereçamento clássico: dar nome às ruas, numerar as portas ao longo delas e manter um registo. Nas 21 cidades africanas estudadas pelo Banco Mundial, só 8 % das ruas tinham nome antes do início do endereçamento, e o custo médio foi de cerca de 5,7 dólares por porta, a preços de 2005 [@farvacque2005]. A segunda é um código de grelha ou de coordenadas, calculado a partir da latitude e da longitude, que não exige trabalho de campo.

## Outros sistemas de código e por que razão não servem

Os códigos de grelha, como o Open Location Code (Plus Codes), são abertos, mundiais e calculáveis sem rede [@olc]. Um código como `7C36VC23+VX4` designa um quadrado de cerca de 3 m, não uma casa, e mistura letras com algarismos. Dito na Guiné-Bissau, cada letra tem de ser nomeada pelo seu nome em português, que a maioria dos falantes de kriol não usa; e dois membros de um agregado em cantos diferentes do quintal obtêm códigos diferentes. Os códigos nacionais só com algarismos evitam as letras, mas não oferecem nada a que a memória se agarre. Os códigos de setor e número são curtos de dizer, mas em setores com até 14 700 moranças os números chegam aos cinco algarismos, e muita gente não usa os nomes dos setores no dia a dia. As moradas de rua e número exigem ruas com nome, que não existem na maior parte do país. O quadro seguinte resume a comparação.

| Forma | Exemplo | Dita | Memorizada | Única por si | Exige |
|:---------------|:----------------|:-------------|:-------------|:---------|:--------------|
| Código de grelha | 7C36VC23+VX4 | letras, um sinal + | difícil | sim | nada |
| Setor e número | Bissau 48213 | fácil | razoável | sim | um registo |
| Algarismos nacionais | 00228 00537 | fácil | difícil | sim | um registo |
| Rua e número de porta | Rua 12, n.º 7 | fácil | fácil | com a vila | ruas com nome, um registo |
| **Palavra de lugar e número** | **Bandim 537** | **fácil** | **fácil** | **sim** | **um registo** |

: Formas de código comparadas para uso na Guiné-Bissau.

Os Plus Codes continuam, ainda assim, úteis como referência universal de coordenadas, e cada registo inclui um. O modelo aqui descrito não os substitui; acrescenta a camada que as pessoas dizem.

# Dados e fontes

**Implantações de edifícios.** O modelo parte de 419 593 implantações de edifícios, depois de retirados os contornos com menos de 6 m². Destas, 99 131 vêm do OpenStreetMap [@geofabrik-gw] e 320 462 são implantações obtidas por aprendizagem automática, do Google Open Buildings [@sirko2021] e da Microsoft [@microsoft-buildings], que obtivemos através do tema de edifícios do Overture Maps [@overture], conservando apenas as que não se sobrepõem a um contorno do OpenStreetMap. A figura 1 mostra a sua distribuição por região: o OpenStreetMap só é a fonte maior na região de Bolama-Bijagós, onde voluntários traçaram as ilhas em pormenor; nas restantes predominam as implantações obtidas por aprendizagem automática. O seu atributo de altura é um valor de preenchimento para a visualização, pelo que o modelo nunca o usa.

![Implantações de edifícios por região e por fonte ($F$, número de implantações). As implantações do Google Open Buildings e da Microsoft fornecem 76 % do total nacional; o OpenStreetMap fornece 46 % em Bissau e 67 % em Bolama.](figures/sources.svg){width=82%}

**Limites e ilhas.** Os 39 setores (38 setores e o Setor Autónomo de Bissau) vêm dos limites administrativos do OpenStreetMap, conferidos com o geoBoundaries e com a lista do PCGN [@pcgn2024], e foram fixados a 18 de outubro de 2026. Os 189 polígonos de ilhas e ilhéus vêm do mesmo extrato.

**Fronteira nacional.** A fronteira nacional é o limite administrativo da Guiné-Bissau de nível 2 do OpenStreetMap (relação 192776, `ISO3166-1=GW`), sob ODbL. É ela que decide que edifícios pertencem ao país: uma implantação, uma morança ou uma entrada só contam quando ficam dentro dessa fronteira ou a menos de 300 m dela, diga o que disser um contorno de setor ou outra fonte de contornos (geoBoundaries, GADM), porque contornos de fontes diferentes podem ultrapassar uma fronteira. Os 300 m admitem implantações desenhadas sobre a linha e a precisão da própria linha. Todos os códigos do registo têm a entrada dentro da fronteira ou a menos dessa distância.

**Lugares.** Os pontos de lugar vêm do OpenStreetMap (bairros, vilas, aldeias, lugarejos, moranças com nome) e depois do GeoNames. Uma localidade do GeoNames só é mantida quando não há nenhum lugar do OpenStreetMap a menos de 400 m nem nenhum com o mesmo nome a menos de 1,5 km. A tabela de lugares tem 4 221 lugares e 39 palavras de setor.

**Recintos e portões.** Muros, vedações, sebes, contornos de morança (`landuse=farmyard`, 782 no extrato) e portões vêm do OpenStreetMap.

**Estatísticas.** A população, os agregados, as línguas e a alfabetização vêm do recenseamento e das estatísticas internacionais citadas na secção 2. Todas as contagens deste artigo que dizem respeito a códigos são calculadas a partir do registo publicado, e os programas que calculam as figuras estão no repositório (`tools/paper_figures.py`).

# O modelo

## Princípios de desenho

O modelo segue nove princípios, por ordem de prioridade.

1. **Memorizável e sem esforço.** Um código é uma palavra de lugar que as pessoas já usam e um número curto; obtê-lo exige um toque.
2. **Único por si só.** O código dito identifica uma casa no país sem vila, setor, ilha nem posição.
3. **A morança e o seu portão.** A unidade é a morança ou o quintal; as suas estruturas são subunidades; a navegação termina no portão.
4. **Primeiro o oficial.** Onde exista uma morada do Estado, é mostrada primeiro, tal como o Estado a escreve.
5. **Sem rede.** Códigos de ponto, palavras de lugar e algarismos de controlo calculam-se sem ligação.
6. **Estável.** Um código nunca muda de lugar nem é reutilizado; reagrupamentos, mudanças de nome e novos limites nunca alteram um código emitido.
7. **Lugares, nunca pessoas.** Nenhum nome ou dado de um morador é guardado.
8. **Aberto e transmissível.** O motor, o registo e as regras são abertos e pensados para serem entregues ao Estado.
9. **Nacional.** O modelo e o seu motor são próprios da Guiné-Bissau.

## As formas de um código

Um código tem três formas equivalentes. A **forma memorizada** $P\;N$ é o nome de placa $P$ do lugar seguido do número $N \in \{1, \dots, 99\,999\}$; é o que as pessoas dizem, escrevem e digitam, e é também a **forma escrita** usada nas placas e nas encomendas. A **forma máquina** é

$$
\underbrace{SS}_{\text{setor}}\;\text{-}\;\underbrace{PPP}_{\text{lugar}}\;\text{-}\;\underbrace{NNNNN}_{\text{número}}\;\text{-}\;c,
\qquad c = \operatorname{Damm}\!\left(F \,\|\, NNNNN\right),
\tag{1}
$$
em que $SS$ é o número do setor com dois algarismos, $PPP$ o índice do lugar dentro dele com três, $NNNNN$ o número completado a cinco algarismos, $F$ o número nacional do nome do lugar com cinco algarismos (secção 4.7), $\|$ a concatenação e $\operatorname{Damm}$ a função de controlo da secção 4.12. Uma estrutura dentro da morança acrescenta um sufixo (`Bandim 537.2`, `10-022-00537.2-c`). Só a forma máquina leva o algarismo de controlo: as pessoas nunca o veem. Um **código de ponto** (secção 4.13) designa qualquer ponto sem morança.

| Forma | Exemplo | Usada por |
|:--|:--|:--|
| Memorizada e escrita | Bandim 537 | pessoas: dita, digitada, pintada no portão |
| Máquina | 10-022-00537-4 | sistemas, códigos QR, parceiros |
| Estrutura | Bandim 537.2 | um segundo edifício da morança |
| Ponto | 10-4327-9117 | qualquer ponto sem morança |

: As formas de um código.

## Setores

Cada um dos 39 setores tem um número de dois algarismos cujo primeiro algarismo é a região (1 Bissau, 2 Bafatá, 3 Bolama, 4 Biombo, 5 Cacheu, 6 Gabú, 7 Oio, 8 Quinara, 9 Tombali), uma chave de três letras e a sua própria grelha de pontos (secção 4.13). Bissau é o setor 10; os números 11 a 19 ficam reservados para o caso de a cidade vir a ser dividida em distritos. Um ponto $\mathbf{p}$ pertence ao setor cujo contorno o contém, por lançamento de raio, excluídos os buracos:

$$
s(\mathbf{p}) =
\begin{cases}
\sigma & \text{se } \mathbf{p} \in \Omega_\sigma \text{ e } \delta_B(\mathbf{p}) \le 300\ \text{m}, \\
\varnothing & \text{nos outros casos},
\end{cases}
\tag{2}
$$
em que $\Omega_\sigma$ é o contorno do setor $\sigma$ e $\delta_B(\mathbf{p})$ a distância de $\mathbf{p}$ à fronteira nacional $B$, nula no seu interior. Os pontos no mar ou no estrangeiro não têm setor. **A fronteira decide:** um ponto a mais de 300 m para fora da fronteira nacional não tem setor, mesmo que um contorno de setor o contenha, e assim nenhum edifício de um país vizinho recebe um código. O motor leva $B$ simplificada pelo método de Douglas–Peucker a 50 m, cuja maior distância à linha verdadeira é de 50,2 m, e aceita um ponto no máximo a 248 m para fora dela, de modo que nenhum ponto aceite fica a mais de 300 m para fora da fronteira verdadeira. O agrupamento aplica o mesmo teste a cada implantação e a cada morança antes de atribuir qualquer número, e o servidor do registo aplica-o a cada novo código e a cada entrada deslocada. A figura 2 mostra os contornos e a densidade de moranças.

![Moranças por célula de 5 km ($c$, escala logarítmica) e contornos dos 39 setores, em quilómetros numa projeção equirretangular local. As células de Bissau têm até 20 890 moranças; a maior parte do leste tem de algumas dezenas a algumas centenas por célula.](figures/map.svg){width=100%}

| Região | Setores | Moranças |
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

: Regiões, setores e moranças no registo.

## Moranças: agrupar as estruturas

Uma casa de família na Guiné-Bissau é, em geral, um conjunto de estruturas. Uma morança rural tem uma casa principal, cozinhas, armazéns e por vezes casas redondas à volta de um terreiro; um quintal de Bissau é muitas vezes murado. As implantações refletem-no: um quarto tem menos de 33 m² e metade mais de 116 m², e na região de Gabú a mediana é de 41 m², porque as moranças fulas e mandingas do leste são feitas de muitas casas pequenas. Numerar edifícios daria vários códigos a uma família; por isso agrupamos as implantações em moranças antes de atribuir qualquer número.

**Classe de povoamento.** Para cada implantação, a densidade $\rho$ de implantações no quadrado de 250 m centrado nela (cinco células de 50 m em cada direção) determina uma classe de povoamento:

$$
\rho = \frac{\#\{\text{implantações a } \pm 2 \text{ células de } 50\ \text{m}\}}{6{,}25\ \text{ha}},
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

**Distância entre estruturas.** Para as implantações $a$ e $b$, de centroides $\mathbf{c}_a, \mathbf{c}_b$ e áreas $A_a, A_b$, aproximamos a distância entre as suas paredes por

$$
g(a, b) = \lVert \mathbf{c}_a - \mathbf{c}_b \rVert - \tfrac{1}{2}\sqrt{A_a} - \tfrac{1}{2}\sqrt{A_b}.
\tag{4}
$$

As regras seguintes aplicam-se por ordem. As estruturas são primeiro ordenadas por setor, latitude, longitude, área e identificador, para que o resultado nunca dependa da ordem em que chegam os dados do mapa.

| Regra | Condição | Efeito |
|:----------|:---------------------------------------------------|:------------------------------|
| Recinto | centroide dentro de um muro, vedação, sebe, morança traçada ($\le 1$ ha), parcela residencial ($\le 2\,500$ m²) ou recinto institucional | o recinto é uma morança |
| Anexo | $A < 40$ m² e $g \le d_a$ até uma estrutura | junta-se à estrutura mais próxima |
| Casas | ambas com $A \ge 40$ m² e $g \le d_g$ | ligação simples numa só morança |
| Limite | um grupo com mais de 12 estruturas | religado com distâncias reduzidas a metade até cada grupo ter no máximo 12 |

: Regras de agrupamento, aplicadas por ordem.

| Classe | $d_a$ (anexo) | $d_g$ (casas) |
|:--|--:|--:|
| cidade | 6 m | 3 m |
| vila | 10 m | 6 m |
| tabanca | 15 m | 12 m |
| disperso | 20 m | 15 m |

: Distâncias de junção por classe de povoamento.

**Resultado.** As regras dão 241 673 moranças a partir de 419 593 implantações: 144 820 moranças de uma estrutura, 56 535 de duas, 21 794 de três e 18 524 de quatro ou mais (média 1,74). Do total de implantações, 65,5 % pertencem a uma morança de duas ou mais estruturas, de 58 % em Bissau a 71 % em Oio; 763 moranças vêm de recintos traçados. Com cerca de 301 000 agregados no recenseamento, há cerca de 1,25 agregados por morança, o que é coerente com moranças familiares que abrigam mais de um agregado.

**Validação.** Voltámos a aplicar as regras de proximidade escondendo os recintos traçados pelos voluntários e comparámos o resultado com esses recintos. Das 159 moranças rurais traçadas, 58 % são recuperadas inteiras e 46 % exatamente, e mais 24 % só falham uma estrutura. Em 53 quintais urbanos murados, só 13 % são recuperados inteiros: dentro de um muro de Bissau os edifícios estão afastados, enquanto os vizinhos do outro lado do muro estão próximos. A regra é deliberadamente prudente na cidade, porque os dois erros não são simétricos: juntar dois códigos mais tarde não custa nada (um torna-se um sinónimo), enquanto separar uma junção errada daria um código novo a uma família.

## Lugares e a regra do ponto ao lugar

A palavra de lugar é um bairro de Bissau (incluindo as antigas aldeias absorvidas pela cidade, que hoje são nomes de bairro: Plaque, Jal, Bono, Quetene, Cuntum), uma vila ou um dos seus bairros, uma aldeia, um lugarejo ou um grupo de moranças. Uma morança $c$ do setor $s$ na massa de terra $L$ recebe o lugar mais próximo do seu setor e da sua massa de terra a menos de 3 km, e caso contrário a palavra do próprio setor:

$$
p(c) =
\begin{cases}
\displaystyle\operatorname*{arg\,min}_{q \in \mathcal{P}(s, L)} d(c, q) & \text{se } \displaystyle\min_{q \in \mathcal{P}(s, L)} d(c, q) \le 3\,000\ \text{m},\\[1ex]
\text{a palavra do setor (índice 000)} & \text{caso contrário,}
\end{cases}
\tag{5}
$$
em que $\mathcal{P}(s, L)$ é o conjunto dos lugares do setor $s$ na massa de terra $L$, $d$ a distância no terreno em metros, e os empates vão para o índice mais baixo. A Ilha de Bissau conta com o continente, porque uma estrada as liga; todas as outras ilhas são massas de terra próprias, pelo que uma casa em Orango nunca é numerada num lugar de Bubaque.

Dos 4 221 lugares, 3 336 têm pelo menos uma morança. Trinta e sete setores usam a sua própria palavra para 5 430 moranças que estão a mais de 3 km de qualquer lugar com nome. Um bairro disputado ou renomeado nunca altera um código: o nome novo torna-se um sinónimo.

## Nomes de placa

A palavra de um código tem de ser curta o bastante para se dizer com um número. Chamamos **nome de placa** à forma curta admissível, e exigimos

$$
\operatorname{placa}(w) \iff \bigl|\operatorname{NFC}(w)\bigr| \le 12 \;\wedge\; \bigl|\operatorname{palavras}(w) \setminus \mathcal{L}\bigr| \le 2 \;\wedge\; w \text{ não contém algarismos},
\tag{6}
$$
em que $|\operatorname{NFC}(w)|$ conta os carateres na forma normal C do Unicode (uma letra acentuada conta uma vez), $\operatorname{palavras}(w)$ são as partes separadas por espaços ou hífenes, e $\mathcal{L} = \{$de, da, do, das, dos, d, e, o, a, os, as, em, na, no, di, du$\}$ é o conjunto das palavras de ligação.

Um nome que não satisfaça a equação (6) passa por etapas fixas: uma forma curta documentada e já em uso; a limpeza (parênteses, «Bairro de», «Tabanca de», «Morança» e palavras genéricas: «Bairro Ajuda II Phase» passa a *Ajuda II*); a abreviatura de um prefixo de santo (*Sto António*); e, nos restantes casos, a escolha da sequência mais distintiva de uma ou duas palavras inteiras. Cada sequência candidata $r$ é pontuada pela frequência média das suas palavras entre todos os nomes de lugar do país,

$$
\operatorname{raridade}(r) = \frac{1}{|\operatorname{palavras}(r)|} \sum_{u \in \operatorname{palavras}(r)} f(u),
\tag{7}
$$
em que $f(u)$ é o número de nomes de lugar que contêm a palavra $u$. Escolhe-se a sequência de menor pontuação, com preferência pelo fim do nome, só se estiver à frente da seguinte por um fator de pelo menos 1,5. Assim, «Sinchã Malam Baio» passa a *Malam Baio* e «Missirá Ama Sidi» a *Ama Sidi*. As palavras de povoamento (*Sinchã*, *Sare*, *Madina*, *Gã*, *Ponta*, *Ilhéu*) são as primeiras a cair e nunca formam sozinhas um nome de placa. Os nomes dos povos que dão nome a uma tabanca (balanta, mancanha, papel, fula, beafada) nunca são retirados automaticamente, porque «Bambadinca Balanta» e «Bambadinca Mancanha» são duas aldeias.

Quando nenhuma forma curta é claramente a certa, o lugar é assinalado à Câmara Municipal, em Bissau, ou à administração do setor, com os régulos e a comunidade, com até três candidatos. Dos 3 336 lugares em uso, 2 807 mantêm o nome, 17 são limpos, 119 são encurtados, 37 são palavras de setor e 356 são assinalados, dos quais 28 ainda excedem o limite. Os 21 759 códigos dos lugares assinalados foram emitidos com o nome provisório. A escolha do conselho pode mudar a palavra uma vez; o nome oficial continua sempre a ser um sinónimo.

## A chave do nome

Dois nomes que soam ou se escrevem de forma parecida nunca podem depender só do ouvinte para serem distinguidos; por isso partilham uma **chave de nome** e, com ela, uma única faixa nacional de números. A chave de uma palavra $w$ é uma composição de passos de normalização,

$$
\kappa(w) = \Phi\bigl(\delta(\nu(\epsilon(\pi(\tau(\alpha(w)))))))\bigr) \,\|\, \#\,n(w),
\tag{8}
$$
em que $\alpha$ passa a minúsculas, lê *ç* como *s* e retira os acentos; $\tau$ substitui por um espaço todo o caráter que não seja a–z ou 0–9; $\pi$ retira um *Bairro*, *Tabanca*, *Aldeia*, *Povoação* ou *Morança* inicial (com um *de*, *da* ou *do* a seguir); $\epsilon$ desenvolve as abreviaturas *Sto*, *Sta*, um *S.* inicial e *N. Sra*; $\nu$ põe de parte um numeral final de I a X ou de 1 a 10, como o numeral romano $n(w)$; $\delta$ retira as palavras pequenas *de, da, do, dos, das, e, o, a, os, as* quando resta mais alguma coisa; e $\Phi$ reduz a uma só letra as grafias de um mesmo som, da seguinte forma. Um *que* final passa a *k*; *tch*, *ch* e *sh* passam a *x*; *ck* e *qu* passam a *k*; *gu* passa a *g*; *ph* passa a *f*; *nh* passa a *n*; *lh* passa a *l*; *c* antes de *e* ou *i* passa a *s* e qualquer outro *c* a *k*; *z* passa a *s*, *y* a *i*, *w* a *u*; o *h* cai; as grafias vocálicas do kriol juntam-se (*e* com *i*, *o* com *u*); e as letras dobradas reduzem-se a uma. O sufixo $\#\,n(w)$ só existe quando foi posto de parte um numeral.

Assim, *Sintchã Dulo*, *Sinchã Duló* e *Sincha Dulu* partilham a chave `sinxadulu`; *Plack* e *Plaque* partilham `plak`; *Áfià* e *Hafia* partilham `afia`; já *Plaque II* (`plak#ii`) é um nome à parte. Como uma palavra escrita sem a cedilha (*Praca* por *Praça*) passaria de outro modo o *c* a *k*, todo o nome que contém *ç* também se resolve a partir da grafia sem cedilha (secção 6.2). A redução erra de propósito para o lado da junção: juntar dois nomes custa apenas uma faixa mais longa, enquanto manter separados dois nomes que soam igual daria a duas casas o mesmo código dito.

Aplicada aos 4 221 lugares e às 39 palavras de setor, a equação (8) dá 3 295 chaves de nome, das quais 2 704 têm moranças. Destas, 407 nomes são partilhados por dois ou mais lugares em uso, num total de 1 039 lugares e 92 745 moranças (38 % do total); 183 nomes repetem-se dentro de um mesmo setor. Missirá é o nome com mais lugares (14), seguido de Áfià (13), Madina (12) e Amedalai (11).

## Uma faixa nacional por nome

Como um nome se diz sem a sua vila, todos os lugares que partilham uma chave de nome tiram os números de uma única **faixa nacional** $\{1, \dots, 99\,999\}$, dividida num bloco por lugar. Cada número cai num só bloco; por isso, um nome e um número descodificam-se num só lugar.

**Dimensão do bloco.** Um lugar com $n$ moranças na primeira emissão recebe o menor bloco da série 1–2–5 que comporte quatro vezes as suas moranças:

$$
b(n) = \min\bigl\{x \in \{10, 20, 50, 100, 200, 500, 1\,000, \dots, 50\,000\} : x \ge 4n \bigr\}.
\tag{9}
$$

O fator quatro decorre da regra de numeração da secção 4.9: a primeira emissão usa um número em cada dois, pelo que metade do bloco fica ocupada pelas moranças iniciais e pelos números entre elas; a outra metade fica para o crescimento do lugar.

**Colocação dos blocos.** Os lugares de um mesmo nome são tomados do maior para o menor, ficando para o fim os que aguardam a escolha do nome de placa por um conselho, e cada bloco começa na marca máxima do nome arredondada para cima a um múltiplo de uma potência de dez adequada à sua dimensão:

$$
\begin{aligned}
\operatorname{passo}(b) &= 10^{\lfloor \log_{10} b \rfloor},
&
\text{início}_i &= \operatorname{passo}(b_i)\left\lceil \frac{H_{i-1}}{\operatorname{passo}(b_i)} \right\rceil,\\
\text{fim}_i &= \text{início}_i + b_i - 1,
&
H_i &= \text{fim}_i + 1,
\end{aligned}
\tag{10}
$$
com $H_0 = 0$. Começar em números redondos torna os blocos legíveis: o bairro de Bandim, em Bissau, tem 0–1 999 e a tabanca de Bandim, em Catió, 2 000–2 199.

**Exemplo resolvido.** Bandim, bairro de Bissau (setor 10, lugar 022), tinha $n = 452$ moranças na primeira emissão e é o maior lugar do seu nome; logo $4n = 1\,808$, $b = 2\,000$ e o seu bloco é 0–1 999. Catorze lugares partilham o nome Missirá; a figura 3 mostra como os seus blocos dividem a faixa. *Missira 101* fica em Bissau e *Missirá 5101* em Sonaco; nenhum dos dois precisa do setor.

![A faixa nacional do nome Missirá, dividida num bloco fixo por lugar (número $N$ no eixo horizontal). A parte escura de cada bloco contém os números da primeira emissão, de $\text{início}+1$ a $\text{início}+2n-1$; a parte clara é a reserva. Galomaro aparece duas vezes porque dois lugares desse setor partilham o nome.](figures/blocks.svg){width=96%}

| Lugar | Setor | Moranças | Bloco |
|:--|:--|--:|:--|
| Missira | Bissau | 771 | 0–4 999 |
| Missirá | Sonaco | 81 | 5 000–5 499 |
| Missirá | Gabú | 53 | 5 500–5 999 |
| Missirá | Bafatá | 49 | 6 000–6 199 |
| Missirá | Bissorã | 44 | 6 200–6 399 |
| Missirá | Bambadinca | 30 | 6 400–6 599 |
| … mais oito | | 113 | até 7 249 |

: Os blocos do nome Missirá.

**Horizonte de crescimento.** Na primeira emissão, um lugar usa os números ímpares até $2n - 1$ num bloco de pelo menos $4n$, pelo que pode acolher quatro vezes as suas moranças iniciais antes de precisar de outro bloco. A uma taxa de crescimento constante $r$, isso leva

$$
t = \frac{\ln 4}{\ln (1 + r)} \approx
\begin{cases}
63\ \text{anos} & r = 2{,}2\,\%\ \text{(média nacional)},\\
35\ \text{anos} & r = 4\,\%\ \text{(periferias de Bissau em rápido crescimento)}.
\end{cases}
\tag{11}
$$

**Tabela fixa.** A tabela de blocos foi fixada na primeira emissão, a 20 de outubro de 2026. Um bloco nunca é deslocado, renumerado ou reduzido. Um lugar novo com um nome já existente, ou um lugar cujo bloco se encha, recebe outro bloco acima da marca máxima do nome, pela equação (10).

A maior faixa partilhada é a de Áfià (13 lugares, 2 560 moranças), que termina em 15 719. Nenhum nome se aproxima de 99 999, pelo que não é necessário qualquer qualificativo.

## A numeração dentro de um lugar: a curva de Hilbert

Dentro do seu bloco, as moranças de um lugar são numeradas ao longo de uma curva de Hilbert [@hilbert1891], para que vizinhos no terreno recebam números vizinhos, como acontece com os números de porta ao longo de uma rua. Entre as curvas que preenchem o plano, a de Hilbert tem as melhores propriedades de agrupamento: uma região compacta do plano corresponde a poucos troços contíguos da curva [@moon2001].

**A grelha.** Cada setor tem um quadro de $10\,000 \times 10\,000$ células, com canto sudoeste $(\varphi_S, \lambda_W)$, latitude de referência $\varphi_r$ e lado de célula $\Delta$ em metros (1,7 m em Bissau, até 9,4 m em Gabú). Um ponto $(\varphi, \lambda)$ está na célula

$$
x = \operatorname{clip}\!\left(\left\lfloor \frac{(\lambda - \lambda_W)\cos\varphi_r \cdot 111\,320}{\Delta} \right\rfloor\right),
\qquad
y = \operatorname{clip}\!\left(\left\lfloor \frac{(\varphi - \varphi_S) \cdot 110\,574}{\Delta} \right\rfloor\right),
\tag{12}
$$
em que $\operatorname{clip}$ limita o resultado a $0, \dots, 9\,999$ e as constantes são os metros por grau de longitude no equador e de latitude.

**A curva.** O índice de Hilbert $h(x, y)$ numa curva de ordem 14 ($2^{14} = 16\,384$ células de lado, que envolvem a grelha) calcula-se do bit mais significativo para o menos significativo. Com $h = 0$ e, para $\sigma = 2^{13}, 2^{12}, \dots, 1$,

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
em que $\oplus$ é o ou exclusivo bit a bit. A figura 4 mostra a curva de ordem 3 calculada pelo motor de referência.

![A curva de Hilbert de ordem 3 sobre uma grelha de $8 \times 8$, com o índice $h$ de cada célula $(i, j)$, tal como o calcula o motor de referência. O modelo usa a mesma construção na ordem 14.](figures/hilbert.svg){width=52%}

**Primeira emissão.** As $n$ moranças de um lugar com o bloco $[\text{início}, \text{fim}]$, ordenadas por $(h, \text{chave})$, em que a chave é o identificador estável da estrutura principal da morança, recebem

$$
N_k = \text{início} + 1 + 2k, \qquad k = 0, 1, \dots, n - 1.
\tag{14}
$$

Os números pares entre vizinhos ficam livres para as moranças construídas mais tarde entre eles.

**Exemplo resolvido: Bandim 537.** A morança mais próxima do mercado de Bandim tem o ponto de entrada em $\varphi = 11{,}8521485$, $\lambda = -15{,}5950371$. No quadro de Bissau ($\lambda_W = -15{,}662$, $\varphi_S = 11{,}795$, $\varphi_r = 11{,}87$, $\Delta = 1{,}7$ m), a equação (12) dá a célula $(4\,291;\ 3\,717)$ e a equação (13) o índice de Hilbert $33\,435\,700$. É a 269.ª das 452 moranças de Bandim ao longo da curva ($k = 268$), pelo que a equação (14) dá $N = 0 + 1 + 2 \cdot 268 = 537$. A figura 5 mostra o bairro inteiro.

![As 452 moranças de Bandim, em Bissau, coloridas pelo seu número $N$ e ligadas por ordem numérica, em metros a partir do canto sudoeste do bairro. Os números avançam pelo bairro quarteirão a quarteirão; Bandim 537 está assinalada.](figures/bandim.svg){width=76%}

## Uma casa nova

Uma morança nova entre os seus vizinhos de Hilbert $a$ (o número emitido imediatamente antes dela ao longo da curva) e $b$ (imediatamente depois), com índices $h_a < h < h_b$, recebe o número livre mais próximo da sua posição proporcional $N^{*}$:

$$
\begin{aligned}
N^{*} &= a + \max\Bigl(1,\ \min\Bigl(b - a - 1,\ \operatorname{round}\Bigl(\frac{h - h_a}{h_b - h_a}\,(b - a)\Bigr)\Bigr)\Bigr),\\
N_{\text{nova}} &= \operatorname*{arg\,min}_{a < m < b,\ m\ \text{livre}} \lvert m - N^{*} \rvert.
\end{aligned}
\tag{15}
$$

Se não houver número livre entre $a$ e $b$, ou se a morança vier depois da última, recebe o maior número do lugar mais um, se ainda estiver no bloco; caso contrário, o bloco seguinte do lugar e, se todos estiverem cheios, um bloco de continuação dimensionado pela equação (9) e colocado pela equação (10). Um número retirado nunca é reutilizado.

## Descodificar sem contexto

Para descodificar uma forma memorizada, os algarismos finais são o número $N$ e as palavras antes deles o nome $P$. A chave do nome dá a faixa nacional, e o número dá o único bloco que o contém:

$$
\operatorname{descodificar}(P, N) = \bigl\{\, q : \kappa(P) \in K(q) \;\wedge\; N \in B(q) \,\bigr\},
\tag{16}
$$
em que $K(q)$ é o conjunto das chaves do lugar $q$ (o seu nome de placa e os seus sinónimos) e $B(q)$ os seus blocos. Como os blocos de um mesmo nome nunca se sobrepõem, o conjunto tem no máximo um elemento. Um número fora de todos os blocos é recusado, nunca adivinhado num lugar próximo. Um nome de setor escrito depois de uma vírgula é mostrado, mas nunca é necessário.

## O algarismo de controlo

A forma máquina leva um algarismo decimal de controlo calculado pelo algoritmo de Damm [@damm2004; @damm2007] sobre a carga $F \,\|\, N$ (dez algarismos, seguidos do número da estrutura, se existir):

$$
c_0 = 0, \qquad c_k = T\bigl[c_{k-1}\bigr]\bigl[d_k\bigr], \quad k = 1, \dots, m, \qquad \operatorname{Damm}(d_1 \cdots d_m) = c_m,
\tag{17}
$$
em que $d_k$ são os algarismos da carga e $T$ é a tabela de operação de um quasigrupo totalmente antissimétrico de ordem 10:

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

Cada linha e cada coluna de $T$ é uma permutação, pelo que qualquer algarismo errado altera o resultado. A tabela é totalmente antissimétrica, isto é, $T[T[c][x]][y] = T[T[c][y]][x]$ implica $x = y$, pelo que qualquer troca de dois algarismos vizinhos diferentes também é detetada. São os dois erros mais frequentes na transcrição de códigos decimais [@verhoeff1969].

**Exemplo resolvido.** O nome Bandim tem o número nacional $F = 228$, pelo que a carga de Bandim 537 é `0022800537`. Os valores sucessivos de $c_k$ são 0, 0, 1, 9, 9, 2, 4, 4, 3, 4, e o algarismo de controlo é 4: a forma máquina é `10-022-00537-4`. Um sistema parceiro que receba `10-022-00573-4`, com dois algarismos trocados, verifica que o algarismo de controlo de `0022800573` não é 4 e recusa o código.

**Ligação ao lugar.** O lugar não está na carga; decorre do nome e do número através da tabela fixa de blocos. Um engano que leve o número para o bloco de outro lugar do mesmo nome altera um algarismo da carga e é, por isso, sempre detetado: `10-050-05101-8` (o código de Missira 101, em Bissau, com um algarismo alterado) é recusado. Um engano nos algarismos do setor ou do lugar é recusado sempre que cai noutro lugar do mesmo nome ou em lugar nenhum; só é aceite quando cai num lugar de nome diferente, cuja palavra todos os ecrãs mostram então (secção 6.3).

## Códigos de ponto

Todo o ponto dentro de um setor tem um código de ponto, calculado sem rede a partir das suas coordenadas na grelha do setor da equação (12). Sejam $X = X_1X_2X_3X_4$ e $Y = Y_1Y_2Y_3Y_4$ as formas decimais de quatro algarismos das coordenadas de célula $x$ e $y$. Os seus algarismos são intercalados,

$$
D = X_1 Y_1 X_2 Y_2 X_3 Y_3 X_4 Y_4,
\qquad
\text{código} = SS\text{-}D_1D_2D_3D_4\text{-}D_5D_6D_7D_8,
\tag{18}
$$
de modo que os dois primeiros algarismos designam um quadrado de 1 000 células de lado e cada par seguinte o refina dez vezes. Um nono algarismo opcional escolhe um nono da célula, disposto como no teclado de um telefone, com 1 2 3 na fila norte:

$$
k = 3\bigl(2 - \lfloor 3 f_y \rfloor\bigr) + \lfloor 3 f_x \rfloor + 1,
\tag{19}
$$
em que $f_x, f_y \in [0, 1)$ são as partes fracionárias da posição do ponto dentro da célula. Um código de ponto descodifica-se no centro da sua célula, pelo que o erro de descodificação é limitado por metade da diagonal da célula:

$$
\varepsilon \le \frac{\Delta\sqrt{2}}{2} \quad (1{,}2\ \text{m em Bissau}),
\qquad
\varepsilon \le \frac{\Delta\sqrt{2}}{6} \ \text{com o nono algarismo}.
\tag{20}
$$

**Exemplo resolvido.** Bandim 537 está em $x = 4\,291{,}1$, $y = 3\,717{,}1$ na grelha de Bissau; logo $X = 4291$, $Y = 3717$, $D = 43279117$ e o código de ponto é `10-4327-9117`; com $f_x = f_y = 0{,}1$, a equação (19) dá $k = 7$ e o código refinado `10-4327-9117.7`. A figura 6 mostra o primeiro nível da grelha sobre Bissau. Os códigos de ponto destinam-se a lugares sem morança (uma banca de mercado, um ponto de encontro num *lumo* semanal, um porto de pesca) e partilham-se como ligações, não se memorizam.

![A grelha de pontos do setor 10 (Bissau), em unidades de 1 000 células ($x/1000$, $y/1000$; uma unidade são 1,7 km). Cada quadrado tem o seu primeiro par de algarismos $X_1Y_1$; os pontos representam uma morança em cada 25. Bandim 537 fica no quadrado 43 e o seu código de ponto é 10-4327-9117.](figures/spot.svg){width=58%}

## Ilhas e a ficha do edifício

Uma morança numa ilha só recebe palavras de lugar da mesma ilha (equação (5)), e a sua ficha mostra a ilha como etiqueta; o código é único sem ela.

Cada estrutura tem uma classe de uso, com a sua confiança e a sua fonte, a área de implantação, o número de pisos quando conhecido e um estado; cada morança agrega-os. As classes são próprias do país (casa de morança, anexo, casa redonda, loja, mercado, escola, posto de saúde, mesquita, igreja, quartel e outras) e são inferidas por uma ordem fixa: etiquetas do OpenStreetMap (confiança de 0,85 a 0,9), lugares com nome dentro da implantação (0,65), o tipo de recinto (0,55), a forma (casas redondas: circularidade de pelo menos 0,9 e área até 80 m²) e o valor por omissão do povoamento. Das 419 593 estruturas, 375 096 são casas de morança e 37 222 anexos; 1 469 são casas redondas, 1 012 grandes edifícios de uso desconhecido, 375 industriais, 331 militares, 308 escritórios e 236 escolas. Os pisos só são conhecidos em 82 estruturas. Uma casa nunca tem nome.

## Exemplos resolvidos

O quadro apresenta códigos reais do registo: a morança mais próxima de vários lugares conhecidos.

| Perto de | Memorizada e escrita | Máquina | Setor |
|:--|:--|:--|:--|
| Mercado de Bandim, Bissau | Bandim 537 | 10-022-00537-4 | Bissau |
| Bissau Velho | Bissau Velho 345 | 10-033-00345-1 | Bissau |
| Vila de Gabú | Gabu 1203 | 62-042-01203-8 | Gabú |
| Vila de Canchungo | Canchungo 1381 | 55-091-01381-7 | Canchungo |
| Vila de Bubaque | Bubaque 501 | 32-071-00501-0 | Bubaque |
| Missirá, Bissau | Missira 101 | 10-050-00101-8 | Bissau |
| Missirá, Sonaco | Missirá 5101 | 65-073-05101-5 | Sonaco |

: Códigos reais do registo.

Duas situações ilustram o uso. Um condutor de mototáxi pergunta para onde ir; o passageiro responde «Bandim, quinhentos e trinta e sete»; o condutor escreve `bandim 537` e a aplicação mostra a morança, o seu setor e o seu portão. Alguém em Gabú escreve `missirá 5101`; o número está no bloco 5 000–5 499, que pertence a Missirá, em Sonaco, pelo que a aplicação vai diretamente para lá, enquanto `missira 101` está em 0–4 999, em Bissau. Não há nada a escolher numa lista nem nada a adivinhar.

# Implementação

**Motor de referência.** `engine/reference/gw_codes.py` implementa todas as funções da secção 4 (setores, lugares, chaves de nome, nomes de placa, atribuição de blocos, numeração de Hilbert, inserção, algarismo de controlo e códigos de ponto) na biblioteca padrão de Python, com os respetivos testes unitários. `engine/SPEC.md` é a especificação normativa, e `engine/data/register.json` contém o que um descodificador precisa sem rede: os setores, cada lugar com o seu nome de placa, sinónimos, chave de nome e blocos fixos, e os contornos dos setores e das ilhas; `engine/data/border.geojson` contém a fronteira nacional da secção 4.3.

**Vetores de conformidade.** `engine/reference/vectors.json` contém 425 chaves de nome, 300 formas de código, 660 resoluções de formas memorizadas, 256 códigos de ponto e 6 casos de numeração. Qualquer implementação tem de os reproduzir exatamente. O emissor N-Ways numerou a primeira emissão com a sua própria implementação e recusou a execução se um só dos 241 673 números diferisse do motor de referência.

**Registo.** `registry/` publica todos os códigos emitidos: um ficheiro CSV comprimido em gzip por setor, com uma linha por morança (formas máquina, memorizada e escrita; área; nome oficial; número; algarismo de controlo; estado; data de emissão; ponto e tipo de entrada; Plus Code; classe de uso; estruturas; área de pavimento; classe de povoamento; código postal), a tabela fixa de áreas `areas.csv` e `MANIFEST.json`, com as contagens e o resumo SHA-256 de cada ficheiro. Os 241 673 códigos são publicados; nenhum é retido.

**Servidor e API.** `server/` é um servidor do registo na biblioteca padrão de Python que qualquer instituição pode instalar com um só comando (`docker compose up`). Importa o registo para SQLite depois de verificar todos os resumos e contagens, serve uma API JSON em `/v1` (estado, informação, ficha completa de um código, pesquisa por qualquer forma, código num ponto, códigos perto de um ponto, verificação, codificação e descodificação de pontos, setores, lugares e listagens paginadas) e volta a exportar o registo byte a byte. Uma instalação funciona só em leitura, a menos que o Estado ou a N-WAYS LIMITED a designe como emissora. Só pode haver um emissor por país, porque dois emissores a trabalhar sobre a mesma tabela de blocos atribuiriam duas vezes o mesmo número. O ponto de emissão aplica exatamente as regras das secções 4.5, 4.9 e 4.10; um teste de paridade com a implementação do próprio emissor concordou em todos os números, formas, lugares e blocos. A API está descrita em `server/openapi.yaml` e, com pedidos e respostas reais, em `docs/api.md`.

# Avaliação

Todas as medições desta secção são calculadas sobre o registo publicado completo com o motor de referência; os programas estão no repositório.

## Unicidade e cobertura

Cada morança dos 39 setores do país tem exatamente um código: 241 673 códigos, 241 673 formas máquina distintas e nenhum par de códigos com a mesma chave de nome e o mesmo número. Na tabela de áreas, os blocos de cada nome são disjuntos e terminam em 99 999 ou antes. Todas as entradas ficam dentro da fronteira nacional ou a menos de 248 m da sua linha simplificada, e nenhuma fica a mais de 300 m para fora da fronteira não simplificada (secção 4.3). Todos os códigos são provisórios até serem confirmados pelos moradores (secção 12).

## Exatidão da descodificação

Descodificámos todos os códigos do registo de três maneiras. As 241 673 formas máquina são lidas como o seu próprio lugar e número. As 241 673 formas memorizadas, resolvidas a nível nacional pela equação (16), sem qualquer contexto, devolvem a sua própria forma máquina. Quando as formas memorizadas são escritas em minúsculas e sem acentos, como muitos telemóveis as produzem, as 241 673 resolvem-se depois da regra da cedilha da secção 4.7. Antes dessa regra, 681 códigos (0,28 %) de sete lugares cujo nome contém *ç* (Praça, Sinchã Içaga, Serração e outros quatro) falhavam neste teste. A regra faz corresponder a grafia sem cedilha à chave existente, pelo que nenhuma chave, faixa ou bloco mudou.

## Deteção de erros

Sorteámos 5 000 códigos e aplicámos às suas formas máquina todas as substituições de um algarismo e todas as trocas de algarismos vizinhos, e depois lemos os resultados.

| Parte da forma máquina | Substituições | Recusadas | Aceites como outro nome |
|:--|--:|--:|--:|
| Número (5 algarismos) | 225 000 | 100 % | 0 |
| Algarismo de controlo | 45 000 | 100 % | 0 |
| Índice do lugar (3 algarismos) | 135 000 | 97,5 % | 2,5 % |
| Setor (2 algarismos) | 90 000 | 98,7 % | 1,3 % |
| **Trocas de vizinhos** | | | |
| Número | 13 041 | 100 % | 0 |
| Índice do lugar | 8 773 | 98,2 % | 1,8 % |
| Setor | 4 669 | 98,4 % | 1,6 % |

: Deteção de erros de transcrição em 5 000 formas máquina sorteadas.

Todos os erros no número e no algarismo de controlo são recusados, como a construção de Damm garante. Os erros nos algarismos do setor ou do lugar são recusados, salvo quando caem por acaso num número válido de um lugar de outro nome, que o ecrã então nomeia, de modo que o erro fica visível.

As pessoas usam a forma memorizada sem o algarismo de controlo, e para esta forma a deteção não pode ser garantida. Sobre os mesmos 5 000 códigos, um algarismo errado no número dito deu, entre os 121 981 resultados que eram números válidos, outra morança emitida do mesmo lugar em 59,4 % dos casos, uma morança de outro lugar do mesmo nome em 0,6 %, um número não emitido (recusado pelo registo) em 34,5 % e um número fora de todos os blocos em 5,5 %. O engano dentro do mesmo lugar é o caso comum, e a ordem de Hilbert mantém-no perto: um último algarismo errado cai a uma distância mediana de 59 m da morança pretendida, contra 523 m para duas moranças do mesmo lugar escolhidas ao acaso. É por isso que a aplicação mostra o lugar e o setor antes de iniciar a navegação, e que os sistemas trocam entre si a forma máquina.

## Comprimento dos códigos

A figura 7 mostra a distribuição das moranças por lugar, e a figura 8 o comprimento dos números emitidos.

![Número de lugares $A(n)$ segundo o seu número de moranças $n$ (3 336 lugares em uso). O lugar mediano tem 31 moranças; 79 lugares têm 500 ou mais.](figures/sizes.svg){width=80%}

![Moranças $C(\ell)$ segundo o número de algarismos $\ell$ do seu número, com faixas nacionais por nome ($R_{\text{nat}}$, tal como emitido) e na alternativa em que cada lugar tem uma faixa própria a começar em 1 ($R_{\text{own}}$).](figures/digits.svg){width=78%}

| Algarismos | Moranças | Proporção |
|:--|--:|--:|
| 1 | 12 866 | 5,3 % |
| 2 | 71 904 | 29,8 % |
| 3 | 99 673 | 41,2 % |
| 4 | 54 233 | 22,4 % |
| 5 | 2 997 | 1,2 % |

: Comprimento dos números emitidos.

O número médio tem 2,85 algarismos, e 98,8 % das casas têm quatro algarismos ou menos. As casas rurais têm sobretudo dois ou três algarismos, as das vilas três ou quatro. Em Bissau, 49 lugares têm uma mediana de 710 moranças cada; o maior, Bono, tem 3 274 e o seu número mais alto na primeira emissão é 6 547. No resto do país, o lugar mediano tem 30 moranças e o maior, Buba, 1 912. No registo, o nome de placa de um código tem em média 7,3 carateres; o código memorizado, nome e número, tem em média 11,1. Vinte e oito lugares em uso (todos assinalados a um conselho) ainda excedem o limite de placa da equação (6).

## Reserva e crescimento

O preenchimento de cada bloco na primeira emissão, moranças a dividir pela dimensão do bloco, é no máximo 0,25 pela equação (9) e tem mediana 0,17. Nenhum bloco precisou de continuação na primeira emissão.

## Códigos de ponto

Para cada um dos 241 673 pontos de entrada, codificámos o código de ponto e voltámos a descodificá-lo. A distância entre o ponto e o centro descodificado teve mediana de 1,65 m, percentil 99 de 4,97 m e máximo de 6,61 m (em Gabú, onde as células têm 9,4 m). Nenhum ponto excedeu o limite da equação (20).

# Desenhos estudados e rejeitados

O desenho final é o último de vários. Cada mudança descrita abaixo resultou de uma medição.

| Opção | Exemplo | Motivo da rejeição |
|:------------------------------|:--------------------|:----------------------------------------|
| Código de grelha alfanumérico | 7C36VC23+VX4 | letras ditas pelo nome português, que a maioria dos falantes de kriol não usa |
| Só algarismos nacionais | 00228 00537 | dez algarismos sem nada a que a memória se agarre |
| Setor e número | Gabú 14738 | cinco algarismos nos setores grandes; nomes de setor pouco usados |
| Lugar e número, qualificado pelo setor | Bandim 275, Catió | não é único por si só; falha quando o código viaja |
| Nomes oficiais completos | Sinchã Samba Camarà 12 | demasiado longo para dizer com um número |
| **Nome de placa e número numa faixa nacional por nome** | **Bandim 537** | **adotado** |

: Formas de código estudadas.

**Qualificar os nomes repetidos pelo setor.** Um desenho inicial mostrava o setor ao lado de uma palavra repetida e punha primeiro o lugar mais próximo. Um código que depende do contexto falha precisamente quando viaja: lido ao telefone, escrito numa encomenda ou digitado longe do lugar. As faixas nacionais eliminam essa dependência.

**Uma faixa por lugar.** Dar a cada lugar uma faixa própria encurtaria os números: o comprimento médio desceria de 2,85 para 2,69 algarismos e nenhum número precisaria de cinco (figura 8), mas 92 745 casas em 1 039 lugares partilhariam o seu código dito com outra casa. Considerámos 0,16 algarismos, em média, um preço pequeno por códigos únicos.

**Os nomes oficiais como palavras de lugar.** Com os nomes oficiais, 335 nomes seriam partilhados por 856 lugares; com os nomes de placa, 407 por 1 039, porque os nomes curtos coincidem mais vezes. Os lugares de cinco algarismos passaram de 21 para 25, sendo os quatro novos assinalados a um conselho. O ganho em brevidade da palavra dita compensa os números mais longos em alguns lugares.

**Poucos lugares em Bissau.** Só com os 28 pontos de bairro que o OpenStreetMap tinha para Bissau, os maiores lugares da cidade teriam chegado a 5 833 moranças e a números de cinco algarismos (até 11 665). Juntar as antigas aldeias absorvidas pela cidade trouxe todos os números de Bissau dos lugares confirmados de volta a quatro algarismos ou menos.

**Carateres de controlo.** Um caráter de controlo que detete todo o erro simples e toda a troca de vizinhos exige onze símbolos com um módulo primo ou um quasigrupo como o de Damm [@verhoeff1969; @damm2007]. Os nomes das letras em português rimam em duas grandes famílias (*bê, cê, dê, gê, pê, quê, tê, vê, zê*; *efe, ele, eme, ene, erre, esse*), pelo que uma letra seria ela própria uma fonte de erro. A forma máquina leva portanto um algarismo decimal; nem as placas nem as pessoas o veem.

**Excluir as zonas oficiais.** Um desenho que não emitisse código onde pudessem existir números de porta oficiais teria deixado o centro de Bissau sem morada utilizável enquanto a sua numeração continua incerta. Hoje todas as casas têm código, e a morada oficial, onde exista, é mostrada primeiro.

**Adiar os bairros densos.** Um desenho que esperava pelo traçado dos muros em imagens de satélite antes de numerar os bairros mais densos de Bissau foi substituído pela emissão de todas as moranças de uma só vez, com a regra urbana prudente da secção 4.4: quando os moradores indicam que duas moranças são uma só casa, um código torna-se sinónimo e nada é renumerado.

**Agrupamento dependente da ordem.** Duas execuções sobre os mesmos dados, com as linhas por outra ordem, deram 241 695 e 241 713 moranças. Ordenar as estruturas antes do agrupamento, e desempatar ao longo da curva de Hilbert pelo identificador estável da morança, tornou o resultado determinístico, de modo que todas as implementações produzem os mesmos números.

# Benefícios para os cidadãos

Para uma família em Bandim, numa morança de Nhacra ou em Orango, um código muda quatro coisas do dia a dia.

**Ser encontrado.** Hoje, uma visita, um mototáxi ou um estafeta é guiado ao telefone, de ponto de referência em ponto de referência. Com um código, a pessoa diz uma frase curta e a aplicação leva ao portão.

**Provar onde se vive.** Bancos, agentes de dinheiro móvel, escolas e empregadores pedem uma morada que possa ser verificada. Antes deste registo, duas moranças do país tinham número de porta nos dados abertos; hoje todas têm um código que se pode dizer, escrever e conferir num registo aberto.

**Receber bens e serviços.** Familiares na diáspora, lojas e empresas de água e eletricidade podem enviar para um código em vez de uma descrição, e um agregado pode pedir uma ligação ou uma reparação no portão certo.

**Simplicidade.** Nada é pedido ao agregado. Todas as moranças que já estavam no mapa receberam o seu código a 20 de outubro de 2026; a aplicação mostra-o com um toque, em português, inglês ou francês. É gratuito, não exige documentos, não guarda dados pessoais e não é um título de terra.

**Alcance estimado.** O número de pessoas que vivem em moranças com código é

$$
P = N_c \cdot \bar{m}, \qquad \bar{m} = \frac{P_{\text{rec}}}{N_c} = \frac{2\,213\,173}{241\,673} \approx 9{,}2,
\tag{21}
$$
em que $N_c$ é o número de moranças com código e $\bar{m}$ o número médio de moradores por morança. Por construção, a estimativa é igual à população recenseada, cerca de 2,2 milhões de pessoas. O pressuposto que importa é que as implantações cubram todas as moranças habitadas. Se faltarem 5 a 15 % das moranças nos dados de implantação, o que é plausível para a construção recente nas periferias das vilas, os códigos chegam inicialmente a 1,9–2,1 milhões de pessoas, e as restantes obtêm um código no momento através de «Adicionar a minha casa» (secção 4.10). Quem mais beneficia é quem menos tem hoje: as famílias dos bairros densos das periferias de Bissau, as tabancas longe de qualquer referência, as ilhas, e mais de um adulto em cada três que não lê bem, para quem um lugar conhecido e um número são mais fáceis do que letras.

# Logística e comércio

A entrega na Guiné-Bissau depende do telefone e, para as ilhas, dos barcos. Fontes do setor estimam o custo de uma tentativa de entrega de última milha em África em cerca de 2,70 dólares e referem taxas de êxito à primeira tentativa de apenas 60 % na maioria das transportadoras [@nextbillion2023]; um fornecedor de software de roteamento admite, num exemplo de custos para o Médio Oriente e África, uma taxa de falha de 5 % para um grande operador [@locus2026]. São números do setor, não medições publicadas em revistas com arbitragem científica. Não conhecemos nenhuma medição para a Guiné-Bissau.

O código dá a uma empresa de logística uma chave estável para cada cliente, que pode ser guardada, desduplicada e ligada às entregas anteriores; o encaminhamento até ao portão antes de o estafeta sair; entradas verificadas, porque a forma máquina recusa qualquer algarismo errado no momento da encomenda e não na estrada; e acesso aberto, porque o registo, o motor e as regras podem ser usados em qualquer sistema, sem rede e sem pagamento. O mercado de Bandim, os *lumos* regionais e os comerciantes que compram castanha de caju, principal exportação do país, podem enviar bens e pagamentos para uma morança em vez de para a vila mais próxima. Os barcos para Bubaque, Bolama e as outras ilhas podem levar um código em cada encomenda.

**Poupança estimada.** Seja $f_0$ a proporção de primeiras tentativas que falham com moradas em texto livre, $f_1$ a proporção com um código e $c$ o custo de uma tentativa. A poupança por mil entregas é

$$
S = 1\,000 \,(f_0 - f_1)\, c.
\tag{22}
$$

| Cenário | $f_0$ | $f_1$ | $c$ (US\$) | $S$ por 1 000 entregas (US\$) |
|:---------|-----:|-----:|------:|------------:|
| Baixo | 0,15 | 0,10 | 2,70 | 135 |
| Central | 0,25 | 0,07 | 2,70 | 486 |
| Alto | 0,40 | 0,05 | 2,70 | 945 |

: Poupança estimada nas entregas, com os pressupostos.

Os intervalos são pressupostos informados pelas fontes acima, não medições na Guiné-Bissau. O programa de medição da secção 13 foi concebido para os substituir.

# Serviços de emergência

Uma ambulância, uma equipa de bombeiros ou uma patrulha da polícia enfrenta o problema do estafeta com mais em jogo. Um inquérito à escala do continente sobre os serviços de emergência médica identificou sistemas em apenas 16 dos 54 países de África, servindo menos de 9 % da sua população [@mouldmillman2017]. Onde os sistemas existem, localizar o doente é uma causa reconhecida de atraso: um estudo qualitativo em Kigali verificou que as equipas e os operadores dependiam do conhecimento local de quem ligava e precisavam de várias chamadas para estabelecer o local [@hunt2023]. Não conhecemos nenhuma medição publicada para a Guiné-Bissau.

Um código ajuda um operador em quatro passos. Quem liga diz uma frase («Missirá, cinco mil cento e um»); o registo devolve uma morança, em Sonaco, e não nenhum dos outros treze lugares chamados Missirá. O operador repete o lugar e o setor. A equipa é enviada para o portão, e um código de ponto assinala qualquer ponto sem morança, como um acidente na estrada. Tudo isto funciona sem rede, porque o motor e os ficheiros do registo não precisam de ligação.

**Efeito estimado.** Larsen e colegas modelaram a sobrevivência após paragem cardíaca fora do hospital como decrescendo 2,3 pontos percentuais por cada minuto até à reanimação cardiopulmonar, 1,1 por cada minuto até à desfibrilhação e 2,1 por cada minuto até aos cuidados avançados [@larsen1993]. Onde uma só equipa presta os três, um atraso $\Delta t$ a encontrar o doente reduz a sobrevivência em

$$
\Delta S = (2{,}3 + 1{,}1 + 2{,}1)\,\Delta t = 5{,}5\,\Delta t \ \text{pontos percentuais}.
\tag{23}
$$

| Minutos poupados a localizar o doente, $\Delta t$ | 1 | 2 | 5 |
|:--|--:|--:|--:|
| Sobrevivência ganha, $\Delta S$ (pontos) | 5,5 | 11 | 27,5 |

: Sensibilidade da equação (23) ao tempo poupado.

O modelo foi ajustado no condado de King, em Washington, onde as taxas de sobrevivência e os tempos de resposta são muito diferentes dos da Guiné-Bissau, e só é linear no intervalo dos seus dados; os números indicam portanto uma ordem de grandeza, não uma previsão. A direção não deixa dúvidas: onde encontrar o portão leva minutos, eliminar a procura conta tanto como um veículo mais rápido.

# Coordenação e planeamento do Estado

Um código é uma chave comum. Quando os ministérios, a Câmara Municipal, as empresas de serviços e o INE se referem a uma morança pelo mesmo código, os seus registos podem ser cruzados sem comparar nomes e descrições. O estudo do Banco Mundial aponta isto como um benefício principal do endereçamento para o poder local: um diretório de moradas lista os locais de forma mais completa do que o rol fiscal e mostra quem falta nele [@farvacque2005].

**O recenseamento.** O recenseamento de 2026 do INE georreferenciou os alojamentos. Uma tabela de códigos por área de recenseamento permitiria que cada conjunto servisse o outro: o recenseamento dá ao registo as contagens de agregados, e o registo dá às equipas de inquérito uma base de 241 673 moranças com códigos estáveis, de onde tirar amostras e aonde voltar, sem guardar nenhum nome.

**Planear com contagens.** O registo conta as moranças por região, setor, lugar, classe de povoamento e classe de edifício, e cada contagem pode ser recalculada a partir dos ficheiros abertos. A lei de ordenamento de 2026 pede instrumentos cartográficos [@geocracia2026]; o registo é um deles, aberto e disponível desde já.

**Acesso aos serviços.** O quadro dá as distâncias em linha reta das moranças ao equipamento cartografado mais próximo de cada tipo, numa amostra aleatória de 20 000 moranças e nos dados do mapa de 20 de outubro de 2026.

| Equipamento | A menos de 2 km | A menos de 5 km | Distância mediana |
|:--|--:|--:|--:|
| Unidade de saúde | 20,8 % | 29,4 % | 16,1 km |
| Escola | 27,7 % | 36,7 % | 12,7 km |
| Polícia | 11,4 % | 22,8 % | 28,0 km |
| Farmácia | 14,6 % | 28,5 % | 20,4 km |

: Distância das moranças ao equipamento cartografado mais próximo.

Estes números descrevem mais o mapa do que o país: poucos postos de saúde, escolas e postos de polícia fora de Bissau estão cartografados, pelo que as distâncias estão sobrestimadas. Mostram onde a cartografia é mais necessária, e um ministério pode substituir a lista de equipamentos pela sua e recalculá-las em minutos.

**Custo evitado.** O endereçamento clássico das mesmas moranças custaria cerca de

$$
C = N_c \cdot c_d = 241\,673 \times 5{,}7\ \text{US}\$ \approx 1{,}4\ \text{milhões de US}\$,
\tag{24}
$$
em que $c_d$ é o custo médio por porta nas cidades africanas segundo o Banco Mundial, a preços de 2005 [@farvacque2005], antes de dar nome a ruas que não existem e de chegar às ilhas. Com $c_d$ entre metade e o dobro dessa média, $C$ fica entre 0,7 e 2,8 milhões de dólares a preços de 2005. Os códigos foram emitidos para todas as moranças de uma só vez, sem custo para o Estado.

**Crescimento.** As moranças novas recebem código à medida que aparecem (secção 4.10), pelo que o registo mostra mês a mês onde o país cresce e onde serão precisos a seguir estradas, água, escolas e postos de saúde.

# Privacidade, segurança e governação

**Privacidade.** Os códigos descrevem lugares, nunca pessoas. As moranças residenciais não têm nomes nem dados dos ocupantes, e o número de agregados nunca é inferido. Os edifícios comerciais e públicos têm os seus nomes públicos. As fotografias tiradas em «Adicionar a minha casa» guardam-se apenas para verificação. Um agregado pode pedir que a sua porta seja ocultada: a morança mantém o código e o portão deixa de ser mostrado. Os parceiros só veem um código com o consentimento do cliente. Na ausência de uma lei nacional de proteção de dados, o modelo aplica os princípios do Ato Adicional da CEDEAO [@ecowas2010], e as regras nacionais mais exigentes prevalecerão quando forem adotadas.

**Segurança.** Os quartéis e as esquadras mantêm o seu código e o seu contorno, ambos já visíveis nos mapas públicos, mas não têm ficha de estrutura. Uma casa sagrada da religião tradicional (*baloba*) é guardada, mas não é publicada sem o acordo da comunidade. Um código não prova nada sobre quem é dono da terra ou a pode usar; a aplicação di-lo sempre que se acrescenta uma casa.

**Confirmação.** Todos os códigos começam provisórios. Passam a confirmados quando os moradores concordam na aplicação que estão certos (dois telemóveis, pelo menos um no portão, com a maioria das respostas de acordo), e as correções do portão seguem o mesmo consenso. Nenhum código é revisto à mão.

**Governação.** Um só emissor por país garante que duas casas nunca partilham um código. Os setores, os códigos emitidos, as chaves de nome e os blocos de cada nome nunca mudam; acrescentar blocos não é uma mudança. As fichas de edifício mudam com provas. A Câmara Municipal ou a administração de um setor, com os régulos e a comunidade, pode mudar o nome de um lugar (o nome antigo torna-se sinónimo e nenhum número muda), escolher uma vez um nome de placa provisório ou acrescentar lugares, que recebem blocos novos. Se o Estado publicar um sistema de moradas, as suas moradas são mostradas primeiro e os códigos passam a ser referências cruzadas. O repositório, o registo e as regras podem ser transferidos para o Estado ou para um organismo que este designe, o INE, a Câmara Municipal de Bissau ou os Correios, ao abrigo das licenças abertas e sem bifurcar o motor.

# Limites e trabalho futuro

- **Lugares.** O OpenStreetMap e o GeoNames cobrem o país de forma desigual, e a lista de bairros da Câmara Municipal é necessária em Bissau.
- **Nomes de placa.** 356 nomes de placa são provisórios até os conselhos escolherem; 28 ainda não têm forma dentro do limite.
- **Moranças.** O agrupamento é inferido. Nos quintais murados da cidade, as regras só recuperam inteiras 13 % das moranças; as correções dos moradores corrigem-nas com o tempo.
- **Portões.** Só 12 portões estão cartografados, pelo que os pontos de entrada do registo são os centros das moranças até os estafetas e os moradores confirmarem os portões.
- **Alturas.** As alturas são desconhecidas em quase todos os edifícios, pelo que as áreas de pavimento são estimativas.
- **Equipamentos.** Os equipamentos estão pouco cartografados, pelo que os números de acesso da secção 11 subestimam o acesso.
- **Enganos ditos.** Sem o algarismo de controlo, um algarismo errado designa em geral outra morança real (secção 6.3); só a apresentação do lugar descodificado atenua este risco.
- **Fronteiras.** Os códigos são únicos dentro da Guiné-Bissau. Um nome de lugar partilhado com o Senegal ou a Guiné (Madina, Missirá) pode dar aí o mesmo código dito; a aplicação mostra o país em todas as fichas.

O programa de medição abaixo vai substituir as estimativas das secções 8 a 11 por dados de terreno. Deve realizar-se em três bairros de Bissau (Bandim, Bairro Militar, Cuntum) e num grupo de tabancas de Biombo ou de Oio.

| Medida | Método | Objetivo |
|:----------------------------|:------------------------------|:---------------------|
| Lembrança do próprio código ao fim de quatro semanas | moradores questionados em kriol, sem a aplicação | pelo menos 80 % exatos |
| Êxito da entrega à primeira tentativa | estafetas parceiros, com e sem código | pelo menos 20 pontos a mais com código |
| Tempo desde a chegada ao bairro até ao portão | registos horários dos estafetas | reduzido a metade |
| Portões confirmados | moradores e estafetas | 10 000 |
| Tempo de localização das chamadas de emergência | com um serviço de ambulância ou de bombeiros disponível | medido, depois reduzido a metade |
| Lembrança por forma | código, forma só com algarismos e código de grelha para a mesma casa | medida por forma |

: Medições de terreno previstas.

O trabalho futuro inclui a comparação das moranças com os alojamentos georreferenciados do recenseamento, se o INE concordar; o traçado dos muros e portões em imagens de satélite nos bairros de avaliação; e a revisão, por falantes nativos, das leituras em kriol e das regras de redução da equação (8), que só podem juntar chaves por sinónimo, nunca dividir uma faixa.

# Conclusão

As casas da Guiné-Bissau podem ter morada sem dar nome às ruas nem numerar as portas, partindo do que as pessoas já dizem: o nome do seu bairro ou tabanca, seguido de um número. Tornar esse código único exigiu uma faixa nacional de números por nome, dividida em blocos fixos; torná-lo robusto exigiu um algarismo de controlo na forma máquina e uma numeração que mantém os vizinhos próximos; torná-lo duradouro exigiu regras que nunca renumeram um código emitido. Sobre o registo completo de 241 673 códigos, o modelo é único, curto (2,85 algarismos em média) e descodificável sem contexto, e recusa todo o erro de um algarismo no número da sua forma máquina. Os seus benefícios para os cidadãos, os estafetas, os serviços de emergência e o Estado dependem do uso, que o programa de terreno vai medir. O modelo, o motor, o registo e o servidor são abertos e foram pensados para serem entregues ao Estado.

# Disponibilidade dos dados e do código {-}

O motor, a especificação, o registo, o servidor e este artigo estão publicados em <https://github.com/n-ways/open-addresses-guinea-bissau> [@nways-gw]. O código está sob a Apache License 2.0, os dados sob a Open Database License 1.0 e os documentos sob CC BY 4.0. Toda a utilização deve indicar: «N-Ways Addressing for Guinea-Bissau, © N-WAYS LIMITED (nways.ng)». As figuras são desenhadas a partir de dados calculados por `tools/paper_figures.py` sobre o registo publicado.

# Agradecimentos {-}

Agradecemos aos contribuidores do OpenStreetMap que cartografaram os edifícios, as moranças e as ilhas da Guiné-Bissau; à Google Research e à Microsoft, pela publicação das suas implantações de edifícios, e à Overture Maps Foundation, pela sua distribuição; ao GeoNames, pelo seu repertório toponímico; e à União Postal Universal, pela sua documentação sobre endereçamento. Os números do recenseamento são os divulgados pelo Instituto Nacional de Estatística.

# Referências {-}

::: {#refs}
:::
