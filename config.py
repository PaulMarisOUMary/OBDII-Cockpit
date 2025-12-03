from logging import DEBUG, INFO
from os import environ
from platform import system
from typing import Dict

from obdii import Command, commands

SYSTEM = system()

TARGET_FPS = 60
WIDTH, HEIGHT = 1280, 400
FULLSCREEN_MODE = True
ROTATED_BY_90 = True

LOG_LEVEL = INFO

SERIAL_PORT = "/dev/ttyUSB0"

environ["PYGAME_HIDE_SUPPORT_PROMPT"] = '1'

DEFAULT_COMMANDS: Dict[Command, int] = {
    commands.VEHICLE_SPEED: 1,
    commands.ENGINE_SPEED: 1,
    commands.ENGINE_LOAD: 1,

    # commands.ENGINE_OIL_TEMP,
    commands.ENGINE_COOLANT_TEMP: 10,
    # commands.INTAKE_AIR_TEMP,

    # commands.BAROMETRIC_PRESSURE,
    # commands.INTAKE_PRESSURE,
}

if SYSTEM == "Windows":
    SERIAL_PORT = "COM10"
    ROTATED_BY_90 = False
    FULLSCREEN_MODE = False

    LOG_LEVEL = DEBUG

elif SYSTEM == "Linux":
    environ["SDL_VIDEODRIVER"] = "KMSDRM"
    environ["SDL_KMSDRM_DEVICE"] = "/dev/dri/card0"

    LOG_LEVEL = DEBUG
