import csv
import html as html_lib
from html.parser import HTMLParser
from pathlib import Path
import re
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

# ==========================================================
# Config & Constants
# ==========================================================
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_ROOT = SCRIPT_DIR.parent
RAW_DATA_DIR = DATA_ROOT / "raw_data"
BASE_URL = "https://www.formulastudent.de/teams/fse/details/tid/{team_id}"
OUTPUT_FILE = RAW_DATA_DIR / "FSG_EV_vehicle_database.csv"

TEAM_LIST = {
    # Australia
    1150: "QUT Motorsport",
    433: "Team Swinburne",
    353: "RMIT Electric Racing",
    253: "Monash Motorsport",
    461: "Formula REV",

    # Austria
    261: "TU Graz Racing Team",
    262: "Joanneum Racing Graz",
    1288: "Campus Tirol Motorsport",
    1332: "JKU Racing Team",
    1151: "FHOOE Racing Team",
    260: "TU Wien Racing",
    1142: "Os.Car Racing Team",

    # Bangladesh
    1577: "Team Bijoy71",
    1536: "KILO FLIGHT",
    1567: "Team Crack Platoon",

    # Belgium
    1211: "VUB Racing",
    1292: "UGent Racing",
    424: "Formula Electric Belgium",
    1316: "Thomas More Innovation",

    # Brazil
    263: "Unicamp E-Racing",
    1101: "Ampera Racing",
    1389: "Itajubá Cheetah E-Racing",
    1365: "Faraday E-Racing",
    264: "Formula FEI Elétrico",
    1095: "EESC-USP Tupã",
    1362: "B'Energy Racing",

    # Bulgaria
    1582: "Sofia University Racing",

    # Canada
    1305: "Team Phantom: SFU Formula SAE Electric",
    1155: "MAC Formula Electric",
    1387: "Formule Polytechnique Montréal",
    430: "Formule ETS",
    400: "McGill Formula Electric",
    265: "Ravens Racing",
    1443: "Formule SAE de l'Université Laval",
    1243: "FSAE Sherbrooke",
    266: "University of Toronto Formula Racing",
    1263: "UW Electric Motorsports",
    1469: "Polar Bear Racing",

    # China
    267: "Beijing Institute of Technology FSAE",
    1148: "AERO",
    1104: "Gspeed Electric Racing",
    1141: "HNU Electric Racing",
    396: "SCUT E-Racing",
    1112: "HFUT racing team",
    1448: "Wonder Racing Team of Electricity",
    1546: "Lushan LS Racing",
    365: "Tongji DIAN Racing Team",
    1296: "RISE Electric Team",
    1454: "AURORA Racing",
    1453: "HUATE Racing Team",
    1102: "HIT Racing Team",
    1463: "VOYAH-WUTE Racing team",
    1429: "AMOY Racing club",

    # Croatia
    1051: "Riteh Racing Team",
    1304: "FESB Racing",
    268: "FSB Racing Team",

    # Czech Republic
    270: "TU Brno Racing",
    1144: "UWB eRacing Team Pilsen",
    269: "EFORCE Prague Formula",

    # Denmark
    1119: "AAU Racing",
    1576: "AU Dolphins",
    1344: "Vermilion Racing",
    1121: "SDU-Vikings",

    # Ecuador
    1426: "UTN Racing Team",
    1544: "FESPE-ELECTRIC",

    # Egypt
    1538: "Arab Academy Motors",
    1140: "Cairo Uni Racing Team",
    1343: "Bue racing team",

    # Estonia
    384: "FS Team Tallinn Electric",

    # Finland
    1029: "Aalto Formula Team",
    272: "Metropolia Motorsport",
    1474: "LPR Motorsports",
    1086: "Tampere Formula Student",

    # France
    1520: "BFS",
    1528: "SigmaRacing",
    1484: "Ecurie Piston Sport Auto",
    1569: "APECS",
    1467: "Formul'INP",
    1320: "EstaCars",
    1504: "ECAM Formula Student Team",
    1584: "Eni Metz Racing Team",
    1481: "Centrale Nantes Formula Student",
    1190: "ISAT Formula Team",
    1516: "ARECE",
    1506: "INSA ROUEN RACING",
    1222: "ESTACA Formula Team",
    1427: "Formula EPF",
    1555: "TLS'e Racing",
    1491: "N7 Racing Team",
    1574: "Troyes Racing Team",
    1533: "INSA Racing Team",

    # Germany
    258: "Ecurie Aix Formula Student Team RWTH Aachen e.V.",
    1197: "AixtremE Racing",
    352: "E-Motion Rennteam Aalen e.V.",
    273: "Running Snail Racing Team",
    339: "StarkStrom Augsburg e.V.",
    399: "Elefant Racing e.V.",
    275: "FaSTTUBe Berlin",
    1482: "Combined University Racing Berlin",
    1210: "greenBEAR",
    1081: "RUB Motorsport",
    277: "Lions Racing Team e.V.",
    278: "Bremergy e.V.",
    657: "T.U.C. Racing e.V.",
    398: "Green Voltage Racing",
    279: "CAT-Racing",
    280: "TU Darmstadt Racing Team e.V.",
    1032: "FaSTDa Racing",
    354: "Fast Forest",
    1205: "Deefholt Dynamics e.V.",
    382: "GET racing Dortmund e. V.",
    359: "ELBFLORACE e.V.",
    1057: "E-Team Duisburg-Essen",
    1282: "E-Traxx Düsseldorf",
    274: "High-Voltage Motorsports e.V.",
    281: "Rennstall Esslingen",
    282: "Racetech Racing Team e.V.",
    1382: "RhoenRacing",
    1241: "Black Forest Performance",
    1023: "Blue Flash Mobility Concepts",
    341: "e-gnition Hamburg",
    1167: "Eleven-O-Six Racing Team",
    283: "HAWKS Racing e.V.",
    284: "HorsePower Hannover",
    1220: "Campus Motorsport Hannover EV",
    1139: "HHN Racing e.V.",
    1169: "HofSpannung Motorsport e.V.",
    351: "Team Starcraft e.V.",
    342: "Schanzer Racing Electric e.V.",
    367: "Kaiserslautern Racing Team",
    254: "KA-RaceIng Electric",
    1021: "High Speed Karlsruhe",
    1120: "Herkules Racing Team Kassel",
    1106: "Infinity Racing - Rennteam der Hochschule Kempten e.V",
    287: "Raceyard E",
    1310: "Rhein-Waal Racing",
    1080: "eMotorsports Cologne",
    1550: "Aurigas Electricus Coloniae",
    288: "Bodensee Racing Team",
    1249: "HSNR Racing",
    1136: "LA eRacing e.V.",
    289: "OWL Racing-Team",
    1226: "Seagulls Luebeck",
    290: "UMD Racing e.V.",
    1127: "Delta Racing Mannheim",
    1072: "CURE",
    370: "Technikum Mittweida Motorsport",
    1408: "mosTEC.racing",
    1290: "eMOTION RACING HRW",
    255: "municHMotorsport",
    336: "TUfast Racing Team e-Technology",
    1274: "ATHENE Racingteam",
    1168: "Racing Power Münster e.V.",
    291: "Strohm und Söhne e.V.",
    1049: "Black Forest Formula Team",
    1198: "IRT electric",
    292: "UPBracing Team E e.V.",
    340: "Rennschmiede Pforzheim e.V.",
    293: "Global Formula Racing (DE)",
    369: "Dynamics e.V.",
    1099: "Evolution Racing Team Saar",
    294: "BRS Motorsport",
    1161: "Rennsteig-Motorsport e.V.",
    295: "Mainfranken Racing",
    296: "Speeding Scientists Siegen e.V.",
    297: "Baltic Racing",
    298: "Rennteam Uni Stuttgart",
    299: "DHBW Engineering Stuttgart e.V.",
    999: "Test Team",
    300: "Einstein Motorsport",
    301: "Formula Student Team Weingarten",
    302: "Scuderia Mensa HS RheinMain Racing",
    1157: "Racing Revolution",
    303: "Team wob-racing",
    1279: "Green Lion Racing",
    304: "WHZ Racing Team",

    # Greece
    1088: "Prom Racing",
    1487: "Poseidon Racing Team",
    1405: "Perseus Racing",
    420: "UoP Racing Team",
    355: "Aristotle University Racing Team Electric",
    1178: "Centaurus Racing Team",
    1460: "Democritus Racing Team",

    # Hungary
    395: "BME Formula Racing Team (FSE)",
    1558: "DEAC Formula Racing",
    1177: "Arrabona Racing Team",
    1527: "Electric Racing Miskolc",
    1428: "Sopiana-e Motorsport",

    # Iceland
    1129: "Team Spark",

    # India
    1052: "Team Vidyuth",
    403: "Team Chimera",
    1364: "Stier Racing",
    427: "ASHWA RACING ELECTRIC",
    1286: "Vega Racing Electric",
    1397: "G-Tron",
    1442: "SKYLINE RACING",
    1466: "PU Power Racing",
    1573: "CHANDIGARH LOINS MOTORS",
    408: "4ze Racing",
    1180: "Raftar Formula Racing Electric",
    1547: "VALOROUS LINE-UP",
    1338: "Smokin' Axles",
    1199: "VITC Formula Electric",
    1561: "FF Motorsports",
    1253: "Pegasus Racing Electric",
    1517: "Velocita E-Racing",
    1509: "Team Amrita Racing Electric",
    402: "Team Defianz Racing Electric",
    1326: "Mechismu Racing Electric",
    1492: "IITG RACING",
    1530: "HITAM RevClusters",
    1564: "Acroracerz",

    # Netherlands
    285: "Formula Student Team Delft",
    256: "University Racing Eindhoven",
    1074: "Green Team Twente",

    # Norway
    611: "Revolve NTNU",

    # Poland
    1258: "PWR Racing Team",
    1048: "AGH Racing Electric",
    1269: "Silesian Greenpower",

    # Spain
    391: "Tecnun eRacing",
    875: "ARUS Racing Team",
    1171: "BCN eMotorsport",

    # Switzerland
    248: "AMZ Racing Team",

    # United Kingdom
    332: "Oxford Brookes Racing",
    333: "UBRacing",
}


