"""Track metadata and radius distributions, without import-time file access."""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path


@dataclass
class TrackData:
    Skidpad_score: float = 75.0
    Autocross_score: float = 100.0
    Endurance_score: float = 250.0
    Skidpad_r: float = 9.125
    Track_length: float = 0.0
    Average_radius: float | None = None
    Name: str = ""
    Country: str = ""
    Track_points: int = 0
    Mesh_size: float = 0.1
    Apex_count: int = 0
    track_Minimum_radius: float | None = None
    top_5_score_rate: float = 0.0
    Radius_distribution_length: list[dict] = field(default_factory=list)
    Radius_distribution_time: list[dict] = field(default_factory=list)
    Radius_distribution_score: list[dict] = field(default_factory=list)

    @property
    def total_score(self):
        return self.Skidpad_score + self.Autocross_score + self.Endurance_score

    def to_json(self):
        return json.dumps(asdict(self) | {"total_score": self.total_score},
                          ensure_ascii=False, allow_nan=False, indent=2)

    def save_json(self, filename):
        Path(filename).write_text(self.to_json(), encoding="utf-8")
