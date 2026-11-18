"""Integrationstests: API und echte PostgreSQL-Datenbank.

Brauchen DATABASE_URL, in der Pipeline z. B. postgresql://app:app@db:5432/messwert
Aufruf:  pytest tests/integration
"""

import os

import pytest
from fastapi.testclient import TestClient

from messwert.app import app

pytestmark = pytest.mark.integration

CSV = "device,value,lower,upper,unit\nSensor-A,20.3,19,21,C\nSensor-B,23.1,19,21,C\nSensor-C,19,19,21,C\n"


@pytest.fixture(scope="module")
def client():
    if not os.environ.get("DATABASE_URL"):
        pytest.fail("DATABASE_URL fehlt: Integrationstests brauchen eine PostgreSQL-Datenbank")
    with TestClient(app) as c:
        yield c


def test_database_is_ready(client):
    response = client.get("/ready")
    assert response.status_code == 200, response.text


def test_report_is_saved_and_read_back(client):
    response = client.post("/api/reports", files={"datei": ("messung.csv", CSV, "text/csv")})
    assert response.status_code == 201, response.text
    report_id = response.json()["id"]

    read_back = client.get(f"/api/reports/{report_id}").json()
    assert read_back["dateiname"] == "messung.csv"
    assert read_back["anzahl"] == 3
    assert read_back["ausserhalb"] == 1

    ids = [r["id"] for r in client.get("/api/reports").json()]
    assert report_id in ids


def test_export_returns_csv_with_result(client):
    report_id = client.post("/api/reports", files={"datei": ("m.csv", CSV, "text/csv")}).json()["id"]
    export = client.get(f"/api/reports/{report_id}/export")
    assert export.status_code == 200
    assert export.text.splitlines()[2] == "Sensor-B,23.1,19.0,21.0,C,ausserhalb"


def test_invalid_file_is_not_saved(client):
    before = len(client.get("/api/reports").json())
    response = client.post("/api/reports", files={"datei": ("kaputt.csv", "device,value\nS,1\n", "text/csv")})
    assert response.status_code == 422
    assert "Pflichtspalten fehlen" in response.json()["fehler"]
    assert len(client.get("/api/reports").json()) == before


def test_unknown_report_returns_404(client):
    assert client.get("/api/reports/999999").status_code == 404


def test_ui_shows_history(client):
    client.post("/api/reports", files={"datei": ("oberflaeche.csv", CSV, "text/csv")})
    page = client.get("/")
    assert page.status_code == 200
    assert "oberflaeche.csv" in page.text
