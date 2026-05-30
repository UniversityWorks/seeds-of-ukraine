

import streamlit as st
import pandas as pd
from datetime import datetime

from database.queries import (
    q03_yield_by_target_regions, q08_max_min_yield,
    q09_avg_water_volume_per_crop, q11_avg_yield_per_variety,
    q12_avg_yield_by_family_and_year, q13_high_quality_crops,
    q14_high_yield_regions_by_year, q19_join_region_like,
    q20_total_yield_per_region,
)
from utils.error_handler   import safe_query
from utils.formatters      import safe_scalar
from ui.components.widgets import section, data_table
from config.settings       import CROP_FAMILY_OPTIONS

_COL_YIELD = {
    "Variety":        "Сорт",
    "Crop":           "Культура",
    "Region":         "Регіон",
    "Season":         "Сезон",
    "Harvest Year":   "Рік врожаю",
    "Yield (t/ha)":   "Врожайність (т/га)",
    "Area (ha)":      "Площа (га)",
    "Quality Score":  "Оцінка якості",
}
_COL_WATER = {
    "Crop":                        "Культура",
    "Avg Water Volume (ml/sqm)":   "Сер. обсяг поливу (мл/м2)",
    "Total Area (ha)":             "Загальна площа (га)",
}
_COL_AVG_YIELD = {
    "Variety":          "Сорт",
    "Crop":             "Культура",
    "Harvest Records":  "Записів врожаю",
    "Avg Yield (t/ha)": "Сер. врожайність (т/га)",
    "Total Area (ha)":  "Загальна площа (га)",
}
_COL_FAMILY_YEAR = {
    "Variety":          "Сорт",
    "Plant Family":     "Ботанічна родина",
    "Year":             "Рік",
    "Avg Yield (t/ha)": "Сер. врожайність (т/га)",
}
_COL_QUALITY = {
    "Crop":              "Культура",
    "Avg Quality Score": "Сер. оцінка якості",
    "Harvest Records":   "Записів врожаю",
}
_COL_TOP_REGIONS = {
    "Region":           "Регіон",
    "Year":             "Рік",
    "Avg Yield (t/ha)": "Сер. врожайність (т/га)",
    "Varieties Tracked":"Відстежено сортів",
}
_COL_REGION_TOTALS = {
    "Region":            "Регіон",
    "Varieties":         "Кількість сортів",
    "Total Harvest (t)": "Загальний врожай (т)",
    "Total Area (ha)":   "Загальна площа (га)",
}
_COL_REGION_SEARCH = {
    "Region":          "Регіон",
    "Variety":         "Сорт",
    "Crop":            "Культура",
    "Year":            "Рік",
    "Yield (t/ha)":    "Врожайність (т/га)",
}


def _rename(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    return df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})


def render(cfg: dict) -> None:
    section("Центр аналітики врожайності",
            "Поглиблена аналітика врожаїв, регіональні бенчмарки та показники продуктивності.")

    sub1, sub2, sub3 = st.tabs([
        "Регіональні звіти",
        "Показники продуктивності",
        "Якість та рейтинги",
    ])

    with sub1:
        section("Врожайність за цільовими регіонами",
                "Оберіть один або кілька регіонів для аналізу їхньої врожайності.")
        regions_list = st.session_state.lookups.get("regions", pd.DataFrame())
        all_names = regions_list["region_name"].tolist() if not regions_list.empty else []

        selected = st.multiselect(
            "Вибір регіонів",
            options=all_names,
            default=all_names[:4],
        )
        if selected:
            df03 = safe_query(q03_yield_by_target_regions, cfg, selected)
            data_table(_rename(df03, _COL_YIELD))

        st.divider()

        section("Пошук регіонів за назвою",
                "Знайти записи врожайності для регіонів, назва яких містить ключове слово.")
        reg_kw = st.text_input("Ключове слово для назви регіону",
                               placeholder="напр. Дніпро, Полтава, Харків...")
        if reg_kw.strip():
            df19 = safe_query(q19_join_region_like, cfg, reg_kw.strip())
            data_table(_rename(df19, _COL_REGION_SEARCH))

        st.divider()

        section("Регіони-лідери за врожайністю",
                "Регіони, середня врожайність яких перевищує поріг у вибраному році.")
        r1, r2 = st.columns(2)
        with r1:
            sel_year = st.selectbox("Рік врожаю", [2024, 2023, 2022, 2021], index=1)
        with r2:
            min_avg = st.number_input("Мін. середня врожайність (т/га)",
                                      value=5.0, step=0.5, min_value=0.0)
        df14 = safe_query(q14_high_yield_regions_by_year, cfg,
                          int(sel_year), float(min_avg))
        data_table(_rename(df14, _COL_TOP_REGIONS))

    with sub2:
        section("Ефективність зрошення за культурою",
                "Середній обсяг поливу та загальна оброблювана площа по культурах.")
        df09 = safe_query(q09_avg_water_volume_per_crop, cfg)
        data_table(_rename(df09, _COL_WATER))

        st.divider()

        section("Середня врожайність за сортом",
                "Загальний рейтинг продуктивності по всіх зареєстрованих сортах.")
        df11 = safe_query(q11_avg_yield_per_variety, cfg)
        data_table(_rename(df11, _COL_AVG_YIELD))

        st.divider()

        section("Врожайність за ботанічною родиною та роком",
                "Фільтрація даних продуктивності за ботанічною родиною та мінімальним роком врожаю.")
        f1, f2 = st.columns(2)
        with f1:
            sel_family = st.selectbox("Ботанічна родина", CROP_FAMILY_OPTIONS)
        with f2:
            sel_min_yr = st.number_input("Починаючи з року",
                                         value=2023, step=1,
                                         min_value=1990, max_value=2100)
        df12 = safe_query(q12_avg_yield_by_family_and_year, cfg,
                          sel_family, int(sel_min_yr))
        data_table(_rename(df12, _COL_FAMILY_YEAR))

    with sub3:
        section("Рекордні показники врожайності")
        df08 = safe_query(q08_max_min_yield, cfg)
        if not df08.empty:
            c1, c2 = st.columns(2)
            c1.metric("Максимальна врожайність",
                      f"{safe_scalar(df08, 'Peak Yield (t/ha)', 0.0):.2f} т/га")
            c2.metric("Мінімальна врожайність",
                      f"{safe_scalar(df08, 'Lowest Yield (t/ha)', 0.0):.2f} т/га")

        st.divider()

        section("Рейтинг культур за якістю",
                "Культури, середня оцінка якості яких перевищує встановлений поріг.")
        min_q = st.slider("Мінімальна середня оцінка якості", 1.0, 10.0, 8.0, 0.5)
        df13  = safe_query(q13_high_quality_crops, cfg, float(min_q))
        data_table(_rename(df13, _COL_QUALITY))

        st.divider()

        section("Загальний врожай за регіонами",
                "Сумарний обсяг врожаю та оброблювана площа по кожному регіону.")
        df20 = safe_query(q20_total_yield_per_region, cfg)
        data_table(_rename(df20, _COL_REGION_TOTALS))
