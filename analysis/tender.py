"""Model tender spring engagement and the resulting heave and pitch response."""

TITLE = "tender"
DESCRIPTION = "Calculate front and rear suspension strokes with tender springs over braking acceleration and downforce."
PLUGIN_ID = "tender"
PARAMETERS = {
    "ms": "float",
    "mu": "float",
    "K_heave_main_N_per_m": "float",
    "tender_to_heave_stiffness_ratio": "float",
    "aero_cl_cd_F_ref_N": "float",
    "F_ref_ratio": "float",
    "anti_geometry_ratio": "float",
    "L": "float",
    "h_cog": "float",
}
HIDDEN_PARAMETERS = {
    "K_heave_main_N_per_m",
    "tender_to_heave_stiffness_ratio",
    "aero_cl_cd_F_ref_N",
}
OUTPUTS = {
    "tender_bind_total_stroke_mm": "Total main-plus-tender suspension compression where stiffness switches from series to main spring (mm)",
    "tender_bind_spring_stroke_mm": "Tender spring compression at coil bind, excluding main spring compression (mm)",
    "tender_bind_force_N": "Force in each modeled spring assembly at the stiffness switch (N)",
    "tender_bind_vehicle_downforce_N": "Total vehicle downforce at simultaneous front/rear stiffness switch with no braking (N)",
    "max_compression_used_mm": "Maximum positive front or rear suspension compression at the manually selected anti ratio (mm)",
    "max_extension_used_mm": "Maximum front or rear suspension extension magnitude at the manually selected anti ratio (mm)",
}

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import root
from app.analysis_result import AnalysisResult


