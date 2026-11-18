# Produktimage der Messwertprüfung.
# Erwartet das fertige Wheel in dist/ (erzeugt vom Pipeline-Job build_wheel).
FROM python:3.13-slim

# Commit, aus dem das Image gebaut wurde; die Anwendung zeigt ihn unter /health.
ARG BUILD_COMMIT=unbekannt
ENV BUILD_COMMIT=$BUILD_COMMIT \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Erst die festgeschriebenen Abhängigkeiten, dann das eigene Paket ohne weitere Abhängigkeiten.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY dist/*.whl /tmp/
RUN pip install --no-cache-dir --no-deps /tmp/*.whl && rm /tmp/*.whl

# Nicht als root laufen.
USER 10001:10001
EXPOSE 8080
CMD ["uvicorn", "messwert.app:app", "--host", "0.0.0.0", "--port", "8080"]
