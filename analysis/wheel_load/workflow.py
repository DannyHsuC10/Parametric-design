"""Analysis plugins return figures and CSV tables without import-time I/O."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis_result import AnalysisResult
from .models import (G, WHEELS, Vehicle, alpha_bounds, four_wheel_load_cg,
                     four_wheel_load_lsm, wheel_load_null_direction, wheel_load_stiffness)


def validate(parameters):
    for name, value in parameters.items():
        if not np.isfinite(value):
            raise ValueError(f"{name} 必須是有限數值")
    positive = {"ms", "L", "t", "hl_rear_track_m", "Ks_pitch_N_per_m", "Ks_roll_N_per_m",
                "MR", "hl_rear_heave_spring_ratio", "hl_rear_roll_spring_ratio",
                "hl_front_roll_motion_ratio", "hl_rear_roll_motion_ratio"}
    nonnegative = {"mu", "h_cog", "wl_downforce_N", "mu_w", "wl_mu_y"}
    for name in positive & parameters.keys():
        if parameters[name] <= 0:
            raise ValueError(f"{name} 必須大於零")
    for name in nonnegative & parameters.keys():
        if parameters[name] < 0:
            raise ValueError(f"{name} 不可為負數")
    if "hl_front_weight_ratio" in parameters and not 0 < parameters["hl_front_weight_ratio"] < 1:
        raise ValueError("hl_front_weight_ratio 必須介於 0 和 1 之間")
    if "wl_aero_front_ratio" in parameters and not 0 <= parameters["wl_aero_front_ratio"] <= 1:
        raise ValueError("wl_aero_front_ratio 必須介於 0 和 1 之間（含端點）")
    if "wl_grid_points" in parameters:
        points = parameters["wl_grid_points"]
        if int(points) != points or not 3 <= points <= 201:
            raise ValueError("wl_grid_points 必須為 3 到 201 的整數")


def make_vehicle(p):
    return Vehicle(p["ms"] + 4*p["mu"], p["h_cog"], p["L"], p["t"],
                   p["hl_rear_track_m"], p["hl_front_weight_ratio"],
                   p["wl_downforce_N"], p["wl_aero_front_ratio"])


def acceleration_grid(p):
    count = int(p["wl_grid_points"])
    # Zero limits are supported by the image fallback in envelope_plot.
    x = np.linspace(-abs(p["ax"]), abs(p["ax"]), count)
    y = np.linspace(-abs(p["ay"]), abs(p["ay"]), count)
    return np.meshgrid(x, y)


def load_map(car, x, y, solver):
    return np.array([solver(car, ax*G, ay*G) for ax, ay in zip(x.flat, y.flat)]).reshape(*x.shape, 4)


def map_frame(x, y, loads):
    return pd.DataFrame({"ax_g": x.ravel(), "ay_g": y.ravel(),
                         **{f"{wheel}_N": loads[..., i].ravel() for i, wheel in enumerate(WHEELS)},
                         "all_wheels_in_contact": np.all(loads >= 0, axis=-1).ravel()})


def equilibrium_error(car, x, y, loads):
    targets = np.array([car.target(ax*G, ay*G) for ax, ay in zip(x.flat, y.flat)])
    return float(np.max(np.abs(loads.reshape(-1, 4) @ car.matrix.T - targets)))


def envelope_plot(x, y, loads, title, wheel_indices=(0, 1)):
    # Two load panels and two colorbars stay within the gallery's four-axis limit.
    figure, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained")
    for axis, index in zip(axes.flat, wheel_indices):
        wheel = WHEELS[index]
        values = loads[..., index]
        # pcolormesh also supports degenerate zero-acceleration sweeps.
        if np.ptp(x) and np.ptp(y):
            image = axis.contourf(x, y, values, levels=30)
            if values.min() < 0 < values.max():
                axis.contour(x, y, values, levels=[0], colors="red", linewidths=1.5)
        else:
            image = axis.imshow(values, origin="lower", aspect="auto",
                                extent=[x.min()-.001, x.max()+.001, y.min()-.001, y.max()+.001])
        figure.colorbar(image, ax=axis, label="Wheel load [N]")
        axis.set(title=wheel, xlabel="ax [g]", ylabel="ay [g]")
    figure.suptitle(title + " | red: Fz = 0; negative: contact assumption exceeded")
    return figure


def summary(stage, loads, error):
    return {f"wl_{stage}_min_N": float(loads.min()), f"wl_{stage}_max_N": float(loads.max()),
            f"wl_{stage}_max_equilibrium_error": error}


def fwl(p):
    car = make_vehicle(p)
    x, y = acceleration_grid(p)
    loads = load_map(car, x, y, four_wheel_load_cg)
    main = envelope_plot(x, y, loads, "CG-ratio front wheel-load envelope")
    rear = envelope_plot(x, y, loads, "CG-ratio rear wheel-load envelope", (2, 3))
    overlay = plt.figure(figsize=(10, 7), layout="constrained")
    axis = overlay.add_subplot(projection="3d")
    for i, wheel in enumerate(WHEELS):
        axis.plot_surface(x, y, loads[..., i], color=f"C{i}", alpha=.5, label=wheel)
    axis.set(xlabel="ax [g]", ylabel="ay [g]", zlabel="Wheel load [N]", title="Four wheel-load surfaces")
    axis.legend()
    outputs = summary("FWL", loads, equilibrium_error(car, x, y, loads))
    outputs["wl_FWL_unloaded_fraction"] = float(np.mean(np.any(loads < 0, axis=-1)))
    return AnalysisResult(main, outputs, {"rear_wheel_load_envelope.png": rear, "four_wheel_load_overlay.png": overlay},
                          {"wheel_load_envelope.csv": map_frame(x, y, loads)},
                          {"plot.png": "CG 前輪載重包絡", "rear_wheel_load_envelope.png": "CG 後輪載重包絡",
                           "four_wheel_load_overlay.png": "四輪三維曲面"})


def solver_comparison(p):
    car = make_vehicle(p)
    ax, ay = p["ax"]*G, p["ay"]*G
    first = four_wheel_load_lsm(car, ax, ay)
    second = four_wheel_load_cg(car, ax, ay)
    lateral = np.linspace(0, abs(p["ay"]), int(p["wl_grid_points"]))
    lsm = np.array([four_wheel_load_lsm(car, 0, a*G) for a in lateral])
    cg = np.array([four_wheel_load_cg(car, 0, a*G) for a in lateral])
    difference = cg-lsm
    direction = wheel_load_null_direction(car)
    bounds = [alpha_bounds(base, direction) for base in lsm]
    lower, upper, feasible = map(np.array, zip(*bounds))
    alpha_cg = difference @ direction / (direction @ direction)
    figure, axes = plt.subplots(2, 2, figsize=(12, 9), layout="constrained")
    position = np.arange(4)
    for offset, values, label in ((-.25, first, "LSM"), (0, abs(first-second), "Abs difference"),
                                   (.25, second, "CG ratio")):
        axes[0, 0].bar(position+offset, values, .25, label=label)
    axes[0, 0].set(xticks=position, xticklabels=WHEELS, ylabel="Load [N]",
                   title=f"ax={p['ax']:g} g, ay={p['ay']:g} g")
    for i, wheel in enumerate(WHEELS):
        axes[0, 1].plot(lateral, lsm[:, i], label=wheel)
        axes[1, 0].plot(lateral, cg[:, i], label=wheel)
        axes[1, 1].plot(lateral, np.where(abs(difference[:, i]) < 1e-9, 0, difference[:, i]), label=wheel)
    if np.max(abs(difference)) < 1e-9:
        axes[1, 1].set_ylim(-1, 1)
        axes[1, 1].text(.5, .85, "Solvers coincide within 1e-9 N", transform=axes[1, 1].transAxes, ha="center")
    for axis, title in zip((axes[0, 1], axes[1, 0], axes[1, 1]),
                           ("LSM lateral sweep", "CG lateral sweep", "Solver difference: CG - LSM")):
        axis.set(xlabel="ay [g]", ylabel="Load / difference [N]", title=title)
        axis.axhline(0, color="black", linewidth=.7)
    for axis in axes.flat:
        axis.grid(alpha=.3)
        axis.legend()
    region, axis = plt.subplots(figsize=(9, 5), layout="constrained")
    axis.fill_between(lateral, lower, upper, where=feasible, interpolate=True,
                      alpha=.25, label="All four wheel loads >= 0")
    axis.plot(lateral, lower, label="alpha min")
    axis.plot(lateral, upper, label="alpha max")
    axis.plot(lateral, alpha_cg, "--", color="black", linewidth=1, label="CG coefficient")
    if car.height > 0:
        front, rear = car.axle_loads(0)
        limit_g = (car.front_track*front + car.rear_track*rear)/(2*car.mass*car.height*G)
        if limit_g <= lateral.max():
            axis.axvline(limit_g, linestyle=":", color="red", label=f"Contact limit: {limit_g:.3f} g")
    axis.set(xlabel="ay [g]", ylabel="Null-space coefficient alpha",
             title="Four-wheel contact feasible interval | ax = 0 | fixed null basis")
    axis.grid(alpha=.3)
    axis.legend()
    residual = car.matrix @ direction
    outputs = {"wl_solver_compar_max_difference_N": float(np.max(abs(first-second))),
               "wl_solver_compar_max_null_residual": float(np.max(abs(residual))),
               "wl_solver_compar_feasible_fraction": float(np.mean(feasible))}
    sweep = {"ay_g": lateral, "alpha_min": lower, "alpha_max": upper, "feasible": feasible,
             "alpha_cg": alpha_cg, "interval_gap": upper-lower,
             "lower_unbounded": np.isneginf(lower), "upper_unbounded": np.isposinf(upper)}
    for i, wheel in enumerate(WHEELS):
        sweep.update({f"{wheel}_lsm_N": lsm[:, i], f"{wheel}_cg_N": cg[:, i],
                      f"{wheel}_delta_N": difference[:, i], f"{wheel}_basis_N": direction[i]})
    return AnalysisResult(figure, outputs, {"null_space_feasible_region.png": region},
                          {"solver_comparison.csv": pd.DataFrame({"wheel": WHEELS, "lsm_N": first,
                              "cg_N": second, "abs_difference_N": abs(first-second)}),
                           "null_space_sweep.csv": pd.DataFrame(sweep)},
                          {"plot.png": "求解器、側向掃描與零空間", "null_space_feasible_region.png": "零空間可行範圍"})


def suspension(p):
    car = make_vehicle(p)
    heave_front = p["Ks_pitch_N_per_m"] * p["MR"]**2
    heave_rear = heave_front * p["hl_rear_heave_spring_ratio"]
    roll_front = p["Ks_roll_N_per_m"] * (p["hl_front_roll_motion_ratio"] * car.front_track)**2
    roll_rear = (p["Ks_roll_N_per_m"] * p["hl_rear_roll_spring_ratio"]
                 * (p["hl_rear_roll_motion_ratio"] * car.rear_track)**2)

    def solver(vehicle, ax, ay):
        return wheel_load_stiffness(vehicle, ax, ay, heave_front, heave_rear, roll_front, roll_rear)

    x, y = acceleration_grid(p)
    loads = load_map(car, x, y, solver)
    point = solver(car, p["ax"]*G, p["ay"]*G)
    transfer = car.mass * p["ax"]*G * car.height / car.wheelbase
    pitch = np.rad2deg(transfer * (1/heave_front + 1/heave_rear) / car.wheelbase)
    outputs = summary("sus_load", loads, equilibrium_error(car, x, y, loads))
    outputs.update(wl_sus_load_front_roll_fraction=roll_front/(roll_front+roll_rear), wl_sus_load_pitch_deg=float(pitch))
    outputs.update({f"wl_sus_load_{wheel}_N": float(point[i]) for i, wheel in enumerate(WHEELS)})
    tables = {
        "suspension_load_envelope.csv": map_frame(x, y, loads),
        "operating_point.csv": pd.DataFrame({"wheel": WHEELS, "ax_g": p["ax"], "ay_g": p["ay"],
                                              "raw_Fz_N": point, "in_contact": point >= 0}),
        "stiffness.csv": pd.DataFrame({"axle": ["front", "rear"],
                                      "heave_N_per_m": [heave_front, heave_rear],
                                      "roll_Nm_per_rad": [roll_front, roll_rear],
                                      "pitch_delta_heave_m": [-transfer/heave_front, transfer/heave_rear]}),
    }
    return AnalysisResult(envelope_plot(x, y, loads, "Suspension-stiffness front wheel-load envelope"), outputs,
                          figures={"rear_wheel_load_envelope.png": envelope_plot(
                              x, y, loads, "Suspension-stiffness rear wheel-load envelope", (2, 3))},
                          tables=tables, figure_titles={"plot.png": "懸吊剛性前輪載重包絡",
                                                        "rear_wheel_load_envelope.png": "懸吊剛性後輪載重包絡"})


def tire_limits(p):
    raw = np.array([p[f"wl_sus_load_{wheel}_N"] for wheel in WHEELS])
    fz = np.maximum(raw, 0)
    fx, fy = p["mu_w"]*fz, p["wl_mu_y"]*fz
    valid = bool(np.all(raw >= 0))
    figure, axis = plt.subplots(figsize=(10, 6), layout="constrained")
    x = np.arange(4)
    for offset, values, label in ((-.25, fz, "Fz"), (0, fx, "Fx limit"), (.25, fy, "Fy limit")):
        bars = axis.bar(x+offset, values, .25, label=label)
        axis.bar_label(bars, fmt="%.0f", padding=3, fontsize=8)
    axis.set(xticks=x, xticklabels=WHEELS, ylabel="Force [N]",
             title=f"Independent limits: mu_x={p['mu_w']:g}, mu_y={p['wl_mu_y']:g}"
                   + ("" if valid else "\nContact assumption exceeded; clipped bounds are indicative"))
    axis.margins(y=.18)
    axis.grid(axis="y", alpha=.3)
    axis.legend()
    ellipse, axes = plt.subplots(2, 2, figsize=(10, 8), layout="constrained")
    theta = np.linspace(0, 2*np.pi, 201)
    for i, (axis, wheel) in enumerate(zip(axes.flat, WHEELS)):
        axis.plot(fx[i]*np.cos(theta), fy[i]*np.sin(theta))
        axis.set(title=wheel, xlabel="Fx [N]", ylabel="Fy [N]", aspect="equal")
        axis.grid(alpha=.3)
    ellipse.suptitle("Illustrative friction ellipses; the two independent maxima cannot be combined")
    outputs = {"wl_max_load_max_Fz_N": float(fz.max()), "wl_max_load_max_Fx_N": float(fx.max()),
               "wl_max_load_max_Fy_N": float(fy.max()), "wl_max_load_unloaded_count": int(np.sum(raw < 0)),
               "wl_max_load_contact_valid": int(valid)}
    table = pd.DataFrame({"wheel": WHEELS, "raw_Fz_N": raw, "Fz_clipped_N": fz,
                          "Fx_limit_N": fx, "Fy_limit_N": fy, "in_contact": raw >= 0,
                          "whole_vehicle_contact_valid": valid})
    return AnalysisResult(figure, outputs, {"friction_ellipses.png": ellipse}, {"tire_force_limits.csv": table},
                          {"plot.png": "輪胎獨立方向力上限", "friction_ellipses.png": "摩擦橢圓示意"})


def run_stage(stage, parameters):
    validate(parameters)
    functions = {"FWL": fwl, "solver_compar": solver_comparison, "sus_load": suspension, "max_load": tire_limits}
    result = functions[stage](parameters)
    for name, value in result.outputs.items():
        print(f"{name} = {value:.6g}")
    if stage == "max_load" and not result.outputs["wl_max_load_contact_valid"]:
        print("存在負輪載：截零後的輪胎力僅供參考；目前模型未求解離地後的接觸力重分配。")
    return result
