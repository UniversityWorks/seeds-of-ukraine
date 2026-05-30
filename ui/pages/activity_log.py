"""
ui/pages/activity_log.py
========================
Вкладка: Журнал аудиту

Відображає тихий журнал аудиту, що наповнюється виключно тригером
PostgreSQL fn_trigger_variety_audit() — жоден код застосунку не пише до нього.

В інтерфейсі представлено як "Журнал системного аудиту та активності".
"""

import streamlit as st
import pandas as pd

from database.queries      import fetch_activity_log
from utils.error_handler   import safe_query
from utils.formatters      import audit_style_df
from ui.components.widgets import section, info
from config.settings       import ACTIVITY_LOG_DEFAULT_ROWS

_COL_AUDIT = {
    "ID":              "ID запису",
    "Variety ID":      "ID сорту",
    "Variety":         "Сорт",
    "Action":          "Операція",
    "Field Changed":   "Змінене поле",
    "Previous Value":  "Попереднє значення",
    "New Value":       "Нове значення",
    "Changed By":      "Змінено користувачем",
    "Timestamp":       "Час змін",
}

_ACTION_UA = {
    "INSERT": "Додавання",
    "UPDATE": "Оновлення",
    "DELETE": "Видалення",
}


def _rename(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    return df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})


def render(cfg: dict) -> None:
    section(
        "Журнал системного аудиту та активності",
        "Журнал у реальному часі кожної зміни у каталозі сортів. "
        "Усі записи фіксуються автоматично — ручне ведення не потрібне.",
    )

    # ── Елементи керування ────────────────────────────────────────────────
    ctrl1, ctrl2 = st.columns([3, 1])
    with ctrl2:
        limit = st.number_input(
            "Показати останніх N записів",
            min_value=10, max_value=1000,
            value=ACTIVITY_LOG_DEFAULT_ROWS, step=10,
        )
        st.button("Оновити", use_container_width=True)

    # ── Дані ──────────────────────────────────────────────────────────────
    df = safe_query(fetch_activity_log, cfg, int(limit))

    if df is None or df.empty:
        st.info(
            "Активностей ще не зафіксовано. "
            "Розпочніть з додавання або редагування сорту у вкладці «Управління сортами»."
        )
        return

    # Перекласти значення операцій на українську
    df_display = _rename(df, _COL_AUDIT).copy()
    if "Операція" in df_display.columns:
        df_display["Операція"] = df_display["Операція"].map(
            lambda v: _ACTION_UA.get(str(v).upper(), v)
        )

    st.dataframe(df_display, use_container_width=True, height=520)

    st.caption(
        f"Відображено {len(df_display):,} найновіших подій аудиту. "
        "Записи відсортовані від найновіших до найстаріших."
    )

    st.divider()

    info(
        "<strong>Принцип роботи:</strong> Щоразу, коли сорт насіння створюється, "
        "змінюється або архівується, автоматизована система контролю цілісності даних "
        "фіксує зміну — включаючи змінене поле, його попереднє та нове значення. "
        "Цей журнал доступний лише для читання та не може бути відредагований або видалений."
    )

    # ── Зведення активності ───────────────────────────────────────────────
    if "Action" in df.columns:
        st.markdown("---")
        section("Зведення активності")
        counts = df["Action"].value_counts()

        c1, c2, c3 = st.columns(3)
        c1.metric("Додано сортів",    int(counts.get("INSERT", 0)))
        c2.metric("Оновлено полів",   int(counts.get("UPDATE", 0)))
        c3.metric("Архівовано сортів", int(counts.get("DELETE", 0)))
