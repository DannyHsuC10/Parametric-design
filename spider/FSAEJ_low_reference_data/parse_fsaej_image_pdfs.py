import argparse
import csv
import re
import shutil
import subprocess
from pathlib import Path

import pdfplumber
from PIL import Image

from parse_fsaej_text_pdfs import (
    GERMAN_COLUMNS,
    blank_row,
    clean_cell,
    normalize_mm,
    parse_kg,
    parse_mm,
    parse_raw_mm,
    parse_vehicle_mass_kg,
    parse_weight_distribution,
    write_csv,
)


PDF_DIR = Path("PDF_file")
OUTPUT_FILE = Path("FSAEJ_image_vehicle_database.csv")
TMP_DIR = Path("tmp/fsaej_image_pages")
PDFTOPPM = Path(r"C:\Users\Danny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe")


def main():
    parser = argparse.ArgumentParser(description="Parse image-based FSAE Japan program PDFs into CSV using OCR.")
    parser.add_argument("--pdf-dir", default=str(PDF_DIR))
    parser.add_argument("--output", default=str(OUTPUT_FILE))
    parser.add_argument("--lang", default="jpn+eng")
    parser.add_argument("--dpi", type=int, default=220)
    parser.add_argument("--tesseract-path", default="")
    parser.add_argument("--keep-images", action="store_true")
    args = parser.parse_args()

    tesseract = find_tesseract(args.tesseract_path)
    rows = []
    for pdf_path in sorted(Path(args.pdf_dir).glob("*.pdf")):
        if not is_image_pdf_name(pdf_path.name):
            continue
        year = infer_year(pdf_path.name)
        print(f"[image] {pdf_path.name} year={year}")
        parsed_rows = parse_pdf_text_layer(pdf_path, year)
        if parsed_rows:
            print(f"  used embedded text layer: {len(parsed_rows)} rows")
            rows.extend(parsed_rows)
            continue
        if not tesseract:
            print("  WARNING: no usable embedded text and tesseract was not found; skipped OCR for this PDF.")
            continue
        parsed_rows = parse_pdf_with_ocr(pdf_path, year, tesseract, args.lang, args.dpi)
        print(f"  used tesseract OCR: {len(parsed_rows)} rows")
        rows.extend(parsed_rows)

    write_csv(rows, Path(args.output))
    print(f"saved {len(rows)} rows to {args.output}")
    if not args.keep_images:
        cleanup_tmp()


