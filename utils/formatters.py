"""
utils/formatters.py
===================
Pure-Python display helpers used by UI components and page modules.

No Streamlit imports — these functions work in any context and are
easily unit-testable.

Fix notes (v2.0.1):
  • audit_style_df() now uses Styler.map() instead of Styler.applymap().
    pandas 2.1 deprecated applymap() on Styler and renamed it to map(),
    raising:  AttributeError: 'Styler' object has no attribute 'applymap'
    A compatibility shim is used so the code works on both pandas <2.1
    and >=2.1 without requiring a specific version pin.
"""

import pandas as pd
from config.settings import AUDIT_COLOURS


def safe_scalar(df: pd.DataFrame, col: str, default=0, cast=float):
    """
    Safely extract a single scalar value from the first row of a DataFrame.

    Parameters
    ----------
    df      : DataFrame (may be empty).
    col     : Column name to extract.
    default : Value returned when df is empty or col is missing.
    cast    : Callable applied to the raw value (e.g. float, int, str).
    """
    if df is None or df.empty or col not in df.columns:
        return default
    try:
        return cast(df[col].iloc[0])
    except (TypeError, ValueError):
        return default


def format_number(value: float, decimals: int = 2, suffix: str = "") -> str:
    """Format a float as a localised string with optional suffix."""
    try:
        return f"{value:,.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return str(value)


def metric_cards_html(cards: list[dict]) -> str:
    """
    Build the HTML string for a row of metric cards.

    Each dict in `cards` may contain:
      label  (str)  — small uppercase label above the value
      value  (str)  — large primary number or text
      delta  (str)  — small supporting line below the value
      accent (str)  — CSS modifier class: "", "gold", "earth", "dark"
    """
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
    """Return the HTML for a styled section title + optional subtitle."""
    sub = f'<div class="section-sub">{subtitle}</div>' if subtitle else ""
    return f'<div class="section-title">{title}</div>{sub}'


def info_card(body: str) -> str:
    """Return a styled info callout card HTML string."""
    return f'<div class="info-card">{body}</div>'


def reminder_pills_html(df: pd.DataFrame) -> str:
    """
    Build HTML pill badges from a watering-reminders DataFrame.
    Expected columns: "Variety", "Next Watering Date", "Volume (ml/sqm)"
    """
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
    """
    Apply colour coding to the "Action" column of the activity-log DataFrame.
    Returns a pandas Styler object ready for st.dataframe().

    Compatibility:
      pandas < 2.1  → uses Styler.applymap()  (the original name)
      pandas >= 2.1 → uses Styler.map()        (renamed in 2.1, applymap removed in 3.0)
    """
    if df is None or df.empty or "Action" not in df.columns:
        return df

    def colour_action(val: str) -> str:
        colour = AUDIT_COLOURS.get(str(val).upper(), "#aaaaaa")
        return f"color: {colour}; font-weight: bold;"

    styler = df.style

    # Detect which method exists at runtime — works across all pandas versions
    if hasattr(styler, "map"):
        # pandas >= 2.1
        return styler.map(colour_action, subset=["Action"])
    else:
        # pandas < 2.1
        return styler.applymap(colour_action, subset=["Action"])
