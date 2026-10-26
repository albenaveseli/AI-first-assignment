# Search Lab: Teknikat e Painformuara të Kërkimit

Detyra e parë semestrale. Katër probleme, tre algoritme dhe **një motor kërkimi i përbashkët**.

## Si ekzekutohet

### Aplikacioni web (FastAPI), mënyra kryesore
```bash
pip install -r requirements.txt
python server.py               # hap http://127.0.0.1:8000
```
Faqja është në anglisht. Çdo algoritëm ekzekutohet **live** në server. Faqja e riprodhon kërkimin hap pas hapi mbi tabelë
(Sudoku, Latin Square, orari i Golfers), me grafikun e thellësisë dhe me zë.
Në hyrje është **matrica e kërkesave**: çdo kërkesë e detyrës lidhet me seksionin ku zgjidhet.

| Endpoint | Çka bën |
|---|---|
| `GET /api/golfers?g=8&p=4&w=6&restarts=false` | DFS për SGP(g, p, w) |
| `GET /api/golfers/landscape?g=8&p=4&w=10` | landscape i Golfers |
| `POST /api/sudoku` `{"level": "hard", "algo": "BFS"}` ose `{"puzzle": "81 shifra"}` | zgjidhësi i Sudoku |
| `GET /api/latin?n=5&algo=IDDFS` | Latin Square |
| `GET /api/trees/puzzle?start=123046758` · `/api/trees/mc?m=3&c=3&boat=2` · `/api/trees/rws` | search trees |
| `GET /api/race/{golfers,sudoku,latin}?algo=DFS` | gara |

Dokumentimi automatik i API-së: `http://127.0.0.1:8000/docs`

### Nga terminali
```bash
python main.py                 # menu interaktive
python main.py golfers         # 32 lojtarë: "Sa javë?"
python main.py golfers 8 4 6   # A është e mundur g=8, p=4, w=6?
python main.py sudoku          # Easy, Medium, Hard
python main.py sudoku hard     # një nivel (ose 81 shifra, 0 = bosh)
python main.py latin 5         # katror latin n = 5
python main.py trees           # 3 search trees
python main.py race            # gara DFS vs BFS vs IDDFS

python export_web.py           # version statik: gjeneron web/data.js për web/index.html
```

Algoritmet kërkojnë vetëm Python 3.10 ose më të ri. FastAPI duhet vetëm për serverin web.

## Struktura

| Skedari | Çka përmban |
|---|---|
| [engine.py](engine.py) | Motori: `Problem`, **DFS**, **BFS**, **IDDFS**, statistikat |
| [golfers.py](golfers.py) | 1. Social Golfers (DFS + Backtracking) |
| [sudoku.py](sudoku.py) | 2. Sudoku (BFS + Backtracking), 3 nivele + 1 bonus |
| [latin_square.py](latin_square.py) | 3. Latin Square (IDDFS + Backtracking) |
| [search_trees.py](search_trees.py) | 4. Search Trees: 8-Puzzle, Missionaries & Cannibals, Rotating Workforce |
| [landscape.py](landscape.py) | Llogaritja e landscape (madhësia + shpërndarja e f) |
| [main.py](main.py) | Programi në terminal |
| [server.py](server.py) | Serveri FastAPI (API + faqja) |
| [static/](static/) | Faqja web live (në anglisht): `index.html`, `app.js` (logjika), `style.css` + `visuals.css` + `polish.css` (dizajni), `polish.js` (animacionet) |
| [web/index.html](web/index.html) | Versioni statik i vizualizimit (pa server) |

## Ideja kryesore: një motor për të gjitha problemet

Çdo problem përshkruhet me të njëjtat pjesë:

| Pjesa | Kuptimi |
|---|---|
| **Variablat** | Çka duhet të vendosim |
| **Domain** | Vlerat që mund t'i marrë një variabël |
| **Kufizimet** | Rregullat që nuk lejohet të shkelen |
| **Objective function** | `f(s)` = numri i shkeljeve. **f(s) = 0 ⇔ s është zgjidhje** |

Algoritmet në `engine.py` **nuk e dinë** cili problem po zgjidhet. Ata thërrasin vetëm:
`next_variable` (cila variabël vjen), `values` (cilat vlera janë ende të lejuara), `assign` / `unassign`.

**Backtracking** do të thotë: kur një variabël nuk ka asnjë vlerë të lejuar, dega braktiset.
- Te **DFS** dhe **IDDFS**: zhbëjmë vendimin e fundit (`unassign`) dhe provojmë vlerën tjetër.
- Te **BFS**: gjendja pa rrugëdalje hidhet nga radha dhe nuk zgjerohet më. Vlerat që shkelin kufizimet nuk futen kurrë në radhë.

