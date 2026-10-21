"""Reproduce original pure functions and audit the integrated solver with matched inputs.

Run: python -m analysis.wheel_load.compare_original
No Excel loader or original module-level plotting code is executed.
"""

import argparse
import ast
from contextlib import redirect_stdout
from dataclasses import replace
import hashlib
import html
from io import StringIO
import json
from pathlib import Path
from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis_data import load_analysis_parameters, parse_analysis_parameters
from analysis_result import normalize_result
from markdown_renderer import render_markdown
from plugin_loader import scan_analysis
from .models import (G, WHEELS, alpha_bounds, four_wheel_load_cg, four_wheel_load_lsm,
                     wheel_load_null_direction, wheel_load_stiffness)
from .parameters import plugin_metadata
from .workflow import make_vehicle


def original_functions(root):
    """Compile only the original top-level functions, without Excel/import side effects."""
    functions = {}
    for filename in ("FWL_solver.py", "sus_load.py"):
        path = Path(root) / "new" / filename
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        body = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
        namespace = {"np": np}
        exec(compile(ast.Module(body=body, type_ignores=[]), str(path), "exec"), namespace)
        functions.update({node.name: namespace[node.name] for node in body})
    return functions


def legacy_alpha_bounds(base, direction):
    """Exact bound loop used in new/solver_compar.py, including its zero-direction skip."""
    lower, upper = -np.inf, np.inf
    for load, slope in zip(base, direction):
        if abs(slope) < 1e-12:
            continue
        if slope > 0:
            lower = max(lower, -load/slope)
        else:
            upper = min(upper, -load/slope)
    return lower, upper


