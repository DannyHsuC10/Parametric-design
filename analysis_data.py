"""Load shared parameters from an analysis CSV file."""

import csv
from pathlib import Path


def load_analysis_parameters(csv_path):
    """Read named numeric parameters from a name,number CSV."""
    path = Path(csv_path)
    with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None or not {"name", "number"}.issubset(reader.fieldnames):
            raise ValueError("CSV must include name and number columns")

        parameters = {
            row["name"].strip(): row["number"].strip()
            for row in reader
            if row.get("name") and row.get("number")
        }

    if not parameters:
        raise ValueError("CSV must contain at least one name,number row")
    return parameters


def parse_analysis_parameters(values, parameter_types):
    """Convert edited parameter strings using each analysis's declared types."""
    parsed = {}
    for name, parameter_type in parameter_types.items():
        if name not in values:
            raise ValueError(f"CSV is missing required parameter: {name}")
        try:
            parsed[name] = int(values[name]) if parameter_type == "int" else float(values[name])
        except (TypeError, ValueError) as error:
            raise ValueError(f"Parameter {name} must be a valid {parameter_type}") from error

    for name, value in parsed.items():
        if name.startswith("num_points") and value < 1:
            raise ValueError(f"{name} must be at least 1")
    return parsed
