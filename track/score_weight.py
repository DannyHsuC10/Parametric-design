"""
分數權重計算
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from track_data import track_data

# 設定物件
base_dir = Path(__file__).resolve().parent
track_info = track_data()
track_info.load_json(base_dir / "track.json")

base_score = float(track_info.Autocross_score + track_info.Endurance_score)
skidpad_score = float(getattr(track_info, "Skidpad_score", 0.0))
skidpad_r = float(getattr(track_info, "Skidpad_r", 0.0))

radius_distribution = track_info.Radius_distribution_time or []
if not radius_distribution:
    raise ValueError("Radius_distribution_time is empty.")

valid_entries = []
for entry in radius_distribution:
    accumulated_time = entry.get("accumulated_time_s")
    if accumulated_time is None:
        continue
    try:
        accumulated_time = float(accumulated_time)
    except (TypeError, ValueError):
        continue
    if accumulated_time <= 0:
        continue
    valid_entries.append(entry)

if not valid_entries:
    raise ValueError("No valid accumulated_time_s values found in Radius_distribution_time.")

total_time = sum(float(entry.get("accumulated_time_s", 0.0) or 0.0) for entry in valid_entries)
if total_time <= 0:
    raise ValueError("Total time is zero.")

closest_index = None
closest_distance = None
for index, entry in enumerate(valid_entries):
    radius_center = entry.get("radius_center_m")
    if radius_center is None:
        continue
    try:
        distance = abs(float(radius_center) - skidpad_r)
    except (TypeError, ValueError):
        continue
    if closest_distance is None or distance < closest_distance:
        closest_distance = distance
        closest_index = index

scored_entries = []
for index, entry in enumerate(valid_entries):
    accumulated_time = float(entry.get("accumulated_time_s", 0.0) or 0.0)
    weight_ratio = accumulated_time / total_time
    weighted_score = weight_ratio * base_score
    skidpad_bonus = skidpad_score if closest_index == index else 0.0
    total_score = weighted_score + skidpad_bonus
    scored_entries.append({
        "rank": 0,
        "radius_range_m": entry.get("radius_range_m"),
        "radius_center_m": float(entry.get("radius_center_m", 0.0)),
        "accumulated_time_s": accumulated_time,
        "weight_ratio": weight_ratio,
        "weighted_score": weighted_score,
        "skidpad_bonus": skidpad_bonus,
        "total_score": total_score,
    })

scored_entries.sort(key=lambda item: item["total_score"], reverse=True)
for rank, entry in enumerate(scored_entries, start=1):
    entry["rank"] = rank

track_info.Radius_distribution_score = scored_entries
# Ensure total scoring pool includes skidpad
track_info.total_score = float(
    float(getattr(track_info, "Autocross_score", 0.0))
    + float(getattr(track_info, "Endurance_score", 0.0))
    + float(getattr(track_info, "Skidpad_score", 0.0))
)
# Sum top-5 total_score (if fewer than 5 entries, sum all available)
top5_sum = sum(entry.get("total_score", 0.0) for entry in scored_entries[:5])
track_info.top_5_score_rate = float(top5_sum / track_info.total_score)*100 if track_info.total_score else None
track_info.save_json(base_dir / "track.json")

output_dir = base_dir / "OpenTRACK Tracks"
output_dir.mkdir(parents=True, exist_ok=True)
plot_path = output_dir / "OpenTRACK_radius_score_weight.png"

fig, ax = plt.subplots(figsize=(12, 5), constrained_layout=True)
centers = [entry["radius_center_m"] for entry in scored_entries]
scores = [entry["total_score"] for entry in scored_entries]
# Color top 5 as red, others as blue
colors = ["#d62728" if i < 5 else "#1f77b4" for i in range(len(scored_entries))]
ax.bar(centers, scores, color=colors, linewidth=0.3)
# Add legend for top 5 vs others
handles = [Patch(color="#d62728", label="Top 5"), Patch(color="#1f77b4", label="Others")]
ax.legend(handles=handles, loc="best")
ax.set_title("Radius Distribution Score Weight")
ax.set_xlabel("Radius center [m]")
ax.set_ylabel("Weighted score")
ax.grid(True, axis="y", alpha=0.3)
fig.savefig(plot_path, dpi=180)
plt.close(fig)



print(f"Saved {plot_path}")
print(f"Saved radius score ranking to {base_dir / 'track.json'}")