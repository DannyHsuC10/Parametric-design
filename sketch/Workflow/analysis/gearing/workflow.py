"""Reusable analysis stages for the planetary gear train workflow."""

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from app.analysis_result import AnalysisResult

G = 9.81
DEFAULTS = {
    "drive_target_speed_kmh": 80.0,
    "drive_motor_rpm": 6000.0,
    "acc_g": 1.2,
    "drive_gear_efficiency": 0.9,
    "drive_wheel_inertia_kg_m2": 0.1,
    "drive_start_torque_Nm": 10.0,
    "drive_rolling_resistance": 0.015,
    "drive_start_resistance": 0.02,
    "drive_vehicle_height_m": 0.6,
    "drive_vehicle_width_m": 1.2,
    "drive_drag_coefficient": 0.9,
    "drive_slope_deg": 10.0,
    "gear_module_mm": 1.5,
    "gearbox_max_diameter_mm": 180.0,
    "gear_planet_count": 3,
    "gear_shaft_diameter_mm": 10.0,
    "gear_sun_width_mm": 10.0,
    "gear_planet_width_mm": 10.0,
    "gear_density_kg_m3": 7870.0,
    "gear_material_strength_MPa": 560.0,
    "gear_safety_factor": 5.0,
    "gear_min_teeth": 20,
    "gear_sun_teeth": 21,
    "gear_planet1_teeth": 45,
    "gear_planet2_teeth": 24,
    "gear_ring_teeth": 90,
}

VEHICLE = {"cog_total_mass_kg": "float", "L": "float", "h_cog": "float",
           "hl_front_weight_ratio": "float", "mu_w": "float", "R_tire": "float"}
PARAMETERS_BY_STAGE = {
    "acc_load": dict(VEHICLE),
    "gear_rate": {**{key: value for key, value in VEHICLE.items() if key != "mu_w"}, "acc_g": "float",
                   "drive_target_speed_kmh": "float",
                   "drive_motor_torque_Nm": "float", "drive_motor_rpm": "float"},
    "gear_tooth": {"gear_module_mm": "float", "gear_ratio_avg": "float",
                   "gearbox_max_diameter_mm": "float", "gear_min_teeth": "int"},
    "number_of_gear": {"gear_module_mm": "float", "gear_sun_teeth": "int",
                        "gear_planet1_teeth": "int", "gear_planet2_teeth": "int",
                        "gear_ring_teeth": "int", "gear_planet_count": "int"},
    "output_check": {"gear_sun_teeth": "int", "gear_planet1_teeth": "int",
                      "gear_planet2_teeth": "int", "gear_ring_teeth": "int",
                      "drive_motor_torque_Nm": "float", "drive_motor_rpm": "float",
                      "drive_gear_efficiency": "float",
                      **VEHICLE},
    "rotational_inertia": {"gear_module_mm": "float", "gear_sun_teeth": "int",
                           "gear_planet1_teeth": "int", "gear_planet2_teeth": "int",
                           "gear_ring_teeth": "int", "gear_planet_count": "int",
                           "gear_shaft_diameter_mm": "float", "gear_sun_width_mm": "float",
                           "gear_planet_width_mm": "float", "gear_density_kg_m3": "float"},
    "acc_resis": {**VEHICLE, "drive_target_speed_kmh": "float",
                  "drive_wheel_inertia_kg_m2": "float",
                  "drive_start_torque_Nm": "float", "drive_rolling_resistance": "float",
                  "drive_start_resistance": "float", "drive_slope_deg": "float",
                  "drive_vehicle_height_m": "float", "drive_vehicle_width_m": "float",
                  "drive_drag_coefficient": "float", "drive_gear_efficiency": "float",
                  "drive_motor_torque_Nm": "float"},
    "tooth_strength": {"gear_ratio_avg": "float", "drive_motor_torque_Nm": "float",
                       "gear_sun_width_mm": "float", "gear_module_mm": "float",
                       "gear_material_strength_MPa": "float", "gear_safety_factor": "float",
                       "gear_min_teeth": "int"},
}
TITLE = {
    "acc_load": "Acc_load", "gear_rate": "Gear_rate", "gear_tooth": "Gear_tooth",
    "number_of_gear": "Number_of_Gear", "output_check": "Output_check",
    "rotational_inertia": "Rotational_inertia", "acc_resis": "acc_resis",
    "tooth_strength": "tooth_Strength",
}
OUTPUTS = {
    "acc_load": ("drive_acc_load_front_max_N", "drive_acc_load_rear_max_N", "drive_accel_limit_m_s2"),
    "gear_rate": ("gear_ratio_accel", "gear_ratio_top_speed", "gear_ratio_avg", "gear_rate_target_speed_kmh",
                  "gear_rate_acceleration_g"),
    "gear_tooth": ("gear_selected_sun_teeth", "gear_selected_ring_teeth", "gear_selected_planet1_teeth",
                   "gear_selected_planet2_teeth", "gear_selected_ratio", "gear_candidate_count"),
    "number_of_gear": ("gear_planet_interference_angle_rad", "gear_planet_limit_angle_rad", "gear_planet_count_check"),
    "output_check": ("gear_output_ratio", "gear_output_torque_Nm", "gear_output_max_speed_kmh",
                     "gear_output_final_speed_kmh", "gear_output_distance_m"),
    "rotational_inertia": ("gear_rotational_inertia_planet_kg_m2", "gear_rotational_inertia_sun_kg_m2",
                           "gear_rotational_inertia_total_kg_m2"),
    "acc_resis": ("gear_resistance_total_N", "gear_resistance_starting_torque_Nm", "gear_resistance_ratio_min"),
    "tooth_strength": ("gear_strength_transition_teeth", "gear_strength_module_required_min_mm"),
}
REQUIRES = {
    "acc_load": ("max_load",), "gear_rate": ("acc_load", "motor"), "gear_tooth": ("gear_rate",),
    "number_of_gear": ("gear_tooth",), "output_check": ("number_of_gear",),
    "rotational_inertia": ("number_of_gear",), "acc_resis": ("gear_rate",),
    "tooth_strength": ("gear_tooth",),
}


