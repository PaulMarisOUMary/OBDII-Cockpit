import logging

from os import environ
from pathlib import Path
from platform import system
from typing import Dict, Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from obdii import Command, commands


CONFIG_DIR = Path(__file__).parent / "config"
SYSTEM = system()


def _load_toml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def _deep_merge(base: Dict, override: Dict) -> Dict:
    result = base.copy()
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


config = _load_toml(CONFIG_DIR / "config.toml")

_is_dev = (
    config.get("dev", {}).get("force_dev_mode", False)
    or SYSTEM == "Windows"
)

if _is_dev:
    dev_config = _load_toml(CONFIG_DIR / "dev.config.toml")
    config = _deep_merge(config, dev_config)


for _key, _value in config.get("environ", {}).items():
    environ[_key] = str(_value)


_display = config.get("display", {})
_connection = config.get("connection", {})
_logging = config.get("logging", {})
_commands = config.get("commands", {})


WIDTH = _display.get("width", 1280)
HEIGHT = _display.get("height", 400)
FULLSCREEN_MODE = _display.get("fullscreen", True)
ROTATED_BY_90 = _display.get("rotated_by_90", True)
TARGET_FPS = _display.get("target_fps", 60)


SERIAL_PORT = _connection.get("serial_port", "/dev/ttyUSB0")


_level_str = _logging.get("level", "INFO").upper()
LOG_LEVEL = getattr(logging, _level_str, logging.INFO)


IS_DEV = _is_dev


DEFAULT_COMMANDS: Dict[Command, int] = {}
for _name, _freq in _commands.items():
    try:
        cmd = commands[1][_name]
        DEFAULT_COMMANDS[cmd] = _freq
    except KeyError:
        raise ValueError(f"Unknown command in config: '{_name}'.")