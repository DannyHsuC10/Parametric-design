"""Noninteractive result galleries for the two migrated aero analyses."""

from dataclasses import asdict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from app.analysis_result import AnalysisResult
from .parameters import DEFAULTS, make_model


def sample(model, parameters, pitch_deg, roll_deg):
    pitch, roll = np.broadcast_arrays(np.asarray(pitch_deg), np.asarray(roll_deg))
    values = model.calculate_from_modal(parameters["v_ref"] / 3.6, parameters["aero_heave_m"],
                                        np.deg2rad(pitch), np.deg2rad(roll))
    frame = pd.DataFrame({"pitch_deg": pitch.ravel(), "roll_deg": roll.ravel(),
                          **{name: value.ravel() for name, value in values.items()}})
    frame["F_front"] = frame.F_FL + frame.F_FR
    frame["F_rear"] = frame.F_RL + frame.F_RR
    frame["dF_left_right"] = frame.F_FL + frame.F_RL - frame.F_FR - frame.F_RR
    frame["dF_front_left_right"] = frame.F_FL - frame.F_FR
    frame["dF_rear_left_right"] = frame.F_RL - frame.F_RR
    frame["roll_downforce_moment_N_m"] = frame.dF_left_right * model.track / 2
    return frame


def _curve(frame, coordinate, title):
    figure, axis = plt.subplots(figsize=(8, 5), layout="constrained")
    axis.plot(frame[f"{coordinate}_deg"], frame.F_down, linewidth=2)
    axis.set(xlabel=f"{coordinate.capitalize()} angle (deg)", ylabel="Total downforce (N)", title=title)
    axis.grid(alpha=0.3)
    return figure


def run_curves(parameters):
    p = DEFAULTS | parameters
    model = make_model(p)
    angles = np.linspace(p["aero_angle_min_deg"], p["aero_angle_max_deg"], int(p["aero_curve_points"]))
    roll = sample(model, p, 0.0, angles)
    pitch = sample(model, p, angles, 0.0)
    baseline = sample(model, p, 0.0, 0.0).iloc[0]
    outputs = {
        "aero_model_CL0": float(model.CL0),
        "aero_modal_baseline_downforce_N": float(baseline.F_down),
        "aero_modal_baseline_drag_N": float(baseline.F_drag),
        "aero_roll_min_downforce_N": float(roll.F_down.min()),
        "aero_roll_max_downforce_N": float(roll.F_down.max()),
        "aero_pitch_min_downforce_N": float(pitch.F_down.min()),
        "aero_pitch_max_downforce_N": float(pitch.F_down.max()),
    }
    print(f"Aero CL0={model.CL0:.5f}; v_ref={p['v_ref']:g} km/h ({p['v_ref']/3.6:g} m/s); "
          f"heave={p['aero_heave_m']*1000:g} mm; baseline downforce={baseline.F_down:.2f} N")
    return AnalysisResult(
        _curve(roll, "roll", "Downforce vs Roll | Pitch = 0 deg"), outputs,
        figures={"pitch_downforce_2d.png": _curve(pitch, "pitch", "Downforce vs Pitch | Roll = 0 deg")},
        tables={"roll_sweep.csv": roll, "pitch_sweep.csv": pitch,
                "baseline.csv": baseline.to_frame().T,
                "model_parameters.csv": pd.DataFrame([asdict(model)])},
        figure_titles={"plot.png": "Roll 角度與下壓力（Pitch＝0°）",
                       "pitch_downforce_2d.png": "Pitch 角度與下壓力（Roll＝0°）"},
    )


