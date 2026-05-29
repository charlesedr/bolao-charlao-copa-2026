import logging
import sys

_configured = False


def get_logger(name: str = "bolao") -> logging.Logger:
    global _configured
    if not _configured:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s | %(message)s")
        )
        root = logging.getLogger("bolao")
        root.setLevel(logging.INFO)
        root.addHandler(handler)
        _configured = True
    return logging.getLogger(name if name.startswith("bolao") else f"bolao.{name}")
