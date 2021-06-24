from .core import Movie
from .presets import rotating_globe


try:
    from ._version import __version__

except ModuleNotFoundError:
    __version__ = "unknown"


__all__ = ("Movie", "rotating_globe")
