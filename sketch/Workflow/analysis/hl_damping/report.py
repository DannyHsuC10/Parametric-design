"""Five local HTML reports, with the same categories as the reference pages."""

import csv
from html import escape
from pathlib import Path

from .parameters import GROUPS, STAGES

REPORTS = {
    "heave": ("02_heave_analysis.html", "ride rate、heave natural frequency、step response 與頻率響應。"),
    "roll": ("03_roll_analysis.html", "sprung roll、front unsprung roll 與 rear unsprung roll 三個自由度；比較理想 modal damping、實體前後 roll damper 拓樸與 1DOF 簡化模型。"),
    "damper": ("04_damper_analysis.html", "將目標阻尼比轉換為 damper force-velocity 曲線。Heave 使用非對稱壓縮／回彈曲線；roll damper 比較 physical fit 與 1DOF sizing。"),
    "independent": ("05_independent_equivalent.html", "將 roll、heave 等效為單輪懸吊設定，分析單輪彈簧、ARB 與阻尼設定架構。"),
    "simulation": ("06_simulation_and_load_cases.html", "包含縱向加速、縱向煞車與側向過彎。準靜態計算檢查彈簧作動量與姿態角；ODE 模擬觀察暫態收斂、峰值與輪胎法向力變化。"),
}

STYLE = """
body{font:16px/1.7 system-ui,'Microsoft JhengHei',sans-serif;margin:auto;padding:32px;max-width:1180px;color:#213247;background:#f5f7fa}
h1,h2{line-height:1.35}a{color:#2468ad}nav{display:flex;gap:18px;flex-wrap:wrap}section{background:white;padding:26px;margin:24px 0;border:1px solid #dce3ed;border-radius:12px}
img{max-width:100%;height:auto}figure{margin:18px 0}figcaption{font-size:14px;color:#617086}table{border-collapse:collapse;font-size:14px;width:100%;white-space:nowrap}
td,th{border:1px solid #dce3ed;padding:7px 10px;text-align:right}th{background:#edf2f8}.table{overflow-x:auto;margin:14px 0}details{margin:16px 0}summary{cursor:pointer;font-weight:600}.note{background:#fff4dc;padding:15px;border-radius:8px}
"""


def _page(title, body):
    nav = "<nav>" + "".join(f'<a href="{filename}">{escape(GROUPS[group])}</a>'
                             for group, (filename, _) in REPORTS.items()) + "</nav>"
    return (f'<!doctype html><html lang="zh-Hant"><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(title)}</title><style>{STYLE}</style><body>'
            f'{nav}<h1>{escape(title)}</h1>{body}</body></html>')


def _table(rows):
    if not rows:
        return ""
    header = "<tr>" + "".join(f"<th>{escape(cell)}</th>" for cell in rows[0]) + "</tr>"
    body = "".join("<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in row) + "</tr>" for row in rows[1:])
    return f'<div class="table"><table>{header}{body}</table></div>'


def write_reports(results_dir):
    root = Path(results_dir)
    destination = root / "hl_damping"
    destination.mkdir(parents=True, exist_ok=True)
    index = "<p>Damped_oscillation_analysis → Heave／Roll → 阻尼器定尺寸與獨立懸吊等效 → 工況與非線性 ODE。</p><ol>"
    for group, (filename, description) in REPORTS.items():
        title = GROUPS[group]
        index += f'<li><a href="{filename}">{escape(title)}</a>：{escape(description)}</li>'
        body = (f"<p>{escape(description)}</p>"
                f'<p><a href="https://taiwantechracing.github.io/Design-Reference/open/HL_damping/outputs/{filename}">原始參考說明</a></p>')
        for stage, (stage_group, stage_title, _, _) in STAGES.items():
            if stage_group != group:
                continue
            folder = root / stage
            body += f"<section><h2>{escape(stage_title)}</h2>"
            if not (folder / "result.csv").exists():
                body += "<p>此小節尚未執行，請在流程圖選擇節點後執行分析。</p></section>"
                continue
            body += f'<p><a href="../{stage}/analysis.md">模型、公式與參數說明</a></p>'
            with (folder / "result.csv").open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.reader(stream))
            body += _table([rows[0]] + [row for row in rows[1:] if row[0] == "導出量"])
            image_files = [folder / "plot.png"] + [path for path in sorted(folder.glob("*.png"))
                if path.name != "plot.png" and not path.name.startswith("fig3_")]
            for path in image_files:
                body += (f'<figure><img loading="lazy" src="../{stage}/{path.name}" alt="{escape(path.stem)}">'
                         f'<figcaption>{escape(path.stem)}</figcaption></figure>')
            for path in sorted(folder.glob("*.csv")):
                body += f'<details><summary>{escape(path.name)}</summary><a href="../{stage}/{path.name}">下載 CSV</a>'
                with path.open(encoding="utf-8-sig", newline="") as stream:
                    rows = list(csv.reader(stream))
                if len(rows) <= 41:
                    body += _table(rows)
                else:
                    body += f"<p>共 {len(rows) - 1} 筆資料；完整數據請開啟 CSV。</p>"
                body += "</details>"
            body += "</section>"
        if group == "simulation":
            body += ('<p class="note">模型使用雙向線性輪胎彈簧。若 Fz 小於零，表示已超出保持接地的假設；'
                     '本模型未計算離地後接觸切換。settling_2_percent_s 空白表示在模擬時間內尚未收斂。</p>')
        (destination / filename).write_text(_page(title, body), encoding="utf-8")
    index += "</ol><p>各類各有兩個可單獨執行的小節點；圖表及完整 CSV 皆保存在對應節點資料夾。</p>"
    (destination / "index.html").write_text(_page("高低速阻尼完整分析", index), encoding="utf-8")
