"""Quasi-static models. x is forward, y is left; positive ay loads the right wheels."""

from dataclasses import dataclass
import numpy as np

G = 9.81
WHEELS = ("FL", "FR", "RL", "RR")


@dataclass(frozen=True)
class Vehicle:
    mass: float
    height: float
    wheelbase: float
    front_track: float
    rear_track: float
    front_ratio: float
    downforce: float = 0.0
    aero_front_ratio: float = 0.5

    @property
    def matrix(self):
        f = self.front_ratio
        return np.array([
            [1, 1, 1, 1],
            [self.wheelbase * (1-f)] * 2 + [-self.wheelbase * f] * 2,
            [self.front_track/2, -self.front_track/2, self.rear_track/2, -self.rear_track/2],
        ])

    def target(self, ax, ay):
        return np.array([
            self.mass * G + self.downforce,
            -self.mass * ax * self.height
            + self.downforce * self.wheelbase * (self.aero_front_ratio - self.front_ratio),
            -self.mass * ay * self.height,
        ])

    def axle_loads(self, ax):
        transfer = self.mass * ax * self.height / self.wheelbase
        front = self.mass * G * self.front_ratio + self.downforce * self.aero_front_ratio - transfer
        rear = self.mass * G * (1-self.front_ratio) + self.downforce * (1-self.aero_front_ratio) + transfer
        return front, rear


def four_wheel_load_cg(car, ax, ay):
    front, rear = car.axle_loads(ax)
    moment = car.mass * ay * car.height
    front_transfer = moment * car.front_ratio / car.front_track
    rear_transfer = moment * (1-car.front_ratio) / car.rear_track
    return np.array([front/2-front_transfer, front/2+front_transfer,
                     rear/2-rear_transfer, rear/2+rear_transfer])


def four_wheel_load_lsm(car, ax, ay):
    """Minimum Euclidean norm solution of the three equilibrium constraints."""
    matrix = car.matrix
    return matrix.T @ np.linalg.solve(matrix @ matrix.T, car.target(ax, ay))


def wheel_load_null_direction(car):
    """Nonzero null basis with a fixed force scale, independent of the two solvers.

    The front/rear wheel-pair sums vanish and the lateral moments cancel.
    Scaling the largest entry to W/4 makes the coefficient dimensionless.
    """
    unit = np.array([1.0, -1.0, -car.front_track/car.rear_track,
                     car.front_track/car.rear_track])
    return (car.mass*G + car.downforce)/4 * unit/np.max(abs(unit))


def wheel_load_stiffness(car, ax, ay, heave_front, heave_rear, roll_front, roll_rear):
    # Rigid-body pitch equilibrium fixes equal front loss and rear gain.
    # Heave stiffness changes deflection, not the total axle transfer.
    if min(heave_front, heave_rear, roll_front, roll_rear) <= 0:
        raise ValueError("Heave and roll stiffness must be positive")
    front, rear = car.axle_loads(ax)
    moment = car.mass * ay * car.height
    ratio = roll_front / (roll_front + roll_rear)
    front_transfer = moment * ratio / car.front_track
    rear_transfer = moment * (1-ratio) / car.rear_track
    return np.array([front/2-front_transfer, front/2+front_transfer,
                     rear/2-rear_transfer, rear/2+rear_transfer])


def alpha_bounds(base, direction, tolerance=1e-10):
    """All alpha for which base + alpha*direction >= 0, including zero directions."""
    lower, upper = -np.inf, np.inf
    for load, slope in zip(base, direction):
        if abs(slope) <= tolerance:
            if load < -tolerance:
                return np.nan, np.nan, False
        elif slope > 0:
            lower = max(lower, -load/slope)
        else:
            upper = min(upper, -load/slope)
    return lower, upper, bool(lower <= upper + tolerance)
