#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta

# ─── загрузка данных ───────────────────────────────────────────────────────────
files = ['2.json', '1.json', 'result.json']
all_messages = []

for fname in files:
    with open(fname, 'r', encoding='utf-8') as f:
        data = json.load(f)
    msgs = data.get('messages', [])
    all_messages.extend(msgs)
    print(f"  {fname}: {len(msgs):,} сообщений")

all_messages.sort(key=lambda m: m.get('date_unixtime', '0'))
print(f"\n  ИТОГО: {len(all_messages):,} сообщений\n")

# ─── вспомогательные функции ──────────────────────────────────────────────────
AUTHOR_ID = 'channel1536853034'

def get_text(m):
    t = m.get('text', '')
    if isinstance(t, list):
        return ''.join(p['text'] if isinstance(p, dict) else p for p in t)
    return t or ''

def parse_date(m):
    try:
        return datetime.fromisoformat(m['date'])
    except:
        return None

def is_author(m):
    return m.get('from_id') == AUTHOR_ID

def is_comment(m):
    return bool(m.get('reply_to_message_id'))

STOPWORDS = {
    'и','в','на','с','по','за','к','из','от','до','не','но','а','что','это','как',
    'так','уже','ну','же','то','бы','да','мне','меня','мы','я','ты','он','она',
    'они','вы','у','о','об','про','при','без','под','над','между','через',
    'или','если','когда','чтобы','всё','всё','все','его','её','их','мой','моя',
    'моё','наш','ваш','со','во','ещё','раз','там','тут','вот','тоже','только',
    'ещё','нет','то','лет','было','будет','были','был','была','есть','нам',
    'вам','им','её','его','ей','ему','нас','вас','них','ним','них','себя','себе',
    'свой','своя','своё','свои','который','которая','которое','которые','где',
    'куда','откуда','потому','поэтому','чем','кто','что','какой','какая',
    'какое','какие','сам','сама','само','сами','один','одна','одно','одни',
    'два','три','ещё','уж','ли','же','бы','вы','мы','их','ему',
}

def tokenize(text):
    return [w.lower() for w in re.findall(r'[а-яёa-z]+', text, re.IGNORECASE) if len(w) > 2 and w.lower() not in STOPWORDS]

def extract_emojis(text):
    return re.findall(r'[\U0001F300-\U0001FFFF\U00002600-\U000027FF]', text)

# ─── БЛОК 1: Общая статистика ─────────────────────────────────────────────────
print("=" * 60)
print("БЛОК 1 — ОБЩАЯ СТАТИСТИКА")
print("=" * 60)

author_posts = [m for m in all_messages if is_author(m) and not is_comment(m)]
comments = [m for m in all_messages if is_comment(m)]
author_comments = [m for m in comments if is_author(m)]
other_comments = [m for m in comments if not is_author(m)]

print(f"\n📊 Постов автора (не ответы): {len(author_posts):,}")
print(f"💬 Комментариев всего: {len(comments):,}")
print(f"   из них от автора: {len(author_comments):,}")
print(f"   от других: {len(other_comments):,}")

dates_all = [parse_date(m) for m in all_messages if parse_date(m)]
dates_posts = [parse_date(m) for m in author_posts if parse_date(m)]

print(f"\n📅 Первое сообщение: {min(dates_all).strftime('%d.%m.%Y %H:%M')}")
print(f"📅 Последнее сообщение: {max(dates_all).strftime('%d.%m.%Y %H:%M')}")
total_days = (max(dates_all) - min(dates_all)).days
total_months = total_days / 30.44
total_weeks = total_days / 7
print(f"   Период: {total_days} дней (~{total_months:.1f} месяцев)")

if total_months > 0:
    print(f"\n📈 Среднее постов в месяц: {len(author_posts)/total_months:.1f}")
    print(f"📈 Среднее постов в неделю: {len(author_posts)/total_weeks:.1f}")
    print(f"📈 Среднее сообщений всего в день: {len(all_messages)/total_days:.1f}")

# Активность по месяцам
month_counts = Counter(d.strftime('%Y-%m') for d in dates_all)
busiest_month = month_counts.most_common(1)[0]
quietest_month = month_counts.most_common()[-1]
print(f"\n🔥 Самый активный месяц: {busiest_month[0]} ({busiest_month[1]:,} сообщений)")
print(f"😴 Самый тихий месяц: {quietest_month[0]} ({quietest_month[1]:,} сообщений)")

