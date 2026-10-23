"""Flow graph generation and an SVG viewport shared by all diagram pages."""

import json

from .markdown_renderer import render_markdown


def flow_edges(flow):
    """Resolve implicit chains before filtering a diagram to a single group."""
    edges = []
    for lane in ("main", "secondary", "tertiary"):
        previous = None
        for row in (row for row in flow if row["flow_row"] == lane):
            source = row["branch_from"] or previous
            detached = str(row.get("flow_detached", "")).strip().lower() in {"1", "true", "yes"}
            if source and not detached:
                edges.append((source, row["node_id"]))
            previous = row["node_id"]
    for row in flow:
        if row["flow_row"] in {"branch", "merge"}:
            sources = [row["branch_from"]]
            if row["flow_row"] == "merge":
                sources.extend((row.get("merge_from") or "").split("|"))
            edges.extend((source.strip(), row["node_id"]) for source in sources if source.strip())
        edges.extend((source.strip(), row["node_id"])
                     for source in (row.get("extra_from") or "").split("|") if source.strip())
    return list(dict.fromkeys(edges))


def render_flow_diagram(flow, group=None):
    """Keep group pages as induced subgraphs of the complete flow."""
    edges = flow_edges(flow)
    visible = [row for row in flow if group is None or row.get("flow_group", "") == group]
    graph_ids = {row["node_id"]: f"flow_node_{index}" for index, row in enumerate(flow)}
    visible_ids = {row["node_id"] for row in visible}
    incoming = {target for _, target in edges}
    outgoing = {source for source, _ in edges}
    source_ids = {node_id for node_id in visible_ids if node_id in outgoing and node_id not in incoming}
    lines = ["graph TD"]
    for source, target in edges:
        if source in visible_ids and target in visible_ids:
            lines.append(f"    {graph_ids[source]} --> {graph_ids[target]}")

    groups = {}
    for row in visible:
        groups.setdefault(row.get("flow_group", ""), []).append(row)
    for index, (title, rows) in enumerate(groups.items()):
        if title:
            escaped_title = title.replace('"', "&quot;")
            lines.append(f'    subgraph flow_group_{index}["{escaped_title}"]')
        for row in rows:
            escaped_title = row["title"].replace('"', "&quot;")
            lines.append(f'    {graph_ids[row["node_id"]]}["{escaped_title}"]')
        if title:
            lines.append("    end")
            if title == "轉向分析":
                lines.append(f"    style flow_group_{index} fill:#f2f2f2,stroke:#444444,stroke-width:3px,color:#222222")
    lines.append("    classDef flowNode fill:#f1f1f1,stroke:#b8b8b8,color:#222222")
    lines.append("    classDef flowSource fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f")
    if visible:
        lines.append("    class " + ",".join(graph_ids[row["node_id"]] for row in visible) + " flowNode")
    if source_ids:
        lines.append("    class " + ",".join(graph_ids[node_id] for node_id in source_ids) + " flowSource")
    rendered = render_markdown("```mermaid\n" + "\n".join(lines) + "\n```")
    click_map = {row["title"]: row["node_id"] for row in visible}
    script = VIEWPORT_SCRIPT.replace("TITLE_TO_ID", json.dumps(click_map, ensure_ascii=True).replace("</", "<\\/"))
    rendered = rendered.replace("</head>", VIEWPORT_STYLE + "</head>")
    rendered = rendered.replace("<body>", '<body>' + VIEWPORT_TOOLBAR + '<div id="flow-viewport"><div id="flow-canvas">')
    return rendered.replace("</body>", "</div></div>" + script + "</body>")


