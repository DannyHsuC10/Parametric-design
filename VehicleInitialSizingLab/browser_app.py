"""Bridge the browser worker to the shared project and solver modules."""

import json

from dynamics_export import build_dynamics_export
from project import PROJECT_FORMAT, SCHEMA, default_project, parse_project, validate_inputs
from vehicle_initial_sizing import solve
from vehicle_initial_sizing_report import build_report, render_csv_results


def handle_request(action, payload_json):
    payload = json.loads(payload_json)
    try:
        if action == "initialize":
            result = {"schema": SCHEMA, "parameters": default_project()}
        elif action == "import":
            result = parse_project(payload)
        elif action == "save":
            project = {"application": PROJECT_FORMAT, "schema_version": 1,
                       "parameters": validate_inputs(payload)}
            result = json.dumps(project, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        elif action == "solve":
            snapshot = solve(**payload["parameters"])
            dynamics = build_dynamics_export(snapshot, payload["name"])
            result = {
                "report": build_report(snapshot),
                "csv": render_csv_results(snapshot),
                "dynamics": json.dumps(dynamics, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            }
        else:
            raise ValueError("無法辨識的操作。")
        response = {"result": result}
    except (ValueError, ArithmeticError) as error:
        response = {"error": str(error), "field": getattr(error, "field", None)}
    return json.dumps(response, ensure_ascii=False, allow_nan=False)
