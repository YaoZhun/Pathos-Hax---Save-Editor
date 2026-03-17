#!/usr/bin/env python3
"""
pathosHax — Pathos: Nethack Codex Save Editor
Entry point for both direct execution and py2app packaging.
"""
import os
os.environ["TK_SILENCE_DEPRECATION"] = "1"

from view import PathosView
from controller import PathosController

if __name__ == "__main__":
    view = PathosView()
    ctrl = PathosController(view)
    view.mainloop()
