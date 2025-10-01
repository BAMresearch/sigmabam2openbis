import re

import pandas as pd

from sigmabam2openbis.maps import NOTE_COLUMNS


def get_bam_username(name: str = "", uppercase: bool = False) -> str | None:
    # """Convert a person's full name into a BAM path format."""
    if not name:
        return None

    # German umlaut replacements
    de_replacements = {"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue"}
    for original, replacement in de_replacements.items():
        name = name.replace(original, replacement)

    # Defining username format
    name_parts = name.strip().split()
    if len(name_parts) != 2:
        return None
    first_letter = name_parts[0][0]
    last_name = name_parts[1][:7]
    username = f"{first_letter}{last_name}"
    if uppercase:
        return username.upper()  # useful for openBIS space names
    return username


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