def _maps(frame, shape, panels):
    """One or two data panels per page, leaving room for their colorbars."""
    figure = plt.figure(figsize=(7 * len(panels), 5.5))
    # 3D z labels extend outside their axes; reserve a gap before the next
    # panel so they do not collide with the preceding colorbar label.
    figure.subplots_adjust(left=0.04, right=0.94, bottom=0.14, top=0.9, wspace=0.45)
    x = frame.pitch_deg.to_numpy().reshape(shape)
    y = frame.roll_deg.to_numpy().reshape(shape)
    for index, (kind, column, title, unit) in enumerate(panels, 1):
        axis = figure.add_subplot(1, len(panels), index, projection="3d" if kind == "surface" else None)
        z = frame[column].to_numpy().reshape(shape)
        if kind == "surface":
            artist = axis.plot_surface(x, y, z, cmap="viridis", edgecolor="none", alpha=0.9)
            axis.set_zlabel(unit, labelpad=8)
            axis.view_init(elev=25, azim=45)
        else:
            spread = np.ptp(z)
            if spread <= 1e-12 * max(1.0, np.max(np.abs(z))):
                margin = max(1e-6, abs(float(z.flat[0])) * 1e-3)
                levels = np.linspace(float(z.flat[0]) - margin, float(z.flat[0]) + margin, 21)
            else:
                levels = 20
            artist = axis.contourf(x, y, z, levels=levels, cmap="viridis")
            if spread > 1e-12:
                axis.contour(x, y, z, levels=10, colors="black", linewidths=0.4, alpha=0.3)
        axis.set(xlabel="Pitch (deg)", ylabel="Roll (deg)", title=title)
        figure.colorbar(artist, ax=axis, shrink=0.6, pad=0.12 if kind == "surface" else 0.03, label=unit)
    return figure


def _cop_sections(pitch, roll):
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
    for axis, frame, angle, coordinate in ((axes[0], pitch, "pitch", "x"), (axes[1], roll, "roll", "y")):
        axis.plot(frame[f"{angle}_deg"], frame[f"COP_{coordinate}"], linewidth=2)
        axis.set(xlabel=f"{angle.capitalize()} (deg)", ylabel=f"CoP {coordinate} (m)",
                 title=f"CoP {coordinate} vs {angle.capitalize()} | other angle = 0 deg")
        axis.grid(alpha=0.3)
    return figure


def _cl_cop(frame):
    figure, axis = plt.subplots(figsize=(8, 5), layout="constrained")
    artist = axis.scatter(frame.CL, frame.COP_x, c=frame.pitch_deg, cmap="coolwarm", s=14, alpha=0.7)
    axis.set(xlabel="Signed CL", ylabel="Longitudinal CoP (m)", title="Longitudinal CoP vs CL")
    axis.grid(alpha=0.3)
    figure.colorbar(artist, ax=axis, label="Pitch (deg)")
    return figure


def _pitch_sensitivity(model, p, angles):
    figure, axis = plt.subplots(figsize=(8, 5), layout="constrained")
    for roll in np.linspace(p["aero_angle_min_deg"], p["aero_angle_max_deg"], 5):
        section = sample(model, p, angles, roll)
        axis.plot(angles, section.COP_x, label=f"Roll = {roll:g} deg", linewidth=1.7)
    axis.axhline(model.wheelbase * (model.front_balance - 0.5), color="black", linestyle="--", label="Nominal")
    axis.set(xlabel="Pitch (deg)", ylabel="Longitudinal CoP (m)", title="CoP sensitivity to pitch")
    axis.grid(alpha=0.3)
    axis.legend(fontsize=8)
    return figure


