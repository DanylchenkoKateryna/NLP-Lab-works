# Labeling Guidelines: 20 Newsgroups Classification

## Огляд

Цей документ описує правила класифікації текстових повідомлень з newsgroups у три категорії. Мета - забезпечити консистентну та точну розмітку даних для навчання класифікатора.

## Класи та їх визначення

### Клас 1: `alt.atheism`

**Визначення:** Дискусії про атеїзм, агностицизм, критику релігії, та філософські питання щодо існування божественного.

**Ключові теми:**
- Аргументи за/проти існування Бога
- Критика релігійних текстів та практик
- Філософські дискусії про мораль без релігії
- Секуляризм та світська етика
- Дискусії про відділення церкви від держави
- Атеїстичні організації та ресурси

**Типові ключові слова:**
- atheism, agnostic, secular, god, deity, belief
- bible criticism, religious dogma
- morality, ethics (в контексті без релігії)
- evolution (в контексті критики креаціонізму)

#### Приклади що ВХОДЯТЬ:

1. ✅ **Приклад 1:**
```
"The argument from design fails because complexity can arise naturally 
through evolution. There's no need to invoke a supernatural creator 
to explain the diversity of life."
```
*Чому входить:* Філософський аргумент проти існування Бога

2. ✅ **Приклад 2:**
```
"Does anyone have good resources on secular ethics? I'm looking for 
philosophical frameworks that don't rely on religious authority."
```
*Чому входить:* Пошук секулярних/атеїстичних ресурсів

3. ✅ **Приклад 3:**
```
"The Bible contradicts itself in Genesis 1 and Genesis 2 regarding the 
order of creation. How do believers reconcile these inconsistencies?"
```
*Чому входить:* Критика релігійних текстів

#### Приклади що НЕ ВХОДЯТЬ:

1. ❌ **Приклад 1:**
```
"What do you think about the new church building in downtown? The 
architecture is beautiful."
```
*Чому не входить:* Обговорення церкви без філософського/критичного контексту → `soc.religion.christian`

2. ❌ **Приклад 2:**
```
"I'm designing a circuit for a digital display. What resistor values 
should I use with LEDs?"
```
*Чому не входить:* Технічне питання про електроніку → `sci.electronics`

3. ❌ **Приклад 3:**
```
"Prayer has helped me through difficult times. I encourage everyone to 
seek God's guidance."
```
*Чому не входить:* Позитивне ставлення до релігії → `soc.religion.christian`

---

### Клас 2: `sci.electronics`

**Визначення:** Технічні дискусії про електроніку, схеми, компоненти, пристрої, та пов'язані інженерні питання.

**Ключові теми:**
- Електронні компоненти (резистори, конденсатори, транзистори, IC)
- Проектування схем та PCB
- Тестування та налагодження електроніки
- Джерела живлення та батареї
- Аудіо/відео електроніка
- Інструменти та обладнання (осцилоскопи, мультиметри)
- DIY електронні проекти

**Типові ключові слова:**
- circuit, component, resistor, capacitor, transistor
- voltage, current, LED, diode, IC, chip
- oscilloscope, multimeter, PCB
- solder, breadboard, schematic

#### Приклади що ВХОДЯТЬ:

1. ✅ **Приклад 1:**
```
"I'm building a 5V power supply. Should I use a 7805 voltage regulator 
or a switching regulator? What are the pros and cons?"
```
*Чому входить:* Технічне питання про електронні компоненти

2. ✅ **Приклад 2:**
```
"Where can I buy blinking LEDs besides Radio Shack? Does anyone sell 
blinking LEDs with variable flash rate?"
```
*Чому входить:* Питання про придбання електронних компонентів

3. ✅ **Приклад 3:**
```
"My circuit is oscillating at the wrong frequency. I've tried different 
capacitor values but can't get it stable. Any debugging tips?"
```
*Чому входить:* Налагодження електронної схеми

#### Приклади що НЕ ВХОДЯТЬ:

1. ❌ **Приклад 1:**
```
"The moral implications of artificial intelligence worry me. Are we 
playing God by creating intelligent machines?"
```
*Чому не входить:* Філософське питання, не технічне → `alt.atheism` (якщо про Бога) або інше

2. ❌ **Приклад 2:**
```
"Please pray for my father who is undergoing surgery tomorrow. We need 
all the support we can get."
```
*Чому не входить:* Релігійна тема → `soc.religion.christian`

3. ❌ **Приклад 3:**
```
"Does anyone know of good Bible study materials for beginners? I'm 
looking for something comprehensive."
```
*Чому не входить:* Релігійна освіта → `soc.religion.christian`

---

### Клас 3: `soc.religion.christian`

**Визначення:** Дискусії про християнство, включаючи теологію, практики, тлумачення Біблії, та християнське життя.

**Ключові теми:**
- Біблійні тексти та їх тлумачення
- Християнська теологія та доктрини
- Молитва та духовні практики
- Церковне життя та спільноти
- Християнська етика та мораль
- Євангелізм та місіонерство
- Різні християнські деномінації

**Типові ключові слова:**
- Jesus, Christ, God, Bible, Scripture, Gospel
- prayer, worship, faith, salvation, grace
- church, Christian, theology, verse
- believer, testimony, ministry

#### Приклади що ВХОДЯТЬ:

1. ✅ **Приклад 1:**
```
"What does John 3:16 really mean in the original Greek? I've heard 
different interpretations of 'believe' in this context."
```
*Чому входить:* Біблійна екзегеза та тлумачення

2. ✅ **Приклад 2:**
```
"Our church is organizing a prayer meeting for the community. All are 
welcome to join us in seeking God's guidance."
```
*Чому входить:* Християнська практика та спільнота

