#  USD Piggybank

A **serverless personal product** designed to track the USD/BRL exchange rate, store historical data, trigger **smart alerts**, and visualize everything through a **public dashboard** — all running **100% for free** using GitHub Actions.

>  **Philosophy**  
> Discipline beats perfect timing.  
> This project focuses on **decision support**, not automated trading.

---

##  Overview

USD Piggybank is both:
- a **practical financial radar** for daily monitoring, and
- a **portfolio project** showcasing automation, resilience, and serverless architecture.

### Key capabilities
-  Fetches **USD/BRL** twice a day (scheduled)
-  Stores historical data in versioned JSON
-  Sends alerts via **Discord webhook** using configurable rules
-  Publishes a live **GitHub Pages dashboard**
-  Runs fully **serverless** (no VM, no cloud costs)

---

##  Live Demo

 **Dashboard**  
https://momoantunes.github.io/USD-Piggybank/

The dashboard is automatically redeployed every time new data is collected.

---

##  Architecture

```
GitHub Actions (Cron - 2x/day)
            |
            v
     Python Collector
   - AwesomeAPI (spot)
   - BCB PTAX (fallback)
            |
            +--> data/usdbrl.json (history)
            |
            +--> Discord Webhook (alerts)
            |
            v
       GitHub Pages
      Static Dashboard
```

### Design decisions
- **No database**: JSON + Git history is sufficient and transparent
- **No servers**: scheduling and execution handled by GitHub Actions
- **Resilient data fetching**: automatic fallback to BCB PTAX on rate limits or failures
- **Human-in-the-loop**: alerts inform decisions, never execute them

---

##  Alert Logic (Decision Support)

Alerts are **signal-based**, not noisy notifications.

Supported triggers:
-  Price below a target (`BUY_BELOW`)
-  Percentage drop (`ALERT_DROP_PCT`)
-  Percentage rise (`ALERT_RISE_PCT`)
-  Optional `ALWAYS_NOTIFY` flag (useful for testing)

>  This project does **not** perform automated buying or selling.

---

##  Dashboard Features

- Latest USD/BRL quote
- Variation compared to previous check
- Data source indicator (Spot vs PTAX fallback)
- Lightweight line chart (recent history)
- Fully static (HTML + vanilla JS)

---

##  Tech Stack

- **Python 3.11**
- **GitHub Actions** (cron scheduling & CI)
- **GitHub Pages**
- **Discord Webhooks**

**Data sources**
- AwesomeAPI (spot market)
- Banco Central do Brasil – PTAX (official fallback)

---

##  Configuration

All configuration is handled through **GitHub Actions variables and secrets**.

### Secrets
- `DISCORD_WEBHOOK_URL`

### Variables
- `BUY_BELOW` (e.g. `5.10`)
- `ALERT_DROP_PCT` (e.g. `0.8`)
- `ALERT_RISE_PCT` (e.g. `1.0`)
- `ALWAYS_NOTIFY` (`true` or `false`)

---

##  Local Development

```bash
pip install -r requirements.txt
python src/main.py
```

You can also trigger execution manually via:  
**Actions → USD Piggybank - 2x/day → Run workflow**

---

##  Why This Project Matters

This repository demonstrates:
- serverless automation design
- resilient data ingestion with fallbacks
- clean, maintainable Python code
- CI/CD-driven static deployments
- conscious financial tooling with human decision-making

It was built as a **real personal tool**, not a toy example.

---

##  Roadmap

- Telegram notifications
- Daily / weekly digest
- Volatility and min/max indicators
- Manual purchase tracking (non-automated)
- Multi-currency support (EUR, BTC, etc.)

---

Built by: Mônica (Engineering) & Hugo (Design)

---
Feel free to fork, adapt, or use this project as inspiration.
