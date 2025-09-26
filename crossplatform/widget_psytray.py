#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import time
import hid
import pystray
import protocol
import json
import logging
from pprint import pp
from PIL import Image, ImageDraw

logging.basicConfig(encoding="utf-8", level=logging.DEBUG)
log = logging.getLogger(__name__)


def process_loop(callback):
    while True:
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
            callback(current_layer, caps_word)

            while True:
                try:
                    message = protocol.recv(device)
                    current_layer, caps_word = message[0], message[1]
                    callback(current_layer, caps_word)
                except hid.HIDException as e:
                    log.error("hid receive error %s", device_info["path"])
                    break 
        else:
            log.error("No candidate devices found. I'll wait and try later.")
            time.sleep(1)


#process_loop(lambda l, c: log.info(f"layer: {l}, caps_word: {c}"))

def icon_updater(icon, iconset):
    def update(layer, caps_word):
        layer = str(layer)
        if caps_word != 0:
            icon.icon = iconset['caps_word']
        elif layer in iconset:
            icon.icon = iconset[layer]
        else:
            icon.icon = iconset['not_found']


    process_loop(update)

icons_names = [
    'default',
    'navigation',
    'pointer',
    'numpad',
    'gaming',
    'caps_word',
    'wait',
    'not_found',
]

icons = {}
for idx, icon in enumerate(icons_names):
    icons[icon] = Image.open(f"icons/{icon}.png")
    icons[str(idx)] = icons[icon]

icon = pystray.Icon(
   'AE',
   icon=icons['wait']
)

threading.Thread(target=icon_updater,args=(icon, icons)).start()


icon.run()
