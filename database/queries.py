"""
database/queries.py
===================
All 27 mandatory SQL query functions, plus the stored-procedure caller
and CRUD helpers.  Every function returns a pandas DataFrame or a scalar.

Naming convention:
  q01_…  through  q27_…   — the 27 mandatory analytical queries
  sp_…                    — stored-procedure / function calls
  crud_…                  — Create / Update / Delete helpers

No Streamlit imports.  No UI logic.  Pure data access.
"""

import pandas as pd
from database.connection import fetch, execute, execute_returning


# ═══════════════════════════════════════════════════════════════════════════
# Q01  Simple SELECT
# Business: View all active crop types in the catalogue
# ═══════════════════════════════════════════════════════════════════════════
def q01_active_crops(cfg: dict) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            c.crop_id,
            c.crop_name        AS "Crop Name",
            c.crop_family      AS "Plant Family",
            s.season_name      AS "Primary Season",
            c.is_active        AS "Active"
        FROM  crops c
        LEFT JOIN seasons s ON s.season_id = c.season_id
        WHERE c.is_active = TRUE
        ORDER BY c.crop_name;
    """)


# ═══════════════════════════════════════════════════════════════════════════
# Q02  BETWEEN … AND
# Business: Filter varieties with growth cycles between N and M days
# ═══════════════════════════════════════════════════════════════════════════
def q02_growth_cycle_range(cfg: dict,
                            min_days: int = 60,
                            max_days: int = 90) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            sv.variety_id,
            sv.variety_name          AS "Variety",
            c.crop_name              AS "Crop",
            sv.growth_cycle_days     AS "Growth Cycle (Days)",
            r.region_name            AS "Region"
        FROM  seed_varieties sv
        JOIN  crops   c ON c.crop_id   = sv.crop_id
        JOIN  regions r ON r.region_id = sv.region_id
        WHERE sv.growth_cycle_days BETWEEN %(min_days)s AND %(max_days)s
          AND sv.is_active = TRUE
        ORDER BY sv.growth_cycle_days;
    """, {"min_days": min_days, "max_days": max_days})


# ═══════════════════════════════════════════════════════════════════════════
# Q03  IN operator
# Business: Filter yield records for a specific set of target regions
# ═══════════════════════════════════════════════════════════════════════════
def q03_yield_by_target_regions(cfg: dict,
                                 region_names: list) -> pd.DataFrame:
    if not region_names:
        return pd.DataFrame()
    placeholders = ",".join(["%s"] * len(region_names))
    return fetch(cfg, f"""
        SELECT
            sv.variety_name          AS "Variety",
            c.crop_name              AS "Crop",
            r.region_name            AS "Region",
            s.season_name            AS "Season",
            yr.harvest_year          AS "Harvest Year",
            yr.yield_tons_ha         AS "Yield (t/ha)",
            yr.area_ha               AS "Area (ha)",
            yr.quality_score         AS "Quality Score"
        FROM  yield_records yr
        JOIN  seed_varieties sv ON sv.variety_id = yr.variety_id
        JOIN  crops          c  ON c.crop_id     = sv.crop_id
        JOIN  regions        r  ON r.region_id   = yr.region_id
        JOIN  seasons        s  ON s.season_id   = yr.season_id
        WHERE r.region_name IN ({placeholders})
        ORDER BY yr.harvest_year DESC, yr.yield_tons_ha DESC;
    """, region_names)


