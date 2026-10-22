"""Load shared parameters from the analysis CSV file."""

import csv
from pathlib import Path


PARAMETER_ALIASES = {
    "simulation_ms_total_kg": "ms",
    "simulation_mu_kg": "mu",
}


def canonical_parameter_name(name):
    return PARAMETER_ALIASES.get(name, name)


def normalize_analysis_parameters(values):
    """Use one shared mass input; explicit ms/mu values take priority over aliases."""
    normalized = {name: value for name, value in values.items() if name not in PARAMETER_ALIASES}
    for alias, name in PARAMETER_ALIASES.items():
        if name not in normalized and alias in values:
            normalized[name] = values[alias]
    return normalized


def load_analysis_parameters(csv_path):
    """Read named parameters from a name,number CSV."""
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
    return normalize_analysis_parameters(parameters)


def parse_analysis_parameters(values, parameter_types):
    """Convert edited parameter strings using each analysis's declared types."""
    values = normalize_analysis_parameters(values)
    parsed = {}
    for name, parameter_type in parameter_types.items():
        if name not in values:
            raise ValueError(f"CSV is missing required parameter: {name}")
        if parameter_type == "str":
            parsed[name] = str(values[name]).strip()
            if not parsed[name]:
                raise ValueError(f"Parameter {name} must not be empty")
            continue
        try:
            if parameter_type == "int":
                parsed[name] = int(values[name])
            else:
                parsed[name] = float(values[name])
        except (TypeError, ValueError) as error:
            raise ValueError(f"Parameter {name} must be a valid {parameter_type}") from error

    for name, value in parsed.items():
        if name.startswith("num_points") and value < 1:
            raise ValueError(f"{name} must be at least 1")
    return parsed
