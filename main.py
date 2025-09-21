from logging import getLogger
from logging.handlers import RotatingFileHandler

from config import DEFAULT_FETCH_COMMANDS, FULLSCREEN_MODE, HEIGHT, LOG_LEVEL, ROTATED_BY_90, SERIAL_PORT, WIDTH
from blue_light import apply_blue_filter, get_strength_by_time
from connection import ConnectionManager
from storage import StorageUpdater

from pygame import MOUSEBUTTONDOWN, Surface, display, font, init, mouse, quit, time, transform, FULLSCREEN, QUIT
from pygame.event import get

from obdii import Connection, at_commands

def main() -> None:
    init()
    font.init()
    mouse.set_visible(False)
    display.set_caption("OBDII Dashboard")

    screen = display.set_mode(
        (WIDTH, HEIGHT),
        FULLSCREEN if FULLSCREEN_MODE else 0
    )
    off_screen = Surface((WIDTH, HEIGHT))

    clock = time.Clock()

    file_handler = RotatingFileHandler(
        filename="obd_dash.log",
        maxBytes=32*1024*1024,
        backupCount=10,
    )
    _logger = getLogger("obdii")

    conn = Connection(
        SERIAL_PORT,
        log_level=LOG_LEVEL,
        log_handler=file_handler,
        early_return=True,
        auto_connect=False,

        timeout=1.0,
        write_timeout=1.0,
    )
    conn.init_sequence.extend(
        [
            at_commands.LINEFEED_OFF,
            at_commands.DLC_OFF,
            at_commands.SET_TIMEOUT(10),
        ]
    )

    storage_updater = StorageUpdater(dict.fromkeys(DEFAULT_FETCH_COMMANDS, None))
    conn_manager = ConnectionManager(conn, storage_updater, _logger)

    # Dodge font not initialized error
    from rendering import draw_dashboard

    try:
        while True:
            for event in get():
                if event.type == QUIT:
                    raise KeyboardInterrupt
                elif event.type == MOUSEBUTTONDOWN:
                    conn_manager.polling_error.set()

            conn_manager.ensure_polling()

            snapshot = storage_updater.copy()

            draw_dashboard(off_screen, snapshot)

            if ROTATED_BY_90:
                rotated = transform.rotate(off_screen, 90)
                screen.blit(rotated, (0, 0))
            else:
                screen.blit(off_screen, (0, 0))

            apply_blue_filter(screen, 1)

            display.flip()

            clock.tick(30)
    except KeyboardInterrupt: ...
    finally:
        conn_manager.polling_stop.set()
        conn_manager.connection.close()
        quit()


if __name__ == "__main__":
    main()