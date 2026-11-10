"""Export suspension dynamics, geometry and vehicle parameters from one sizing result."""

import json
import math
from pathlib import Path


def load_template():
    path = Path(__file__).with_name("dynamics_template.json")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def frame_parameters(snapshot):
    return {
        "m_frame": snapshot["frequency_mass"]["quarter_sprung_mass_kg"],
        "k_frame": 10 * snapshot["selected_stiffness"]["roll"]["stiffness_N_per_m"],
    }


def damping_coefficients(snapshot):
    p = snapshot["parameters"]
    zeta = p["zeta"]
    damping = snapshot["damping"]
    coefficients = {}
    for end, axle in (("f", "front"), ("r", "rear")):
        # The heave channel uses the sum of the two wheel displacements.
        coefficients[f"heave_{end}_c"] = zeta * damping["pure_heave"][axle]["damper_critical_damping_Ns_per_m"] / 4
        coefficients[f"roll_{end}_c"] = zeta * damping["roll"][axle]["damper_critical_damping_Ns_per_m"]
    coefficients["tire_c"] = 2 * zeta * math.sqrt(p["Kt"] * p["mu"])
    return coefficients


def build_dynamics_export(snapshot, name):
    full = load_template()
    full.update(frame_parameters(snapshot))
    damping = damping_coefficients(snapshot)
    p = snapshot["parameters"]
    anti = snapshot["anti"]["heave_only"]
    mr = p["MR"]
    full.update(
        m=p["ms"] + 4 * p["mu"], mu_f=p["mu"], mu_r=p["mu"],
        lf=p["lf"], lr=p["lr"], tf=p["tf"], tr=p["tr"], h_cg=p["h_cog"],
        Ixx=p["sprung_roll_inertia_kg_m2"],
        h_rc_f=snapshot["front_rc"]["rc_normalized_optimal_height_m"],
        h_rc_r=snapshot["rear_rc_height_m"],
        brake_front=snapshot["brake"]["brake_ideal_front_ratio"], drive_front=0.5,
        anti_front=anti["front_anti_ratio"], anti_rear=anti["rear_anti_ratio"],
        zeta=p["zeta"],
    )

    def channel(prefix, stiffness, damping, ratio):
        full.update({f"{prefix}_k": stiffness, f"{prefix}_c": damping, f"{prefix}_mr": ratio})

    for end, axle in (("f", "front"), ("r", "rear")):
        heave = snapshot["damping"]["pure_heave"][axle]
        roll = snapshot["damping"]["roll"][axle]
        channel(f"heave_{end}", heave["spring_stiffness_N_per_m"] / 4, damping[f"heave_{end}_c"], mr)
        channel(f"roll_{end}", roll["spring_stiffness_N_per_m"], damping[f"roll_{end}_c"], mr)
        channel(f"corner_{end}", 0, 0, 1)
        channel(f"tire_{end}", p["Kt"], damping["tire_c"], 1)
    channel("roll_c", 0, 0, 1)

    tender = snapshot["tender"]
    full.update(
        tender_enabled=p["use_tender"],
        tender_stiffness_N_per_m=tender["K_tender_required_N_per_m"] if tender is not None else None,
        heave_configuration="main_spring",
    )
    fvsa = snapshot["fvsa"]["前軸"]["fvsa_length_m"]
    steer = p["steering_angle_deg"]
    travel_mm = 1000 * p["sus_travel"]
    vehicle = {key: full.pop(key) for key in (
        "m", "lf", "lr", "tf", "tr", "h_cg", "Ixx", "Iyy", "mu_f", "mu_r", "drive_front", "brake_front",
    )}
    vehicle.update(gravity=p["g"], free_radius=p["R_tire"])
    geometry = {
        "h_rc_f": full.pop("h_rc_f"), "h_rc_r": full.pop("h_rc_r"),
        "clearance_steer_deg": steer,
        "fvsa_f": fvsa, "kpi_f_deg": p["kpi_deg"], "caster_f_deg": snapshot["caster"]["caster_deg"],
        "fvsa_r": fvsa, "kpi_r_deg": p["kpi_deg"], "caster_r_deg": 0.0,
        "bump_mm": travel_mm, "droop_mm": travel_mm, "steer_deg": steer,
    }
    return {
        "application": "VehicleInitialSizingLab-DynamicsExport",
        "schema_version": 2,
        "name": name,
        "dynamics": full,
        "geometry": geometry,
        "vehicle": vehicle,
    }
