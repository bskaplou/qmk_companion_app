#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

APP = ["QmkLayoutWidget.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "LSUIElement": True,
    },
    "packages": ["rumps", "hid"],
    "iconfile": "icon.png",
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
