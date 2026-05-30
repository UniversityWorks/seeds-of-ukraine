

import streamlit as st
from datetime import date

from database.queries    import (crud_insert_variety, crud_update_variety,
                                  crud_archive_variety, q15_varieties_with_crops)
from database.session    import (refresh_lookups, crop_options,
                                  region_options, variety_options)
from utils.error_handler import safe_query, safe_write
from ui.components.widgets import section, info


def render(cfg: dict) -> None:
    section("Управління сортами",
            "Додавання, оновлення або архівування сортів насіння. "
            "Усі зміни автоматично відображаються у журналі аудиту.")

    lookups = st.session_state.lookups
    crops   = crop_options(lookups)
    regions = region_options(lookups)
    vars_   = variety_options(lookups)

    mode = st.radio(
        "",
        ["Додати новий сорт", "Редагувати існуючий сорт", "Архівувати сорт"],
        horizontal=True,
    )

    if mode == "Додати новий сорт":
        st.markdown("---")
        with st.form("form_add_variety", clear_on_submit=True):
            st.markdown("**Дані нового сорту**")
            col1, col2 = st.columns(2)

            with col1:
                v_name    = st.text_input("Назва сорту *")
                v_crop    = st.selectbox("Культура *",   list(crops.keys()))
                v_region  = st.selectbox("Регіон *",     list(regions.keys()))
                v_planted = st.date_input("Дата посіву", value=date.today())

            with col2:
                v_growth   = st.number_input("Цикл росту (днів) *",
                                              min_value=1, max_value=500, value=90)
                v_interval = st.number_input("Інтервал поливу (днів) *",
                                              min_value=1, max_value=90, value=7)
                v_volume   = st.number_input("Обсяг поливу (мл/м2) *",
                                              min_value=10.0, max_value=20000.0,
                                              value=3500.0, step=100.0)
                v_germ     = st.number_input("Схожість (%) *",
                                              min_value=0.0, max_value=100.0,
                                              value=85.0, step=0.5)

            v_notes   = st.text_area("Примітки (необов'язково)")
            submitted = st.form_submit_button("Зберегти сорт",
                                              use_container_width=True)

        if submitted:
            if not v_name.strip():
                st.warning("Назва сорту є обов'язковою.")
            elif not crops or not regions:
                st.warning("Культури або регіони не знайдено. Спершу наповніть базу даних.")
            else:
                new_id = safe_write(crud_insert_variety, cfg, {
                    "variety_name":        v_name.strip(),
                    "crop_id":             crops[v_crop],
                    "region_id":           regions[v_region],
                    "growth_cycle_days":   int(v_growth),
                    "water_interval_days": int(v_interval),
                    "water_volume_ml_sqm": float(v_volume),
                    "germination_rate_pct":float(v_germ),
                    "planted_on":          str(v_planted),
                    "notes":               v_notes.strip() or None,
                })
                if new_id:
                    st.success(
                        f"Сорт '{v_name}' успішно додано "
                        f"(ID: {new_id}). Журнал аудиту оновлено."
                    )
                    st.session_state.lookups = refresh_lookups(cfg)
                    st.rerun()

    elif mode == "Редагувати існуючий сорт":
        st.markdown("---")
        if not vars_:
            st.info("Активних сортів не знайдено.")
            return

        sel_label = st.selectbox("Оберіть сорт для редагування", list(vars_.keys()))
        vid       = vars_[sel_label]

        df_all = safe_query(q15_varieties_with_crops, cfg)
        import pandas as _pd
        row    = (df_all[df_all["variety_id"] == vid]
                  if not df_all.empty and "variety_id" in df_all.columns
                  else _pd.DataFrame())

        def _val(col, default):
            return row[col].iloc[0] if not row.empty and col in row.columns else default

        with st.form("form_edit_variety"):
            col1, col2 = st.columns(2)
            with col1:
                ev_name     = st.text_input("Назва сорту",
                                             value=_val("Variety", sel_label.split(" (")[0]))
                ev_growth   = st.number_input("Цикл росту (днів)",
                                               min_value=1, max_value=500,
                                               value=int(_val("Growth Cycle (Days)", 90)))
                ev_interval = st.number_input("Інтервал поливу (днів)",
                                               min_value=1, max_value=90, value=7)
            with col2:
                ev_volume   = st.number_input("Обсяг поливу (мл/м2)",
                                               min_value=10.0, max_value=20000.0,
                                               value=3500.0, step=100.0)
                ev_germ     = st.number_input("Схожість (%)",
                                               min_value=0.0, max_value=100.0,
                                               value=85.0, step=0.5)
                ev_active   = st.checkbox("Активний", value=True)

            ev_notes = st.text_area("Примітки")
            upd_btn  = st.form_submit_button("Зберегти зміни",
                                              use_container_width=True)

        if upd_btn:
            rows = safe_write(crud_update_variety, cfg, vid, {
                "variety_name":        ev_name.strip(),
                "growth_cycle_days":   int(ev_growth),
                "water_interval_days": int(ev_interval),
                "water_volume_ml_sqm": float(ev_volume),
                "germination_rate_pct":float(ev_germ),
                "notes":               ev_notes.strip() or None,
                "is_active":           ev_active,
            })
            if rows:
                st.success("Сорт оновлено. Зміни зафіксовано у журналі аудиту.")
                st.session_state.lookups = refresh_lookups(cfg)
                st.rerun()
            else:
                st.warning("Змін не збережено.")

    else:
        st.markdown("---")
        if not vars_:
            st.info("Активних сортів для архівування не знайдено.")
            return

        info(
            "<strong>Архівування</strong> позначає сорт як неактивний. "
            "Він залишається доступним для历ретроспективної аналітики, але "
            "виключається з активних представлень планування. "
            "Дія фіксується автоматично."
        )

        arc_label  = st.selectbox("Оберіть сорт для архівування", list(vars_.keys()))
        arc_vid    = vars_[arc_label]
        short_name = arc_label.split(" (")[0].strip()

        if st.button(f"Архівувати '{short_name}'"):
            rows = safe_write(crud_archive_variety, cfg, arc_vid)
            if rows:
                st.success(f"'{short_name}' архівовано. Журнал аудиту оновлено.")
                st.session_state.lookups = refresh_lookups(cfg)
                st.rerun()
            else:
                st.warning("Архівування не вдалось — сорт вже може бути неактивним.")
