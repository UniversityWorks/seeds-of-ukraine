-- =============================================================================
-- Seeds of Ukraine — PostgreSQL Schema
-- 3NF-normalised agricultural SaaS platform
-- Version: 2.0  |  Engine: PostgreSQL 15+
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ---------------------------------------------------------------------------
-- DROP ORDER (reverse FK dependency)
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS audit_variety_history   CASCADE;
DROP TABLE IF EXISTS care_schedule_log       CASCADE;
DROP TABLE IF EXISTS yield_records           CASCADE;
DROP TABLE IF EXISTS seed_varieties          CASCADE;
DROP TABLE IF EXISTS crops                   CASCADE;
DROP TABLE IF EXISTS climate_zones           CASCADE;
DROP TABLE IF EXISTS regions                 CASCADE;
DROP TABLE IF EXISTS seasons                 CASCADE;
DROP FUNCTION IF EXISTS fn_trigger_variety_audit()            CASCADE;
DROP FUNCTION IF EXISTS sp_generate_watering_reminders(INT)   CASCADE;

-- =============================================================================
-- seasons
-- =============================================================================
CREATE TABLE seasons (
    season_id   SERIAL PRIMARY KEY,
    season_name VARCHAR(30)  NOT NULL UNIQUE,
    start_month SMALLINT     NOT NULL CHECK (start_month BETWEEN 1 AND 12),
    end_month   SMALLINT     NOT NULL CHECK (end_month   BETWEEN 1 AND 12)
);

-- =============================================================================
-- climate_zones
-- =============================================================================
CREATE TABLE climate_zones (
    zone_id     SERIAL PRIMARY KEY,
    zone_name   VARCHAR(60)  NOT NULL UNIQUE,
    description TEXT
);

-- =============================================================================
-- regions
-- =============================================================================
CREATE TABLE regions (
    region_id   SERIAL PRIMARY KEY,
    region_name VARCHAR(80)  NOT NULL UNIQUE,
    oblast      VARCHAR(80)  NOT NULL,
    zone_id     INT          NOT NULL REFERENCES climate_zones(zone_id) ON DELETE RESTRICT,
    latitude    NUMERIC(8,5),
    longitude   NUMERIC(8,5)
);
CREATE INDEX idx_regions_zone ON regions(zone_id);

-- =============================================================================
-- crops
-- =============================================================================
CREATE TABLE crops (
    crop_id     SERIAL PRIMARY KEY,
    crop_name   VARCHAR(80)  NOT NULL UNIQUE,
    crop_family VARCHAR(80),
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    season_id   INT          REFERENCES seasons(season_id) ON DELETE SET NULL
);
CREATE INDEX idx_crops_active ON crops(is_active);
CREATE INDEX idx_crops_season ON crops(season_id);

