"""Motor speed/torque curve and the shared maximum torque for gearing analyses."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis_result import AnalysisResult

PLUGIN_ID = "motor"
TITLE = "motor 馬達扭矩曲線"
DESCRIPTION = "讀取轉速／扭矩曲線，將 max(torque) 傳給傳動分析。"
PARAMETERS = {}
CURVE_FILE = Path(__file__).resolve().parents[1] / "data" / "input_data" / "motor_speed_vs_torque.csv"
INPUT_FILES = (CURVE_FILE,)
OUTPUTS = {
    "drive_motor_torque_Nm": "馬達曲線最大扭矩 max(torque)（N·m）",
    "motor_peak_torque_rpm": "最大扭矩對應轉速（RPM）",
    "motor_curve_max_rpm": "曲線資料最高轉速（RPM）",
    "motor_sample_count": "轉速／扭矩資料點數",
}


def load_curve(path):
    try:
        frame = pd.read_csv(path)
    except (OSError, ValueError) as error:
        raise ValueError(f"無法讀取馬達曲線 {path}：{error}") from error
    if not {"speed", "torque"}.issubset(frame.columns):
        raise ValueError("馬達曲線 CSV 需要 speed（RPM）與 torque（N·m）欄位")
    try:
        curve = frame[["speed", "torque"]].astype(float)
    except (TypeError, ValueError) as error:
        raise ValueError("馬達轉速與扭矩必須為數值") from error
    if len(curve) < 2 or not np.isfinite(curve.to_numpy()).all():
        raise ValueError("馬達曲線至少需要兩筆有限數值資料")
    if (curve["speed"] < 0).any() or curve["speed"].duplicated().any():
        raise ValueError("馬達轉速不可為負值或重複")
    if curve["torque"].max() <= 0:
        raise ValueError("馬達曲線的最大扭矩必須大於零")
    return curve.sort_values("speed").reset_index(drop=True)


def main(parameters, *, input_path=None):
    curve = load_curve(CURVE_FILE if input_path is None else input_path)
    peak = curve.loc[curve["torque"].idxmax()]
    max_torque = float(curve["torque"].max())
    figure, axis = plt.subplots(figsize=(6, 5))
    axis.plot(curve["speed"], curve["torque"], color="green", label="Motor curve")
    axis.scatter([peak["speed"]], [max_torque], color="red", zorder=3,
                 label=f"Max torque: {max_torque:.6g} N·m")
    axis.set(title="Motor Speed vs Torque", xlabel="Motor Speed (RPM)", ylabel="Torque (N·m)")
    axis.grid(True)
    axis.legend()
    figure.tight_layout()
    print(f"max torque: {max_torque} N·m at {peak['speed']:g} RPM")
    return AnalysisResult(
        figure,
        outputs={"drive_motor_torque_Nm": max_torque, "motor_peak_torque_rpm": float(peak["speed"]),
                 "motor_curve_max_rpm": float(curve["speed"].max()), "motor_sample_count": len(curve)},
        tables={"motor_speed_vs_torque.csv": curve},
        figure_titles={"plot.png": "馬達轉速／扭矩曲線與最大扭矩"},
        artifacts={"analysis.md": (Path(__file__).with_name("gearing") / "notes" / "motor.md")
                   .read_text(encoding="utf-8")},
    )