VIEWPORT_STYLE = """<style>
html, body { height: 100%; margin: 0; padding: 0; overflow: hidden; }
#flow-toolbar { height: 40px; box-sizing: border-box; display: flex; align-items: center;
  gap: 8px; padding: 4px 10px; border-bottom: 1px solid #555; white-space: nowrap; }
#flow-toolbar button { background: #363636; color: #eee; border: 1px solid #777;
  border-radius: 4px; padding: 2px 10px; font: inherit; cursor: pointer; }
#flow-toolbar button:hover { background: #505050; }
#flow-zoom { min-width: 48px; text-align: center; font-variant-numeric: tabular-nums; }
#flow-hint { font-size: 12px; overflow: hidden; text-overflow: ellipsis; }
#flow-source-legend { display: inline-flex; align-items: center; gap: 5px; white-space: nowrap;
  font-size: 12px; }
#flow-source-legend > span { width: 13px; height: 13px; box-sizing: border-box;
  background: #fef3c7; border: 2px solid #d97706; border-radius: 3px; }
#flow-viewport { position: absolute; inset: 40px 0 0; overflow: auto;
  overscroll-behavior: contain; touch-action: none; cursor: grab; }
#flow-viewport.dragging, #flow-viewport.dragging .node { cursor: grabbing; user-select: none; }
#flow-canvas { position: relative; min-width: 100%; min-height: 100%; }
#flow-canvas .mermaid { display: block; overflow: visible; margin: 0; padding: 0; }
#flow-canvas svg { position: absolute; max-width: none !important; }
#flow-canvas .node > rect, #flow-canvas .cluster > rect {
  rx: 6px !important; ry: 6px !important;
}
#flow-canvas .node:hover > rect, #flow-canvas .node:hover .label-container {
  fill: #dbeafe !important; stroke: #60a5fa !important;
}
#flow-canvas .node.flow-selected > rect, #flow-canvas .node.flow-selected .label-container {
  fill: #bfdbfe !important; stroke: #2563eb !important; stroke-width: 3px !important;
}
#flow-canvas .node.flow-pressed > rect, #flow-canvas .node.flow-pressed .label-container {
  fill: #93c5fd !important; stroke: #1d4ed8 !important; stroke-width: 3px !important;
}
#flow-canvas .node.flow-selected .label, #flow-canvas .node.flow-selected .label *,
#flow-canvas .node.flow-selected text, #flow-canvas .node.flow-pressed .label,
#flow-canvas .node.flow-pressed .label *, #flow-canvas .node.flow-pressed text {
  color: #0f172a !important; fill: #0f172a !important;
}
</style>"""

VIEWPORT_TOOLBAR = """<div id="flow-toolbar" role="toolbar" aria-label="流程圖縮放">
<button id="flow-zoom-out" title="縮小" aria-label="縮小">−</button>
<span id="flow-zoom" aria-live="polite">100%</span>
<button id="flow-zoom-in" title="放大" aria-label="放大">＋</button>
<button id="flow-fit">符合視窗</button><button id="flow-reset">100%</button>
<span id="flow-source-legend"><span></span>流程起點</span>
<span id="flow-hint">滾輪縮放｜拖曳平移｜Shift＋滾輪水平捲動</span>
</div>"""

