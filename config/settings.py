
import os

APP_NAME        = "Насіння України"
APP_TAGLINE     = "Управління культурами · Аналітика врожайності · Регіональна аналітика"

DEFAULT_DB_HOST     = os.getenv("SOU_DB_HOST",     "localhost")
DEFAULT_DB_PORT     = int(os.getenv("SOU_DB_PORT",  "5432"))
DEFAULT_DB_NAME     = os.getenv("SOU_DB_NAME",     "seeds_ukraine")
DEFAULT_DB_USER     = os.getenv("SOU_DB_USER",     "postgres")
DEFAULT_DB_PASSWORD = os.getenv("SOU_DB_PASSWORD", "")

DB_CONNECT_TIMEOUT   = 5
DB_STATEMENT_TIMEOUT = 30_000

DEFAULT_TABLE_HEIGHT      = 420
ACTIVITY_LOG_DEFAULT_ROWS = 100
CARE_HORIZON_DEFAULT_DAYS = 7

COLOR_GREEN_DEEP  = "#1a3c2b"
COLOR_GREEN_MID   = "#2d6a4f"
COLOR_GREEN_LIGHT = "#52b788"
COLOR_GREEN_PALE  = "#d8f3dc"
COLOR_GOLD        = "#d4a017"
COLOR_GOLD_LIGHT  = "#f5e6aa"
COLOR_EARTH       = "#6b4226"
COLOR_CREAM       = "#faf7f0"
COLOR_WHITE       = "#ffffff"

AUDIT_COLOURS = {
    "INSERT": COLOR_GREEN_MID,
    "UPDATE": COLOR_GOLD,
    "DELETE": "#c0392b",
}

CROP_FAMILY_OPTIONS = [
    "Poaceae",
    "Asteraceae",
    "Solanaceae",
    "Fabaceae",
    "Brassicaceae",
    "Amaranthaceae",
    "Linaceae",
    "Cannabaceae",
    "Lamiaceae",
    "Polygonaceae",
]

def build_db_config(
    host:     str = DEFAULT_DB_HOST,
    port:     int = DEFAULT_DB_PORT,
    dbname:   str = DEFAULT_DB_NAME,
    user:     str = DEFAULT_DB_USER,
    password: str = DEFAULT_DB_PASSWORD,
) -> dict:
    """Повертає словник параметрів підключення для psycopg2."""
    return {
        "host":     host,
        "port":     int(port),
        "dbname":   dbname,
        "user":     user,
        "password": password,
    }
