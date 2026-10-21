"""Pure numerical models shared by the cornering-analysis plugins."""

import numpy as np
from scipy.integrate import solve_ivp

G = 9.81


def require_positive(values, names):
    for name in names:
        if not np.isfinite(values[name]) or values[name] <= 0:
            raise ValueError(f"{name} must be finite and greater than zero")


def sweep(low, high, count, name):
    if not np.isfinite([low, high]).all() or low <= 0 or high <= low:
        raise ValueError(f"{name} requires 0 < minimum < maximum")
    if not np.isfinite(count) or count < 2 or int(count) != count:
        raise ValueError(f"{name} requires at least two integer sample points")
    return np.linspace(low, high, int(count))


def cornering_speed(radius, friction):
    radius = np.asarray(radius, dtype=float)
    if not np.isfinite(friction) or friction <= 0 or not np.isfinite(radius).all() or np.any(radius <= 0):
        raise ValueError("Radius and lateral friction must be positive and finite")
    return np.sqrt(friction * G * radius)


def turning_radius(angle_deg, wheelbase):
    angle_deg = np.asarray(angle_deg, dtype=float)
    if not np.isfinite(wheelbase) or wheelbase <= 0:
        raise ValueError("Wheelbase must be finite and greater than zero")
    if not np.isfinite(angle_deg).all() or np.any((angle_deg <= 0) | (angle_deg >= 90)):
        raise ValueError("Steering angles must be between 0 and 90 degrees")
    return wheelbase / np.tan(np.deg2rad(angle_deg))


def ackermann_angles(radius, wheelbase, width):
    radius = np.asarray(radius, dtype=float)
    require_positive({"L": wheelbase, "t": width}, ("L", "t"))
    if not np.isfinite(radius).all() or np.any(radius <= width / 2):
        raise ValueError("Turning radius must be finite and greater than half the front track width")
    return np.arctan(wheelbase / (radius - width / 2)), np.arctan(wheelbase / (radius + width / 2))


def slalom_geometry(track_width, offset_ratios, wheel_track, cone_radius, driving_error,
                    gap, tire_width=0.1905):
    """Circular slalom paths tangent to alternating cone-clearance circles."""
    require_positive({"track_width": track_width, "wheel_track": wheel_track,
                      "gap": gap, "tire_width": tire_width},
                     ("track_width", "wheel_track", "gap", "tire_width"))
    if not np.isfinite([cone_radius, driving_error]).all() or min(cone_radius, driving_error) < 0:
        raise ValueError("Cone radius and driving error must be finite and nonnegative")
    ratios = np.asarray(offset_ratios, dtype=float)
    if ratios.ndim != 1 or not ratios.size or not np.isfinite(ratios).all() or np.any(ratios < 0):
        raise ValueError("Offset ratios must be a nonempty list of finite, nonnegative numbers")
    offsets = track_width * ratios
    clearance = wheel_track / 2 + tire_width / 2 + cone_radius + driving_error
    height = offsets + clearance
    radius = ((gap / 2) ** 2 + height**2) / (2 * height)
    angles = np.rad2deg(np.arctan(2 * (radius - height) / gap))
    return offsets, clearance, radius, angles


def bicycle_ode(time, state, delta_fun, vx, mass, inertia, lf, lr, cf, cr):
    vy, yaw_rate = state
    front_slip = delta_fun(time) - (vy + lf * yaw_rate) / vx
    rear_slip = -(vy - lr * yaw_rate) / vx
    front_force, rear_force = cf * front_slip, cr * rear_slip
    return [(front_force + rear_force) / mass - vx * yaw_rate,
            (lf * front_force - lr * rear_force) / inertia]


def bicycle_step_response(times, step_time, steering_rad, vx, mass, inertia, lf, lr, cf, cr):
    """Integrate only after the steering step so the solver cannot skip it."""
    states = np.zeros((2, len(times)))
    active = times > step_time
    if np.any(active):
        solution = solve_ivp(
            bicycle_ode, (step_time, float(times[-1])), (0.0, 0.0), t_eval=times[active],
            args=(lambda time: steering_rad, vx, mass, inertia, lf, lr, cf, cr),
            rtol=1e-8, atol=1e-10,
        )
        if not solution.success or not np.isfinite(solution.y).all():
            raise ValueError(f"Bicycle model integration failed: {solution.message}")
        states[:, active] = solution.y
    return states
