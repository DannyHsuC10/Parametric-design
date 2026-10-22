"""Excel component mass properties, without import-time reads or plotting."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from openpyxl import load_workbook

from analysis_result import AnalysisResult

TITLE = "COG_movable"
DESCRIPTION = "由 Excel 質量分布計算重心、簧上／簧下質量與慣量。"
PLUGIN_ID = "cog_movable"
PROJECT_DIR = Path(__file__).resolve().parents[1]
SOURCE_FILES = {
    "sprung": "data/input_data/Center_of_gravity_LP03_sprung.xlsx",
    "unsprung_front": "data/input_data/Center_of_gravity_LP03_unsprungfront.xlsx",
    "unsprung_rear": "data/input_data/Center_of_gravity_LP03_unsprungrear.xlsx",
}
INPUT_FILES = tuple(PROJECT_DIR / path for path in SOURCE_FILES.values())
PARAMETER_DEFAULTS = {
    # Axle center coordinates are manual vehicle geometry, not Excel component CGs.
    "cog_front_axle_x_m": 0.765, "cog_rear_axle_x_m": -0.765,
    "h_cog": 0.3,
}
PARAMETERS = {
    **dict.fromkeys(("cog_front_axle_x_m", "cog_rear_axle_x_m"), "float"),
    **dict.fromkeys(("t", "hl_rear_track_m", "h_cog"), "float"),
}
HIDDEN_PARAMETERS = set()
OUTPUTS = {
    "ms": "Total sprung mass from Excel (kg)",
    "mu": "Mean unsprung mass per wheel for quarter-car models (kg)",
    "mu_front": "Front unsprung mass per wheel (kg)",
    "mu_rear": "Rear unsprung mass per wheel (kg)",
    "L": "Wheelbase from manually entered wheel-center axle coordinates (m)",
    "cog_total_mass_kg": "Total component mass (kg)",
    "cog_unsprung_front_mass_kg": "Front axle unsprung mass (kg)",
    "cog_unsprung_rear_mass_kg": "Rear axle unsprung mass (kg)",
    "cog_front_axle_x_used_m": "Manually entered front wheel-center axle x relative to Excel datum (m)",
    "cog_rear_axle_x_used_m": "Manually entered rear wheel-center axle x relative to Excel datum (m)",
    "hl_sprung_roll_inertia_kg_m2": "Sprung point-mass Ixx about sprung CG (kg m²)",
    "hl_front_weight_ratio": "Total static front axle weight / total weight",
    "hl_sprung_front_weight_ratio": "Front sprung axle mass / sprung mass",
    **{f"cog_{group}_{axis}_m": f"{group} CG {axis} relative to Excel datum (m)"
       for group in ("total", "sprung") for axis in "xyz"},
    **{f"cog_total_I{a}{a}_kg_m2": f"Total point-mass I{a}{a} about total CG (kg m²)"
       for a in "xyz"},
}


def read_mass_file(file_path, group, track_width=None):
    """Validate the source units and retain each component's Excel location."""
    path = Path(file_path)
    if not path.is_absolute():
        path = PROJECT_DIR / path
    if not path.is_file():
        raise ValueError(f"找不到質量資料：{path}")
    with path.open("rb") as stream:
        book = load_workbook(stream, read_only=True, data_only=True)
        try:
            sheet = book.worksheets[0]
            rows = iter(sheet.iter_rows(values_only=True))
            headers = [str(value).strip() for value in next(rows)]
            units = next(rows)
            lateral = "dy" if group == "sprung" else "dy/y"
            columns = ("name", "weight LP03", "dx", lateral, "dz")
            missing = set(columns) - set(headers)
            if missing:
                raise ValueError(f"{path.name} 缺少欄位：{', '.join(sorted(missing))}")
            indices = [headers.index(name) for name in columns]
            for index, unit in zip(indices[1:], ("kg", "m", "m" if lateral == "dy" else "m/m", "m")):
                if str(units[index]).strip() != unit:
                    raise ValueError(f"{path.name} 的 {headers[index]} 單位必須為 {unit}")
            records = []
            for row_number, row in enumerate(rows, 3):
                if all(value is None for value in row):
                    continue
                name = str(row[indices[0]] or "").strip()
                try:
                    values = np.array([float(row[index]) for index in indices[1:]])
                except (TypeError, ValueError) as error:
                    raise ValueError(f"{path.name} 第 {row_number} 列質量或座標不是有效數值") from error
                if not name or not np.isfinite(values).all() or values[0] < 0:
                    raise ValueError(f"{path.name} 第 {row_number} 列名稱、質量或座標無效")
                mass, x, y, z = values
                if track_width is not None:
                    y *= track_width
                records.append(dict(group=group, name=name, mass_kg=mass, x_m=x, y_m=y, z_m=z,
                                    source_file=str(path), source_sheet=sheet.title, source_row=row_number))
        finally:
            book.close()
    frame = pd.DataFrame(records)
    if frame.empty or frame.mass_kg.sum() <= 0:
        raise ValueError(f"{path.name} 必須包含正質量的元件")
    return frame


