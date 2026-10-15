import argparse
import csv
import re
from pathlib import Path

import pdfplumber


PDF_DIR = Path("PDF_file")
OUTPUT_FILE = Path("FSAEJ_text_vehicle_database.csv")

GERMAN_COLUMNS = [
    "team",
    "team_id",
    "year",
    "car_title",
    "University",
    "Location",
    "Homepage",
    "Social Media",
    "CV Team",
    "DV Team",
    "Short Link",
    "Frame Construction",
    "Material",
    "Overall L",
    "Overall W",
    "Overall H",
    "Wheelbase",
    "Track (Fr)",
    "Track (Rr)",
    "Weight with 68kg driver (Fr)",
    "Weight with 68kg driver (Rr)",
    "Suspension",
    "Tyres (Fr / Rr)",
    "Wheels (Fr / Rr)",
    "Drive Type",
    "Differential",
    "Cooling",
    "Brake System",
    "Electronics",
    "Number of Motors",
    "Motor Location",
    "Max Motor Power (per motor)",
    "Motor Type",
    "Max Motor RPM (highest)",
    "Motor Controller",
    "Max System Voltage",
    "Electrode Materials",
    "Combined Accumulator Capacity",
    "Transmission Ratio (Primary)",
    "Transmission Ratio (Secondary)",
    "Processing unit(s)",
    "Floating Point Operations Per Second of all processing units that are working for the DV system",
    "Power consumption of all processing units that are working for the DV system",
    "Camera(s)",
    "Radar sensor(s)",
    "Lidar sensor(s)",
    "Other sensors",
    "Highlights of the DV system",
    "Engine",
    "Bore",
    "Stroke",
    "Cylinders",
    "Displacement",
    "Compression Ratio",
    "Fuel System",
    "Fuel",
    "Max Power Design",
    "Max Torque Design",
]


def main():
    parser = argparse.ArgumentParser(description="Parse text-based FSAE Japan program PDFs into CSV.")
    parser.add_argument("--pdf-dir", default=str(PDF_DIR))
    parser.add_argument("--output", default=str(OUTPUT_FILE))
    args = parser.parse_args()

    rows = []
    for pdf_path in sorted(Path(args.pdf_dir).glob("program*.pdf")):
        year = infer_year(pdf_path.name)
        print(f"[text] {pdf_path.name} year={year}")
        rows.extend(parse_pdf(pdf_path, year))

    write_csv(rows, Path(args.output))
    print(f"saved {len(rows)} rows to {args.output}")


def infer_year(filename: str) -> int | str:
    match = re.search(r"program(\d{1,2})", filename, re.I)
    if not match:
        return ""
    yy = int(match.group(1))
    # In the supplied files, program20 is 2022, so the event year is issue + 2002.
    return 2002 + yy if yy >= 7 else ""


def parse_pdf(pdf_path: Path, year: int | str) -> list[dict]:
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        pending = {}
        for page_number, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables() or []
            for table in tables:
                if not table or len(table) < 3:
                    continue
                normalized_header = " ".join(clean_cell(cell) for cell in table[0] if cell)
                if "Car No" in normalized_header or "School Name" in normalized_header:
                    for data_row in table[2:]:
                        item = parse_basic_row(data_row, year, pdf_path.name, page_number)
                        if item:
                            pending[item["car_title"]] = item
                            rows.append(item)
                elif any(token in normalized_header for token in ["Wheels", "Engine", "ﾎｲ", "タイヤ", "タｲヤ", "エンジン"]):
                    detail_rows = [row for row in table[2:] if row and any(clean_cell(cell) for cell in row)]
                    basic_keys = [key for key in pending if pending[key].get("_needs_detail")]
                    for key, data_row in zip(basic_keys, detail_rows):
                        parse_detail_row(pending[key], data_row)
                        pending[key]["_needs_detail"] = False

    for row in rows:
        row.pop("_needs_detail", None)
    return rows


