#Seeds of Ukraine — SaaS Platform


A commercial-grade, modular Streamlit + PostgreSQL SaaS/CRM platform
for modern Ukrainian farmers, agronomists, and agricultural businesses.

---

## Quick Start (Arch Linux)

```bash
# 1. Clone / place the project
cd seeds_of_ukraine_v2

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Create and seed the database
createdb seeds_ukraine
psql seeds_ukraine < assets/sql/schema.sql

# 4. (Optional) set env vars instead of using the sidebar
export SOU_DB_HOST=localhost
export SOU_DB_PORT=5432
export SOU_DB_NAME=seeds_ukraine
export SOU_DB_USER=postgres
export SOU_DB_PASSWORD=yourpassword

# 5. Launch
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## Project Architecture

```
seeds_of_ukraine_v2/
│
├── app.py                          
├── requirements.txt
├── README.md
│
├── .streamlit/
│   └── config.toml                 
│
├── config/                         
│   ├── __init__.py
│   ├── settings.py                 
│   └── styles.py                   
│
├── database/                      
│   ├── __init__.py
│   ├── connection.py               
│   ├── session.py                 
│   └── queries.py                 
│
├── ui/                             
│   ├── __init__.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── shell.py               
│   │   └── widgets.py              
│   └── pages/
│       ├── __init__.py
│       ├── overview.py             
│       ├── catalogue.py           
│       ├── yield_intelligence.py  
│       ├── care_planner.py        
│       ├── advanced_analytics.py   
│       ├── manage_varieties.py     
│       ├── record_harvest.py      
│       └── activity_log.py        
│
├── utils/                          
│   ├── __init__.py
│   ├── charts.py                  
│   ├── formatters.py              
│   └── error_handler.py            
│
└── assets/
    └── sql/
        └── schema.sql             
```

---

## Architecture Design Decisions

### Why this structure?

| Layer | Pattern | Rationale |
|---|---|---|
| `config/` | Centralised constants | Single source of truth for colours, defaults, CSS. Change once, applies everywhere. |
| `database/connection.py` | Driver isolation | All `psycopg2` calls live here. Swapping to asyncpg or SQLAlchemy requires editing one file only. |
| `database/queries.py` | Repository pattern | 27 named functions, each doing exactly one thing. Trivially testable in isolation. |
| `database/session.py` | Session façade | Bridges the raw connection layer and the Streamlit session_state without polluting either side. |
| `ui/pages/` | One file per tab | Each page is independently readable. Adding a new tab = adding one file + one `with tabs[N]:` line. |
| `ui/components/` | Component library | Shell and widget helpers are imported by any page that needs them — zero duplication. |
| `utils/` | Pure helpers | `charts.py`, `formatters.py`, `error_handler.py` contain zero Streamlit/DB imports where possible, making them fully unit-testable. |

### 3NF Database Schema

Seven normalised tables:
`seasons → climate_zones → regions → crops → seed_varieties → yield_records → care_schedule_log`
plus the trigger-only `audit_variety_history`.

Season-composite indexes and a GIN trigram index on `variety_name` are
included for production-level query performance.

### Trigger & Stored Procedure

| DB Object | UI name |
|---|---|
| `trg_variety_audit` + `fn_trigger_variety_audit()` | "Activity Log" (Tab 8) |
| `sp_generate_watering_reminders(horizon)` | "Generate Reminders" button (Tab 4) |

Neither object is ever mentioned by name in the UI.

---

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `SOU_DB_HOST` | `localhost` | PostgreSQL host |
| `SOU_DB_PORT` | `5432` | PostgreSQL port |
| `SOU_DB_NAME` | `seeds_ukraine` | Database name |
| `SOU_DB_USER` | `postgres` | Database user |
| `SOU_DB_PASSWORD` | *(empty)* | Database password |

Environment variables are read by `config/settings.py` at startup.
Sidebar values override them for the current session.

---

## 27 Mandatory Queries — Coverage Map

| # | Pattern | Function | UI Location |
|---|---|---|---|
| 01 | Simple SELECT | `q01_active_crops` | Catalogue → All Active Crops |
| 02 | BETWEEN…AND | `q02_growth_cycle_range` | Catalogue → Growth Cycle Filter |
| 03 | IN | `q03_yield_by_target_regions` | Yield Intelligence → Regional Reports |
| 04 | LIKE | `q04_search_varieties_by_keyword` | Catalogue → Keyword Search |
| 05 | AND | `q05_active_high_germination` | Care Planner → High-Performance Tracker |
| 06 | OR | `q06_steppe_or_forest_steppe` | Catalogue → Keyword Search |
| 07 | DISTINCT | `q07_distinct_climate_zones` | Catalogue → Climate Zone Coverage |
| 08 | MIN/MAX | `q08_max_min_yield` | Overview cards + Yield → Quality |
| 09 | SUM/AVG | `q09_avg_water_volume_per_crop` | Yield → Productivity Benchmarks |
| 10 | COUNT | `q10_count_varieties` | Overview cards + Care Planner |
| 11 | Agg + GROUP BY | `q11_avg_yield_per_variety` | Yield → Productivity Benchmarks |
| 12 | Agg + WHERE | `q12_avg_yield_by_family_and_year` | Yield → Productivity Benchmarks |
| 13 | Agg + HAVING | `q13_high_quality_crops` | Yield → Quality & Rankings |
| 14 | Agg+HAVING+WHERE+ORDER | `q14_high_yield_regions_by_year` | Yield → Regional Reports |
| 15 | INNER JOIN | `q15_varieties_with_crops` | Catalogue → All Active Crops |
| 16 | LEFT JOIN | `q16_unmanaged_varieties` | Catalogue → Climate Zone Coverage |
| 17 | RIGHT JOIN | `q17_regions_all_with_varieties` | Catalogue → Climate Zone Coverage |
| 18 | JOIN + WHERE | `q18_short_cycle_southern` | Care Planner → Southern Varieties |
| 19 | JOIN + LIKE | `q19_join_region_like` | Yield → Regional Reports |
| 20 | JOIN + Agg | `q20_total_yield_per_region` | Overview + Yield → Regional |
| 21 | JOIN + Agg + HAVING | `q21_underperforming_zones` | Advanced → Zone Performance |
| 22 | Subquery comparison | `q22_above_avg_growth_cycle` | Advanced → Yield Benchmarks |
| 23 | Subquery + Agg | `q23_above_avg_yield_varieties` | Advanced → Yield Benchmarks |
| 24 | Subquery EXISTS | `q24_regions_with_pending_care` | Advanced → Zone Performance |
| 25 | Subquery ANY/SOME | `q25_shorter_interval_than_any_wheat` | Advanced → Strategic Filters |
| 26 | Subquery IN | `q26_polissia_and_forest_steppe` | Advanced → Strategic Filters |
| 27 | Subquery + JOIN | `q27_varieties_in_top_yield_regions` | Advanced → Strategic Filters |
