


import pandas as pd
from database.connection import ping as _ping, fetch


def ping(cfg: dict) -> bool:
   
    try:
        return _ping(cfg)
    except Exception:
        return False

def refresh_lookups(cfg: dict) -> dict:
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


def crop_options(lookups: dict) -> dict:
    df = lookups.get("crops", pd.DataFrame())
    if df.empty:
        return {}
    return dict(zip(df["crop_name"], df["crop_id"]))


def region_options(lookups: dict) -> dict:
    df = lookups.get("regions", pd.DataFrame())
    if df.empty:
        return {}
    return dict(zip(df["region_name"], df["region_id"]))


def season_options(lookups: dict) -> dict:
    df = lookups.get("seasons", pd.DataFrame())
    if df.empty:
        return {}
    return dict(zip(df["season_name"], df["season_id"]))


def variety_options(lookups: dict) -> dict:
    df = lookups.get("varieties", pd.DataFrame())
    if df.empty:
        return {}
    return dict(zip(df["label"], df["variety_id"]))
