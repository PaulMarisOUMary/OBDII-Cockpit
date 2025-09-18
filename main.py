from logging import DEBUG, INFO, getLogger
from logging.handlers import RotatingFileHandler

from pygame import MOUSEBUTTONDOWN, display, font, init, mouse, quit, time, FULLSCREEN, QUIT
from pygame.event import get
from threading import Event, Lock, Thread

from obdii import Connection, at_commands, commands

from polling import background_fetch

"""
On device replace the following:
- DEFAULT_SERIAL_PORT = "/dev/ttyUSB0"
- screen = display.set_mode((WIDTH, HEIGHT), FULLSCREEN)
"""


DEFAULT_SERIAL_PORT = "COM5" # "/dev/ttyUSB0"

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

WIDTH, HEIGHT = 1280, 400

storage = dict.fromkeys(DEFAULT_FETCH_COMMANDS, None)
storage_lock = Lock()

polling_stop = Event()
polling_error = Event()

file_handler = RotatingFileHandler(
    filename="obd_dash.log",
    maxBytes=32*1024*1024,
    backupCount=10,
)
obdii_logger = getLogger("obdii")

obd = Connection(DEFAULT_SERIAL_PORT, 
                # log_level=DEBUG,
                log_level=INFO,
                log_handler=file_handler,
                early_return=True,
                auto_connect=False,
            )
obd.init_sequence.extend(
    [
        at_commands.LINEFEED_OFF,
        at_commands.DLC_OFF,
        at_commands.SET_TIMEOUT(10),
    ]
)


fetch_thread = Thread(target=background_fetch, args=(obd, storage, storage_lock, polling_stop), daemon=True)

def ensure_polling() -> None:
    if polling_error.is_set() or not fetch_thread.is_alive():
        reconnect()

def reconnect() -> None:
    global fetch_thread

    print("Attempting to reconnect...")
    with storage_lock:
        obdii_logger.warning(f"Attempting to reconnect, storage: {storage.copy()}")


    if fetch_thread and fetch_thread.is_alive():
        polling_stop.set()
        fetch_thread.join()

    polling_stop.clear()
    polling_error.clear()
    obd.close()

    try:
        obd.connect()
    except ConnectionError:
        print("Reconnect failed.")
        obdii_logger.warning("Reconnect failed")
        return

    fetch_thread = Thread(
        target=background_fetch,
        args=(obd, storage, storage_lock, polling_stop, polling_error),
        daemon=True
    )
    fetch_thread.start()
    print("Reconnected and started polling thread.")

if __name__ == "__main__":
    init()
    font.init()
    screen = display.set_mode((WIDTH, HEIGHT), ) # display.set_mode((WIDTH, HEIGHT), FULLSCREEN)
    display.set_caption("OBDII Dashboard")
    mouse.set_visible(False)
    clock = time.Clock()

    from rendering import draw_dashboard

    try:
        while True:
            for event in get():
                if event.type == QUIT:
                    raise KeyboardInterrupt
                elif event.type == MOUSEBUTTONDOWN:
                    polling_error.is_set()

            ensure_polling()

            with storage_lock:
                snapshot = storage.copy()

            draw_dashboard(screen, snapshot)
            clock.tick(22) # Change to release CPU usage
            # import pygame
            # pygame.image.save(screen, "dashboard.png")
            # break

    except KeyboardInterrupt:
        print("Exiting...")

    finally:
        polling_stop.set()
        obd.close()
        quit()