def parse_basic_row(row: list[str | None], year: int | str, source: str, page_number: int) -> dict | None:
    row = normalize_row(row, 8)
    car_no = clean_cell(row[0])
    if not re.search(r"\d", car_no):
        return None

    school = clean_cell(row[1])
    dimensions = clean_cell(row[6])
    weight = clean_cell(row[7])
    team_name, university = split_school_name(school)
    dim_values = numbered_values(dimensions)
    weight_values = numbered_values(weight)
    dimensions = parse_dimensions(dim_values)
    weights = parse_weights(weight_values)

    data = blank_row()
    data.update(
        {
            "team": team_name or university or f"Car {car_no}",
            "team_id": car_no,
            "year": str(year),
            "car_title": f"Car #{car_no}",
            "University": university or team_name,
            "Frame Construction": clean_cell(row[3]),
            "Material": clean_cell(row[4]),
            "Suspension": clean_cell(row[5]),
            "Overall L": dimensions["Overall L"],
            "Overall H": dimensions["Overall H"],
            "Wheelbase": dimensions["Wheelbase"],
            "Track (Fr)": dimensions["Track (Fr)"],
            "Track (Rr)": dimensions["Track (Rr)"],
            "Weight with 68kg driver (Fr)": weights["front"],
            "Weight with 68kg driver (Rr)": weights["rear"],
            "Highlights of the DV system": "",
            "source_pdf": source,
            "source_page": str(page_number),
            "_needs_detail": True,
        }
    )
    return data


def parse_detail_row(data: dict, row: list[str | None]) -> None:
    row = normalize_row(row, 8)
    wheel_tyre = clean_cell(row[1])
    engine = clean_cell(row[2])
    induction = clean_cell(row[3])
    final_drive = clean_cell(row[5])

    engine_values = numbered_values(engine)
    data.update(
        {
            "Tyres (Fr / Rr)": wheel_tyre,
            "Wheels (Fr / Rr)": wheel_tyre,
            "Engine": engine_values.get("1", engine),
            "Displacement": engine_values.get("2", ""),
            "Max Power Design": engine_values.get("3", ""),
            "Max Torque Design": engine_values.get("4", ""),
            "Fuel System": induction,
            "Drive Type": final_drive,
            "Differential": final_drive,
            "Transmission Ratio (Primary)": clean_cell(row[4]),
            "Brake System": clean_cell(row[6]),
            "Electronics": clean_cell(row[7]),
        }
    )


def blank_row() -> dict:
    row = {col: "" for col in GERMAN_COLUMNS}
    row["source_pdf"] = ""
    row["source_page"] = ""
    return row


def write_csv(rows: list[dict], output: Path) -> None:
    fieldnames = GERMAN_COLUMNS + ["source_pdf", "source_page"]
    with output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def clean_cell(value: str | None) -> str:
    if not value:
        return ""
    value = str(value).replace("\n", " ")
    value = collapse_pdf_double_text(value)
    value = value.replace("：", ":").replace("×", "x")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def collapse_pdf_double_text(text: str) -> str:
    # Some old PDFs extract English/Japanese glyphs as doubled adjacent characters.
    duplicate_pairs = 0
    i = 0
    while i + 1 < len(text):
        if text[i] == text[i + 1] and text[i] not in "\n\r\t " and not text[i].isdigit():
            duplicate_pairs += 1
            i += 2
        else:
            i += 1
    if duplicate_pairs < 3:
        return text

    out = []
    i = 0
    while i < len(text):
        if i + 1 < len(text) and text[i] == text[i + 1] and text[i] not in "\n\r\t " and not text[i].isdigit():
            out.append(text[i])
            i += 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def normalize_row(row: list[str | None], size: int) -> list[str | None]:
    row = list(row or [])
    if len(row) < size:
        row.extend([""] * (size - len(row)))
    return row


def split_school_name(text: str) -> tuple[str, str]:
    if not text:
        return "", ""
    parts = text.split()
    english = " ".join(part for part in parts if re.search(r"[A-Za-z]", part))
    japanese = " ".join(part for part in parts if not re.search(r"[A-Za-z]", part))
    return english or japanese, japanese or english


def numbered_values(text: str) -> dict[str, str]:
    values = {}
    if not text:
        return values
    markers = list(re.finditer(r"[①②③④⑤]", text))
    for index, marker in enumerate(markers):
        key = str("①②③④⑤".index(marker.group(0)) + 1)
        start = marker.end()
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        values[key] = text[start:end].strip()
    return values


