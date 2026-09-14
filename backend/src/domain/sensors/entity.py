from dataclasses import dataclass
from uuid import UUID


@dataclass
class Sensor:
    id: UUID | None
    device_type: str
    display_name: str
    default_config: dict
