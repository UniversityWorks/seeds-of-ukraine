"""
app.py — Насіння України
========================
Точка входу. Запуск:  streamlit run app.py

Цей файл виконує рівно три дії:
  1. Встановлює глобальну конфігурацію сторінки Streamlit.
  2. Ініціалізує оболонку застосунку (бокова панель + заголовок).
  3. Делегує кожну вкладку власному модулю сторінки у ui/pages/.
"""

import streamlit as st

st.set_page_config(
    page_title="Насіння України",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

from config.settings   import build_db_config
from database.session  import ping, refresh_lookups
from ui.components.shell import render_sidebar, render_header, render_not_connected
from ui.pages import (
    overview,
    catalogue,
    yield_intelligence,
    care_planner,
    advanced_analytics,
    manage_varieties,
    record_harvest,
    activity_log,
)

db_config = render_sidebar()

if "connected" not in st.session_state:
    st.session_state.connected = False
if "lookups" not in st.session_state:
    st.session_state.lookups = None

config_key = str(db_config)
if st.session_state.get("_last_config") != config_key:
    st.session_state._last_config = config_key
    if ping(db_config):
        st.session_state.connected = True
        st.session_state.lookups   = refresh_lookups(db_config)
    else:
        st.session_state.connected = False

render_header()

if not st.session_state.connected:
    render_not_connected()
    st.stop()

tabs = st.tabs([
    "Огляд",
    "Каталог сортів",
    "Аналітика врожайності",
    "Планувальник догляду",
    "Розширена аналітика",
    "Управління сортами",
    "Реєстрація врожаю",
    "Журнал аудиту",
])

with tabs[0]: overview.render(db_config)
with tabs[1]: catalogue.render(db_config)
with tabs[2]: yield_intelligence.render(db_config)
with tabs[3]: care_planner.render(db_config)
with tabs[4]: advanced_analytics.render(db_config)
with tabs[5]: manage_varieties.render(db_config)
with tabs[6]: record_harvest.render(db_config)
with tabs[7]: activity_log.render(db_config)