# ==========================================================
# Helper Functions
# ==========================================================

class Node:
    def __init__(self, name: str | None, parent: "Node | None" = None, attrs: dict | None = None):
        self.name = name
        self.parent = parent
        self.attrs = attrs or {}
        self.children = []
        self.text = ""

    def get_text(self, separator: str = " ", strip: bool = True) -> str:
        parts = []
        self._collect_text(parts)
        value = separator.join(part for part in parts if part)
        return re.sub(r"\s+", " ", value).strip() if strip else value

    def find_all(self, names: list[str] | str) -> list["Node"]:
        if isinstance(names, str):
            names = [names]
        matches = []
        for child in self.children:
            if child.name in names:
                matches.append(child)
            matches.extend(child.find_all(names))
        return matches

    def find_all_next(self, names: list[str]) -> list["Node"]:
        root = self
        while root.parent is not None:
            root = root.parent

        nodes = flatten_nodes(root)
        try:
            start = nodes.index(self) + 1
        except ValueError:
            start = 0
        return [node for node in nodes[start:] if node.name in names]

    def has_class(self, class_name: str) -> bool:
        return class_name in self.attrs.get("class", "").split()

    def _collect_text(self, parts: list[str]) -> None:
        if self.name is None:
            parts.append(self.text)
            return
        for child in self.children:
            child._collect_text(parts)


class DOMParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, self.current, dict(attrs))
        self.current.children.append(node)
        if tag not in ["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"]:
            self.current = node

    def handle_endtag(self, tag):
        while self.current.parent is not None:
            if self.current.name == tag:
                self.current = self.current.parent
                return
            self.current = self.current.parent

    def handle_data(self, data):
        if data.strip():
            node = Node(None, self.current)
            node.text = data
            self.current.children.append(node)


def parse_html(html: str) -> Node:
    parser = DOMParser()
    parser.feed(html)
    return parser.root


def flatten_nodes(node: Node) -> list[Node]:
    nodes = [node]
    for child in node.children:
        nodes.extend(flatten_nodes(child))
    return nodes


def find_first(root: Node, names: list[str], exact_text: str) -> Node | None:
    for node in flatten_nodes(root):
        if node.name in names and node.get_text(" ", strip=True) == exact_text:
            return node
    return None


def first_text_by_class(root: Node, class_name: str) -> str:
    for node in flatten_nodes(root):
        if node.has_class(class_name):
            return node.get_text(" ", strip=True)
    return ""


def extract_table(table: Node) -> dict[str, str]:
    """從 HTML 元素中解析所有表格欄位與數值"""
    data = {}
    for row in table.find_all("tr"):
        cols = row.find_all(["td", "th"])
        if len(cols) >= 2:
            key = cols[0].get_text(" ", strip=True)
            val = cols[1].get_text(" ", strip=True)
            if key:
                data[key] = val
    return data


