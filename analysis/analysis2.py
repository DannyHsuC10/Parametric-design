"""
Simple analysis example 2
"""

TITLE = "Cosine Wave"
DESCRIPTION = "Plot cos(x)"
PLUGIN_ID = "cosine"
PARAMETERS = {"xi": "float", "xf": "float", "num_points_cos": "int"}


import numpy as np
import matplotlib.pyplot as plt
def main(parameters):

    xi = parameters["xi"]
    xf = parameters["xf"]
    num_points = parameters["num_points_cos"]

    print("=" * 40)
    print("Running Cosine Wave Analysis")
    print("=" * 40)

    x = np.linspace(xi, xf, num_points)
    y = np.cos(x)

    print(f"Average = {np.mean(y):.3f}")
    print(f"Std = {np.std(y):.3f}")

    fig, ax = plt.subplots()

    ax.plot(x, y, color="red")

    ax.set_title(TITLE)

    return fig, {}