VIEWPORT_SCRIPT = r"""<script>
(() => {
  const titleToId = TITLE_TO_ID;
  const viewport = document.getElementById('flow-viewport');
  const canvas = document.getElementById('flow-canvas');
  const zoomLabel = document.getElementById('flow-zoom');
  const padding = 32;
  let svg = null, width = 0, height = 0, scale = 1, offsetX = padding, offsetY = padding;
  let clickTimer = null, drag = null, suppressClickUntil = 0;
  let selectedNodeId = null, pressedNode = null;

  function nodeId(group) {
    const title = (group.textContent || '').replace(/\s+/g, ' ').trim();
    return titleToId[title] || null;
  }
  function selectNode(id) {
    selectedNodeId = id;
    canvas.querySelectorAll('g.node').forEach(group => {
      group.classList.toggle('flow-selected', id != null && nodeId(group) === id);
    });
  }
  function clearPressedNode() {
    if (pressedNode) pressedNode.classList.remove('flow-pressed');
    pressedNode = null;
  }
  window.flowSelection = {select: selectNode};

  function layout() {
    const canvasWidth = Math.max(viewport.clientWidth, width * scale + 2 * padding);
    const canvasHeight = Math.max(viewport.clientHeight, height * scale + 2 * padding);
    canvas.style.width = canvasWidth + 'px';
    canvas.style.height = canvasHeight + 'px';
    offsetX = Math.max(padding, (canvasWidth - width * scale) / 2);
    offsetY = Math.max(padding, (canvasHeight - height * scale) / 2);
    svg.style.left = offsetX + 'px';
    svg.style.top = offsetY + 'px';
    svg.style.width = width * scale + 'px';
    svg.style.height = height * scale + 'px';
    zoomLabel.textContent = Math.round(scale * 100) + '%';
  }
  function zoomTo(next, x = viewport.clientWidth / 2, y = viewport.clientHeight / 2) {
    if (!svg) return;
    const graphX = (viewport.scrollLeft + x - offsetX) / scale;
    const graphY = (viewport.scrollTop + y - offsetY) / scale;
    scale = Math.min(1, Math.max(0.1, next));
    layout();
    viewport.scrollLeft = graphX * scale + offsetX - x;
    viewport.scrollTop = graphY * scale + offsetY - y;
  }
  function fit() {
    if (!svg) return;
    zoomTo(Math.min((viewport.clientWidth - 2 * padding) / width,
                    (viewport.clientHeight - 2 * padding) / height, 1));
    viewport.scrollLeft = 0;
    viewport.scrollTop = 0;
  }
  function initialize() {
    const candidate = canvas.querySelector('.mermaid svg');
    if (!candidate || !candidate.viewBox.baseVal.width) return;
    svg = candidate;
    width = svg.viewBox.baseVal.width;
    height = svg.viewBox.baseVal.height;
    observer.disconnect();
    scale = 1;
    layout();
    viewport.scrollLeft = viewport.scrollTop = 0;
    selectNode(selectedNodeId);
  }
  const observer = new MutationObserver(initialize);
  observer.observe(canvas, {childList: true, subtree: true});
  initialize();
  new ResizeObserver(() => { if (svg) zoomTo(scale); }).observe(viewport);
  window.flowViewport = {zoomTo, fit, get scale() { return scale; }};
  document.getElementById('flow-zoom-in').onclick = () => zoomTo(scale * 1.2);
  document.getElementById('flow-zoom-out').onclick = () => zoomTo(scale / 1.2);
  document.getElementById('flow-reset').onclick = () => zoomTo(1);
  document.getElementById('flow-fit').onclick = fit;
  viewport.addEventListener('wheel', event => {
    event.preventDefault();
    const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? viewport.clientHeight : 1;
    if (event.shiftKey || (!event.ctrlKey && Math.abs(event.deltaX) > Math.abs(event.deltaY))) {
      viewport.scrollLeft += (event.deltaX || event.deltaY) * unit;
      return;
    }
    const bounds = viewport.getBoundingClientRect();
    zoomTo(scale * Math.exp(-event.deltaY * unit * 0.0015),
           event.clientX - bounds.left, event.clientY - bounds.top);
  }, {passive: false});
  viewport.addEventListener('pointerdown', event => {
    if (!svg || ![0, 1].includes(event.button)) return;
    // Let native scrollbar thumbs handle their own pointer events.
    const bounds = viewport.getBoundingClientRect();
    if (event.clientX - bounds.left >= viewport.clientWidth ||
        event.clientY - bounds.top >= viewport.clientHeight) return;
    clearPressedNode();
    const group = event.target.closest('g.node');
    if (event.button === 0 && group && nodeId(group)) {
      pressedNode = group;
      pressedNode.classList.add('flow-pressed');
    }
    drag = {id: event.pointerId, x: event.clientX, y: event.clientY,
            left: viewport.scrollLeft, top: viewport.scrollTop, moved: false};
    if (event.button === 1) event.preventDefault();
  });
  viewport.addEventListener('pointermove', event => {
    if (!drag || drag.id !== event.pointerId) return;
    const dx = event.clientX - drag.x, dy = event.clientY - drag.y;
    if (!drag.moved && Math.hypot(dx, dy) <= 4) return;
    if (!drag.moved) {
      drag.moved = true;
      clearTimeout(clickTimer);
      clearPressedNode();
      viewport.setPointerCapture(event.pointerId);
      viewport.classList.add('dragging');
    }
    viewport.scrollLeft = drag.left - dx;
    viewport.scrollTop = drag.top - dy;
  });
  function endDrag(event) {
    if (!drag || drag.id !== event.pointerId) return;
    clearPressedNode();
    if (drag.moved) suppressClickUntil = performance.now() + 350;
    if (viewport.hasPointerCapture(event.pointerId)) viewport.releasePointerCapture(event.pointerId);
    viewport.classList.remove('dragging');
    drag = null;
  }
  window.addEventListener('pointerup', endDrag);
  window.addEventListener('pointercancel', endDrag);
  window.addEventListener('blur', clearPressedNode);
  function findNode(event) {
    const group = event.target.closest('g.node');
    if (!group || performance.now() < suppressClickUntil) return null;
    return nodeId(group);
  }
  function request(nodeId, kind, clickedAt) {
    window.location.href = 'flow-node://' + kind + '/' + encodeURIComponent(nodeId)
      + '?clicked_at=' + clickedAt;
  }
  document.addEventListener('click', event => {
    const nodeId = findNode(event);
    if (!nodeId) return;
    selectNode(nodeId);
    clearTimeout(clickTimer);
    const clickedAt = performance.timeOrigin + event.timeStamp;
    clickTimer = setTimeout(() => request(nodeId, 'single', clickedAt), 260);
  });
  document.addEventListener('dblclick', event => {
    const nodeId = findNode(event);
    if (!nodeId) return;
    selectNode(nodeId);
    clearTimeout(clickTimer);
    request(nodeId, 'double', performance.timeOrigin + event.timeStamp);
  });
})();
</script>"""
