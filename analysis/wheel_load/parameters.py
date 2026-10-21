"""CSV inputs shared with the existing suspension workflow."""

DEFAULTS = {
    "wl_downforce_N": 0.0,
    "wl_aero_front_ratio": 0.5,
    "wl_mu_y": 1.7,
    "wl_grid_points": 81,
}
STAGES = ("FWL", "solver_compar", "sus_load", "max_load")
TITLES = ("FWL 四輪載重包絡", "solver_compar 求解器與零空間比較",
          "sus_load 懸吊剛性輪載", "max_load 輪胎力上限")
BASE = dict.fromkeys(("ms", "mu", "h_cog", "L", "t", "hl_rear_track_m",
                      "hl_front_weight_ratio", "ax", "ay",
                      "wl_downforce_N", "wl_aero_front_ratio"), "float")
STIFFNESS = dict.fromkeys(("Ks_pitch_N_per_m", "Ks_roll_N_per_m", "MR",
                          "hl_rear_heave_spring_ratio", "hl_rear_roll_spring_ratio",
                          "hl_front_roll_motion_ratio", "hl_rear_roll_motion_ratio"), "float")


def plugin_metadata(stage):
    parameters = dict(BASE, wl_grid_points="int")
    hidden = set()
    if stage == "FWL":
        names = ("min_N", "max_N", "unloaded_fraction", "max_equilibrium_error")
    elif stage == "solver_compar":
        names = ("max_difference_N", "max_null_residual", "feasible_fraction")
    elif stage == "sus_load":
        parameters.update(STIFFNESS)
        hidden = {"Ks_pitch_N_per_m", "Ks_roll_N_per_m"}
        names = ("min_N", "max_N", "front_roll_fraction", "pitch_deg", "max_equilibrium_error",
                 "FL_N", "FR_N", "RL_N", "RR_N")
    else:
        parameters = {f"wl_sus_load_{wheel}_N": "float" for wheel in ("FL", "FR", "RL", "RR")}
        hidden = set(parameters)
        parameters.update(mu_w="float", wl_mu_y="float")
        names = ("max_Fz_N", "max_Fx_N", "max_Fy_N", "unloaded_count", "contact_valid")
    index = STAGES.index(stage)
    return {
        "PLUGIN_ID": "fwl" if stage == "FWL" else stage,
        "TITLE": TITLES[index], "DESCRIPTION": "輪載與輪胎力分析",
        "PARAMETERS": parameters, "PARAMETER_DEFAULTS": DEFAULTS,
        "HIDDEN_PARAMETERS": hidden,
        "REQUIRES": STAGES[index-1:index] if index else (),
        "OUTPUTS": {f"wl_{stage}_{name}": name for name in names},
    }
