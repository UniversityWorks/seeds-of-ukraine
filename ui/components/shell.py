"""
ui/components/shell.py
======================
Компоненти оболонки застосунку:
  render_sidebar()       — форма підключення у боковій панелі; повертає db_config.
  render_header()        — широкий заголовок-банер угорі кожної сторінки.
  render_not_connected() — екран-шлюз до встановлення з'єднання.
"""

import streamlit as st
from config.styles   import GLOBAL_CSS
from config.settings import (
    APP_NAME,APP_TAGLINE,
    DEFAULT_DB_HOST, DEFAULT_DB_PORT, DEFAULT_DB_NAME,
    DEFAULT_DB_USER, DEFAULT_DB_PASSWORD,
    build_db_config,
)


def render_sidebar() -> dict:
    """
    Відображає панель підключення та вводить глобальний CSS.
    Повертає словник db_config зі значень форми.
    """
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f"""
        <div style='text-align:center; padding:1.5rem 0 1rem;'>
            <div style='font-family:Playfair Display,serif; font-size:1.15rem;
                        color:#f5e6aa; font-weight:700; margin-top:0.5rem;'>
                {APP_NAME}
            </div>
            <div style='font-size:0.7rem; color:#7ac99a; letter-spacing:0.08em;
                        text-transform:uppercase; margin-top:0.25rem;'>
                
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        st.markdown(
            "<div style='font-size:0.7rem;letter-spacing:0.08em;"
            "text-transform:uppercase;color:#7ac99a;margin-bottom:0.75rem;"
            "font-weight:600;'>Підключення до платформи</div>",
            unsafe_allow_html=True,
        )

        host     = st.text_input("Хост",     value=DEFAULT_DB_HOST)
        port     = st.number_input("Порт",   value=DEFAULT_DB_PORT, step=1,
                                   min_value=1, max_value=65535)
        dbname   = st.text_input("База даних", value=DEFAULT_DB_NAME)
        user     = st.text_input("Користувач", value=DEFAULT_DB_USER)
        password = st.text_input("Пароль", type="password",
                                  value=DEFAULT_DB_PASSWORD)

        st.button("Підключитися", use_container_width=True)

        st.divider()

        connected = st.session_state.get("connected", False)
        if connected:
            st.markdown(
                "<div style='text-align:center;font-size:0.75rem;"
                "color:#52b788;'>Підключено</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='text-align:center;font-size:0.75rem;"
                "color:#e57373;'>Не підключено</div>",
                unsafe_allow_html=True,
            )

        st.divider()

        st.markdown(f"""
        <div style='font-size:0.7rem;color:#7ac99a;text-align:center;padding:0.5rem;'>
            © 2024 {APP_NAME}<br>
        </div>
        """, unsafe_allow_html=True)

    return build_db_config(
        host=host,
        port=int(port),
        dbname=dbname,
        user=user,
        password=password,
    )


def render_header() -> None:
    """Відображає широкий градієнтний заголовок-банер."""
    st.markdown(f"""
    <div class="sou-header">
        <div>
            <h1 class="sou-header-title">
                {APP_NAME}
            </h1>
            <p class="sou-header-sub">{APP_TAGLINE}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_not_connected() -> None:
    """Відображає екран-шлюз при відсутності активного з'єднання."""
    st.markdown("""
    <div class="info-card" style="font-size:1rem; padding:1.5rem 2rem;">
        <strong>Відсутнє підключення до платформи.</strong><br><br>
        Введіть дані підключення у боковій панелі та натисніть
        <strong>Підключитися</strong>. Переконайтеся, що PostgreSQL
        запущено та схему застосовано:<br><br>
        <code>createdb seeds_ukraine</code><br>
        <code>psql seeds_ukraine &lt; assets/sql/schema.sql</code>
    </div>
    """, unsafe_allow_html=True)
