const pyodideModule = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs";
const workerURL = new URL(import.meta.url);
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
    const sourceURL = new URL(`../${name}`, workerURL);
    sourceURL.search = workerURL.search;
    const response = await fetch(sourceURL);
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
      ? "Could not load the solver. Check your connection and try again."
      : "The solver could not complete this action. Reload the page and try again."});
  }
};
