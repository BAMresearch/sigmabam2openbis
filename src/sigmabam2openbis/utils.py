import re

import pandas as pd

from sigmabam2openbis.maps import NOTE_COLUMNS


def build_notes(row):
    """
    Build 'Notes' by concatenating values from specific columns.
    Empty cells are replaced with 'None'.
    """
    return " | ".join(
        f"{col}: {row.get(col) if pd.notna(row.get(col)) and str(row.get(col)).strip() else 'None'}"
        for col in NOTE_COLUMNS
        if col in row
    )


def clean_concentration_with_log(val):
    """
    Clean a concentration value (as string), remove symbols (<, >, %, etc.),
    convert it to float, and return a validation log message.
    """
    if not isinstance(val, str):
        return (None, "Invalid: not a string")

    original = val.strip()
    val = original.replace("%", "").replace("<", "").replace(">", "")

    if "-" in val:
        return (0.0, f"Range detected in '{original}' → set to 0")

    match = re.search(r"[\d.,]+", val)
    if match:
        num = match.group().replace(",", ".")
        try:
            return (float(num), None)
        except Exception:
            return (None, f"Invalid number in '{original}'")

    return (None, f"Unrecognized format: '{original}'")
