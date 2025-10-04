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
from PySide6.QtGui import QIcon, QAction, QGuiApplication
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtCore import (
    Signal,
    QRunnable,
    QThreadPool,
    Slot,
    QObject,
    QStandardPaths,
    QSysInfo,
    Qt,
)

from pprint import pp

from pynput.keyboard import Key, Controller
import copykitten

logging.basicConfig(encoding="utf-8", level=logging.DEBUG)
log = logging.getLogger(__name__)

keyboard = Controller()

device = None
stop = False


def process_loop(callback_state, callback_wait, callback_select_device, callback_press):
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
                if state is None:
                    protocol.close(device)
                else:
                    current_layer, caps_word = state
                    callback_state(current_layer, caps_word)

                    while True:
                        try:
                            message = protocol.recv(device)
                            if message is None:
                                protocol.close(device)
                                break
                            if message[0] == protocol.HID_LAYERS_OUT_STATE:
                                current_layer, caps_word = message[1], message[2]
                                callback_state(current_layer, caps_word)
                            elif message[0] == protocol.HID_LAYERS_OUT_PRESS:
                                symbol = message[1:5].decode("utf32")
                                callback_press(symbol)
                        except hid.HIDException as e:
                            log.error("hid receive error %s", device_info["path"])
                            break
        else:
            log.error("No candidate devices found. I'll wait and try later.")

        time.sleep(1)


APPLICATION_NAME = "QmkLayoutWidget"
CONFIG_FILE = "configuration.json"

DEFAULT_CONFIG = {
    "mode": "dark" if QSysInfo.kernelType() == "darwin" else "light",
    "icons": {
        "0": "default",
        "1": "navigation",
        "2": "pointer",
        "3": "numpad",
        "4": "emoji",
        "5": "gaming",
        "6": "symbols",
        "7": "shortcuts",
        "8": "media",
        "caps_word": "caps_word",
        "wait0": "wait0",
        "wait1": "wait1",
        "wait2": "wait2",
        "not_found": "not_found",
    },
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
    log.info("loading configuration from file %s", file_path)

    try:
        with open(file_path, "rb") as f:
            config = json.loads(f.read())
            config["config_directory"] = os.path.join(
                config_locations[0], APPLICATION_NAME
            )
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

        log.info("default config %s written feel free to edit", file_path)

        config = init_config()

    return config


class DevicesSignal(QObject):
    it = Signal(object)


wait_pos = 0


def setup_application(config):
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

    def emulate_keypress(symbol):
        try:
            original = copykitten.paste()
        except Exception as e:
            log.error("opykitten.paste %s", e)
            original = ""

        copykitten.copy(symbol)
        # FIXME imperical value and potentially reduces typing speed
        time.sleep(0.02)
        keyboard.press(Key.cmd_l)
        keyboard.press("v")
        keyboard.release("v")
        keyboard.release(Key.cmd_l)
        # FIXME imperical value and potentially reduces typing speed
        time.sleep(0.02)
        try:
            copykitten.copy(original)
        except Exception as e:
            log.error("opykitten.copy %s", e)

    wait_icon_names = list(
        filter(lambda i: i.startswith("wait"), config["icons"].keys())
    )

    devices_signal = DevicesSignal()

    app = QApplication([])

    icon_tail = "white"
    if config.get("mode", "dark").lower() == "light":
        icon_tail = "black"
    elif config.get("mode", "dark").lower() == "auto":
        os_color_scheme = QGuiApplication.styleHints().colorScheme()
        log.info("os color scheme detected: %s", os_color_scheme)
        if os_color_scheme == Qt.ColorScheme.Light:
            icon_tail = "black"
        elif os_color_scheme == Qt.ColorScheme.Dark:
            icon_tail = "white"
        else:
            icon_tail = "white"

    current_dir = Path(__file__).parent
    icons = {}
    for name, icon in config["icons"].items():
        app_icon_path = os.path.join(current_dir, "icons", f"{icon}_{icon_tail}.png")
        config_icon_path_tail = os.path.join(
            config["config_directory"], f"{icon}_{icon_tail}.png"
        )
        config_icon_path = os.path.join(config["config_directory"], f"{icon}.png")
        if os.path.isfile(app_icon_path):
            icons[name] = QIcon(app_icon_path)
            log.info("icon '%s' loaded from file '%s'", name, app_icon_path)
        elif os.path.isfile(config_icon_path):
            icons[name] = QIcon(config_icon_path)
            log.info("icon '%s' loaded from file '%s'", name, config_icon_path)
        elif os.path.isfile(config_icon_path_tail):
            icons[name] = QIcon(config_icon_path_tail)
            log.info("icon '%s' loaded from file '%s'", name, config_icon_path_tail)
        else:
            log.error(
                "failed to load icon '%s' from paths %s",
                name,
                [app_icon_path, config_icon_path, config_icon_path_tail],
            )

    app.setQuitOnLastWindowClosed(False)

    menu = QMenu()

    # I don't expect > 5 keyboards to be connected at once
    device_actions = []
    for da in range(5):
        a = QAction(str(da))
        device_actions.append(a)

    quit = QAction("Quit")
    quit.triggered.connect(shutdown)
    menu.addAction(quit)

    tray = QSystemTrayIcon()
    tray.setIcon(icons["wait0"])
    tray.setContextMenu(menu)
    tray.setVisible(True)

    pool = QThreadPool()
    pool.start(
        lambda: process_loop(
            update_state_icon, wait_for_device, select_device, emulate_keypress
        )
    )

    @Slot()
    def draw_devices_menu(devices):
        menu.clear()

        for idx, dev in enumerate(devices):
            da = device_actions[idx]

            label = f"{dev['product_string']} - {dev['path'].decode('utf8')}"
            if idx == 0:
                da.setText(f"✓ {label}")
            else:
                da.setText(f"  {label}")
                da.triggered.connect(shutdown)

            menu.addAction(da)

        menu.addSeparator()
        menu.addAction(quit)
        # pp(devices)

    devices_signal.it.connect(draw_devices_menu)

    app.exec()


setup_application(init_config())
