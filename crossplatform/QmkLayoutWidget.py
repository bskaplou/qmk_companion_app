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
from PySide6.QtCore import Signal, QRunnable, QThreadPool, Slot, QObject, QStandardPaths

from pprint import pp

logging.basicConfig(encoding="utf-8", level=logging.DEBUG)
log = logging.getLogger(__name__)


device = None
stop = False


def process_loop(callback_state, callback_wait, callback_select_device):
    global device
    while not stop:
        callback_wait()
        candidates = protocol.candidates()
        if len(candidates) > 0:
            active_device_index = callback_select_device(candidates)
            device_info = candidates[active_device_index]
            device = protocol.open(
                device_info["vendor_id"], device_info["product_id"], device_info["path"]
            )
            if device is not None:
                state = protocol.enable_reporting_and_get_state(device)
                if state is not None:
                    current_layer, caps_word = state
                    callback_state(current_layer, caps_word)

                    while True:
                        try:
                            message = protocol.recv(device)
                            if message is None:
                                protocol.close(device)
                                break
                            current_layer, caps_word = message[0], message[1]
                            callback_state(current_layer, caps_word)
                        except hid.HIDException as e:
                            log.error("hid receive error %s", device_info["path"])
                            break
        else:
            log.error("No candidate devices found. I'll wait and try later.")

        time.sleep(1)


APPLICATION_NAME = "QmkLayoutWidget"
CONFIG_FILE = "configuration.json"

DEFAULT_CONFIG = {
    "icons": {
        "0": "default.png",
        "1": "navigation.png",
        "2": "pointer.png",
        "3": "numpad.png",
        "4": "gaming.png",
        "5": "symbols.png",
        "caps_word": "caps_word.png",
        "wait0": "wait0.png",
        "wait1": "wait1.png",
        "wait2": "wait2.png",
        "not_found": "not_found.png",
    }
}


def init_config():
    config = None
    file_path = None

    config_locations = QStandardPaths.standardLocations(
        QStandardPaths.StandardLocation.AppConfigLocation
    )
    if config_locations is None or len(config_locations) < 1:
        log.error("config dir not found, using default config")
        return DEFAULT_CONFIG

    file_path = os.path.join(config_locations[0], APPLICATION_NAME, CONFIG_FILE)

    try:
        with open(file_path, "rb") as f:
            return json.loads(f.read())
    except FileNotFoundError as e:
        log.info(
            'configuration file "%s" not found, I\'ll try to create it', e.filename
        )

    if config is None:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            f.write(
                json.dumps(
                    DEFAULT_CONFIG,
                    indent=4,
                    ensure_ascii=False,
                )
            )

        log.info("default config written feel free to edit")

        return init_config()


class DevicesSignal(QObject):
    it = Signal(object)


wait_pos = 0


def setup_application(config):
    devices_signal = DevicesSignal()

    def shutdown():
        global stop
        log.info("shutting down app")
        app.quit()
        log.info("shutting down device connection")
        stop = True
        protocol.close(device)
        log.info("app should quit now")

    def select_device(candidates):
        devices_signal.it.emit(candidates)
        return 0

    wait_icon_names = list(
        filter(lambda i: i.startswith("wait"), config["icons"].keys())
    )

    def wait_for_device():
        global wait_pos
        tray.setIcon(icons[wait_icon_names[wait_pos]])
        wait_pos = (wait_pos + 1) % len(wait_icon_names)

    def update_state_icon(layer, caps_word):
        layer = str(layer)
        if caps_word != 0:
            tray.setIcon(icons["caps_word"])
        elif layer in icons:
            tray.setIcon(icons[layer])
        else:
            tray.setIcon(icons["not_found"])

    app = QApplication([])

    current_dir = Path(__file__).parent
    icons = {}
    for name, icon in config["icons"].items():
        icons[name] = QIcon(os.path.join(current_dir, "icons", icon))

    app.setQuitOnLastWindowClosed(False)

    @Slot()
    def draw_devices_menu(devices):
        # pp(devices)
        pass

    menu = QMenu()

    menu.addSection("Devices")
    menu.addSeparator()
    quit = QAction("Quit")
    quit.triggered.connect(shutdown)
    menu.addAction(quit)

    tray = QSystemTrayIcon()
    tray.setIcon(icons["wait0"])
    tray.setContextMenu(menu)
    tray.setVisible(True)

    def worker():
        process_loop(update_state_icon, wait_for_device, select_device)

    threadpool = QThreadPool()
    threadpool.start(worker)

    devices_signal.it.connect(draw_devices_menu)

    app.exec()


setup_application(init_config())
