# Dataset Card: 20 Newsgroups Classification (3 Classes)

## Назва проєкту
Класифікація текстових повідомлень з newsgroups за тематичними категоріями

## Задача (Тип A: Класифікація)

**Input:** Текст повідомлення з newsgroup дискусії  
**Output:** Категорія (клас) повідомлення

Класи:
- `alt.atheism` - дискусії про атеїзм та релігію
- `sci.electronics` - технічні питання про електроніку
- `soc.religion.christian` - християнська тематика

## Джерело даних

**Походження:** 20 Newsgroups Dataset  
**Тип:** Usenet newsgroup повідомлення з 1990-х років  
**Ліцензія:** Public Domain  
**Посилання:** https://www.kaggle.com/datasets/crawford/20-newsgroups/versions/1?resource=download

Дані були отримані у форматі text файлів, де кожне повідомлення містить:
- Заголовки (From, Subject, та інші)
- Тіло повідомлення

## Обсяг датасету

| Метрика | Значення |
|---------|----------|
| Загальна кількість текстів | 6,383 |
| Кількість класів | 3 |
| Тексти з темою (Subject) | 6,139 (96.2%) |

### Розподіл по класах:

| Клас | Кількість | Відсоток |
|------|-----------|----------|
| alt.atheism | 2,405 | 37.7% |
| sci.electronics | 1,975 | 30.9% |
| soc.religion.christian | 2,003 | 31.4% |

**Коефіцієнт дисбалансу:** 1.22:1 (відносно збалансовані класи)

## Статистика текстів

### Довжина в символах:
- Середнє: 1,844
- Медіана: 1,183
- Мінімум: 26
- Максимум: 71,503

### Довжина в словах:
- Середнє: 300
- Медіана: 185
- Мінімум: 2
- Максимум: 11,679

### Середня кількість слів по класах:
- alt.atheism: 327.3 слів
- sci.electronics: 190.6 слів
- soc.religion.christian: 374.1 слів

## Мова та домени

**Мова:** Англійська (EN)

**Домени/Тематики:**
1. **alt.atheism** - релігійні та філософські дискусії (атеїзм, критика релігії)
2. **sci.electronics** - технічні питання (схеми, компоненти, радіоелектроніка)
3. **soc.religion.christian** - християнська теологія та практики

**Стиль мови:** 
- Неформальний/напів-формальний
- Інтернет-дискусії 1990-х років
- Технічний жаргон (для sci.electronics)
- Релігійна термінологія (для релігійних груп)

## Очищення та нормалізація

### Lab 1 — Базова нормалізація (`data/processed.csv`):

1. **Парсинг структури:**
   - Розділення повідомлень (кожне починається з "From:")
   - Витягнення заголовків (Subject, From)
   - Відокремлення тіла повідомлення

