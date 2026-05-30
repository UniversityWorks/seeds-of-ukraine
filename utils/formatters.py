

import pandas as pd
from config.settings import AUDIT_COLOURS


def safe_scalar(df: pd.DataFrame, col: str, default=0, cast=float):
   
    if df is None or df.empty or col not in df.columns:
        return default
    try:
        return cast(df[col].iloc[0])
    except (TypeError, ValueError):
        return default


def format_number(value: float, decimals: int = 2, suffix: str = "") -> str:
    try:
        return f"{value:,.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return str(value)


def metric_cards_html(cards: list[dict]) -> str:
   
    items = []
    for c in cards:
        accent = c.get("accent", "")
        cls    = f"metric-card {accent}".strip()
        items.append(f"""
        <div class="{cls}">
            <div class="mc-label">{c.get('label','')}</div>
            <div class="mc-value">{c.get('value','—')}</div>
            <div class="mc-delta">{c.get('delta','')}</div>
        </div>
        """)
    return f'<div class="metric-row">{"".join(items)}</div>'


def section_header(title: str, subtitle: str = "") -> str:
    sub = f'<div class="section-sub">{subtitle}</div>' if subtitle else ""
    return f'<div class="section-title">{title}</div>{sub}'


def info_card(body: str) -> str:
    return f'<div class="info-card">{body}</div>'


def reminder_pills_html(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return ""
    pills = []
    for _, row in df.iterrows():
        pills.append(
            f'<span class="reminder-pill">'
            f'💧 {row.get("Variety","?")} — '
            f'{row.get("Next Watering Date","?")} '
            f'({row.get("Volume (ml/sqm)","?")} ml/sqm)'
            f'</span>'
        )
    return "".join(pills)


def audit_style_df(df: pd.DataFrame) -> "pd.io.formats.style.Styler":
    if df is None or df.empty or "Action" not in df.columns:
        return df

    def colour_action(val: str) -> str:
        colour = AUDIT_COLOURS.get(str(val).upper(), "#aaaaaa")
        return f"color: {colour}; font-weight: bold;"

    styler = df.style

    if hasattr(styler, "map"):
        return styler.map(colour_action, subset=["Action"])
    else:
        return styler.applymap(colour_action, subset=["Action"])
