#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import threading
import hid
import time
import rumps
import json
import logging

logging.basicConfig(encoding="utf-8", level=logging.DEBUG)
log = logging.getLogger(__name__)

# defined here https://github.com/vial-kb/vial-qmk/blob/vial/tmk_core/protocol/usb_descriptor_common.h
RAW_USAGE_PAGE = 0xFF60
RAW_USAGE_ID = 0x61

# protocol
HID_LAYERS_IN = 0x88
HID_LAYERS_OUT = 0x89
GET_LAYERS_STATE = 0x01
SET_REPORT_CHANGE = 0x02
INVERT_LAYER = 0x03

# raw hid specific
MESSAGE_LENGTH = 32

alpha = "Æ"
numpad = "¾"
pointer = "🐁"
navigation = "⇆"
caps_word = "🆎"

unknown = "❓"
device_not_found = "❌"
loading = "⌛"

DEFAULT_LAYERS_SYMBOLS = {
    "0": alpha,
    "1": navigation,
    "2": pointer,
    "3": numpad,
    "caps_word": caps_word,
}


def get_symbol(layer, caps_word, syms):
    layer = str(layer) if caps_word == 0 else "caps_word"
    if layer in syms:
        return syms[layer]

    return unknown


def hid_open(product_id, vendor_id, path):
    try:
        device = hid.Device(vid=vendor_id, pid=product_id, path=path)
        log.info("successfully opened device %s", path)
        return device
    except hid.HIDException as e:
        log.error("failed to open device %s %s", path, e)
        return None


def hid_close(device):
    if device is not None:
        log.info("closing device device %s", device)
        device.close()


def candidates(raw_usage_page=RAW_USAGE_PAGE, raw_usage_id=RAW_USAGE_ID):
    candidates = []
    for dev in hid.enumerate():
        if dev["usage_page"] == raw_usage_page and dev["usage"] == raw_usage_id:
            candidates.append(
                {
                    "path": dev["path"],
                    "vendor_id": dev["vendor_id"],
                    "product_id": dev["product_id"],
                    "path": dev["path"],
                    "product_string": dev["product_string"],
                    "manufacturer_string": dev["manufacturer_string"],
                }
            )

    return candidates


def send(device, data):
    request_data = [0x00] * (MESSAGE_LENGTH + 1)  # First byte is Report ID
    request_data[1] = HID_LAYERS_IN
    request_data[2 : len(data)] = data
    request = bytes(request_data)

    return device.write(request)


def recv(device, timeout=None):
    finish_before = round(time.time() * 1000) + (0 if timeout is None else timeout)

    while timeout is None or round(time.time() * 1000) < finish_before:
        timeout_remaining = (
            None if timeout is None else finish_before - round(time.time() * 1000)
        )
        response = device.read(MESSAGE_LENGTH, timeout=timeout_remaining)
        if len(response) == 0:
            log.info("read timeout")
            return None
        elif response[0] == HID_LAYERS_OUT:
            return response[1:]
        else:
            log.error("non-protocol HID message received %s", response)

    return None


def enable_reporting_and_get_current_layer(device):
    log.info("sending GET_LAYERS_STATE")
    send(device, [GET_LAYERS_STATE])
    response = recv(device, 500)
    if response is None:
        return None

    if response[2] != 0:
        log.info(
            "layer reporting is enabled %s, current layer %s, caps word %s",
            response[2],
            response[0],
            response[1],
        )
        return response[0], response[1]  # layer num
    else:
        log.info("layer reporting is not enabled %s, will enable it now", response[2])
        send(device, [SET_REPORT_CHANGE, 1])
        response = recv(device, 500)
        if response[2] != 1:
            log.error("failed to enable reporting, dig deeper!")
            return None

        log.info(
            "layer reporting successfully enabled %s, current layer %s, caps word %s",
            response[2],
            response[0],
            response[1],
        )
        return response[0], response[1]


def build_menu(menu, devices, active_device_index):
    # All these Quit jumps are to workaround rumps bug in clear which removes Quit as well
    for name in menu:
        if name != "Quit":
            del menu[name]

    for idx, device in enumerate(devices):
        item = f"{'✔️' if idx == active_device_index else ' '} {device['product_string']} {device['path'].decode('utf-8')}"
        if "Quit" in menu:
            menu.insert_before("Quit", rumps.MenuItem(item))
        else:
            menu.add(rumps.MenuItem(item))

    return menu


def monitor_device_layers(device_info, app, layers_symbols):
    device = hid_open(
        device_info["vendor_id"], device_info["product_id"], device_info["path"]
    )
    if device is None:
        # TODO implement search loop
        exit(1)

    message = enable_reporting_and_get_current_layer(device)
    if message is None:
        # TODO implement search loop
        exit(1)

    current_layer, caps_word = message
    app.title = get_symbol(current_layer, caps_word, layers_symbols)

    while True:
        try:
            message = recv(device)
            current_layer, caps_word = message[0], message[1]
            app.title = get_symbol(current_layer, caps_word, layers_symbols)
        except hid.HIDException as e:
            log.error("hid receive error %s", device_info["path"])
            return


def wait_for_candidates():
    devices = []
    while len(devices) == 0:
        devices = candidates()
        if len(devices) == 0:
            log.info("no suitable devices found. I'll sleep a bit and will try later.")
            time.sleep(1)
        else:
            return devices


def fill_app(app, config):
    devices = wait_for_candidates()
    while True:
        active_device_index = 0
        build_menu(app.menu, devices, active_device_index)
        monitor_device_layers(
            devices[active_device_index], app, config["layers_symbols"]
        )
        log.error(
            "device %s seems to be disconnected I will try to reinit a bit later...",
            devices[active_device_index]["path"],
        )
        app.title = loading
        devices = wait_for_candidates()


APPLICATION_NAME = "QmkLayoutWidget"
CONFIG_FILE = "configuration.json"


class QmkLayerStatusBarApp(rumps.App):
    pass


def init_config(app):
    config = None
    file_path = None

    try:
        with app.open(CONFIG_FILE, "rb") as f:
            return json.loads(f.read())
    except FileNotFoundError as e:
        log.info(
            'configuration file "%s" not found, I\'ll try to create it', e.filename
        )
        file_path = e.filename

    if config is None:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            f.write(
                json.dumps(
                    {
                        "layers_symbols": DEFAULT_LAYERS_SYMBOLS,
                    },
                    indent=4,
                    ensure_ascii=False,
                )
            )

        log.info("default config written feel free to edit")

        return init_config(app)


def run_app_and_hid_thread():
    # init app with no device asap to display something to user, content will be updated in separate thread
    app = QmkLayerStatusBarApp(APPLICATION_NAME, loading)
    config = init_config(app)
    threading.Thread(
        target=fill_app,
        args=(
            app,
            config,
        ),
    ).start()
    app.run()


run_app_and_hid_thread()
