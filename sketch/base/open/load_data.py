import pandas as pd
import numpy as np
from pathlib import Path


class ParameterLoader:
    """
    Load parameters from Excel.

    Excel format

    | name | value | comment | unit |
    |------|-------|---------|------|
    | m    | 321   | Vehicle mass | kg |
    | mu_w | 1.7   | Tire friction | - |
    """

    def __init__(self):

        self.data = {}

    def load(self, filename):

        # 自動取得目前 python 所在資料夾
        current_dir = Path(__file__).parent

        file_path = current_dir / filename

        # 讀取 Excel
        df = pd.read_excel(file_path)

        if "name" not in df.columns:
            raise ValueError("Excel must contain 'name' column.")

        if "value" not in df.columns:
            raise ValueError("Excel must contain 'value' column.")

        for _, row in df.iterrows():

            name = str(row["name"]).strip()

            if name == "" or pd.isna(name):
                continue

            value = self.parse_value(row["value"])

            self.data[name] = value

            # 可以直接 param.m 這樣存取
            setattr(self, name, value)

        return self

    @staticmethod
    def parse_value(value):

        if pd.isna(value):
            return None

        # Excel 讀進來通常已經是數字
        if isinstance(value, (int, float, bool, np.number)):
            return value

        text = str(value).strip()

        if text == "":
            return None

        # 字串
        if (
            (text.startswith('"') and text.endswith('"'))
            or
            (text.startswith("'") and text.endswith("'"))
        ):
            return text[1:-1]

        # int
        try:
            return int(text)
        except:
            pass

        # float
        try:
            return float(text)
        except:
            pass

        # list / ndarray
        try:
            return eval(text)
        except:
            pass

        return text