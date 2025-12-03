from logging import getLogger
from logging.handlers import RotatingFileHandler

from config import DEFAULT_FETCH_COMMANDS, FULLSCREEN_MODE, HEIGHT, LOG_LEVEL, ROTATED_BY_90, SERIAL_PORT, SIMULATION, TARGET_FPS, WIDTH

from blue_filter import BlueFilter
from connection import ConnectionManager
from simulation import Simulator
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

    storage_updater = StorageUpdater(dict.fromkeys(DEFAULT_FETCH_COMMANDS.keys(), None))
    conn_manager = ConnectionManager(conn, storage_updater, _logger)

    # Dodge font not initialized error
    from rendering import Dashboard

    dashboard = Dashboard()
    if SIMULATION:
        simulator = Simulator()
    
    rotated_cache = None
    needs_rotation = ROTATED_BY_90

    try:
        while True:
            dt = clock.get_time() / 1000.0
            if dt > 0.1:
                dt = 0.1

            for event in get():
                if event.type == QUIT:
                    raise KeyboardInterrupt
                elif event.type == MOUSEBUTTONDOWN:
                    conn_manager.polling_error.set()

            conn_manager.ensure_polling()

            snapshot = storage_updater.copy()

            if SIMULATION:
                sim_values = simulator.update(dt) # type: ignore
                snapshot.update(sim_values)

            dashboard.draw(off_screen, snapshot, dt)

            if needs_rotation:
                if rotated_cache is None or rotated_cache.get_size() != (HEIGHT, WIDTH):
                    rotated_cache = Surface((HEIGHT, WIDTH))
                rotated_cache.blit(transform.rotate(off_screen, 90), (0, 0))
                screen.blit(rotated_cache, (0, 0))
            else:
                screen.blit(off_screen, (0, 0))

            blue_filter.apply(screen)

            display.flip()

            clock.tick(TARGET_FPS)

            # import pygame
            # pygame.image.save(screen, "dashboard.png")
            # break
    except KeyboardInterrupt: ...
    finally:
        conn_manager.stop()
        conn_manager.connection.close()
        quit()


if __name__ == "__main__":
    main()