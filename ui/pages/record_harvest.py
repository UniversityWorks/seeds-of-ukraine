

import streamlit as st
import pandas as pd
from datetime import datetime

from database.queries    import crud_insert_yield, q03_yield_by_target_regions
from database.session    import (refresh_lookups, variety_options,
                                  region_options, season_options)
from utils.error_handler import safe_query, safe_write
from ui.components.widgets import section, data_table

_COL_YIELD = {
    "Variety":       "Сорт",
    "Crop":          "Культура",
    "Region":        "Регіон",
    "Season":        "Сезон",
    "Harvest Year":  "Рік врожаю",
    "Yield (t/ha)":  "Врожайність (т/га)",
    "Area (ha)":     "Площа (га)",
    "Quality Score": "Оцінка якості",
}


def _rename(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    return df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})


def render(cfg: dict) -> None:
    section("Реєстрація нового врожаю",
            "Внесення показника врожайності для будь-якого сорту та сезону.")

    lookups = st.session_state.lookups
    vars_   = variety_options(lookups)
    regions = region_options(lookups)
    seasons = season_options(lookups)

    if not vars_ or not regions or not seasons:
        st.warning("Дані платформи не знайдено. "
                   "Спершу застосуйте схему та початкові дані.")
        return

    with st.form("form_record_harvest", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            y_var    = st.selectbox("Сорт *",          list(vars_.keys()))
            y_region = st.selectbox("Регіон збору *",  list(regions.keys()))
            y_season = st.selectbox("Сезон *",          list(seasons.keys()))

        with col2:
            y_year    = st.number_input("Рік врожаю *",
                                         min_value=1990, max_value=2100,
                                         value=datetime.now().year)
            y_yield   = st.number_input("Врожайність (т/га) *",
                                         min_value=0.0, max_value=500.0,
                                         value=5.0, step=0.1)
            y_area    = st.number_input("Площа (га) *",
                                         min_value=0.1, max_value=500_000.0,
                                         value=100.0, step=10.0)
            y_quality = st.slider("Оцінка якості (1 – 10)", 1, 10, 7)

        submitted = st.form_submit_button("Зареєструвати врожай",
                                          use_container_width=True)

    if submitted:
        new_id = safe_write(crud_insert_yield, cfg, {
            "variety_id":   vars_[y_var],
            "region_id":    regions[y_region],
            "season_id":    seasons[y_season],
            "harvest_year": int(y_year),
            "yield_tons_ha":float(y_yield),
            "area_ha":      float(y_area),
            "quality_score":int(y_quality),
        })
        if new_id:
            st.success(f"Запис врожаю №{new_id} успішно збережено.")
            st.session_state.lookups = refresh_lookups(cfg)
            st.rerun()

    st.divider()
    section("Останні записи врожаю",
            "Усі внесені показники врожайності, що наразі зберігаються у системі.")

    regions_df  = lookups.get("regions", pd.DataFrame())
    all_regions = (regions_df["region_name"].tolist()
                   if not regions_df.empty else [])

    if all_regions:
        df_recent = safe_query(q03_yield_by_target_regions, cfg, all_regions)
        data_table(_rename(df_recent, _COL_YIELD), height=380)
    else:
        st.info("Регіони ще не зареєстровано.")
