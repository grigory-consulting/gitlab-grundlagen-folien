"""Smoke-Test gegen das laufende Containerimage (nicht gegen den Quelltext).

Braucht BASE_URL, in der Pipeline http://app:8080 (Image als Service mit Alias app).
Aufruf:  BASE_URL=http://localhost:8080 pytest tests/smoke
"""

import os
import time

import httpx2
import pytest

BASE_URL = os.environ.get("BASE_URL", "")
CSV = "device,value,lower,upper,unit\nSensor-A,20.3,19,21,C\nSensor-B,23.1,19,21,C\n"


@pytest.fixture(scope="module")
def http():
    if not BASE_URL:
        pytest.fail("BASE_URL fehlt: Adresse der laufenden Anwendung, z. B. http://app:8080")
    with httpx2.Client(base_url=BASE_URL, timeout=5) as client:
        # Der Container braucht nach dem Start einige Sekunden. Höchstens 60 s warten.
        for _ in range(30):
            try:
                if client.get("/ready").status_code == 200:
                    break
            except httpx2.TransportError:
                pass
            time.sleep(2)
        else:
            pytest.fail(f"Anwendung unter {BASE_URL} wurde nicht bereit")
        yield client


def test_image_reports_commit(http):
    health = http.get("/health").json()
    print(f"Image-Version {health['version']}, Commit {health['commit']}")
    assert health["status"] == "ok"
    expected = os.environ.get("CI_COMMIT_SHORT_SHA")
    if expected:
        assert health["commit"] == expected


def test_upload_save_export(http):
    response = http.post("/api/reports", files={"datei": ("smoke.csv", CSV, "text/csv")})
    assert response.status_code == 201, response.text
    report_id = response.json()["id"]
    assert http.get(f"/api/reports/{report_id}").json()["ausserhalb"] == 1
    assert "ausserhalb" in http.get(f"/api/reports/{report_id}/export").text


def test_ui_is_served(http):
    # Scheitert, wenn die HTML-Templates nicht im Image gelandet sind.
    page = http.get("/")
    assert page.status_code == 200
    assert "CSV hochladen" in page.text
