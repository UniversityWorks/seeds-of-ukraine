"""
ui/pages/overview.py
====================
Вкладка: Огляд

Виконавча інформаційна панель:
  - Чотири KPI-метрики (Q08, Q10, кількість регіонів)
  - Таблиця загального врожаю за регіонами (Q20)
  - Таблиця активних культур за сезонами (Q01)
  - Таблиця середньої врожайності сортів (Q11 x Q15)

Всі графіки та діаграми видалено. Дані відображаються
у вигляді структурованих таблиць та KPI-блоків.
"""

import streamlit as st
import pandas as pd

from database.queries      import (q01_active_crops, q08_max_min_yield,
                                   q10_count_varieties, q11_avg_yield_per_variety,
                                   q15_varieties_with_crops, q20_total_yield_per_region)
from utils.error_handler   import safe_query
from utils.formatters      import safe_scalar
from ui.components.widgets import section, data_table

# Маппінг технічних назв колонок на українські бізнес-заголовки
_COL_CROPS = {
    "crop_id":     "ID культури",
    "Crop Name":   "Назва культури",
    "Plant Family":"Ботанічна родина",
    "Primary Season": "Основний сезон",
    "Active":      "Активна",
}
_COL_YIELD_REGION = {
    "Region":            "Регіон",
    "Varieties":         "Кількість сортів",
    "Total Harvest (t)": "Загальний врожай (т)",
    "Total Area (ha)":   "Загальна площа (га)",
}
_COL_AVG_YIELD = {
    "Variety":           "Сорт",
    "Crop":              "Культура",
    "Harvest Records":   "Записів врожаю",
    "Avg Yield (t/ha)":  "Середня врожайність (т/га)",
    "Total Area (ha)":   "Загальна площа (га)",
}


def _rename(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Перейменовує колонки за словником, ігнорує відсутні."""
    return df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})


def render(cfg: dict) -> None:
    # ── KPI-метрики ───────────────────────────────────────────────────────
    counts     = safe_query(q10_count_varieties, cfg)
    extremes   = safe_query(q08_max_min_yield,   cfg)
    regions_df = st.session_state.lookups.get("regions", pd.DataFrame())

    total_v  = safe_scalar(counts,   "Total Varieties",     0,   int)
    active_v = safe_scalar(counts,   "Active Varieties",    0,   int)
    peak_y   = safe_scalar(extremes, "Peak Yield (t/ha)",   0.0, float)
    low_y    = safe_scalar(extremes, "Lowest Yield (t/ha)", 0.0, float)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Усього сортів",             str(total_v),
              delta=f"{active_v} активних")
    m2.metric("Максимальна врожайність",    f"{peak_y:.1f} т/га",
              delta="рекордний показник")
    m3.metric("Мінімальна врожайність",     f"{low_y:.2f} т/га",
              delta="базовий рівень")
    m4.metric("Зареєстровано регіонів",     str(len(regions_df)),
              delta="областей України")

    st.divider()

    # ── Загальний врожай за регіонами (Q20) ──────────────────────────────
    section("Загальний врожай за регіонами",
            "Сукупний обсяг врожаю по зареєстрованих областях.")
    df20 = safe_query(q20_total_yield_per_region, cfg)
    if not df20.empty:
        data_table(_rename(df20, _COL_YIELD_REGION))
    else:
        st.info("Даних про врожай не знайдено.")

    st.divider()

    col_left, col_right = st.columns(2)

    # ── Активні культури за сезонами (Q01) ───────────────────────────────
    with col_left:
        section("Активні культури за сезонами",
                "Усі культури, що наразі позначені як активні у платформі.")
        df01 = safe_query(q01_active_crops, cfg)
        if not df01.empty:
            # Зведена таблиця: кількість культур по сезонах
            vc = df01["Primary Season"].value_counts()
            season_summary = pd.DataFrame({
                "Сільськогосподарський сезон": vc.index.tolist(),
                "Кількість культур":            vc.values.tolist(),
            })
            data_table(season_summary, height=220)

    # ── Середня врожайність за сортами (Q11 x Q15) ───────────────────────
    with col_right:
        section("Продуктивність сортів",
                "Середня врожайність та загальна площа по кожному сорту.")
        df11 = safe_query(q11_avg_yield_per_variety, cfg)
        if not df11.empty:
            data_table(_rename(df11, _COL_AVG_YIELD), height=220)
