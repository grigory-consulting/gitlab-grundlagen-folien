"""Unit-Tests der Webanwendung ohne Datenbank."""

from fastapi.testclient import TestClient

from messwert.app import app


def test_health_reports_running_process(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_title_comes_from_app_title(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("APP_TITLE", "Messwertprüfung Labor 3")
    with TestClient(app) as client:
        assert client.get("/health").json()["titel"] == "Messwertprüfung Labor 3"


def test_not_ready_without_database(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with TestClient(app) as client:
        response = client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "nicht bereit"}