Çdo zgjidhje e gjetur **verifikohet** me objective function: programi printon `f(s) = 0`.

---

## 1. Social Golfers Problem (DFS + Backtracking)

### Modelimi dhe reprezentimi
Rasti i përgjithshëm: `g` grupe, `p` lojtarë për grup, `w` javë, `n = g·p`.

- **Variablat:** `X(j, k, s)` = lojtari në javën *j*, grupin *k*, vendin *s*. Gjithsej `w·g·p` variabla (për 8×4×10: 320).
- **Domain:** `{0, 1, …, n−1}`
- **Kufizimet:**
  - K1: në një javë, çdo lojtar luan saktësisht një herë.
  - K2: dy lojtarë takohen më së shumti **një herë** gjatë gjithë javëve.
- **Thyerja e simetrisë** (nuk e ndryshon përgjigjen, vetëm e shkurton kërkimin):
  - S1: java 1 merret fikse, **saktësisht si në shembullin e detyrës**.
  - S2: brenda grupit lojtarët janë në rend rritës (`{1,5,9,13}` = `{13,9,5,1}`).
  - S3: grupi fillon me lojtarin më të vogël që s'ka luajtur ende atë javë (renditja e grupeve s'ka rëndësi).
  - S4: javët renditen sipas partnerit të dytë të lojtarit 0 (renditja e javëve s'ka rëndësi).
- **Forward checking:** pas çdo vendosjeje kontrollojmë: a ka çdo lojtar i lirë ende së paku `p−1` partnerë që s'i ka takuar? Nëse jo, dega pritet **menjëherë**, pa pritur të ngecet më poshtë.
- **Reprezentimi në kod:** bashkësitë ruhen si **bitmask** (numër i plotë ku biti *i* = lojtari *i*). Kështu kontrolli "a janë takuar?" bëhet me një veprim të vetëm.

### Objective function
```
f(s) = Σ_{çdo çift (a,b)} max(0, takime(a,b) − 1)  +  Σ_{çdo javë} (lojtarë të përsëritur)
f(s) = 0  ⇔  orari është i vlefshëm
```

### Përgjigjja: sa javë?
Në çdo javë një lojtar takon `p − 1 = 3` lojtarë të rinj. Gjithsej ka `n − 1 = 31` për të takuar. Pra:

```
w ≤ ⌊(n − 1) / (p − 1)⌋ = ⌊31 / 3⌋ = 10 javë
```

| Metoda | Javë të gjetura për 32 lojtarë |
|---|---|
| Kufiri teorik | **10** |
| DFS + Backtracking (deterministik) | **6** (≈ 20 s, 2 milionë nyje) |
| DFS me rinisje të rastësishme | **7** (≈ 1 min) |

Sipas literaturës (CSPLib, problemi 10), zgjidhja me 10 javë ekziston, por u gjet vetëm në vitin 2004 me metoda të specializuara konstruktive. Kërkimi i verbër ngadalësohet sepse në javët e fundit mbeten shumë pak çifte të lira.

**DFS me rinisje:** DFS i thjeshtë ngec në një degë të keqe herët dhe nuk del prej saj. E ndalojmë pas 20 000 nyjeve dhe e nisim përsëri me renditje tjetër të vlerave. Mbetet DFS + Backtracking, pa heuristikë.

**Kufiri nuk arrihet gjithmonë:** për 12 lojtarë (4 grupe × 3), kufiri është ⌊11/2⌋ = 5. DFS e eksploron **gjithë** pemën dhe **vërteton** që 5 javë janë të pamundura (`python main.py golfers 4 3 5`). Maksimumi është 4.

### Landscape (32 lojtarë, 10 javë)
| Hapësira | Madhësia |
|---|---|
| Pa kufizime: 32^320 | ≈ 10^482 |
| Çdo javë një permutacion (K1): (32!)^10 | ≈ 10^354 |
| Çdo javë një ndarje në grupe: P^10, ku P = 32! / ((4!)^8 · 8!) | ≈ 10^198 |
| Me javën 1 fikse: P^9 | ≈ 10^178 |

Nga 2000 orare të rastësishme, **asnjë** nuk ka f = 0. Zgjidhjet janë "gjilpërë në kashtë".

---

## 2. Sudoku Solver (BFS + Backtracking)

### Modelimi dhe reprezentimi
- **Variablat:** `X(r, c)` për çdo qelizë **bosh**.
- **Domain:** `{1, …, 9}`
- **Kufizimet:** AllDifferent në çdo rresht, kolonë dhe kuti 3×3 (27 kufizime). Numrat e dhënë nuk ndryshojnë.
- **Gjendja:** listë me 81 numra, ku 0 = bosh. Variabla e radhës është qeliza e parë bosh (renditje fikse, e painformuar).
- **Lidhja me problemin 3:** një Sudoku i zgjidhur **është** Latin Square 9×9 me një kufizim shtesë për kutitë.

### Objective function
```
f(s) = Σ_{27 njësitë} (9 − numri i vlerave të ndryshme në njësi)
f(s) = 0  ⇔  Sudoku është zgjidhur
```

### Tri nivelet
Niveli është **matur** me punën që i duhet BFS-it. Çdo Sudoku është kontrolluar që ka **saktësisht një** zgjidhje.

| Niveli | Qeliza bosh | Nyje BFS | Gjendje në memorie (max) | Koha |
|---|---|---|---|---|
| Easy | 45 | 68 | 5 | 0.00 s |
| Medium | 51 | 4 631 | 738 | 0.01 s |
| Hard | 60 | 364 345 | 33 031 | ≈ 1 s |
| Ekstrem (bonus: Arto Inkala, 2012) | 61 | 2 068 780 | 356 812 | ≈ 6 s |

### Landscape
| Niveli | Pa kufizime 9^bosh | Pas heqjes së vlerave që bien ndesh me të dhënat | Zgjidhje |
|---|---|---|---|
| Easy | 10^42.9 | 10^11.1 | 1 |
| Medium | 10^48.7 | 10^22.6 | 1 |
| Hard | 10^57.3 | 10^35.8 | 1 |

### Pse BFS "me backtracking"?
BFS në kuptimin klasik nuk kthehet mbrapa, sepse i mban të gjitha degët njëkohësisht në radhë (FIFO). Te ne, backtracking-u ndodh në dy vende:
1. Një vlerë që shkel kufizimet **nuk futet kurrë** në radhë (pruning).
2. Një gjendje ku variabla e radhës nuk ka **asnjë** vlerë të lejuar hidhet. Kjo është rrugë qorre, dhe numërohet si backtrack.

Kostoja e BFS është **memoria**: te Sudoku Ekstrem mban 356 812 Sudoku të pjesshme njëkohësisht, ndërsa DFS mban vetëm 61 (një për çdo nivel).

---

## 3. Latin Square (IDDFS + Backtracking)

### Modelimi dhe reprezentimi
- **Variablat:** `X(r, c)` për çdo qelizë, n² variabla.
- **Domain:** `{1, …, n}`
- **Kufizimet:** AllDifferent në çdo rresht dhe në çdo kolonë.
- **Thyerja e simetrisë:** rreshti i parë = 1 2 … n (si në shembullin e detyrës), kolona e parë = 1 2 … n. Çdo katror latin mund të kthehet në këtë formë duke i riemërtuar numrat dhe duke i ndërruar rreshtat, prandaj nuk humbet asnjë zgjidhje.

### Objective function
```
f(s) = Σ_{rreshta} (n − vlera të ndryshme) + Σ_{kolona} (n − vlera të ndryshme)
f(s) = 0  ⇔  s është katror latin
```

### IDDFS
DFS me kufi thellësie `L = 0, 1, 2, …`. Çdo iteracion rifillon nga rrënja.
- Memoria: si DFS, `O(thellësia)`.
- Garancia: si BFS, gjen zgjidhjen më të cekët.
- Kostoja: nivelet e sipërme rivizitohen në çdo iteracion.

| n | Nyje IDDFS | Iteracione | Koha |
|---|---|---|---|
| 4 | 151 | 10 | 0.00 s |
| 5 | 4 897 | 17 | 0.01 s |
| 6 | 1 194 051 | 26 | ≈ 2.6 s |

**Zbulim nga eksperimentet:** te Latin Square **të gjitha** zgjidhjet ndodhen në thellësinë e fundit (çdo qelizë e mbushur). Për çdo kufi `L` para saj, IDDFS e eksploron **gjithë** pemën deri në `L`, kurse iteracioni i fundit është thjesht DFS. Për n = 6, DFS i duhen 51 nyje dhe IDDFS-it 1.2 milionë. Pa thyerjen e simetrisë, IDDFS nuk e zgjidh as n = 5 brenda 20 sekondave. Për n ≥ 7 programi e shpjegon këtë dhe e tregon zgjidhjen e iteracionit të fundit (DFS).

IDDFS shkëlqen kur zgjidhja është **e cekët** dhe thellësia e saj nuk dihet, p.sh. te 8-Puzzle.

**Krahasim pa kërkim:** `L[r][c] = ((c − r) mod n) + 1` jep **saktësisht** daljen e shembullit të detyrës.

### Landscape (n = 5)
| Hapësira | Madhësia |
|---|---|
| Pa kufizime: 5^25 | ≈ 10^17.5 |
| Çdo rresht permutacion: (5!)^5 | ≈ 10^10.4 |
| Katrorë latinë (zgjidhje): 161 280 | ≈ 10^5.2 |

Numri i saktë i katrorëve latinë sipas n (OEIS A002860): 1, 2, 12, 576, 161 280, 812 851 200, … Për n ≤ 4 programi i numëron vetë (`latin_square.count_all(4)` = 576).

---

## 4. Search Trees

Pema ndërtohet me të njëjtin funksion për të tre problemet (`build_tree`). Çdo nyje shënohet:

| Shenja | Kuptimi |
|---|---|
| `[GOAL]` | gjendje përfundimtare |
| `[X invalid]` | shkel një kufizim; nuk zgjerohet |
| `[perseritur]` | gjendje e parë më parë; nuk zgjerohet (përndryshe pema do ishte e pafundme) |
| `*` | nyja është në rrugën e zgjidhjes |

### 8-Puzzle (BFS)
- **Gjendja:** tabela 3×3, 0 = vendi bosh. **Veprimet:** lëvizja e vendit bosh LART, POSHTË, MAJTAS, DJATHTAS.
- **Goal:** `123/456/78_`. Nga `123/_46/758` zgjidhja ka 3 hapa. Pema ka 24 nyje.
- Fakt: gjysma e gjendjeve të 8-Puzzle nuk e arrijnë dot goal-in (paritet i inversioneve, `EightPuzzle.is_solvable`).

### Missionaries and Cannibals (BFS)
- **Gjendja:** `(M, C, B)` = misionarë dhe kanibalë në bregun e majtë, B = ku është varka.
- **Veprimet:** varka merr 1M, 2M, 1C, 2C ose 1M+1C.
- **Kufizimi:** në asnjë breg kanibalët s'janë më shumë se misionarët (kur ka misionarë).
- Pema e plotë ka 47 nyje. Zgjidhja ka **11 kalime**.

### Rotating Workforce Scheduling (DFS)
Detyra nuk jep të dhëna, prandaj e përcaktuam vetë një rast të vogël:
- 3 punëtorë, 7 ditë, ndërrimet **D** (ditë), **N** (natë), **-** (pushim).
- Çdo ditë duhet 1 D, 1 N dhe 1 pushim.
- *Rotating:* orari ka 3 rreshta. Punëtori 1 nis me rreshtin 1 dhe çdo javë kalon në rreshtin tjetër, kështu që 21 ditët lexohen si një varg ciklik.
- **Rregullat:** pas N nuk vjen D · jo më shumë se 4 ditë punë radhazi · jo më shumë se 2 pushime radhazi.
- **Gjendja:** ditët e caktuara deri tani. **Veprimi:** cakto ditën e radhës (6 mënyra).

---

## Gara e algoritmeve (`python main.py race`)

| Problemi | DFS | BFS | IDDFS |
|---|---|---|---|
| Golfers 8×4, 5 javë | ✔ 5 713 nyje, 0.06 s | ✖ memoria: 600 mijë gjendje | ✖ rivizitime |
| Sudoku Hard | ✔ 304 053 nyje | ✔ 364 345 nyje, 33 mijë në memorie | ✖ > 2 milionë nyje |
| Latin Square n = 6 | ✔ 51 nyje | ✔ 172 914 nyje | ✔ 1 194 051 nyje |

**Përfundimi:**
- **DFS** përdor pak memorie dhe arrin shpejt në fund, por mund të ngecë në një degë të keqe.
- **BFS** gjen zgjidhjen më të cekët, por e paguan me memorie të madhe.
- **IDDFS** ka memorien e DFS-it dhe garancinë e BFS-it, por i përsërit nivelet e sipërme. Ia vlen vetëm kur zgjidhja është e cekët.

## Vizualizimi (`web/index.html`)
- **Modeli** i çdo problemi në kartela.
- **Landscape:** madhësia e hapësirës (shkallë logaritmike) dhe histogrami i f(s).
- **"Si mendon algoritmi":** grafiku i thellësisë së çdo nyjeje sipas rendit të vizitës. DFS vizaton dhëmbë sharre, BFS shkallë, IDDFS disa sharra njëra pas tjetrës (një për çdo iteracion). Mund të luhet hap pas hapi, me zë.
- **Golfers:** matrica e takimeve 32×32 dhe orari me **emrat e klasës**.
- **Search Trees:** pemë që hapen dhe mbyllen me klik, me rrugën e zgjidhjes të theksuar.
- **Gara** e tre algoritmeve.
