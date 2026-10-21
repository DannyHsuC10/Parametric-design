"""Shared parameter conversion and solvers for damped suspension analyses."""

import numpy as np
from scipy.integrate import solve_ivp

from oscillation_models import require_positive


SINGLE_DOF_PARAMETERS = {
    "ms": "float",
    "Ks": "float",
    "Kt": "float",
    "MR": "float",
    "damping_rate_best_ratio": "float",
}
QUARTER_CAR_PARAMETERS = {
    "ms": "float",
    "mu": "float",
    "Ks": "float",
    "Kt": "float",
    "damping_rate_best_ratio": "float",
}


def system_settings(parameters, quarter_car=False, damping_ratio=None):
    """Use Ks for the two-mass model, or tire-corrected ride rate for SDOF."""
    require_positive(parameters, "ms", "Ks", "Kt")
    mass = parameters["ms"] / 4
    stiffness = parameters["Ks"]
    if quarter_car:
        require_positive(parameters, "mu")
    else:
        require_positive(parameters, "MR")
        wheel_rate = stiffness * parameters["MR"] ** 2
        stiffness = wheel_rate * parameters["Kt"] / (wheel_rate + parameters["Kt"])
    ratio = parameters["damping_rate_best_ratio"] if damping_ratio is None else damping_ratio
    if not np.isfinite(ratio) or ratio < 0:
        raise ValueError("Damping ratio must be finite and nonnegative")
    critical = float(2 * np.sqrt(mass * stiffness))
    return mass, float(stiffness), ratio * critical, critical, ratio


def checked_solution(rhs, times, initial_state, rtol=0.001, atol=0.000001):
    solution = solve_ivp(rhs, (times[0], times[-1]), initial_state, t_eval=times,
                         method="RK45", rtol=rtol, atol=atol)
    if not solution.success or not np.all(np.isfinite(solution.y)):
        raise RuntimeError(f"Damped suspension solver failed: {solution.message}")
    return solution.y


def quarter_car_response(ms, mu, ks, kt, damping, times, initial_state,
                         road_height=0.0, road_step_time=None, rtol=0.001, atol=0.000001):
    """Solve equilibrium-relative states; split integration at a road discontinuity."""
    boundaries = [float(times[0]), float(times[-1])]
    if road_step_time is not None and times[0] < road_step_time < times[-1]:
        boundaries.insert(1, float(road_step_time))
    state = np.asarray(initial_state, dtype=float)
    response = np.empty((4, len(times)))
    for start, end in zip(boundaries, boundaries[1:]):
        road = road_height if road_step_time is not None and start >= road_step_time else 0.0

        def rhs(time, current):
            xs, vs, xu, vu = current
            force = ks * (xs - xu) + damping * (vs - vu)
            return [vs, -force / ms, vu, (force - kt * (xu - road)) / mu]

        solution = solve_ivp(rhs, (start, end), state, dense_output=True,
                             method="RK45", rtol=rtol, atol=atol)
        if not solution.success or not np.all(np.isfinite(solution.y)):
            raise RuntimeError(f"Quarter-car solver failed: {solution.message}")
        mask = (times >= start) & (times <= end)
        response[:, mask] = solution.sol(times[mask])
        state = solution.y[:, -1]
    if not np.all(np.isfinite(response)):
        raise RuntimeError("Quarter-car solver produced a non-finite sampled response")
    return response


def print_settings(mass, stiffness, damping, ratio, stiffness_name):
    print(f"Quarter sprung mass: {mass:.6g} kg")
    print(f"{stiffness_name}: {stiffness:.6f} N/m")
    print(f"Damping ratio from damping_rate_best_ratio: {ratio:.6g}; damping coefficient: {damping:.6f} N s/m")