# ═══════════════════════════════════════════════════════════════════════════
# Q04  LIKE
# Business: Search varieties by keyword in variety name
# ═══════════════════════════════════════════════════════════════════════════
def q04_search_varieties_by_keyword(cfg: dict,
                                     keyword: str) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            sv.variety_id,
            sv.variety_name          AS "Variety",
            c.crop_name              AS "Crop",
            r.region_name            AS "Region",
            sv.growth_cycle_days     AS "Growth Cycle (Days)",
            sv.germination_rate_pct  AS "Germination Rate (%)"
        FROM  seed_varieties sv
        JOIN  crops   c ON c.crop_id   = sv.crop_id
        JOIN  regions r ON r.region_id = sv.region_id
        WHERE LOWER(sv.variety_name) LIKE LOWER(%(kw)s)
        ORDER BY sv.variety_name;
    """, {"kw": f"%{keyword}%"})


# ═══════════════════════════════════════════════════════════════════════════
# Q05  Two conditions combined with AND
# Business: Active varieties of a crop with germination rate above threshold
# ═══════════════════════════════════════════════════════════════════════════
def q05_active_high_germination(cfg: dict,
                                 crop_name: str = "Sunflower",
                                 min_rate: float = 90.0) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            sv.variety_name          AS "Variety",
            c.crop_name              AS "Crop",
            sv.germination_rate_pct  AS "Germination Rate (%)",
            sv.growth_cycle_days     AS "Growth Cycle (Days)",
            r.region_name            AS "Region"
        FROM  seed_varieties sv
        JOIN  crops   c ON c.crop_id   = sv.crop_id
        JOIN  regions r ON r.region_id = sv.region_id
        WHERE sv.is_active = TRUE
          AND sv.germination_rate_pct > %(min_rate)s
          AND c.crop_name = %(crop_name)s
        ORDER BY sv.germination_rate_pct DESC;
    """, {"min_rate": min_rate, "crop_name": crop_name})


# ═══════════════════════════════════════════════════════════════════════════
# Q06  Two conditions combined with OR
# Business: Varieties in Steppe OR Forest-Steppe climate zones
# ═══════════════════════════════════════════════════════════════════════════
def q06_steppe_or_forest_steppe(cfg: dict) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            sv.variety_name    AS "Variety",
            c.crop_name        AS "Crop",
            r.region_name      AS "Region",
            cz.zone_name       AS "Climate Zone",
            sv.planted_on      AS "Planted On"
        FROM  seed_varieties sv
        JOIN  crops         c  ON c.crop_id   = sv.crop_id
        JOIN  regions       r  ON r.region_id = sv.region_id
        JOIN  climate_zones cz ON cz.zone_id  = r.zone_id
        WHERE cz.zone_name = 'Steppe'
           OR cz.zone_name = 'Forest-Steppe'
        ORDER BY cz.zone_name, sv.variety_name;
    """)


# ═══════════════════════════════════════════════════════════════════════════
# Q07  DISTINCT
# Business: Unique climate zones that host at least one active variety
# ═══════════════════════════════════════════════════════════════════════════
def q07_distinct_climate_zones(cfg: dict) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT DISTINCT
            cz.zone_name    AS "Climate Zone",
            cz.description  AS "Description"
        FROM  seed_varieties sv
        JOIN  regions       r  ON r.region_id = sv.region_id
        JOIN  climate_zones cz ON cz.zone_id  = r.zone_id
        WHERE sv.is_active = TRUE
        ORDER BY cz.zone_name;
    """)


# ═══════════════════════════════════════════════════════════════════════════
# Q08  MIN / MAX
# Business: Maximum and minimum yield ever recorded
# ═══════════════════════════════════════════════════════════════════════════
def q08_max_min_yield(cfg: dict) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            MAX(yr.yield_tons_ha) AS "Peak Yield (t/ha)",
            MIN(yr.yield_tons_ha) AS "Lowest Yield (t/ha)"
        FROM  yield_records yr;
    """)


# ═══════════════════════════════════════════════════════════════════════════
# Q09  SUM / AVG
# Business: Average watering volume and total cultivated area per crop
# ═══════════════════════════════════════════════════════════════════════════
def q09_avg_water_volume_per_crop(cfg: dict) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            c.crop_name                           AS "Crop",
            ROUND(AVG(sv.water_volume_ml_sqm), 2) AS "Avg Water Volume (ml/sqm)",
            ROUND(SUM(yr.area_ha), 2)             AS "Total Area (ha)"
        FROM  seed_varieties sv
        JOIN  crops         c  ON c.crop_id    = sv.crop_id
        LEFT JOIN yield_records yr ON yr.variety_id = sv.variety_id
        GROUP BY c.crop_name
        ORDER BY "Avg Water Volume (ml/sqm)" DESC;
    """)


