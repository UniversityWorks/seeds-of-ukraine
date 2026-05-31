

import streamlit as st
import pandas as pd

from database.queries      import (q01_active_crops, q08_max_min_yield,
                                   q10_count_varieties, q11_avg_yield_per_variety,
                                   q15_varieties_with_crops, q20_total_yield_per_region)
from utils.error_handler   import safe_query
from utils.formatters      import safe_scalar
from ui.components.widgets import section, data_table

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
    return df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})


def render(cfg: dict) -> None:
    regions_df = st.session_state.lookups.get("regions", pd.DataFrame())

    section("Загальний врожай за регіонами",
            "Сукупний обсяг врожаю по зареєстрованих областях.")
    df20 = safe_query(q20_total_yield_per_region, cfg)
    if not df20.empty:
        data_table(_rename(df20, _COL_YIELD_REGION))
    else:
        st.info("Даних про врожай не знайдено.")

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        section("Активні культури за сезонами",
                "Усі культури, що наразі позначені як активні у платформі.")
        df01 = safe_query(q01_active_crops, cfg)
        if not df01.empty:
            vc = df01["Primary Season"].value_counts()
            season_summary = pd.DataFrame({
                "Сільськогосподарський сезон": vc.index.tolist(),
                "Кількість культур":            vc.values.tolist(),
            })
            data_table(season_summary, height=220)

    with col_right:
        section("Продуктивність сортів",
                "Середня врожайність та загальна площа по кожному сорту.")
        df11 = safe_query(q11_avg_yield_per_variety, cfg)
        if not df11.empty:
            data_table(_rename(df11, _COL_AVG_YIELD), height=220)
