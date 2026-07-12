from datetime import datetime
from logging import getLogger, Formatter, Logger, StreamHandler, INFO
from logging.handlers import RotatingFileHandler


def setup_logging(level: int = INFO) -> Logger:
    filename = datetime.now().strftime("obd_%m-%d-%y.log")
    file_handler = RotatingFileHandler(
        filename=filename,
        maxBytes=32 * 1024 * 1024,
        backupCount=15,
    )

    formatter = Formatter(
        fmt="{relativeCreated:>9.0f}ms {asctime} {levelname:<5} {name}: {message}",
        datefmt="%m-%d-%y %H:%M:%S",
        style='{'
    )
    file_handler.setFormatter(formatter)

    console_handler = StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)

    dashboard_logger = getLogger("dashboard")
    dashboard_logger.addHandler(console_handler)

    return dashboard_logger