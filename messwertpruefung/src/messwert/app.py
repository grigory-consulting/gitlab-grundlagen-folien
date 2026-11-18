"""Webanwendung Messwertprüfung: CSV hochladen, Bericht ansehen, Historie öffnen.

Start lokal:  uvicorn messwert.app:app --port 8080
Konfiguration über Umgebungsvariablen:
  DATABASE_URL  Verbindung zu PostgreSQL (Pflicht für Speichern und /ready)
  APP_TITLE     Überschrift der Oberfläche (Standard: Messwertprüfung)
  BUILD_COMMIT  Commit, aus dem das Image gebaut wurde (setzt die Pipeline)
"""

import csv
import io
import os
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from messwert import db
from messwert.validation import ValidationError, evaluate, read_csv

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def app_title() -> str:
    return os.environ.get("APP_TITLE", "Messwertprüfung")


def app_version() -> str:
    try:
        return version("messwert")
    except PackageNotFoundError:
        return "nicht installiert"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Ohne DATABASE_URL startet die Anwendung trotzdem; /ready meldet dann "nicht bereit".
    if os.environ.get("DATABASE_URL"):
        db.init_schema()
    yield


app = FastAPI(title="Messwertprüfung", lifespan=lifespan)


def _process(filename: str, raw_data: bytes) -> int:
    try:
        results = evaluate(read_csv(raw_data.decode("utf-8")))
    except UnicodeDecodeError:
        raise ValidationError("Die Datei ist nicht UTF-8-kodiert") from None
    return db.save_report(filename, results)


def _report_or_404(report_id: int) -> dict:
    report = db.load_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Bericht {report_id} gibt es nicht")
    return report


# --- Betrieb -----------------------------------------------------------------


@app.get("/health")
def health():
    """Der Prozess läuft. Sagt nichts über die Datenbank."""
    return {
        "status": "ok",
        "titel": app_title(),
        "version": app_version(),
        "commit": os.environ.get("BUILD_COMMIT", "unbekannt"),
    }


@app.get("/ready")
def ready():
    """Die Anwendung kann arbeiten: Datenbank ist erreichbar."""
    if db.is_ready():
        return {"status": "bereit"}
    return JSONResponse(status_code=503, content={"status": "nicht bereit"})


# --- API ---------------------------------------------------------------------


@app.post("/api/reports", status_code=201)
async def api_upload(file: Annotated[UploadFile, File(alias="datei")]):
    try:
        report_id = _process(file.filename or "upload.csv", await file.read())
    except ValidationError as error:
        return JSONResponse(status_code=422, content={"fehler": str(error)})
    return db.load_report(report_id)


@app.get("/api/reports")
def api_list():
    return db.list_reports()


@app.get("/api/reports/{report_id}")
def api_report(report_id: int):
    return _report_or_404(report_id)


@app.get("/api/reports/{report_id}/export")
def api_export(report_id: int):
    report = _report_or_404(report_id)
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["device", "value", "lower", "upper", "unit", "ergebnis"])
    for row in report["zeilen"]:
        outcome = "innerhalb" if row["innerhalb"] else "ausserhalb"
        writer.writerow([row["device"], row["value"], row["lower"], row["upper"], row["unit"], outcome])
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="bericht-{report_id}.csv"'},
    )


# --- Oberfläche --------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
def index(request: Request, error: Annotated[str, Query(alias="fehler")] = ""):
    reports = db.list_reports() if db.is_ready() else []
    return templates.TemplateResponse(
        request, "index.html", {"title": app_title(), "reports": reports, "error": error}
    )


@app.post("/hochladen")
async def upload(file: Annotated[UploadFile, File(alias="datei")]):
    try:
        report_id = _process(file.filename or "upload.csv", await file.read())
    except ValidationError as error:
        return RedirectResponse(f"/?fehler={quote(str(error))}", status_code=303)
    return RedirectResponse(f"/berichte/{report_id}", status_code=303)


@app.get("/berichte/{report_id}", response_class=HTMLResponse)
def report_page(request: Request, report_id: int):
    return templates.TemplateResponse(
        request, "report.html", {"title": app_title(), "report": _report_or_404(report_id)}
    )
