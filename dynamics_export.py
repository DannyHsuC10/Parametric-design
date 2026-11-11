"""Export suspension dynamics, geometry and vehicle parameters from one sizing result."""

import json
import math
from pathlib import Path

from project import FIELDS, default_project, project_document, project_parameters, validate_inputs


DYNAMICS_FORMAT = "VehicleInitialSizingLab-DynamicsExport"
DYNAMICS_VERSION = 3
LEGACY_DYNAMICS_ERROR = "舊版 Dynamics JSON 的車輛或懸吊參數不完整或無效。"


def dynamics_project_parameters(document):
    version = document.get("schema_version")
    if type(version) is not int or version not in (2, DYNAMICS_VERSION):
        raise ValueError("請選擇版本 2 或 3 的 Dynamics JSON。")
    if "source_project" in document:
        return project_parameters(document["source_project"]), False
    return _legacy_dynamics_parameters(document), True


def _legacy_dynamics_parameters(document):
    vehicle = document.get("vehicle")
    geometry = document.get("geometry")
    dynamics = document.get("dynamics")
    if not all(isinstance(section, dict) for section in (vehicle, geometry, dynamics)):
        raise ValueError(LEGACY_DYNAMICS_ERROR)

    mass, mu_front, mu_rear = (vehicle.get(key) for key in ("m", "mu_f", "mu_r"))
    bump_mm, steer_deg, front_rc = (geometry.get(key) for key in ("bump_mm", "steer_deg", "h_rc_f"))
    h_cog, lf, lr = (vehicle.get(key) for key in ("h_cg", "lf", "lr"))
    if not all(type(value) in (int, float) and math.isfinite(value)
               for value in (mass, mu_front, mu_rear, bump_mm, steer_deg, front_rc, h_cog, lf, lr)):
        raise ValueError(LEGACY_DYNAMICS_ERROR)
    if mu_front != mu_rear or not 0 < steer_deg < 90 or not 0 < front_rc < h_cog:
        raise ValueError(LEGACY_DYNAMICS_ERROR)

    recovered = {
        "ms": mass - 4 * mu_front,
        "mu": mu_front,
        "h_cog": h_cog,
        "lf": lf,
        "lr": lr,
        "tf": vehicle.get("tf"),
        "tr": vehicle.get("tr"),
        "sprung_roll_inertia_kg_m2": vehicle.get("Ixx"),
        "R_tire": vehicle.get("free_radius"),
        "sus_travel": bump_mm / 1000,
        "min_turn_radius_m": (lf + lr) / math.tan(math.radians(steer_deg)),
        "kpi_deg": geometry.get("kpi_f_deg"),
        "rc_chassis_stiffness_ratio": h_cog / front_rc - 1,
        "use_tender": dynamics.get("tender_enabled"),
        "MR": dynamics.get("heave_f_mr"),
        "zeta": dynamics.get("zeta"),
        "Kt": dynamics.get("tire_f_k"),
    }
    return validate_inputs(default_project() | recovered)


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
        # Export damping in the dynamics model's two-wheel sum coordinate.
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
        channel(f"heave_{end}", heave["spring_stiffness_N_per_m"], damping[f"heave_{end}_c"], mr)
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
        "m", "lf", "lr", "tf", "tr", "h_cg", "Ixx", "mu_f", "mu_r", "drive_front", "brake_front",
    )}
    if "Iyy" in full:
        vehicle["Iyy"] = full.pop("Iyy")
    vehicle.update(gravity=p["g"], free_radius=p["R_tire"])
    geometry = {
        "h_rc_f": full.pop("h_rc_f"), "h_rc_r": full.pop("h_rc_r"),
        "clearance_steer_deg": steer,
        "fvsa_f": fvsa, "kpi_f_deg": p["kpi_deg"], "caster_f_deg": snapshot["caster"]["caster_deg"],
        "fvsa_r": fvsa, "kpi_r_deg": p["kpi_deg"], "caster_r_deg": 0.0,
        "bump_mm": travel_mm, "droop_mm": travel_mm, "steer_deg": steer,
    }
    return {
        "application": DYNAMICS_FORMAT,
        "schema_version": DYNAMICS_VERSION,
        "name": name,
        "dynamics": full,
        "geometry": geometry,
        "vehicle": vehicle,
        "source_project": project_document({key: p[key] for key in FIELDS}),
    }
