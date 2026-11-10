"use strict";

window.MathJax = {
  startup: {typeset: false},
  options: {enableAssistiveMml: false},
  tex: {displayMath: [["$$", "$$"]]},
  svg: {fontCache: "local"},
};

const byId = (id) => document.getElementById(id);
const report = byId("report");

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function escapeHtml(text) {
  return text.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

// The report emits a topologically ordered Mermaid flow with one decision branch.
function renderFlow(source) {
  const lines = source.trim().split("\n");
  if (lines.shift() !== "graph TD") return null;

  const nodes = new Map();
  const pattern = /^\s*([A-Z]+)(?:[\[{]"([^"]+)"[\]}])? -->\s*(?:\|"([^"]+)"\| )?([A-Z]+)(?:[\[{]"([^"]+)"[\]}])?$/;
  for (const line of lines) {
    const match = line.match(pattern);
    if (!match) return null;
    const [, from, fromLabel, branch, to, toLabel] = match;
    if (!nodes.has(from)) nodes.set(from, {label: fromLabel, level: 0});
    const target = nodes.get(to) ?? {label: toLabel, branch, level: 0};
    if (toLabel) target.label = toLabel;
    target.level = Math.max(target.level, nodes.get(from).level + 1);
    nodes.set(to, target);
  }
  const levels = [];
  for (const node of nodes.values()) {
    if (!node.label) return null;
    const branch = node.branch ? "<b>" + escapeHtml(node.branch) + "</b>" : "";
    (levels[node.level] ??= []).push('<span class="flow-node">' + branch + escapeHtml(node.label) + "</span>");
  }
  const rows = levels.map((level) => '<div class="flow-level">' + level.join("") + "</div>");
  const label = report.lang === "en" ? "Expand calculation workflow" : "展開計算流程";
  return '<details class="flow"><summary>' + label + '</summary>' + rows.join("") + "</details>";
}

marked.use({
  extensions: [{
    name: "equation",
    level: "block",
    tokenizer(source) {
      const match = /^\$\$\n([\s\S]*?)\n\$\$(?:\n|$)/.exec(source);
      if (match) return {type: "equation", raw: match[0], math: match[1]};
    },
    renderer({math}) {
      return '<div class="equation">$$\n' + escapeHtml(math) + '\n$$</div>\n';
    },
  }],
  renderer: {
    code({text, lang}) {
      return lang === "mermaid" ? (renderFlow(text) ?? false) : false;
    },
  },
});

async function renderResult(result) {
  const overview = byId("summary");
  const math = window.MathJax;
  await math.startup.promise;
  math.typesetClear([report]);
  report.lang = overview.lang = result.language === "en" ? "en" : "zh-Hant";

  // The Markdown comes only from the local solver's report generator.
  report.innerHTML = marked.parse(result.markdown);
  for (const table of report.querySelectorAll("table")) {
    const wrapper = element("div", "", "table-scroll");
    table.before(wrapper);
    wrapper.append(table);
  }
  const headings = Array.from(report.querySelectorAll("h2"));
  headings.forEach((heading, index) => { heading.id = "chapter-" + index; });

  const metrics = result.summary.map(({label, value, unit}) => {
    const card = element("div", "", "metric");
    const number = element("dd", value);
    number.append(element("span", unit));
    card.append(element("dt", label), number);
    return card;
  });
  overview.replaceChildren(...metrics);
  overview.hidden = false;
  byId("placeholder").hidden = true;
  await math.typesetPromise([report]);
  const formulas = report.querySelectorAll(".equation");
  return {
    chapters: headings.map((heading) => heading.textContent),
    ok: !report.querySelector("[data-mjx-error]") &&
      [...formulas].every((formula) => formula.querySelector("mjx-container > svg")),
  };
}

function clearResult() {
  window.MathJax.typesetClear?.([report]);
  report.replaceChildren();
  byId("summary").replaceChildren();
  byId("summary").hidden = true;
  byId("placeholder").hidden = false;
}

const desktop = window.chrome?.webview;
desktop?.addEventListener("message", async ({data}) => {
  if (data.event === "chapter") {
    byId("chapter-" + data.index)?.scrollIntoView({block: "start"});
  } else if (data.event === "clear") {
    clearResult();
    window.scrollTo(0, 0);
  } else if (data.event === "render") {
    try {
      window.scrollTo(0, 0);
      const {chapters, ok} = await renderResult(data.report);
      desktop.postMessage({event: "rendered", chapters, ok});
    } catch (error) {
      console.error(error);
      desktop.postMessage({event: "rendered", chapters: [], ok: false});
    }
  }
});
desktop?.postMessage({event: "ready"});
