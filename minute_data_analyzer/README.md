# ⚙️ Minute Data Gap Report Analyzer

## 📚 Overview

The analyzer:
- Reads a **strict text status report** with lines in the form:  
  `Gap of <secs>s found between <YYYYMMDDhhmmss> and <YYYYMMDDhhmmss>.`
- **No time massaging:** timestamps are interpreted as **fixed EST (UTC−5, no DST)** and are **not** converted to UTC.
- Buckets gaps by duration (M5‑oriented):  
  `5–15`, `15–30`, `30–60`, `60–180`, `≥180` minutes (half‑open intervals `[a, b)`).
- Produces artifacts **next to the input file**; names are the **full input filename (with extension) + a suffix**.  
  Example: `DAT_ASCII_EURUSD_M1_2001.txt → DAT_ASCII_EURUSD_M1_2001.txt_gap_buckets_by_date.csv`.
- Writes **2 CSVs + 1 SVG + a manifest**:
  1) `…_gap_buckets_by_date.csv` — **per‑date × per‑bucket** counts + totals:  
     `date`, `5–15 min`, `15–30 min`, `30–60 min`, `60–180 min`, `≥180 min`,  
     `bucketed_total` (sum of gaps ≥5m), `lt_5_min` (gaps <5m), `all_gaps_total` (all gaps).
  2) `…_gap_bucket_counts.csv` — **year‑level totals per bucket**:  
     `bucket`, `count`, `percent_of_all_gaps`, `all_gaps_total` *(no `ALL` rows)*.
  3) `…_gaps_scatter.svg` — scatter plot (red dots): **X = date (monthly ticks, EST)**, **Y = bucket labels**.
  4) `…_manifest.sha256` — SHA‑256 of the input and outputs (filenames only, no paths).
- **Deterministic by design**: stable CSV ordering/format; deterministic SVG (fixed rcParams; normalized `<dc:date>`).

---

## 📦 Dependencies 

### Python 3.13.5

```
numpy==2.1.2
pandas==2.2.3
matplotlib==3.10.6
```
> It’s recommended to update build tools inside your venv: `pip`, `setuptools`, `wheel`.

---

## 📥 Input format

- **Plain text status report only**, each valid line strictly:
  ```
  Gap of <secs>s found between <YYYYMMDDhhmmss> and <YYYYMMDDhhmmss>.
  ```
  Example:
  ```
  Gap of 420s found between 20040105 123000 and 20040105 123700.
  Gap of 900s found between 20040106 081500 and 20040106 083000.
  ```
- Invalid/empty lines are safely **ignored** and do not affect results.

---

## 📤 Output artifacts

- `…_gap_buckets_by_date.csv` — per date × bucket + `bucketed_total`, `lt_5_min`, `all_gaps_total`.
- `…_gap_bucket_counts.csv` — per bucket for the year: `bucket`, `count`, `percent_of_all_gaps`, `all_gaps_total`.
- `…_gaps_scatter.svg` — **red dots**, X axis with monthly ticks `YYYY‑MM`, Y axis is the list of buckets; X label: `Date (EST, UTC‑5 fixed)`.
- `…_manifest.sha256` — lines of the form:
  ```
  <SHA256>␠␠<filename>
  ```

---

## 🔁 Reproducibility & hashes

The tool is deterministic: with identical Python/library versions it produces **byte‑for‑byte** identical CSV/SVG/manifest → **SHA‑256** matches.

What’s locked down:
- **CSV**: row/column order; `lineterminator="\n"`; `float_format="%.4f"`.
- **SVG**: `svg.hashsalt`, `svg.fonttype="none"`, font `DejaVu Sans`, locale‑free axis formatters, fixed DPI; `<dc:date>` normalized to a constant.

---

## 🛠️ Install & run

### 🍎/🐧 macOS / Linux (zsh/bash)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt  ## set up the environment

# run (single command, no flags):
python ./core_minute_data_gap_report_analyzer.py ./DAT_ASCII_EURUSD_M1_2001.txt
# Artifacts will appear next to REPORT.txt:
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
python -m pip install -r requirements.txt  ## set up the environment

# run:
python .\core_minute_data_gap_report_analyzer.py .\DAT_ASCII_EURUSD_M1_2001.txt
# Artifacts will appear next to REPORT.txt:
#   REPORT.txt_gap_buckets_by_date.csv
#   REPORT.txt_gap_bucket_counts.csv
#   REPORT.txt_gaps_scatter.svg
#   REPORT.txt_manifest.sha256
```

---

## ℹ️ Notes

- Bucketing is purely by **duration**; weekends/holidays are **not** identified separately (the upstream status report typically excludes closed sessions).
- The message `Matplotlib is building the font cache…` appears only on the **first** run in a fresh environment — that’s expected.