def split_weight(text: str) -> tuple[str, str]:
    match = re.search(r"(\d+(?:\.\d+)?)\s*[:：]\s*(\d+(?:\.\d+)?)", text)
    if not match:
        return "", ""
    front = float(match.group(1))
    rear = float(match.group(2))
    total = front + rear
    if total <= 0:
        return "", ""
    # This is a distribution percentage, not absolute weight; keep the original meaning explicit.
    return f"{front:g}%", f"{rear:g}%"


def parse_weights(values: dict[str, str]) -> dict[str, str]:
    vehicle_mass = parse_vehicle_mass_kg(values.get("1", ""))
    dist = parse_weight_distribution(values.get("2", ""))
    if vehicle_mass is None or dist is None:
        return {"front": "", "rear": ""}

    total_with_driver = vehicle_mass + 68
    if total_with_driver < 150:
        return {"front": "", "rear": ""}

    front_ratio, rear_ratio = dist
    ratio_total = front_ratio + rear_ratio
    if ratio_total <= 0:
        return {"front": "", "rear": ""}

    front = total_with_driver * front_ratio / ratio_total
    rear = total_with_driver * rear_ratio / ratio_total
    if abs((front + rear) - total_with_driver) > max(2, total_with_driver * 0.02):
        return {"front": "", "rear": ""}
    return {"front": f"{front:.1f} kg", "rear": f"{rear:.1f} kg"}


def parse_vehicle_mass_kg(text: str) -> float | None:
    text = clean_cell(text).replace("，", ",").replace("．", ".")
    digits = re.sub(r"\D", "", text)
    if len(digits) < 3:
        return None
    vehicle_mass = int(digits[:3])
    if vehicle_mass > 450:
        return None
    return float(vehicle_mass)


def parse_kg(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*k?g\b", clean_cell(text), re.I)
    if not match:
        match = re.search(r"(\d+(?:\.\d+)?)", clean_cell(text))
    return float(match.group(1)) if match else None


def parse_weight_distribution(text: str) -> tuple[float, float] | None:
    text = clean_cell(text)
    match = re.search(r"(\d+(?:\.\d+)?)\s*[:：]\s*(\d+(?:\.\d+)?)", text)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def parse_dimensions(values: dict[str, str]) -> dict[str, str]:
    overall_l = normalize_mm(values.get("1", ""))
    overall_h = normalize_mm(values.get("2", ""))
    wheelbase = normalize_mm(values.get("3", ""))
    front_track = normalize_mm(values.get("4", ""))
    rear_track = normalize_mm(values.get("5", ""))

    wheelbase_value = parse_mm(wheelbase)
    if wheelbase_value is not None and wheelbase_value <= 1525:
        wheelbase = ""

    front_track_value = parse_mm(front_track)
    rear_track_value = parse_mm(rear_track)
    if front_track_value and rear_track_value:
        ratio = front_track_value / rear_track_value
        if ratio < 0.75 or ratio > 1.35:
            front_track = ""
            rear_track = ""

    return {
        "Overall L": overall_l,
        "Overall H": overall_h,
        "Wheelbase": wheelbase,
        "Track (Fr)": front_track,
        "Track (Rr)": rear_track,
    }


def normalize_mm(text: str) -> str:
    value = parse_raw_mm(text)
    return f"{value:g} mm" if value is not None else ""


def parse_raw_mm(text: str) -> float | None:
    text = clean_cell(text)
    if not text:
        return None
    text = text.replace("ｍ", "m").replace("Ｍ", "m").replace("，", ",").replace("．", ".")
    for match in re.finditer(r"\d[\d,.]*", text):
        token = match.group(0)
        digits = re.sub(r"\D", "", token)
        if len(digits) < 4:
            continue
        value = int(digits[:4])
        if 1000 <= value <= 4000:
            return float(value)
    return None


def parse_mm(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*mm\b", clean_cell(text).replace("ｍ", "m"), re.I)
    return float(match.group(1)) if match else None


if __name__ == "__main__":
    main()
