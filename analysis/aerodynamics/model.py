"""Modal aero equations migrated from new/Aero.py, with angles in radians."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ModalAeroModel:
    rho: float = 1.225
    area: float = 1.2
    CL0: float = -2.4
    Kh: float = -5.0
    Kp: float = 0.2
    Kr: float = 0.0
    Khh: float = 50.0
    Kpp: float = 30.0
    Krr: float = 8.0
    CD0: float = 1.8
    Kd_h: float = 0.0
    Kd_p: float = 0.0
    Kd_r: float = 0.0
    front_balance: float = 0.45
    K_balance_pitch: float = 0.20
    K_balance_roll: float = 0.10
    wheelbase: float = 1.55
    track: float = 1.25

    def calculate_from_modal(self, V, qh, qp, qr):
        """Evaluate scalars or arrays: speed m/s, heave m, pitch/roll rad.

        CL < 0 produces positive downward force. CoP is relative to the
        wheelbase/track midpoint, with x forward and y left. At zero net
        downforce CoP is undefined; zero is returned, as in the source model.
        """
        speed, heave, pitch, roll = np.broadcast_arrays(
            *[np.asarray(value, dtype=float) for value in (V, qh, qp, qr)]
        )
        cl = (self.CL0 + self.Kh * np.abs(heave) + self.Kp * np.abs(pitch)
              + self.Kr * np.abs(roll) + self.Khh * heave**2
              + self.Kpp * pitch**2 + self.Krr * roll**2)
        cd = self.CD0 + self.Kd_h * np.abs(heave) + self.Kd_p * np.abs(pitch) + self.Kd_r * np.abs(roll)
        dynamic_force = 0.5 * self.rho * self.area * speed**2
        downforce, drag = -dynamic_force * cl, dynamic_force * cd
        front_ratio = self.front_balance + self.K_balance_pitch * pitch
        left_ratio = 0.5 + self.K_balance_roll * roll
        return {
            "F_down": downforce, "F_drag": drag, "CL": cl, "CD": cd,
            "F_FL": downforce * front_ratio * left_ratio,
            "F_FR": downforce * front_ratio * (1 - left_ratio),
            "F_RL": downforce * (1 - front_ratio) * left_ratio,
            "F_RR": downforce * (1 - front_ratio) * (1 - left_ratio),
            "COP_x": np.where(downforce != 0, self.wheelbase * (front_ratio - 0.5), 0.0),
            "COP_y": np.where(downforce != 0, self.track * (left_ratio - 0.5), 0.0),
            "qh": heave, "qp": pitch, "qr": roll,
        }