def run_surfaces(parameters):
    p = DEFAULTS | parameters
    model = make_model(p, surface=True)
    angles = np.linspace(p["aero_angle_min_deg"], p["aero_angle_max_deg"], int(p["aero_surface_points"]))
    pitch_grid, roll_grid = np.meshgrid(angles, angles)
    frame = sample(model, p, pitch_grid, roll_grid)
    # Evaluate exact zero-angle sections even when an even grid excludes zero.
    pitch = sample(model, p, angles, 0.0)
    roll = sample(model, p, 0.0, angles)
    outputs, summary = {}, []
    for column, name, unit in (("F_down", "downforce", "N"), ("F_drag", "drag", "N"),
                               ("COP_x", "COP_x", "m"), ("COP_y", "COP_y", "m"),
                               *((name, name, "N") for name in ("F_FL", "F_FR", "F_RL", "F_RR"))):
        stats = {"min": float(frame[column].min()), "max": float(frame[column].max()), "mean": float(frame[column].mean())}
        summary.append({"quantity": name, "unit": unit, **stats})
        outputs.update({f"aero_3d_{name}_{stat}_{unit}": value for stat, value in stats.items()})
    for coefficient in ("CL", "CD"):
        for stat in ("min", "max"):
            outputs[f"aero_3d_{coefficient}_{stat}"] = float(getattr(frame[coefficient], stat)())
    for stat in ("min", "max"):
        index = int(getattr(frame.F_down, f"idx{stat}")())
        for angle in ("pitch", "roll"):
            outputs[f"aero_3d_{stat}_downforce_{angle}_deg"] = float(frame.loc[index, f"{angle}_deg"])
    for angle, section in (("pitch", pitch), ("roll", roll)):
        for coordinate in ("x", "y"):
            slope = np.polyfit(np.deg2rad(section[f"{angle}_deg"]), section[f"COP_{coordinate}"], 1)[0]
            outputs[f"aero_3d_dCOP_{coordinate}_d{angle}_m_per_rad"] = float(slope)

    result = AnalysisResult(_maps(frame, pitch_grid.shape, [
        ("surface", "F_down", "Total downforce", "Downforce (N)"),
        ("surface", "CL", "Signed lift coefficient", "CL"),
    ]), outputs, tables={"aero_surface.csv": frame, "pitch_section.csv": pitch, "roll_section.csv": roll,
                        "summary.csv": pd.DataFrame(summary), "model_parameters.csv": pd.DataFrame([asdict(model)])},
        figure_titles={"plot.png": "姿態與總下壓力、CL 曲面"})
    pages = [
        ("cop_surfaces.png", "縱向與橫向 CoP 曲面", [
            ("surface", "COP_x", "Longitudinal CoP", "CoP x (m)"), ("surface", "COP_y", "Lateral CoP", "CoP y (m)")]),
        ("cop_contours.png", "縱向與橫向 CoP 等高線", [
            ("contour", "COP_x", "Longitudinal CoP", "CoP x (m)"), ("contour", "COP_y", "Lateral CoP", "CoP y (m)")]),
        ("axle_downforce_3d.png", "前後軸下壓力曲面", [
            ("surface", "F_front", "Front axle downforce", "Force (N)"), ("surface", "F_rear", "Rear axle downforce", "Force (N)")]),
        ("downforce_drag_maps.png", "總下壓力與阻力等高線", [
            ("contour", "F_down", "Total downforce", "Force (N)"), ("contour", "F_drag", "Aerodynamic drag", "Force (N)")]),
        ("side_asymmetry.png", "左右總下壓力差", [
            ("contour", "dF_left_right", "Left minus right downforce", "Force (N)")]),
        ("front_wheel_downforce_3d.png", "前左與前右下壓力曲面", [
            ("surface", "F_FL", "Front left downforce", "Force (N)"), ("surface", "F_FR", "Front right downforce", "Force (N)")]),
        ("rear_wheel_downforce_3d.png", "後左與後右下壓力曲面", [
            ("surface", "F_RL", "Rear left downforce", "Force (N)"), ("surface", "F_RR", "Rear right downforce", "Force (N)")]),
        ("wheel_asymmetry_maps.png", "前後軸各自左右下壓力差", [
            ("contour", "dF_front_left_right", "Front left minus right", "Force (N)"),
            ("contour", "dF_rear_left_right", "Rear left minus right", "Force (N)")]),
        ("cl_contour.png", "CL 等高線", [("contour", "CL", "Signed lift coefficient", "CL")]),
    ]
    try:
        for filename, title, panels in pages:
            result.figures[filename] = _maps(frame, pitch_grid.shape, panels)
            result.figure_titles[filename] = title
        for filename, title, figure in (
            ("cop_sections.png", "CoP 的精確零角度截面", _cop_sections(pitch, roll)),
            ("cl_cop_relation.png", "CL 與縱向 CoP 的關係", _cl_cop(frame)),
            ("cop_pitch_sensitivity.png", "不同 Roll 下的 CoP／Pitch 敏感度", _pitch_sensitivity(model, p, angles)),
        ):
            result.figures[filename] = figure
            result.figure_titles[filename] = title
        print(f"Aero 3D: {len(frame)} grid points; downforce {frame.F_down.min():.2f}–{frame.F_down.max():.2f} N; "
              f"CoP x {frame.COP_x.min():.4f}–{frame.COP_x.max():.4f} m; "
              f"CoP y {frame.COP_y.min():.4f}–{frame.COP_y.max():.4f} m")
        return result
    except BaseException:
        result.close()
        raise
