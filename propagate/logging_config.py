import logging
import os

_APP_NAME = "propagate"


def setup_logging() -> None:
    root = logging.getLogger(_APP_NAME)
    root.setLevel(logging.INFO)

    if root.handlers:
        return

    fmt = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    log_path = os.environ.get("PROPAGATE_LOG_LOCATION", "./propagate.log")

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    root.addHandler(stream)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(
        f"{_APP_NAME}.{name}" if not name.startswith(_APP_NAME) else name
    )
