"""Score corner-radius bins using time shares and the skidpad event score."""

import math


def calculate_score_weights(track):
    scores = (track.Skidpad_score, track.Autocross_score, track.Endurance_score)
    if not all(math.isfinite(value) and value >= 0 for value in scores):
        raise ValueError("Event scores must be finite and nonnegative.")
    if not math.isfinite(track.Skidpad_r) or track.Skidpad_r <= 0:
        raise ValueError("Skidpad radius must be finite and greater than zero.")
    entries = [entry for entry in track.Radius_distribution_time
               if entry["accumulated_time_s"] > 0]
    if not entries:
        # A straight-only map has no corner-radius time to distribute.
        track.Radius_distribution_score = []
        track.top_5_score_rate = 0.0
        return []
    total_time = sum(entry["accumulated_time_s"] for entry in entries)
    closest = min(range(len(entries)),
                  key=lambda index: abs(entries[index]["radius_center_m"] - track.Skidpad_r))
    ranked = []
    for index, entry in enumerate(entries):
        ratio = entry["accumulated_time_s"] / total_time
        weighted_score = ratio * (track.Autocross_score + track.Endurance_score)
        bonus = track.Skidpad_score if index == closest else 0.0
        ranked.append(entry | {
            "weight_ratio": ratio, "weighted_score": weighted_score,
            "skidpad_bonus": bonus, "total_score": weighted_score + bonus,
        })
    ranked.sort(key=lambda entry: entry["total_score"], reverse=True)
    for rank, entry in enumerate(ranked, start=1):
        entry["rank"] = rank
    track.Radius_distribution_score = ranked
    track.top_5_score_rate = (100 * sum(entry["total_score"] for entry in ranked[:5])
                              / track.total_score if track.total_score else 0.0)
    return ranked


def create_score_figure(entries):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    figure, axis = plt.subplots(figsize=(12, 5), constrained_layout=True)
    axis.bar([entry["radius_center_m"] for entry in entries],
             [entry["total_score"] for entry in entries],
             color=["#d62728" if index < 5 else "#1f77b4" for index in range(len(entries))],
             linewidth=0.3)
    axis.legend(handles=[Patch(color="#d62728", label="Top 5"),
                         Patch(color="#1f77b4", label="Others")])
    axis.set_title("Radius Distribution Score Weight")
    axis.set_xlabel("Radius center [m]")
    axis.set_ylabel("Weighted score")
    axis.grid(True, axis="y", alpha=0.3)
    return figure