def find_tesseract(user_path: str = "") -> str:
    candidates = [
        user_path,
        shutil.which("tesseract") or "",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(Path(candidate))
    print("WARNING: tesseract was not found. Pure image PDFs require Tesseract OCR plus Japanese language data.")
    print("         You can pass it explicitly with --tesseract-path \"C:\\Program Files\\Tesseract-OCR\\tesseract.exe\".")
    return ""


def is_image_pdf_name(filename: str) -> bool:
    return filename.startswith("学生フォーミュラ") or filename.startswith("FSAEJ")


def infer_year(filename: str) -> int | str:
    match = re.search(r"(20\d{2})", filename)
    return int(match.group(1)) if match else ""


def parse_pdf_with_ocr(pdf_path: Path, year: int | str, tesseract: str, lang: str, dpi: int) -> list[dict]:
    page_images = render_pages(pdf_path, dpi)
    rows = []
    for page_image in page_images:
        text = ocr_image(page_image, tesseract, lang)
        if not looks_like_team_info(text):
            continue
        rows.extend(parse_ocr_page(text, year, pdf_path.name, source_page_from_image(page_image)))
    return rows


def parse_pdf_text_layer(pdf_path: Path, year: int | str) -> list[dict]:
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
            if "Technical" not in text and "OVRALL" not in text and "OVERALL" not in text:
                continue
            rows.extend(parse_modern_specs_page(text, year, pdf_path.name, str(page_number)))
    return rows


def render_pages(pdf_path: Path, dpi: int) -> list[Path]:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    prefix = TMP_DIR / pdf_path.stem
    command = [str(PDFTOPPM), "-png", "-r", str(dpi), str(pdf_path), str(prefix)]
    subprocess.run(command, check=True)
    return sorted(TMP_DIR.glob(f"{pdf_path.stem}-*.png"))


def ocr_image(image_path: Path, tesseract: str, lang: str) -> str:
    # Touch the file with PIL first so corrupt render output fails clearly.
    with Image.open(image_path) as image:
        image.verify()
    command = [tesseract, str(image_path), "stdout", "-l", lang, "--psm", "6"]
    result = subprocess.run(command, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.stdout


def looks_like_team_info(text: str) -> bool:
    lowered = text.lower()
    return (
        "team information" in lowered
        or "vehicle" in lowered
        or "車両" in text
        or re.search(r"\bE?\d{1,3}\b", text)
    )


def parse_ocr_page(text: str, year: int | str, source_pdf: str, source_page: str) -> list[dict]:
    modern_rows = parse_modern_specs_page(text, year, source_pdf, source_page)
    if modern_rows:
        return modern_rows

    blocks = split_team_blocks(text)
    rows = []
    for block in blocks:
        row = parse_team_block(block, year, source_pdf, source_page)
        if row:
            rows.append(row)
    return rows


def parse_modern_specs_page(text: str, year: int | str, source_pdf: str, source_page: str) -> list[dict]:
    normalized = normalize_ocr_text(text)
    if "Technical Specs" not in normalized and "Technical Snecs" not in normalized:
        return []

    markers = list(re.finditer(r"Technical\s+S(?:p|n)ecs", normalized, re.I))
    rows = []
    for index, marker in enumerate(markers):
        segment_start = marker.start()
        segment_end = markers[index + 1].start() if index + 1 < len(markers) else len(normalized)
        segment = normalized[segment_start:segment_end]
        context = normalized[max(0, segment_start - 900):segment_start]
        row = parse_modern_specs_block(segment, context, year, source_pdf, source_page, index + 1)
        if row:
            rows.append(row)
    return rows


def normalize_ocr_text(text: str) -> str:
    text = clean_cell(text)
    replacements = {
        "Snecs": "Specs",
        "OVRALL": "OVERALL",
        "OVRAL": "OVERALL",
        "WHEL": "WHEEL",
        "WHELS": "WHEELS",
        "Monocoaue": "Monocoque",
        "Soaceframe": "Spaceframe",
        "Hoosler": "Hoosier",
        "ke": "kg",
        "BRAkg": "BRAKE",
    }
    for old, new in replacements.items():
        text = re.sub(old, new, text, flags=re.I)
    return text


def parse_modern_specs_block(
    segment: str,
    context: str,
    year: int | str,
    source_pdf: str,
    source_page: str,
    entry_index: int,
) -> dict | None:
    team, car_no = extract_modern_team_identity(context, source_page, entry_index)
    row = blank_row()
    row.update(
        {
            "team": team or f"Car {car_no}",
            "team_id": car_no,
            "year": str(year),
            "car_title": f"Car #{car_no}",
            "University": team,
            "source_pdf": source_pdf,
            "source_page": source_page,
        }
    )

    dimensions = parse_slash_numbers(find_value_after_label(segment, r"OVERALL\s+L/?W/?H"), 3)
    if len(dimensions) == 3:
        row["Overall L"] = format_mm(dimensions[0])
        row["Overall H"] = format_mm(dimensions[2])

    tracks = parse_slash_numbers(find_value_after_label(segment, r"WHEEL\s*BASE/TRACK\s*\(F[^\)]*\)"), 3)
    if len(tracks) == 3:
        row["Wheelbase"] = format_mm(tracks[0])
        row["Track (Fr)"] = format_mm(tracks[1])
        row["Track (Rr)"] = format_mm(tracks[2])

    weights = parse_slash_numbers(find_value_after_label(segment, r"WEIGHT\s*\(F[^\)]*\)"), 3)
    if len(weights) >= 3:
        fill_weight_from_total_front_rear(row, weights[0], weights[1], weights[2])

    row["Frame Construction"] = find_text_value(segment, "FRAME CONSTRUCTION", ["MATERIAL", "DISPLACEMENT"])
    row["Material"] = find_text_value(segment, "MATERIAL", ["MAX POWER", "OVERALL"])
    row["Engine"] = find_text_value(segment, "ENGINE", ["DISPLACEMENT", "FRAME CONSTRUCTION"])
    row["Displacement"] = find_text_value(segment, "DISPLACEMENT", ["MAX POWER", "MATERIAL"])
    row["Max Power Design"] = find_text_value(segment, "MAX POWER", ["TORQUE DESIGN", "OVERALL"])
    row["Max Torque Design"] = find_text_value(segment, "TORQUE DESIGN", ["INDUCTION TYPE", "WHEEL BASE"])
    row["Fuel System"] = find_text_value(segment, "INDUCTION TYPE", ["FUEL TANK VOLUME", "WEIGHT"])
    row["Drive Type"] = find_text_value(segment, "DRIVE TYPE", ["DIFFERENTIAL", "SUSPENSION"])
    row["Differential"] = find_text_value(segment, "DIFFERENTIAL", ["TYRES", "BRAKE SYSTEM"])
    row["Brake System"] = find_text_value(segment, "BRAKE SYSTEM", ["UNIQUE FEATURES", "UNIGUE FEATURES"])
    row["Tyres (Fr / Rr)"] = find_text_value(segment, "TYRES", ["WHEELS", "BRAKE SYSTEM"])
    row["Wheels (Fr / Rr)"] = find_text_value(segment, "WHEELS", ["UNIQUE FEATURES", "UNIGUE FEATURES"])
    row["Suspension"] = find_text_value(segment, "SUSPENSION", ["DRIVE TYPE", "TYRES"])
    row["Highlights of the DV system"] = find_text_value(segment, "UNIQUE FEATURES", [])

    validate_dimension_fields(row)
    return row


def extract_modern_team_identity(context: str, source_page: str, entry_index: int) -> tuple[str, str]:
    car_match = re.search(r"\b([CE]\d{2,3})\b", context)
    car_no = car_match.group(1) if car_match else f"{source_page}-{entry_index}"
    candidates = []
    for line in context.split(" | "):
        line = clean_cell(line)
        if not line or len(line) > 90:
            continue
        if re.search(r"University|Institute|College|Technology|Academy|School|高専|大学", line, re.I):
            candidates.append(line)
    team = candidates[-1] if candidates else ""
    return team, car_no


def find_value_after_label(segment: str, label: str) -> str:
    match = re.search(label + r"(.{0,100})", segment, re.I)
    return match.group(1) if match else ""


def parse_slash_numbers(text: str, expected: int) -> list[float]:
    values = []
    for match in re.finditer(r"\d[\d,.]*", text):
        raw = match.group(0)
        if "," in raw or "." in raw and len(re.sub(r"\D", "", raw)) == 4:
            mm_value = parse_raw_mm(raw)
            if mm_value is not None:
                values.append(mm_value)
                continue
        cleaned = raw.replace(",", "")
        try:
            values.append(float(cleaned))
        except ValueError:
            continue
        if len(values) >= expected:
            break
    return values


def format_mm(value: float) -> str:
    if 1000 <= value <= 4000:
        return f"{value:g} mm"
    return ""


def fill_weight_from_total_front_rear(row: dict, vehicle_mass: float, front: float, rear: float) -> None:
    if vehicle_mass > 450 or vehicle_mass < 82:
        return
    if front <= 0 or rear <= 0 or abs((front + rear) - vehicle_mass) > max(3, vehicle_mass * 0.05):
        return
    total_with_driver = vehicle_mass + 68
    row["Weight with 68kg driver (Fr)"] = f"{total_with_driver * front / vehicle_mass:.1f} kg"
    row["Weight with 68kg driver (Rr)"] = f"{total_with_driver * rear / vehicle_mass:.1f} kg"


def find_text_value(segment: str, label: str, stop_labels: list[str]) -> str:
    pattern = re.escape(label).replace(r"\ ", r"\s+")
    match = re.search(pattern + r"\s+(.{0,180})", segment, re.I)
    if not match:
        return ""
    value = match.group(1)
    for stop_label in stop_labels:
        stop_match = re.search(re.escape(stop_label).replace(r"\ ", r"\s+"), value, re.I)
        if stop_match:
            value = value[:stop_match.start()]
            break
    return clean_cell(value)


def validate_dimension_fields(row: dict) -> None:
    wheelbase_value = parse_mm(row["Wheelbase"])
    if wheelbase_value is not None and wheelbase_value <= 1525:
        row["Wheelbase"] = ""
    front_track = parse_mm(row["Track (Fr)"])
    rear_track = parse_mm(row["Track (Rr)"])
    if front_track and rear_track:
        ratio = front_track / rear_track
        if ratio < 0.75 or ratio > 1.35:
            row["Track (Fr)"] = ""
            row["Track (Rr)"] = ""


def split_team_blocks(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    blocks = []
    current = []
    for line in lines:
        if re.match(r"^(?:E)?\d{1,3}\b", line) and current:
            blocks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks


def parse_team_block(block: str, year: int | str, source_pdf: str, source_page: str) -> dict | None:
    first_line = next((line for line in block.splitlines() if line.strip()), "")
    car_no_match = re.match(r"^(E?\d{1,3})\b\s*(.*)", first_line)
    if not car_no_match:
        return None

    car_no = car_no_match.group(1)
    name = clean_cell(car_no_match.group(2)) or extract_university_name(block)
    row = blank_row()
    row.update(
        {
            "team": name or f"Car {car_no}",
            "team_id": car_no,
            "year": str(year),
            "car_title": f"Car #{car_no}",
            "University": name,
            "Tyres (Fr / Rr)": extract_after_keywords(block, ["タイヤ", "Tire", "Tyre"]),
            "Wheels (Fr / Rr)": extract_after_keywords(block, ["ホイール", "Wheel"]),
            "Frame Construction": extract_after_keywords(block, ["フレーム", "Frame"]),
            "Material": extract_after_keywords(block, ["材", "Material"]),
            "Suspension": extract_after_keywords(block, ["サスペンション", "Suspension"]),
            "Engine": extract_after_keywords(block, ["エンジン", "Engine", "Motor"]),
            "Displacement": extract_after_keywords(block, ["排気量", "Displacement"]),
            "Max Power Design": extract_after_keywords(block, ["最高出力", "Power"]),
            "Max Torque Design": extract_after_keywords(block, ["最大トルク", "Torque"]),
            "Highlights of the DV system": extract_after_keywords(block, ["特徴", "Feature"]),
            "source_pdf": source_pdf,
            "source_page": source_page,
        }
    )
    fill_dimension_fields(row, block)
    fill_weight_fields(row, block)
    return row


def extract_university_name(block: str) -> str:
    for line in block.splitlines()[1:4]:
        if re.search(r"University|Institute|College|大学|高専", line, re.I):
            return clean_cell(line)
    return ""


def extract_after_keywords(block: str, keywords: list[str]) -> str:
    lines = block.splitlines()
    for index, line in enumerate(lines):
        if any(keyword.lower() in line.lower() for keyword in keywords):
            value = re.sub("|".join(re.escape(k) for k in keywords), "", line, flags=re.I).strip(" :：-")
            tail = " ".join(lines[index + 1:index + 3])
            return clean_cell(" ".join(part for part in [value, tail] if part))
    return ""


def fill_dimension_fields(row: dict, block: str) -> None:
    patterns = {
        "Overall L": [r"(?:全長|Overall\s*L(?:ength)?)\D{0,20}(\d{3,4}\s*mm)"],
        "Overall H": [r"(?:全高|Overall\s*H(?:eight)?)\D{0,20}(\d{3,4}\s*mm)"],
        "Wheelbase": [r"(?:ホイールベース|Wheelbase)\D{0,20}(\d{3,4}\s*mm)"],
        "Track (Fr)": [r"(?:フロントトレッド|Front\s*Track)\D{0,20}(\d{3,4}\s*mm)"],
        "Track (Rr)": [r"(?:リアトレッド|Rear\s*Track)\D{0,20}(\d{3,4}\s*mm)"],
    }
    for field, regexes in patterns.items():
        for regex in regexes:
            match = re.search(regex, block, re.I)
            if match:
                row[field] = normalize_mm(match.group(1))
                break
    wheelbase_value = parse_mm(row["Wheelbase"])
    if wheelbase_value is not None and wheelbase_value <= 1525:
        row["Wheelbase"] = ""
    front_track = parse_mm(row["Track (Fr)"])
    rear_track = parse_mm(row["Track (Rr)"])
    if front_track and rear_track:
        ratio = front_track / rear_track
        if ratio < 0.75 or ratio > 1.35:
            row["Track (Fr)"] = ""
            row["Track (Rr)"] = ""


def fill_weight_fields(row: dict, block: str) -> None:
    gross_mass = extract_after_keywords(block, ["Gross Vehicle Mass", "車両総重量", "総重量", "車重"])
    if not gross_mass:
        gross_match = re.search(r"(?:Gross\s*Vehicle\s*Mass|車両総重量|総重量|車重)\D{0,20}(\d[\d,.]*\s*k?g)", block, re.I)
        gross_mass = gross_match.group(1) if gross_match else ""

    dist_text = extract_after_keywords(block, ["Fr.Rr Weight Dist.", "Fr/Rr Weight Dist.", "前後重量配分", "Weight Dist"])
    if not dist_text:
        dist_match = re.search(r"(?:前後重量配分|Weight\s*Dist)[^\d]*(\d+(?:\.\d+)?)\s*[:：]\s*(\d+(?:\.\d+)?)", block, re.I)
        dist_text = dist_match.group(0) if dist_match else ""

    vehicle_mass = parse_vehicle_mass_kg(gross_mass)
    dist = parse_weight_distribution(dist_text)
    if vehicle_mass is None or dist is None:
        return

    total_with_driver = vehicle_mass + 68
    if total_with_driver < 150:
        return

    front_ratio, rear_ratio = dist
    ratio_total = front_ratio + rear_ratio
    if ratio_total <= 0:
        return

    row["Weight with 68kg driver (Fr)"] = f"{total_with_driver * front_ratio / ratio_total:.1f} kg"
    row["Weight with 68kg driver (Rr)"] = f"{total_with_driver * rear_ratio / ratio_total:.1f} kg"


def source_page_from_image(image_path: Path) -> str:
    match = re.search(r"-(\d+)\.png$", image_path.name)
    return str(int(match.group(1))) if match else ""


def cleanup_tmp() -> None:
    if TMP_DIR.exists():
        for path in TMP_DIR.glob("*.png"):
            path.unlink()


if __name__ == "__main__":
    main()
