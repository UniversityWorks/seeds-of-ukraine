"""
ui/pages/care_planner.py
========================
Вкладка: Планувальник догляду

Функції:
  - Панель нагадувань про полив — виклик sp_generate_watering_reminders()
  - Трекер продуктивних сортів — Q05 (AND умови)
  - Зведення кількості сортів  — Q10 (COUNT)
  - Швидкостиглі південні сорти — Q18 (JOIN + WHERE)
"""

import streamlit as st
import pandas as pd

from database.queries      import (sp_watering_reminders, q05_active_high_germination,
                                   q10_count_varieties, q18_short_cycle_southern)
from utils.error_handler   import safe_query
from utils.formatters      import safe_scalar
from ui.components.widgets import section, data_table
from config.settings       import CARE_HORIZON_DEFAULT_DAYS

# ── Маппінги колонок ──────────────────────────────────────────────────────
_COL_REMINDERS = {
    "Variety":            "Сорт",
    "Crop":               "Культура",
    "Region":             "Регіон",
    "Next Watering Date": "Наступна дата поливу",
    "Volume (ml/sqm)":    "Обсяг (мл/м2)",
}
_COL_GERMINATION = {
    "Variety":             "Сорт",
    "Crop":                "Культура",
    "Germination Rate (%)":"Схожість (%)",
    "Growth Cycle (Days)": "Цикл росту (днів)",
    "Region":              "Регіон",
}
_COL_SOUTHERN = {
    "Variety":             "Сорт",
    "Crop":                "Культура",
    "Growth Cycle (Days)": "Цикл росту (днів)",
    "Region":              "Регіон",
    "Climate Zone":        "Кліматична зона",
}


def _rename(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    return df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})


def render(cfg: dict) -> None:
    section("Планувальник завдань та сповіщень про полив",
            "Автоматизоване планування догляду на основі інтервалів поливу кожного сорту.")

    # ── Збережена процедура: генерація нагадувань про полив ───────────────
    sp_col1, sp_col2 = st.columns([3, 1])
    with sp_col1:
        horizon = st.slider("Горизонт планування (днів наперед)",
                            1, 30, CARE_HORIZON_DEFAULT_DAYS)
    with sp_col2:
        st.write("")
        st.write("")
        run_sp = st.button("Сформувати нагадування", use_container_width=True)

    if run_sp or st.session_state.get("_sp_ran"):
        st.session_state["_sp_ran"] = True
        df_sp = safe_query(sp_watering_reminders, cfg, int(horizon))
        if not df_sp.empty:
            st.success(
                f"Виявлено {len(df_sp)} завдань з поливу "
                f"на наступні {horizon} дн."
            )
            st.divider()
            section("Майбутні завдання з поливу")
            data_table(_rename(df_sp, _COL_REMINDERS))
        else:
            st.info(
                f"У межах наступних {horizon} дн. завдань з поливу не знайдено. "
                "Усі сорти дотримуються розкладу."
            )

    st.divider()

    # ── Q05: AND умови — сорти з високою схожістю ─────────────────────────
    section("Трекер продуктивних сортів",
            "Фільтрація активних сортів за типом культури та мінімальним рівнем схожості.")

    lookups  = st.session_state.lookups
    crops_df = lookups.get("crops", pd.DataFrame())
    crop_names = crops_df["crop_name"].tolist() if not crops_df.empty else []

    v1, v2 = st.columns(2)
    with v1:
        care_crop = st.selectbox("Тип культури",
                                  crop_names if crop_names else ["—"])
    with v2:
        germ_thresh = st.slider("Мін. рівень схожості (%)", 50.0, 99.0, 85.0, 1.0)

    if crop_names and care_crop != "—":
        df05 = safe_query(q05_active_high_germination, cfg,
                          care_crop, float(germ_thresh))
        data_table(_rename(df05, _COL_GERMINATION))

    st.divider()

    # ── Q10: COUNT — зведення кількості сортів ────────────────────────────
    section("Зведення кількості сортів у платформі")
    df10 = safe_query(q10_count_varieties, cfg)
    if not df10.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Усього сортів",
                  safe_scalar(df10, "Total Varieties",  0, int))
        c2.metric("Активних сортів",
                  safe_scalar(df10, "Active Varieties",  0, int))
        c3.metric("Архівованих сортів",
                  safe_scalar(df10, "Archived Varieties", 0, int))

    st.divider()

    # ── Q18: JOIN + WHERE — швидкостиглі південні сорти ──────────────────
    section("Швидкостиглі сорти для південних зон",
            "Сорти, придатні для короткого вегетаційного вікна степових та прибережних зон.")
    max_gc = st.slider("Максимальний цикл росту (днів)", 50, 200, 100)
    df18   = safe_query(q18_short_cycle_southern, cfg, int(max_gc))
    data_table(_rename(df18, _COL_SOUTHERN))
