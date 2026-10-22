"""Group pages preserve graph topology; zoom and clicks work in Qt's real web engine."""

import csv
from html import escape, unescape
import json
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# Chromium's own subprocess sandbox is unavailable on some headless test hosts.
# These settings apply only to this test process, never to the desktop app.
os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")

from PySide6.QtCore import QEventLoop, QPoint, Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

from flow_diagram import flow_edges, render_flow_diagram
from main import FlowDiagramPage, MainWindow


ROOT = Path(__file__).resolve().parents[1]


def fixture_source(flow, group=None):
    """Use simple SVG nodes so interaction tests exercise Qt without a CDN."""
    source = render_flow_diagram(flow, group)
    source = re.sub(r'<script src="https://[^\"]+"></script>', "", source)
    nodes = []
    for index, row in enumerate(row for row in flow if group is None or row.get("flow_group", "") == group):
        x = 100 + index * 300
        nodes.append(f'<g class="node"><rect x="{x}" y="100" width="200" height="100" '
                     'style="fill:#f1f1f1;stroke:#b8b8b8"/>'
                     f'<text x="{x+20}" y="150">{escape(row["title"])}</text></g>')
    svg = '<div class="mermaid"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1800 2400">' + "".join(nodes) + '</svg></div>'
    return re.sub(r'<div class="mermaid">.*?</div>', lambda _: svg, source, flags=re.S)


class FlowDiagramTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "data/analysis_flow.csv").open(encoding="utf-8-sig", newline="") as stream:
            cls.flow = list(csv.DictReader(stream))

    def test_each_group_is_an_induced_subgraph_without_external_or_new_edges(self):
        edges = set(flow_edges(self.flow))
        names = {f"flow_node_{i}": row["node_id"] for i, row in enumerate(self.flow)}
        for group in dict.fromkeys(row["flow_group"] for row in self.flow):
            with self.subTest(group=group):
                source = render_flow_diagram(self.flow, group)
                diagram = unescape(re.search(r'<div class="mermaid">(.*?)</div>', source, re.S).group(1))
                visible = {row["node_id"] for row in self.flow if row["flow_group"] == group}
                actual_edges = {(names[a], names[b]) for a, b in re.findall(r"(flow_node_\d+) --> (flow_node_\d+)", diagram)}
                self.assertEqual(actual_edges, {(a, b) for a, b in edges if a in visible and b in visible})
                declared = {names[name] for name in re.findall(r'(flow_node_\d+)\["', diagram)}
                self.assertEqual(declared, visible)


class FlowViewportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def wait_for(self, predicate):
        for _ in range(100):
            if predicate():
                return
            QTest.qWait(30)
        self.assertTrue(predicate(), "Timed out waiting for web engine")

    def js(self, source, page=None):
        values = []
        loop = QEventLoop()
        (page or self.page).runJavaScript("JSON.stringify(eval(" + json.dumps(source) + "))",
                                         lambda result: (values.append(result), loop.quit()))
        QTimer.singleShot(3000, loop.quit)
        loop.exec()
        self.assertTrue(values, "JavaScript did not return")
        return json.loads(values[0]) if values[0] else None

    def setUp(self):
        self.view = QWebEngineView()
        self.page = FlowDiagramPage(self.view)
        self.view.setPage(self.page)
        self.view.resize(900, 500)
        self.view.show()
        self.requests = []
        self.page.flowNodeRequested.connect(lambda node, double: self.requests.append((node, double)))
        source = fixture_source([dict(node_id=node, title=title, flow_row="main", branch_from="", flow_group="")
                                 for node, title in (("chosen", "Chosen"), ("other", "Other"))])
        ready = []
        self.view.loadFinished.connect(ready.append)
        self.view.setHtml(source)
        self.wait_for(lambda: ready)
        self.assertTrue(ready[-1])
        self.assertTrue(self.js("!!window.flowViewport"))

    def tearDown(self):
        self.view.close()
        self.view.deleteLater()
        self.app.processEvents()

    def test_zoom_has_both_scroll_axes_and_wheel_preserves_cursor_anchor(self):
        result = self.js("""(() => {
          const v = document.getElementById('flow-viewport');
          const svg = document.querySelector('svg');
          flowViewport.zoomTo(1);
          v.scrollLeft = 200; v.scrollTop = 300;
          const x = 350, y = 220, before = svg.getBoundingClientRect();
          const gx = (x - before.left) / flowViewport.scale;
          const gy = (y - before.top) / flowViewport.scale;
          v.dispatchEvent(new WheelEvent('wheel', {deltaY: -120, clientX: x, clientY: y, cancelable: true}));
          const after = svg.getBoundingClientRect();
          return {scale: flowViewport.scale, horizontal: v.scrollWidth > v.clientWidth,
            vertical: v.scrollHeight > v.clientHeight,
            dx: Math.abs((x - after.left) / flowViewport.scale - gx),
            dy: Math.abs((y - after.top) / flowViewport.scale - gy)};
        })()""")
        self.assertGreater(result["scale"], 1)
        self.assertTrue(result["horizontal"])
        self.assertTrue(result["vertical"])
        self.assertLess(result["dx"], 2)
        self.assertLess(result["dy"], 2)
        self.assertTrue(self.js("""(() => {
          const v = document.getElementById('flow-viewport');
          const before = v.scrollLeft;
          v.dispatchEvent(new WheelEvent('wheel', {deltaY: 120, shiftKey: true, cancelable: true}));
          return v.scrollLeft > before;
        })()"""))

    def test_fit_reset_limits_and_node_clicks(self):
        self.assertTrue(self.js("""(() => {
          document.getElementById('flow-fit').click();
          const v = document.getElementById('flow-viewport'), svg = document.querySelector('svg').getBoundingClientRect();
          return svg.width <= v.clientWidth && svg.height <= v.clientHeight;
        })()"""))
        self.assertEqual(self.js("document.getElementById('flow-reset').click(); flowViewport.scale"), 1)
        self.assertEqual(self.js("flowViewport.zoomTo(100); flowViewport.scale"), 4)
        self.assertEqual(self.js("flowViewport.zoomTo(0); flowViewport.scale"), 0.01)
        self.js("flowViewport.zoomTo(1); document.getElementById('flow-viewport').scrollLeft = 0; document.getElementById('flow-viewport').scrollTop = 0;")
        # Selection styling must override Mermaid's inline fill and stroke.
        self.js("flowSelection.select('other')")
        self.assertEqual(self.js("document.querySelector('.flow-selected').textContent"), "Other")
        QTest.mousePress(self.view.focusProxy(), Qt.MouseButton.LeftButton, pos=QPoint(200, 200))
        self.wait_for(lambda: self.js("!!document.querySelector('.flow-pressed')"))
        self.assertEqual(self.js("getComputedStyle(document.querySelector('.flow-pressed rect')).fill"), "rgb(147, 197, 253)")
        QTest.mouseRelease(self.view.focusProxy(), Qt.MouseButton.LeftButton, pos=QPoint(200, 200))
        self.wait_for(lambda: self.requests)
        self.assertEqual(self.requests, [("chosen", False)])
        self.assertEqual(self.js("document.querySelectorAll('.flow-selected').length"), 1)
        self.assertEqual(self.js("document.querySelector('.flow-selected').textContent"), "Chosen")
        self.assertEqual(self.js("getComputedStyle(document.querySelector('.flow-selected rect')).fill"), "rgb(191, 219, 254)")
        self.assertFalse(self.js("!!document.querySelector('.flow-pressed')"))
        self.requests.clear()
        # Queue the second click after Chromium receives the native first click.
        # A runJavaScript call immediately after QTest.mouseClick can overtake it.
        self.js("""document.querySelector('g.node').addEventListener('click', event => {
          const node = event.currentTarget;
          setTimeout(() => node.dispatchEvent(new MouseEvent('dblclick', {bubbles: true})), 0);
        }, {once: true});""")
        QTest.mouseClick(self.view.focusProxy(), Qt.MouseButton.LeftButton, pos=QPoint(200, 200))
        self.wait_for(lambda: self.requests)
        QTest.qWait(300)
        self.assertEqual(self.requests, [("chosen", True)])
        self.assertEqual(self.js("document.querySelector('.flow-selected').textContent"), "Chosen")

    def test_drag_pans_without_requesting_a_node(self):
        self.js("flowViewport.zoomTo(1); const v = document.getElementById('flow-viewport'); v.scrollLeft = 0; v.scrollTop = 0;")
        target = self.view.focusProxy()
        QTest.mousePress(target, Qt.MouseButton.LeftButton, pos=QPoint(200, 200))
        self.wait_for(lambda: self.js("!!document.querySelector('.flow-pressed')"))
        QTest.mouseMove(target, QPoint(100, 100), delay=30)
        self.wait_for(lambda: self.js("document.getElementById('flow-viewport').scrollLeft > 50"))
        QTest.mouseRelease(target, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
        result = self.js("({left: document.getElementById('flow-viewport').scrollLeft, top: document.getElementById('flow-viewport').scrollTop})")
        self.assertGreater(result["left"], 50)
        self.assertGreater(result["top"], 50)
        QTest.qWait(300)
        self.assertEqual(self.requests, [])
        self.assertFalse(self.js("!!document.querySelector('.flow-selected, .flow-pressed')"))

    def test_dropdown_defaults_to_full_flow_and_pages_share_node_selection(self):
        def build_fixture(window, flow=None, view=None, group=None):
            view.setHtml(fixture_source(window.flow, group))

        with TemporaryDirectory(dir=ROOT) as temporary, patch.object(MainWindow, "select_csv"), \
                patch.object(MainWindow, "build_flow_buttons", build_fixture), patch("main.LAST_SET_CSV", Path(temporary) / "last.csv"):
            window = MainWindow()

            def highlighted(page):
                return self.js("document.querySelector('.flow-selected')?.textContent", page)

            try:
                self.assertEqual(window.flow_selector.currentText(), "完整流程")
                self.assertEqual(window.flow_stack.currentIndex(), 0)
                options = [window.flow_selector.itemText(index) for index in range(window.flow_selector.count())]
                self.assertNotIn("未分組分析", options)
                self.assertNotIn("", window.flow_groups)
                self.assertEqual(set(options[1:]), {row["flow_group"] for row in window.flow if row.get("flow_group")})
                self.assertEqual(len(window.flow_views), 1)
                self.wait_for(lambda: highlighted(window.flow_pages[0]) == "元件重心、質量與慣量")
                group = window.flow_groups.index("煞車分析")
                window.flow_selector.setCurrentIndex(group)
                self.assertEqual(window.flow_stack.currentIndex(), group)
                view = window.flow_views[group]
                self.assertEqual(len(window.flow_views), 2)
                window.flow_pages[group].flowNodeRequested.emit("pedal_ratio", False)
                self.assertEqual(window.active_node_id, "pedal_ratio")
                self.assertTrue(window.run_selected_button.isEnabled())
                self.assertTrue(window.run_with_dependencies_button.isEnabled())
                self.wait_for(lambda: highlighted(window.flow_pages[group]) == "Pedal_ratio")
                self.wait_for(lambda: highlighted(window.flow_pages[0]) == "Pedal_ratio")
                with patch.object(window, "show_result") as show_result:
                    window.flow_pages[group].flowNodeRequested.emit("brake_force", True)
                    self.assertEqual(window.active_node_id, "brake_force")
                    show_result.assert_called_once_with("brake_force")
                self.wait_for(lambda: highlighted(window.flow_pages[0]) == "Brake_force")
                self.wait_for(lambda: highlighted(window.flow_pages[group]) == "Brake_force")
                window.flow_selector.setCurrentIndex(0)
                self.assertEqual(window.flow_stack.currentIndex(), 0)
                window.flow_selector.setCurrentIndex(group)
                self.assertIs(window.flow_views[group], view)
            finally:
                window.close()
                window.deleteLater()
                self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
