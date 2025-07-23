"""
Handles loading of the YAML configuration file.
"""

from pathlib import Path
from typing import Any, Dict

import yaml

CONFIG_PATH = Path(__file__).parent.parent / "config" / "data.yml"

def load_config() -> Dict[str, Any]:
    """Loads the configuration from the data.yml file.

    Returns:
        Dict[str, Any]: The configuration as a dictionary.

    Raises:
        FileNotFoundError: If the config file cannot be found.
    """
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


CONFIG = load_config()