2. **Базова нормалізація:**
   - Видалення зайвих пробілів та переносів рядків
   - Уніфікація апострофів (різні типи → стандартний ')
   - Заміна URL на `<URL>` (знайдено: 0)
   - Заміна email-адрес на `<EMAIL>` (знайдено: 5,306)
   - Заміна телефонів на `<PHONE>` (знайдено: 500)

3. **Виявлені проблеми:**
   - Точні дублікати: 17 (0.27%)
   - Дуже короткі тексти (<5 слів): 10 (0.16%)
   - Сміттєві тексти: 0 (0.00%)
   - Проблеми кодування: 0 (0.00%)

### Lab 2 — Повний детермінований пайплайн (`data/processed_v2/`):

Реалізовано у `src/preprocess.py`. Деталі: `docs/preprocess_policy.md`.

| Крок | Що робить | Модуль |
|---|---|---|
| `clean_text` | Видаляє заголовки newsgroup, цитування (`>`), підписи (`--`), HTML теги/entities, нормалізує пробіли | `clean_text()` |
| `normalize_text` | Нормалізує Unicode: лапки, апострофи, тире, гомогліфи (кирилиця→латиниця) | `normalize_text()` |
| `mask_pii` | Маскує URL→`<URL>`, email→`<EMAIL>`, телефони→`<PHONE>` | `mask_pii()` |
| `sentence_split` | NLTK Punkt (English) з захистом версій/чисел | `sentence_split()` |

**Зняті ризики після Lab 2:**
- Цитування (`>` рядки) — видалено
- HTML артефакти — декодовано
- Unicode варіанти апострофів/лапок/тире — уніфіковано
- Кириличні гомогліфи у англійському тексті — замінено на латиницю
- Блоки підписів — видалено

**Ризики, що залишились:**
- 17 точних дублікатів (дедублікація — рішення для етапу навчання моделі)
- Дуже довгі тексти (max ~11k слів) — не обрізано
- Неформальний правопис 1990-х — не виправляється (інженерна обробка, не LLM)

## Ризики та обмеження

### Виявлені ризики:

1. **Довжина текстів:**
   - Деякі тексти екстремально довгі (макс 11,679 слів)
   - Може знадобитися обрізання або спеціальна обробка

2. **Якість тексту:**
   - Newsgroup дискусії містять неформальну мову
   - Можливі друкарські помилки та скорочення
   - Цитування інших повідомлень створює шум

3. **Термінологія:**
   - Технічний жаргон в sci.electronics (назви компонентів, схеми)
   - Релігійна лексика може бути складною для моделей
   - Спеціалізовані терміни можуть потребувати окремої обробки

4. **Структурні особливості:**
   - Багато повідомлень містять цитування попередніх (> символ)
   - Заголовки email та адреси анонімізовані
   - Можливі discussion threads (ланцюжки відповідей)

5. **Темпоральність:**
   - Дані з 1990-х років
   - Можливі застарілі терміни та технології
   - Культурний контекст того часу

### Можливі упередження (bias):

- **Географічні:** Переважно користувачі з США та Європи
- **Демографічні:** Переважно чоловіча аудиторія (типово для Usenet 1990-х)
- **Тематичні:** Обмежені конкретними newsgroups
- **Технічні:** Користувачі з доступом до інтернету в 1990-х (tech-savvy)

## План наступного кроку (Lab 2)

### Що треба поліпшити в даних:

1. **Preprocessing:**
   - Видалення цитувань (рядки з `>`)
   - Видалення заголовків та підписів
   - Обробка спеціальних символів

2. **Feature Engineering:**
   - Реалізація TF-IDF векторизації
   - Експеримент з різними n-gram розмірами (unigrams, bigrams)
   - Можлива інтеграція subject як додаткової ознаки

3. **Text Normalization:**
   - Видалення стоп-слів (NLTK/spaCy)
   - Застосування стемінгу (Porter Stemmer) або лематизації
   - Приведення до нижнього регістру

4. **Data Balancing (якщо потрібно):**
   - Хоча класи відносно збалансовані (1.22:1), можна розглянути:
   - SMOTE для текстових даних (якщо performance погана для меншого класу)
   - Class weights в моделях

5. **Handling Long Texts:**
   - Встановити максимальну довжину (наприклад, 500-1000 слів)
   - Truncation vs summarization approach
   - Аналіз чи важлива довжина для класифікації

6. **Model Development:**
   - Baseline: Naive Bayes (Multinomial)
   - Logistic Regression
   - Support Vector Machines (SVM)
   - Cross-validation (5-fold)
   - Metrics: Accuracy, Precision, Recall, F1-score

7. **Analysis:**
   - Confusion matrix для розуміння помилок
   - Feature importance analysis
   - Error analysis (які тексти класифікуються неправильно)

## Splits & Leakage (Lab 5)

**Strategy:** Stratified random split 80/10/10, seed=42, duplicate-aware.

| Split | Size | alt.atheism | sci.electronics | soc.religion.christian |
|---|---|---|---|---|
| train | 5,132 | 37.7% | 30.8% | 31.5% |
| val | 614 | 36.8% | 32.7% | 30.5% |
| test | 637 | 38.5% | 30.5% | 31.1% |

**Leakage findings:**
- Exact duplicate train∩test = **0** (duplicate-aware split groups identical texts to one split)
- Near-duplicate (cosine ≥ 0.95) train∩test ≈ 35 pairs (on 500-doc sample)
- **CRITICAL: 3,944/6,383 docs (62%) contain `"Newsgroup: {class}"` in text** — direct label leak
- Thread/subject overlap: 87.7% of test subjects also appear in train
- No temporal split needed (no date column)

**Action required before fair model evaluation:** strip `Newsgroup:` / `document_id:` metadata footer from `text_v2`.

See: `docs/leakage_risk_report_lab5.md`, `docs/splits_manifest_lab5.json`.

## Classification Baseline (Lab 6)

**Baselines:**

| Baseline | Feature extraction | Input | Test Acc | Test Macro F1 |
|---|---|---|---|---|
| B1 (leaky) | TF-IDF word unigrams (1,1), 20k features | `text_v2` raw | ~0.97 | ~0.97 |
| B2 (honest) | TF-IDF word 1-2 grams (1,2), 20k features | `clean_text` (footer stripped) | ~0.79 | ~0.79 |

**Features:** Word n-grams computed on `text_v2` / `clean_text` from `data/processed_v2/processed_v2.csv`.
Both models use `LogisticRegression(C=1.0, solver='lbfgs')` via sklearn `Pipeline`.
See notebook `notebooks/lab6_tfidf_logistic_baseline.ipynb` for exact computed values.

**Key finding — template leakage:**
62% of documents in `text_v2` contain the literal string `"Newsgroup: {class}"` appended during data collection.
This acts as a direct label in the raw text, inflating Baseline 1 accuracy to ~97%.
After stripping this footer (`strip_footer()` in `src/classification_baseline.py`), accuracy drops by ~18 pp to ~79%, revealing the true difficulty of the task.

**Remaining risks after Lab 6:**

- **Class overlap (religion):** `alt.atheism` and `soc.religion.christian` share dense overlapping theological vocabulary. TF-IDF bag-of-words features cannot separate them reliably; this is the largest error source in Baseline 2.
- **Short texts:** Posts with fewer than ~200 characters lack sufficient TF-IDF signal; the model defaults to the majority class.
- **Group leakage:** 87.7% of test post subjects also appear in train (thread overlap from ЛР5). A subject/thread-aware split would give a more conservative generalisation estimate.
- **Quoted-text noise:** Although `clean_text` strips quote lines via Lab 2 preprocessing, some posts consist almost entirely of cited content, making the actual reply topic invisible to the classifier.

See: `docs/audit_summary_lab6.md`, `docs/confusion_matrix_lab6.png`, `tests/error_cases_lab6.jsonl`.

## Topic Modeling Findings (Lab 8)

### Large topics identified in the corpus

| Topic | Model | Quality | Key words |
|-------|-------|---------|-----------|
| Electronics Hardware | LDA k=5 | Good | circuit, voltage, current, resistor, capacitor |
| Christian Theology | LDA k=5 | Good | jesus, christ, church, bible, faith, prayer |
| Atheism Debate | LDA k=5 | Good | atheist, religion, argue, evidence, moral, logic |
| Generic Discourse | LDA k=5, LSA k=5 | Bad | think, know, say, people, just, make |
| Mixed Religion (LSA) | LSA k=5 comp.0 | Bad | god, religion, believe, faith, atheist, christian |

### Is the corpus homogeneous or mixed?

**Mixed in vocabulary, but structured by class.** The electronics class is cleanly isolated. The two religious classes (`alt.atheism`, `soc.religion.christian`) share dense theological vocabulary and are hard to separate by topic modeling alone — only their stance differs.

### Presence of noisy or template documents

- ~15% of topics contain generic Usenet discourse words (`think`, `know`, `say`, `people`) that are not captured by standard English stop-words
- Newsgroup metadata footers (`Newsgroup: {class}`) were stripped before topic modeling (label leakage artefact from Lab 5)
- PII placeholders (`<URL>`, `<EMAIL>`, `<PHONE>`) were excluded from topic vocabulary

### Is topic modeling useful for this corpus?

**Partially.** LDA k=5 successfully separates electronics from both religious classes. The alt.atheism / soc.religion.christian split is incomplete — both classes discuss the same subject (religion) from opposing stances, which bag-of-words cannot encode. Topic modeling is useful for unsupervised corpus exploration and preprocessing quality validation, but not for classification.

### Remaining risks

- Generic discourse topics (stop-word topic) pollute all models; extended stop-word list needed
- `alt.atheism` ↔ `soc.religion.christian` overlap requires stance-aware features beyond unigrams
- Very short documents (<50 words) contribute noise topics

See: `docs/audit_summary_lab8.md`, `docs/topic_notes_lab8.md`, `notebooks/lab8_topic_modeling_lsa_lda.ipynb`.


---

## Lab 9: Word Embeddings (Word2Vec / FastText)

### Is the corpus large enough for embeddings?

**Borderline.** 1.3M tokens / 18,613 vocab words (min_count=3) is sufficient for frequent words but too small for reliable embeddings of rare terms. Frequent domain words (voltage, church) produce good neighborhoods; rare words (omnipotent, scripture) require FastText subword support.

### Domain terms

The corpus has two well-separated domain clusters:
- **Electronics:** voltage, circuit, resistor, ground, transistor, capacitor → coherent neighborhoods
- **Religion:** church, resurrection, omnipotent, sin → coherent in both models

### Noisy text / spelling variation

Usenet text has significant morphological variability and spelling noise (believeth, scriptura, phototransistor, voltatge). FastText subword n-grams () handle this better than Word2Vec.

### FastText vs Word2Vec

**FastText is better** for this corpus. Key reasons:
1. Usenet morphological variability → subwords help (scripture/scriptures/scriptural)
2. Small corpus → rare words benefit from subword coverage
3. W2V competitive only for frequent, well-represented words

### Are embeddings useful overall?

**Partially.** Electronics and religious institution clusters are genuine and potentially useful for query expansion or vocabulary exploration. Generic discourse words (believe, think, know) and metadata-contaminated tokens (atheism W2V top=) produce noisy neighborhoods. Not recommended as primary classification features — TF-IDF SVM (Lab 7) remains stronger.

### Remaining risks

- Newsgroup header metadata partially retained in  contaminates some embeddings (atheism → alt)
- Corpus size limits W2V quality on rare theological/electronics vocabulary
- Generic Usenet discourse words cannot form meaningful embeddings in any model

See: , , .
---

---

## Lab 10: NER Pipeline + Hybrid Rules

### Baseline model and entity types

**Model**: spaCy `en_core_web_sm` v3.8.0  
**Standard labels**: PERSON, ORG, GPE, DATE, NORP, MONEY, CARDINAL, ORDINAL, WORK_OF_ART, …

Important entity types for this corpus:
- **ELECTRONICS_COMPONENT** (domain-specific, not in spaCy) — transistor, resistor, capacitor, diode, oscilloscope, …
- **PERSON** — religious figures (Jesus Christ, Pope John Paul II, Muhammad, …) and public intellectuals
- **DATE** — standard calendar dates + Usenet RFC-2822 header dates
- **ORG** — tech companies (Intel, Hewlett-Packard) and institutions (MIT Media Lab, American Atheists)
- **GPE** — locations (Poland, Rome, Arabia)

### Baseline failures on this corpus

1. **All electronics components missed** — `en_core_web_sm` has no electronics training data (10/11 gold entities missed)
2. **RFC-2822 Usenet dates** — "Thu, 15 Apr 1993 09:45:12 -0500" → only year fragment tagged
3. **Compound religious names** — "Holy Spirit" (nothing), "John the Baptist" (split), "Pope John Paul II" (boundary)

### Three hybrid rules added

| Rule | Label | Method | Gold set improvement |
|------|-------|--------|---------------------|
| 1 | `ELECTRONICS_COMPONENT` | PhraseMatcher, 26-term vocab | 0 → 10 correct |
| 2 | `PERSON` (religious) | PhraseMatcher, 22 names + longest-span dedup | 9 → 12 correct |
| 3 | `DATE` (Usenet) | Regex RFC-2822, asymmetric overlap check | 6 → 9 correct |

### Evaluation on 25-sentence gold set

| | Baseline | Hybrid |
|-|----------|--------|
| Precision | 0.462 | **0.678** |
| Recall | 0.453 | **0.755** |
| F1 | 0.457 | **0.714** |

### Remaining NER issues

- Boundary errors (10): article prefix ("The Council" vs "Council"), partial number overlap
- False positives (8): spaCy ORDINAL/CARDINAL/DATE noise on non-entity tokens
- Missed (2): "God" (too generic), "Pentecost" (religious calendar date)
- Type error (1): "Islam" → ORG instead of NORP

See: `docs/audit_summary_lab10.md`, `docs/ner_notes_lab10.md`, `notebooks/lab10_ner_pipeline_hybrid_rules.ipynb`.

---

**Дата створення:** 2025-02-15
**Версія:** 9.0 (оновлено Lab 10: 2026-05-29)
**Автор:** Kateryna
