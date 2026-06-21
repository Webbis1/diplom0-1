import sys
import time
import random

# Проверяем наличие библиотеки перед стартом
try:
    from bitarray import bitarray
except ImportError:
    print("Ошибка: Библиотека 'bitarray' не установлена.")
    print("Выполните команду: pip install bitarray")
    sys.exit(1)

# --- НАСТРОЙКИ ТЕСТА ---
MAX_ID = 20_000_000      # Максимально возможное число (размер битовой сетки)
NUM_ELEMENTS = 9_000_000  # Сколько случайных чисел мы реально "сохраним"
NUM_LOOKUPS = 9_000_000    # Сколько одиночных поисков проведем
BATCH_SIZE = 1000        # Размер пачки для массового поиска
NUM_BATCHES = 500        # Количество пачек для теста

print(text := f" ГЕНЕРАЦИЯ ДАННЫХ (Диапазон 0 - {MAX_ID:,}) ")
print("-" * len(text))

# Генерируем случайный набор уникальных чисел, которые мы "вставим" в структуры
data_to_insert = random.sample(range(MAX_ID), NUM_ELEMENTS)
# Набор чисел для проверки (часть есть в базе, части нет)
single_search_targets = [random.randint(0, MAX_ID + 1000) for _ in range(NUM_LOOKUPS)]
# Пачки чисел для массового поиска
batch_search_targets = [
    [random.randint(0, MAX_ID + 1000) for _ in range(BATCH_SIZE)]
    for _ in range(NUM_BATCHES)
]

# --- 1. ЗАПОЛНЕНИЕ И ПАМЯТЬ ---
print("\n[1] Заполнение структур и замер памяти...")

# Тест SET
start = time.perf_counter()
py_set = set(data_to_insert)
set_init_time = time.perf_counter() - start
set_memory = sys.getsizeof(py_set)

# Тест BITARRAY
start = time.perf_counter()
ba = bitarray(MAX_ID + 1000) # Инициализируем сетку с запасом
ba.setall(0)
for num in data_to_insert:
    ba[num] = 1
ba_init_time = time.perf_counter() - start
ba_memory = ba.buffer_info()[3] # Реальный размер выделенного Си-буфера в байтах

print(f"Python SET:      Время = {set_init_time:.4f} сек | Память = {set_memory / 1024 / 1024:.2f} MB")
print(f"Bitarray (C):    Время = {ba_init_time:.4f}  сек | Память = {ba_memory / 1024 / 1024:.2f} MB")


# --- 2. ОДИНОЧНЫЙ ПОИСК (Single Lookup) ---
print(f"\n[2] Одиночный поиск ({NUM_LOOKUPS:,} запросов)...")

# Тест SET
start = time.perf_counter()
set_hits = 0
for num in single_search_targets:
    if num in py_set:
        set_hits += 1
set_search_time = time.perf_counter() - start

# Тест BITARRAY
start = time.perf_counter()
ba_hits = 0
for num in single_search_targets:
    # Защита от выхода за границы массива при поиске
    if num < len(ba) and ba[num]:
        ba_hits += 1
ba_search_time = time.perf_counter() - start

print(f"Python SET:      Время = {set_search_time:.4f} сек (Найдено: {set_hits:,})")
print(f"Bitarray (C):    Tiempo = {ba_search_time:.4f} сек (Найдено: {ba_hits:,})")


# --- 3. ПОИСК ПАЧКАМИ (Batch Lookup) ---
print(f"\n[3] Поиск пачками ({NUM_BATCHES} пачек по {BATCH_SIZE} элементов)...")

# Тест SET
start = time.perf_counter()
set_batch_hits = 0
for batch in batch_search_targets:
    # Используем списковое включение (List Comprehension)
    found = [num for num in batch if num in py_set]
    set_batch_hits += len(found)
set_batch_time = time.perf_counter() - start

# Тест BITARRAY
start = time.perf_counter()
ba_batch_hits = 0
ba_len = len(ba)
for batch in batch_search_targets:
    # Прямой проход по индексам в Си-массиве
    found = [num for num in batch if num < ba_len and ba[num]]
    ba_batch_hits += len(found)
ba_batch_time = time.perf_counter() - start

print(f"Python SET:      Время = {set_batch_time:.4f} сек")
print(f"Bitarray (C):    Время = {ba_batch_time:.4f} сек")

print("\n" + "="*40 + "\nРезюме: Тест завершен успешно.")