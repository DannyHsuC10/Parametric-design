"""Numerical helpers shared by the spring simulation analyses."""

import numpy as np


MAX_TIME_SAMPLES = 2_000_001


def require_positive(parameters, *names):
    for name in names:
        value = parameters[name]
        if not np.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and greater than zero")


def time_grid(duration, step):
    """Include the exact endpoint without sampling beyond the solver interval."""
    if not np.isfinite(duration) or not np.isfinite(step) or duration <= 0 or step <= 0:
        raise ValueError("Simulation duration and time step must be finite and positive")
    ratio = duration / step
    if not np.isfinite(ratio) or ratio > MAX_TIME_SAMPLES - 1:
        raise ValueError("Too many time samples; increase the time step or reduce duration")
    times = np.arange(int(np.floor(ratio)) + 1, dtype=float) * step
    if len(times) > 1 and np.isclose(times[-1], duration, rtol=0, atol=1e-12 * max(1.0, duration)):
        times[-1] = duration
    else:
        times = np.append(times, duration)
    return times


def explicit_euler(mass, stiffness, x0, v0, times):
    """Update both states using their values at the previous time step."""
    displacement = np.empty(len(times), dtype=float)
    velocity = np.empty(len(times), dtype=float)
    displacement[0], velocity[0] = x0, v0
    try:
        with np.errstate(over="raise", invalid="raise"):
            for index, step in enumerate(np.diff(times)):
                displacement[index + 1] = displacement[index] + velocity[index] * step
                velocity[index + 1] = (
                    velocity[index] - (stiffness / mass) * displacement[index] * step
                )
    except FloatingPointError as error:
        raise ValueError("Euler response overflowed; reduce the time step or duration") from error
    return displacement, velocity


def analytical_response(mass, stiffness, x0, v0, times):
    omega = np.sqrt(stiffness / mass)
    cosine = np.cos(omega * times)
    sine = np.sin(omega * times)
    return x0 * cosine + (v0 / omega) * sine, -x0 * omega * sine + v0 * cosine


def oscillator_energy(mass, stiffness, displacement, velocity):
    return 0.5 * mass * velocity**2 + 0.5 * stiffness * displacement**2


def energy_error_percent(energy):
    if energy[0] == 0:
        return np.zeros_like(energy)
    return (energy - energy[0]) / energy[0] * 100


