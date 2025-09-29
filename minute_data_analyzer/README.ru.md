# ⚙️ Minute Data Gap Report Analyzer

## 📚  Общая информация

Aнализатор:
- Читает **строгий текстовый статус‑репорт** с линиями вида:  
  `Gap of <secs>s found between <YYYYMMDDhhmmss> and <YYYYMMDDhhmmss>.`
- **Без самодеятельности по времени:** метки трактуются как **фиксированный EST (UTC−5, без DST)** и **не конвертируются** в UTC.
- Классифицирует гэпы по длительности (M5‑ориентировано):  
  `5–15`, `15–30`, `30–60`, `60–180`, `≥180` минут (полуинтервалы `[a,b)`).
- Генерирует артефакты **рядом с входным файлом**, имена = **полное имя входа (с расширением) + суффикс**.  
  Пример: `DAT_ASCII_EURUSD_M1_2001.txt → DAT_ASCII_EURUSD_M1_2001.txt_gap_buckets_by_date.csv`.
- Пишет **2 CSV + 1 SVG + манифест**:
  1) `…_gap_buckets_by_date.csv` — по **датам × классификациям** + итоги:  
     `date`, `5–15 min`, `15–30 min`, `30–60 min`, `60–180 min`, `≥180 min`,  
     `bucketed_total` (сумма ≥5м), `lt_5_min` (разрывы <5м), `all_gaps_total` (все).
  2) `…_gap_bucket_counts.csv` — **годовые итоги по классификациям**:  
     `bucket`, `count`, `percent_of_all_gaps`, `all_gaps_total` *(строки `ALL` — нет)*.
  3) `…_gaps_scatter.svg` — диаграмма (красные точки): **X = дата (месячные тики, EST)**, **Y = корзины**.
  4) `…_manifest.sha256` — SHA‑256 входа и выходов (только имена, без путей).
- **Детерминизм**: стабильный CSV (порядок/формат), детерминированный SVG (фиксированные rcParams; нормализуем `<dc:date>`).

---

## 📦 Зависимости

### Python 3.13.5

```
numpy==2.1.2
pandas==2.2.3
matplotlib==3.10.6
```
> Рекомендуется обновить инструменты сборки внутри venv: `pip`, `setuptools`, `wheel`.

---

## 📥 Формат входных данных

- **Только текстовый статус‑репорт**, каждая валидная строка строго:
  ```
  Gap of <secs>s found between <YYYYMMDDhhmmss> and <YYYYMMDDhhmmss>.
  ```
  Пример:
  ```
  Gap of 420s found between 20040105 123000 and 20040105 123700.
  Gap of 900s found between 20040106 081500 and 20040106 083000.
  ```
- Невалидные/пустые строки корректно **пропускаются** и не влияют на расчёты.

---

## 📤 Формат выходных данных

- `…_gap_buckets_by_date.csv` — по датам × корзины + `bucketed_total`, `lt_5_min`, `all_gaps_total`.
- `…_gap_bucket_counts.csv` — по корзинам за год: `bucket`, `count`, `percent_of_all_gaps`, `all_gaps_total`.
- `…_gaps_scatter.svg` — **красные точки**, ось X с месячными тиками `YYYY‑MM`, ось Y — список корзин; подпись X: `Date (EST, UTC‑5 fixed)`.
- `…_manifest.sha256` — строки формата:
  ```
  <SHA256>␠␠<filename>
  ```

---

## 🔁 Воспроизводимость и хэши

Утилита детерминирована: при одинаковых версиях Python/библиотек выдаёт **байт‑в‑байт** одинаковые CSV/SVG/манифест → **SHA‑256** совпадают.

Что зафиксировано:
- **CSV**: порядок строк/колонок; `lineterminator="\n"`; `float_format="%.4f"`.
- **SVG**: `svg.hashsalt`, `svg.fonttype="none"`, шрифт `DejaVu Sans`, выключена локаль форматтера осей, фиксированный DPI; `<dc:date>` приводится к константе.

---

## 🛠️ Установка и запуск

### 🍎/🐧 macOS / Linux (zsh/bash)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt  ## установить окружение

# запуск (одна команда, без флагов):
python ./core_minute_data_gap_report_analyzer.py ./DAT_ASCII_EURUSD_M1_2001.txt
# Артефакты появятся рядом с REPORT.txt:
#   REPORT.txt_gap_buckets_by_date.csv
#   REPORT.txt_gap_bucket_counts.csv
#   REPORT.txt_gaps_scatter.svg
#   REPORT.txt_manifest.sha256

```

### 🪟 Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt  ## установить окружение

# запуск:
python .\core_minute_data_gap_report_analyzer.py .\DAT_ASCII_EURUSD_M1_2001.txt 
# Артефакты появятся рядом с REPORT.txt:
#   REPORT.txt_gap_buckets_by_date.csv
#   REPORT.txt_gap_bucket_counts.csv
#   REPORT.txt_gaps_scatter.svg
#   REPORT.txt_manifest.sha256
```

---

## ℹ️ Notes

- Классификация только по **длительности**; выходные/праздники отдельно **не распознаются** (статус‑репорт обычно уже исключает закрытые периоды).
- Сообщение `Matplotlib is building the font cache…` появляется только при **первом** запуске в новом окружении — это нормально.
