"""Render Markdown notes with local SVG equations and Mermaid diagrams."""

import html
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from matplotlib import rc_context
from matplotlib.font_manager import FontProperties
from matplotlib.mathtext import math_to_image

from .document_theme import document_colors


INLINE_PATTERN = re.compile(r"(\$[^$\n]+\$|`[^`]+`|\*\*.+?\*\*)")
ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
RENDERER_FINGERPRINT = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def svg_display_size(svg_data):
    """Return an SVG's CSS pixel size, preserving Matplotlib's point units."""
    root = ET.fromstring(svg_data)

    def pixels(dimension):
        if dimension.endswith("pt"):
            return float(dimension[:-2]) * 96 / 72
        return float(dimension.removesuffix("px"))

    return pixels(root.attrib["width"]), pixels(root.attrib["height"])


def _math_svg(formula, inline=False, color=None):
    """Render math locally into a scalable SVG so it does not rely on a CDN."""
    return _cached_math_svg(formula, inline, color or document_colors()["foreground"])


@lru_cache(maxsize=512)
def _cached_math_svg(formula, inline, color):
    buffer = BytesIO()
    font_size = 12 if inline else 14
    normalized_formula = re.sub(r"\\ge(?![A-Za-z])", r"\\geq", formula)
    normalized_formula = re.sub(r"\\le(?![A-Za-z])", r"\\leq", normalized_formula)
    try:
        with rc_context({
            "savefig.transparent": True,
            "mathtext.fontset": "cm",
            # Computer Modern's normal math face uses italic variables and roman digits.
            "mathtext.default": "normal",
        }):
            math_to_image(
                f"${normalized_formula}$",
                buffer,
                prop=FontProperties(size=font_size, math_fontfamily="cm"),
                format="svg",
                dpi=200,
                color=color or document_colors()["foreground"],
            )
    except Exception:
        return f'<code class="math-source">{html.escape(formula)}</code>'

    svg_data = buffer.getvalue()
    width, height = svg_display_size(svg_data)
    root = ET.fromstring(svg_data)
    root.set("class", "math-inline" if inline else "math-display")
    root.set("width", f"{width:.3f}px")
    root.set("height", f"{height:.3f}px")
    root.set("aria-label", formula)
    return ET.tostring(root, encoding="unicode")


def render_markdown_file(path, *, cache_info=None):
    """Reuse a saved vector-HTML rendering until the source, theme or renderer changes."""
    path = Path(path)
    markdown_text = path.read_text(encoding="utf-8-sig")
    key = json.dumps([RENDERER_FINGERPRINT, document_colors(), markdown_text], ensure_ascii=False, sort_keys=True)
    signature = hashlib.sha256(key.encode("utf-8")).hexdigest()
    marker = f"<!-- markdown-render:{signature} -->\n"
    cache_path = path.with_suffix(".rendered.html")
    try:
        cached = cache_path.read_text(encoding="utf-8")
        if cached.startswith(marker):
            if cache_info is not None:
                cache_info["cache_hit"] = True
            return cached[len(marker):]
    except (OSError, UnicodeError):
        pass
    if cache_info is not None:
        cache_info["cache_hit"] = False
    rendered = render_markdown(markdown_text)
    try:
        cache_path.write_text(marker+rendered, encoding="utf-8")
    except OSError:
        # A read-only notes folder can still be displayed normally.
        pass
    return rendered


def _inline_markdown(text, math_color=None):
    """Convert the inline Markdown and dollar-delimited math used in notes."""
    rendered = []
    position = 0
    for match in INLINE_PATTERN.finditer(text):
        rendered.append(html.escape(text[position:match.start()]))
        token = match.group(0)
        if token.startswith("$"):
            rendered.append(_math_svg(token[1:-1], inline=True, color=math_color))
        elif token.startswith("`"):
            rendered.append(f"<code>{html.escape(token[1:-1])}</code>")
        else:
            rendered.append(f"<strong>{html.escape(token[2:-2])}</strong>")
        position = match.end()
    rendered.append(html.escape(text[position:]))
    return "".join(rendered)


