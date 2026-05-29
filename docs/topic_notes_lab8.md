# Topic Notes — Lab 8: Topic Modeling (LSA / LDA)

**Corpus:** 20 Newsgroups — 3 classes: `alt.atheism`, `sci.electronics`, `soc.religion.christian`  
**Corpus size:** 6,192 documents (після фільтрації: видалено документи < 15 слів та metadata footers)  
**Date:** 2026-05-29

---

## 1. Models and Parameters

### LSA (Latent Semantic Analysis)
- Vectorizer: `TfidfVectorizer`, `analyzer='word'`, `ngram_range=(1,1)`, `min_df=5`, `max_df=0.90`, `stop_words='english'`, `sublinear_tf=True`
- Decomposition: `TruncatedSVD`, `random_state=42`
- k values tested: **5**, **8**
- Explained variance (k=5): **0.022** (2.2%) — LSA на BOW корпусі пояснює мало дисперсії

### LDA (Latent Dirichlet Allocation)
- Vectorizer: `CountVectorizer`, `analyzer='word'`, `ngram_range=(1,1)`, `min_df=5`, `max_df=0.90`, `stop_words='english'`
- Model: `LatentDirichletAllocation`, `random_state=42`, `max_iter=30`, `learning_method='online'`, `doc_topic_prior=0.1`, `topic_word_prior=0.01`
- k values tested: **5**, **8**
- Perplexity k=5: **~3,224** | k=8: **~3,141**

### Corpus filtering
- Видалено документи < 15 слів (136 документів)
- Stripped `Newsgroup: {class}` та `document_id: {num}` footers (leakage artefacts від Lab 5)
- Видалено PII placeholders (`<URL>`, `<EMAIL>`, `<PHONE>`) з тексту

---

## 2. Topics

### 2.1 LDA k=5 — Результати

| Topic | Top words | Назва | Якість |
|-------|-----------|-------|--------|
| 0 | god, believe, does, atheism, evidence, say, don, belief, atheists, true | Атеїзм / суперечки про Бога | GOOD |
| 1 | think, people, don, just, like, know, time, bible, writes, good | Загальний дискурс Usenet | BAD |
| 2 | islam, religion, people, islamic, writes, book, jon, muslim, religious, world | Іслам та релігійні дискусії | MODERATE |
| 3 | use, like, used, power, know, just, thanks, ground, don, good | Електроніка (погано виділена) | BAD/NOISY |
| 4 | god, jesus, church, christ, sin, paul, faith, love, lord, man | Християнська теологія | GOOD |

**Topic-label alignment (LDA k=5):**

| Клас | T0 | T1 | T2 | T3 | T4 |
|------|----|----|----|----|-----|
| alt.atheism | 653 | **894** | 513 | 105 | 153 |
| sci.electronics | 42 | 84 | 4 | **1760** | 2 |
| soc.religion.christian | 182 | 600 | 94 | 46 | **1060** |

#### Topic 0: Атеїзм / суперечки про Бога
**Якість: GOOD**  
Топ-слова `atheism`, `atheists`, `belief`, `evidence` чітко вказують на `alt.atheism`. Топ-документи — дебатні пости з аргументами про існування Бога, мораль без релігії, докази. Тема стабільна та змістовна.  
Слабкість: слова `god`, `believe`, `say`, `don` — загальні для обох релігійних класів. Частина `alt.atheism` постів іде в Topic 1 (загальний дискурс) — це типова проблема для класу, де тон (аргументативний) важливіший за лексику.

#### Topic 1: Загальний дискурс Usenet
**Якість: BAD — generic/stop-word topic**  
Слова `think`, `people`, `don`, `just`, `like`, `know`, `time`, `good` — це стиль усіх Usenet постів, а не тема. Ця тема є "смітниковим відром" для загального дискурсу. Поглинає 894 документів `alt.atheism` і 600 `soc.religion.christian` — обидва класи мають схожий дискусійний стиль.  
**Чому так сталося:** `stop_words='english'` в sklearn видаляє граматичні слова, але не неформальні дискурсні слова Usenet (`think`, `know`, `writes`, `good`). Це — класичний "stop-word topic" або "style topic".

#### Topic 2: Іслам та міжрелігійні дискусії
**Якість: MODERATE**  
Несподівана тема — LDA знайшов підтему про іслам. `alt.atheism` newsgroup часто містив дискусії про Коран (`Qur'an`), іслам та Рушді. Це реальна підтема, але не окремий клас у датасеті. `jon` — це username активного учасника. Тема реальна, але часткова — ісламські дискусії перемішані з загальними релігійними.