def main(parameters):
    sprung_mass = parameters["ms"]
    unsprung_mass = parameters["mu"]
    main_heave_stiffness = parameters["K_heave_main_N_per_m"] / 1000.0
    tender_rate = parameters["tender_to_heave_stiffness_ratio"]
    reference_downforce = parameters["aero_cl_cd_F_ref_N"]
    reference_downforce_ratio = parameters["F_ref_ratio"]
    anti_geometry_ratio = parameters["anti_geometry_ratio"]
    wheelbase = parameters["L"]
    cg_height = parameters["h_cog"]
    if sprung_mass <= 0 or unsprung_mass <= 0:
        raise ValueError("ms and mu must be greater than zero")
    if main_heave_stiffness <= 0 or tender_rate <= 0:
        raise ValueError(
            "K_heave_main_N_per_m and tender_to_heave_stiffness_ratio must be greater than zero"
        )
    if wheelbase <= 0 or cg_height < 0 or reference_downforce < 0:
        raise ValueError("L must be positive; h_cog and F_ref cannot be negative")
    if not 0 <= reference_downforce_ratio <= 1:
        raise ValueError("F_ref_ratio must be between 0 and 1")
    if not 0 <= anti_geometry_ratio <= 1:
        raise ValueError("anti_geometry_ratio must be between 0 and 1")

    mass = sprung_mass + 4 * unsprung_mass
    gravity = 9.81
    tender_heave_stiffness = tender_rate * main_heave_stiffness
    series_heave_stiffness = (
        main_heave_stiffness * tender_heave_stiffness
        / (main_heave_stiffness + tender_heave_stiffness)
    )
    max_applied_downforce = reference_downforce * reference_downforce_ratio
    # With no braking the equilibrium equations split vehicle downforce equally
    # between the front and rear spring assemblies.
    bind_force = max_applied_downforce / 2.0
    tender_max_stroke = bind_force / tender_heave_stiffness
    main_stroke_at_bind = bind_force / main_heave_stiffness
    bind_stroke = tender_max_stroke + main_stroke_at_bind

    def series_force(stroke):
        equivalent_stiffness = (
            main_heave_stiffness * tender_heave_stiffness
            / (main_heave_stiffness + tender_heave_stiffness)
        )
        if stroke <= bind_stroke:
            return equivalent_stiffness * stroke
        return bind_force + main_heave_stiffness * (stroke - bind_stroke)

    def solve_strokes(downforce, braking_acceleration_g, anti_geometry_ratio):
        weight_transfer = (
            mass * braking_acceleration_g * gravity * cg_height / wheelbase
        ) * (1 - anti_geometry_ratio)
        total_vertical_force = downforce

        def residual(strokes):
            front_force = series_force(strokes[0])
            rear_force = series_force(strokes[1])
            return (
                front_force + rear_force - total_vertical_force,
                front_force - rear_force - 2 * weight_transfer,
            )

        try:
            solution = root(residual, [10.0, 10.0])
        except (ValueError, FloatingPointError, RuntimeError):
            return None
        front_stroke, rear_stroke = solution.x
        if not np.all(np.isfinite(solution.x)):
            return None
        equilibrium_residual = np.asarray(residual(solution.x), dtype=float)
        force_tolerance = 1e-6 * max(
            abs(total_vertical_force), 2 * abs(weight_transfer), 1.0
        )
        heave = (front_stroke + rear_stroke) / 2
        pitch = np.degrees(
            np.arctan((front_stroke - rear_stroke) / (wheelbase * 1000))
        )
        converged = bool(
            solution.success
            and np.all(np.abs(equilibrium_residual) <= force_tolerance)
        )
        return front_stroke, rear_stroke, heave, pitch, converged

    downforce_ratios = [0.0, 0.25, 0.50, 0.75, 1.0]
    braking_accelerations = np.linspace(0, 2.0, 41)
    final_responses = []
    max_compression = 0.0
    max_extension = 0.0
    skipped_point_count = 0
    for downforce_ratio in downforce_ratios:
        downforce = downforce_ratio * max_applied_downforce
        for acceleration in braking_accelerations:
            response = solve_strokes(downforce, acceleration, anti_geometry_ratio)
            if response is None:
                skipped_point_count += 1
                continue
            final_responses.append((downforce_ratio, acceleration, response))
            max_compression = max(max_compression, response[0], response[1], 0.0)
            max_extension = max(max_extension, -response[0], -response[1], 0.0)

    figure, axes = plt.subplots(2, 2, figsize=(12, 8))
    response_fields = [
        (axes[0, 0], "front", "Front Suspension Stroke", "Front Stroke (mm)"),
        (axes[0, 1], "rear", "Rear Suspension Stroke", "Rear Stroke (mm)"),
        (axes[1, 0], "heave", "Vehicle Heave", "Heave (mm)"),
        (axes[1, 1], "pitch", "Vehicle Pitch", "Pitch (deg)"),
    ]
    pitch_curves = []
    successful_point_count = 0
    nonconverged_point_count = 0
    for downforce_ratio in downforce_ratios:
        successful_accelerations = []
        successful_responses = []
        curve_results = [
            (acceleration, response)
            for ratio, acceleration, response in final_responses
            if ratio == downforce_ratio
        ]
        for acceleration, response in curve_results:
            successful_accelerations.append(acceleration)
            successful_responses.append(response)

        successful_accelerations = np.asarray(successful_accelerations)
        successful_responses = np.asarray(successful_responses)
        successful_point_count += len(successful_responses)
        if len(successful_responses):
            front = successful_responses[:, 0]
            rear = successful_responses[:, 1]
            heave = successful_responses[:, 2]
            pitch = successful_responses[:, 3]
            convergence_flags = successful_responses[:, 4].astype(bool)
            nonconverged_point_count += int(np.count_nonzero(~convergence_flags))
        else:
            front = rear = heave = pitch = np.array([])
        series = {
            "front": front,
            "rear": rear,
            "heave": heave,
            "pitch": pitch,
        }
        label = f"{downforce_ratio * reference_downforce_ratio * 100:.0f}% F_ref"
        for axis, key, title, ylabel in response_fields:
            if len(successful_accelerations):
                axis.plot(
                    successful_accelerations,
                    series[key],
                    linewidth=2,
                    label=label,
                )
            axis.set_title(title)
            axis.set_xlabel("Braking Acceleration (g)")
            axis.set_ylabel(ylabel)
            axis.grid(True)
            axis.legend(title="Applied F_ref")
        pitch_curves.append((successful_accelerations, pitch))

    gradient_figure, pitch_gradient_axis = plt.subplots(figsize=(10, 6))
    for downforce_ratio, (accelerations, pitch) in zip(downforce_ratios, pitch_curves):
        if len(accelerations) < 2:
            continue
        pitch_gradient_axis.plot(
            accelerations,
            np.gradient(pitch, accelerations),
            linewidth=2,
            label=f"{downforce_ratio * reference_downforce_ratio * 100:.0f}% F_ref",
        )
    pitch_gradient_axis.set_xlabel("Braking Acceleration (g)")
    pitch_gradient_axis.set_ylabel("Pitch Gradient (deg/g)")
    pitch_gradient_axis.set_title("Pitch Gradient vs Braking Acceleration")
    pitch_gradient_axis.grid(True)
    pitch_gradient_axis.legend(title="Applied F_ref")
    title = (
        f"Tender response at anti = {anti_geometry_ratio:.0%}; "
        f"maximum applied downforce = {max_applied_downforce:.1f} N"
    )
    figure.suptitle(title)
    figure.tight_layout(rect=[0, 0, 1, 0.96])
    gradient_figure.suptitle(title)
    gradient_figure.tight_layout()

    print(f"Vehicle mass: {mass:.2f} kg")
    print(f"Aero reference downforce F_ref: {reference_downforce:.2f} N")
    print(f"Applied F_ref ratio: {reference_downforce_ratio:.1%}")
    print(f"Maximum applied downforce: {max_applied_downforce:.2f} N")
    print(f"Initial series heave stiffness: {series_heave_stiffness:.3f} N/mm")
    print(f"Tender stroke limit: {tender_max_stroke:.2f} mm")
    print(f"Stiffness switch total stroke: {bind_stroke:.2f} mm")
    print(f"Stiffness switch force: {bind_force:.2f} N")
    print(f"Stiffness switch vehicle downforce (no braking): {max_applied_downforce:.2f} N")
    print(f"Manually set anti geometry ratio: {anti_geometry_ratio:.2f}")
    print(f"Maximum front/rear compression: {max_compression:.2f} mm")
    print(f"Maximum front/rear extension: {max_extension:.2f} mm")
    print(
        f"Equilibrium combinations plotted: {successful_point_count} total "
        f"({successful_point_count - nonconverged_point_count} converged, "
        f"{nonconverged_point_count} nonconverged); {skipped_point_count} skipped "
        "because no finite solution was returned"
    )
    return AnalysisResult(figure, {
        "tender_bind_total_stroke_mm": float(bind_stroke),
        "tender_bind_spring_stroke_mm": float(tender_max_stroke),
        "tender_bind_force_N": float(bind_force),
        "tender_bind_vehicle_downforce_N": float(max_applied_downforce),
        "max_compression_used_mm": float(max_compression),
        "max_extension_used_mm": float(max_extension),
    }, figures={"tender_pitch_gradient.png": gradient_figure}, figure_titles={
        "plot.png": "主要結果｜懸吊行程、Heave 與 Pitch",
        "tender_pitch_gradient.png": "Pitch gradient 與煞車加速度",
    })