def mass_properties(frame):
    """Point-mass first moments and inertia tensors about the datum and CG."""
    masses = frame.mass_kg.to_numpy()
    points = frame[["x_m", "y_m", "z_m"]].to_numpy()
    total = float(masses.sum())
    first = masses @ points
    center = first / total

    def tensor(coords):
        return np.eye(3) * (masses @ np.sum(coords**2, axis=1)) - (coords.T * masses) @ coords

    return dict(mass_kg=total, first_kg_m=first, cg_m=center,
                inertia_datum_kg_m2=tensor(points), inertia_cg_kg_m2=tensor(points - center))


def axle_position(value, label):
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} 軸中心 x 必須輸入數值（m）") from error
    if not np.isfinite(result):
        raise ValueError(f"{label} 軸中心 x 必須是有限數值")
    return result


def calculate(parameters):
    for name in ("t", "hl_rear_track_m", "h_cog"):
        if not np.isfinite(parameters[name]) or parameters[name] <= 0:
            raise ValueError(f"{name} 必須為正的有限數值")
    frames = [read_mass_file(SOURCE_FILES[group], group, track)
              for group, track in (("sprung", None), ("unsprung_front", parameters["t"]),
                                   ("unsprung_rear", parameters["hl_rear_track_m"]))]
    combined = pd.concat(frames, ignore_index=True)
    combined.insert(0, "component_id", np.arange(1, len(combined) + 1))
    props = {name: mass_properties(frame) for name, frame in
             zip(("sprung", "unsprung_front", "unsprung_rear", "total"), [*frames, combined])}
    sprung, front, rear, total = (props[name] for name in ("sprung", "unsprung_front", "unsprung_rear", "total"))
    front_x = axle_position(parameters["cog_front_axle_x_m"], "前輪")
    rear_x = axle_position(parameters["cog_rear_axle_x_m"], "後輪")
    wheelbase = front_x - rear_x
    if wheelbase <= 0:
        raise ValueError("前輪中心 x 必須大於後輪中心 x（x 正方向朝前）")
    ratio = (total["cg_m"][0] - rear_x) / wheelbase
    sprung_ratio = (total["mass_kg"] * ratio - front["mass_kg"]) / sprung["mass_kg"]
    if not 0 < ratio < 1 or not 0 < sprung_ratio < 1:
        raise ValueError("重心／軸座標導致軸載重不合理，請確認原點與軸座標")
    outputs = {
        "ms": sprung["mass_kg"], "mu": (front["mass_kg"] + rear["mass_kg"]) / 4,
        "mu_front": front["mass_kg"] / 2, "mu_rear": rear["mass_kg"] / 2,
        "L": float(wheelbase), "cog_total_mass_kg": total["mass_kg"],
        "cog_unsprung_front_mass_kg": front["mass_kg"], "cog_unsprung_rear_mass_kg": rear["mass_kg"],
        "cog_front_axle_x_used_m": front_x, "cog_rear_axle_x_used_m": rear_x,
        "hl_sprung_roll_inertia_kg_m2": float(sprung["inertia_cg_kg_m2"][0, 0]),
        "hl_front_weight_ratio": float(ratio), "hl_sprung_front_weight_ratio": float(sprung_ratio),
        **{f"cog_{g}_{a}_m": float(props[g]["cg_m"][i]) for g in ("total", "sprung") for i, a in enumerate("xyz")},
        **{f"cog_total_I{a}{a}_kg_m2": float(total["inertia_cg_kg_m2"][i, i]) for i, a in enumerate("xyz")},
    }
    summaries = []
    for group, prop in props.items():
        summaries.append({"group": group, "mass_kg": prop["mass_kg"],
                          **{f"cg_{a}_m": prop["cg_m"][i] for i, a in enumerate("xyz")},
                          **{f"M{a}_kg_m": prop["first_kg_m"][i] for i, a in enumerate("xyz")},
                          **{f"I{a}{b}_{origin}_kg_m2": prop[f"inertia_{origin}_kg_m2"][i, j]
                             for origin in ("datum", "cg") for i, a in enumerate("xyz")
                             for j, b in enumerate("xyz") if j >= i}})
    return combined, pd.DataFrame(summaries), outputs


