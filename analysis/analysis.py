"""
Simple analysis example
"""

TITLE = "Sine Wave"
DESCRIPTION = "Plot sin(x)"
PLUGIN_ID = "sine"
PARAMETERS = {"xi": "float", "xf": "float", "num_points_sin": "int"}
OUTPUTS = {"max_sin": "整個取樣範圍的最大 sin 值"}


import numpy as np
import matplotlib.pyplot as plt
def main(parameters):

    xi = parameters["xi"]
    xf = parameters["xf"]
    num_points = parameters["num_points_sin"]

    print("=" * 40)
    print("Running Sine Wave Analysis")
    print("=" * 40)

    x = np.linspace(xi, xf, num_points)
    y = np.sin(x)

    max_sin = float(np.max(y))
    print(f"Maximum = {max_sin:.3f}")
    print(f"Minimum = {np.min(y):.3f}")

    fig, ax = plt.subplots()

    ax.plot(x, y)

    ax.set_title(TITLE)

    return fig, {"max_sin": max_sin}
