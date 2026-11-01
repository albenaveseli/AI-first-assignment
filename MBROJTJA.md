# Udhëzues për mbrojtjen

Ky dokument shpjegon **çfarë**, **si** dhe **pse** është bërë çdo pjesë e detyrës, me referenca të sakta te kodi.
Lexoje me radhë: pjesa 0 është baza, pastaj vijnë katër problemet, në fund pyetjet që mund t'i bëjë profesori.

---

## 0. Baza: idetë që përsëriten kudo

### 0.1 Çka është "kërkimi i painformuar"?
Algoritmi **nuk ka asnjë informacion** se sa larg është zgjidhja. Ai thjesht provon mundësitë me një rend fiks.
Nuk ka heuristikë ("kjo duket më afër"). Dallimi midis DFS, BFS dhe IDDFS është vetëm **rendi** në të cilin i provon gjendjet.

### 0.2 Si e kemi modeluar çdo problem: CSP
Të tre problemet e para (Golfers, Sudoku, Latin) janë **Constraint Satisfaction Problems**:

| Fjala | Kuptimi | Shembull (Sudoku) |
|---|---|---|
| **Variabël** | diçka që duhet ta vendosim | një qelizë bosh |
| **Domain** | vlerat që mund t'i marrë | 1–9 |
| **Kufizim** | rregull që s'lejohet të shkelet | në rresht s'përsëritet numri |
| **Gjendje** | si duket "loja" në një moment | grid-i i mbushur pjesërisht |
| **Objective function f(s)** | sa rregulla shkel gjendja | f = 0 → zgjidhje |

Kërkimi ndërton një **pemë**: rrënja = gjendja fillestare, çdo nivel = vendosim një variabël më shumë, gjethet = gjendje të plota.

