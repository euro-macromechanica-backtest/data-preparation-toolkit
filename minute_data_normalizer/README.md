# ⚙️ Minute Data Normalizer

## 📚 Overview

- Assigns column **headers** in this exact order:
  `datetime;open;high;low;close;volume` *(if the input file has no header)*.
- Converts timestamps from **fixed EST (UTC−5, no DST)** to **UTC**.
- Formats `datetime` as **`YYYY-MM-DDTHH:MM`** *(no seconds; `T` separator)*.
- Sorts rows by time in **ascending** order.
- The normalizer **does not insert or delete anything**:
  - does **not** backfill missing minutes;
  - does **not** drop duplicate timestamps;
  - does **not modify** values in `open/high/low/close/volume` *(read/written as text)*.
- Writes a **plain CSV** with `;` as the delimiter.
- Output filename = input name + **`_UTC`** suffix before `.csv`.  
  Example: `DAT_ASCII_EURUSD_M1_2010.csv` → `DAT_ASCII_EURUSD_M1_2010_UTC.csv`.

---

## 📦 Dependencies

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

## 📥 Input format

- **CSV only** with `;` delimiter.
- For headerless **DAT_ASCII** files, the first column must be a timestamp in:  
  `YYYYMMDD HHMMSS` (e.g., `20100103 170000`).  
  The **no‑space** variant is also supported: `YYYYMMDDHHMMSS`.

---

## 📤 Output format

- Header: `datetime;open;high;low;close;volume`.
- Time: **UTC**, text format `YYYY-MM-DDTHH:MM`.
- Delimiter: `;`.
- Columns `open/high/low/close/volume` are written **as is**, without rounding or conversion.

---

## 🔁 Reproducibility & hashes

The utility is deterministic: same input and same environment versions → **byte‑for‑byte identical CSV**, so **SHA‑256** hashes match.

---

## 🛠️ Install & run

### 🍎/🐧 macOS / Linux (zsh/bash)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.lock  ## install environment

# run:
python ./core_minute_normalizer.py --input ./DAT_ASCII_EURUSD_M1_2024.csv
# Output: ./DAT_ASCII_EURUSD_M1_2024_UTC.csv
```

### 🪟 Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.lock  ## install environment

# run:
python .\core_minute_normalizer.py --input .\DAT_ASCII_EURUSD_M1_2024.csv
# Output: .\DAT_ASCII_EURUSD_M1_2024_UTC.csv
```
