"""Plot recorded track-speed PKL data without running the lap simulator.

Run this script to save a PNG and show the figure. Use --no-show for file output
only, or --input other_data.pkl to select another SimulationLogger recording.
The original lateral-limit curve is unavailable in the recorded data.
"""

import argparse
import pickle
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np


def load_speed_data(pkl_path: Path) -> tuple[dict[str, np.ndarray], dict]:
    """Read a trusted SimulationLogger pickle and validate its plot inputs."""
    with pkl_path.open("rb") as file:
        package = pickle.load(file)
    if not isinstance(package, dict) or not isinstance(package.get("data"), dict):
        raise ValueError("Expected a SimulationLogger pickle with a 'data' dictionary.")
    recorded = package["data"]
    missing = {"s_world", "v", "s", "phase", "t"} - recorded.keys()
    if missing:
        raise ValueError(f"Missing PKL fields: {', '.join(sorted(missing))}")
    metadata = package.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("PKL metadata must be a dictionary.")

    coordinates = np.asarray(recorded["s_world"], dtype=float)
    if coordinates.ndim != 2 or coordinates.shape[1] < 2:
        raise ValueError("s_world must have shape (samples, 2 or more).")

    def scalar_series(name: str) -> np.ndarray:
        values = np.asarray(recorded[name], dtype=float)
        if values.ndim == 2 and values.shape[1] >= 1:
            return values[:, 0]
        if values.ndim == 1:
            return values
        raise ValueError(f"{name} must be a one-dimensional series or a sample matrix.")

    data = {
        "x_m": coordinates[:, 0],
        "y_m": coordinates[:, 1],
        "speed_m_s": scalar_series("v"),
        "distance_m": scalar_series("s"),
        "time_s": scalar_series("t"),
    }
    samples = len(coordinates)
    if samples < 2:
        raise ValueError("At least two track samples are required.")
    phase = np.asarray(recorded["phase"], dtype=str)
    if phase.ndim != 1 or any(len(values) != samples for values in (*data.values(), phase)):
        raise ValueError("Track coordinates, speed, distance and phase lengths differ.")
    if any(not np.all(np.isfinite(values)) for values in data.values()):
        raise ValueError("Track coordinates, speed and distance must be finite.")
    if np.any(data["speed_m_s"] < 0):
        raise ValueError("Speed must be nonnegative.")
    if np.any(np.diff(data["time_s"]) <= 0) or np.any(np.diff(data["distance_m"]) < 0):
        raise ValueError("Time must increase strictly and distance must not decrease.")
    data["phase"] = phase
    unknown = set(data["phase"]) - {"accelerate", "brake", "hold"}
    if unknown:
        raise ValueError(f"Unknown phase values: {', '.join(sorted(unknown))}")
    return data, metadata


def build_speed_figure(data: dict[str, np.ndarray], metadata: dict):
    """Plot the recorded centerline without depending on the source simulator."""

    speed = data["speed_m_s"]
    points = np.column_stack((data["x_m"], data["y_m"]))
    segments = np.stack((points[:-1], points[1:]), axis=1)
    line_collection = LineCollection(
        segments,
        cmap="turbo",
        norm=plt.Normalize(float(np.min(speed)), float(np.max(speed))),
        linewidths=3.0,
    )
    line_collection.set_array(speed[:-1])

    fig, (ax, ax_speed) = plt.subplots(
        2, 1, figsize=(11, 10), gridspec_kw={"height_ratios": [3.0, 1.0]}
    )
    ax.add_collection(line_collection)
    ax.scatter(points[0, 0], points[0, 1], color="black", s=35, label="Start")
    ax.autoscale_view()
    fig.colorbar(line_collection, ax=ax).set_label("Speed [m/s]")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    lap_time = metadata.get("lap_time_s")
    title = "Aero Fx/Fy Speed Map"
    if lap_time is not None:
        title += f" (lap time={float(lap_time):.3f} s)"
    ax.set_title(title)
    ax.grid(True, linestyle=":", linewidth=0.6)
    ax.legend(loc="best")

    for phase_name, color in (
        ("accelerate", "tab:green"),
        ("brake", "tab:red"),
        ("hold", "0.35"),
    ):
        mask = data["phase"] == phase_name
        ax_speed.scatter(
            data["distance_m"][mask], speed[mask],
            s=8, color=color, label=phase_name, alpha=0.8,
        )
    ax_speed.set_xlabel("Distance [m]")
    ax_speed.set_ylabel("Speed [m/s]")
    ax_speed.grid(True, linestyle=":", linewidth=0.6)
    ax_speed.legend(ncol=4, loc="best")
    fig.tight_layout()
    return fig


def plot_track_speed_map(pkl_path: Path, output_path: Path, *, show: bool = True) -> Path:
    data, metadata = load_speed_data(pkl_path)
    fig = build_speed_figure(data, metadata)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    print(f"Saved: {output_path.resolve()}", flush=True)
    print("Lateral speed limit omitted: it is not stored in the PKL.", flush=True)
    if show:
        plt.show()
    plt.close(fig)
    return output_path


def main() -> None:
    project_dir = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "--pkl", type=Path,
                        default=project_dir / "data/input_data/steady_lapsim.pkl")
    parser.add_argument("--output", type=Path,
                        default=project_dir / "data/results/steady_lapsim/plot.png")
    parser.add_argument("--no-show", action="store_true")
    args = parser.parse_args()
    plot_track_speed_map(
        args.input,
        args.output or args.input.with_name("track_speed_map_from_pkl.png"),
        show=not args.no_show,
    )


if __name__ == "__main__":
    main()
