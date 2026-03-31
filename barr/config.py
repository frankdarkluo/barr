from pathlib import Path
from typing import Any, Dict

import yaml


def load_yaml(path: str) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)

