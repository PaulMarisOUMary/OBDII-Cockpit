from datetime import datetime
from logging import getLogger, Formatter
from logging.handlers import RotatingFileHandler

from config import DEFAULT_COMMANDS, FULLSCREEN_MODE, HEIGHT, LOG_LEVEL, ROTATED_BY_90, SERIAL_PORT, TARGET_FPS, WIDTH

from blue_filter import BlueFilter
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

    blue_filter = BlueFilter(0.5)

    clock = time.Clock()

    filename = datetime.now().strftime("obd_%m-%d-%y.log")
    file_handler = RotatingFileHandler(
        filename=filename,
        maxBytes=32*1024*1024,
        backupCount=15,
    )
    formatter = Formatter(
        fmt="{asctime} {levelname:<5} {name}: {message}",
        datefmt="%m-%d-%y %H:%M:%S",
        style='{'
    )
    _logger = getLogger("obdii")

    conn = Connection(
        SERIAL_PORT,
        auto_connect=False,
        early_return=True,

        log_handler=file_handler,
        log_formatter=formatter,
        log_level=LOG_LEVEL,

        timeout=1.0,
        write_timeout=1.0,
    )
    conn.init_sequence.extend(
        [
            at_commands.LINEFEED_OFF,
            at_commands.SET_TIMEOUT(10),
        ]
    )

    storage_updater = StorageUpdater(dict.fromkeys(DEFAULT_COMMANDS, None))
    conn_manager = ConnectionManager(conn, storage_updater, _logger)

    # Dodge font not initialized error
    from rendering import Dashboard

    dashboard = Dashboard()

    needs_rotation = ROTATED_BY_90

    try:
        while True:
            dt = clock.tick(TARGET_FPS)

            for event in get():
                if event.type == QUIT:
                    raise KeyboardInterrupt
                elif event.type == MOUSEBUTTONDOWN:
                    conn_manager.polling_error.set()

            conn_manager.ensure_polling()

            snapshot = storage_updater.copy()

            dashboard.draw(off_screen, snapshot, dt)

            if needs_rotation:
                screen.blit(transform.rotate(off_screen, 90), (0, 0))
            else:
                screen.blit(off_screen, (0, 0))

            blue_filter.apply(screen)

            display.flip()

            # import pygame
            # pygame.image.save(screen, "dashboard.png")
            # break
    except KeyboardInterrupt:
        _logger.info("Shutting down.")
    finally:
        conn_manager.stop()
        conn_manager.connection.close()
        quit()


if __name__ == "__main__":
    main()