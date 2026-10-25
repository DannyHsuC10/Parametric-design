"""Per-node execution options and private manual inputs."""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path


@dataclass
class NodeSettings:
    skip: bool = False
    manual: bool = False
    parameters: dict[str, str] = field(default_factory=dict)


def load_node_settings(path):
    path = Path(path)
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("分析個別設定必須是 JSON 物件")
    settings = {}
    for node_id, entry in data.items():
        if (not isinstance(entry, dict)
                or not isinstance(entry.get("skip", False), bool)
                or not isinstance(entry.get("manual", False), bool)
                or not isinstance(entry.get("parameters", {}), dict)):
            raise ValueError(f"分析個別設定格式錯誤：{node_id}")
        settings[node_id] = NodeSettings(
            skip=entry.get("skip", False), manual=entry.get("manual", False),
            parameters={name: str(value) for name, value in entry.get("parameters", {}).items()},
        )
    return settings


def save_node_settings(path, settings):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps({node: asdict(options) for node, options in settings.items()},
                                    ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
