# Messwertprüfung

Übungsprojekt der Schulung „GitLab: Grundlagen und GitLab DevOps“ (Teil V bis VIII). Eine kleine Webanwendung nimmt Messwerte als CSV entgegen, prüft sie gegen Grenzen und speichert die Berichte in PostgreSQL. Im Kurs geht es nicht um die Anwendung, sondern um die Pipeline, die sie prüft, baut und als Image ausliefert.

Dieser Ordner ist der **Endstand nach Lab 12**. Die Startstände der Labs entstehen daraus.

## Was die Anwendung tut

```csv
device,value,lower,upper,unit
Sensor-A,20.3,19,21,C
Sensor-B,23.1,19,21,C
Sensor-C,19,19,21,C
```

Ergebnis: A innerhalb, B außerhalb, C innerhalb. Beide Grenzen gehören zum zulässigen Bereich (`lower <= value <= upper`).

- Ein Wert **außerhalb** ist ein gültiges Ergebnis. Der Bericht wird gespeichert, und kein Test wird dadurch rot.
- Eine **kaputte Datei** wird vollständig abgelehnt, mit Zeilenangabe: fehlende Spalte, keine Zahl, `lower > upper`, keine Messzeilen.

| Pfad | Zweck |
|---|---|
| `GET /` | Oberfläche: CSV hochladen, frühere Prüfungen |
| `GET /berichte/{id}` | Bericht ansehen |
| `POST /api/reports` | CSV prüfen und speichern (Feld `datei`) |
| `GET /api/reports`, `GET /api/reports/{id}` | Berichte lesen |
| `GET /api/reports/{id}/export` | Bericht als CSV |
| `GET /health` | Prozess läuft; zeigt Titel, Version, Commit |
| `GET /ready` | Datenbank erreichbar (200) oder nicht (503) |

Konfiguration über Umgebungsvariablen: `DATABASE_URL` (PostgreSQL), `APP_TITLE` (Überschrift), `BUILD_COMMIT` (setzt der Image-Build).

## Aufbau

| Datei / Ordner | Inhalt |
|---|---|
| `src/messwert/validation.py` | Fachlogik: CSV lesen, Grenzen prüfen |
| `src/messwert/db.py` | Speichern und Lesen in PostgreSQL |
| `src/messwert/app.py`, `templates/` | Webanwendung (FastAPI) |
| `tests/unit/` | ohne Datenbank, schnell |
| `tests/integration/` | gegen eine echte PostgreSQL (`DATABASE_URL`) |
| `tests/scenarios/` | vorbereitete CSV-Dateien aus `testdata/<SCENARIO>/` |
| `tests/smoke/` | gegen das laufende Image (`BASE_URL`) |
| `requirements.txt`, `requirements-dev.txt` | festgeschriebene Abhängigkeiten |
| `Dockerfile` | Produktimage aus dem gebauten Wheel |
| `.gitlab-ci.yml`, `.gitlab/ci/templates.yml` | Pipeline |

## Pipeline

```text
lint ──> unit_tests ──> build_wheel ──> install_check
         integration_tests ─┐    │
         scenarios          └────┴──> build_image ──> container_smoke
```

| Job | Zeigt (Lab) |
|---|---|
| `lint`, `unit_tests` | Vorlagen mit `extends`, `include` (07) |
| `workflow:rules` | Branch-, MR- und Tag-Pipelines, keine Doppelläufe (07) |
| `APP_TITLE` | woher eine Variable kommt (08) |
| `.python`-Vorlage | pip-Cache (09) |
| `build_wheel` → `install_check` | Artifact-Übergabe, `needs` (09) |
| `integration_tests` | PostgreSQL als Service mit Alias `db` (10) |
| `build_image` | Docker-in-Docker, Registry, Commit-Tag, Digest (11) |
| `container_smoke` | das gebaute Image läuft mit frischer Datenbank (11) |
| `unit_tests`, `scenarios` | JUnit, Coverage, `parallel:matrix` (12) |

`build_image` braucht einen **privileged** Docker-Runner. `container_smoke` nutzt `FF_NETWORK_PER_BUILD`, damit die beiden Services sich gegenseitig erreichen.

## Lokal ausführen (optional, nur für Trainer)

Teilnehmende brauchen das nicht; alles läuft auf dem Runner.

```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest                                            # nur Unit-Tests
ruff check . && ruff format --check .

docker run -d --name mw-db -p 55432:5432 -e POSTGRES_DB=messwert -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=nur-fuer-tests postgres:17-alpine
DATABASE_URL=postgresql://app:nur-fuer-tests@localhost:55432/messwert pytest tests/integration
DATABASE_URL=postgresql://app:nur-fuer-tests@localhost:55432/messwert uvicorn messwert.app:app --app-dir src --port 8080
```

Image bauen: erst `python -m build --wheel`, dann `docker build -t messwert:lokal .`. Wer das Wheel nach einer Codeänderung nicht neu baut, bekommt ein Image mit altem Stand. Der Smoke-Test deckt genau das auf.

Im Kurs lief die Pipeline auf GitLab CE 19.4 mit einem privileged Docker-Runner (Docker-Executor).
