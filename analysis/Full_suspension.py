"""Analysis entry point for the complete vehicle suspension."""

from pathlib import Path

from .full_suspension.workflow import METRICS, SCENARIOS, run

PLUGIN_ID = "full_suspension"
TITLE = "Full suspension"
DESCRIPTION = "完整懸吊模型：road_acc 與 road_FL_bump，輸出四輪響應、姿態與 Dashboard GIF。"
PARAMETERS = {
    # Values produced by the shared mass, tire, stiffness, damping, and RC analyses.
    **dict.fromkeys(("ms", "mu_front", "mu_rear",
                     "cog_front_axle_x_used_m", "cog_rear_axle_x_used_m", "cog_total_x_m",
                     "cog_total_Ixx_kg_m2", "cog_total_Iyy_kg_m2", "cog_total_Izz_kg_m2", "t", "hl_rear_track_m",
                     "h_cog", "Ks_pitch_N_per_m", "Ks_roll_N_per_m", "Kt", "MR",
                     "hl_rear_heave_spring_ratio", "hl_rear_roll_spring_ratio",
                     "hl_front_roll_center_m", "hl_rear_roll_center_m",
                     "damped_sweep_selected_ratio_used", "tender_to_heave_stiffness_ratio",
                     "tender_bind_total_stroke_mm"), "float"),
    # Shared input edited in Tender; use the same value without another field.
    "anti_geometry_ratio": "float",
    # Full-car model settings with no corresponding output in the upstream analyses.
    "full_body_twist_stiffness_Nm_per_rad": "float",
}
VISIBLE_PARAMETERS = {"MR", "hl_rear_heave_spring_ratio", "hl_rear_roll_spring_ratio",
                      "full_body_twist_stiffness_Nm_per_rad", "h_cog", "t", "hl_rear_track_m"}
PARAMETER_DEFAULTS = {
    "MR": 1.0,
    "hl_rear_track_m": 1.24,
    "hl_rear_heave_spring_ratio": 0.8,
    "hl_rear_roll_spring_ratio": 0.75,
    "full_body_twist_stiffness_Nm_per_rad": 180000.0,
}
HIDDEN_PARAMETERS = set(PARAMETERS) - VISIBLE_PARAMETERS
OUTPUTS = {"full_suspension_case_count": "完整懸吊工況數"}
OUTPUTS.update({f"full_suspension_{scenario}_{metric}": f"{scenario}｜{label}"
                for scenario in SCENARIOS for metric, label in METRICS.items()})
# Output-key parameter mapping lets the app run the upstream producers on demand.
REQUIRES = ()
INPUT_FILES = tuple(sorted((Path(__file__).parent / "full_suspension").rglob("*.py")))


def main(parameters):
    return run(parameters)