def metadata(stage):
    return {
        "TITLE": TITLE[stage], "DESCRIPTION": "行星齒輪與縱向性能分析",
        "PLUGIN_ID": stage, "PARAMETERS": PARAMETERS_BY_STAGE[stage],
        "PARAMETER_DEFAULTS": DEFAULTS, "REQUIRES": REQUIRES[stage],
        "HIDDEN_PARAMETERS": ({"cog_total_mass_kg", "gear_ratio_avg"}
                               if stage in {"gear_tooth", "tooth_strength"}
                               else {"cog_total_mass_kg"})
                              | ({"drive_motor_torque_Nm"} if stage in {"gear_rate", "tooth_strength"} else set()),
        "OUTPUTS": {name: name for name in OUTPUTS[stage]},
    }


def _figure(title, xlabel, ylabel, series):
    fig, ax = plt.subplots(figsize=(8, 5))
    for x, y, label, style in series:
        ax.plot(x, y, style, linewidth=2, label=label)
    ax.set(title=title, xlabel=xlabel, ylabel=ylabel)
    ax.grid(True, alpha=0.3)
    if len(series) > 1:
        ax.legend()
    fig.tight_layout()
    return fig


def run(stage, p):
    if stage in {"acc_load", "gear_rate", "output_check", "acc_resis"}:
        m = p["cog_total_mass_kg"]
        L = p["L"]
        lf = L * p["hl_front_weight_ratio"]
        hcg = p["h_cog"]
        mu = p.get("mu_w")
    outputs = {}
    tables = {}

    if stage == "acc_load":
        a = np.linspace(0, mu * G, 100)
        nr = (m * a * hcg + m * G * lf) / L
        nf = m * G - nr
        outputs = {"drive_acc_load_front_max_N": float(nf.max()), "drive_acc_load_rear_max_N": float(nr.max()),
                   "drive_accel_limit_m_s2": float(mu * G)}
        fig = _figure("Normal Load vs Acceleration", "Longitudinal acceleration (g)", "Normal load (N)",
                      [(a/G, nf, "Front", "-"), (a/G, nr, "Rear", "-")])
        tables["acc_load.csv"] = pd.DataFrame({"acceleration_m_s2": a, "front_load_N": nf, "rear_load_N": nr})

    elif stage == "gear_rate":
        rw = p.get("R_tire", 0.2)
        target = p["drive_target_speed_kmh"]
        tmax, rpmmax = p["drive_motor_torque_Nm"], p["drive_motor_rpm"]
        amax = p["acc_g"] * G
        if amax <= 0:
            raise ValueError("acc_g 必須大於 0")
        nr = (m * amax * hcg + m * G * lf) / L
        nf = m * G - nr
        if nf <= 0 or nr <= 0:
            raise ValueError("此 acc_g 會造成前／後軸法向載荷歸零，請調低加速度")
        total_force = m * amax
        front_force = total_force * nf / (m * G)
        rear_force = total_force * nr / (m * G)
        wheel_torque = max(front_force * rw / 2, rear_force * rw / 2)
        z_acc = wheel_torque / tmax
        wheel_rpm = (target/3.6/rw) * 60/(2*np.pi)
        z_speed = rpmmax / wheel_rpm
        z_avg = (z_acc + z_speed) / 2
        speed = np.linspace(0, target*1.1, 150)
        rpm_w = (speed/3.6/rw) * 60/(2*np.pi)
        outputs = {"gear_ratio_accel": float(z_acc), "gear_ratio_top_speed": float(z_speed),
                   "gear_ratio_avg": float(z_avg), "gear_rate_target_speed_kmh": float(target),
                   "gear_rate_acceleration_g": float(p["acc_g"])}
        fig = _figure("Motor RPM vs Vehicle Speed", "Vehicle speed (km/h)", "Motor speed (RPM)",
                      [(speed, rpm_w*z_acc, f"Acceleration ratio {z_acc:.2f}", "-"),
                       (speed, rpm_w*z_speed, f"Top-speed ratio {z_speed:.2f}", "-"),
                       (speed, rpm_w*z_avg, f"Average ratio {z_avg:.2f}", "-"),
                       (speed, np.full_like(speed, rpmmax), "Motor maximum", "--")])
        tables["gear_rate.csv"] = pd.DataFrame({"speed_kmh": speed, "motor_rpm_accel_ratio": rpm_w*z_acc,
                                                 "motor_rpm_top_speed_ratio": rpm_w*z_speed,
                                                 "motor_rpm_average_ratio": rpm_w*z_avg})

    elif stage == "gear_tooth":
        module, desired = p["gear_module_mm"], p["gear_ratio_avg"]
        total = math.floor(p["gearbox_max_diameter_mm"] / module)
        tmin = p["gear_min_teeth"]
        candidates = []
        # Geometry fixes Tp2 = Tr - Ts - Tp1, keeping the exhaustive search practical.
        for ts in range(tmin, max(tmin, total-2*tmin)+1):
            for tp1 in range(tmin, max(tmin, (total-tmin)//2)+1):
                for tr in range(3*tmin, total+1):
                    tp2 = tr-ts-tp1
                    if tp2 < tmin or tp2 > (total-tmin)//2 or 2*tp1+ts > total:
                        continue
                    common = math.gcd(tp1, tp2)
                    if common == 1 or (ts*tp2-tr*tp1) % (3*common):
                        continue
                    ratio = (tp1/ts)*(tr/tp2)
                    if ratio > desired:
                        candidates.append((ts, tr, tp1, tp2, ratio))
        candidates.sort(key=lambda row: row[-1])
        if not candidates:
            raise ValueError("找不到符合齒數限制與目標齒比的組合，請調整模數、齒輪箱直徑或目標齒比。")
        df = pd.DataFrame(candidates, columns=["T_s", "T_r", "T_p1", "T_p2", "ratio"])
        best = min(candidates, key=lambda row: abs(row[-1]-desired))
        outputs = {"gear_selected_sun_teeth": int(best[0]), "gear_selected_ring_teeth": int(best[1]),
                   "gear_selected_planet1_teeth": int(best[2]), "gear_selected_planet2_teeth": int(best[3]),
                   "gear_selected_ratio": float(best[4]), "gear_candidate_count": len(candidates)}
        fig_height = max(7.0, 3.5 + 0.28 * len(df))
        fig, ax = plt.subplots(figsize=(12, fig_height))
        ax.axis("off")
        ax.set_title("Planetary Gear Tooth Combination Search", fontsize=16, fontweight="bold", pad=18)
        ax.text(.05, .91,
                f"Total combinations searched: {total:,}\n"
                f"Valid combinations: {len(df):,}\n"
                f"Module: {module:g} mm    Minimum teeth: {tmin}    Max diameter: {p['gearbox_max_diameter_mm']:g} mm\n"
                f"Target ratio: {desired:g}",
                transform=ax.transAxes, va="top", family="monospace", fontsize=11)
        display_df = df.copy()
        display_df["ratio"] = display_df["ratio"].round(3)
        table = ax.table(cellText=display_df.values, colLabels=display_df.columns,
                         cellLoc="center", bbox=[.06, .03, .88, .70])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        ratio_fig, ratio_ax = plt.subplots(figsize=(8, 5))
        ratio_ax.hist(df["ratio"], bins=min(20, max(5, len(df))), color="#586b7a", edgecolor="white")
        ratio_ax.axvline(desired, color="crimson", linestyle="--", linewidth=1.5, label=f"Target ratio {desired:g}")
        ratio_ax.set(title="Feasible Gear Ratio Distribution", xlabel="Overall gear ratio", ylabel="Combination count")
        ratio_ax.grid(axis="y", alpha=.25)
        ratio_ax.legend()
        ratio_fig.tight_layout()

        teeth_fig, teeth_ax = plt.subplots(figsize=(8, 5))
        points = teeth_ax.scatter(df["T_s"], df["T_r"], c=df["ratio"], cmap="viridis", s=55, edgecolors="white")
        teeth_ax.set(title="Feasible Tooth Combination Distribution", xlabel="Sun gear teeth (T_s)", ylabel="Ring gear teeth (T_r)")
        teeth_ax.grid(True, alpha=.25)
        teeth_fig.colorbar(points, ax=teeth_ax, label="Overall gear ratio")
        teeth_fig.tight_layout()
        figures = {"gear_ratio_distribution.png": ratio_fig,
                   "gear_tooth_distribution.png": teeth_fig}
        tables["gear_tooth_candidates.csv"] = df

    elif stage == "number_of_gear":
        module, ts, tp, n = p["gear_module_mm"], int(p["gear_sun_teeth"]), int(p["gear_planet1_teeth"]), p["gear_planet_count"]
        theta = 2*np.arcsin(np.clip((tp*module+2*module)/(tp*module+ts*module), -1, 1))
        limit, next_limit = 2*np.pi/n, 2*np.pi/(n+1)
        if theta > limit:
            result = "幾何干涉，需減少行星齒輪數量"
        elif theta > next_limit:
            result = "目前配置接近數量極限"
        else:
            result = "無幾何干涉，可評估增加行星齒輪"
        outputs = {"gear_planet_interference_angle_rad": float(theta), "gear_planet_limit_angle_rad": float(limit),
                   "gear_planet_count_check": result}
        fig, ax = plt.subplots(figsize=(8, 4)); ax.barh(["Current", "Current limit", "n+1 limit"], [theta, limit, next_limit])
        ax.set(xlabel="Angle (rad)", title="Planetary Gear Number Check"); ax.grid(axis="x", alpha=.3); fig.tight_layout()
        tables["number_of_gear.csv"] = pd.DataFrame({"quantity": ["calculated", "n limit", "n+1 limit"], "angle_rad": [theta, limit, next_limit]})

    elif stage == "output_check":
        ts, tp1, tp2, tr = (p[k] for k in ("gear_sun_teeth", "gear_planet1_teeth", "gear_planet2_teeth", "gear_ring_teeth"))
        z = (tp1/ts)*(tr/tp2); rw=p["R_tire"]
        tout=p["drive_motor_torque_Nm"]*z*p["drive_gear_efficiency"]
        v_max=(2*np.pi*rw*p["drive_motor_rpm"]/z)*3.6/60
        faxle=2*tout/rw
        dt=.1; time=np.arange(0,10,dt); accel=np.zeros_like(time); speed=np.zeros_like(time); dist=np.zeros_like(time)
        vel=pos=acc=0.0
        for i in range(len(time)):
            nr=(m*acc*hcg+m*G*lf)/L; nf=m*G-nr
            force=min(faxle, max(0,nr*mu))+min(faxle, max(0,nf*mu))
            acc=force/m; vel=min(vel+acc*dt, v_max/3.6); pos+=vel*dt
            accel[i]=acc/G; speed[i]=vel*3.6; dist[i]=pos
        outputs={"gear_output_ratio":float(z),"gear_output_torque_Nm":float(tout),"gear_output_max_speed_kmh":float(v_max),
                 "gear_output_final_speed_kmh":float(speed[-1]),"gear_output_distance_m":float(dist[-1])}
        fig,axes=plt.subplots(3,1,figsize=(8,8),sharex=True)
        for ax,y,label in zip(axes,(dist,speed,accel),("Position (m)","Velocity (km/h)","Acceleration (g)")):
            ax.plot(time,y,linewidth=2);ax.set_ylabel(label);ax.grid(True,alpha=.3)
        axes[-1].set_xlabel("Time (s)");fig.suptitle("Acceleration Simulation");fig.tight_layout()
        tables["output_check.csv"]=pd.DataFrame({"time_s":time,"position_m":dist,"speed_kmh":speed,"acceleration_g":accel})

    elif stage == "rotational_inertia":
        density=p["gear_density_kg_m3"]; module=p["gear_module_mm"]; shaft=p["gear_shaft_diameter_mm"]
        teeth=[p["gear_sun_teeth"],p["gear_planet1_teeth"],p["gear_planet2_teeth"]]
        widths=[p["gear_sun_width_mm"],p["gear_planet_width_mm"],p["gear_planet_width_mm"]]
        vals=[]
        for t,w in zip(teeth,widths):
            ro=t*module/2000; ri=(shaft/2000 if t==teeth[0] else shaft/2000)
            vals.append(.5*density*np.pi*(ro**2-ri**2)*(w/1000)*(ro**2+ri**2))
        z2=p["gear_ring_teeth"]/p["gear_planet2_teeth"]; z=p["gear_planet1_teeth"]*z2/p["gear_sun_teeth"]
        ip=z2**2*(vals[1]+vals[2]); ins=z**2*vals[0]; total=ip*p["gear_planet_count"]+ins
        outputs={"gear_rotational_inertia_planet_kg_m2":float(ip),"gear_rotational_inertia_sun_kg_m2":float(ins),
                 "gear_rotational_inertia_total_kg_m2":float(total)}
        fig,ax=plt.subplots(figsize=(8,4));ax.axis("off");ax.text(.5,.5,"Equivalent Rotational Inertia\n\n"+"\n".join(f"Gear {i+1}: {v:.5e} kg·m²" for i,v in enumerate(vals))+f"\n\nPlanet: {ip:.5e} kg·m²\nSun: {ins:.5e} kg·m²\nTotal: {total:.5e} kg·m²",ha="center",va="center",family="monospace");fig.tight_layout()
        tables["rotational_inertia.csv"]=pd.DataFrame({"gear":["sun","planet1","planet2"],"inertia_kg_m2":vals})

    elif stage == "acc_resis":
        rw=p["R_tire"]; v=p["drive_target_speed_kmh"]/3.6; a=mu*G
        fin=p["drive_wheel_inertia_kg_m2"]*a/rw**2; fstart=p["drive_start_torque_Nm"]/rw
        frr=p["drive_rolling_resistance"]*m*G; fbody=m*G*p["drive_start_resistance"]
        slope=m*G*np.sin(np.deg2rad(p["drive_slope_deg"]))
        area=p["drive_vehicle_height_m"]*p["drive_vehicle_width_m"]
        fair=.5*p["drive_drag_coefficient"]*1.225*area*v**2+6*np.pi*np.hypot(p["drive_vehicle_height_m"],p["drive_vehicle_width_m"])*1.81e-5*v
        body=fbody+slope+fair; wheel=frr+fstart+fin; total=(body/4+wheel)/p["drive_gear_efficiency"]
        torque=total*rw; ratio=1.1*torque/p["drive_motor_torque_Nm"]
        items=[("Inertial force",fin,"N"),("Drivetrain start resistance",fstart,"N"),("Rolling resistance",frr,"N"),("Vehicle start resistance",fbody,"N"),("Grade resistance",slope,"N"),("Aerodynamic resistance",fair,"N"),("Body resistance",body,"N"),("Wheel resistance",wheel,"N"),("Total resistance",total,"N"),("Starting torque",torque,"N·m"),("Minimum gear ratio",ratio,"-")]
        outputs={"gear_resistance_total_N":float(total),"gear_resistance_starting_torque_Nm":float(torque),"gear_resistance_ratio_min":float(ratio)}
        fig,ax=plt.subplots(figsize=(9,5));ax.axis("off");ax.table(cellText=[[n,f"{v:.2f} {u}"] for n,v,u in items],colLabels=["Quantity","Value"],loc="center",cellLoc="center").scale(1,1.5);ax.set_title("Vehicle Resistance Calculation");fig.tight_layout()
        tables["acc_resis.csv"]=pd.DataFrame(items,columns=["quantity","value","unit"])

    else:  # tooth_strength
        teeth=np.arange(p["gear_min_teeth"],101); tau=p["gear_material_strength_MPa"]; width=p["gear_sun_width_mm"]
        required=np.sqrt(6*p["drive_motor_torque_Nm"]*p["gear_ratio_avg"]*p["gear_safety_factor"]/(teeth*np.pi*width*tau))
        chosen=np.maximum(required,p["gear_module_mm"]); knee=int(teeth[np.flatnonzero(required<=p["gear_module_mm"])[0]]) if np.any(required<=p["gear_module_mm"]) else int(teeth[-1])
        outputs={"gear_strength_transition_teeth":knee,"gear_strength_module_required_min_mm":float(required.min())}
        fig=_figure("Gear Module vs Sun Gear Tooth Number","Number of teeth","Module (mm)",[(teeth,required,"Strength required","-"),(teeth,np.full_like(teeth,p["gear_module_mm"],dtype=float),"Manufacturing minimum","-"),(teeth,chosen,"Selected module","--")])
        tables["tooth_strength.csv"]=pd.DataFrame({"teeth":teeth,"strength_module_mm":required,"selected_module_mm":chosen})

    for name, value in outputs.items():
        print(f"{name}: {value!r}".encode("ascii", "backslashreplace").decode("ascii"))
    titles = {"plot.png": TITLE[stage]}
    if stage == "gear_tooth":
        titles.update({"gear_ratio_distribution.png": "可行解齒比分布",
                       "gear_tooth_distribution.png": "可行解齒數組合分布"})
    return AnalysisResult(fig, outputs, figures=figures if stage == "gear_tooth" else {},
                          tables=tables, figure_titles=titles,
                          artifacts={"analysis.md": (Path(__file__).with_name("notes")
                                     / f"{stage}.md").read_text(encoding="utf-8")})