# ─── БЛОК 2: Рейтинг участников ───────────────────────────────────────────────
print("\n" + "=" * 60)
print("БЛОК 2 — РЕЙТИНГ УЧАСТНИКОВ")
print("=" * 60)

# Все участники (кроме автора канала в роли постера)
all_commenters = [(m.get('from', 'Unknown'), m.get('from_id', '')) for m in all_messages if m.get('from_id') != AUTHOR_ID and m.get('from')]
commenter_counter = Counter(name for name, _ in all_commenters)

print(f"\n🏆 Топ комментаторов по количеству сообщений:")
for i, (name, cnt) in enumerate(commenter_counter.most_common(30), 1):
    print(f"  {i:2}. {name}: {cnt:,}")

# Средняя длина сообщения
user_lengths = defaultdict(list)
for m in all_messages:
    name = m.get('from', 'Unknown')
    text = get_text(m)
    if text and m.get('from_id') != AUTHOR_ID:
        user_lengths[name].append(len(text))

print(f"\n📝 Средняя длина сообщения (графоманский рейтинг):")
avg_lengths = {name: sum(lens)/len(lens) for name, lens in user_lengths.items() if len(lens) >= 5}
for i, (name, avg) in enumerate(sorted(avg_lengths.items(), key=lambda x: -x[1])[:15], 1):
    count = len(user_lengths[name])
    print(f"  {i:2}. {name}: {avg:.0f} символов (сообщений: {count})")

# Кто чаще пишет первый комментарий
first_commenters = []
post_ids = {m['id'] for m in all_messages if is_author(m) and not is_comment(m)}
comments_by_reply = defaultdict(list)
for m in all_messages:
    if is_comment(m) and not is_author(m):
        rid = m.get('reply_to_message_id')
        if rid in post_ids:
            comments_by_reply[rid].append(m)

for rid, cmts in comments_by_reply.items():
    cmts_sorted = sorted(cmts, key=lambda m: m.get('date_unixtime', '0'))
    if cmts_sorted:
        first_commenters.append(cmts_sorted[0].get('from', 'Unknown'))

first_commenter_counter = Counter(first_commenters)
print(f"\n⚡ Кто чаще всего пишет первый комментарий под постом:")
for i, (name, cnt) in enumerate(first_commenter_counter.most_common(10), 1):
    print(f"  {i:2}. {name}: {cnt} раз")

# ─── БЛОК 3: Активность по времени ───────────────────────────────────────────
print("\n" + "=" * 60)
print("БЛОК 3 — АКТИВНОСТЬ ПО ВРЕМЕНИ")
print("=" * 60)

