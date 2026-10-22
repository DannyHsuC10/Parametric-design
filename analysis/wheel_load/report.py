"""Local workflow notes and linked figures/tables for the four wheel-load nodes."""

import csv
import html
from pathlib import Path
import re

from app.analysis_result import load_plot_choices
from app.markdown_renderer import render_markdown, render_markdown_file
from .parameters import STAGES, TITLES


def write_reports(results_dir):
    root = Path(results_dir)
    folder = root / "wheel_load"
    folder.mkdir(parents=True, exist_ok=True)
    notes = Path(__file__).with_name("README.md").read_text(encoding="utf-8")
    note_sections = {
        section.splitlines()[0]: section.rstrip()
        for section in re.split(r"(?m)(?=^## )", notes)
        if section.startswith("## ")
    }
    (folder / "workflow.md").write_text(notes, encoding="utf-8")
    sections = ["<hr><h1>已儲存分析結果</h1><p>下列內容為各節點最近一次儲存的結果；執行整套輪載流程可更新全部節點。</p>"]
    if (root / "wheel_load_comparison" / "index.html").exists():
        sections.append('<p><a href="../wheel_load_comparison/index.html">原始 new 程式與整合版的同參數比較</a></p>')
    for stage, title in zip(STAGES, TITLES):
        destination = root / stage
        if not (destination / "result.csv").exists():
            continue
        stage_section = next(section for heading, section in note_sections.items()
                             if heading.startswith(f"## {stage}："))
        stage_notes = (f"# {title}：計算方程式\n\n"
                       + note_sections["## 共用符號與單位"] + "\n\n"
                       + stage_section + "\n\n"
                       + note_sections["## 流程與執行方式"] + "\n")
        (destination / "analysis.md").write_text(stage_notes, encoding="utf-8")
        render_markdown_file(destination / "analysis.md")
        sections.append(f"<section><h2>{html.escape(title)}</h2>")
        with (destination / "result.csv").open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        sections.append("<details><summary>本次輸入與導出量</summary><table><tr><th>類別</th><th>變量</th><th>數值</th></tr>")
        for row in rows:
            cells = (html.escape(row[key]) for key in ("category", "name", "number"))
            sections.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
        sections.append("</table></details>")
        for label, filename in load_plot_choices(destination):
            sections.append(f'<figure><figcaption>{html.escape(label)}</figcaption>'
                            f'<img style="width:100%;max-width:1200px" src="../{stage}/{html.escape(filename, quote=True)}"></figure>')
        sections.append("<p>CSV： " + " / ".join(
            f'<a href="../{stage}/{path.name}">{path.name}</a>' for path in sorted(destination.glob("*.csv"))) + "</p></section>")
    document = render_markdown(notes).replace("</body>", "\n".join(sections) + "</body>")
    (folder / "index.html").write_text(document, encoding="utf-8")