def clean_html_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html_lib.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def extract_tables_from_html(block: str) -> dict[str, str]:
    data = {}
    for table_match in re.finditer(r"<table\b[^>]*>(.*?)</table>", block, flags=re.I | re.S):
        table_html = table_match.group(1)
        for row_match in re.finditer(r"<tr\b[^>]*>(.*?)</tr>", table_html, flags=re.I | re.S):
            cells = re.findall(r"<t[hd]\b[^>]*>(.*?)</t[hd]>", row_match.group(1), flags=re.I | re.S)
            if len(cells) >= 2:
                key = clean_html_text(cells[0])
                val = clean_html_text(cells[1])
                if key:
                    data[key] = val
    return data


def timeline_card_blocks(html: str) -> list[str]:
    starts = [
        match.start()
        for match in re.finditer(
            r'<div\b[^>]*class="[^"]*\btimeline-card\b[^"]*"[^>]*data-year=',
            html,
            flags=re.I,
        )
    ]
    blocks = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(html)
        block = html[start:end]
        block = re.split(r"FS past achievements|fs-past-achievements", block, maxsplit=1, flags=re.I)[0]
        blocks.append(block)
    return blocks


def scrape_team(team_id: int, team_name: str) -> list[dict]:
    """抓取單一車隊的歷史車輛規格數據（含年份與車名提取）"""
    print(f"\n[Scraping] {team_name} (ID: {team_id})...")
    url = BASE_URL.format(team_id=team_id)

    try:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=10) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            html = response.read().decode(charset, errors="replace")
    except URLError as e:
        print(f" Failed to fetch page for {team_name}: {e}")
        return []

    team_database = []
    seen_keys = set()

    for order_index, card in enumerate(timeline_card_blocks(html), start=1):
        year_match = re.search(r'data-year="(19\d{2}|20\d{2})"', card)
        year = year_match.group(1) if year_match else ""
        if not re.fullmatch(r"(19\d{2}|20\d{2})", year):
            continue

        if "Car Specifications" not in card:
            continue

        car_number = ""
        car_name = ""
        number_match = re.search(r'class="[^"]*\bcar-number-small\b[^"]*"[^>]*>(.*?)</span>', card, flags=re.I | re.S)
        name_match = re.search(r'class="[^"]*\bcar-name-small\b[^"]*"[^>]*>(.*?)</span>', card, flags=re.I | re.S)
        if number_match:
            car_number = clean_html_text(number_match.group(1))
        if name_match:
            car_name = clean_html_text(name_match.group(1))
        car_title = " ".join(part for part in [car_number, car_name] if part)

        current_data = {
            "team": team_name,
            "team_id": team_id,
            "year": int(year),
            "car_title": car_title,
            "raw_order_index": order_index,
        }

        current_data.update(extract_tables_from_html(card))

        dedupe_key = (
            current_data.get("team_id"),
            current_data.get("year"),
            current_data.get("car_title"),
        )
        if dedupe_key not in seen_keys:
            team_database.append(current_data)
            seen_keys.add(dedupe_key)
        current_data = None

    print(f" -> Cars with specs found: {len(team_database)}")

    return team_database


# ==========================================================
# Main Workflow
# ==========================================================
def main():
    database = []

    for tid, name in TEAM_LIST.items():
        cars = scrape_team(tid, name)
        database.extend(cars)
        time.sleep(1)

    if not database:
        print("\nNo data collected.")
        return

    database = dedupe_and_sort(database)
    cols = ordered_columns(database)

    print(f"\n==========================================")
    print(f"Total cars collected: {len(database)}")
    for row in database[:10]:
        print({key: row.get(key, "") for key in ["team", "year", "car_title"]})

    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(database)
    print(f"\nSuccessfully saved sorted data to {OUTPUT_FILE}")


def dedupe_and_sort(rows: list[dict]) -> list[dict]:
    unique_rows = []
    seen = set()
    for row in rows:
        key = (row.get("team_id"), row.get("year"), row.get("car_title"))
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append(row)

    return sorted(
        unique_rows,
        key=lambda row: (
            str(row.get("team", "")),
            int(row["year"]) if str(row.get("year", "")).isdigit() else 9999,
            str(row.get("car_title", "")),
        ),
    )


def ordered_columns(rows: list[dict]) -> list[str]:
    core_cols = ["team", "team_id", "year", "car_title"]
    columns = []
    for row in rows:
        for col in row:
            if col not in columns and col != "raw_order_index":
                columns.append(col)
    return core_cols + [col for col in columns if col not in core_cols]


if __name__ == "__main__":
    main()
