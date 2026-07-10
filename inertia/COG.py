import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

# ==================================================
# Read CSV
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

    df = pd.read_csv(file_path, skiprows=[1])

    total_mass = df["m"].sum()

    print(f"Total Mass = {total_mass:.3f} kg")

    return df, total_mass

# ==================================================
# First Moment
# ==================================================
def calc_first_moment(df):
    """
    計算一次慣性矩(質量矩)

    Parameters
    ----------
    front_axle_x : float
        前軸位置

    rear_axle_x : float
        後軸位置

    Returns
    -------
    result : dict
    """

    mx = (df["m"] * df["dx"])
    my = (df["m"] * df["dy"])
    mz = (df["m"] * df["dz"])

    result = {
        "Mx": mx,
        "My": my,
        "Mz": mz}

    return result

# ==================================================
# Second Moment
# ==================================================
def calc_second_moment(df):
    """
    計算慣量矩

    Returns
    -------
    result : dict
    """

    Ixx = (df["m"] * (df["dy"]**2 + df["dz"]**2))
    Iyy = (df["m"] * (df["dx"]**2 + df["dz"]**2))
    Izz = (df["m"] * (df["dx"]**2 + df["dy"]**2))

    Ixx_all = (df["m"] * (df["dy"]**2 + df["dz"]**2)).sum()
    Iyy_all = (df["m"] * (df["dx"]**2 + df["dz"]**2)).sum()
    Izz_all = (df["m"] * (df["dx"]**2 + df["dy"]**2)).sum()

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
def plot_3d_distribution(df, size=20):

    save_dir = Path(__file__).parent

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    scatter = ax.scatter(
        df["dx"],
        df["dy"],
        df["dz"],
        s=df["m"] * size,
        c=df["m"],
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
def plot_top_view(df,size=40):# 轉動慣輛評估

    save_dir = Path(__file__).parent

    fig, ax = plt.subplots(figsize=(10, 8))

    scatter = ax.scatter(
        df["dx"],
        df["dy"],
        s=abs(calc_second_moment(df)["Izz"] * size),
        c=abs(calc_second_moment(df)["Izz"]),
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
    ax.set_xlabel("dx (Nm^2)")
    ax.set_ylabel("dy (Nm^2)")

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
def plot_side_view(df,size=40):# 用於重心評估

    save_dir = Path(__file__).parent

    fig, ax = plt.subplots(figsize=(10, 8))

    scatter = ax.scatter(
        df["dx"],
        df["dz"],
        s=abs(calc_first_moment(df)["Mz"] * size),
        c=abs(calc_first_moment(df)["Mz"]),
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
    ax.set_xlabel("mdx (Nm)")
    ax.set_ylabel("mdz (Nm)")

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

    file_path = current_dir / "Center_of_gravity_LP03.csv"

    df, total_mass = read_mass_file(file_path)

    first = calc_first_moment(df)

    second = calc_second_moment(df)

    plot_3d_distribution(df)
    plot_top_view(df)
    plot_side_view(df)
