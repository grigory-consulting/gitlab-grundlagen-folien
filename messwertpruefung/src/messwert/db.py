"""Speicherung der Prüfberichte in PostgreSQL.

Die Verbindung kommt aus der Umgebungsvariable DATABASE_URL,
z. B. postgresql://app:app@db:5432/messwert
"""

import json
import os
import time

import psycopg
from psycopg.rows import dict_row

from messwert.validation import Result

SCHEMA = """
CREATE TABLE IF NOT EXISTS berichte (
    id          SERIAL PRIMARY KEY,
    erstellt    TIMESTAMPTZ NOT NULL DEFAULT now(),
    dateiname   TEXT NOT NULL,
    anzahl      INTEGER NOT NULL,
    ausserhalb  INTEGER NOT NULL,
    zeilen      JSONB NOT NULL
)
"""


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL ist nicht gesetzt")
    return url


def connect() -> psycopg.Connection:
    return psycopg.connect(database_url(), row_factory=dict_row, connect_timeout=5)


def init_schema(attempts: int = 30, delay: float = 1.0) -> None:
    """Legt die Tabelle an. Wartet, bis die Datenbank erreichbar ist (startet oft gleichzeitig)."""
    for attempt in range(1, attempts + 1):
        try:
            with connect() as conn:
                conn.execute(SCHEMA)
            return
        except psycopg.OperationalError:
            if attempt == attempts:
                raise
            time.sleep(delay)


def is_ready() -> bool:
    """True, wenn die Datenbank erreichbar ist."""
    try:
        with connect() as conn:
            conn.execute("SELECT 1")
        return True
    except (psycopg.Error, RuntimeError):
        return False


def save_report(filename: str, results: list[Result]) -> int:
    rows = [
        {
            "device": r.measurement.device,
            "value": r.measurement.value,
            "lower": r.measurement.lower,
            "upper": r.measurement.upper,
            "unit": r.measurement.unit,
            "innerhalb": r.within_limits,
        }
        for r in results
    ]
    outside = sum(1 for r in results if not r.within_limits)
    with connect() as conn:
        record = conn.execute(
            "INSERT INTO berichte (dateiname, anzahl, ausserhalb, zeilen) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (filename, len(rows), outside, json.dumps(rows)),
        ).fetchone()
    return record["id"]


def list_reports() -> list[dict]:
    with connect() as conn:
        return conn.execute(
            "SELECT id, erstellt, dateiname, anzahl, ausserhalb FROM berichte ORDER BY id DESC"
        ).fetchall()


def load_report(report_id: int) -> dict | None:
    with connect() as conn:
        return conn.execute(
            "SELECT id, erstellt, dateiname, anzahl, ausserhalb, zeilen FROM berichte WHERE id = %s",
            (report_id,),
        ).fetchone()
