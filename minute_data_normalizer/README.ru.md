# ⚙️ Minute Data Normalizer

Нормализатор минутных данных HistData.com

---

## 📚 Общая информация

- Присвоение заголовков **столбцов** строго в порядке:
  `datetime;open;high;low;close;volume` *(если входной файл без заголовка)*.
- Конвертация времени из **фиксированного EST (UTC−5, без перехода на летнее время)** в **UTC**.
- Форматирование `datetime` как **`YYYY-MM-DDTHH:MM`** *(без секунд; разделитель — `T`)*.
- Сортировка строк по времени **по возрастанию**.
- Нормализатор **ничего не вставляет и не удаляет**:
  - не заполняет пропуски минут;
  - не удаляет дубликаты меток времени;
  - **не изменяет** значения в столбцах `open/high/low/close/volume` *(читаются/записываются как текст)*.
- Записывает **обычный CSV** с разделителем `;`.
- Имя выходного файла: как у входного + суффикс **`_UTC`** перед `.csv`.  
  Пример: `DAT_ASCII_EURUSD_M1_2010.csv` → `DAT_ASCII_EURUSD_M1_2010_UTC.csv`.

---

## 📦 Зависимости

### Python 3.13.5

```
numpy==2.3.3
pandas==2.3.2
python-dateutil==2.9.0.post0
pytz==2025.2
six==1.17.0
tzdata==2025.2
```

---

## 📥 Формат входных данных

- **Только CSV** с разделителем `;`.
- Если файл без заголовка и в стиле **DAT_ASCII**, ожидается первая колонка времени в формате:  
  `YYYYMMDD HHMMSS` (например, `20100103 170000`).  
  Также поддерживается вариант **без пробела**: `YYYYMMDDHHMMSS`.

---

## 📤 Формат выходных данных

- Заголовок: `datetime;open;high;low;close;volume`.
- Время: **UTC**, текстовый формат `YYYY-MM-DDTHH:MM`.
- Разделитель: `;`.
- Столбцы `open/high/low/close/volume` — записываются **как есть**, без округления и преобразований.

---

## 🔁 Воспроизводимость и хэши

Утилита детерминирована: одинаковый вход и одинаковые версии окружения → **байт‑в‑байт одинаковый CSV**, поэтому совпадают **SHA‑256** хэши.

---

## 🛠️ Установка и запуск

### 🍎/🐧 macOS / Linux (zsh/bash)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.lock  ## установить окружение

# запуск:
python ./core_minute_normalizer.py --input ./DAT_ASCII_EURUSD_M1_2024.csv
# Output: ./DAT_ASCII_EURUSD_M1_2024_UTC.csv
```

### 🪟 Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.lock  ## установить окружение

# запуск:
python .\core_minute_normalizer.py --input .\DAT_ASCII_EURUSD_M1_2024.csv
# Output: .\DAT_ASCII_EURUSD_M1_2024_UTC.csv
```