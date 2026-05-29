# Audit Summary — Lab 8: Topic Modeling (LSA / LDA)

**Date:** 2026-05-28


## 1. Corpus Size After Filtering
- Documents used: **6192**
- min_words filter: 15
- Vectorizer min_df: 5, max_df: 0.9

## 2. Models Tested
- LSA: TfidfVectorizer (sublinear_tf=True) + TruncatedSVD (k=5, k=8)
- LDA: CountVectorizer + LatentDirichletAllocation (max_iter=30) (k=5, k=8)

## 3. k Values Tested
- k = 5
- k = 8

## 4. Best Topics (2–3 most useful)
- **Християнська теологія (LDA k=5, Topic 4)**: god, jesus, church, christ, sin, paul, faith, love, lord, man
  > Найчистіша тема: jesus, church, christ, paul, faith, lord. Топ-доки — soc.religion.christian. 1060/1982 документів домінантні тут.
- **Атеїзм / суперечки про Бога (LDA k=5, Topic 0)**: god, believe, does, atheism, evidence, say, don, belief, atheists, true
  > Аргументаційна лексика: atheism, evidence, belief, atheists. Топ-доки — alt.atheism overview і debate posts.
- **Іслам / підтема (LDA k=5, Topic 2)**: islam, religion, people, islamic, writes, book, jon, muslim, religious, world
  > Несподівана реальна підтема: alt.atheism активно обговорював іслам і Рушді.
- **Електроніка (LDA k=5, Topic 3)**: use, like, used, power, know, just, thanks, ground, don, good
  > sci.electronics ізольований на 93% (1760/1892 документів → Topic 3). Top words слабкі, але alignment відмінний.

## 5. Worst Topics (2–3 problematic)
- **Загальний дискурс Usenet (LDA k=5, Topic 1)**: think, people, don, just, like, know, time, bible, writes, good
  > Problem: Stop-word / style topic. Поглинає 894 alt.atheism + 600 soc.religion.christian. sklearn English stop-words не покривають Usenet discourse words.
- **Username-driven topics (LSA k=5, Topics 2-4)**: bronx, queens, beauchaine, keith, jon, livesey, kent, alink, ksand
  > Problem: LSA вловлює патерни активних авторів (Bob Beauchaine .sig, Keith Livesey, Kent/KSAND) замість тем. 3 із 5 LSA компонентів = username artifacts.
- **Mixed corpus-wide (LSA k=5, Component 0)**: god, don, people, think, just, know, does, like, say, believe
  > Problem: Перший SVD компонент absorbs global variance. Поглинає 1880 alt.atheism + 1910 soc.religion.christian.

## 6. What Caused Weak Topics
1. Generic discourse: sklearn English stop-words не покривають Usenet дискурсні слова (think, know, writes, good). 2. Username artifacts (LSA): активні автори утворюють псевдо-теми. 3. alt.atheism / soc.religion.christian: спільна теологічна лексика — stance невидима для BOW.

## 7. Best Model for This Corpus
LDA k=5 — найкраща модель. Правильно ізолює sci.electronics (93% alignment), виділяє Christian theology та atheism debate як окремі теми. LSA: 3/5 компонентів — username artifacts; Component 0 поглинає обидва релігійні класи.

## 8. Next Steps
- Додати NEWSGROUP_EXTRA_STOPWORDS: writes, think, know, say, just, good, time, people
- Спробувати k=3 (відповідає 3 ground-truth класам) — може дати найчистіші теми
- Використати lemma_text із processed_v3 для уніфікації word forms
- Додати bigrams для electronics: voltage_divider, power_supply, circuit_board
- Фільтрувати username tokens (keith, jon, kent, beauchaine) перед vectorizer
- Фільтрувати документи < 50 слів — короткі пости = noise topics
