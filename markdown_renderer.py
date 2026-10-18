"""Render the project's Markdown notes with offline LaTeX math SVGs."""

import base64
import html
import re
from io import BytesIO

from matplotlib.mathtext import math_to_image


def _math_image(formula, inline=False):
    """Typeset a MathText formula as an embedded SVG data URL."""
    buffer = BytesIO()
    try:
        math_to_image(f"${formula}$", buffer, format="svg", dpi=160, color="#202938")
    except Exception:
        return f'<code class="math-source">{html.escape(formula)}</code>'

    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    css_class = "math-inline" if inline else "math-display"
    return f'<img class="{css_class}" src="data:image/svg+xml;base64,{encoded}" />'


def _inline_markdown(text):
    token_pattern = re.compile(r"(\$[^$\n]+\$|`[^`]+`|\*\*.+?\*\*)")
    rendered = []
    position = 0
    for match in token_pattern.finditer(text):
        rendered.append(html.escape(text[position:match.start()]))
        token = match.group(0)
        if token.startswith("$"):
            rendered.append(_math_image(token[1:-1], inline=True))
        elif token.startswith("`"):
            rendered.append(f"<code>{html.escape(token[1:-1])}</code>")
        else:
            rendered.append(f"<strong>{html.escape(token[2:-2])}</strong>")
        position = match.end()
    rendered.append(html.escape(text[position:]))
    return "".join(rendered)


def render_markdown(markdown_text):
    """Convert the heading, paragraph, list, and math Markdown used by notes to HTML."""
    blocks = []
    paragraph = []
    math_lines = None
    list_items = []

    def flush_paragraph():
        if paragraph:
            blocks.append(f"<p>{_inline_markdown(' '.join(paragraph))}</p>")
            paragraph.clear()

    def flush_list():
        if list_items:
            items = "".join(f"<li>{_inline_markdown(item)}</li>" for item in list_items)
            blocks.append(f"<ul>{items}</ul>")
            list_items.clear()

    for line in markdown_text.splitlines():
        stripped = line.strip()
        if math_lines is not None:
            if stripped == "$$":
                blocks.append(f'<div class="math-container">{_math_image(" ".join(math_lines))}</div>')
                math_lines = None
            else:
                math_lines.append(stripped)
            continue

        if stripped == "$$":
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
                blocks.append(f"<h{level}>{_inline_markdown(heading.group(2))}</h{level}>")
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
        blocks.append(f'<div class="math-container">{_math_image(" ".join(math_lines))}</div>')

    return """<!doctype html>
<html><head><meta charset="utf-8"><style>
body { font-family: "Segoe UI", "Microsoft JhengHei", sans-serif; color: #202938;
       background: #ffffff; line-height: 1.7; padding: 12px 20px; }
h1, h2, h3, h4 { color: #183b56; line-height: 1.3; margin: 1.25em 0 0.5em; }
h1 { font-size: 1.8em; border-bottom: 2px solid #dce5eb; padding-bottom: 0.35em; }
h2 { font-size: 1.35em; border-bottom: 1px solid #e8edf1; padding-bottom: 0.25em; }
p { margin: 0.65em 0; }
ul { padding-left: 1.6em; }
code { font-family: Consolas, monospace; background: #f1f4f7; padding: 0.1em 0.3em;
       border-radius: 3px; }
.math-container { text-align: center; margin: 1em 0; overflow-x: auto; }
.math-display { max-width: 100%; height: auto; }
.math-inline { vertical-align: middle; height: 1.5em; }
.math-source { color: #9b2c2c; }
</style></head><body>
""" + "\n".join(blocks) + "</body></html>"
