"""Small, independently runnable stages around the complete imported models."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal
from scipy.integrate import solve_ivp

from app.analysis_result import AnalysisResult
from .damper import DamperAnalysis
from .equivalent_independent import EquivalentIndependentAnalysis
from .heave_analysis import HeaveAnalysis
from .frequency import frequency_response
from .parameters import STAGES
from .roll_analysis import RollAnalysis
from .simulation import SimulationAnalysis
from .state_space import StateSpaceAnalysis, StateSpaceOutputs
from .vehicle import make_vehicle


def response_metrics(time, response, final):
    """2% settling time is undefined if the response has not settled by the end."""
    response = np.asarray(response)
    outside = np.flatnonzero(np.abs(response - final) > 0.02 * max(abs(final), 1e-12))
    settling = (float(time[outside[-1] + 1]) if len(outside) and outside[-1] + 1 < len(time)
                else (np.nan if len(outside) else 0.0))
    peak_index = int(np.argmax(np.abs(response)))
    return {"final": final, "peak_abs": float(abs(response[peak_index])),
            "peak_time_s": float(time[peak_index]), "settling_2_percent_s": settling,
            "overshoot_percent": max(0.0, (abs(response[peak_index]) - abs(final))
                                      / max(abs(final), 1e-12) * 100)}


def build_models(parameters):
    vehicle = make_vehicle(parameters)
    heave = HeaveAnalysis(vehicle).run()
    roll = RollAnalysis(vehicle).run()
    independent = EquivalentIndependentAnalysis(vehicle, heave, roll).run()
    state = StateSpaceAnalysis(vehicle, heave, roll)
    fit = state._fit_physical_roll_damping()
    systems = StateSpaceOutputs(
        roll_physical_low=state._roll_system(fit["low_matrix"]),
        roll_physical_high=state._roll_system(fit["high_matrix"]),
        roll_modal_low=state._roll_system(roll.modal.damping_matrix_low),
        roll_modal_high=state._roll_system(roll.modal.damping_matrix_high),
        roll_1dof_low=state._roll_1dof(roll.modal.target_zeta_low[0]),
        roll_1dof_high=state._roll_1dof(roll.modal.target_zeta_high[0]),
        physical_fit=fit["table"],
    )
    damper = DamperAnalysis(vehicle, heave, roll, independent, systems)
    simulation = SimulationAnalysis(vehicle, heave, roll, independent, damper)
    return vehicle, heave, roll, independent, state, systems, damper, simulation


def _bars(frames, title):
    figure, axes = plt.subplots(1, len(frames), figsize=(6 * len(frames), 4.8), squeeze=False)
    for axis, (label, values) in zip(axes[0], frames.items()):
        axis.bar(list(values), list(values.values()), color=["#3878b4", "#ed9a37"])
        axis.set(title=label, xlabel="Axle")
        axis.grid(axis="y", alpha=0.3)
    figure.suptitle(title)
    figure.tight_layout()
    return figure


def _heave_response(vehicle, heave, state):
    table, traces = [], {}
    time = np.linspace(0, 3, 1200)
    frequency = np.logspace(-1, 2.3, 600)
    for axle, axle_heave in ((vehicle.front, heave.front), (vehicle.rear, heave.rear)):
        figure, axes = plt.subplots(3, 1, figsize=(9, 9))
        for speed in ("low", "high"):
            system = state.heave_system(axle, axle_heave, speed)
            _, response = signal.step(system, T=time)
            response = np.squeeze(response) * 20  # 20 mm road displacement
            _, frf = frequency_response(system, w=2 * np.pi * frequency)
            axes[0].plot(time, response, label=speed)
            axes[1].semilogx(frequency, 20 * np.log10(np.maximum(np.abs(frf), 1e-20)), label=speed)
            axes[2].semilogx(frequency, np.rad2deg(np.unwrap(np.angle(frf))), label=speed)
            table.append({"axle": axle.name, "speed": speed,
                          **response_metrics(time, response, 20.0)})
            traces[f"heave_{axle.name}_{speed}_step.csv"] = pd.DataFrame({
                "time_s": time, "sprung_displacement_mm": response})
            traces[f"heave_{axle.name}_{speed}_frequency.csv"] = pd.DataFrame({
                "frequency_hz": frequency, "magnitude_ratio": np.abs(frf),
                "phase_deg": np.rad2deg(np.unwrap(np.angle(frf)))})
        axes[0].set(xlabel="Time [s]", ylabel="Sprung displacement [mm]", title="20 mm road step")
        axes[1].set(xlabel="Frequency [Hz]", ylabel="Magnitude [dB]", title="Road to sprung mass")
        axes[2].set(xlabel="Frequency [Hz]", ylabel="Phase [deg]")
        for axis in axes:
            axis.legend()
            axis.grid(True, which="both")
        figure.suptitle(f"{axle.name.title()} heave: low / high damping linearizations")
        figure.tight_layout()
        state.collect_figure(f"heave_{axle.name}_response.png", figure)
    return pd.DataFrame(table), traces


def _roll_response(vehicle, state, systems):
    ay = vehicle.analysis.roll_step_ay_g
    state._plot_roll_steps({name: getattr(systems, f"roll_{name.replace(' ', '_')}")
                            for name in ("modal low", "modal high", "physical low", "physical high")})
    state._plot_single_roll_step(systems.roll_modal_low, "Modal roll low damping", "roll_step_low_speed.png", ay)
    state._plot_single_roll_step(systems.roll_modal_high, "Modal roll high damping", "roll_step_high_speed.png", ay)
    state._plot_roll_bode(systems.roll_modal_low, systems.roll_modal_high)
    state._plot_single_roll_bode(systems.roll_modal_low, "Modal roll low damping", "roll_bode_low_speed.png")
    state._plot_single_roll_bode(systems.roll_modal_high, "Modal roll high damping", "roll_bode_high_speed.png")
    state._plot_roll_1dof(systems.roll_1dof_low, systems.roll_1dof_high, ay)
    state._plot_roll_solution_comparison(systems.roll_modal_low, systems.roll_modal_high,
        systems.roll_physical_low, systems.roll_physical_high, systems.roll_1dof_low, systems.roll_1dof_high, ay)
    figure, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    frequency = np.logspace(-1, 2.3, 600)
    time = np.linspace(0, 3, 1200)
    metrics, modes, tables = [], [], {}
    for column, speed in enumerate(("low", "high")):
        for model in ("modal", "physical", "1dof"):
            system = getattr(systems, f"roll_{model}_{speed}")
            _, frf = frequency_response(system, w=2 * np.pi * frequency)
            gain = np.abs(frf) * 180 / np.pi
            phase = np.rad2deg(np.unwrap(np.angle(frf)))
            axes[0, column].semilogx(frequency, gain, label=model)
            axes[1, column].semilogx(frequency, phase, label=model)
            _, response, states = signal.lsim(system, U=np.full_like(time, ay), T=time)
            response = np.rad2deg(np.squeeze(response))
            final = float((system.C @ np.linalg.solve(-system.A, system.B) + system.D).item())
            metrics.append({"model": model, "speed": speed,
                            **response_metrics(time, response, np.rad2deg(final * ay))})
            step_table = {"time_s": time, "sprung_roll_deg": response}
            if model != "1dof":
                step_table.update(front_unsprung_roll_deg=np.rad2deg(states[:, 1]),
                                  rear_unsprung_roll_deg=np.rad2deg(states[:, 2]))
            tables[f"roll_{model}_{speed}_step.csv"] = pd.DataFrame(step_table)
            tables[f"roll_{model}_{speed}_frequency.csv"] = pd.DataFrame({
                "frequency_hz": frequency, "gain_deg_per_g": gain, "phase_deg": phase})
            for pole in np.linalg.eigvals(system.A):
                modes.append({"model": model, "speed": speed, "pole_real_per_s": pole.real,
                              "pole_imag_per_s": pole.imag, "natural_frequency_hz": abs(pole) / (2 * np.pi),
                              "damping_ratio": -pole.real / max(abs(pole), 1e-12)})
        axes[0, column].set(title=f"{speed.title()} damping", ylabel="Gain [deg/g]")
        axes[1, column].set(xlabel="Frequency [Hz]", ylabel="Phase [deg]")
    for axis in axes.flat:
        axis.grid(True, which="both")
        axis.legend()
    figure.suptitle("Roll frequency response: modal / physical / 1DOF")
    figure.tight_layout()
    state.collect_figure("roll_frequency_comparison.png", figure)
    tables.update(roll_step_metrics=pd.DataFrame(metrics), roll_damped_poles=pd.DataFrame(modes),
                  roll_physical_damping_fit=systems.physical_fit)
    return tables


def simulate_lateral(vehicle, roll, curves, duration_s=2.0):
    """3DOF ODE with the fitted, piecewise roll dampers, driven by a lateral step."""
    arms = np.array([vehicle.front.motion_ratio.roll * vehicle.front.track_m,
                     vehicle.rear.motion_ratio.roll * vehicle.rear.track_m])
    force = np.array([vehicle.weight_n * roll.modal.sprung_to_roll_axis_height_m
                      * vehicle.analysis.roll_step_ay_g, 0.0, 0.0])
    inverse_mass = np.linalg.inv(roll.mass_matrix)

    def rhs(_time, state):
        angles, rates = state[:3], state[3:]
        velocities = (rates[0] - rates[1:]) * arms * 1000
        moments = np.array([curves[name].force(v).item() for name, v in
                            zip(("front", "rear"), velocities)]) * arms
        damping = np.array([sum(moments), -moments[0], -moments[1]])
        return np.r_[rates, inverse_mass @ (force - roll.stiffness_matrix @ angles - damping)]

    if not np.isfinite(duration_s) or duration_s <= 0:
        raise ValueError("duration_s 必須為正的有限數值")
    time = np.linspace(0, duration_s, max(2, int(np.ceil(duration_s * 450))))
    solution = solve_ivp(rhs, (0, duration_s), np.zeros(6), t_eval=time, rtol=1e-7, atol=1e-9)
    if not solution.success:
        raise ValueError(f"Roll ODE integration failed: {solution.message}")
    table = pd.DataFrame({"time_s": time, "sprung_roll_deg": np.rad2deg(solution.y[0]),
                          "front_unsprung_roll_deg": np.rad2deg(solution.y[1]),
                          "rear_unsprung_roll_deg": np.rad2deg(solution.y[2])})
    for index, axle in enumerate((vehicle.front, vehicle.rear), start=1):
        static = vehicle.weight_n * axle.weight_ratio / 2
        delta = vehicle.tire_vertical_rate_n_per_m * axle.track_m * solution.y[index] / 2
        table[f"{axle.name}_outside_fz_n"] = static + delta
        table[f"{axle.name}_inside_fz_n"] = static - delta
    return table


def _ode_results(vehicle, heave, roll, state, systems, damper, simulation):
    simulations, tables, metrics = {}, {}, []
    for case, acceleration in (("braking", -vehicle.analysis.ode_braking_g),
                               ("acceleration", vehicle.analysis.ode_acceleration_g)):
        response = simulation._plot_longitudinal_ode(
            acceleration, f"ode_{case}.png", f"nonlinear_{case}_comparison.png")
        simulations[case] = response
        for topology in ("decoupled", "independent"):
            pitch = response[f"pitch_{topology}_deg"]
            data = {"time_s": pitch["time_s"], "pitch_deg": pitch["value"]}
            front_force, rear_force = simulation._longitudinal_transfer_forces(acceleration)
            final_pitch = np.rad2deg(np.arctan2(
                front_force / heave.front.ride_rate_n_per_m
                - rear_force / heave.rear.ride_rate_n_per_m, vehicle.wheelbase_m))
            metrics.append({"case": case, "model": topology, "response": "pitch_deg",
                            **response_metrics(pitch["time_s"], pitch["value"], final_pitch)})
            for axle in (vehicle.front, vehicle.rear):
                trace = response[f"{axle.name}_{topology}"]
                divider = 2 if topology == "decoupled" else 1
                data[f"{axle.name}_sprung_displacement_m"] = trace["sprung_displacement_m"]
                data[f"{axle.name}_unsprung_displacement_m"] = trace["unsprung_displacement_m"]
                data[f"{axle.name}_tire_fz_n"] = (vehicle.weight_n * axle.weight_ratio / 2
                                                   + trace["tire_force_delta_n"] / divider)
            tables[f"ode_{case}_{topology}.csv"] = pd.DataFrame(data)
    simulation._plot_decoupled_longitudinal_comparison(simulations["braking"], simulations["acceleration"])
    state._plot_tire_fz_transient(systems.roll_physical_low, vehicle.analysis.roll_step_ay_g)
    lateral = simulate_lateral(vehicle, roll, damper._roll_physical_curves())
    tables["ode_cornering_physical.csv"] = lateral
    final = roll.roll_gradient_deg_per_g * vehicle.analysis.roll_step_ay_g
    metrics.append({"case": "cornering", "model": "physical nonlinear", "response": "roll_deg",
                    **response_metrics(lateral.time_s.to_numpy(), lateral.sprung_roll_deg.to_numpy(), final)})
    figure, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    for column in ("sprung_roll_deg", "front_unsprung_roll_deg", "rear_unsprung_roll_deg"):
        axes[0].plot(lateral.time_s, lateral[column], label=column.removesuffix("_deg"))
    for column in lateral.columns:
        if column.endswith("_fz_n"):
            axes[1].plot(lateral.time_s, lateral[column], label=column.removesuffix("_fz_n"))
    axes[0].set(ylabel="Roll [deg]", title="Nonlinear physical roll dampers: 3DOF cornering ODE")
    axes[1].set(xlabel="Time [s]", ylabel="Tire normal force [N]")
    axes[1].axhline(0, color="black", linestyle="--", linewidth=1)
    for axis in axes:
        axis.legend(ncol=2)
        axis.grid(True)
    figure.tight_layout()
    simulation.collect_figure("ode_cornering_physical.png", figure)
    tables["ode_metrics.csv"] = pd.DataFrame(metrics)
    return simulations, lateral, tables


def run_stage(stage, parameters):
    vehicle, heave, roll, independent, state, systems, damper, simulation = build_models(parameters)
    tables, figures, values = {}, {}, []
    if stage == "hl_heave":
        tables["heave_summary.csv"] = heave.to_frame()
        figure = _bars({"Ride rate [N/m]": {"front": heave.front.ride_rate_n_per_m, "rear": heave.rear.ride_rate_n_per_m},
                        "Natural frequency [Hz]": {"front": heave.front.natural_frequency_hz, "rear": heave.rear.natural_frequency_hz}},
                       "Heave spring / tire series stiffness")
        values = [heave.front.natural_frequency_hz, heave.rear.natural_frequency_hz]
    elif stage == "hl_heave_response":
        metrics, traces = _heave_response(vehicle, heave, state)
        tables = {"heave_step_metrics.csv": metrics, **traces}
        figures = state.figures
        figure = figures["heave_front_response.png"]
        values = [metrics.loc[metrics.axle == axle, "peak_abs"].max() for axle in ("front", "rear")]
    elif stage == "hl_roll":
        tables = {"roll_summary.csv": roll.to_frame(),
                  "roll_modes.csv": pd.DataFrame({"mode": [1, 2, 3], "natural_frequency_hz": roll.modal.natural_frequencies_hz,
                      "target_zeta_low": roll.modal.target_zeta_low, "target_zeta_high": roll.modal.target_zeta_high})}
        for name, matrix in (("mass", roll.mass_matrix), ("stiffness", roll.stiffness_matrix),
                             ("modal_damping_low", roll.modal.damping_matrix_low),
                             ("modal_damping_high", roll.modal.damping_matrix_high), ("mode_shapes", roll.modal.mode_shapes)):
            tables[f"roll_{name}.csv"] = pd.DataFrame(matrix, columns=["sprung", "front_unsprung", "rear_unsprung"]
                if name != "mode_shapes" else ["mode_1", "mode_2", "mode_3"])
        figure = _bars({"Actual roll stiffness [Nm/rad]": {"front": roll.front.actual_roll_stiffness_n_m_per_rad,
                       "rear": roll.rear.actual_roll_stiffness_n_m_per_rad}}, "3DOF roll stiffness distribution")
        values = [roll.roll_gradient_deg_per_g, *roll.modal.natural_frequencies_hz]
    elif stage == "hl_roll_response":
        tables = _roll_response(vehicle, state, systems)
        figures = state.figures
        figure = figures["roll_response_modal_physical_1dof.png"]
        values = systems.physical_fit.relative_fit_error.to_list()
    elif stage in {"hl_heave_damper", "hl_independent_damper"}:
        is_independent = stage == "hl_independent_damper"
        curves = damper._heave_curves(is_independent)
        title = "Independent equivalent shock dyno" if is_independent else "Decoupled asymmetric heave shock dyno"
        damper._plot_curves(curves, title, "shock_dyno.png")
        tables["damper_coefficients.csv"] = damper._curve_table(curves)
        velocity = np.linspace(-250, 250, 501)
        tables["shock_dyno.csv"] = pd.DataFrame({"velocity_mm_s": velocity,
            **{f"{name}_force_n": curve.force(velocity) for name, curve in curves.items()}})
        figures = damper.figures
        figure = figures["shock_dyno.png"]
        values = [curves[name].force(250).item() for name in ("front", "rear")]
    elif stage == "hl_roll_damper":
        physical, one_dof = damper._roll_physical_curves(), damper._roll_1dof_curves()
        damper._plot_curves(physical, "Physical roll shock dyno", "shock_dyno_roll_physical.png")
        damper._plot_roll_solution_compare(one_dof, physical)
        tables = {"damper_roll_physical.csv": damper._curve_table(physical),
                  "damper_roll_1dof.csv": damper._curve_table(one_dof),
                  "roll_physical_damping_fit.csv": systems.physical_fit}
        velocity = np.linspace(-250, 250, 501)
        tables["roll_shock_dyno.csv"] = pd.DataFrame({"velocity_mm_s": velocity, **{
            f"{model}_{axle}_force_n": curves[axle].force(velocity)
            for model, curves in (("physical", physical), ("1dof", one_dof)) for axle in ("front", "rear")}})
        figures = damper.figures
        figure = figures["shock_dyno_roll_solution_compare.png"]
        values = [physical[name].low_bump_n_per_mm_s * 1000 for name in ("front", "rear")]
    elif stage == "hl_independent":
        tables["independent_equivalent.csv"] = independent.to_frame()
        figure = _bars({"Single-wheel spring [N/mm]": {"front": independent.front.spring_rate_n_per_mm,
                        "rear": independent.rear.spring_rate_n_per_mm},
                        "Required ARB [Nm/rad]": {"front": independent.front.required_arb_stiffness_n_m_per_rad,
                        "rear": independent.rear.required_arb_stiffness_n_m_per_rad}}, "Independent suspension equivalence")
        values = [independent.front.spring_rate_n_per_mm, independent.rear.spring_rate_n_per_mm]
    elif stage == "hl_load_cases":
        table = pd.DataFrame([simulation._calc_scenario(item) for item in vehicle.analysis.scenarios])
        tables["spring_force_scenarios.csv"] = table
        figure, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
        x = np.arange(len(table))
        axes[0].plot(x, table.pitch_deg, "o-", label="pitch")
        axes[0].plot(x, table.roll_deg, "o-", label="roll")
        axes[0].set_ylabel("Angle [deg]")
        for axle in ("front", "rear"):
            axes[1].plot(x, table[f"{axle}_heave_spring_stroke_mm"], "o-", label=f"{axle} heave")
            axes[1].plot(x, table[f"{axle}_roll_suspension_travel_mm"], "s--", label=f"{axle} roll")
            axes[2].plot(x, table[f"{axle}_heave_spring_force_n"], "o-", label=f"{axle} heave")
            axes[2].plot(x, table[f"{axle}_roll_spring_force_n"], "s--", label=f"{axle} roll")
        axes[1].set_ylabel("Spring stroke [mm]")
        axes[2].set_ylabel("Spring force [N]")
        axes[2].set_xticks(x, table["case"], rotation=20, ha="right")
        for axis in axes:
            axis.legend(ncol=2)
            axis.grid(True)
        figure.suptitle("Quasi-static acceleration / braking / cornering cases")
        figure.tight_layout()
        values = [table.pitch_deg.abs().max(), table.roll_deg.abs().max()]
    elif stage == "hl_ode":
        simulations, lateral, tables = _ode_results(vehicle, heave, roll, state, systems, damper, simulation)
        figures = {**state.figures, **simulation.figures}
        figure = figures["fig_decoupled_longitudinal_accel_brake_ode45.png"]
        values = [np.max(np.abs(simulations[case]["pitch_decoupled_deg"]["value"])) for case in ("braking", "acceleration")]
        values.append(lateral.filter(like="_fz_n").min().min())
    else:
        raise ValueError(f"Unknown HL damping stage: {stage}")
    outputs = {f"{stage}_{key}": float(value) for key, value in zip(STAGES[stage][3], values, strict=True)}
    print(STAGES[stage][1])
    for name, value in outputs.items():
        print(f"{name}: {value:.6g}")
    return AnalysisResult(figure, outputs, figures, tables)
