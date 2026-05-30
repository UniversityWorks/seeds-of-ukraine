"""
database/connection.py
======================
Low-level database plumbing.

Fix history
-----------
v2.0.1  Switched from pd.read_sql_query to cursor.execute + fetchall.
v2.0.2  Tried mogrify() — rejected dict on this psycopg2 build.
v2.0.3  _normalise_params(): convert %(name)s+dict → %s+tuple.
v2.0.4  IndexError: tuple index out of range — caused by bare % characters
        inside SQL column aliases such as "Germination Rate (%)" and
        "Avg Germination Rate (%)".  After _normalise_params() replaced
        %(name)s with %s, psycopg2 counted those alias-% chars as extra
        positional placeholders, so the tuple ran out of values.

        Definitive fix — _build_sql():
          Perform the entire parameter substitution in pure Python using
          psycopg2.extensions.adapt() for safe value quoting, then pass
          the fully-rendered SQL string to cur.execute() with NO params.
          This means psycopg2 never sees any % characters at all and
          cannot misinterpret column aliases as placeholders.

        This approach is safe against SQL injection because adapt() uses
        psycopg2's own C-level quoting/escaping for every value.
"""

import re
import psycopg2
import psycopg2.extensions
import psycopg2.extras
import pandas as pd
from typing import Any, List


# Matches %(identifier)s named placeholders
_NAMED_RE = re.compile(r'%\((\w+)\)s')

# Matches positional %s placeholders (not preceded by another %)
_POSITIONAL_RE = re.compile(r'(?<!%)%s')


def _adapt_value(conn, val) -> str:
    """
    Use psycopg2's adapt() to safely render a Python value as a SQL literal.
    Returns a properly quoted/escaped string ready for direct embedding.
    """
    adapted = psycopg2.extensions.adapt(val)
    if hasattr(adapted, 'prepare'):
        adapted.prepare(conn)
    return adapted.getquoted().decode('utf-8')


def _build_sql(conn, sql: str, params) -> str:
    """
    Render a fully-substituted SQL string by embedding params as SQL literals.

    Supports:
      - %(name)s + dict  : named placeholders
      - %s + list/tuple  : positional placeholders
      - None             : no substitution; % in aliases left untouched

    Returns a plain SQL string with NO remaining placeholders.
    psycopg2's cur.execute() is then called with this string and params=None,
    so it never interprets any % characters — including those in column aliases
    like "Germination Rate (%)" or "Avg Germination Rate (%)".
    """
    if params is None:
        return sql

    if isinstance(params, dict):
        # Replace each %(key)s with its adapted value in one pass
        def replacer(m):
            key = m.group(1)
            return _adapt_value(conn, params[key])
        return _NAMED_RE.sub(replacer, sql)

    # List or tuple — positional %s substitution
    values = list(params) if not isinstance(params, list) else params
    idx = [0]   # mutable counter for closure

    def pos_replacer(m):
        v = _adapt_value(conn, values[idx[0]])
        idx[0] += 1
        return v

    return _POSITIONAL_RE.sub(pos_replacer, sql)


def _open(cfg: dict) -> psycopg2.extensions.connection:
    """Open and return a psycopg2 connection from a config dict."""
    return psycopg2.connect(
        host=cfg.get("host", "localhost"),
        port=cfg.get("port", 5432),
        dbname=cfg["dbname"],
        user=cfg["user"],
        password=cfg.get("password", ""),
        connect_timeout=cfg.get("connect_timeout", 5),
        options=f"-c statement_timeout={cfg.get('statement_timeout', 30000)}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def ping(cfg: dict) -> bool:
    """Return True if a connection can be opened, else False."""
    try:
        conn = _open(cfg)
        conn.close()
        return True
    except Exception:
        return False


def fetch(cfg: dict, sql: str, params=None) -> pd.DataFrame:
    """
    Execute a SELECT and return a pandas DataFrame.
    Accepts %(name)s+dict, %s+list/tuple, or no params.
    All substitution is done in Python; psycopg2 receives plain SQL.
    """
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
    """Execute a write statement. Returns rowcount. Commits automatically."""
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
    """Execute INSERT…RETURNING and return the first column of the first row."""
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
    """Execute a SELECT and return raw rows as a list of tuples."""
    conn = _open(cfg)
    try:
        rendered = _build_sql(conn, sql, params)
        with conn.cursor() as cur:
            cur.execute(rendered)
            return cur.fetchall()
    finally:
        conn.close()