-- =============================================================================
-- seed_varieties
-- =============================================================================
CREATE TABLE seed_varieties (
    variety_id           SERIAL PRIMARY KEY,
    variety_name         VARCHAR(120) NOT NULL,
    crop_id              INT          NOT NULL REFERENCES crops(crop_id)   ON DELETE CASCADE,
    region_id            INT          NOT NULL REFERENCES regions(region_id) ON DELETE RESTRICT,
    growth_cycle_days    SMALLINT     NOT NULL CHECK (growth_cycle_days   > 0),
    water_interval_days  SMALLINT     NOT NULL CHECK (water_interval_days > 0),
    water_volume_ml_sqm  NUMERIC(8,2) NOT NULL CHECK (water_volume_ml_sqm > 0),
    germination_rate_pct NUMERIC(5,2) CHECK (germination_rate_pct BETWEEN 0 AND 100),
    planted_on           DATE,
    is_active            BOOLEAN      NOT NULL DEFAULT TRUE,
    notes                TEXT,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_variety_crop      ON seed_varieties(crop_id);
CREATE INDEX idx_variety_region    ON seed_varieties(region_id);
CREATE INDEX idx_variety_growth    ON seed_varieties(growth_cycle_days);
CREATE INDEX idx_variety_planted   ON seed_varieties(planted_on);
CREATE INDEX idx_variety_name_trgm ON seed_varieties USING GIN (variety_name gin_trgm_ops);

-- =============================================================================
-- yield_records
-- =============================================================================
CREATE TABLE yield_records (
    yield_id      SERIAL PRIMARY KEY,
    variety_id    INT          NOT NULL REFERENCES seed_varieties(variety_id) ON DELETE CASCADE,
    region_id     INT          NOT NULL REFERENCES regions(region_id)         ON DELETE RESTRICT,
    season_id     INT          NOT NULL REFERENCES seasons(season_id)         ON DELETE RESTRICT,
    harvest_year  SMALLINT     NOT NULL CHECK (harvest_year BETWEEN 1990 AND 2100),
    yield_tons_ha NUMERIC(8,3) NOT NULL CHECK (yield_tons_ha >= 0),
    area_ha       NUMERIC(10,3) NOT NULL CHECK (area_ha > 0),
    quality_score SMALLINT     CHECK (quality_score BETWEEN 1 AND 10),
    recorded_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_yield_variety ON yield_records(variety_id);
CREATE INDEX idx_yield_region  ON yield_records(region_id);
CREATE INDEX idx_yield_season  ON yield_records(season_id);
CREATE INDEX idx_yield_year    ON yield_records(harvest_year);

-- =============================================================================
-- care_schedule_log
-- =============================================================================
CREATE TABLE care_schedule_log (
    log_id         SERIAL PRIMARY KEY,
    variety_id     INT          NOT NULL REFERENCES seed_varieties(variety_id) ON DELETE CASCADE,
    care_type      VARCHAR(40)  NOT NULL DEFAULT 'watering',
    scheduled_date DATE         NOT NULL,
    completed_date DATE,
    is_completed   BOOLEAN      NOT NULL DEFAULT FALSE,
    notes          TEXT,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_care_variety   ON care_schedule_log(variety_id);
CREATE INDEX idx_care_scheduled ON care_schedule_log(scheduled_date);
CREATE INDEX idx_care_completed ON care_schedule_log(is_completed);

-- =============================================================================
-- audit_variety_history  (populated entirely by trigger)
-- =============================================================================
CREATE TABLE audit_variety_history (
    audit_id      SERIAL PRIMARY KEY,
    variety_id    INT          NOT NULL,
    operation     VARCHAR(10)  NOT NULL,
    changed_field VARCHAR(60),
    old_value     TEXT,
    new_value     TEXT,
    changed_by    VARCHAR(80)  NOT NULL DEFAULT current_user,
    changed_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audit_variety ON audit_variety_history(variety_id);
CREATE INDEX idx_audit_changed ON audit_variety_history(changed_at);

-- =============================================================================
-- TRIGGER FUNCTION: silent audit on seed_varieties
-- =============================================================================
CREATE OR REPLACE FUNCTION fn_trigger_variety_audit()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_variety_history
            (variety_id, operation, changed_field, old_value, new_value)
        VALUES (NEW.variety_id, 'INSERT', 'variety_name', NULL, NEW.variety_name);

    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.variety_name IS DISTINCT FROM NEW.variety_name THEN
            INSERT INTO audit_variety_history
                (variety_id, operation, changed_field, old_value, new_value)
            VALUES (NEW.variety_id, 'UPDATE', 'variety_name',
                    OLD.variety_name, NEW.variety_name);
        END IF;
        IF OLD.growth_cycle_days IS DISTINCT FROM NEW.growth_cycle_days THEN
            INSERT INTO audit_variety_history
                (variety_id, operation, changed_field, old_value, new_value)
            VALUES (NEW.variety_id, 'UPDATE', 'growth_cycle_days',
                    OLD.growth_cycle_days::TEXT, NEW.growth_cycle_days::TEXT);
        END IF;
        IF OLD.is_active IS DISTINCT FROM NEW.is_active THEN
            INSERT INTO audit_variety_history
                (variety_id, operation, changed_field, old_value, new_value)
            VALUES (NEW.variety_id, 'UPDATE', 'is_active',
                    OLD.is_active::TEXT, NEW.is_active::TEXT);
        END IF;
        NEW.updated_at := NOW();

    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_variety_history
            (variety_id, operation, changed_field, old_value, new_value)
        VALUES (OLD.variety_id, 'DELETE', 'variety_name', OLD.variety_name, NULL);
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_variety_audit
BEFORE INSERT OR UPDATE OR DELETE ON seed_varieties
FOR EACH ROW EXECUTE FUNCTION fn_trigger_variety_audit();

-- =============================================================================
-- STORED FUNCTION: sp_generate_watering_reminders
-- Exposed in UI as "Task Scheduler — Watering & Care Reminders"
-- =============================================================================
CREATE OR REPLACE FUNCTION sp_generate_watering_reminders(p_horizon_days INT DEFAULT 7)
RETURNS TABLE (
    variety_name        VARCHAR,
    crop_name           VARCHAR,
    region_name         VARCHAR,
    next_watering_date  DATE,
    water_volume_ml_sqm NUMERIC
) LANGUAGE plpgsql AS $$
DECLARE
    v_rec          RECORD;
    v_last_watered DATE;
    v_next_date    DATE;
BEGIN
    FOR v_rec IN
        SELECT sv.variety_id, sv.variety_name, sv.water_interval_days,
               sv.water_volume_ml_sqm, sv.planted_on,
               c.crop_name, r.region_name
        FROM   seed_varieties sv
        JOIN   crops   c ON c.crop_id   = sv.crop_id
        JOIN   regions r ON r.region_id = sv.region_id
        WHERE  sv.is_active = TRUE
    LOOP
        SELECT MAX(completed_date)
        INTO   v_last_watered
        FROM   care_schedule_log
        WHERE  variety_id   = v_rec.variety_id
          AND  care_type    = 'watering'
          AND  is_completed = TRUE;

        v_last_watered := COALESCE(v_last_watered, v_rec.planted_on, CURRENT_DATE);
        v_next_date    := v_last_watered + v_rec.water_interval_days;

        IF v_next_date <= CURRENT_DATE + p_horizon_days THEN
            IF NOT EXISTS (
                SELECT 1 FROM care_schedule_log
                WHERE  variety_id     = v_rec.variety_id
                  AND  care_type      = 'watering'
                  AND  scheduled_date = v_next_date
                  AND  is_completed   = FALSE
            ) THEN
                INSERT INTO care_schedule_log (variety_id, care_type, scheduled_date)
                VALUES (v_rec.variety_id, 'watering', v_next_date);
            END IF;

            variety_name        := v_rec.variety_name;
            crop_name           := v_rec.crop_name;
            region_name         := v_rec.region_name;
            next_watering_date  := v_next_date;
            water_volume_ml_sqm := v_rec.water_volume_ml_sqm;
            RETURN NEXT;
        END IF;
    END LOOP;
END;
$$;

-- =============================================================================
-- SEED DATA  (15+ rows per table)
-- =============================================================================

-- seasons
INSERT INTO seasons (season_name, start_month, end_month) VALUES
    ('Spring',  3,  5),
    ('Summer',  6,  8),
    ('Autumn',  9, 11),
    ('Winter', 12,  2);

-- climate_zones (15)
INSERT INTO climate_zones (zone_name, description) VALUES
    ('Steppe',              'Dry continental steppe covering southern Ukraine; hot summers, cold winters'),
    ('Forest-Steppe',       'Transitional zone with mixed forests and arable land; moderate rainfall'),
    ('Polissia',            'Northern wetlands zone; heavy rainfall, peat soils, mild summers'),
    ('Carpathian Highland', 'Alpine and sub-alpine zones in western Ukraine; cool, humid, mountainous'),
    ('Black Sea Coast',     'Warm Mediterranean-influenced coast; mild winters, dry hot summers'),
    ('Azov Steppe',         'Southeastern semi-arid zone near the Sea of Azov; saline soils'),
    ('Donbas Plain',        'Eastern industrial plain; continental climate with cold winters'),
    ('Podillia Plateau',    'Central-western elevated plateau; fertile loam soils, moderate rainfall'),
    ('Dnipro Lowland',      'Central river valley; fertile black earth, warm temperate climate'),
    ('Kryvorizska Steppe',  'Mineral-rich steppe in central Ukraine; semi-arid conditions'),
    ('Slobozhanshchyna',    'Northeastern plains; cold winters, warm summers, moderate precipitation'),
    ('Subcarpathia',        'Foothills zone west of the Carpathians; humid, fertile valley soils'),
    ('Pryazovia',           'Coastal steppe south of Zaporizhzhia; windy, saline steppes'),
    ('Zhytomyr Forest',     'Mixed coniferous-deciduous forests; acidic soils, moderate rainfall'),
    ('Chernihiv Woodlands', 'Northern forested lowlands; loamy soils, cool humid climate');

-- regions (18)
INSERT INTO regions (region_name, oblast, zone_id, latitude, longitude) VALUES
    ('Kyiv Region',          'Kyivska Oblast',            9,  50.44959,  30.52380),
    ('Kharkiv Region',       'Kharkivska Oblast',        11,  49.99300,  36.23000),
    ('Lviv Region',          'Lvivska Oblast',           12,  49.84000,  24.03000),
    ('Odesa Region',         'Odeska Oblast',             5,  46.48000,  30.73000),
    ('Dnipro Region',        'Dnipropetrovska Oblast',    9,  48.46000,  35.04000),
    ('Zaporizhzhia Region',  'Zaporizka Oblast',          6,  47.84000,  35.14000),
    ('Poltava Region',       'Poltavska Oblast',          2,  49.59000,  34.55000),
    ('Vinnytsia Region',     'Vinnytska Oblast',          8,  49.23000,  28.47000),
    ('Cherkasy Region',      'Cherkaska Oblast',          2,  49.44000,  32.06000),
    ('Sumy Region',          'Sumska Oblast',            11,  50.91000,  34.80000),
    ('Zhytomyr Region',      'Zhytomyrska Oblast',       14,  50.25000,  28.66000),
    ('Chernihiv Region',     'Chernihivska Oblast',      15,  51.49500,  31.30000),
    ('Mykolaiv Region',      'Mykolaivska Oblast',        1,  46.97500,  31.99400),
    ('Kherson Region',       'Khersonska Oblast',         1,  46.63500,  32.61700),
    ('Ivano-Frankivsk',      'Ivano-Frankivska Oblast',   4,  48.92100,  24.71000),
    ('Ternopil Region',      'Ternopilska Oblast',        8,  49.55300,  25.59400),
    ('Rivne Region',         'Rivnenska Oblast',          3,  50.61900,  26.25100),
    ('Khmelnytskyi Region',  'Khmelnytska Oblast',        8,  49.41900,  26.99700);

-- crops (18)
INSERT INTO crops (crop_name, crop_family, is_active, season_id) VALUES
    ('Winter Wheat',      'Poaceae',       TRUE,  (SELECT season_id FROM seasons WHERE season_name='Autumn')),
    ('Spring Wheat',      'Poaceae',       TRUE,  (SELECT season_id FROM seasons WHERE season_name='Spring')),
    ('Sunflower',         'Asteraceae',    TRUE,  (SELECT season_id FROM seasons WHERE season_name='Spring')),
    ('Maize (Corn)',      'Poaceae',       TRUE,  (SELECT season_id FROM seasons WHERE season_name='Spring')),
    ('Sugar Beet',        'Amaranthaceae', TRUE,  (SELECT season_id FROM seasons WHERE season_name='Spring')),
    ('Rapeseed',          'Brassicaceae',  TRUE,  (SELECT season_id FROM seasons WHERE season_name='Autumn')),
    ('Soybean',           'Fabaceae',      TRUE,  (SELECT season_id FROM seasons WHERE season_name='Spring')),
    ('Barley',            'Poaceae',       TRUE,  (SELECT season_id FROM seasons WHERE season_name='Autumn')),
    ('Tomato',            'Solanaceae',    TRUE,  (SELECT season_id FROM seasons WHERE season_name='Spring')),
    ('Potato',            'Solanaceae',    TRUE,  (SELECT season_id FROM seasons WHERE season_name='Spring')),
    ('Buckwheat',         'Polygonaceae',  TRUE,  (SELECT season_id FROM seasons WHERE season_name='Summer')),
    ('Pea',               'Fabaceae',      TRUE,  (SELECT season_id FROM seasons WHERE season_name='Spring')),
    ('Oats',              'Poaceae',       TRUE,  (SELECT season_id FROM seasons WHERE season_name='Spring')),
    ('Rye',               'Poaceae',       TRUE,  (SELECT season_id FROM seasons WHERE season_name='Autumn')),
    ('Millet',            'Poaceae',       TRUE,  (SELECT season_id FROM seasons WHERE season_name='Spring')),
    ('Flax',              'Linaceae',      TRUE,  (SELECT season_id FROM seasons WHERE season_name='Spring')),
    ('Hemp (Industrial)', 'Cannabaceae',   FALSE, (SELECT season_id FROM seasons WHERE season_name='Spring')),
    ('Lavender',          'Lamiaceae',     TRUE,  (SELECT season_id FROM seasons WHERE season_name='Summer'));

-- seed_varieties (20) — audit trigger fires automatically on each INSERT
INSERT INTO seed_varieties
    (variety_name, crop_id, region_id, growth_cycle_days, water_interval_days,
     water_volume_ml_sqm, germination_rate_pct, planted_on, notes)
VALUES
    ('Podolyanka',
     (SELECT crop_id FROM crops WHERE crop_name='Winter Wheat'),
     (SELECT region_id FROM regions WHERE region_name='Vinnytsia Region'),
     270, 14, 3500.00, 94.5, '2023-10-15', 'High-yield winter wheat for Podillia'),

    ('Myronivska 808',
     (SELECT crop_id FROM crops WHERE crop_name='Winter Wheat'),
     (SELECT region_id FROM regions WHERE region_name='Kyiv Region'),
     260, 14, 3200.00, 96.0, '2023-10-10', 'Classic Ukrainian soft wheat variety'),

    ('Ariana',
     (SELECT crop_id FROM crops WHERE crop_name='Sunflower'),
     (SELECT region_id FROM regions WHERE region_name='Dnipro Region'),
     105, 10, 4500.00, 91.0, '2024-04-20', 'High-oleic confectionery sunflower'),

    ('Lider',
     (SELECT crop_id FROM crops WHERE crop_name='Sunflower'),
     (SELECT region_id FROM regions WHERE region_name='Zaporizhzhia Region'),
     100, 10, 4200.00, 89.5, '2024-04-18', 'Drought-resistant for dry steppe'),

    ('Kvitnevyi',
     (SELECT crop_id FROM crops WHERE crop_name='Maize (Corn)'),
     (SELECT region_id FROM regions WHERE region_name='Poltava Region'),
     130,  7, 5500.00, 87.0, '2024-05-01', 'FAO 300 silage maize'),

    ('Dniprovskyi 181',
     (SELECT crop_id FROM crops WHERE crop_name='Maize (Corn)'),
     (SELECT region_id FROM regions WHERE region_name='Cherkasy Region'),
     140,  7, 5800.00, 88.5, '2024-05-05', 'Old reliable grain maize variety'),

    ('Ukrainska',
     (SELECT crop_id FROM crops WHERE crop_name='Sugar Beet'),
     (SELECT region_id FROM regions WHERE region_name='Vinnytsia Region'),
     165, 12, 6000.00, 82.0, '2024-04-10', 'Sugar content 17-18%; adapted to Podillia'),

    ('Ternopilska 25',
     (SELECT crop_id FROM crops WHERE crop_name='Sugar Beet'),
     (SELECT region_id FROM regions WHERE region_name='Ternopil Region'),
     170, 12, 6200.00, 83.5, '2024-04-08', 'High-sugar variety for western regions'),

    ('Exagone',
     (SELECT crop_id FROM crops WHERE crop_name='Rapeseed'),
     (SELECT region_id FROM regions WHERE region_name='Lviv Region'),
     280, 16, 2800.00, 90.0, '2023-08-25', 'European hybrid rapeseed, winter type'),

    ('Ukrainskyi Zorianyi',
     (SELECT crop_id FROM crops WHERE crop_name='Soybean'),
     (SELECT region_id FROM regions WHERE region_name='Poltava Region'),
     120,  8, 4800.00, 86.0, '2024-05-15', 'Medium-maturity soybean for forest-steppe'),

    ('Haidamatskyi',
     (SELECT crop_id FROM crops WHERE crop_name='Barley'),
     (SELECT region_id FROM regions WHERE region_name='Kharkiv Region'),
      90, 14, 2500.00, 93.0, '2023-09-20', 'Winter malting barley for eastern Ukraine'),

    ('Nova Ukraina',
     (SELECT crop_id FROM crops WHERE crop_name='Tomato'),
     (SELECT region_id FROM regions WHERE region_name='Odesa Region'),
      75,  4, 7500.00, 78.5, '2024-05-20', 'Processing tomato for Black Sea coast'),

    ('Yablunivska',
     (SELECT crop_id FROM crops WHERE crop_name='Potato'),
     (SELECT region_id FROM regions WHERE region_name='Zhytomyr Region'),
      90,  6, 5200.00, 95.0, '2024-04-25', 'Early potato for northern Polissia'),

    ('Zolotodolynnyi',
     (SELECT crop_id FROM crops WHERE crop_name='Buckwheat'),
     (SELECT region_id FROM regions WHERE region_name='Chernihiv Region'),
      70, 10, 3000.00, 85.0, '2024-06-01', 'Fast-growing buckwheat for woodlands'),

    ('Zerniatko',
     (SELECT crop_id FROM crops WHERE crop_name='Pea'),
     (SELECT region_id FROM regions WHERE region_name='Rivne Region'),
      65, 10, 3200.00, 88.0, '2024-04-15', 'Short-season smooth-seeded pea'),

    ('Zoriane Nebo',
     (SELECT crop_id FROM crops WHERE crop_name='Oats'),
     (SELECT region_id FROM regions WHERE region_name='Sumy Region'),
      80, 12, 2900.00, 91.5, '2024-04-01', 'Spring oats for feed and milling'),

    ('Kharkivska 86',
     (SELECT crop_id FROM crops WHERE crop_name='Spring Wheat'),
     (SELECT region_id FROM regions WHERE region_name='Kharkiv Region'),
     105, 14, 3400.00, 92.0, '2024-04-05', 'Reliable spring wheat for Slobozhanshchyna'),

    ('Prydesnyanskyi',
     (SELECT crop_id FROM crops WHERE crop_name='Rye'),
     (SELECT region_id FROM regions WHERE region_name='Chernihiv Region'),
     260, 16, 2600.00, 89.0, '2023-09-10', 'Winter rye adapted to sandy acidic soils'),

    ('Poltavske Zoloto',
     (SELECT crop_id FROM crops WHERE crop_name='Millet'),
     (SELECT region_id FROM regions WHERE region_name='Poltava Region'),
      80, 10, 3100.00, 84.0, '2024-05-25', 'Golden millet for forest-steppe zone'),

    ('Podilska Lavanda',
     (SELECT crop_id FROM crops WHERE crop_name='Lavender'),
     (SELECT region_id FROM regions WHERE region_name='Khmelnytskyi Region'),
     365,  7, 1800.00, 72.0, '2023-05-01', 'Perennial lavender for essential oil production');

-- yield_records (20)
INSERT INTO yield_records
    (variety_id, region_id, season_id, harvest_year, yield_tons_ha, area_ha, quality_score)
VALUES
    (1,  (SELECT region_id FROM regions WHERE region_name='Vinnytsia Region'),
         (SELECT season_id FROM seasons WHERE season_name='Summer'),  2023,  6.80, 450.00, 9),
    (2,  (SELECT region_id FROM regions WHERE region_name='Kyiv Region'),
         (SELECT season_id FROM seasons WHERE season_name='Summer'),  2023,  6.20, 380.00, 8),
    (3,  (SELECT region_id FROM regions WHERE region_name='Dnipro Region'),
         (SELECT season_id FROM seasons WHERE season_name='Autumn'),  2023,  3.50, 600.00, 9),
    (4,  (SELECT region_id FROM regions WHERE region_name='Zaporizhzhia Region'),
         (SELECT season_id FROM seasons WHERE season_name='Autumn'),  2023,  3.10, 500.00, 7),
    (5,  (SELECT region_id FROM regions WHERE region_name='Poltava Region'),
         (SELECT season_id FROM seasons WHERE season_name='Autumn'),  2023,  9.20, 320.00, 8),
    (6,  (SELECT region_id FROM regions WHERE region_name='Cherkasy Region'),
         (SELECT season_id FROM seasons WHERE season_name='Autumn'),  2023,  8.90, 410.00, 8),
    (7,  (SELECT region_id FROM regions WHERE region_name='Vinnytsia Region'),
         (SELECT season_id FROM seasons WHERE season_name='Autumn'),  2023, 55.00, 200.00, 9),
    (8,  (SELECT region_id FROM regions WHERE region_name='Ternopil Region'),
         (SELECT season_id FROM seasons WHERE season_name='Autumn'),  2023, 57.50, 180.00, 9),
    (9,  (SELECT region_id FROM regions WHERE region_name='Lviv Region'),
         (SELECT season_id FROM seasons WHERE season_name='Summer'),  2024,  3.80, 250.00, 8),
    (10, (SELECT region_id FROM regions WHERE region_name='Poltava Region'),
         (SELECT season_id FROM seasons WHERE season_name='Autumn'),  2023,  2.90, 300.00, 7),
    (11, (SELECT region_id FROM regions WHERE region_name='Kharkiv Region'),
         (SELECT season_id FROM seasons WHERE season_name='Summer'),  2024,  5.40, 420.00, 8),
    (12, (SELECT region_id FROM regions WHERE region_name='Odesa Region'),
         (SELECT season_id FROM seasons WHERE season_name='Autumn'),  2023, 68.00,  90.00, 8),
    (13, (SELECT region_id FROM regions WHERE region_name='Zhytomyr Region'),
         (SELECT season_id FROM seasons WHERE season_name='Summer'),  2024, 28.00,  60.00, 9),
    (14, (SELECT region_id FROM regions WHERE region_name='Chernihiv Region'),
         (SELECT season_id FROM seasons WHERE season_name='Autumn'),  2023,  1.60, 120.00, 7),
    (15, (SELECT region_id FROM regions WHERE region_name='Rivne Region'),
         (SELECT season_id FROM seasons WHERE season_name='Summer'),  2024,  4.20,  80.00, 8),
    (16, (SELECT region_id FROM regions WHERE region_name='Sumy Region'),
         (SELECT season_id FROM seasons WHERE season_name='Summer'),  2024,  3.80, 150.00, 8),
    (17, (SELECT region_id FROM regions WHERE region_name='Kharkiv Region'),
         (SELECT season_id FROM seasons WHERE season_name='Summer'),  2024,  5.10, 200.00, 7),
    (18, (SELECT region_id FROM regions WHERE region_name='Chernihiv Region'),
         (SELECT season_id FROM seasons WHERE season_name='Summer'),  2024,  3.20, 160.00, 7),
    (19, (SELECT region_id FROM regions WHERE region_name='Poltava Region'),
         (SELECT season_id FROM seasons WHERE season_name='Autumn'),  2023,  2.50, 140.00, 8),
    (20, (SELECT region_id FROM regions WHERE region_name='Khmelnytskyi Region'),
         (SELECT season_id FROM seasons WHERE season_name='Summer'),  2024,  1.20,  15.00, 9);

-- care_schedule_log (20)
INSERT INTO care_schedule_log
    (variety_id, care_type, scheduled_date, completed_date, is_completed, notes)
VALUES
    (1,  'watering',    '2024-04-01', '2024-04-01', TRUE,  'Spring activation watering'),
    (1,  'watering',    '2024-04-15', '2024-04-15', TRUE,  'Second cycle'),
    (2,  'watering',    '2024-04-03', '2024-04-03', TRUE,  'Regular interval'),
    (3,  'watering',    '2024-05-01', '2024-05-01', TRUE,  'Post-planting soak'),
    (3,  'fertilising', '2024-05-20', '2024-05-20', TRUE,  'NPK starter dose'),
    (4,  'watering',    '2024-05-05', NULL,         FALSE, 'Pending — check moisture'),
    (5,  'watering',    '2024-05-10', '2024-05-10', TRUE,  'Irrigation cycle 1'),
    (5,  'watering',    '2024-05-17', NULL,         FALSE, 'Upcoming'),
    (6,  'watering',    '2024-05-12', '2024-05-12', TRUE,  'Drip irrigation'),
    (7,  'watering',    '2024-04-22', '2024-04-22', TRUE,  'Soil moisture maintained'),
    (8,  'watering',    '2024-04-20', NULL,         FALSE, 'Scheduled — irrigation needed'),
    (9,  'watering',    '2024-05-08', '2024-05-08', TRUE,  'Rainfall supplement'),
    (10, 'watering',    '2024-05-23', NULL,         FALSE, 'Upcoming reminder'),
    (11, 'watering',    '2024-04-05', '2024-04-05', TRUE,  'Winter barley spring watering'),
    (12, 'watering',    '2024-05-24', '2024-05-24', TRUE,  'Daily tomato cycle start'),
    (13, 'watering',    '2024-05-01', '2024-05-01', TRUE,  'Early potato watering'),
    (14, 'watering',    '2024-06-11', NULL,         FALSE, 'First buckwheat irrigation'),
    (15, 'fertilising', '2024-04-25', '2024-04-25', TRUE,  'Pre-emergence nitrogen'),
    (16, 'watering',    '2024-04-13', '2024-04-13', TRUE,  'Oat field irrigation'),
    (20, 'watering',    '2024-05-08', '2024-05-08', TRUE,  'Lavender establishment watering');
