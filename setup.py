"""
pathosHax — py2app setup script
Usage:
    pip install py2app
    python setup.py py2app
"""
from setuptools import setup
import os

APP = ["run.py"]
DATA_FILES = []
ICON = "icon.icns" if os.path.exists("icon.icns") else None

OPTIONS = {
    "argv_emulation": False,
    "includes": ["tkinter", "tkinter.ttk", "tkinter.filedialog",
                 "tkinter.messagebox", "tkinter.simpledialog"],
    "packages": [],
    "plist": {
        "CFBundleName": "pathosHax",
        "CFBundleDisplayName": "pathosHax — Pathos Save Editor",
        "CFBundleIdentifier": "com.pathoshax.saveeditor",
        "CFBundleVersion": "3.0.0",
        "CFBundleShortVersionString": "3.0",
        "NSHighResolutionCapable": True,
        "NSHumanReadableCopyright": "pathosHax — MIT License",
    },
}

if ICON:
    OPTIONS["iconfile"] = ICON

setup(
    app=APP,
    name="pathosHax",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
