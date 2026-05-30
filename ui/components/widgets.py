"""
ui/components/widgets.py
========================
Невеликі багаторазові фрагменти Streamlit UI, що використовуються
у кількох модулях сторінок.
"""

import streamlit as st
import pandas as pd
from utils.error_handler import show_df


def filter_panel():
    st.markdown('<div class="filter-panel">', unsafe_allow_html=True)


def filter_panel_end():
    st.markdown('</div>', unsafe_allow_html=True)


def section(title: str, subtitle: str = "") -> None:
    """Відображає стилізований заголовок розділу з необов'язковим підзаголовком."""
    sub_html = f'<div class="section-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="section-title">{title}</div>{sub_html}',
        unsafe_allow_html=True,
    )


def info(body: str) -> None:
    """Відображає стилізовану інформаційну картку."""
    st.markdown(f'<div class="info-card">{body}</div>', unsafe_allow_html=True)


def data_table(df: pd.DataFrame,
               height: int = 420,
               empty_msg: str = "Даних за обраними фільтрами не знайдено.") -> None:
    """Уніфікований рендер DataFrame з обробкою порожнього стану."""
    show_df(df, height=height, empty_msg=empty_msg)


def crop_selector(label: str, lookups: dict) -> tuple:
    """Рендерить список культур та повертає (назва, id)."""
    from database.session import crop_options
    opts = crop_options(lookups)
    if not opts:
        st.warning("Активних культур не знайдено.")
        return "", 0
    name = st.selectbox(label, list(opts.keys()))
    return name, opts[name]


def region_selector(label: str, lookups: dict,
                    multiselect: bool = False,
                    default_n: int = 4):
    """Рендерить список регіонів. Повертає (назва, id) або список назв."""
    from database.session import region_options
    opts   = region_options(lookups)
    names  = list(opts.keys())
    if multiselect:
        return st.multiselect(label, names, default=names[:default_n])
    name = st.selectbox(label, names)
    return name, opts[name]


def variety_selector(label: str, lookups: dict) -> tuple:
    """Рендерить список сортів та повертає (мітка, id)."""
    from database.session import variety_options
    opts = variety_options(lookups)
    if not opts:
        st.warning("Активних сортів не знайдено.")
        return "", 0
    lbl = st.selectbox(label, list(opts.keys()))
    return lbl, opts[lbl]


def season_selector(label: str, lookups: dict) -> tuple:
    """Рендерить список сезонів та повертає (назва, id)."""
    from database.session import season_options
    opts = season_options(lookups)
    if not opts:
        st.warning("Сезони не знайдено.")
        return "", 0
    name = st.selectbox(label, list(opts.keys()))
    return name, opts[name]
