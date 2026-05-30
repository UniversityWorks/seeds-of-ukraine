"""
ui/pages/advanced_analytics.py
===============================
Вкладка: Розширена аналітика

Підвкладки:
  1. Ефективність зон    — Q21 (JOIN+agg+HAVING), Q24 (EXISTS)
  2. Бенчмарки врожайності — Q22 (підзапит порівняння), Q23 (підзапит+agg)
  3. Стратегічні фільтри — Q25 (ANY/SOME), Q26 (підзапит IN), Q27 (підзапит+JOIN)
"""

import streamlit as st
import pandas as pd

from database.queries import (
    q21_underperforming_zones, q22_above_avg_growth_cycle,
    q23_above_avg_yield_varieties, q24_regions_with_pending_care,
    q25_shorter_interval_than_any_wheat, q26_polissia_and_forest_steppe,
    q27_varieties_in_top_yield_regions,
)
from utils.error_handler   import safe_query
from ui.components.widgets import section, data_table

# ── Маппінги колонок ──────────────────────────────────────────────────────
_COL_ZONES = {
    "Climate Zone":              "Кліматична зона",
    "Avg Germination Rate (%)":  "Сер. схожість (%)",
    "Varieties in Zone":         "Сортів у зоні",
}
_COL_PENDING = {
    "Region": "Регіон",
    "Oblast": "Область",
}
_COL_LONG_SEASON = {
    "Variety":             "Сорт",
    "Crop":                "Культура",
    "Growth Cycle (Days)": "Цикл росту (днів)",
    "Region":              "Регіон",
}
_COL_TOP_YIELD = {
    "Variety":          "Сорт",
    "Crop":             "Культура",
    "Year":             "Рік",
    "Yield (t/ha)":     "Врожайність (т/га)",
}
_COL_INTENSIVE = {
    "Variety":                  "Сорт",
    "Crop":                     "Культура",
    "Watering Interval (Days)": "Інтервал поливу (днів)",
}
_COL_NORTHERN = {
    "Variety":    "Сорт",
    "Crop":       "Культура",
    "Region":     "Регіон",
    "Planted On": "Дата посіву",
}
_COL_ELITE = {
    "Variety":             "Сорт",
    "Crop":                "Культура",
    "Region":              "Регіон",
    "Climate Zone":        "Кліматична зона",
    "Growth Cycle (Days)": "Цикл росту (днів)",
    "Germination (%)":     "Схожість (%)",
}


def _rename(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    return df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})


def render(cfg: dict) -> None:
    section("Розширена аналітика та бізнес-інтелект",
            "Аналітика на основі підзапитів: бенчмарки, виявлення ризиків та стратегічні висновки.")

    sub1, sub2, sub3 = st.tabs([
        "Ефективність кліматичних зон",
        "Бенчмарки врожайності",
        "Стратегічні фільтри",
    ])

    # ── Підвкладка 1: Ефективність зон ───────────────────────────────────
    with sub1:
        section("Кліматичні зони з низькою схожістю",
                "Зони, середній рівень схожості яких нижче порогового — потребують втручання.")
        germ_thr = st.slider("Позначати зони нижче середньої схожості (%)",
                             60.0, 98.0, 90.0, 1.0)
        df21 = safe_query(q21_underperforming_zones, cfg, float(germ_thr))
        if df21.empty:
            st.info("Усі кліматичні зони перевищують встановлений поріг схожості.")
        else:
            # Додаємо колонку статусу для наочності
            df21_display = _rename(df21, _COL_ZONES).copy()
            if "Сер. схожість (%)" in df21_display.columns:
                df21_display["Статус"] = df21_display["Сер. схожість (%)"].apply(
                    lambda x: "Критично" if x < germ_thr * 0.9 else "Увага"
                )
            data_table(df21_display)

        st.divider()

        section("Регіони з невиконаними завданнями догляду",
                "Регіони, де є хоча б один незавершений запис догляду.")
        df24 = safe_query(q24_regions_with_pending_care, cfg)
        if df24.empty:
            st.success("Прострочених завдань догляду в жодному регіоні не виявлено.")
        else:
            data_table(_rename(df24, _COL_PENDING))

    # ── Підвкладка 2: Бенчмарки врожайності ──────────────────────────────
    with sub2:
        section("Сорти з тривалим вегетаційним циклом",
                "Сорти, цикл вирощування яких перевищує загальний середній показник — потребують розширеного планування.")
        df22 = safe_query(q22_above_avg_growth_cycle, cfg)
        data_table(_rename(df22, _COL_LONG_SEASON))

        st.divider()

        section("Кращі показники — врожайність вище середньої",
                "Сорти, що зафіксували врожайність вище загального середнього значення.")
        df23 = safe_query(q23_above_avg_yield_varieties, cfg)
        if not df23.empty:
            # Зведена таблиця по культурах
            df23_display = _rename(df23, _COL_TOP_YIELD)
            data_table(df23_display)

            st.divider()
            section("Зведення за культурами")
            if "Культура" in df23_display.columns and "Врожайність (т/га)" in df23_display.columns:
                summary = (df23_display
                           .groupby("Культура")["Врожайність (т/га)"]
                           .agg(Записів="count",
                                Максимум="max",
                                Середня="mean")
                           .reset_index()
                           .round(2))
                st.dataframe(summary, use_container_width=True)
        else:
            st.info("Даних не знайдено.")

    # ── Підвкладка 3: Стратегічні фільтри ────────────────────────────────
    with sub3:
        section("Сорти з інтенсивним режимом поливу",
                "Сорти, що потребують поливу частіше, ніж будь-який сорт пшениці — вищі трудовитрати.")
        df25 = safe_query(q25_shorter_interval_than_any_wheat, cfg)
        data_table(_rename(df25, _COL_INTENSIVE))

        st.divider()

        section("Сорти зон Полісся та Лісостепу",
                "Сорти, що вирощуються у зонах підвищеного зволоження на півночі України.")
        df26 = safe_query(q26_polissia_and_forest_steppe, cfg)
        data_table(_rename(df26, _COL_NORTHERN))

        st.divider()

        section("Елітні регіональні сорти",
                "Сорти з регіонів, загальний обсяг врожаю яких перевищує середній показник по країні.")
        df27 = safe_query(q27_varieties_in_top_yield_regions, cfg)
        data_table(_rename(df27, _COL_ELITE))