# ═══════════════════════════════════════════════════════════════════════════
# Q10  COUNT
# Business: Total registered variety counts (all / active / archived)
# ═══════════════════════════════════════════════════════════════════════════
def q10_count_varieties(cfg: dict) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            COUNT(*)                              AS "Total Varieties",
            COUNT(*) FILTER (WHERE is_active)     AS "Active Varieties",
            COUNT(*) FILTER (WHERE NOT is_active) AS "Archived Varieties"
        FROM seed_varieties;
    """)


# ═══════════════════════════════════════════════════════════════════════════
# Q11  Aggregate + regular fields with GROUP BY
# Business: Average yield per variety across all recorded seasons
# ═══════════════════════════════════════════════════════════════════════════
def q11_avg_yield_per_variety(cfg: dict) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            sv.variety_name                       AS "Variety",
            c.crop_name                           AS "Crop",
            COUNT(yr.yield_id)                    AS "Harvest Records",
            ROUND(AVG(yr.yield_tons_ha), 2)       AS "Avg Yield (t/ha)",
            ROUND(SUM(yr.area_ha), 2)             AS "Total Area (ha)"
        FROM  seed_varieties sv
        JOIN  crops         c  ON c.crop_id    = sv.crop_id
        JOIN  yield_records yr ON yr.variety_id = sv.variety_id
        GROUP BY sv.variety_name, c.crop_name
        ORDER BY "Avg Yield (t/ha)" DESC;
    """)


# ═══════════════════════════════════════════════════════════════════════════
# Q12  Aggregate + WHERE on a standard field
# Business: Avg yield in a given crop family for harvests from a min year
# ═══════════════════════════════════════════════════════════════════════════
def q12_avg_yield_by_family_and_year(cfg: dict,
                                      crop_family: str = "Poaceae",
                                      min_year: int = 2023) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            sv.variety_name                 AS "Variety",
            c.crop_family                   AS "Plant Family",
            yr.harvest_year                 AS "Year",
            ROUND(AVG(yr.yield_tons_ha), 2) AS "Avg Yield (t/ha)"
        FROM  seed_varieties sv
        JOIN  crops         c  ON c.crop_id    = sv.crop_id
        JOIN  yield_records yr ON yr.variety_id = sv.variety_id
        WHERE c.crop_family  = %(family)s
          AND yr.harvest_year >= %(min_year)s
        GROUP BY sv.variety_name, c.crop_family, yr.harvest_year
        ORDER BY yr.harvest_year DESC, "Avg Yield (t/ha)" DESC;
    """, {"family": crop_family, "min_year": min_year})


# ═══════════════════════════════════════════════════════════════════════════
# Q13  Aggregate + HAVING
# Business: Crops whose average quality score exceeds a threshold
# ═══════════════════════════════════════════════════════════════════════════
def q13_high_quality_crops(cfg: dict,
                             min_quality: float = 8.0) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            c.crop_name                     AS "Crop",
            ROUND(AVG(yr.quality_score), 2) AS "Avg Quality Score",
            COUNT(yr.yield_id)              AS "Harvest Records"
        FROM  crops         c
        JOIN  seed_varieties sv ON sv.crop_id    = c.crop_id
        JOIN  yield_records  yr ON yr.variety_id = sv.variety_id
        GROUP BY c.crop_name
        HAVING AVG(yr.quality_score) > %(min_quality)s
        ORDER BY "Avg Quality Score" DESC;
    """, {"min_quality": min_quality})


