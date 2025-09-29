# Euro Macromechanica (EMM) Backtest — Data Preparation Toolkit
*(code-only)*

> 🧭 This repository is part of the **Euro Macromechanica (EMM) Backtest** ecosystem.

---

## ‼️ Please read the [Euro Macromechanica (EMM) Backtest — Overview & Methodology](https://github.com/euro-macromechanica-backtest/results/blob/main/README.md)

---

## 📚 Related repositories

- **Backtest results, strategy validation and evidence, data-quality policy (core baseline/extended baseline/stress), and integrity materials** — *[results](https://github.com/euro-macromechanica-backtest/results)*
- **Prepared aggregates and datasets for full reproducibility** — *[data-hub](https://github.com/euro-macromechanica-backtest/data-hub)*
- **Metric‑computation methodology and metrics calculator** for EMM backtest results — *[metrics-toolkit](https://github.com/euro-macromechanica-backtest/metrics-toolkit)*

---

## 🧭 Purpose

- **Minute data normalizer** — prepares HistData-compatible minute series: converts **UTC−05:00 (fixed)** to **UTC+00:00**, then sorts by timestamp.  
- **Economic calendar normalizer** — converts local event timestamps from source providers to **UTC+00:00** (DST handled via the **IANA** time zone database), then sorts by timestamp.  
- **Minute data analyzer** — reports **5-minute gap classification counts** (important for M5 bar quality), derived from HistData minute files `DAT_ASCII_EURUSD_M1_YYYY.txt`.

Detailed audit instructions: see [`AUDIT.md`](https://github.com/euro-macromechanica-backtest/results/blob/main/docs/AUDIT.md).

---

## ⚖️ License

**Apache-2.0** (`LICENSE`) applies to the source code in this repository.  
Any external data you process with these tools remains under the terms set by its original providers.

---

## ✉️ Contacts

GitHub: **@rleydev (thelaziestcat)** · email: **thelazyazzcat@gmail.com** / **thelaziestcat@proton.me**