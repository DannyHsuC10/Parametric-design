"""Export the complete recording analysis without opening the desktop app."""

import matplotlib
matplotlib.use("Agg")

from app.analysis_result import save_analysis_result
from .workflow import INPUT_FILE, run


if __name__ == "__main__":
    result = run()
    try:
        save_analysis_result(INPUT_FILE.parents[1] / "results", "steady_lapsim", {}, result)
    finally:
        result.close()
