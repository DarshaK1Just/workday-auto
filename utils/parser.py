import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config" / "data.yml"

with open(CONFIG_PATH, "r") as f:
    CONFIG = yaml.safe_load(f)
