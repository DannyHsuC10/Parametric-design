"""ISO 8608 road profile and speed-weighted excitation analysis."""

TITLE = "PSD"
DESCRIPTION = "Generate an ISO 8608 road profile and analyze speed-weighted excitation."
PLUGIN_ID = "psd"
PARAMETERS = {}
OUTPUTS = {
    "dominant_excitation_band_low_Hz": "Lower edge of the dominant excitation band (Hz)",
    "dominant_excitation_band_high_Hz": "Upper edge of the dominant excitation band (Hz)",
    "peak_excitation_frequency_Hz": "Peak weighted excitation frequency (Hz)",
    "mean_speed_mps": "Mean vehicle speed from the trace (m/s)",
}

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from analysis_result import AnalysisResult


def _load_velocity_trace(path):
    with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("速度資料 CSV 必須包含 time 與 speed 欄位")
        fields = {field.strip().lower(): field for field in reader.fieldnames}
        if "time" not in fields or "speed" not in fields:
            raise ValueError("速度資料 CSV 必須包含 time 與 speed 欄位")
        records = [
            {"time": row[fields["time"]], "speed": row[fields["speed"]]}
            for row in reader
        ]

    try:
        time = np.asarray([float(row["time"]) for row in records], dtype=float)
        speed = np.asarray([float(row["speed"]) for row in records], dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError("time 與 speed 欄位必須是數值") from error
    if len(time) < 2 or len(speed) != len(time):
        raise ValueError("速度資料至少需要兩筆 time、speed 數值")
    if not np.all(np.isfinite(time)) or not np.all(np.isfinite(speed)):
        raise ValueError("time 與 speed 欄位不可包含空值或非有限數值")
    if np.mean(speed) <= 0:
        raise ValueError("平均車速必須大於零")
    return time, speed


def main(parameters):
    project_dir = Path(__file__).resolve().parent.parent
    data_path = project_dir / "data" / "input_data" / "vt_data.csv"
    if not data_path.is_file():
        raise FileNotFoundError(f"找不到速度資料檔：{data_path}")
    time, speed = _load_velocity_trace(data_path)

    # ISO 8608 Class C road profile (same constants as PSD.m).
    road_length = 1000.0  # m
    spatial_step = 0.01  # m
    sample_count = int(round(road_length / spatial_step)) + 1
    distance = np.arange(sample_count, dtype=float) * spatial_step
    reference_spatial_frequency = 0.1  # cycles/m
    reference_psd = 16e-6  # m^3
    waviness = 2.0
    spatial_bin_width = 1 / road_length
    spatial_frequency = np.arange(sample_count // 2 + 1) * spatial_bin_width
    spatial_frequency[0] = spatial_frequency[1]
    road_psd = reference_psd * (spatial_frequency / reference_spatial_frequency) ** (
        -waviness
    )

    random_phase = 2 * np.pi * np.random.random(len(spatial_frequency))
    amplitude = np.sqrt(2 * road_psd * spatial_bin_width)
    spectrum = amplitude * np.exp(1j * random_phase)
    full_spectrum = np.concatenate((spectrum, np.conjugate(spectrum[-2:0:-1])))
    road = np.real(np.fft.ifft(full_spectrum)) * sample_count
    distance = distance[: len(road)]

    speed_pdf, speed_edges = np.histogram(speed, bins=40, density=True)
    speed_centers = (speed_edges[:-1] + speed_edges[1:]) / 2
    spatial_frequency_for_excitation = spatial_frequency[1:]
    road_weight = road_psd[1:]
    excitation_frequency = (
        spatial_frequency_for_excitation[:, None] * speed_centers[None, :]
    ).ravel()
    excitation_weight = (road_weight[:, None] * speed_pdf[None, :]).ravel()

    frequency_edges = np.linspace(0, 50, 300)
    weighted_counts, _ = np.histogram(
        excitation_frequency,
        bins=frequency_edges,
        weights=excitation_weight,
    )
    max_weight = float(np.max(weighted_counts)) if len(weighted_counts) else 0.0
    if max_weight <= 0:
        raise ValueError("速度資料無法產生 0–50 Hz 範圍內的激振頻譜")
    weighted_counts = weighted_counts / max_weight
    frequency_centers = (frequency_edges[:-1] + frequency_edges[1:]) / 2

    total_energy = float(np.sum(weighted_counts))
    if total_energy <= 0:
        raise ValueError("加權激振頻譜總能量為零")
    energy = weighted_counts / total_energy
    cumulative_energy = np.cumsum(energy)
    dominant_mask = energy >= 0.7 * np.max(energy)
    dominant_frequencies = frequency_centers[dominant_mask]
    if len(dominant_frequencies) == 0:
        raise ValueError("找不到主要激振頻帶")

    mean_speed = float(np.mean(speed))
    road_time = distance / mean_speed
    sampling_frequency = 1 / float(np.mean(np.diff(road_time)))
    road_fft = np.fft.fft(road)
    two_sided_amplitude = np.abs(road_fft / len(road))
    one_sided_amplitude = two_sided_amplitude[: len(road) // 2]
    if len(one_sided_amplitude) > 2:
        one_sided_amplitude[1:-1] *= 2
    fft_frequency = sampling_frequency * np.arange(len(one_sided_amplitude)) / len(road)

    figure, excitation_axes = plt.subplots(3, 1, figsize=(10, 9))
    road_figure, road_axes = plt.subplots(3, 1, figsize=(10, 9))
    speed_figure, speed_axes = plt.subplots(3, 1, figsize=(10, 9))
    axes = [road_axes[0], speed_axes[0], speed_axes[1], speed_axes[2],
            excitation_axes[0], excitation_axes[1], excitation_axes[2], road_axes[1], road_axes[2]]
    axes[0].plot(distance, road)
    axes[0].set(xlabel="Distance (m)", ylabel="Road Height (m)", title="ISO Road Profile")
    axes[1].plot(time, speed, linewidth=1.5)
    axes[1].set(xlabel="Time (s)", ylabel="Speed (m/s)", title="Vehicle Speed Trace")
    axes[2].hist(speed, bins=30)
    axes[2].set(xlabel="Speed (m/s)", ylabel="Counts", title="Speed Distribution")
    axes[3].hist(speed, bins=30, density=True)
    axes[3].set(
        xlabel="Speed (m/s)",
        ylabel="Probability Density",
        title="Speed Probability Density",
    )
    axes[4].plot(frequency_centers, weighted_counts, linewidth=2)
    axes[4].set(
        xlabel="Excitation Frequency (Hz)",
        ylabel="Normalized Energy",
        title="Weighted Excitation Frequency Spectrum",
        xlim=(0, 50),
    )
    axes[5].plot(frequency_centers, energy, linewidth=2)
    axes[5].set(
        xlabel="Frequency (Hz)",
        ylabel="Normalized Energy",
        title="Frequency vs Excitation Energy",
        xlim=(0, 30),
    )
    axes[6].plot(frequency_centers, cumulative_energy, linewidth=2)
    axes[6].set(
        xlabel="Frequency (Hz)",
        ylabel="Cumulative Energy",
        title="Cumulative Excitation Energy",
        xlim=(0, 30),
        ylim=(0, 1),
    )
    axes[7].plot(fft_frequency, one_sided_amplitude, linewidth=1.5)
    axes[7].set(
        xlabel="Frequency (Hz)", ylabel="Amplitude", title="Road Profile FFT", xlim=(0, 50)
    )
    axes[8].loglog(fft_frequency, one_sided_amplitude, linewidth=1.5)
    axes[8].set(
        xlabel="Frequency (Hz)",
        ylabel="Amplitude",
        title="Road FFT (log-log)",
        xlim=(1e-2, 50),
    )
    for axis in axes:
        axis.grid(True)
    figure.suptitle("Speed-weighted excitation spectrum and energy")
    road_figure.suptitle("ISO road profile and FFT")
    speed_figure.suptitle("Vehicle speed trace and distributions")
    for page in (figure, road_figure, speed_figure):
        page.tight_layout()

    dominant_low = float(np.min(dominant_frequencies))
    dominant_high = float(np.max(dominant_frequencies))
    peak_frequency = float(frequency_centers[int(np.argmax(energy))])
    print(f"Dominant excitation band: {dominant_low:.2f} Hz ~ {dominant_high:.2f} Hz")
    print(f"Peak weighted excitation frequency: {peak_frequency:.2f} Hz")
    outputs = {
        "dominant_excitation_band_low_Hz": dominant_low,
        "dominant_excitation_band_high_Hz": dominant_high,
        "peak_excitation_frequency_Hz": peak_frequency,
        "mean_speed_mps": mean_speed,
    }
    return AnalysisResult(figure, outputs, figures={
        "road_profile_fft.png": road_figure, "vehicle_speed_distribution.png": speed_figure,
    }, figure_titles={
        "plot.png": "主要結果｜激振頻譜與能量",
        "road_profile_fft.png": "路面剖面與 FFT",
        "vehicle_speed_distribution.png": "車速時序與分布",
    })
