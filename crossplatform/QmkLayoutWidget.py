#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import time
import hid
import protocol
import json
import logging
from pathlib import Path
import os.path
import random
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

logging.basicConfig(encoding="utf-8", level=logging.DEBUG)
log = logging.getLogger(__name__)


device = None
stop = False


def process_loop(callback_state, callback_wait):
    global device
    while not stop:
        callback_wait()
        candidates = protocol.candidates()
        if len(candidates) > 0:
            active_device_index = 0
            device_info = candidates[active_device_index]
            device = protocol.open(
                device_info["vendor_id"], device_info["product_id"], device_info["path"]
            )
            if device is None:
                # TODO implement search loop
                exit(1)

            state = protocol.enable_reporting_and_get_state(device)
            if state is None:
                # TODO implement search loop
                exit(1)

            current_layer, caps_word = state
            callback_state(current_layer, caps_word)

            while True:
                try:
                    message = protocol.recv(device)
                    current_layer, caps_word = message[0], message[1]
                    callback_state(current_layer, caps_word)
                except hid.HIDException as e:
                    log.error("hid receive error %s", device_info["path"])
                    break
        else:
            log.error("No candidate devices found. I'll wait and try later.")
            time.sleep(1)


wait_pos = 0


def icon_updater(tray, iconset):
    wait_icon_names = list(filter(lambda i: i.startswith("wait"), iconset.keys()))

    def wait_for_device():
        global wait_pos
        tray.setIcon(iconset[wait_icon_names[wait_pos]])
        wait_pos = (wait_pos + 1) % len(wait_icon_names)

    def update(layer, caps_word):
        layer = str(layer)
        if caps_word != 0:
            tray.setIcon(iconset["caps_word"])
        elif layer in iconset:
            tray.setIcon(iconset[layer])
        else:
            tray.setIcon(iconset["not_found"])

    process_loop(update, wait_for_device)


icons_names = [
    "default",
    "navigation",
    "pointer",
    "numpad",
    "gaming",
    "symbols",
    "caps_word",
    "wait0",
    "wait1",
    "wait2",
    "not_found",
]

app = QApplication([])

current_dir = Path(__file__).parent
icons = {}
for idx, icon in enumerate(icons_names):
    icons[icon] = QIcon(os.path.join(current_dir, "icons", f"{icon}.png"))
    icons[str(idx)] = icons[icon]

app.setQuitOnLastWindowClosed(False)

tray = QSystemTrayIcon()
tray.setIcon(icons["wait0"])
tray.setVisible(True)

menu = QMenu()


def shutdown():
    global stop
    log.info("shutting down app")
    app.quit()
    log.info("shutting down python")
    stop = True
    protocol.close(device)


quit = QAction("Quit")
quit.triggered.connect(shutdown)
menu.addAction(quit)

# Add the menu to the tray
tray.setContextMenu(menu)

threading.Thread(target=icon_updater, args=(tray, icons)).start()

app.exec()
