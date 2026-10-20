"""Estimate lift coefficient and downforce from the skidpad reference point."""

TITLE = "Aero CL CD"
DESCRIPTION = "Estimate lift coefficient from a reference downforce, speed, and area."
PLUGIN_ID = "aero_cl_cd"
PARAMETERS = {
    "F_ref": "float",
    "v_ref": "float",
    "A_air": "float",
}
HIDDEN_PARAMETERS = {"F_ref", "v_ref"}
OUTPUTS = {
    "Cl": "Estimated lift coefficient from the aerodynamic reference point",
    "aero_cl_cd_F_ref_N": "Reference downforce passed through to the tender analysis (N)",
}

import matplotlib.pyplot as plt
import numpy as np


def main(parameters):
    reference_force = parameters["F_ref"]
    reference_speed_kmh = parameters["v_ref"]
    reference_area = parameters["A_air"]
    air_density = 1.225
    reference_speed = reference_speed_kmh / 3.6
    if reference_area <= 0:
        raise ValueError("A_air must be greater than zero")
    if reference_speed <= 0:
        raise ValueError("v_ref must be greater than zero")

    lift_coefficient = reference_force / (
        0.5 * air_density * reference_area * reference_speed**2
    )
    print(f"Reference Lift Coefficient Cl = {lift_coefficient:.3f}")

    speed_kmh = np.linspace(0, 100, 201)
    speed = speed_kmh / 3.6
    downforce = 0.5 * lift_coefficient * air_density * reference_area * speed**2

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(speed_kmh, downforce, linewidth=2, label="Downforce")
    axis.scatter(
        [reference_speed_kmh],
        [reference_force],
        color="red",
        zorder=5,
        label=f"Reference Point\n{reference_force:.1f} N\n{reference_speed_kmh:.1f} km/h",
    )
    axis.set_xlabel("Vehicle Speed (km/h)")
    axis.set_ylabel("Downforce (N)")
    axis.set_title("Downforce vs Vehicle Speed")
    axis.grid(True)
    axis.legend()
    figure.tight_layout()
    return figure, {
        "Cl": float(lift_coefficient),
        "aero_cl_cd_F_ref_N": float(reference_force),
    }
