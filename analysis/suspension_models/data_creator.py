"""唯一批次啟動介面。修改下方設定後執行此檔案。"""

if __package__:
    from .batch_runner import main
else:
    from batch_runner import main


# ===== 使用者設定 =====
# 工況清單由 batch_cases.py 的 FAMILIES 管理，可執行 --list 查看目前保留的配對。
# 輸出類型："all"（quarter + LR + FR）、"quarter"（單輪）、"LR"（左右雙輪）、"FR"（前後雙輪）
FAMILY = "all"

# 批次工具只輸出完整模擬 PKL 數據。
# ======================


FAMILY_ALIASES = {
    "all": None,
    "quarter": ["quarter"],
    "LR": ["LR"],
    "FR": ["FR"],
}


if __name__ == "__main__":
    if FAMILY not in FAMILY_ALIASES:
        raise ValueError(f"FAMILY 請設定為以下其中之一：{', '.join(FAMILY_ALIASES)}")
    raise SystemExit(main(FAMILY_ALIASES[FAMILY]))
