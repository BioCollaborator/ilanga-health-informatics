"""
South African ID number utilities.

Structure of a 13-digit SA ID number:  YYMMDD SSSS C A Z
    YYMMDD  date of birth
    SSSS    sequence; 0000-4999 registered female, 5000-9999 registered male
    C       0 = SA citizen, 1 = permanent resident
    A       historically 8 or 9 (no longer meaningful)
    Z       check digit (Luhn algorithm)

Every ID produced by this course is SYNTHETIC. It follows the format so that
validation code behaves realistically, but it is generated at random and is not
linked to any real person.
"""
from __future__ import annotations

import datetime as _dt


def luhn_check_digit(first12: str) -> int:
    """Return the Luhn check digit for the first 12 digits of an SA ID."""
    if len(first12) != 12 or not first12.isdigit():
        raise ValueError("first12 must be exactly 12 digits")
    total = 0
    # Walk from the right; the rightmost payload digit is doubled.
    for i, ch in enumerate(reversed(first12)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return (10 - total % 10) % 10


def _luhn_ok(number: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def make_sa_id(dob: _dt.date, sex: str, sequence: int, citizen: bool = True) -> str:
    """Build a synthetic, format-valid SA ID number."""
    if sex not in ("F", "M"):
        raise ValueError("sex must be 'F' or 'M'")
    seq = int(sequence) % 5000 + (5000 if sex == "M" else 0)
    first12 = f"{dob:%y%m%d}{seq:04d}{0 if citizen else 1}8"
    return first12 + str(luhn_check_digit(first12))


def parse(id_number: str, reference_year: int = 2025) -> dict:
    """Decode the parts of an SA ID number (no validity guarantee)."""
    s = str(id_number)
    yy, mm, dd = int(s[0:2]), int(s[2:4]), int(s[4:6])
    century = 2000 if yy <= reference_year % 100 else 1900
    return {
        "dob": f"{century + yy:04d}-{mm:02d}-{dd:02d}",
        "sex_digit_says": "F" if int(s[6:10]) < 5000 else "M",
        "citizenship": {"0": "SA citizen", "1": "Permanent resident"}.get(s[10], "Unknown"),
        "check_digit": int(s[12]),
    }


def is_valid(id_number) -> bool:
    """True if the value is 13 digits, has a real calendar date and passes Luhn."""
    if id_number is None:
        return False
    s = str(id_number).strip()
    if len(s) != 13 or not s.isdigit():
        return False
    try:
        _dt.date(2000, int(s[2:4]), int(s[4:6]))  # leap-year-safe month/day check
    except ValueError:
        return False
    return _luhn_ok(s)
