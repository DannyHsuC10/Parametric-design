import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from load_data import ParameterLoader

param = ParameterLoader().load("data.xlsx")

# Parameters
Ks = param.Ks     # Suspension stiffness (N/m)
Kt = param.Kt     # Tire stiffness (N/m)

# Chassis stiffness sweep
ratio = np.arange(1, 21)
Kc = ratio * Ks

# 剛性
# =====================================
# Equivalent stiffness
Keq = 1.0 / (1.0 / Kt + 1.0 / Ks + 1.0 / Kc)

# Saturation (Kc -> infinity)
Keq_inf = 1.0 / (1.0 / Kt + 1.0 / Ks)


# 10x Rule(10倍原則)
# =====================================
# Design ratios to highlight
plt.figure(figsize=(8, 5))
highlight_ratios = [3, 5, 10]

colors = {
    3: "green",
    5: "orange",
    10: "red"
}

for r in highlight_ratios:

    idx = np.where(ratio == r)[0][0]
    Keq_r = Keq[idx]

    print(f"Equivalent stiffness @{r}x = {Keq_r:,.1f} N/m")

    # Vertical line
    plt.axvline(
        r,
        linestyle="--",
        color=colors[r],
        linewidth=2,
        label=f"{r}× Rule"
    )

    # Highlight point
    plt.scatter(
        r,
        Keq_r,
        color=colors[r],
        s=70,
        zorder=5
    )

    # Annotation
    plt.annotate(
        f"{Keq_r:,.0f} N/m",
        xy=(r, Keq_r),
        xytext=(8, 10),
        textcoords="offset points",
        color=colors[r]
    )


# Plot
# =====================================
plt.plot(
    ratio,
    Keq,
    "o-",
    linewidth=2,
    markersize=6,
    label="Equivalent Stiffness"
)

# Saturation line
plt.axhline(
    Keq_inf,
    linestyle="--",
    color="black",
    linewidth=2,
    label="Saturation Limit"
)

plt.grid(True)

plt.xlabel("Chassis Stiffness / Suspension Stiffness Ratio ($K_c/K_s$)")
plt.ylabel("Equivalent Stiffness $K_{eq}$ (N/m)")
plt.title("Effect of Chassis Stiffness on Overall Stiffness")

plt.legend()

plt.tight_layout()

# Save figure
output_path = Path(__file__).parent / "Overall_Rigidity.png"

plt.savefig(output_path, dpi=300)

print(f"\nFigure saved to:\n{output_path}")

plt.show()