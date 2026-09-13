import sys

from .core import rz

print("\033[95m[SimpleSyntax] ReiZyuki Simple CSS-inspired Python media task library\033[0m")

sys.modules["simplesoup"] = sys.modules[__name__]

__all__ = ["rz"]
