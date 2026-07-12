import config

from pygame import (
    display,
    font,
    mouse,
    time as pg_time,
    transform,
    Surface,
    FULLSCREEN,
    MOUSEBUTTONDOWN,
    QUIT,
)
from pygame.event import get as get_events

def main() -> None:
    display.init()
    font.init()
    mouse.set_visible(False)

    screen = display.set_mode(
        (config.WIDTH, config.HEIGHT),
        FULLSCREEN if config.FULLSCREEN_MODE else 0
    )
    off_screen = Surface((config.WIDTH, config.HEIGHT))

    screen.fill((0, 0, 0))
    display.flip()

    from logs import setup_logging
    logger = setup_logging(level=config.LOG_LEVEL)
    logger.info("Dashboard starting up.")

    from blue_filter import BlueFilter
    blue_filter = BlueFilter(0.5)

    clock = pg_time.Clock()

    from obdii import Connection, at_commands
    default_commands = config.get_default_commands()

    conn = Connection(
        config.SERIAL_PORT,
        auto_connect=False,
        early_return=True,

        log_handler=None,

        timeout=1.0,
        write_timeout=1.0,
    )
    conn.init_sequence.extend(
        [
            at_commands.LINEFEED_OFF,
            at_commands.SET_TIMEOUT(10),
        ]
    )

    from storage import StorageUpdater
    from connection import ConnectionManager

    storage_updater = StorageUpdater(dict.fromkeys(default_commands, None))
    conn_manager = ConnectionManager(conn, storage_updater, logger, default_commands)

    from rendering import Dashboard
    dashboard = Dashboard()
    logger.info("Dashboard initialized.")

    needs_rotation = config.ROTATED_BY_90

    try:
        while True:
            dt = clock.tick(config.TARGET_FPS)

            for event in get_events():
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
        logger.info("Shutting down.")
    finally:
        conn_manager.stop()
        conn_manager.connection.close()
        quit()


if __name__ == "__main__":
    main()