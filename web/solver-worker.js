const pyodideModule = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs";
const sources = [
  "browser_app.py",
  "project.py",
  "vehicle_initial_sizing.py",
  "vehicle_initial_sizing_report.py",
  "report_english.py",
  "dynamics_export.py",
  "excel_results.py",
  "default_project.json",
  "dynamics_template.json",
];

async function initialize() {
  const {loadPyodide} = await import(pyodideModule);
  const pyodide = await loadPyodide();
  const directory = "/vehicle-sizing";
  pyodide.FS.mkdir(directory);
  await Promise.all(sources.map(async (name) => {
    const response = await fetch(new URL(`../${name}`, import.meta.url));
    if (!response.ok) throw new Error(`Cannot load ${name}: HTTP ${response.status}`);
    pyodide.FS.writeFile(`${directory}/${name}`, new Uint8Array(await response.arrayBuffer()));
  }));
  pyodide.runPython(`
import sys
sys.path.insert(0, "/vehicle-sizing")
from browser_app import handle_request
`);
  return pyodide.globals.get("handle_request");
}

let handleRequest;
self.onmessage = async ({data: {action, payload}}) => {
  try {
    handleRequest ??= await initialize();
    self.postMessage(JSON.parse(handleRequest(action, JSON.stringify(payload))));
  } catch (error) {
    console.error(error);
    self.postMessage({error: action === "initialize"
      ? "無法載入計算引擎。請確認網路連線後再試。"
      : "計算引擎處理失敗，請重新整理頁面後再試。"});
  }
};