DAYS_RU = ['Понедельник','Вторник','Среда','Четверг','Пятница','Суббота','Воскресенье']
day_counts = Counter(d.weekday() for d in dates_all)
print(f"\n📅 Посты по дням недели:")
for day_idx in range(7):
    cnt = day_counts.get(day_idx, 0)
    bar = '█' * (cnt // max(1, max(day_counts.values()) // 20))
    print(f"  {DAYS_RU[day_idx]:12}: {cnt:5,}  {bar}")

hour_counts = Counter(d.hour for d in dates_all)
print(f"\n🕐 Распределение по часам суток:")
for h in range(24):
    cnt = hour_counts.get(h, 0)
    bar = '█' * (cnt // max(1, max(hour_counts.values()) // 30))
    print(f"  {h:02d}:00  {cnt:5,}  {bar}")

peak_hour = max(hour_counts.items(), key=lambda x: x[1])
night_msgs = sum(hour_counts.get(h, 0) for h in range(0, 6))
day_msgs = sum(hour_counts.get(h, 0) for h in range(6, 22))
print(f"\n  Пиковый час: {peak_hour[0]:02d}:00 ({peak_hour[1]:,} сообщений)")
print(f"  Ночных (00-06): {night_msgs:,} | Дневных (06-22): {day_msgs:,}")
print(f"  Режим: {'🦉 Сова' if peak_hour[0] >= 21 or peak_hour[0] <= 4 else '🐦 Жаворонок' if peak_hour[0] <= 10 else '🌞 Дневной человек'}")

# Среднее время до первого комментария
response_times = []
post_time_map = {m['id']: parse_date(m) for m in all_messages if is_author(m) and not is_comment(m) and parse_date(m)}

for rid, cmts in comments_by_reply.items():
    if rid in post_time_map:
        post_dt = post_time_map[rid]
        cmts_sorted = sorted(cmts, key=lambda m: m.get('date_unixtime', '0'))
        first_cmt_dt = parse_date(cmts_sorted[0])
        if first_cmt_dt and first_cmt_dt > post_dt:
            diff = (first_cmt_dt - post_dt).total_seconds()
            if diff < 86400:  # не больше суток
                response_times.append(diff)

if response_times:
    avg_response = sum(response_times) / len(response_times)
    median_response = sorted(response_times)[len(response_times)//2]
    print(f"\n⏱ Среднее время до первого комментария: {avg_response/60:.1f} мин")
    print(f"⏱ Медианное время до первого комментария: {median_response/60:.1f} мин")

# ─── БЛОК 4: Анализ текста ────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("БЛОК 4 — АНАЛИЗ ТЕКСТА")
print("=" * 60)

all_texts = [get_text(m) for m in all_messages]
author_texts = [get_text(m) for m in all_messages if is_author(m)]

# Топ слов
all_words = []
for text in all_texts:
    all_words.extend(tokenize(text))

word_counter = Counter(all_words)
print(f"\n📖 Топ-20 самых частых слов:")
for i, (word, cnt) in enumerate(word_counter.most_common(20), 1):
    print(f"  {i:2}. {word}: {cnt:,}")

# Биграммы и триграммы
bigrams = []
trigrams = []
for text in all_texts:
    tokens = tokenize(text)
    bigrams.extend(' '.join(tokens[i:i+2]) for i in range(len(tokens)-1))
    trigrams.extend(' '.join(tokens[i:i+3]) for i in range(len(tokens)-2))

print(f"\n🔗 Топ-10 биграмм:")
for i, (phrase, cnt) in enumerate(Counter(bigrams).most_common(10), 1):
    print(f"  {i:2}. «{phrase}»: {cnt:,}")

print(f"\n🔗 Топ-10 триграмм:")
for i, (phrase, cnt) in enumerate(Counter(trigrams).most_common(10), 1):
    print(f"  {i:2}. «{phrase}»: {cnt:,}")

# Самое длинное сообщение
msgs_with_text = [(m, get_text(m)) for m in all_messages if get_text(m)]
longest = max(msgs_with_text, key=lambda x: len(x[1]))
print(f"\n📜 Самое длинное сообщение:")
print(f"   Автор: {longest[0].get('from', 'Unknown')}")
print(f"   Дата: {longest[0].get('date', '')}")
print(f"   Длина: {len(longest[1])} символов")
print(f"   Начало: {longest[1][:200]}...")

# Самое короткое осмысленное
short_msgs = [(m, t) for m, t in msgs_with_text if len(t) >= 2 and re.search(r'[а-яёa-z]', t, re.I)]
shortest = min(short_msgs, key=lambda x: len(x[1]))
print(f"\n✂️ Самое короткое осмысленное сообщение:")
print(f"   Автор: {shortest[0].get('from', 'Unknown')}, дата: {shortest[0].get('date', '')}")
print(f"   Текст: «{shortest[1]}»")

# Вопросительные и восклицательные
q_count = sum(1 for t in all_texts if '?' in t)
excl_count = sum(1 for t in all_texts if '!' in t)
print(f"\n❓ Вопросительных сообщений: {q_count:,}")
print(f"❗ Восклицательных сообщений: {excl_count:,}")
print(f"   Уровень драматизма: {(excl_count + q_count) / max(1, len(msgs_with_text)) * 100:.1f}%")

# Эмодзи автора
author_emojis = []
for text in author_texts:
    author_emojis.extend(extract_emojis(text))
emoji_counter = Counter(author_emojis)
print(f"\n😄 Любимые эмодзи автора:")
for emoji, cnt in emoji_counter.most_common(15):
    print(f"   {emoji}: {cnt}")

# Знаки препинания автора
punct_counter = Counter()
for text in author_texts:
    for ch in text:
        if ch in '.,!?;:…—–-()':
            punct_counter[ch] += 1
print(f"\n✍️ Любимые знаки препинания автора:")
for char, cnt in punct_counter.most_common(10):
    print(f"   «{char}»: {cnt:,}")

# ─── БЛОК 5: Реакции и вовлечённость ─────────────────────────────────────────
print("\n" + "=" * 60)
print("БЛОК 5 — РЕАКЦИИ И ВОВЛЕЧЁННОСТЬ")
print("=" * 60)

# Реакции
msgs_with_reactions = [(m, sum(r.get('count', 0) for r in m.get('reactions', []))) for m in all_messages if m.get('reactions')]
msgs_with_reactions.sort(key=lambda x: -x[1])

if msgs_with_reactions:
    print(f"\n🏆 Топ-5 постов по реакциям:")
    for i, (m, cnt) in enumerate(msgs_with_reactions[:5], 1):
        text = get_text(m)[:100] or '[медиа]'
        print(f"  {i}. {cnt} реакций | {m.get('date','')} | {text}")

# Посты с максимумом комментариев
reply_count = Counter()
for m in all_messages:
    rid = m.get('reply_to_message_id')
    if rid:
        reply_count[rid] += 1

post_map = {m['id']: m for m in all_messages}
print(f"\n💬 Топ-5 самых обсуждаемых постов:")
for i, (post_id, cnt) in enumerate(reply_count.most_common(5), 1):
    m = post_map.get(post_id)
    if m:
        text = get_text(m)[:100] or '[медиа]'
        print(f"  {i}. {cnt} комментариев | {m.get('date','')} | {text}")

# Провальные посты
author_post_ids = {m['id'] for m in author_posts}
posts_no_reactions = [m for m in author_posts if not m.get('reactions') and m['id'] not in reply_count]
print(f"\n💀 Постов без реакций и комментариев: {len(posts_no_reactions):,} из {len(author_posts):,}")

# Общий рейтинг эмодзи реакций
all_reaction_emojis = []
for m in all_messages:
    for r in m.get('reactions', []):
        emoji = r.get('emoji', '')
        count = r.get('count', 1)
        all_reaction_emojis.extend([emoji] * count)

reaction_counter = Counter(all_reaction_emojis)
print(f"\n🎭 Топ эмодзи-реакций:")
for emoji, cnt in reaction_counter.most_common(15):
    print(f"   {emoji}: {cnt:,}")

# ─── БЛОК 6: Забавные рекорды ─────────────────────────────────────────────────
print("\n" + "=" * 60)
print("БЛОК 6 — ЗАБАВНЫЕ РЕКОРДЫ")
print("=" * 60)

# Самый длинный тред
print(f"\n🧵 Самый длинный тред (топ-5):")
for i, (post_id, cnt) in enumerate(reply_count.most_common(5), 1):
    m = post_map.get(post_id)
    if m:
        text = get_text(m)[:80] or '[медиа]'
        print(f"  {i}. {cnt} ответов | {m.get('date','')} | {text}")

# Самый быстрый комментарий
fastest = []
for rid, cmts in comments_by_reply.items():
    if rid in post_time_map:
        post_dt = post_time_map[rid]
        for cmt in cmts:
            cmt_dt = parse_date(cmt)
            if cmt_dt and cmt_dt >= post_dt:
                diff = (cmt_dt - post_dt).total_seconds()
                fastest.append((diff, cmt, post_map.get(rid)))

fastest.sort(key=lambda x: x[0])
print(f"\n⚡ Топ-5 самых быстрых комментариев:")
for i, (diff, cmt, post) in enumerate(fastest[:5], 1):
    print(f"  {i}. {cmt.get('from','?')} — через {diff:.0f} сек | {cmt.get('date','')} | «{get_text(cmt)[:60]}»")

# День с максимальным количеством сообщений
day_msg_count = Counter(parse_date(m).strftime('%Y-%m-%d') for m in all_messages if parse_date(m))
busiest_day = day_msg_count.most_common(1)[0]
print(f"\n🌋 Самый горячий день: {busiest_day[0]} — {busiest_day[1]:,} сообщений")

# Топ-5 самых активных дней
print(f"\n🔥 Топ-5 самых активных дней:")
for i, (day, cnt) in enumerate(day_msg_count.most_common(5), 1):
    print(f"  {i}. {day}: {cnt:,} сообщений")

# Самый большой перерыв в постинге автора
if len(dates_posts) > 1:
    dates_posts_sorted = sorted(dates_posts)
    gaps = [(dates_posts_sorted[i+1] - dates_posts_sorted[i], dates_posts_sorted[i], dates_posts_sorted[i+1])
            for i in range(len(dates_posts_sorted)-1)]
    max_gap = max(gaps, key=lambda x: x[0])
    print(f"\n😴 Самый большой перерыв в постинге:")
    print(f"   {max_gap[0].days} дней — с {max_gap[1].strftime('%d.%m.%Y')} по {max_gap[2].strftime('%d.%m.%Y')}")

print("\n" + "=" * 60)
print("АНАЛИЗ ЗАВЕРШЁН")
print("=" * 60)