### 0.3 Motori i përbashkët: [engine.py](engine.py)
Ky është **zemra e projektit**. Algoritmet nuk e dinë cili problem po zgjidhet. Ata flasin me problemin vetëm përmes ndërfaqes `Problem` ([engine.py:25](engine.py#L25)):

| Metoda | Çka bën |
|---|---|
| `initial_state()` | jep gjendjen fillestare |
| `next_variable(state)` | cila variabël vjen tani (`None` = gjithçka e mbushur → zgjidhje) |
| `values(state, var)` | vlerat e domain-it që **nuk** shkelin asnjë kufizim |
| `assign` / `unassign` | vendos / **zhbën** një vlerë (kjo e dyta = backtracking) |
| `copy(state)` | kopje e gjendjes (vetëm BFS ka nevojë) |
| `objective(state)` | f(s), përdoret për verifikim dhe landscape |

**Pse kështu?** Algoritmi shkruhet **një herë** dhe vlen për çdo problem. Në mbrojtje: *"DFS-ja ime është 20 rreshta dhe zgjidh edhe Golfers, edhe Sudoku, edhe Latin Square, sepse ato i njeh vetëm përmes ndërfaqes."*

### 0.4 Çka është Backtracking?
Kur një variabël **nuk ka asnjë vlerë të lejuar**, jemi në **rrugë qorre**: dega braktiset dhe kthehemi te vendimi i mëparshëm për të provuar vlerën tjetër.

Pse është i fuqishëm? Sepse `values()` kthen **vetëm** vlerat e vlefshme. Kështu një degë e gabuar pritet **sapo** shfaqet gabimi, jo në fund. Kjo quhet **pruning** (krasitje).

### 0.5 Statistikat ([engine.py:64](engine.py#L64), klasa `Stats`)
- `nodes`: sa gjendje u krijuan
- `backtracks`: sa herë një degë mbaroi pa rrugëdalje
- `max_memory`: për DFS/IDDFS = thellësia maksimale e stack-ut; për BFS = madhësia maksimale e radhës
- `iterations`: vetëm për IDDFS, sa kufij thellësie u provuan

### 0.6 Landscape ([landscape.py](landscape.py))
"Landscape" = si duket terreni i objective function mbi të gjitha gjendjet. E llogarisim në dy mënyra:
1. **Madhësia e hapësirës** (`landscape_sizes` në secilin problem): sa gjendje ekzistojnë, shprehur si 10^x. E japim hap pas hapi: pa kufizime, pastaj me disa kufizime, pastaj sa zgjidhje ka.
2. **Kampionim** (`sample_objective`, [landscape.py:16](landscape.py#L16)): marrim 1500–2000 gjendje të rastësishme të plota dhe shohim shpërndarjen e f(s).
   **Përfundimi kyç:** asnjë gjendje e rastësishme nuk ka f = 0. Zgjidhjet janë "gjilpërë në kashtë", prandaj na duhet kërkim **sistematik** me backtracking, jo provim i rastësishëm.

---

## 1. Social Golfers: DFS + Backtracking
Skedari: [golfers.py](golfers.py)

### 1.1 Problemi me fjalë të thjeshta
32 lojtarë, çdo javë ndahen në 8 grupe me nga 4. Dy lojtarë nuk lejohet të jenë bashkë në grup **më shumë se një herë**. Sa javë mund të vazhdohet?

### 1.2 ✅ Modelimi
- **Gjendja fillestare:** java 1 sipas shembullit, të gjitha javët e tjera bosh.
- **Veprimi:** vendos një lojtar në vendin e radhës bosh (javë → grup → vend).
- **Testi i qëllimit:** të gjitha vendet plot, dhe f = 0.

### 1.3 ✅ Reprezentimi
| | Përgjigjja | Ku në kod |
|---|---|---|
| **Variabla** | `X(j, k, s)` = lojtari në javën j, grupin k, vendin s | `decode` [golfers.py:88](golfers.py#L88) e kthen indeksin në (javë, grup, vend) |
| **Numri i variablave** | w · g · p (10 · 8 · 4 = 320) | `self.total` |
| **Domain** | {0, 1, …, 31} | `self.all` (bitmask me 32 bite) |
| **K1** | çdo lojtar luan 1 herë në javë | `forbidden = used` te `values` [golfers.py:116](golfers.py#L116) |
| **K2** | dy lojtarë takohen ≤ 1 herë | `forbidden \|= st.met[m]` po aty |

**Gjendja në kod** (klasa `GolfState`, [golfers.py:53](golfers.py#L53)):
- `schedule`: lista me vlerat e të gjitha variablave (-1 = bosh)
- `met[a]`: me kë është takuar lojtari a
- `used[j]`: kush ka luajtur në javën j

**Pse bitmask?** `met[a]` është një numër i plotë ku biti *i* = 1 nëse a është takuar me lojtarin i. P.sh. {0, 2, 5} = `0b100101`. Kontrolli "a janë takuar a dhe b?" bëhet me një veprim të vetëm: `met[a] & (1 << b)`. Kjo e bëri programin rreth 3 herë më të shpejtë.

**Tabela e detyrës ka një gabim:** "Week 1" ka zënë kolonën "Group 1", prandaj Group 8 mbetet bosh. Lojtarët që mungojnë janë pikërisht 16, 17, 18, 19, prandaj Group 8 = {16, 17, 18, 19}. Shih `EXAMPLE_WEEK1` ([golfers.py:30](golfers.py#L30)).

### 1.4 Thyerja e simetrisë: pse dhe si
Shumë orare janë "i njëjti orar i shkruar ndryshe". P.sh. grupi {1,5,9,13} = {13,9,5,1}. Pa thyerje simetrie, DFS do t'i kërkonte të gjitha këto kopje. Rregullat tona (te `values`):
- **S1:** java 1 fikse. Çdo orar mund të riemërtohet që java 1 të jetë kjo, sepse emrat e lojtarëve janë arbitrarë.
- **S2:** brenda grupit, lojtarët në rend rritës (`start = members[-1] + 1`).
- **S3:** grupi fillon me lojtarin më të vogël të lirë (`allowed &= -allowed` merr bitin më të ulët). Kështu renditja e grupeve nuk ka rëndësi.
- **S4:** javët renditen sipas partnerit të dytë të lojtarit 0, sepse renditja e javëve s'ka rëndësi.

**Pse nuk humbet asnjë zgjidhje?** Çdo zgjidhje mund të "rirregullohet" (riemërtim, rirenditje) që t'i plotësojë këto rregulla. Pra nëse ekziston një zgjidhje, ekziston edhe një në formën tonë. Prandaj kur DFS thotë **"JO"**, ajo është **provë**. E testova: pa simetri dhe me simetri, sa herë që të dy mbaruan, dhanë të njëjtën përgjigje.

### 1.5 Forward checking ([golfers.py:143](golfers.py#L143), `_still_feasible`)
Pas vendosjes së lojtarit x, pyesim: *"A mund të përfundojë ende kjo javë?"* Çdo lojtar i lirë duhet ose të mund të hyjë në grupin që po formohet, ose të ketë të paktën p − 1 partnerë që s'i ka takuar. Nëse jo, dega pritet **menjëherë**. Kjo është backtracking i hershëm: zbulon rrugën qorre para se të arrijmë aty.

### 1.6 ✅ Objective function ([golfers.py:191](golfers.py#L191))
```
f(s) = Σ çifte max(0, takime − 1) + Σ javë lojtarë të përsëritur
```
- Nëse çifti (3, 7) takohet 2 herë → +1. Nëse 3 herë → +2.
- Nëse një lojtar shfaqet 2 herë në të njëjtën javë → +1.
- **f = 0 ⇔ orari është i vlefshëm.**

### 1.7 ✅ Landscape ([golfers.py:230](golfers.py#L230))
| Hapësira (32 lojtarë, 10 javë) | Madhësia |
|---|---|
| pa kufizime: 32^320 | 10^482 |
| çdo javë një permutacion: (32!)^10 | 10^354 |
| çdo javë një ndarje në grupe: P^10 | 10^198 |
| me javën 1 fikse: P^9 | 10^178 |

P = 32! / ((4!)^8 · 8!) është numri i mënyrave për t'i ndarë 32 lojtarë në 8 grupe të parenditura me nga 4. Pjesëtojmë me 4!^8 sepse renditja brenda grupit s'ka rëndësi, dhe me 8! sepse renditja e grupeve s'ka rëndësi.

### 1.8 ✅ DFS + Backtracking ([engine.py:140](engine.py#L140))
```python
def recurse(depth, parent_id):
    var = problem.next_variable(state)        # cili vend vjen?
    if var is None: return True               # të gjitha plot → ZGJIDHJE
    for value in problem.values(state, var):  # vetëm lojtarët e lejuar
        problem.assign(state, var, value)     # vendose
        if recurse(depth + 1, ...): return True   # shko më thellë
        problem.unassign(state, var)          # BACKTRACK: zhbëje
    return False                              # asnjë s'funksionoi → kthehu mbrapa
```
**Si ta shpjegosh:** "DFS shkon gjithmonë më thellë. Kur një vend nuk ka lojtar të lejuar, `recurse` kthen False. Prindi e zhbën vendimin me `unassign` dhe provon lojtarin tjetër."

### 1.9 Përgjigjja: sa javë?
**Kufiri teorik:** një lojtar takon 3 të rinj në javë dhe ka 31 për të takuar, pra w ≤ ⌊31/3⌋ = **10** (`upper_bound`, [golfers.py:36](golfers.py#L36)).

| | Javë |
|---|---|
| Kufiri teorik | 10 |
| DFS i thjeshtë | 6 (≈ 20 s) |
| DFS me rinisje të rastësishme | 7 (≈ 1 min) |

**DFS me rinisje** (`dfs_with_restarts`, [golfers.py:261](golfers.py#L261)): DFS ngec herët në një degë të keqe. E ndalojmë pas 20 000 nyjeve dhe e rinisim me renditje tjetër të vlerave. Mbetet DFS + backtracking, pa heuristikë.

**Pyetja e dytë (g, p, w të çfarëdoshme):** programi merr g, p, w dhe jep PO (me orarin), JO (provë, sepse gjithë pema u eksplorua) ose E PANJOHUR (koha mbaroi). Shembull: 12 lojtarë (4 × 3), kufiri është 5, por DFS **vërteton** që 5 javë janë të pamundura. Maksimumi është 4.

---

## 2. Sudoku: BFS + Backtracking
Skedari: [sudoku.py](sudoku.py)

### 2.1 ✅ Modelimi
- **Gjendja fillestare:** grid-i me numrat e dhënë, 0 = bosh.
- **Veprimi:** shkruaj një shifër në qelizën e parë bosh (rresht pas rreshti, rend fiks, pra i painformuar).
- **Testi i qëllimit:** asnjë qelizë bosh dhe f = 0.

### 2.2 ✅ Reprezentimi
| | Përgjigjja | Ku në kod |
|---|---|---|
| **Variablat** | `X(r, c)` për çdo qelizë **bosh** | `next_variable` [sudoku.py:67](sudoku.py#L67): `state.index(0)` |
| **Domain** | {1, …, 9} | `values` [sudoku.py:74](sudoku.py#L74) |
| **Kufizimet** | 27 AllDifferent: 9 rreshta, 9 kolona, 9 kuti | `UNITS` [sudoku.py:42](sudoku.py#L42) |
| **Gjendja** | listë me 81 numra | qeliza (r, c) ka indeksin r · 9 + c |

**PEERS** ([sudoku.py:32](sudoku.py#L32)): për çdo qelizë llogarisim një herë 20 "fqinjët" e saj (8 në rresht, 8 në kolonë, 4 të tjerë në kuti). Vlerat e lejuara = 1–9 minus vlerat e fqinjëve.

### 2.3 Tri nivelet ([sudoku.py:24](sudoku.py#L24))
Nivelet **i kemi matur**, jo zgjedhur sipas syrit: niveli = sa punë i duhet BFS-it. Për secilin kontrollova që ka **saktësisht një zgjidhje** (`count_solutions`).

| Niveli | Bosh | Nyje BFS | Max në memorie |
|---|---|---|---|
| Easy | 45 | 68 | 5 |
| Medium | 51 | 4 631 | 738 |
| Hard | 60 | 364 345 | 33 031 |
| Extreme (bonus) | 61 | 2 068 780 | 356 812 |

### 2.4 ✅ Objective function ([sudoku.py:91](sudoku.py#L91))
```
f(s) = Σ mbi 27 njësitë (9 − numri i vlerave të ndryshme)
```
Nëse një rresht ka dy 5-ëshe, ka vetëm 8 vlera të ndryshme → +1. **f = 0 ⇔ Sudoku është zgjidhur.**

### 2.5 ✅ Landscape ([sudoku.py:134](sudoku.py#L134))
Për Hard: pa kufizime 9^60 ≈ 10^57. Pasi heqim vlerat që bien ndesh me numrat e dhënë: ≈ 10^36. Zgjidhje: **1**.

### 2.6 ✅ BFS + Backtracking ([engine.py:172](engine.py#L172))
```python
queue = deque([gjendja_fillestare])           # radhë FIFO
while queue:
    state = queue.popleft()                    # merr të parën (më të vjetrën)
    var = problem.next_variable(state)
    if var is None: return ZGJIDHJE
    children = problem.values(state, var)      # vetëm shifrat e lejuara
    if not children: backtracks += 1           # RRUGË QORRE → hidhet
    for value in children:
        child = copy(state); assign(child, var, value)
        queue.append(child)                    # fëmijët në fund të radhës
```
**Kjo pyetje ka shumë gjasa të bëhet: "si bën backtrack BFS?"**
BFS klasik **nuk** kthehet mbrapa si DFS, sepse i mban të gjitha degët njëkohësisht në radhë. Te ne backtracking-u është **braktisja e degëve të vdekura**, në dy vende:
1. Një shifër që shkel kufizimet **nuk futet kurrë** në radhë (pruning).
2. Një gjendje ku qeliza e radhës s'ka **asnjë** shifër të lejuar **hidhet** dhe nuk zgjerohet më.

**Kostoja e BFS:** memoria. Te Extreme mban 356 812 Sudoku të pjesshme njëkohësisht, ndërsa DFS vetëm 61. Prandaj BFS përdor `copy()`: çdo gjendje në radhë duhet të ketë kopjen e vet.

---

## 3. Latin Square: IDDFS + Backtracking
Skedari: [latin_square.py](latin_square.py)

### 3.1 ✅ Modelimi
- **Gjendja fillestare:** rreshti i parë = 1 … n (si në shembull), kolona e parë = 1 … n, të tjerat bosh.
- **Veprimi:** shkruaj një numër në qelizën e parë bosh.
- **Testi i qëllimit:** n² qeliza plot dhe f = 0.

### 3.2 ✅ Reprezentimi
| | Përgjigjja | Ku në kod |
|---|---|---|
| **Variablat** | `X(r, c)`, n² variabla | `next_variable` [latin_square.py:54](latin_square.py#L54) |
| **Domain** | {1, …, n} | `values` [latin_square.py:61](latin_square.py#L61) |
| **Kufizimet** | AllDifferent në çdo rresht dhe kolonë | `used = rreshti ∪ kolona` |
| **Gjendja** | listë me n² numra, 0 = bosh | `state[r*n:(r+1)*n]` = rreshti, `state[c::n]` = kolona |

**Thyerja e simetrisë** (`initial_state`, [latin_square.py:36](latin_square.py#L36)): çdo katror latin mund të riemërtohet dhe t'i ndërrohen rreshtat që rreshti dhe kolona e parë të bëhen 1 … n. Nuk humbet asnjë zgjidhje, por pema zvogëlohet shumë. Pa të, IDDFS nuk e zgjidh as n = 5 për 20 sekonda. Me të: 0.01 s.

### 3.3 Shembulli i detyrës
Formula `L[r][c] = ((c − r) mod n) + 1` (`cyclic_construction`, [latin_square.py:92](latin_square.py#L92)) jep **saktësisht** daljen e shembullit.
**Kujdes:** në tekstin e detyrës dalja ka vetëm 4 rreshta. Rreshti i parë `1 2 3 4 5` u "humb" sepse u shkrua menjëherë pas ` ``` ` në Markdown, dhe Markdown-i e lexoi si emër gjuhe.

IDDFS kthen një katror tjetër, po aq të vlefshëm. Detyra kërkon "**një** matricë", jo pikërisht atë. Për n = 5 ka 161 280 të tillë.

### 3.4 ✅ Objective function ([latin_square.py:80](latin_square.py#L80))
```
f(s) = Σ rreshta (n − vlera të ndryshme) + Σ kolona (n − vlera të ndryshme)
```

### 3.5 ✅ Landscape ([latin_square.py:123](latin_square.py#L123))
| n = 5 | Madhësia |
|---|---|
| pa kufizime: 5^25 | 10^17.5 |
| çdo rresht permutacion: (5!)^5 | 10^10.4 |
| katrorë latinë | 161 280 ≈ 10^5.2 |

`count_all` ([latin_square.py:101](latin_square.py#L101)) i **numëron vetë** me DFS të plotë për n ≤ 4: 1, 2, 12, 576. Përputhen me vlerat e njohura (OEIS A002860).

### 3.6 ✅ IDDFS + Backtracking ([engine.py:215](engine.py#L215))
```python
for limit in 0, 1, 2, ...:                     # kufiri i thellësisë rritet
    r = depth_limited(gjendja_fillestare, 0, limit)
    if r == "found":   return ZGJIDHJE
    if r == "failure": return PA ZGJIDHJE      # asgjë s'u pre nga kufiri

def depth_limited(state, depth, limit):
    if e plotë: return "found"
    if depth == limit: return "cutoff"         # mund të ketë më thellë
    for value in values(...):
        assign; r = depth_limited(..., depth + 1, limit)
        if r == "found": return "found"
        unassign                                # BACKTRACK
```
**Ideja:** IDDFS = DFS i përsëritur me kufi gjithnjë e më të thellë.
- **Memoria** si DFS: vetëm një rrugë njëkohësisht.
- **Garancia** si BFS: gjen zgjidhjen më të cekët.
- **Kostoja:** nivelet e sipërme rivizitohen në çdo iteracion.

**Dallimi "cutoff" kundrejt "failure"** (pikë e mirë për mbrojtjen): "cutoff" do të thotë "u ndal nga kufiri, ndoshta ka zgjidhje më thellë", kurse "failure" do të thotë "s'ka zgjidhje fare në këtë degë". Nëse gjithë iteracioni kthen "failure", s'ka kuptim të rritet kufiri.

### 3.7 Zbulimi i rëndësishëm: pse IDDFS është i ngadaltë këtu?
Te Latin Square **të gjitha** zgjidhjet janë në thellësinë e fundit (n² qeliza). IDDFS, para se të arrijë aty, e eksploron **gjithë pemën** për çdo kufi më të vogël. Iteracioni i fundit është thjesht DFS.

| n | DFS | IDDFS |
|---|---|---|
| 5 | 28 nyje | 4 897 nyje |
| 6 | 51 nyje | 1 194 051 nyje |

Për n ≥ 7, IDDFS nuk mbaron në kohë, dhe programi tregon zgjidhjen e iteracionit të fundit (DFS). **Përfundimi:** IDDFS ia vlen kur zgjidhja është **e cekët** dhe thellësia nuk dihet (p.sh. 8-Puzzle), jo kur zgjidhja është gjithmonë në fund.

---

## 4. Search Trees
Kjo pikë dorëzohet **vetëm si PDF** te [Search_Trees_PDF/](Search_Trees_PDF/): `Search_Trees.pdf` (të tria pemët) dhe nga një PDF për secilin problem. Nuk ka kod për të, as faqe në web.

### 4.1 Si lexohet pema në PDF
Çdo PDF ka: formulimin e problemit, pemën nivel pas niveli, pemën e plotë dhe rrugën e zgjidhjes.
1. Rrënja = gjendja fillestare.
2. Fëmijët e një nyjeje = gjendjet që arrihen me **një** veprim.
3. Çdo nyje është shënuar:
   - **invalid**: shkel rregullin, nuk zgjerohet më tej;
   - **repeated**: gjendja është parë më parë, nuk zgjerohet;
   - **goal**: zgjidhja;
   - **normal**: zgjerohet.
4. Rruga nga rrënja te goal-i është e theksuar.
5. BFS e zgjeron pemën nivel pas niveli (radhë FIFO), DFS shkon thellë në një degë (stack).

**Pse shënohen gjendjet e përsëritura?** Pa këtë, pema do të ishte e pafundme. P.sh. te 8-Puzzle mund të lëvizësh LART-POSHTË-LART-POSHTË pa fund.

### 4.2 ✅ 8-Puzzle (BFS)
- **Gjendja:** tuple me 9 numra, 0 = vendi bosh.
- **Veprimet:** vendi bosh lëviz LART, POSHTË, MAJTAS, DJATHTAS. Lëvizjet jashtë tabelës nuk ekzistojnë.
- **Goal:** 1 2 3 / 4 5 6 / 7 8 _
- **Rezultati:** nga `123/_46/758`, pema ka 24 nyje dhe zgjidhja 3 hapa: DJATHTAS, POSHTË, DJATHTAS.
- **Fakt për mbrojtjen:** gjysma e gjendjeve **nuk** e arrijnë dot goal-in. Arsyeja: çdo lëvizje e ruan paritetin e numrit të "inversioneve" (çifte numrash në rend të gabuar). Goal-i ka 0 inversione (çift), prandaj gjendjet me numër tek inversionesh nuk e arrijnë kurrë.

### 4.3 ✅ Missionaries and Cannibals (BFS)
- **Gjendja:** (M, C, B) = misionarë dhe kanibalë në bregun e **majtë**, B = 1 nëse varka është majtas.
- **Veprimet:** varka merr 1M, 2M, 1C, 2C ose 1M+1C.
- **Rregulli:** në asnjë breg kanibalët s'janë më shumë se misionarët, kur ka misionarë.
- **Goal:** (0, 0, 0).
- **Rezultati:** 47 nyje (18 të pavlefshme, 14 të përsëritura), zgjidhja me **11 kalime**.

### 4.4 ✅ Rotating Workforce Scheduling (DFS)
Detyra nuk jep të dhëna, prandaj e **përcaktuam vetë** një rast të vogël:
- 3 punëtorë, 7 ditë, ndërrimet D (ditë), N (natë), − (pushim). Çdo ditë: 1 D, 1 N dhe 1 pushim.
- **"Rotating":** orari ka 3 rreshta. Punëtori 1 punon rreshtin 1 në javën 1, rreshtin 2 në javën 2, rreshtin 3 në javën 3, pastaj rifillon. Pra 21 ditët janë një **cikël**.
- **Rregullat:** pas N s'vjen D; max 4 ditë pune radhazi; max 2 pushime radhazi.
- **Gjendja:** ditët e caktuara deri tani. **Veprimi:** cakto ditën e radhës (6 mënyra: permutacionet e D, N, −).
- **Rezultati:** pema me DFS, 43 nyje, orar i vlefshëm në thellësinë 7.

---

## 5. Skedarët e tjerë

| Skedari | Roli |
|---|---|
| [main.py](main.py) | Programi në terminal. P.sh. `python main.py golfers 4 3 5`, `python main.py latin 5`, `python main.py race` |
| [server.py](server.py) | Serveri FastAPI. Çdo endpoint e ekzekuton algoritmin **live** dhe kthen zgjidhjen + statistikat + gjurmën për animacion. Dokumentimi i API-së: `/docs` |
| [static/](static/) | Faqja web: `index.html` (struktura), `app.js` (logjika, player-i), `polish.js` (animacionet), 3 skedarë CSS |
| [Search_Trees_PDF/](Search_Trees_PDF/) | Pika 4: pemët e kërkimit hap pas hapi, si PDF |
| [README.md](README.md) | Dokumentimi i projektit (në anglisht) |

**Gjurma e kërkimit** (`Tracer`, [engine.py:97](engine.py#L97)): gjatë kërkimit regjistrojmë çdo nyje me prindin, thellësinë, variablën dhe vlerën. Faqja web e riprodhon këtë hap pas hapi. Grafiku i thellësisë tregon "nënshkrimin" e algoritmit: DFS = dhëmbë sharre, BFS = shkallë, IDDFS = disa sharra radhazi.

---

## 6. Gara: pse secili problem ka algoritmin e vet
`python main.py race` ose faqja *Race*.

| | DFS | BFS | IDDFS |
|---|---|---|---|
| Golfers 8×4, 5 javë | ✔ 0.06 s | ✖ mbushet memoria (600 mijë gjendje) | ✖ rivizitime |
| Sudoku Hard | ✔ | ✔ 33 mijë në memorie | ✖ shumë ngadalë |
| Latin n = 6 | ✔ 51 nyje | ✔ 172 mijë nyje | ✔ 1.2 milion nyje |

| Algoritmi | Memoria | Gjen më të cekëtën? | I plotë? |
|---|---|---|---|
| DFS | O(d), e vogël | jo | po, në pemë të fundme |
| BFS | O(b^d), e madhe | po | po |
| IDDFS | O(d), e vogël | po | po |

(d = thellësia, b = numri i fëmijëve për nyje)

---

## 7. Pyetje që mund t'i bëjë profesori

**Pse thua që kërkimi është "i painformuar"?**
Rendi i variablave është fiks (qeliza e parë bosh, vendi i radhës) dhe vlerat provohen me radhë. Nuk ka asnjë vlerësim "sa larg jemi nga zgjidhja".

**A nuk është forward checking-u një heuristikë?**
Jo. Forward checking nuk ndryshon **rendin** e kërkimit dhe nuk vlerëson afërsinë me zgjidhjen. Ai vetëm pret degët që janë **me siguri** të vdekura. Është backtracking i hershëm.

**Si e di që zgjidhja është e saktë?**
Çdo zgjidhje verifikohet me objective function, dhe programi printon `f(s) = 0`.

**Pse nuk gjen DFS 10 javë për 32 lojtarë?**
Hapësira është rreth 10^178 edhe pas thyerjes së simetrisë. Në javët e fundit mbeten shumë pak çifte të lira, dhe DFS kthehet mbrapa miliona herë. 10 javë ekzistojnë sipas literaturës (CSPLib, problemi 10), por u gjetën me metoda konstruktive të specializuara, jo me kërkim të verbër.

**Si e di që 12 lojtarë s'mund të luajnë 5 javë?**
DFS e eksploroi gjithë pemën pa gjetur zgjidhje. Meqë thyerja e simetrisë nuk heq asnjë zgjidhje, kjo është provë e plotë.

**Ku është backtracking-u te BFS?**
Shih pikën 2.6: vlerat e pavlefshme nuk futen në radhë, dhe gjendjet pa vlerë të lejuar hidhen.

**Pse IDDFS te Latin Square bën më shumë punë se DFS?**
Shih pikën 3.7: zgjidhjet janë gjithmonë në fund, dhe IDDFS rivizitot nivelet e sipërme në çdo iteracion.

**Pse fiksove rreshtin e parë te Latin Square? A nuk është mashtrim?**
Jo. Çdo katror latin mund të sillet në këtë formë me riemërtim dhe rirenditje rreshtash, prandaj nuk humbet asnjë zgjidhje. Edhe shembulli i detyrës fillon me `1 2 3 4 5`.

**Si ndryshon pema BFS nga pema DFS?**
BFS merr nyjen më të vjetër (radhë FIFO), prandaj pema rritet nivel pas niveli. DFS merr nyjen më të re (stack), prandaj zbret thellë në një degë para se të provojë tjetrën. Shih PDF-të: 8-Puzzle dhe Missionaries janë me BFS, Rotating Workforce me DFS.

**Pse objective function, kur kërkimi s'ka nevojë për të?**
Kërkimi i painformuar nuk e përdor për të udhëhequr kërkimin. E përdorim për dy gjëra: (1) **verifikimin** e zgjidhjes (f = 0) dhe (2) **landscape-in**, për të treguar sa e rrallë është një zgjidhje.

---

## 8. Demo e shpejtë për prezantim (5 minuta)
1. `python server.py`, pastaj hap http://127.0.0.1:8000
2. **Overview:** trego matricën e kërkesave, ku çdo ✓ të çon te seksioni.
3. **Social Golfers:** "Small example (12 players)" → shtyp ▶ te player-i dhe trego backtracking-un (pikat e kuqe). Pastaj w = 5 → "NO", me provë.
4. **Sudoku:** Hard → Solve → trego "max queue size" (memoria e BFS). Pastaj Extreme.
5. **Latin Square:** n = 5 → trego daljen dhe formulën ciklike. Ndrysho në DFS dhe krahaso nyjet.
6. **Search Trees:** hap `Search_Trees_PDF/Search_Trees.pdf` dhe trego pemën e Missionaries me 11 kalimet.
7. **Race:** fillo garën dhe shpjego tabelën e kompromiseve.
