"""Tangent wave example for the analysis flow."""

TITLE = "Tangent Wave"
DESCRIPTION = "Plot tan(x)"
PLUGIN_ID = "tangent"
PARAMETERS = {"xi": "float", "xf": "float", "num_points_tan": "int"}
OUTPUTS = {"max_tan": "取樣範圍內的最大 tan 值"}

import numpy as np
import matplotlib.pyplot as plt


def main(parameters):
    xi = parameters["xi"]
    xf = parameters["xf"]
    num_points = parameters["num_points_tan"]

    x = np.linspace(xi, xf, num_points)
    y = np.tan(x)
    max_tan = float(np.nanmax(y))

    print("Running Tangent Wave Analysis")
    print(f"Maximum = {max_tan:.3f}")

    fig, ax = plt.subplots()
    ax.plot(x, y)
    ax.set_title(TITLE)
    ax.set_xlabel("x")
    ax.set_ylabel("tan(x)")
    ax.grid(True)
    return fig, {"max_tan": max_tan}
