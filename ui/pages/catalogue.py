

import streamlit as st
import pandas as pd

from database.queries import (
    q01_active_crops, q02_growth_cycle_range, q04_search_varieties_by_keyword,
    q06_steppe_or_forest_steppe, q07_distinct_climate_zones,
    q15_varieties_with_crops, q16_unmanaged_varieties,
    q17_regions_all_with_varieties,
)
from utils.error_handler   import safe_query
from ui.components.widgets import section, data_table

_COL_CROPS = {
    "Crop Name":      "Назва культури",
    "Plant Family":   "Ботанічна родина",
    "Primary Season": "Основний сезон",
    "Active":         "Активна",
}
_COL_VARIETIES = {
    "Variety":              "Сорт",
    "Crop":                 "Культура",
    "Family":               "Ботанічна родина",
    "Primary Season":       "Сезон",
    "Growth Cycle (Days)":  "Цикл росту (днів)",
    "Watering Every (Days)":"Полив кожні (днів)",
    "Germination Rate (%)": "Схожість (%)",
    "Planted On":           "Дата посіву",
    "Active":               "Активний",
}
_COL_CYCLE = {
    "Variety":             "Сорт",
    "Crop":                "Культура",
    "Growth Cycle (Days)": "Цикл росту (днів)",
    "Region":              "Регіон",
}
_COL_SEARCH = {
    "Variety":             "Сорт",
    "Crop":                "Культура",
    "Region":              "Регіон",
    "Growth Cycle (Days)": "Цикл росту (днів)",
    "Germination Rate (%)":"Схожість (%)",
}
_COL_ZONE = {
    "Variety":      "Сорт",
    "Crop":         "Культура",
    "Region":       "Регіон",
    "Climate Zone": "Кліматична зона",
    "Planted On":   "Дата посіву",
}
_COL_CLIMATE_ZONES = {
    "Climate Zone": "Кліматична зона",
    "Description":  "Опис",
}
_COL_UNMANAGED = {
    "Variety":    "Сорт",
    "Crop":       "Культура",
    "Region":     "Регіон",
    "Planted On": "Дата посіву",
}
_COL_COVERAGE = {
    "Region":           "Регіон",
    "Oblast":           "Область",
    "Climate Zone":     "Кліматична зона",
    "Assigned Variety": "Призначений сорт",
}


def _rename(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    return df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})


def render(cfg: dict) -> None:
    section("Каталог сортів насіння",
            "Перегляд, фільтрація та пошук усіх зареєстрованих сортів по регіонах України.")

    sub1, sub2, sub3, sub4 = st.tabs([
        "Активні культури",
        "Фільтр циклу росту",
        "Пошук за ключовим словом",
        "Кліматичне покриття",
    ])

    with sub1:
        section("Типи активних культур",
                "Усі типи культур, що наразі позначені активними у платформі.")
        df01 = safe_query(q01_active_crops, cfg)
        data_table(_rename(df01, _COL_CROPS))

        st.divider()

        section("Повний каталог сортів",
                "Кожен зареєстрований сорт з даними про культуру, родину та сезон.")
        df15 = safe_query(q15_varieties_with_crops, cfg)
        data_table(_rename(df15, _COL_VARIETIES), height=480)

    with sub2:
        section("Фільтр за тривалістю вегетаційного циклу",
                "Відображати лише сорти, повний цикл вирощування яких потрапляє у вибране вікно.")

        st.markdown('<div class="filter-panel">', unsafe_allow_html=True)
        fc1, fc2 = st.columns(2)
        with fc1:
            min_days = st.slider("Мінімум циклу росту (днів)", 20, 300, 60)
        with fc2:
            max_days = st.slider("Максимум циклу росту (днів)", 21, 400, 90)
        st.markdown('</div>', unsafe_allow_html=True)

        df02 = safe_query(q02_growth_cycle_range, cfg, min_days, max_days)
        data_table(_rename(df02, _COL_CYCLE))

        if not df02.empty:
            st.divider()
            section("Розподіл за тривалістю циклу",
                    "Зведена таблиця кількості сортів по культурах у вибраному діапазоні.")
            summary = (df02
                       .rename(columns={"Crop": "Культура",
                                        "Growth Cycle (Days)": "Цикл росту (днів)"})
                       .groupby("Культура")["Цикл росту (днів)"]
                       .agg(Кількість="count",
                            Мінімум="min",
                            Максимум="max",
                            Середній="mean")
                       .reset_index()
                       .round(1))
            st.dataframe(summary, use_container_width=True)

    with sub3:
        section("Пошук сорту за ключовим словом",
                "Пошук по всіх назвах сортів за частковим збігом.")
        kw = st.text_input("Ключове слово для пошуку",
                           placeholder="напр. Українська, Зоряне, Дніпровський...")
        if kw.strip():
            df04 = safe_query(q04_search_varieties_by_keyword, cfg, kw.strip())
            data_table(_rename(df04, _COL_SEARCH))
        else:
            st.info("Введіть ключове слово для початку пошуку.")

        st.divider()

        section("Сорти зони Степ та Лісостеп",
                "Усі сорти, адаптовані до найважливіших агрокліматичних зон України.")
        df06 = safe_query(q06_steppe_or_forest_steppe, cfg)
        data_table(_rename(df06, _COL_ZONE))

    with sub4:
        section("Активні кліматичні зони",
                "Кліматичні зони, в яких присутній хоча б один активний сорт.")
        df07 = safe_query(q07_distinct_climate_zones, cfg)
        data_table(_rename(df07, _COL_CLIMATE_ZONES))

        st.divider()

        section("Сорти без записів догляду",
                "Активні сорти, що не мають жодного запису догляду — потребують уваги.")
        df16 = safe_query(q16_unmanaged_varieties, cfg)
        if df16.empty:
            st.success("Усі активні сорти мають щонайменше один запис догляду.")
        else:
            data_table(_rename(df16, _COL_UNMANAGED))

        st.divider()

        section("Регіональне покриття",
                "Усі зареєстровані регіони — прогалини вказують на регіони без призначених сортів.")
        df17 = safe_query(q17_regions_all_with_varieties, cfg)
        data_table(_rename(df17, _COL_COVERAGE))
