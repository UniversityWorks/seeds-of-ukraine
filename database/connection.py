import re
import psycopg2
import psycopg2.extensions
import psycopg2.extras
import pandas as pd
from typing import Any, List


_NAMED_RE = re.compile(r'%\((\w+)\)s')

_POSITIONAL_RE = re.compile(r'(?<!%)%s')


def _adapt_value(conn, val) -> str:
    adapted = psycopg2.extensions.adapt(val)
    if hasattr(adapted, 'prepare'):
        adapted.prepare(conn)
    return adapted.getquoted().decode('utf-8')


def _build_sql(conn, sql: str, params) -> str:

    if params is None:
        return sql

    if isinstance(params, dict):
        def replacer(m):
            key = m.group(1)
            return _adapt_value(conn, params[key])
        return _NAMED_RE.sub(replacer, sql)

    values = list(params) if not isinstance(params, list) else params
    idx = [0]   

    def pos_replacer(m):
        v = _adapt_value(conn, values[idx[0]])
        idx[0] += 1
        return v

    return _POSITIONAL_RE.sub(pos_replacer, sql)


def _open(cfg: dict) -> psycopg2.extensions.connection:
    return psycopg2.connect(
        host=cfg.get("host", "localhost"),
        port=cfg.get("port", 5432),
        dbname=cfg["dbname"],
        user=cfg["user"],
        password=cfg.get("password", ""),
        connect_timeout=cfg.get("connect_timeout", 5),
        options=f"-c statement_timeout={cfg.get('statement_timeout', 30000)}",
    )



def ping(cfg: dict) -> bool:
    try:
        conn = _open(cfg)
        conn.close()
        return True
    except Exception:
        return False


def fetch(cfg: dict, sql: str, params=None) -> pd.DataFrame:
   
    conn = _open(cfg)
    try:
        rendered = _build_sql(conn, sql, params)
        with conn.cursor() as cur:
            cur.execute(rendered)
            cols = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchall()
            if not rows:
                return pd.DataFrame(columns=cols)
            return pd.DataFrame(rows, columns=cols)
    finally:
        conn.close()


def execute(cfg: dict, sql: str, params=None) -> int:
    conn = _open(cfg)
    try:
        rendered = _build_sql(conn, sql, params)
        with conn:
            with conn.cursor() as cur:
                cur.execute(rendered)
                return cur.rowcount
    finally:
        conn.close()


def execute_returning(cfg: dict, sql: str, params=None) -> Any:
    conn = _open(cfg)
    try:
        rendered = _build_sql(conn, sql, params)
        with conn:
            with conn.cursor() as cur:
                cur.execute(rendered)
                row = cur.fetchone()
                return row[0] if row else None
    finally:
        conn.close()


def fetch_many(cfg: dict, sql: str, params=None) -> List[tuple]:
    conn = _open(cfg)
    try:
        rendered = _build_sql(conn, sql, params)
        with conn.cursor() as cur:
            cur.execute(rendered)
            return cur.fetchall()
    finally:
        conn.close()