#### Topic 3: Електроніка (погано виділена)
**Якість: BAD/NOISY**  
Клас `sci.electronics` дуже добре ізольований за домінантним топіком (1760 із 1892 документів → Topic 3). Але самі топ-слова слабкі: `power`, `ground` — електроніка, але `use`, `like`, `used`, `know`, `just`, `thanks`, `don`, `good` — загальний дискурс. Ця тема виявлена правильно (за alignment), але слова не читабельні без контексту.  
**Чому:** Electronics-специфічна лексика (`circuit`, `voltage`, `resistor`) не домінує достатньо над загальними словами. Потрібно min_df менший, або bigrams (`voltage divider`, `power supply`).

#### Topic 4: Християнська теологія
**Якість: GOOD**  
`jesus`, `church`, `christ`, `sin`, `paul`, `faith`, `love`, `lord` — однозначно `soc.religion.christian`. Топ-документи — теологічні обговорення, питання про Christian практики, тлумачення Писання. Найбільш "чиста" і читабельна тема в моделі. 1060 із 1982 документів сoc.religion.christian мають її як домінантну.

---

### 2.2 LDA k=8 — Нотатки

| Topic | Top words | Назва | Якість |
|-------|-----------|-------|--------|
| 0 | atheism, atheists, god, atheist, religion, just, religious, don, believe, people | Атеїзм | GOOD |
| 1 | jesus, god, people, think, like, life, just, don, time, christ | Загальна релігія / поверхнева | NOISY |
| 2 | islam, book, islamic, muslim, muslims, qur, world, rushdie, wrote, private | Іслам / Рушді | GOOD |
| 3 | use, power, ground, circuit, wire, data, does, good, using | Електроніка (hardware) | GOOD |
| 4 | god, church, paul, christ, homosexuality, faith, sin, word, lord, christian | Церква / Christian ethics | GOOD |
| 5 | god, does, people, believe, say, don, think, true, question, evidence | Теїзм / аргументи про Бога | MODERATE |
| 6 | don, moral, know, people, mary, just, think, writes, morality, say | Мораль / дискурс | BAD |
| 7 | like, ve, don, know, want, time, just, make, number, use | Суто дискурсний шум | BAD |

k=8 розбиває атеїзм на: "атеїзм" (T0) + "теїзм/аргументи" (T5) + "мораль" (T6).  
Розбиває релігію: "ісламські дискусії" (T2) + "Christian ethics" (T4) + "загальна релігія" (T1).  
Electronics: тепер T3 читабельний (`circuit`, `wire`, `ground`).

---

### 2.3 LSA k=5 — Нотатки

| Component | Top words | Назва | Якість |
|-----------|-----------|-------|--------|
| 0 | god, don, people, think, just, know, does, like, say, believe | Корпус-загальний | BAD |
| 1 | god, thanks, use, chip, jesus, circuit, believe, mail, output, voltage | Змішаний (релігія + електроніка) | MIXED |
| 2 | bronx, queens, sank, manhattan, blew, beauchaine, bob, sea, stay | Конкретний thread (шум) | BAD |
| 3 | keith, jon, morality, writes, livesey, god, objective, jesus, moral | Username-driven (конкретні автори) | BAD |
| 4 | kent, alink, ksand, private, activities, cheers, net, wrote, jon | Username-driven (шум) | BAD |

LSA показав 2 добрих і 3 поганих компоненти з 5. Основна проблема — часті автори (keith, jon, kent, livesey, bob beauchaine) утворюють псевдо-теми замість змістовних тем.

**LSA topic-label alignment** — слабший за LDA:
- Topic 0 поглинає 1880 alt.atheism і 1910 soc.religion.christian — майже всі релігійні документи в одному компоненті
- sci.electronics (1190) домінує в Topic 1 (але разом із religious vocabulary)

---

## 3. Погані теми

### 3.1 Generic Discourse Topic (LDA k=5 Topic 1; LDA k=8 Topics 6, 7)

**Слова:** `think, people, don, just, like, know, time, writes, good`  
**Тип:** stop-word / style topic  
**Чому погана:** Відображає розмовний стиль Usenet постів 1990-х, спільний для ВСІХ трьох класів. Не є змістовною темою. Поглинає 894 alt.atheism + 600 soc.religion.christian документів.  
**Причина:** `stop_words='english'` не покриває дискурсні слова `think`, `know`, `writes`, `good`.  
**Що змінити:**
1. Додати `NEWSGROUP_EXTRA_STOPWORDS` до векторайзера (містить writes, think, know, say, just, etc.)
2. Підвищити `min_df` до 10 — слова, що зустрічаються у менш ніж 0.16% документів, мабуть рідкісні username-artifacts; слова з mid-range df ймовірно discourse words

