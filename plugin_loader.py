import os
import importlib
from pathlib import Path
from analysis_data import normalize_analysis_parameters

PROJECT_DIR = Path(__file__).resolve().parent


class AnalysisPlugin:


    def __init__(self, name, module):

        self.name = name
        self.module = module
        self.plugin_id = getattr(module, "PLUGIN_ID", name)

        self.title = getattr(
            module,
            "TITLE",
            name
        )

        self.description = getattr(
            module,
            "DESCRIPTION",
            ""
        )
        self.parameters = getattr(module, "PARAMETERS", {})
        self.parameter_defaults = getattr(module, "PARAMETER_DEFAULTS", {})
        self.hidden_parameters = set(getattr(module, "HIDDEN_PARAMETERS", ()))
        self.outputs = getattr(module, "OUTPUTS", {})
        self.required_analyses = tuple(getattr(module, "REQUIRES", ()))


    def run(self, parameters):

        return self.module.main(normalize_analysis_parameters(parameters))



def scan_analysis(folder=None):

    plugins = []

    folder = Path(folder) if folder is not None else PROJECT_DIR / "analysis"
    package_name = folder.name
    files = os.listdir(folder)


    for file in files:


        # 只抓 python

        if not file.endswith(".py"):
            continue


        # 排除init

        if file.startswith("__"):
            continue



        module_name = file[:-3]


        try:

            module = importlib.import_module(
                f"{package_name}.{module_name}"
            )


            plugin = AnalysisPlugin(
                module_name,
                module
            )


            plugins.append(plugin)



        except Exception as e:

            print(
                f"Cannot load {file}: {e}"
            )


    return plugins