def render_markdown(markdown_text):
    """Convert project Markdown to HTML with embedded SVG equations."""
    blocks = []
    paragraph = []
    math_lines = None
    mermaid_lines = None
    list_items = []
    colors = document_colors()

    def render_inline(text):
        return _inline_markdown(text, math_color=colors["foreground"])

    def flush_paragraph():
        if paragraph:
            blocks.append(f"<p>{render_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def flush_list():
        if list_items:
            items = "".join(f"<li>{render_inline(item)}</li>" for item in list_items)
            blocks.append(f"<ul>{items}</ul>")
            list_items.clear()

    def add_display_math(formula):
        blocks.append(
            '<div class="math-container">'
            + _math_svg(formula, inline=False, color=colors["foreground"])
            + "</div>"
        )

    for line in markdown_text.splitlines():
        stripped = line.strip()
        if mermaid_lines is not None:
            if stripped == "```":
                blocks.append(
                    '<div class="mermaid">'
                    + html.escape("\n".join(mermaid_lines))
                    + "</div>"
                )
                mermaid_lines = None
            else:
                mermaid_lines.append(line)
            continue

        if math_lines is not None:
            if stripped == "$$":
                add_display_math(" ".join(math_lines))
                math_lines = None
            else:
                math_lines.append(stripped)
        elif stripped.lower() == "```mermaid":
            flush_paragraph()
            flush_list()
            mermaid_lines = []
        elif stripped.startswith("$$") and stripped.endswith("$$") and len(stripped) > 4:
            flush_paragraph()
            flush_list()
            add_display_math(stripped[2:-2].strip())
        elif stripped == "$$":
            flush_paragraph()
            flush_list()
            math_lines = []
        elif not stripped:
            flush_paragraph()
            flush_list()
        elif stripped.startswith("#"):
            flush_paragraph()
            flush_list()
            heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if heading:
                level = len(heading.group(1))
                blocks.append(f"<h{level}>{render_inline(heading.group(2))}</h{level}>")
                # QTextBrowser does not draw CSS border-bottom on headings.
                blocks.append(
                    '<hr class="heading-rule" width="100%" '
                    f'style="color: {colors["border"]}; '
                    f'background-color: {colors["border"]};" />'
                )
            else:
                paragraph.append(stripped)
        elif stripped.startswith("- "):
            flush_paragraph()
            list_items.append(stripped[2:])
        else:
            flush_list()
            paragraph.append(stripped)

    flush_paragraph()
    flush_list()
    if math_lines is not None:
        add_display_math(" ".join(math_lines))
    if mermaid_lines is not None:
        blocks.append(
            '<div class="mermaid">'
            + html.escape("\n".join(mermaid_lines))
            + "</div>"
        )

    has_mermaid = any('class="mermaid"' in block for block in blocks)
    mermaid_scripts = ""
    if has_mermaid:
        mermaid_config = {
            "startOnLoad": False,
            "securityLevel": "strict",
            "theme": "base",
            "themeVariables": {
                "darkMode": True,
                "background": colors["background"],
                "primaryColor": colors["surface"],
                "primaryTextColor": colors["foreground"],
                "primaryBorderColor": colors["border"],
                "lineColor": "#ffffff",
                "defaultLinkColor": "#ffffff",
                "arrowheadColor": "#ffffff",
                "secondaryColor": colors["surface"],
                "tertiaryColor": colors["background"],
                "clusterBkg": "#555555",
                "clusterBorder": "#858585",
                "edgeLabelBackground": colors["background"],
                "textColor": colors["foreground"],
            },
        }
        mermaid_scripts = """<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
window.addEventListener('load', function () {
  if (window.mermaid) {
    mermaid.initialize(MERMAID_CONFIG);
    mermaid.run();
  }
});
</script>""".replace("MERMAID_CONFIG", json.dumps(mermaid_config))

    stylesheet = """<style>
html { background: BACKGROUND; color: FOREGROUND; color-scheme: dark; }
body { font-family: "Segoe UI", "Microsoft JhengHei", sans-serif; color: FOREGROUND;
       background: BACKGROUND; font-size: 16px; line-height: 1.7; padding: 12px 20px; }
h1, h2, h3, h4, h5, h6 { color: FOREGROUND; line-height: 1.3; margin: 1.25em 0 0.3em; }
h1 { font-size: 1.8em; }
h2 { font-size: 1.35em; }
.heading-rule { border: 0; height: 1px; background: BORDER; color: BORDER;
                margin-top: 0; margin-bottom: 0.8em; }
p { margin: 0.65em 0; }
ul { padding-left: 1.6em; }
a { color: ACCENT; }
code { font-family: Consolas, monospace; color: FOREGROUND; background: SURFACE;
       padding: 0.1em 0.3em; border-radius: 3px; }
.math-container { text-align: center; margin: 1.2em 0; overflow-x: auto; }
.math-display { display: inline-block; max-width: 100%; height: auto; }
.math-inline { vertical-align: middle; }
.math-source { color: ERROR; }
.mermaid { display: flex; justify-content: center; overflow-x: auto; }
.mermaid .node { cursor: pointer; }
.mermaid svg .cluster rect { fill: #555555 !important; stroke: #858585 !important; }
.mermaid svg .cluster-label text, .mermaid svg .cluster-label span,
.mermaid svg .cluster-label p { fill: #ffffff !important; color: #ffffff !important; }
.mermaid svg .flowchart-link, .mermaid svg .edgePath .path { stroke: #ffffff !important; }
.mermaid svg marker path, .mermaid svg .arrowheadPath {
    fill: #ffffff !important; stroke: #ffffff !important;
}
</style>"""
    for name, color in colors.items():
        stylesheet = stylesheet.replace(name.upper(), color)

    return """<!doctype html>
<html><head><meta charset="utf-8">
""" + mermaid_scripts + stylesheet + "</head><body>\n" + "\n".join(blocks) + "</body></html>"
