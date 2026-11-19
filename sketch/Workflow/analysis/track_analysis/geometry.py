"""Rebuild an OpenTRACK Excel map and create track-analysis figures."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from openpyxl import load_workbook
from analysis.cornering.models import cornering_speed


@dataclass
class Segment:
    # One row from the Shape sheet, normalized into geometry-friendly fields.
    section: int
    kind: str
    start: tuple[float, float]
    end: tuple[float, float]
    length: float
    center: tuple[float, float] | None = None
    radius: float | None = None
    direction: str = ""


def read_workbook(path: Path) -> tuple[dict[str, str], list[Segment], dict[str, np.ndarray]]:
    wb = load_workbook(path, data_only=True, read_only=True)

    # Track metadata is stored in fixed rows of the Info sheet.
    info_values = [row[1] for row in wb["Info"].iter_rows(min_row=1, max_row=7, values_only=True)]
    keys = ("name", "country", "city", "type", "config", "direction", "mirror")
    info = {key: str(value) for key, value in zip(keys, info_values)}

    # Shape rows define the centerline as LINE and ARC sections.
    shape = wb["Shape"]
    headers = {str(cell.value): index for index, cell in enumerate(next(shape.iter_rows()))}
    segments: list[Segment] = []
    for row_number, row in enumerate(shape.iter_rows(min_row=2, values_only=True), start=1):
        kind = str(row[headers["Type"]] or "").strip().upper()
        if not kind:
            continue
        if kind not in {"LINE", "ARC"}:
            print(f"Warning: skipped unknown segment type in row {row_number + 1}: {kind}")
            continue
        get = lambda name: row[headers[name]]
        segment = Segment(
            section=row_number,
            kind=kind,
            start=(float(get("Start_X")), float(get("Start_Y"))),
            end=(float(get("End_X")), float(get("End_Y"))),
            length=float(get("length")),
        )
        if kind == "ARC":
            # ARC sections need circle geometry in addition to start/end points.
            segment.center = (float(get("Center_X")), float(get("Center_Y")))
            segment.radius = float(get("Radius"))
            segment.direction = str(get("Direction") or "").strip()
        segments.append(segment)

    # These sheets are section-based tables; build_track expands them to every mesh point.
    sheets = {
        "elevation": "Elevation",
        "bank": "Banking",
        "factor_grip": "Grip Factors",
        "sector": "Sectors",
    }
    tables: dict[str, np.ndarray] = {}
    for key, sheet_name in sheets.items():
        values = [row[1] for row in wb[sheet_name].iter_rows(min_row=2, values_only=True) if row[0] is not None]
        tables[key] = np.asarray(values, dtype=float)
    wb.close()
    return info, segments, tables


def reconstruct_geometry(segments: list[Segment], ds: float) -> dict[str, np.ndarray]:
    if not math.isfinite(ds) or ds <= 0:
        raise ValueError("Mesh size must be finite and greater than zero.")
    if not segments:
        raise ValueError("Shape sheet contains no valid segments.")
    # Start from the first segment start point and append generated mesh points.
    x, y = segments[0].start
    distance = 0.0
    xs: list[float] = []
    ys: list[float] = []
    ss: list[float] = []
    kappas: list[float] = []
    sections: list[int] = []
    kinds: list[str] = []

    for segment in segments:
        if segment.kind == "LINE":
            # Split straight sections into nearly uniform steps no larger than ds.
            dx = segment.end[0] - segment.start[0]
            dy = segment.end[1] - segment.start[1]
            length = math.hypot(dx, dy)
            if length == 0:
                continue
            count = max(1, math.ceil(length / ds))
            step = length / count
            ux, uy = dx / length, dy / length
            for _ in range(count):
                x += ux * step
                y += uy * step
                distance += step
                xs.append(x); ys.append(y); ss.append(distance); kappas.append(0.0)
                sections.append(segment.section); kinds.append("LINE")
        else:
            # Walk along the arc angle; clockwise arcs use negative curvature.
            assert segment.center is not None and segment.radius is not None
            if not math.isfinite(segment.radius) or segment.radius <= 0 or segment.length <= 0:
                raise ValueError(f"Invalid arc radius or length in section {segment.section}.")
            cx, cy = segment.center
            theta = math.atan2(segment.start[1] - cy, segment.start[0] - cx)
            sign = -1.0 if segment.direction.lower().startswith("clock") else 1.0
            count = max(1, math.ceil(segment.length / ds))
            dtheta = (segment.length / segment.radius) / count
            for _ in range(count):
                theta += sign * dtheta
                x = cx + segment.radius * math.cos(theta)
                y = cy + segment.radius * math.sin(theta)
                distance += segment.radius * dtheta
                xs.append(x); ys.append(y); ss.append(distance); kappas.append(sign / segment.radius)
                sections.append(segment.section); kinds.append("LEFT" if sign > 0 else "RIGHT")

    if len(ss) < 2:
        raise ValueError("Track geometry must generate at least two mesh points.")
    return {
        "X": np.asarray(xs), "Y": np.asarray(ys), "x": np.asarray(ss),
        "kappa_raw": np.asarray(kappas), "section": np.asarray(sections, dtype=np.int32),
        "segment_type": np.asarray(kinds),
    }


def gaussian_smooth(values: np.ndarray, window: int = 80) -> np.ndarray:
    # Edge padding keeps the output length identical to the input length.
    radius = window // 2
    sigma = max(window / 6.0, np.finfo(float).eps)
    positions = np.arange(-radius, radius + 1, dtype=float)
    kernel = np.exp(-0.5 * (positions / sigma) ** 2)
    kernel /= kernel.sum()
    padded = np.pad(values, radius, mode="edge")
    return np.convolve(padded, kernel, mode="valid")


def peak_prominence(values: np.ndarray, index: int) -> float:
    # Estimate local peak prominence without depending on SciPy.
    peak = values[index]
    left_min = peak
    for i in range(index - 1, -1, -1):
        if values[i] > peak:
            break
        left_min = min(left_min, values[i])
    right_min = peak
    for i in range(index + 1, len(values)):
        if values[i] > peak:
            break
        right_min = min(right_min, values[i])
    return peak - max(left_min, right_min)


def find_peaks(values: np.ndarray, minimum_prominence: float, minimum_distance: int) -> np.ndarray:
    # Pick strong local maxima first, then enforce a minimum index spacing.
    candidates = [
        i for i in range(1, len(values) - 1)
        if values[i] > values[i - 1] and values[i] >= values[i + 1]
        and peak_prominence(values, i) >= minimum_prominence
    ]
    selected: list[int] = []
    for index in sorted(candidates, key=lambda i: values[i], reverse=True):
        if all(abs(index - other) >= minimum_distance for other in selected):
            selected.append(index)
    return np.asarray(sorted(selected), dtype=np.int32)


def build_track(segments: list[Segment], tables: dict[str, np.ndarray], ds: float) -> dict[str, np.ndarray]:
    track = reconstruct_geometry(segments, ds)
    raw = track["kappa_raw"]
    # Apex detection is based on smoothed curvature, not the raw stepped curvature.
    kappa = gaussian_smooth(raw)
    prominence = float(np.percentile(np.abs(kappa), 70) * 0.20)
    distance = max(1, round(8.0 / ds))
    left = find_peaks(kappa, prominence, distance)
    right = find_peaks(-kappa, prominence, distance)
    apex = np.asarray(sorted(np.concatenate((left, right)).tolist()), dtype=np.int32)

    section_indices = track["section"] - 1
    # Expand section-level values so every generated mesh point has matching data.
    for key, values in tables.items():
        if values.size == 0:
            raise ValueError(f"Input table {key!r} is empty.")
        track[key] = values[np.clip(section_indices, 0, len(values) - 1)]
    s = track["x"]
    elevation = track.pop("elevation")
    # Convert elevation slope into inclination angle and smooth small point-to-point noise.
    inclination = -np.degrees(np.diff(elevation) / np.diff(s))
    inclination = np.append(inclination, inclination[-1] if inclination.size else 0.0)
    inclination = np.convolve(np.pad(inclination, 2, mode="edge"), np.ones(5) / 5, mode="valid")

    track.update({
        "Z": elevation, "r": kappa, "incl": inclination,
        "dx": np.diff(np.concatenate(([0.0], s))), "n": np.asarray(len(s), dtype=np.int64),
        "apex_index": apex, "apex_s": s[apex],
        "apex_type": np.sign(kappa[apex]).astype(np.int8),
        "apex_strength": np.abs(kappa[apex]),
        "apex_mask": np.isin(np.arange(len(s)), apex),
        "arrow": np.asarray(0, dtype=np.int8),
    })
    return track


def ascii_map(track: dict[str, np.ndarray], width: int = 66) -> str:
    # Lightweight terminal preview for the log file.
    x, y = track["X"], track["Y"]
    span = float(np.ptp(x)) or 1.0
    xx = np.rint(x / span * width).astype(int)
    yy = np.rint(y / (15 / 8) / span * width).astype(int)
    xx -= xx.min(); yy = -yy; yy -= yy.min()
    points = set(zip(xx.tolist(), yy.tolist()))
    return "\n".join("".join("o" if (col, row) in points else " " for col in range(xx.max() + 1)).rstrip()
                     for row in range(yy.max() + 1))


def build_ranked_radius_distribution(
    values: np.ndarray,
    edges: np.ndarray,
    centers: np.ndarray,
    metric_key: str,
) -> list[dict[str, float | int | str]]:
    ranked_indices = np.argsort(-values, kind="stable")
    return [
        {
            "rank": rank,
            "radius_range_m": f"{edges[index]:.0f}-{edges[index + 1]:.0f}",
            "radius_center_m": float(centers[index]),
            metric_key: float(values[index]),
        }
        for rank, index in enumerate(ranked_indices, start=1)
    ]


def radius_distributions(track, max_speed, radius_limit, mu_y):
    """Integrate distance and estimated time in 1 m corner-radius bins."""
    if not all(math.isfinite(value) and value > 0 for value in (max_speed, radius_limit, mu_y)):
        raise ValueError("Maximum speed, radius limit, and lateral friction must be positive and finite.")
    curvature = track["r"]
    radius = np.full_like(curvature, np.nan, dtype=float)
    nonzero = np.abs(curvature) > 1e-9
    radius[nonzero] = 1.0 / np.abs(curvature[nonzero])
    mask = np.isfinite(radius) & (radius <= radius_limit)
    finite_radius, finite_dx = radius[mask], track["dx"][mask]
    # mu_y is dimensionless: v²/r = mu_y * g.
    limited_speed = np.minimum(cornering_speed(finite_radius, mu_y), max_speed)
    finite_dt = finite_dx / limited_speed
    bins = np.arange(0.0, math.ceil(radius_limit) + 1.0, 1.0)
    lengths, edges = np.histogram(finite_radius, bins=bins, weights=finite_dx)
    times, _ = np.histogram(finite_radius, bins=bins, weights=finite_dt)
    centers = (edges[:-1] + edges[1:]) / 2.0
    return (
        build_ranked_radius_distribution(lengths, edges, centers, "accumulated_length_m"),
        build_ranked_radius_distribution(times, edges, centers, "accumulated_time_s"),
    )


def create_figures(
    track: dict[str, np.ndarray],
    length_distribution: list[dict],
    time_distribution: list[dict],
):
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from matplotlib.colors import TwoSlopeNorm

    x, y = track["X"], track["Y"]
    raw_curvature = track["kappa_raw"]
    curvature = track["r"]
    apex = track["apex_index"]
    figures = {}

    def save_current(fig: plt.Figure, suffix: str) -> None:
        figures[f"{suffix}.png"] = fig

    # XY map: color the track by smoothed curvature and add apex markers.
    fig, ax = plt.subplots(figsize=(10, 8), constrained_layout=True)
    points = np.column_stack((x, y))
    segments = np.stack((points[:-1], points[1:]), axis=1)
    limit = float(np.max(np.abs(curvature))) or 1.0
    norm = TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit)
    line_values = (curvature[:-1] + curvature[1:]) / 2.0
    colored_track = LineCollection(segments, cmap="rainbow", norm=norm, linewidth=3.0)
    colored_track.set_array(line_values)
    ax.add_collection(colored_track)
    ax.autoscale()
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("XY Map")
    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.grid(True)
    cbar = fig.colorbar(colored_track, ax=ax)
    cbar.set_label("Curvature [1/m]")
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, loc="best")
    save_current(fig, "xy_map")

    # Curvature comparison: apex points are marked only on the smoothed curve.
    fig, ax = plt.subplots(figsize=(12, 5), constrained_layout=True)
    ax.plot(track["x"], raw_curvature, color="#2ca02c", linewidth=1, label="Raw curvature")
    ax.plot(track["x"], curvature, color="#1f77b4", linewidth=1, label="Gaussian smoothed")
    ax.scatter(
        track["apex_s"],
        curvature[apex],
        s=22,
        c="#c13636",
        linewidths=0.35,
        label="Apex after smoothing",
        zorder=3,
    )
    ax.set_title("Curvature vs Distance")
    ax.set_xlabel("Distance [m]")
    ax.set_ylabel("Curvature [1/m]")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    save_current(fig, "radius")

    # FFT spectrum of smoothed curvature over distance.
    ds_fft = float(np.mean(track["dx"])) if len(track["dx"]) else 1.0
    fft_val = np.fft.fft(curvature)
    freq = np.fft.fftfreq(len(curvature), d=ds_fft)
    amp = np.abs(fft_val)
    positive_freq_mask = freq > 0
    positive_freq = freq[positive_freq_mask]
    positive_amp = amp[positive_freq_mask]

    fig, ax = plt.subplots(figsize=(12, 5), constrained_layout=True)
    freq_limit = 0.5
    fft_plot_mask = positive_freq <= freq_limit
    ax.plot(positive_freq[fft_plot_mask], positive_amp[fft_plot_mask], color="#1f77b4", linewidth=1.2)
    ax.set_xlim(0.0, freq_limit)
    ax.set_title("Curvature Spectrum (FFT)")
    ax.set_xlabel("Spatial Frequency [1/m]")
    ax.set_ylabel("Amplitude")
    ax.grid(True, alpha=0.3)
    save_current(fig, "curvature_fft_frequency")

    fig, ax = plt.subplots(figsize=(12, 5), constrained_layout=True)
    wavelength = 1.0 / positive_freq
    order = np.argsort(wavelength)
    ax.plot(wavelength[order], positive_amp[order], color="#1f77b4", linewidth=1.2)
    ax.set_xscale("log")
    ax.set_title("Track Curvature Spectrum")
    ax.set_xlabel("Spatial Wavelength [m]")
    ax.set_ylabel("Amplitude")
    ax.grid(True, which="both", alpha=0.3)
    save_current(fig, "curvature_fft_wavelength")

    # Radius time distribution: each point contributes dx / v to a 1 m radius bin.
    fig, ax = plt.subplots(figsize=(12, 5), constrained_layout=True)
    by_radius = sorted(time_distribution, key=lambda item: item["radius_center_m"])
    length_by_radius = np.asarray([item["accumulated_length_m"] for item in
                                  sorted(length_distribution, key=lambda item: item["radius_center_m"])])
    time_by_radius = np.asarray([item["accumulated_time_s"] for item in by_radius])
    centers = np.asarray([item["radius_center_m"] for item in by_radius])
    widths = np.ones_like(centers)
    top_time_indices = np.argsort(-time_by_radius, kind="stable")[:5]
    top_length_indices = np.argsort(-length_by_radius, kind="stable")[:5]
    top_index_set = set(top_time_indices.tolist())
    bar_colors = ["#d62728" if index in top_index_set else "#1f77b4" for index in range(len(time_by_radius))]
    ax.bar(centers, time_by_radius, width=widths, align="center", color=bar_colors, linewidth=0.3)
    ax.set_title("Radius Time Distribution")
    ax.set_xlabel("Radius [m]")
    ax.set_ylabel("Accumulated time [s]")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(
        handles=[
            plt.Rectangle((0, 0), 1, 1, color="#d62728", label="Top 5 time bins"),
            plt.Rectangle((0, 0), 1, 1, color="#1f77b4", label="Other radius bins"),
        ],
        loc="best",
    )
    save_current(fig, "radius_time_distribution")

    fig, ax = plt.subplots(figsize=(12, 5), constrained_layout=True)
    bar_colors = ["#d62728" if index in set(top_length_indices.tolist()) else "#1f77b4" for index in range(len(length_by_radius))]
    ax.bar(centers, length_by_radius, width=widths, align="center", color=bar_colors, linewidth=0.3)
    ax.set_title("Radius Length Distribution")
    ax.set_xlabel("Radius [m]")
    ax.set_ylabel("Accumulated length [m]")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(
        handles=[
            plt.Rectangle((0, 0), 1, 1, color="#d62728", label="Top 5 length bins"),
            plt.Rectangle((0, 0), 1, 1, color="#1f77b4", label="Other radius bins"),
        ],
        loc="best",
    )
    save_current(fig, "radius_length_distribution")

    # Remaining plots are section data expanded onto the generated distance vector.
    scalar_plots = [
        ("elevation", "Elevation", track["x"], track["Z"], "Distance [m]", "Elevation [m]"),
        ("inclination", "Inclination", track["x"], track["incl"], "Distance [m]", "Inclination [deg]"),
        ("banking", "Banking", track["x"], track["bank"], "Distance [m]", "Banking [deg]"),
        ("grip_factor", "Grip Factor", track["x"], track["factor_grip"], "Distance [m]", "Grip factor [-]"),
    ]
    for suffix, title, xx, yy, xlabel, ylabel in scalar_plots:
        fig, ax = plt.subplots(figsize=(12, 5), constrained_layout=True)
        ax.plot(xx, yy, color="#1f77b4", linewidth=1.4)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        save_current(fig, suffix)

    return figures