# ═══════════════════════════════════════════════════════════════════════════
# Q14  Aggregate + HAVING + WHERE + ORDER BY
# Business: Regions with avg yield above threshold in a specific harvest year
# ═══════════════════════════════════════════════════════════════════════════
def q14_high_yield_regions_by_year(cfg: dict,
                                    harvest_year: int = 2023,
                                    min_avg_yield: float = 5.0) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            r.region_name                   AS "Region",
            yr.harvest_year                 AS "Year",
            ROUND(AVG(yr.yield_tons_ha), 2) AS "Avg Yield (t/ha)",
            COUNT(yr.yield_id)              AS "Varieties Tracked"
        FROM  yield_records yr
        JOIN  regions r ON r.region_id = yr.region_id
        WHERE yr.harvest_year = %(year)s
        GROUP BY r.region_name, yr.harvest_year
        HAVING AVG(yr.yield_tons_ha) > %(min_avg)s
        ORDER BY "Avg Yield (t/ha)" DESC;
    """, {"year": harvest_year, "min_avg": min_avg_yield})


# ═══════════════════════════════════════════════════════════════════════════
# Q15  INNER JOIN
# Business: Full variety catalogue joined with crop and season data
# ═══════════════════════════════════════════════════════════════════════════
def q15_varieties_with_crops(cfg: dict) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            sv.variety_id,
            sv.variety_name              AS "Variety",
            c.crop_name                  AS "Crop",
            c.crop_family                AS "Family",
            s.season_name                AS "Primary Season",
            sv.growth_cycle_days         AS "Growth Cycle (Days)",
            sv.water_interval_days       AS "Watering Every (Days)",
            sv.germination_rate_pct      AS "Germination Rate (%)",
            sv.planted_on                AS "Planted On",
            sv.is_active                 AS "Active"
        FROM  seed_varieties sv
        INNER JOIN crops   c ON c.crop_id   = sv.crop_id
        INNER JOIN seasons s ON s.season_id = c.season_id
        ORDER BY c.crop_name, sv.variety_name;
    """)


# ═══════════════════════════════════════════════════════════════════════════
# Q16  LEFT JOIN
# Business: Varieties with no care log entries (never tended — flag them)
# ═══════════════════════════════════════════════════════════════════════════
def q16_unmanaged_varieties(cfg: dict) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            sv.variety_name   AS "Variety",
            c.crop_name       AS "Crop",
            r.region_name     AS "Region",
            sv.planted_on     AS "Planted On",
            csl.log_id        AS "Care Log ID"
        FROM  seed_varieties sv
        INNER JOIN crops   c   ON c.crop_id    = sv.crop_id
        INNER JOIN regions r   ON r.region_id  = sv.region_id
        LEFT  JOIN care_schedule_log csl
               ON  csl.variety_id = sv.variety_id
        WHERE csl.log_id IS NULL
          AND sv.is_active = TRUE
        ORDER BY sv.planted_on;
    """)


# ═══════════════════════════════════════════════════════════════════════════
# Q17  RIGHT JOIN
# Business: All regions including those with no varieties assigned yet
# ═══════════════════════════════════════════════════════════════════════════
def q17_regions_all_with_varieties(cfg: dict) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            r.region_name     AS "Region",
            r.oblast          AS "Oblast",
            cz.zone_name      AS "Climate Zone",
            sv.variety_name   AS "Assigned Variety"
        FROM  seed_varieties sv
        RIGHT JOIN regions       r  ON r.region_id = sv.region_id
        LEFT  JOIN climate_zones cz ON cz.zone_id  = r.zone_id
        ORDER BY r.region_name, sv.variety_name;
    """)


# ═══════════════════════════════════════════════════════════════════════════
# Q18  INNER JOIN + WHERE condition
# Business: Fast-maturing varieties (< max_days) in southern climate zones
# ═══════════════════════════════════════════════════════════════════════════
def q18_short_cycle_southern(cfg: dict,
                               max_days: int = 100) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            sv.variety_name      AS "Variety",
            c.crop_name          AS "Crop",
            sv.growth_cycle_days AS "Growth Cycle (Days)",
            r.region_name        AS "Region",
            cz.zone_name         AS "Climate Zone"
        FROM  seed_varieties sv
        INNER JOIN crops        c  ON c.crop_id   = sv.crop_id
        INNER JOIN regions      r  ON r.region_id = sv.region_id
        INNER JOIN climate_zones cz ON cz.zone_id  = r.zone_id
        WHERE sv.growth_cycle_days < %(max_days)s
          AND cz.zone_name IN ('Steppe', 'Black Sea Coast', 'Azov Steppe')
        ORDER BY sv.growth_cycle_days;
    """, {"max_days": max_days})


# ═══════════════════════════════════════════════════════════════════════════
# Q19  INNER JOIN + LIKE
# Business: Varieties and yields in regions whose name contains a keyword
# ═══════════════════════════════════════════════════════════════════════════
def q19_join_region_like(cfg: dict,
                          keyword: str = "Dnipro") -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            r.region_name     AS "Region",
            sv.variety_name   AS "Variety",
            c.crop_name       AS "Crop",
            yr.harvest_year   AS "Year",
            yr.yield_tons_ha  AS "Yield (t/ha)"
        FROM  regions r
        INNER JOIN seed_varieties sv ON sv.region_id  = r.region_id
        INNER JOIN crops          c  ON c.crop_id     = sv.crop_id
        INNER JOIN yield_records  yr ON yr.variety_id = sv.variety_id
        WHERE r.region_name ILIKE %(kw)s
        ORDER BY yr.harvest_year DESC;
    """, {"kw": f"%{keyword}%"})


