# ⚙️ Economic Calendar Normalizer

Минимальный скрипт для нормализации экономических календарей: перевод в UTC (IANA/DST), вставка `datetime_utc` после `event`, удаление `local_dt`/`source_tz`, сортировка и детерминированная запись CSV. 

---

## 📚 Общая информация

Нормализатор:
- Читает CSV (UTF-8; **разделитель `;`**; допускается BOM).
- Использует только `local_dt` (локальное время источника) и `source_tz` (IANA).
- Конвертирует в UTC по базе IANA (`tzdata==2025.2`) с учётом DST/переходов.
- Создаёт `datetime_utc` `YYYY-MM-DDTHH:MM:SS+00:00`, вставляет **сразу после `event`**.
- Полностью удаляет `local_dt` и `source_tz` из выхода.
- Сортирует строки по `datetime_utc` по возрастанию.
- Пишет детерминированный CSV: UTF-8 (без BOM), `;`, LF (`\n`). Имя по умолчанию: `<input>_UTC.csv`.

**Форматы `local_dt`**

Авто-распознавание: ISO, `YYYY-MM-DD HH:MM[:SS]`, US `MM/DD/YYYY ...` (вкл. AM/PM), EU `DD/MM/YYYY ...`, EU `DD.MM.YYYY ...`.
Вход **не должен** включать смещение/таймзону в `local_dt` (`+02:00`, `Z`).

**DST по умолчанию**

- Осень (двусмысленное время) → `--ambiguous latest` (второе появление).
- Весна (несуществующее время) → `--nonexistent shift_forward` (сдвиг вперёд).
Можно поменять флагами в команде.

**Таймзоны (IANA)**

По умолчанию — allow-list США/Еврозоны.

Частые синонимы:
- `Europe/Frankfurt` → **`Europe/Berlin`**
- `Europe/Kiev` → **`Europe/Kyiv`**
- `CET`/`CEST` → **`Europe/Berlin`**
- `EST`/`EDT` → **`America/New_York`**

---

## 📦 Зависимости

### Python 3.13.5

python-dateutil==2.9.0.post0
tzdata==2025.2

---

## 🛠️ Установка и запуск

### 🍎/🐧 macOS/Linux (bash/zsh)
```bash
# В папке со скриптом:
python3 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt    # установить окружение

# Конвертация (UTC + сортировка + запись *_UTC.csv рядом с исходником)
python core_calendar_normalizer.py ./calendar_2001.csv
# Output: ./calendar_2001_UTC.csv
```

### 🪟 Windows (PowerShell)
```powershell
# В папке со скриптом:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt    # установить окружение

# Конвертация (ОБЫЧНЫЙ локальный путь — одинарные \)
python .\core_calendar_normalizer.py .\calendar_2001.csv
# Output: ./calendar_2001_UTC.csv
```