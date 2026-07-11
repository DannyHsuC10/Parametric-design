import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

frontwheel_track = 1300/1000 # m
rearwheel_track = 1250/1000 # m

frontwheel_axle = 0.763333771 # 重心與前軸距離 (m)
rearwheel_axle = -0.762276229 # 重心與後軸距離 (m)
# ==================================================
# Read Excel
# ==================================================
def read_mass_file(file_path):
    """
    讀取質量分布檔案

    Parameters
    ----------
    file_path : str or Path

    Returns
    -------
    df : DataFrame
    total_mass : float
    """

    df = pd.read_excel(file_path, skiprows=[1])
    df.columns = df.columns.str.strip()

    # convert numeric columns to numeric dtype
    for col in ["weight LP03", "dx", "dy", "dz", "dy/y"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    total_mass = df["weight LP03"].sum()

    print(f"Total Mass = {total_mass:.3f} kg")

    return df, total_mass

# ==================================================
# First Moment
# ==================================================
def calc_first_moment(sprung_mass_df, unsprung_front_df=None, unsprung_rear_df=None):
    """
    計算一次慣性矩(質量矩)

    Parameters
    ----------
    sprung_mass_df : DataFrame
        Sprung mass data
    unsprung_front_df : DataFrame, optional
        Front unsprung mass data
    unsprung_rear_df : DataFrame, optional
        Rear unsprung mass data

    Returns
    -------
    result : dict
    """

    mx_parts = [sprung_mass_df["weight LP03"] * sprung_mass_df["dx"]]
    my_parts = [sprung_mass_df["weight LP03"] * sprung_mass_df["dy"]]
    mz_parts = [sprung_mass_df["weight LP03"] * sprung_mass_df["dz"]]

    if unsprung_front_df is not None:
        mx_parts.append(unsprung_front_df["weight LP03"] * frontwheel_axle)
        my_parts.append(unsprung_front_df["weight LP03"] * unsprung_front_df["dy/y"] * frontwheel_track)
        mz_parts.append(unsprung_front_df["weight LP03"] * unsprung_front_df["dz"])

    if unsprung_rear_df is not None:
        mx_parts.append(unsprung_rear_df["weight LP03"] * rearwheel_axle)
        my_parts.append(unsprung_rear_df["weight LP03"] * unsprung_rear_df["dy/y"] * rearwheel_track)
        mz_parts.append(unsprung_rear_df["weight LP03"] * unsprung_rear_df["dz"])

    mx = pd.concat(mx_parts, ignore_index=True)
    my = pd.concat(my_parts, ignore_index=True)
    mz = pd.concat(mz_parts, ignore_index=True)

    result = {
        "Mx": mx,
        "My": my,
        "Mz": mz}

    return result

# ==================================================
# Second Moment
# ==================================================
def normalize_unsprung_dy(unsprung_mass_df, track_width):
    df = unsprung_mass_df.copy()
    df["dy"] = df["dy/y"] * track_width
    return df


def combine_mass_data(sprung_mass_df, unsprung_front_df=None, unsprung_rear_df=None):
    frames = [sprung_mass_df.copy()]
    if unsprung_front_df is not None:
        frames.append(normalize_unsprung_dy(unsprung_front_df, frontwheel_track))
    if unsprung_rear_df is not None:
        frames.append(normalize_unsprung_dy(unsprung_rear_df, rearwheel_track))
    return pd.concat(frames, ignore_index=True)


def calc_second_moment(sprung_mass_df, unsprung_front_df=None, unsprung_rear_df=None):
    """
    計算慣量矩

    Returns
    -------
    result : dict
    """


    df = combine_mass_data(sprung_mass_df, unsprung_front_df, unsprung_rear_df)

    Ixx = (df["weight LP03"] * (df["dy"]**2 + df["dz"]**2))
    Iyy = (df["weight LP03"] * (df["dx"]**2 + df["dz"]**2))
    Izz = (df["weight LP03"] * (df["dx"]**2 + df["dy"]**2))

    Ixx_all = Ixx.sum()
    Iyy_all = Iyy.sum()
    Izz_all = Izz.sum()

    result = {
        "Ixx_all": Ixx_all,
        "Iyy_all": Iyy_all,
        "Izz_all": Izz_all,

        "Ixx": Ixx,
        "Iyy": Iyy,
        "Izz": Izz,
    }

    return result

# ==================================================
# 3D View
# ==================================================
def plot_3d_distribution(sprung_mass_df, unsprung_front_df=None, unsprung_rear_df=None, size=20):

    save_dir = Path(__file__).parent
    df = combine_mass_data(sprung_mass_df, unsprung_front_df, unsprung_rear_df)

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    scatter = ax.scatter(
        df["dx"],
        df["dy"],
        df["dz"],
        s=df["weight LP03"] * size,
        c=df["weight LP03"],
        cmap='viridis'
    )

    for _, row in df.iterrows():
        ax.text(
            row["dx"],
            row["dy"],
            row["dz"],
            row["name"],
            fontsize=7
        )

    ax.scatter(
        0,
        0,
        0,
        marker='x',
        s=200,
        label='CG'
    )

    ax.set_title("Mass Distribution 3D")
    ax.set_xlabel("dx (m)")
    ax.set_ylabel("dy (m)")
    ax.set_zlabel("dz (m)")

    ax.legend()

    cbar = plt.colorbar(scatter)
    cbar.set_label("Mass (kg)")

    plt.tight_layout()

    save_path = save_dir/ "Figures" / "Mass_Distribution_3D.png"
    plt.savefig(save_path, dpi=300)

    plt.show()

# ==================================================
# Top View second_moment (XY)
# ==================================================
def plot_top_view(sprung_mass_df, unsprung_front_df=None, unsprung_rear_df=None, size=80):# 轉動慣輛評估

    save_dir = Path(__file__).parent
    df = combine_mass_data(sprung_mass_df, unsprung_front_df, unsprung_rear_df)
    second = calc_second_moment(sprung_mass_df, unsprung_front_df, unsprung_rear_df)

    fig, ax = plt.subplots(figsize=(10, 8))

    scatter = ax.scatter(
        df["dx"],
        df["dy"],
        s=abs(second["Izz"] * size),
        c=abs(second["Izz"]),
        cmap='viridis'
    )

    for _, row in df.iterrows():
        ax.text(
            row["dx"],
            row["dy"],
            row["name"],
            fontsize=7
        )

    ax.scatter(
        0,
        0,
        marker='x',
        s=200,
        label='CG'
    )

    ax.set_title("second_moment Distribution Top View (XY)")
    ax.set_xlabel("dx (m)")
    ax.set_ylabel("dy (m)")

    ax.grid(True)
    ax.axis('equal')

    cbar = plt.colorbar(scatter)
    cbar.set_label("second_moment (kg·m²)")

    ax.legend()

    plt.tight_layout()

    save_path = save_dir/ "Figures" / "second_moment_Distribution_XY.png"
    plt.savefig(save_path, dpi=300)

    plt.show()

# ==================================================
# Side View first_moment (XZ)
# ==================================================
def plot_side_view(sprung_mass_df, unsprung_front_df=None, unsprung_rear_df=None, size=120):# 用於重心評估

    save_dir = Path(__file__).parent
    df = combine_mass_data(sprung_mass_df, unsprung_front_df, unsprung_rear_df)
    first = calc_first_moment(sprung_mass_df, unsprung_front_df, unsprung_rear_df)

    fig, ax = plt.subplots(figsize=(10, 8))

    scatter = ax.scatter(
        df["dx"],
        df["dz"],
        s=abs(first["Mz"] * size),
        c=abs(first["Mz"]),
        cmap='viridis')

    for _, row in df.iterrows():
        ax.text(
            row["dx"],
            row["dz"],
            row["name"],
            fontsize=7)

    ax.scatter(
        0,
        0,
        marker='x',
        s=200,
        label='CG')

    ax.set_title("first_moment Distribution Side View (XZ)")
    ax.set_xlabel("mdx (m)")
    ax.set_ylabel("mdz (m)")

    ax.grid(True)
    ax.axis('equal')

    cbar = plt.colorbar(scatter)
    cbar.set_label("first_moment (Nm)")

    ax.legend()

    plt.tight_layout()

    save_path = save_dir/ "Figures" / "first_moment_Distribution_XZ.png"
    plt.savefig(save_path, dpi=300)

    plt.show()

# ==================================================
# Example
# ==================================================
if __name__ == "__main__":

    current_dir = Path(__file__).parent

    sprung_mass_df, sprung_mass = read_mass_file(current_dir / "Center_of_gravity_LP03_sprung.xlsx")
    unsprung_front_df, unsprung_front_mass = read_mass_file(current_dir / "Center_of_gravity_LP03_unsprungfront.xlsx")
    unsprung_rear_df, unsprung_rear_mass = read_mass_file(current_dir / "Center_of_gravity_LP03_unsprungrear.xlsx")

    first = calc_first_moment(sprung_mass_df, unsprung_front_df, unsprung_rear_df)
    second = calc_second_moment(sprung_mass_df, unsprung_front_df, unsprung_rear_df)

    plot_3d_distribution(sprung_mass_df, unsprung_front_df, unsprung_rear_df)
    plot_top_view(sprung_mass_df, unsprung_front_df, unsprung_rear_df)
    plot_side_view(sprung_mass_df, unsprung_front_df, unsprung_rear_df)