# ═══════════════════════════════════════════════════════════════════════════
# Q20  INNER JOIN + aggregate
# Business: Total harvest tonnage and cultivated area per region
# ═══════════════════════════════════════════════════════════════════════════
def q20_total_yield_per_region(cfg: dict) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            r.region_name                               AS "Region",
            COUNT(DISTINCT sv.variety_id)               AS "Varieties",
            ROUND(SUM(yr.yield_tons_ha * yr.area_ha), 2) AS "Total Harvest (t)",
            ROUND(SUM(yr.area_ha), 2)                   AS "Total Area (ha)"
        FROM  regions r
        INNER JOIN seed_varieties sv ON sv.region_id  = r.region_id
        INNER JOIN yield_records  yr ON yr.variety_id = sv.variety_id
        GROUP BY r.region_name
        ORDER BY "Total Harvest (t)" DESC;
    """)


# ═══════════════════════════════════════════════════════════════════════════
# Q21  INNER JOIN + aggregate + HAVING
# Business: Climate zones where avg germination rate falls below threshold
# ═══════════════════════════════════════════════════════════════════════════
def q21_underperforming_zones(cfg: dict,
                               threshold: float = 90.0) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            cz.zone_name                           AS "Climate Zone",
            ROUND(AVG(sv.germination_rate_pct), 2) AS "Avg Germination Rate (%)",
            COUNT(sv.variety_id)                   AS "Varieties in Zone"
        FROM  climate_zones cz
        INNER JOIN regions       r  ON r.zone_id   = cz.zone_id
        INNER JOIN seed_varieties sv ON sv.region_id = r.region_id
        GROUP BY cz.zone_name
        HAVING AVG(sv.germination_rate_pct) < %(threshold)s
        ORDER BY "Avg Germination Rate (%)";
    """, {"threshold": threshold})


# ═══════════════════════════════════════════════════════════════════════════
# Q22  Subquery with comparison operator
# Business: Varieties whose growth cycle exceeds the fleet-wide average
# ═══════════════════════════════════════════════════════════════════════════
def q22_above_avg_growth_cycle(cfg: dict) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            sv.variety_name      AS "Variety",
            c.crop_name          AS "Crop",
            sv.growth_cycle_days AS "Growth Cycle (Days)",
            r.region_name        AS "Region"
        FROM  seed_varieties sv
        JOIN  crops   c ON c.crop_id   = sv.crop_id
        JOIN  regions r ON r.region_id = sv.region_id
        WHERE sv.growth_cycle_days > (
            SELECT AVG(growth_cycle_days)
            FROM   seed_varieties
            WHERE  is_active = TRUE
        )
        ORDER BY sv.growth_cycle_days DESC;
    """)


# ═══════════════════════════════════════════════════════════════════════════
# Q23  Subquery with aggregate function
# Business: Varieties with at least one harvest record above the global avg
# ═══════════════════════════════════════════════════════════════════════════
def q23_above_avg_yield_varieties(cfg: dict) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            sv.variety_name   AS "Variety",
            c.crop_name       AS "Crop",
            yr.harvest_year   AS "Year",
            yr.yield_tons_ha  AS "Yield (t/ha)"
        FROM  seed_varieties sv
        JOIN  crops         c  ON c.crop_id    = sv.crop_id
        JOIN  yield_records yr ON yr.variety_id = sv.variety_id
        WHERE yr.yield_tons_ha > (
            SELECT AVG(yield_tons_ha) FROM yield_records
        )
        ORDER BY yr.yield_tons_ha DESC;
    """)