def compare(root, parameters, destination):
    root, destination = Path(root), Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    p = parameters
    vehicle = make_vehicle(p)
    # Original CG/LSM wrappers use one track and F_add=0. Isolate the sign change.
    car = replace(vehicle, rear_track=vehicle.front_track, downforce=0)
    original_car = SimpleNamespace(
        m=car.mass, h=car.height, L=car.wheelbase, d=car.front_track,
        CG_x=np.array([car.front_ratio, 1-car.front_ratio]), CG_y=np.array([.5, .5]))
    originals = original_functions(root)
    ax, ay = p["ax"]*G, p["ay"]*G

    def old_solver(name, x, y):
        return originals[f"four_wheel_load_{name}"](x, y, np.zeros(3), np.zeros(3), original_car)

    rows = []
    raw = {}
    for name, solver in (("cg", four_wheel_load_cg), ("lsm", four_wheel_load_lsm)):
        old = old_solver(name, ax, ay)
        current = solver(car, ax, ay)
        aligned = old_solver(name, ax, -ay)
        raw[name] = old, current
        rows.extend({"model": name, "wheel": wheel, "original_N": old[i], "integrated_N": current[i],
                     "raw_difference_N": current[i]-old[i], "original_with_ay_reversed_N": aligned[i],
                     "difference_after_coordinate_alignment_N": current[i]-aligned[i]}
                    for i, wheel in enumerate(WHEELS))
    pd.DataFrame(rows).to_csv(destination / "cg_lsm_comparison.csv", index=False, encoding="utf-8-sig")

    hf = p["Ks_pitch_N_per_m"] * p["MR"]**2
    hr = hf*p["hl_rear_heave_spring_ratio"]
    rf = p["Ks_roll_N_per_m"]*(p["hl_front_roll_motion_ratio"]*vehicle.front_track)**2
    rr = (p["Ks_roll_N_per_m"]*p["hl_rear_roll_spring_ratio"]
          * (p["hl_rear_roll_motion_ratio"]*vehicle.rear_track)**2)
    # Match the original suspension's front downforce distribution as well.
    sus_car = replace(vehicle, aero_front_ratio=vehicle.front_ratio)
    old_sus = originals["wheel_load_stiffness"](
        vehicle.mass, G, vehicle.downforce, ax, ay, vehicle.height, vehicle.wheelbase,
        vehicle.front_ratio, vehicle.front_track, vehicle.rear_track, hf, hr, rf, rr)
    current_sus = wheel_load_stiffness(sus_car, ax, ay, hf, hr, rf, rr)
    sus_table = pd.DataFrame({"wheel": WHEELS, "original_N": old_sus,
                              "integrated_N": current_sus, "difference_N": current_sus-old_sus})
    sus_table.to_csv(destination / "suspension_comparison.csv", index=False, encoding="utf-8-sig")
    old_fz, new_fz = np.maximum(old_sus, 0), np.maximum(current_sus, 0)
    forces = pd.DataFrame({"wheel": WHEELS, "original_Fz_N": old_fz, "integrated_Fz_N": new_fz,
                           "original_Fx_limit_N": p["mu_w"]*old_fz,
                           "integrated_Fx_limit_N": p["mu_w"]*new_fz,
                           "original_Fy_limit_N": p["wl_mu_y"]*old_fz,
                           "integrated_Fy_limit_N": p["wl_mu_y"]*new_fz})
    forces.to_csv(destination / "tire_force_comparison.csv", index=False, encoding="utf-8-sig")
    old_residual = sus_car.matrix @ old_sus-sus_car.target(ax, ay)
    new_residual = sus_car.matrix @ current_sus-sus_car.target(ax, ay)
    residuals = pd.DataFrame({"equilibrium": ["vertical_force_N", "longitudinal_first_moment_Nm", "lateral_first_moment_Nm"],
                              "original_error": old_residual, "integrated_error": new_residual})
    residuals.to_csv(destination / "equilibrium_errors.csv", index=False, encoding="utf-8-sig")

    lateral = np.linspace(0, max(abs(p["ay"]), 2.2), int(p["wl_grid_points"]))
    bases = np.array([four_wheel_load_lsm(car, 0, a*G) for a in lateral])
    cg = np.array([four_wheel_load_cg(car, 0, a*G) for a in lateral])
    direction = wheel_load_null_direction(car)
    intervals = np.array([alpha_bounds(base, direction) for base in bases])
    lower, upper, feasible = intervals[:, 0], intervals[:, 1], intervals[:, 2].astype(bool)
    original_pairs = [(old_solver("lsm", 0, a*G), old_solver("cg", 0, a*G)) for a in lateral]
    old_bounds = np.array([legacy_alpha_bounds(first, second-first) for first, second in original_pairs])
    alpha_table = pd.DataFrame({"ay_g": lateral, "original_alpha_min": old_bounds[:, 0],
                                "original_alpha_max": old_bounds[:, 1], "corrected_alpha_min": lower,
                                "corrected_alpha_max": upper, "corrected_feasible": feasible,
                                "corrected_interval_gap": upper-lower,
                                "solver_difference_norm_N": np.linalg.norm(cg-bases, axis=1)})
    alpha_table.to_csv(destination / "alpha_comparison.csv", index=False, encoding="utf-8-sig")

    figure, axes = plt.subplots(2, 2, figsize=(13, 9), layout="constrained")
    x = np.arange(4)
    for offset, values, label in ((-.3, raw["cg"][0], "Original CG"), (-.1, raw["lsm"][0], "Original LSM"),
                                   (.1, raw["cg"][1], "Integrated CG"), (.3, raw["lsm"][1], "Integrated LSM")):
        axes[0, 0].bar(x+offset, values, .2, label=label)
    axes[0, 0].set(title="Same ax, ay: CG/LSM lateral sign change", xticks=x, xticklabels=WHEELS, ylabel="Load [N]")
    for offset, values, label in ((-.25, old_sus, "Original"), (0, current_sus, "Integrated"),
                                   (.25, current_sus-old_sus, "Difference")):
        axes[0, 1].bar(x+offset, values, .25, label=label)
    axes[0, 1].set(title="Suspension: matched mass and axle stiffness", xticks=x, xticklabels=WHEELS, ylabel="Load [N]")
    axes[1, 0].plot(lateral, lower, label="Fixed-basis alpha min")
    axes[1, 0].plot(lateral, upper, label="Fixed-basis alpha max")
    axes[1, 0].fill_between(lateral, lower, upper, where=feasible, interpolate=True, alpha=.25)
    axes[1, 0].set(title="Corrected nonnegative-load interval", xlabel="ay [g]", ylabel="alpha")
    axes[1, 1].plot(lateral, np.where(feasible, np.maximum(upper-lower, 0), np.nan), label="Feasible interval width")
    axes[1, 1].set(title=f"CG-LSM norm <= {np.max(np.linalg.norm(cg-bases, axis=1)):.3g} N",
                   xlabel="ay [g]", ylabel="alpha max - alpha min")
    for axis in axes.flat:
        axis.grid(alpha=.3)
        axis.legend(fontsize=8)
    figure.savefig(destination / "comparison.png", dpi=180)
    plt.close(figure)

    mapping = pd.DataFrame({"parameter": list(p), "value": list(p.values())})
    mapping.to_csv(destination / "matched_inputs.csv", index=False, encoding="utf-8-sig")
    manifest = {name: hashlib.sha256((root / "new" / name).read_bytes()).hexdigest()
                for name in ("FWL.py", "FWL_solver.py", "sus_load.py", "solver_compar.py", "max_load.py")}
    (destination / "source_hashes.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    aligned_error = max(abs(row["difference_after_coordinate_alignment_N"]) for row in rows)
    notes = rf"""# 原始分析與整合版：同參數比較

本次直接執行 `new/FWL_solver.py`、`new/sus_load.py` 的原始函式本體，略過 Excel 載入與頂層繪圖。使用現有 CSV 的相同質量、幾何、加速度及換算後的軸端剛度；這是控制變因的公式比較，不是重現未知的舊 Excel 參數。

## 主要差異

- 原版 CG／LSM 在正側向輸入時左側增載，原版 sus_load 則是右側增載。整合版統一為右側增載。因此相同數字的側向輸入會左右對調；將原版 CG／LSM 的側向輸入反號後，最大差異為 {aligned_error:.3g} N。
- 原版 sus_load 把縱向轉移再乘前後 heave 剛度比例。相同工況下，原版總垂向力誤差為 {old_residual[0]:.6g} N，縱向載重一階矩誤差為 {old_residual[1]:.6g} Nm。整合版這兩項誤差為 {new_residual[0]:.3g} N、{new_residual[1]:.3g} Nm。
- 原版與前次整合版都用 CG 與 LSM 的差向量當作零空間方向。兩解重合時該方向為零，係數上下界不能描述完整合法解空間。此次改用非零、固定尺度的零空間基底。
- max_load 的截零與摩擦係數乘輪載公式一致；相同摩擦係數下，輪胎力差異由 sus_load 的輪載差異傳遞而來，詳見 `tire_force_comparison.csv`。

## 零空間係數修正

令總承載為 $W=mg+D$，先定義只與輪距相關的無因次方向，再以固定的 $W/4$ 換算成力：

$$
\mathbf{{u}}=(1,-1,-t_f/t_r,t_f/t_r)^{{\mathsf{{T}}}}
$$

$$
\mathbf{{v}}=\frac{{W}}{{4}}\frac{{\mathbf{{u}}}}{{\max_i|u_i|}},\qquad A\mathbf{{v}}=\mathbf{{0}}
$$

現在使用 $\mathbf{{N}}(\alpha)=\mathbf{{N}}_{{LSM}}+\alpha\mathbf{{v}}$，逐輪限制非負。基底不再依賴 CG 與 LSM 的數值差異，係數為無因次量，沿側向掃描維持相同尺度。

前次圖中的固定 [-5, 5] 視窗已取消，陰影僅填入上下界交集非空的工況。當上下界相交，至少兩個輪載可同時達到零；越過交點則不存在四輪非負輪載平衡解。

## 參數與圖面差異

- 目前總質量為 {vehicle.mass:g} kg，由簧上質量加四輪簧下質量取得；原程式直接讀取 `param.m`，舊值未知。
- 原 FWL 與 sus_load 使用同一個 `target_a` 當作兩軸範圍；整合版分別使用 `ax`、`ay`。原 solver_compar 的側向掃描固定為 0–2 g，目前使用 CSV 的側向上限。
- 原 CG／LSM 腳本的額外力為零，原 sus_load 讀取 `F_ref`；目前共用可調下壓力。本次 CG／LSM 比較固定零下壓力與相同前後輪距，以隔離側向符號改變；sus_load 比較則匹配原版的空力前軸比例。
- 原版直接輸入前後軸 heave、roll 剛度；整合版從共用彈簧剛度、運動比與後軸比例換算。本次將換算後相同軸端數值傳給兩版。
- 原 FWL 三維圖的水平軸是 m/s²，整合版是 g；圖面斜率需換算後比較。

詳見 `matched_inputs.csv`、`cg_lsm_comparison.csv`、`suspension_comparison.csv`、`tire_force_comparison.csv`、`equilibrium_errors.csv` 與 `alpha_comparison.csv`。原始來源雜湊保存在 `source_hashes.json`。
"""
    (destination / "comparison.md").write_text(notes, encoding="utf-8")
    extra = '<img src="comparison.png" style="width:100%;max-width:1300px">'
    for label, frame in (("CG／LSM 指定工況", pd.DataFrame(rows)), ("懸吊輪載比較", sus_table),
                         ("相同摩擦係數下的輪胎力比較", forces), ("平衡誤差", residuals)):
        extra += f"<h2>{html.escape(label)}</h2>" + frame.to_html(index=False, float_format=lambda value: f"{value:.6g}")
    document = render_markdown(notes).replace("</body>", extra+"</body>")
    (destination / "index.html").write_text(document, encoding="utf-8")
    return alpha_table


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=root / "data/analysis_parameters.csv")
    parser.add_argument("--output", type=Path, default=root / "data/results/wheel_load_comparison")
    args = parser.parse_args()
    plugins = {plugin.plugin_id: plugin for plugin in scan_analysis()}
    values = {name: str(value) for plugin in plugins.values() for name, value in plugin.parameter_defaults.items()}
    values.update(load_analysis_parameters(args.csv))
    with redirect_stdout(StringIO()):
        for stage in ("compressed_travel", "aero_stiffness", "frequency_stiffness", "tire_stiffness"):
            plugin = plugins[stage]
            result = normalize_result(plugin.run(parse_analysis_parameters(values, plugin.parameters)))
            try:
                values.update({name: str(value) for name, value in result.outputs.items()})
            finally:
                result.close()
    parameter_types = plugin_metadata("sus_load")["PARAMETERS"] | {"mu_w": "float", "wl_mu_y": "float"}
    compare(root, parse_analysis_parameters(values, parameter_types), args.output)
    print(f"Comparison: {args.output / 'index.html'}")


if __name__ == "__main__":
    main()
