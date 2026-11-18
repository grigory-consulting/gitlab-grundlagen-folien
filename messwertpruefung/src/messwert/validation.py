"""Fachlogik der Messwertprüfung: CSV einlesen und Messwerte gegen Grenzen prüfen.

Vertrag:
- Beide Grenzen gehören zum zulässigen Bereich: lower <= value <= upper.
- Eine strukturell ungültige Datei wird vollständig abgelehnt (ValidationError).
- Ein Wert außerhalb der Grenzen ist ein gültiges Ergebnis, kein Fehler.
"""

import csv
import io
import math
from dataclasses import dataclass

REQUIRED_COLUMNS = ("device", "value", "lower", "upper", "unit")


class ValidationError(ValueError):
    """Die CSV-Datei verletzt das vereinbarte Format."""


@dataclass(frozen=True)
class Measurement:
    device: str
    value: float
    lower: float
    upper: float
    unit: str


@dataclass(frozen=True)
class Result:
    measurement: Measurement
    within_limits: bool


def is_within_limits(value: float, lower: float, upper: float) -> bool:
    """True, wenn der Wert im zulässigen Bereich liegt (beide Grenzen inklusive)."""
    return lower <= value <= upper


def _number(text: str, column: str, line: int) -> float:
    try:
        number = float(text)
    except ValueError:
        raise ValidationError(f"Zeile {line}: '{column}' ist keine Zahl: {text!r}") from None
    if not math.isfinite(number):
        raise ValidationError(f"Zeile {line}: '{column}' ist nicht endlich: {text!r}")
    return number


def read_csv(content: str) -> list[Measurement]:
    """Liest CSV-Text (Komma, Dezimalpunkt) und liefert die Messwerte."""
    reader = csv.DictReader(io.StringIO(content))
    missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise ValidationError(f"Pflichtspalten fehlen: {', '.join(missing)}")

    measurements = []
    # Zeile 1 ist die Kopfzeile, die erste Messzeile ist Zeile 2.
    for line, row in enumerate(reader, start=2):
        device = (row["device"] or "").strip()
        if not device:
            raise ValidationError(f"Zeile {line}: Gerätekennung fehlt")
        lower = _number(row["lower"], "lower", line)
        upper = _number(row["upper"], "upper", line)
        if lower > upper:
            raise ValidationError(f"Zeile {line}: lower ({lower}) ist größer als upper ({upper})")
        value = _number(row["value"], "value", line)
        measurements.append(Measurement(device, value, lower, upper, (row["unit"] or "").strip()))

    if not measurements:
        raise ValidationError("Die Datei enthält keine Messzeilen")
    return measurements


def evaluate(measurements: list[Measurement]) -> list[Result]:
    """Prüft jeden Messwert gegen seine Grenzen."""
    return [Result(m, is_within_limits(m.value, m.lower, m.upper)) for m in measurements]
