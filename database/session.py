"""
database/session.py
===================
Session-level helpers that sit between the raw connection layer
(database/connection.py) and the Streamlit app shell (app.py).

Responsibilities:
  • ping()           — thin wrapper so app.py doesn't import from connection.py directly.
  • refresh_lookups()— build the lookup dict (crops, regions, seasons, varieties)
                       that populates every dropdown in the UI.

The lookup dict is stored in st.session_state.lookups and refreshed
whenever a write operation mutates the underlying tables.
"""

import pandas as pd
from database.connection import ping as _ping, fetch


# ─────────────────────────────────────────────────────────────────────────────
# Connectivity
# ─────────────────────────────────────────────────────────────────────────────

def ping(cfg: dict) -> bool:
    """
    Test database connectivity.  Returns True on success, False on any error.
    Intentionally swallows all exceptions so the UI can render a friendly
    message rather than an unhandled traceback.
    """
    try:
        return _ping(cfg)
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Lookup tables
# ─────────────────────────────────────────────────────────────────────────────

def refresh_lookups(cfg: dict) -> dict:
    """
    Fetch all reference / lookup data needed to populate UI dropdowns.

    Returns a dict with four keys:
      crops     — DataFrame(crop_id, crop_name)
      regions   — DataFrame(region_id, region_name)
      seasons   — DataFrame(season_id, season_name)
      varieties — DataFrame(variety_id, label)   where label = "Name (Crop)"
    """
    crops = fetch(
        cfg,
        "SELECT crop_id, crop_name FROM crops WHERE is_active ORDER BY crop_name;",
    )
    regions = fetch(
        cfg,
        "SELECT region_id, region_name FROM regions ORDER BY region_name;",
    )
    seasons = fetch(
        cfg,
        "SELECT season_id, season_name FROM seasons ORDER BY season_id;",
    )
    varieties = fetch(
        cfg,
        """
        SELECT sv.variety_id,
               sv.variety_name || ' (' || c.crop_name || ')' AS label
        FROM   seed_varieties sv
        JOIN   crops c ON c.crop_id = sv.crop_id
        WHERE  sv.is_active
        ORDER  BY sv.variety_name;
        """,
    )
    return {
        "crops":     crops,
        "regions":   regions,
        "seasons":   seasons,
        "varieties": varieties,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Convenience accessors (thin wrappers used by page modules)
# ─────────────────────────────────────────────────────────────────────────────

def crop_options(lookups: dict) -> dict:
    """Return {crop_name: crop_id} dict for selectbox widgets."""
    df = lookups.get("crops", pd.DataFrame())
    if df.empty:
        return {}
    return dict(zip(df["crop_name"], df["crop_id"]))


def region_options(lookups: dict) -> dict:
    """Return {region_name: region_id} dict for selectbox widgets."""
    df = lookups.get("regions", pd.DataFrame())
    if df.empty:
        return {}
    return dict(zip(df["region_name"], df["region_id"]))


def season_options(lookups: dict) -> dict:
    """Return {season_name: season_id} dict for selectbox widgets."""
    df = lookups.get("seasons", pd.DataFrame())
    if df.empty:
        return {}
    return dict(zip(df["season_name"], df["season_id"]))


def variety_options(lookups: dict) -> dict:
    """Return {label: variety_id} dict for selectbox widgets."""
    df = lookups.get("varieties", pd.DataFrame())
    if df.empty:
        return {}
    return dict(zip(df["label"], df["variety_id"]))
