"use strict";

const form = byId("parameters");
const controls = byId("controls");
const chapterSelect = byId("chapters");
const reportLanguage = byId("report-language");
const reportDownload = byId("report-download");
const dynamicsDownload = byId("download-dynamics");
const parameterFields = byId("parameter-fields");
const reportContent = byId("report-content");
const openProjectButton = byId("open-project");
const saveProjectButton = byId("save-project");
const fileInput = byId("project-file");
const workbenchURL = new URL(document.currentScript.src);
const workerURL = new URL("solver-worker.js", workbenchURL);
workerURL.search = workbenchURL.search;
const groupButtons = [];
const groupPanels = [];
const inputs = new Map();
const reportDownloads = {
  markdown: ["vehicle_initial_sizing_report.md", "text/markdown",
    (result) => result.reports[reportLanguage.value].markdown],
  csv: ["vehicle_initial_sizing_results.csv", "text/csv", (result) => "\uFEFF" + result.csv],
  excel: ["vehicle_initial_sizing_results.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    (result) => Uint8Array.from(atob(result.excel), (character) => character.charCodeAt(0))],
};

let worker;
let initialized = false;
let projectFile;
let lastResult;
let staleResult = false;
let busy = false;
let dirty = false;
const staleMessage = "Parameters changed. The report shows the previous results. Solve again to export updated results.";

function request(action, payload = null) {
  const activeWorker = (worker ??= new Worker(workerURL, {type: "module"}));
  return new Promise((resolve, reject) => {
    const timer = action === "initialize" ? setTimeout(() => {
      fail("The solver took too long to load. Check your connection and try again.");
    }, 60000) : undefined;

    function fail(message) {
      clearTimeout(timer);
      activeWorker.terminate();
      worker = null;
      reject(new Error(message));
    }

    activeWorker.onmessage = ({data}) => {
      clearTimeout(timer);
      if (data.error) reject(Object.assign(new Error(data.error), {field: data.field}));
      else resolve(data.result);
    };
    activeWorker.onerror = (error) => {
      console.error(error);
      fail("Could not start the solver. Reload the page and try again.");
    };
    activeWorker.postMessage({action, payload});
  });
}

function setStatus(message, isError = false) {
  byId("status").textContent = message;
  byId("status").classList.toggle("status-error", isError);
}

function updateControls() {
  const editingDisabled = busy || !initialized;
  controls.disabled = editingDisabled;
  openProjectButton.disabled = editingDisabled;
  saveProjectButton.disabled = editingDisabled;
  fileInput.disabled = editingDisabled;
  chapterSelect.disabled = busy || chapterSelect.options.length < 2;
  reportLanguage.disabled = busy;
  const exportDisabled = busy || !lastResult || staleResult;
  reportDownload.disabled = exportDisabled;
  dynamicsDownload.disabled = exportDisabled;
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
  byId("project-name").textContent = filename ?? "Default Parameters";
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
  event.target.removeAttribute("aria-invalid");
  dirty = true;
  staleResult = Boolean(lastResult);
  setStatus(staleResult ? staleMessage : "Parameters changed. You can solve or save the project.");
  updateControls();
});

openProjectButton.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => {
  const [file] = fileInput.files;
  fileInput.value = "";
  if (!file) return;
  runTask("Opening project…", async () => {
    const values = await request("import", await file.text());
    if (dirty && !window.confirm("Replace the current unsaved parameters with the imported project?")) {
      setStatus("Kept the current parameters.");
      return;
    }
    setProject(values, file.name);
    setStatus("Project imported. Ready to solve.");
  });
});

saveProjectButton.addEventListener("click", () => runTask("Preparing project download…", async () => {
  const content = await request("save", parameters());
  const name = projectFile ?? "vehicle_project.json";
  download(/\.json$/i.test(name) ? name : name + ".json", "application/json", content);
  dirty = false;
  setStatus("Project JSON download started.");
}));

async function renderSelectedReport() {
  chapterSelect.length = 1;
  try {
    const {chapters, ok} = await renderResult(lastResult.reports[reportLanguage.value]);
    chapters.forEach((chapter, index) => {
      const option = new Option(chapter, index);
      option.lang = reportLanguage.value === "en" ? "en" : "zh-Hant";
      chapterSelect.add(option);
    });
    setStatus(ok ? (staleResult ? staleMessage : "Solve complete.") : "Some formulas could not be displayed. Download the Markdown to see them.", !ok);
  } catch (error) {
    console.error(error);
    setStatus("The report could not be displayed. Download the Markdown to read it.", true);
  }
  reportContent.scrollTop = 0;
}

reportLanguage.addEventListener("change", () => {
  if (lastResult) runTask("Switching report language…", renderSelectedReport);
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  runTask("Solving…", async () => {
    lastResult = await request("solve", {
      parameters: parameters(),
      name: projectFile?.replace(/\.json$/i, "") ?? "Vehicle Initial Sizing",
    });
    staleResult = false;
    setStatus("Rendering report…");
    await renderSelectedReport();
    if (getComputedStyle(reportContent).overflowY === "visible") byId("results").scrollIntoView();
  });
});

chapterSelect.addEventListener("change", () => {
  byId("chapter-" + chapterSelect.value)?.scrollIntoView({block: "start"});
});

reportDownload.addEventListener("change", () => {
  const format = reportDownload.value;
  reportDownload.value = "";
  if (!format || reportDownload.disabled) return;
  const [name, type, content] = reportDownloads[format];
  download(name, type, content(lastResult));
});

dynamicsDownload.addEventListener("click", () => {
  if (dynamicsDownload.disabled) return;
  download("Vehicle_initial_settings.json", "application/json", lastResult.dynamics);
});

async function start() {
  byId("retry").hidden = true;
  await runTask("Loading the solver…", async () => {
    const initial = await request("initialize");
    buildForm(initial.schema);
    setProject(initial.parameters);
    initialized = true;
    setStatus("Default parameters loaded. Ready to solve.");
  });
  byId("retry").hidden = initialized;
}

byId("retry").addEventListener("click", start);
start();