# ═══════════════════════════════════════════════════════════════════════════
# Q24  Subquery with EXISTS
# Business: Regions that have at least one pending (uncompleted) care task
# ═══════════════════════════════════════════════════════════════════════════
def q24_regions_with_pending_care(cfg: dict) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            r.region_name AS "Region",
            r.oblast      AS "Oblast"
        FROM  regions r
        WHERE EXISTS (
            SELECT 1
            FROM   seed_varieties sv
            JOIN   care_schedule_log csl ON csl.variety_id = sv.variety_id
            WHERE  sv.region_id     = r.region_id
              AND  csl.is_completed = FALSE
        )
        ORDER BY r.region_name;
    """)


# ═══════════════════════════════════════════════════════════════════════════
# Q25  Subquery with ANY / SOME
# Business: Varieties that water more often than ANY wheat variety
# ═══════════════════════════════════════════════════════════════════════════
def q25_shorter_interval_than_any_wheat(cfg: dict) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            sv.variety_name        AS "Variety",
            c.crop_name            AS "Crop",
            sv.water_interval_days AS "Watering Interval (Days)"
        FROM  seed_varieties sv
        JOIN  crops c ON c.crop_id = sv.crop_id
        WHERE sv.water_interval_days < ANY (
            SELECT sv2.water_interval_days
            FROM   seed_varieties sv2
            JOIN   crops c2 ON c2.crop_id = sv2.crop_id
            WHERE  c2.crop_name LIKE '%Wheat%'
        )
        ORDER BY sv.water_interval_days;
    """)


# ═══════════════════════════════════════════════════════════════════════════
# Q26  Subquery with IN
# Business: Varieties planted in Polissia or Forest-Steppe zones
# ═══════════════════════════════════════════════════════════════════════════
def q26_polissia_and_forest_steppe(cfg: dict) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            sv.variety_name   AS "Variety",
            c.crop_name       AS "Crop",
            r.region_name     AS "Region",
            sv.planted_on     AS "Planted On"
        FROM  seed_varieties sv
        JOIN  crops   c ON c.crop_id   = sv.crop_id
        JOIN  regions r ON r.region_id = sv.region_id
        WHERE r.region_id IN (
            SELECT r2.region_id
            FROM   regions       r2
            JOIN   climate_zones cz ON cz.zone_id = r2.zone_id
            WHERE  cz.zone_name IN ('Polissia', 'Forest-Steppe')
        )
        ORDER BY r.region_name, sv.variety_name;
    """)


# ═══════════════════════════════════════════════════════════════════════════
# Q27  Subquery + INNER JOIN combined
# Business: Varieties from regions whose total harvest exceeds the national
#           per-region average
# ═══════════════════════════════════════════════════════════════════════════
def q27_varieties_in_top_yield_regions(cfg: dict) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            sv.variety_name          AS "Variety",
            c.crop_name              AS "Crop",
            r.region_name            AS "Region",
            cz.zone_name             AS "Climate Zone",
            sv.growth_cycle_days     AS "Growth Cycle (Days)",
            sv.germination_rate_pct  AS "Germination (%)"
        FROM  seed_varieties sv
        INNER JOIN crops        c  ON c.crop_id   = sv.crop_id
        INNER JOIN regions      r  ON r.region_id = sv.region_id
        INNER JOIN climate_zones cz ON cz.zone_id  = r.zone_id
        WHERE r.region_id IN (
            SELECT yr_in.region_id
            FROM   yield_records yr_in
            GROUP  BY yr_in.region_id
            HAVING SUM(yr_in.yield_tons_ha * yr_in.area_ha) > (
                SELECT AVG(regional_total)
                FROM (
                    SELECT SUM(yield_tons_ha * area_ha) AS regional_total
                    FROM   yield_records
                    GROUP  BY region_id
                ) sub
            )
        )
        ORDER BY r.region_name, sv.variety_name;
    """)


