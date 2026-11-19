"""Collect the original package's plots for the application's result gallery."""

import matplotlib.pyplot as plt


class PlotCollector:
    def __init__(self):
        self.figures = {}

    def collect_figure(self, filename, figure):
        self.figures[filename] = figure
        # Retain the Figure object without accumulating pyplot windows.
        plt.close(figure)
