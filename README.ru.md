# Euro Macromechanica (EMM) Backtest — Data Preparation Toolkit
*(code-only)*
 
> 🧭 Этот репозиторий является частью экосистемы **Euro Macromechanica (EMM) Backtest**.

---

## ‼️ Читайте [обзор и методологию – Euro Macromechanica (EMM) Backtest](https://github.com/euro-macromechanica-backtest/results/blob/main/README.ru.md)

---

## 📚 Связанная экосистема

- **Результаты бэктеста, доказательство наличия стратегии, политика качества данных (headline/stress), integrity-материалы** — *[results](https://github.com/euro-macromechanica-backtest/results)*  
- **Подготовленные агрегаты/данные для воспроизводимости** — *[data-hub](https://github.com/euro-macromechanica-backtest/data-hub)*
- **Калькуляторы метрик** для результатов бэктеста EMM - *[metrics_toolkit](https://github.com/euro-macromechanica-backtest/metrics-toolkit)*

---

## 🧭 Назначение

**minute data nomralizer** — готовит минутные ряды (HistData-совместимые): конверсия **UTC-5 (fixed) → UTC±00:00**, соортировка после приведения к UTC±00:00.
**economic calendar normalizer** - приводит локальное время собранных событий источников в **UTC±00:00** с учетом **DST** с помощью **IANA**.
**minute data analyzer** - выводит колличество разрывов 5 минутной классификации **(важно для качества M5-баров)** на основе отчетов `DAT_ASCII_EURUSD_M1_YYYY.txt` HistData данных.

Подробная инструкция по аудиту в [`AUDIT.ru.md`](https://github.com/euro-macromechanica-backtest/results/blob/main/docs/AUDIT.ru.md).

---

## ⚖️ Лицензия

**Apache-2.0** (`LICENSE`) — на исходный код в этом репозитории.  
Внешние данные, которыми вы пользуетесь с помощью этих инструментов, остаются под условиями их оригинальных провайдеров.

---

## ✉️ Контакты

GitHub: **@rleydev (thelaziestcat)** · email: **thelazyazzcat@gmail.com** / **thelaziestcat@proton.me**
