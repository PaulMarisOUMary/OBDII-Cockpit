from logging import DEBUG, INFO
from os import environ
from platform import system

from obdii import commands

SYSTEM = system()

WIDTH, HEIGHT = 1280, 400
FULLSCREEN_MODE = True
ROTATED_BY_90 = True

LOG_LEVEL = INFO

SERIAL_PORT = "/dev/ttyUSB0"

environ["PYGAME_HIDE_SUPPORT_PROMPT"] = '1'

DEFAULT_FETCH_COMMANDS = {
    commands.VEHICLE_SPEED.name,
    commands.ENGINE_SPEED.name,
    commands.ENGINE_LOAD.name,

    # commands.ENGINE_OIL_TEMP.name,
    commands.ENGINE_COOLANT_TEMP.name,
    # commands.INTAKE_AIR_TEMP.name,

    # commands.BAROMETRIC_PRESSURE.name,
    # commands.INTAKE_PRESSURE.name,
}

if SYSTEM == "Windows":
    SERIAL_PORT = "COM9"
    ROTATED_BY_90 = False
    FULLSCREEN_MODE = False
    LOG_LEVEL = DEBUG

elif SYSTEM == "Linux":
    environ["SDL_VIDEODRIVER"] = "KMSDRM"
    environ["SDL_KMSDRM_DEVICE"] = "/dev/dri/card0"

    LOG_LEVEL = DEBUG
