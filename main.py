from logging import getLogger
from logging.handlers import RotatingFileHandler

from pygame import MOUSEBUTTONDOWN, Surface, display, font, init, mouse, quit, time, transform, FULLSCREEN, QUIT
from pygame.event import get
from threading import Event, Lock, Thread

from obdii import Connection, at_commands

from config import DEFAULT_FETCH_COMMANDS, FULLSCREEN_MODE, HEIGHT, LOG_LEVEL, ROTATED_BY_90, SERIAL_PORT, WIDTH
from polling import background_fetch


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

obd = Connection(SERIAL_PORT,
                log_level=LOG_LEVEL,
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
    screen = display.set_mode((WIDTH, HEIGHT), FULLSCREEN) if FULLSCREEN_MODE else display.set_mode((WIDTH, HEIGHT))

    offscreen = Surface((WIDTH, HEIGHT))

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

            draw_dashboard(offscreen, snapshot)

            if ROTATED_BY_90:
                rotated = transform.rotate(offscreen, 90)
                screen.blit(rotated, (0, 0))
            else:
                screen.blit(offscreen, (0, 0))

            display.flip()

            clock.tick(30) # Change to release CPU usage
            # import pygame
            # pygame.image.save(screen, "dashboard.png")
            # break

    except KeyboardInterrupt:
        print("Exiting...")

    finally:
        polling_stop.set()
        obd.close()
        quit()