---

### 3.2 Username-Driven Topics (LSA k=5 Topics 2, 3, 4)

**Слова:** `keith, jon, morality, livesey` | `kent, alink, ksand` | `bronx, queens, sank, beauchaine`  
**Тип:** template/style topic (специфічні автори або threads)  
**Чому погана:** LSA вловлює паттерн постингу конкретних активних користувачів (keith livesey, jon, bob beauchaine) замість тематичного змісту. `bronx/queens/sank` — рядки з конкретного cross-posted thread.  
**Причина:** В Usenet корпусах деякі автори надзвичайно активні і утворюють власні "теми". LSA чутливий до цього, LDA — менше.  
**Що змінити:**
1. Фільтрувати авторів: додати username токени до stop-words
2. min_df=10+ відфільтрує рідкісні proper nouns
3. Перейти на lemma_text для уніфікації word forms

---

### 3.3 Redundant Topics (LDA k=8 Topics 5 + 0)

**Слова:** T0=`atheism, atheists, god, atheist, religion` | T5=`god, does, people, believe, say, evidence`  
**Тип:** duplicate / split topic  
**Чому погана:** k=8 змушує модель розбити "атеїзм" на дві частини: T0 (категоріальний — слова-маркери `atheism`, `atheist`) і T5 (аргументаційний — `believe`, `evidence`, `true`). Це реальна підструктура, але при k=5 вона об'єднана в одну більш корисну тему.  
**Причина:** k надто великий для корпусу з 3 натуральними класами.  
**Що змінити:** k=3 як sanity check; k=5 як оптимальний баланс для цього корпусу.

---

## 4. Порівняння LSA vs LDA

| Критерій | LSA k=5 | LDA k=5 |
|---------|---------|---------|
| Читабельні теми | 1 з 5 | 3 з 5 |
| Поганих/шумних тем | 4 з 5 | 2 з 5 |
| Змішаних тем | 1 (електроніка+релігія) | 1 (ісламська підтема) |
| Дублікатів | Немає | Немає |
| Username artifacts | 3 теми | Немає |
| Alignment з класами | Слабкий (alt.ath + soc.rel → Topic 0) | Добрий (sci.el → T3: 93%) |
| Diversity score | 0.88 | 0.82 |

**Яка модель дала більш читабельні теми:** LDA k=5

**У якої моделі більше:**
- Шумних тем: LSA (4 із 5 проти 2 із 5 у LDA)
- Username-driven тем: тільки LSA
- Дублікатів: LDA k=8 (Topics 0+5; Topics 6+7)

**Яка модель корисніша для цього корпусу:**

LDA k=5 значно корисніший для 20 Newsgroups. LDA правильно ізолює `sci.electronics` (93% документів у Topic 3), виділяє `soc.religion.christian` у Topic 4 (53% + є ще ісламська підтема), і частково відокремлює `alt.atheism` (Topic 0). LSA — навпаки — першим компонентом поглинає майже всі релігійні документи обох класів, бо вони мають спільну теологічну лексику. LSA також схильний вловлювати патерни конкретних активних авторів замість тем. Для цього корпусу, де є 3 чітких класи, LDA з його ймовірнісною моделлю та Dirichlet priors краще справляється з розподілом документів по темах. LDA не потребує orthogonality між темами, тому може коректно представити перекриття між `alt.atheism` і `soc.religion.christian`.

---

## 5. Висновок

Topic modeling на 20 Newsgroups (3 класи) **частково успішний**:

**Що вийшло добре:**
- `sci.electronics` — чисто ізольований LDA (93% документів у Topic 3, k=5)
- `soc.religion.christian` — добре виділений LDA Topic 4 (jesus, church, christ, sin, paul)
- LDA k=8 додатково знайшов ісламську підтему в alt.atheism newsgroup — реальна підструктура
- LDA загалом значно кращий за LSA для цього корпусу

**Що не вийшло:**
- `alt.atheism` не ізольований чисто — велика частина постів іде в generic discourse Topic 1
- LSA вловлює username-driven patterns (keith, jon, kent) замість тем
- Generic discourse topic (Topic 1 у LDA, Topic 0 у LSA) поглинає значну частину корпусу
- k=8 надто великий — створює дублікати та розбиті теми

**Чи topic modeling корисний для цього корпусу?**  
Корисний для exploration і підтвердження структури. Для класифікації — supervised моделі (Labs 6–7) значно надійніші. Головне обмеження: `alt.atheism` і `soc.religion.christian` відрізняються *позицією*, а не *лексикою* — це невидимо для bag-of-words.
