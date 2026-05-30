"""
utils/error_handler.py
======================
Централізована обробка помилок для модулів сторінок Streamlit.
"""

import traceback
import pandas as pd
import streamlit as st
from typing import Callable, Any


def safe_query(fn: Callable, *args, **kwargs) -> pd.DataFrame:
    """
    Безпечно виконує функцію запиту у контексті Streamlit.
    Повертає DataFrame або порожній DataFrame при будь-якому винятку.
    """
    try:
        result = fn(*args, **kwargs)
        return result if isinstance(result, pd.DataFrame) else pd.DataFrame()
    except Exception as exc:
        st.error(f"Помилка завантаження даних: {exc}")
        with st.expander("Технічні деталі"):
            st.code(traceback.format_exc(), language="python")
        return pd.DataFrame()


def safe_write(fn: Callable, *args, **kwargs) -> Any:
    """
    Безпечно виконує операцію запису (CRUD).
    Повертає результат функції або None при помилці.
    """
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        st.error(f"Операція не виконана: {exc}")
        return None


def show_df(df: pd.DataFrame,
            height: int = 420,
            empty_msg: str = "Даних за обраними фільтрами не знайдено.") -> None:
    """
    Уніфікований рендер DataFrame зі станом порожнього результату.
    """
    if df is None or df.empty:
        st.info(empty_msg)
    else:
        st.dataframe(df, use_container_width=True, height=height)
        st.caption(f"Відображено {len(df):,} {_records_ua(len(df))}")


def _records_ua(n: int) -> str:
    """Повертає правильне відмінювання слова 'запис' для числа n."""
    if 11 <= n % 100 <= 14:
        return "записів"
    mod = n % 10
    if mod == 1:
        return "запис"
    if 2 <= mod <= 4:
        return "записи"
    return "записів"