def main(parameters):
    frame, summary, outputs = calculate(parameters)
    center = np.array([outputs[f"cog_total_{a}_m"] for a in "xyz"])
    relative = frame[["x_m", "y_m", "z_m"]].to_numpy() - center
    yaw = frame.mass_kg.to_numpy() * np.sum(relative[:, :2]**2, axis=1)
    figure = plt.figure(figsize=(11, 8), layout="constrained")
    axis = figure.add_subplot(projection="3d")
    points = axis.scatter(frame.x_m, frame.y_m, frame.z_m, s=frame.mass_kg * 12,
                          c=frame.mass_kg, cmap="viridis", alpha=.75)
    axis.scatter(*center, marker="X", s=160, color="red", label="Total CG")
    axis.set(xlabel="x / datum [m]", ylabel="y / datum [m]", zlabel="z / datum [m]",
             title=f"Component mass distribution | {outputs['cog_total_mass_kg']:.2f} kg")
    axis.legend()
    figure.colorbar(points, ax=axis, shrink=.65, label="Component mass [kg]")
    top, ax = plt.subplots(figsize=(11, 7), layout="constrained")
    points = ax.scatter(frame.x_m, frame.y_m, s=20 + yaw * 15, c=yaw, cmap="viridis", alpha=.75)
    ax.scatter(*center[:2], marker="X", s=160, color="red", label="Total CG")
    for name, x in (("Front axle", outputs["cog_front_axle_x_used_m"]), ("Rear axle", outputs["cog_rear_axle_x_used_m"])):
        ax.axvline(x, linestyle="--", label=name)
    ax.set(xlabel="x / datum [m]", ylabel="y / datum [m]", title="Yaw inertia contributions about total CG")
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(alpha=.3)
    ax.legend()
    top.colorbar(points, ax=ax, label="Point-mass Izz contribution [kg m²]")
    side, ax = plt.subplots(figsize=(12, 8), layout="constrained")
    points = ax.scatter(frame.x_m, frame.z_m, s=frame.mass_kg * 10, c=frame.mass_kg * frame.z_m, cmap="coolwarm")
    # Left/right components share side-view coordinates. Combine their IDs so
    # labels remain readable; the component table retains every full name.
    labels = frame.assign(x_plot=frame.x_m.round(8), z_plot=frame.z_m.round(8))
    for (x, z), rows in labels.groupby(["x_plot", "z_plot"]):
        label = "/".join(str(value) for value in rows.component_id)
        ax.annotate(label, (x, z), xytext=(4, 5), textcoords="offset points", fontsize=8)
    ax.scatter(center[0], center[2], marker="X", s=160, color="red", label="Total CG")
    ax.set(xlabel="x / datum [m]", ylabel="z / datum [m]",
           title="Mass first moments / side view | labels: component IDs")
    ax.grid(alpha=.3)
    ax.legend()
    side.colorbar(points, ax=ax, label="m z / datum [kg m]")
    for name in ("ms", "mu", "mu_front", "mu_rear", "hl_sprung_roll_inertia_kg_m2", "hl_front_weight_ratio"):
        print(f"{name}: {outputs[name]:.8g}")
    return AnalysisResult(figure, outputs, {"inertia_top_view.png": top, "first_moment_side_view.png": side},
                          {"mass_components.csv": frame, "mass_properties.csv": summary},
                          {"plot.png": "元件質量與三維重心", "inertia_top_view.png": "俯視慣量分布",
                           "first_moment_side_view.png": "側視一次質量矩"})
