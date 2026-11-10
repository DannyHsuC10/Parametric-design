"use strict";

const form = byId("parameters");
const controls = byId("controls");
const chapterSelect = byId("chapters");
const reportLanguage = byId("report-language");
const parameterFields = byId("parameter-fields");
const reportContent = byId("report-content");
const fileInput = byId("project-file");
const groupButtons = [];
const groupPanels = [];
const inputs = new Map();
const downloads = [
  ["download-markdown", "vehicle_initial_sizing_report.md", "text/markdown",
    (result) => result.reports[reportLanguage.value].markdown],
  ["download-csv", "vehicle_initial_sizing_results.csv", "text/csv", (result) => "\uFEFF" + result.csv],
  ["download-excel", "vehicle_initial_sizing_results.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    (result) => Uint8Array.from(atob(result.excel), (character) => character.charCodeAt(0))],
  ["download-dynamics", "Vehicle_initial_settings.json", "application/json", (result) => result.dynamics],
];

let worker;
let defaults;
let projectFile;
let lastResult;
let staleResult = false;
let busy = false;
let dirty = false;
const staleMessage = "參數已變更。右側顯示上次結果，請重新求解後再匯出。";

function request(action, payload = null) {
  worker ??= new Worker("web/solver-worker.js", {type: "module"});
  return new Promise((resolve, reject) => {
    worker.onmessage = ({data}) => {
      if (data.error) reject(Object.assign(new Error(data.error), {field: data.field}));
      else resolve(data.result);
    };
    worker.onerror = (error) => {
      console.error(error);
      worker.terminate();
      worker = null;
      reject(new Error("無法啟動計算引擎。請重新整理頁面後再試。"));
    };
    worker.postMessage({action, payload});
  });
}

function setStatus(message, isError = false) {
  byId("status").textContent = message;
  byId("status").classList.toggle("status-error", isError);
}

function updateControls() {
  controls.disabled = busy || !defaults;
  chapterSelect.disabled = busy || chapterSelect.options.length < 2;
  reportLanguage.disabled = busy;
  for (const [id] of downloads) byId(id).disabled = busy || !lastResult || staleResult;
}

async function runTask(message, task) {
  if (busy) return;
  busy = true;
  updateControls();
  setStatus(message);
  let failedField;
  try {
    await task();
  } catch (error) {
    setStatus(error.message, true);
    failedField = inputs.get(error.field);
  } finally {
    busy = false;
    updateControls();
  }
  if (failedField) {
    selectGroup(failedField.group);
    failedField.input.setAttribute("aria-invalid", "true");
    failedField.input.focus();
  }
}

function selectGroup(selected) {
  groupButtons.forEach((button, index) => {
    button.setAttribute("aria-pressed", index === selected);
    groupPanels[index].hidden = index !== selected;
  });
  parameterFields.scrollTop = 0;
}

function buildForm(schema) {
  for (const [index, group] of schema.entries()) {
    const panel = element("section", "", "parameter-group");
    panel.id = "parameter-group-" + index;
    const button = element("button", group.tab);
    button.type = "button";
    button.setAttribute("aria-controls", panel.id);
    button.addEventListener("click", () => selectGroup(index));
    groupButtons.push(button);
    groupPanels.push(panel);
    byId("parameter-groups").append(button);
    parameterFields.append(panel);
    panel.append(element("h3", group.title));

    for (const field of group.fields) {
      const row = element("div", "", "parameter-field");
      const label = element("label", field.label);
      const input = element("input");
      input.id = "field-" + field.name;
      input.type = field.kind;
      if (input.type === "number") input.step = "any";
      label.htmlFor = input.id;
      if (field.unit) label.append(element("span", field.unit, "field-unit"));
      if (field.hint) {
        const hint = element("small", field.hint, "field-hint");
        hint.id = input.id + "-hint";
        input.setAttribute("aria-describedby", hint.id);
        label.append(hint);
      }
      row.append(label, input);
      panel.append(row);
      inputs.set(field.name, {input, group: index});
    }
  }
  selectGroup(0);
}

function parameters() {
  const values = {};
  for (const [name, {input}] of inputs) {
    if (input.type === "checkbox") values[name] = input.checked;
    else if (input.validity.badInput) values[name] = input.value;
    else values[name] = input.value === "" ? null : input.valueAsNumber;
  }
  return values;
}

function setProject(values, filename) {
  for (const [name, {input}] of inputs) {
    if (input.type === "checkbox") input.checked = values[name];
    else input.value = values[name] ?? "";
    input.removeAttribute("aria-invalid");
  }
  projectFile = filename;
  byId("project-name").textContent = filename ?? "預設參數";
  dirty = false;
  lastResult = null;
  staleResult = false;
  chapterSelect.length = 1;
  clearResult();
  updateControls();
}

function download(name, type, content) {
  const mimeType = typeof content === "string" ? type + ";charset=utf-8" : type;
  const url = URL.createObjectURL(new Blob([content], {type: mimeType}));
  const link = element("a");
  link.href = url;
  link.download = name;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

form.addEventListener("input", (event) => {
  if (event.target === fileInput) return;
  event.target.removeAttribute("aria-invalid");
  dirty = true;
  staleResult = Boolean(lastResult);
  setStatus(staleResult ? staleMessage : "參數已變更，可以重新求解或下載專案。");
  updateControls();
});

byId("open-project").addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => {
  const [file] = fileInput.files;
  fileInput.value = "";
  if (!file) return;
  runTask("正在讀取專案…", async () => {
    const values = await request("import", await file.text());
    if (dirty && !window.confirm("要用匯入的專案取代目前尚未下載的參數嗎？")) {
      setStatus("已保留目前參數。");
      return;
    }
    setProject(values, file.name);
    setStatus("已匯入專案，可以開始求解。");
  });
});

byId("save-project").addEventListener("click", () => runTask("正在準備專案…", async () => {
  const content = await request("save", parameters());
  const name = projectFile ?? "vehicle_project.json";
  download(/\.json$/i.test(name) ? name : name + ".json", "application/json", content);
  dirty = false;
  setStatus("已開始下載專案 JSON。");
}));

byId("reset-project").addEventListener("click", () => {
  if (dirty && !window.confirm("要用預設值取代目前尚未下載的參數嗎？")) return;
  setProject(defaults);
  setStatus("已恢復預設參數。");
});

async function renderSelectedReport() {
  chapterSelect.length = 1;
  try {
    const {chapters, ok} = await renderResult(lastResult.reports[reportLanguage.value]);
    chapters.forEach((chapter, index) => chapterSelect.add(new Option(chapter, index)));
    setStatus(ok ? (staleResult ? staleMessage : "求解完成。") : "部分公式排版失敗，可下載 Markdown 查看原文。", !ok);
  } catch (error) {
    console.error(error);
    setStatus("報告排版失敗，可下載 Markdown 查看原文。", true);
  }
  reportContent.scrollTop = 0;
}

reportLanguage.addEventListener("change", () => {
  const english = reportLanguage.value === "en";
  chapterSelect.lang = english ? "en" : "zh-Hant";
  chapterSelect.options[0].textContent = english ? "Jump to section" : "跳至章節";
  if (lastResult) runTask("正在切換報告語言…", renderSelectedReport);
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  runTask("正在求解…", async () => {
    lastResult = await request("solve", {
      parameters: parameters(),
      name: projectFile?.replace(/\.json$/i, "") ?? "車輛初步設計",
    });
    staleResult = false;
    setStatus("正在排版報告…");
    await renderSelectedReport();
    if (getComputedStyle(reportContent).overflowY === "visible") byId("results").scrollIntoView();
  });
});

chapterSelect.addEventListener("change", () => {
  byId("chapter-" + chapterSelect.value)?.scrollIntoView({block: "start"});
});

for (const [id, name, type, content] of downloads) {
  byId(id).addEventListener("click", () => {
    if (lastResult && !staleResult) download(name, type, content(lastResult));
  });
}

async function start() {
  byId("retry").hidden = true;
  await runTask("正在載入計算引擎…", async () => {
    const initial = await request("initialize");
    buildForm(initial.schema);
    defaults = initial.parameters;
    setProject(defaults);
    setStatus("已載入預設參數，可以開始求解。");
  });
  byId("retry").hidden = Boolean(defaults);
}

byId("retry").addEventListener("click", start);
start();
