"""Evaluate state-space frequency response without polynomial conversion."""

import numpy as np


def frequency_response(system, w):
    omega = np.asarray(w)
    matrix = 1j * omega[:, None, None] * np.eye(len(system.A)) - system.A
    states = np.linalg.solve(matrix, np.broadcast_to(system.B, (len(omega), *system.B.shape)))
    response = (system.C @ states + system.D)[:, 0, 0]
    return omega, response


def bode(system, w):
    omega, response = frequency_response(system, w)
    return (omega, 20 * np.log10(np.maximum(np.abs(response), 1e-20)),
            np.rad2deg(np.unwrap(np.angle(response))))