# ═══════════════════════════════════════════════════════════════════════════
# STORED PROCEDURE CALL
# Business: "Task Scheduler — Watering & Care Reminders"
# ═══════════════════════════════════════════════════════════════════════════
def sp_watering_reminders(cfg: dict,
                           horizon_days: int = 7) -> pd.DataFrame:
    return fetch(cfg, """
        SELECT
            variety_name        AS "Variety",
            crop_name           AS "Crop",
            region_name         AS "Region",
            next_watering_date  AS "Next Watering Date",
            water_volume_ml_sqm AS "Volume (ml/sqm)"
        FROM sp_generate_watering_reminders(%(horizon)s)
        ORDER BY next_watering_date;
    """, {"horizon": horizon_days})


# ═══════════════════════════════════════════════════════════════════════════
# CRUD — Varieties
# ═══════════════════════════════════════════════════════════════════════════

def crud_insert_variety(cfg: dict, data: dict) -> int:
    """Insert a new seed variety; the audit trigger fires automatically."""
    return execute_returning(cfg, """
        INSERT INTO seed_varieties
            (variety_name, crop_id, region_id, growth_cycle_days,
             water_interval_days, water_volume_ml_sqm,
             germination_rate_pct, planted_on, notes)
        VALUES
            (%(variety_name)s, %(crop_id)s, %(region_id)s,
             %(growth_cycle_days)s, %(water_interval_days)s,
             %(water_volume_ml_sqm)s, %(germination_rate_pct)s,
             %(planted_on)s, %(notes)s)
        RETURNING variety_id;
    """, data)


def crud_update_variety(cfg: dict, variety_id: int, data: dict) -> int:
    """Update editable fields of a seed variety; audit trigger fires automatically."""
    data["variety_id"] = variety_id
    return execute(cfg, """
        UPDATE seed_varieties
        SET variety_name         = %(variety_name)s,
            growth_cycle_days    = %(growth_cycle_days)s,
            water_interval_days  = %(water_interval_days)s,
            water_volume_ml_sqm  = %(water_volume_ml_sqm)s,
            germination_rate_pct = %(germination_rate_pct)s,
            notes                = %(notes)s,
            is_active            = %(is_active)s
        WHERE variety_id = %(variety_id)s;
    """, data)


def crud_archive_variety(cfg: dict, variety_id: int) -> int:
    """Soft-delete: mark variety inactive; audit trigger fires automatically."""
    return execute(cfg,
        "UPDATE seed_varieties SET is_active = FALSE WHERE variety_id = %s;",
        (variety_id,))


# ═══════════════════════════════════════════════════════════════════════════
# CRUD — Yield records
# ═══════════════════════════════════════════════════════════════════════════

def crud_insert_yield(cfg: dict, data: dict) -> int:
    """Insert a new harvest yield record."""
    return execute_returning(cfg, """
        INSERT INTO yield_records
            (variety_id, region_id, season_id, harvest_year,
             yield_tons_ha, area_ha, quality_score)
        VALUES
            (%(variety_id)s, %(region_id)s, %(season_id)s, %(harvest_year)s,
             %(yield_tons_ha)s, %(area_ha)s, %(quality_score)s)
        RETURNING yield_id;
    """, data)


# ═══════════════════════════════════════════════════════════════════════════
# Activity log (audit trail)
# ═══════════════════════════════════════════════════════════════════════════

def fetch_activity_log(cfg: dict, limit: int = 100) -> pd.DataFrame:
    """Retrieve the most recent audit history entries."""
    return fetch(cfg, """
        SELECT
            avh.audit_id      AS "ID",
            avh.variety_id    AS "Variety ID",
            sv.variety_name   AS "Variety",
            avh.operation     AS "Action",
            avh.changed_field AS "Field Changed",
            avh.old_value     AS "Previous Value",
            avh.new_value     AS "New Value",
            avh.changed_by    AS "Changed By",
            avh.changed_at    AS "Timestamp"
        FROM  audit_variety_history avh
        LEFT JOIN seed_varieties sv ON sv.variety_id = avh.variety_id
        ORDER BY avh.changed_at DESC
        LIMIT %(limit)s;
    """, {"limit": limit})
