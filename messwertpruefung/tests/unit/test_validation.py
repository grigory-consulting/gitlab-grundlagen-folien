"""Unit-Tests der Fachlogik. Laufen ohne Datenbank."""

import re

import pytest

from messwert.validation import ValidationError, evaluate, is_within_limits, read_csv

HEADER = "device,value,lower,upper,unit\n"


# --- Grenzprüfung ------------------------------------------------------------


def test_value_in_the_middle_is_within_limits():
    assert is_within_limits(20.3, 19, 21)


def test_value_above_upper_limit_is_outside():
    assert not is_within_limits(23.1, 19, 21)


def test_value_below_lower_limit_is_outside():
    assert not is_within_limits(18.9, 19, 21)


def test_lower_limit_is_within_range():
    assert is_within_limits(19, 19, 21)


def test_upper_limit_is_within_range():
    assert is_within_limits(21, 19, 21)


# --- CSV einlesen ------------------------------------------------------------


def test_valid_file_is_read():
    measurements = read_csv(HEADER + "Sensor-A,20.3,19,21,C\nSensor-B,23.1,19,21,C\n")
    assert [m.device for m in measurements] == ["Sensor-A", "Sensor-B"]
    assert measurements[0].value == 20.3


def test_value_outside_is_result_not_error():
    results = evaluate(read_csv(HEADER + "Sensor-B,23.1,19,21,C\n"))
    assert results[0].within_limits is False


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("device,value,lower,unit\nS,1,0,C\n", "Pflichtspalten fehlen: upper"),
        (HEADER, "keine Messzeilen"),
        (HEADER + ",20,19,21,C\n", "Zeile 2: Gerätekennung fehlt"),
        (HEADER + "S,abc,19,21,C\n", "Zeile 2: 'value' ist keine Zahl"),
        (HEADER + "S,nan,19,21,C\n", "Zeile 2: 'value' ist nicht endlich"),
        (HEADER + "S,20,22,21,C\n", "Zeile 2: lower (22.0) ist größer als upper (21.0)"),
        (HEADER + "S,20,19,21,C\nT,20,19,x,C\n", "Zeile 3: 'upper' ist keine Zahl"),
    ],
    ids=["missing-column", "empty", "no-device", "not-a-number", "nan", "limits-swapped", "line-3"],
)
def test_invalid_file_is_rejected(content, message):
    with pytest.raises(ValidationError, match=re.escape(message)):
        read_csv(content)