3. ✅ **Приклад 3:**
```
"The doctrine of the Trinity is central to Christian theology. How do 
we reconcile one God in three persons?"
```
*Чому входить:* Християнська теологічна дискусія

#### Приклади що НЕ ВХОДЯТЬ:

1. ❌ **Приклад 1:**
```
"The Bible has numerous scientific errors. For example, it describes 
a flat earth with a dome above it."
```
*Чому не входить:* Критика Біблії з атеїстичної позиції → `alt.atheism`

2. ❌ **Приклад 2:**
```
"I need help designing a digital timer circuit. What IC should I use 
for precise timing?"
```
*Чому не входить:* Технічне питання про електроніку → `sci.electronics`

3. ❌ **Приклад 3:**
```
"The cosmological argument for God's existence doesn't hold up under 
scrutiny. Who created God?"
```
*Чому не входить:* Філософська критика релігії → `alt.atheism`

---

## Граничні випадки (Edge Cases)

### Випадок 1: Міжрелігійні дискусії

**Ситуація:** Повідомлення обговорює як християнство, так і атеїзм.

**Правило:** Класифікуйте за **основним фокусом** повідомлення:
- Якщо захищає християнство → `soc.religion.christian`
- Якщо критикує релігію або пропагує атеїзм → `alt.atheism`
- Якщо нейтральне порівняння → дивіться на тон автора

**Приклад:**
```
"As a Christian, I find the atheist arguments about morality interesting 
but ultimately flawed. True morality comes from God, not human reasoning."
```
→ `soc.religion.christian` (автор захищає християнську позицію)

### Випадок 2: Технічні питання в релігійному контексті

**Ситуація:** Обговорення технології, але в контексті церкви.

**Правило:** 
- Якщо основна тема - технічна проблема → `sci.electronics`
- Якщо основна тема - використання в церкві → `soc.religion.christian`

**Приклад 1:**
```
"Our church needs a new PA system. What amplifier and speakers would 
you recommend for a 200-person sanctuary?"
```
→ `sci.electronics` (технічна консультація, церква - лише контекст)

**Приклад 2:**
```
"We're planning to livestream our Sunday services. Any advice on camera 
equipment and how to engage online viewers spiritually?"
```
→ `soc.religion.christian` (фокус на церковному служінні, технологія - засіб)

### Випадок 3: Цитування інших категорій

**Ситуація:** Автор цитує повідомлення з іншої категорії.

**Правило:** Класифікуйте за **основним контентом автора**, не цитатою.

**Приклад:**
```
> Someone wrote: "The Bible is full of contradictions"

I disagree. What seem like contradictions are often complementary 
perspectives. Let me explain the Genesis creation accounts...
```
→ `soc.religion.christian` (відповідь захищає Біблію)

### Випадок 4: Мультитематичні повідомлення

**Ситуація:** Повідомлення торкається кількох тем.

**Правило:** Визначте **домінуючу тему** (більше 60% контенту).

**Приклад:**
```
"Quick question about soldering SMD components - what tip size works 
best? Also, does anyone know when the next prayer meeting is?"
```
→ `sci.electronics` (основна частина про електроніку, релігія - побічна)

---

## Складні випадки та рекомендації

### Іслам та інші релігії

**Питання:** Як класифікувати дискусії про іслам або інші релігії?

**Відповідь:**
- Якщо з **християнської перспективи** (порівняння, євангелізація) → `soc.religion.christian`
- Якщо **критика релігії** загалом → `alt.atheism`
- Якщо суто про іслам без християнського контексту → може не підходити жоден клас (примітка для аналізу)

### Філософія та етика

**Питання:** Філософські дискусії можуть бути в кількох категоріях.

**Відповідь:**
- Філософія **релігії** (аргументи за/проти Бога) → `alt.atheism`
- **Християнська** етика/філософія → `soc.religion.christian`
- Секулярна філософія → `alt.atheism`

### Наука vs Релігія

**Питання:** Дискусії про еволюцію, Великий вибух, тощо.

**Відповідь:**
- Наука **проти** креаціонізму → `alt.atheism`
- Захист **креаціонізму** або інтелігентного дизайну → `soc.religion.christian`
- Чиста наука без релігійного контексту → не підходить

---

## Контрольний список для класифікації

При класифікації тексту задайте собі ці питання:

1. ✅ **Основна тема:**
   - Про що в основному це повідомлення?
   - Який відсоток контенту присвячений кожній темі?

2. ✅ **Позиція автора:**
   - Яку позицію займає автор?
   - Чи підтримує автор релігію чи критикує?

3. ✅ **Ключові слова:**
   - Які технічні терміни присутні?
   - Яка специфічна лексика використовується?

4. ✅ **Контекст:**
   - Чому автор пише це повідомлення?
   - Яку допомогу або дискусію шукає автор?

5. ✅ **Тон:**
   - Технічний/науковий?
   - Філософський/аргументативний?
   - Духовний/молитовний?

---

## Якість розмітки

### Метрики якості:
- **Консистентність:** Однакові тексти отримують однакові мітки
- **Точність:** Мітка відповідає змісту
- **Повнота:** Кожен текст має мітку

### Що робити при невпевненості:
1. Перечитайте текст повністю
2. Перевірте ключові слова та контекст
3. Порівняйте з прикладами вище
4. Якщо все ще невпевнені - позначте для перегляду
5. Консультуйтеся з колегами при складних випадках

---

**Версія:** 1.0  
**Дата:** 2025-02-15  
**Автор:** [Ваше ім'я]
