"""Szenario-Tests mit vorbereiteten CSV-Dateien aus testdata/<SCENARIO>/.

Die Pipeline führt diese Tests je Szenario in einem eigenen Job aus (parallel:matrix).
Aufruf lokal:  SCENARIO=valid pytest tests/scenarios
"""

import os
from pathlib import Path

import pytest

from messwert.validation import ValidationError, evaluate, read_csv

SCENARIO = os.environ.get("SCENARIO", "valid")
DIRECTORY = Path(__file__).parents[2] / "testdata" / SCENARIO
FILES = sorted(DIRECTORY.glob("*.csv"))

if not FILES:
    raise RuntimeError(f"Keine CSV-Dateien für Szenario {SCENARIO!r} in {DIRECTORY}")


def expected_outside(file: Path) -> int:
    # Erste Zeile der Datei: "# erwartet ausserhalb=<Anzahl>"
    header = file.read_text(encoding="utf-8").splitlines()[0]
    return int(header.split("=")[1])


def without_comments(file: Path) -> str:
    return "\n".join(
        line for line in file.read_text(encoding="utf-8").splitlines() if not line.startswith("#")
    )


# Der Szenarioname steht in der Test-ID, damit GitLab die Fälle beider Jobs unterscheiden kann.
@pytest.mark.parametrize("file", FILES, ids=[f"{SCENARIO}-{f.stem}" for f in FILES])
def test_scenario(file):
    content = without_comments(file)
    if SCENARIO == "invalid":
        with pytest.raises(ValidationError):
            read_csv(content)
    else:
        results = evaluate(read_csv(content))
        assert sum(not r.within_limits for r in results) == expected_outside(file)
