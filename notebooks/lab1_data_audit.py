import pandas as pd
import numpy as np
import re
from collections import Counter
import os

os.makedirs('data', exist_ok=True)
os.makedirs('docs', exist_ok=True)
os.makedirs('notebooks', exist_ok=True)

print("Завантаження даних з файлів...")
print("-"*80)

def parse_newsgroup_file(filepath, category):
    """Парсинг файлу newsgroup у окремі повідомлення"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    messages = re.split(r'\n(?=From: )', content)
    
    parsed_messages = []
    for msg in messages:
        if not msg.strip():
            continue
            
        lines = msg.split('\n')
        
        subject = ""
        from_field = ""
        body_start = 0
        
        for i, line in enumerate(lines):
            if line.startswith('Subject:'):
                subject = line.replace('Subject:', '').strip()
            elif line.startswith('From:'):
                from_field = line.replace('From:', '').strip()
            elif line.strip() == '' and i > 0:
                body_start = i + 1
                break
        
        body = '\n'.join(lines[body_start:]).strip()
        
        if body:
            parsed_messages.append({
                'category': category,
                'subject': subject,
                'from': from_field,
                'text': body
            })
    
    return parsed_messages

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

categories_files = {
    'alt.atheism': os.path.join(BASE_DIR, 'uploads', 'alt.atheism.txt'),
    'sci.electronics': os.path.join(BASE_DIR, 'uploads', 'sci.electronics.txt'),
    'soc.religion.christian': os.path.join(BASE_DIR, 'uploads', 'soc.religion.christian.txt')
}

all_messages = []
for category, filepath in categories_files.items():
    messages = parse_newsgroup_file(filepath, category)
    all_messages.extend(messages)

df_raw = pd.DataFrame(all_messages)
df_raw['id'] = range(len(df_raw))

category_to_id = {cat: i for i, cat in enumerate(sorted(categories_files.keys()))}
df_raw['label_id'] = df_raw['category'].map(category_to_id)

df_raw = df_raw.sample(frac=1, random_state=42).reset_index(drop=True)
df_raw['id'] = range(len(df_raw))

df_raw[['id', 'text', 'subject', 'from', 'category', 'label_id']].to_csv(
    'data/raw.csv', 
    index=False
)
print(f"✓ Збережено raw.csv з {len(df_raw)} записами")
print()

print("Перші 10 прикладів:")
print("-"*80)
for i in range(10):
    text_preview = df_raw.iloc[i]['text'][:120].replace('\n', ' ')
    print(f"[{i}] {df_raw.iloc[i]['category']}")
    print(f"    Subject: {df_raw.iloc[i]['subject'][:60]}")
    print(f"    Text: {text_preview}...")
    print()

print("\n" + "="*80)
print("Статистика")
print("="*80)
print()

total_texts = len(df_raw)
print(f"Загальна кількість текстів: {total_texts}")
print()

df_raw['char_length'] = df_raw['text'].str.len()
df_raw['word_count'] = df_raw['text'].str.split().str.len()

print("Статистика довжини текстів:")
print("-"*80)
print(f"Символи:")
print(f"  Середнє: {df_raw['char_length'].mean():.0f}")
print(f"  Медіана: {df_raw['char_length'].median():.0f}")
print(f"  Мінімум: {df_raw['char_length'].min()}")
print(f"  Максимум: {df_raw['char_length'].max()}")
print()
print(f"Слова:")
print(f"  Середнє: {df_raw['word_count'].mean():.0f}")
print(f"  Медіана: {df_raw['word_count'].median():.0f}")
print(f"  Мінімум: {df_raw['word_count'].min()}")
print(f"  Максимум: {df_raw['word_count'].max()}")
print()

print("Розподіл класів:")
print("-"*80)
class_counts = df_raw['category'].value_counts().sort_index()
for label, count in class_counts.items():
    percentage = (count / total_texts) * 100
    bar = '█' * int(percentage / 2)
    print(f"{label:30s}: {count:4d} ({percentage:5.1f}%) {bar}")
print()

print("="*80)
print("Базова нормалізація")
print("="*80)
print()

def normalize_text(text):
    """Застосування базової нормалізації до тексту"""
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    text = text.replace('\u2019', "'")
    text = text.replace('\u2018', "'")
    text = text.replace('`', "'")
    text = text.replace('´', "'")
    
    text = re.sub(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', 
        '<URL>', 
        text
    )
    
    text = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
        '<EMAIL>', 
        text
    )
    
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '<PHONE>', text)
    text = re.sub(r'\(\d{3}\)\s*\d{3}[-.]?\d{4}', '<PHONE>', text)
    
    return text

print("Застосування правил нормалізації:")
print()

df_processed = df_raw.copy()
df_processed['text_normalized'] = df_processed['text'].apply(normalize_text)

url_count = df_processed['text_normalized'].str.contains('<URL>', regex=False).sum()
email_count = df_processed['text_normalized'].str.contains('<EMAIL>', regex=False).sum()
phone_count = df_processed['text_normalized'].str.contains('<PHONE>', regex=False).sum()

print(f"✓ Нормалізовано {len(df_processed)} текстів")
print(f"  - Знайдено {url_count} URL")
print(f"  - Знайдено {email_count} email-адрес")
print(f"  - Знайдено {phone_count} телефонів")
print()

if email_count > 0:
    print("Приклад нормалізації:")
    print("-"*80)
    sample_idx = df_processed[df_processed['text_normalized'].str.contains('<EMAIL>', regex=False)].index[0]
    print("До нормалізації:")
    print(df_processed.loc[sample_idx, 'text'][:300])
    print("\nПісля нормалізації:")
    print(df_processed.loc[sample_idx, 'text_normalized'][:300])
    print()

print("="*80)
print("Перевірки якості")
print("="*80)
print()

print("1. Перевірка на точні дублікати...")
duplicates = df_processed['text_normalized'].duplicated()
dup_count = duplicates.sum()
dup_percentage = (dup_count / total_texts) * 100
print(f"   Точні дублікати: {dup_count} ({dup_percentage:.2f}%)")

if dup_count > 0:
    dup_text = df_processed[duplicates]['text_normalized'].iloc[0][:150]
    print(f"   Приклад дублікату: {dup_text}...")
print()

print("2. Перевірка на порожні/дуже короткі тексти (< 5 слів)...")
short_texts = df_processed['word_count'] < 5
short_count = short_texts.sum()
short_percentage = (short_count / total_texts) * 100
print(f"   Дуже короткі тексти: {short_count} ({short_percentage:.2f}%)")

if short_count > 0:
    print(f"   Приклади коротких текстів:")
    for idx in df_processed[short_texts].head(3).index:
        cat = df_processed.loc[idx, 'category']
        text = df_processed.loc[idx, 'text_normalized'][:100]
        print(f"     - [{cat}] {text}")
print()

print("3. Перевірка на сміттєві тексти (тільки цифри/символи)...")

def is_garbage(text):
    if not text or len(text.strip()) == 0:
        return True
    
    clean = re.sub(r'[\s\.,;:!?\-\(\)\[\]<>"\'/]', '', text)
    if len(clean) == 0:
        return True
    
    alpha_ratio = sum(c.isalpha() for c in clean) / len(clean) if len(clean) > 0 else 0
    return alpha_ratio < 0.3

garbage = df_processed['text_normalized'].apply(is_garbage)
garbage_count = garbage.sum()
garbage_percentage = (garbage_count / total_texts) * 100
print(f"   Сміттєві тексти: {garbage_count} ({garbage_percentage:.2f}%)")

if garbage_count > 0:
    print(f"   Приклади сміттєвих текстів:")
    for idx in df_processed[garbage].head(3).index:
        cat = df_processed.loc[idx, 'category']
        text = df_processed.loc[idx, 'text_normalized'][:100]
        print(f"     - [{cat}] '{text}'")
print()

print("4. Перевірка балансу класів...")
class_sizes = df_processed['category'].value_counts()
min_class_size = class_sizes.min()
max_class_size = class_sizes.max()
imbalance_ratio = max_class_size / min_class_size

print(f"   Найменший клас: {min_class_size} зразків ({class_sizes.idxmin()})")
print(f"   Найбільший клас: {max_class_size} зразків ({class_sizes.idxmax()})")
print(f"   Коефіцієнт дисбалансу: {imbalance_ratio:.2f}:1")

if imbalance_ratio > 2:
    print(f"   Попередження: Виявлено помірний дисбаланс класів")
elif imbalance_ratio > 1.5:
    print(f"   Попередження: Невеликий дисбаланс класів")
else:
    print(f"   Класи відносно збалансовані")
print()

print("="*80)
print("Збереження оброблених даних")
print("="*80)
print()

df_processed[['id', 'text_normalized', 'label_id', 'category', 'subject', 'char_length', 'word_count']].to_csv(
    'data/processed.csv', 
    index=False
)
print("Збережено processed.csv")

labels_df = pd.DataFrame({
    'label_id': [category_to_id[cat] for cat in sorted(category_to_id.keys())],
    'label_name': sorted(category_to_id.keys()),
    'count': [class_counts[cat] for cat in sorted(category_to_id.keys())],
    'percentage': [(class_counts[cat] / total_texts * 100) for cat in sorted(category_to_id.keys())]
})
labels_df.to_csv('data/labels.csv', index=False)
print("Збережено labels.csv")
print()

print("="*80)
print("ВИСНОВКИ")
print("="*80)
print()

print("Підсумок про датасет 20newsgroups (3 класи):")
print()

print("1. Огляд датасету:")
print(f"   - Зібрано {total_texts} текстових документів з 3 категорій newsgroups")
print(f"   - Категорії охоплюють різні теми: релігія/атеїзм, електроніка, християнство")
print(f"   - Дані англійською мовою з Usenet newsgroup дискусій")
print(f"   - Середня довжина тексту: {df_raw['word_count'].mean():.0f} слів")
print()

print("2. Якість даних:")
print(f"   - Низький рівень дублікатів ({dup_percentage:.1f}%) вказує на хорошу різноманітність")
print(f"   - Мінімальна кількість сміттєвих/порожніх текстів ({garbage_count + short_count} всього)")
print(f"   - Середня довжина тексту {df_raw['word_count'].mean():.0f} слів підходить для класифікації")
print(f"   - Класи {'збалансовані' if imbalance_ratio < 1.5 else 'помірно дисбалансовані'} (коефіцієнт: {imbalance_ratio:.1f}:1)")
print()

print("3. Виявлені ризики:")
risks = []
if df_raw['word_count'].max() > 1000:
    risks.append(f"   - Деякі тексти дуже довгі (макс {df_raw['word_count'].max()} слів)")
risks.append("   - Newsgroup дискусії можуть містити неформальну мову та друкарські помилки")
risks.append("   - Специфічна термінологія (технічні терміни, релігійна лексика) може ускладнити роботу моделей")
if imbalance_ratio > 1.5:
    risks.append(f"   - Помірний дисбаланс класів може вплинути на якість для меншого класу")
risks.append("   - Цитування можуть створювати шум у даних")

for risk in risks:
    print(risk)
print()

print("4. Застосоване попереднє оброблення:")
print("   - Видалено зайві пробіли та нормалізовано переноси рядків")
print("   - Уніфіковано апострофи")
print(f"   - Анонімізовано URL ({url_count}), email ({email_count}), телефони ({phone_count})")
print()

print("5. Наступні кроки для Lab 2:")
print("   - Реалізувати видобування ознак (TF-IDF або word embeddings)")
print("   - Застосувати видалення стоп-слів та стемінг/лематизацію")
if imbalance_ratio > 1.5:
    print("   - Розглянути техніки балансування (oversampling/undersampling)")
if df_raw['word_count'].max() > 1000:
    print("   - Експериментувати з обробкою довгих текстів (обрізання/резюмування)")
print("   - Побудувати baseline класифікатори (Naive Bayes, Logistic Regression, SVM)")
print("   - Провести крос-валідацію та аналіз помилок")
print()

print(f"Згенеровані файли:")
print(f"  data/raw.csv ({len(df_raw)} записів)")
print(f"  data/processed.csv ({len(df_processed)} записів)")
print(f"  data/labels.csv ({len(labels_df)} класів)")
print()
