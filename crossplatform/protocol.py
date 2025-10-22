#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hid
import time
import logging
import json
import lzma
import struct

log = logging.getLogger(__name__)

# defined here https://github.com/vial-kb/vial-qmk/blob/vial/tmk_core/protocol/usb_descriptor_common.h
RAW_USAGE_PAGE = 0xFF60
RAW_USAGE_ID = 0x61

# protocol
HID_LAYERS_IN = 0x88
HID_LAYERS_OUT_STATE = 0x89
HID_LAYERS_OUT_PRESS = 0x90
HID_LAYERS_OUT_VERSION = 0x91
HID_LAYERS_OUT_ERROR = 0x92

GET_VERSION = 0x00
GET_LAYERS_STATE = 0x01
SET_REPORT_CHANGE = 0x02
INVERT_LAYER = 0x03
SET_REPORT_PRESS = 0x04

# raw hid specific
MESSAGE_LENGTH = 32

CMD_VIA_GET_PROTOCOL_VERSION = 0x01
CMD_VIA_VIAL_PREFIX = 0xFE
CMD_VIAL_GET_KEYBOARD_ID = 0x00
CMD_VIAL_GET_SIZE = 0x01
CMD_VIAL_GET_DEFINITION = 0x02
CMD_VIA_GET_LAYER_COUNT = 0x11
CMD_VIA_KEYMAP_GET_BUFFER = 0x12
VIA_UNHANDLED = 0xFF


def open(product_id, vendor_id, path):
    try:
        device = hid.Device(vid=vendor_id, pid=product_id, path=path)
        log.info("successfully opened device %s, %s, %s", product_id, vendor_id, path)
        return device
    except hid.HIDException as e:
        log.error(
            "failed to open device %s, %s, %s exception: %s",
            product_id,
            vendor_id,
            path,
            e,
        )
        return None


def close(device):
    if device is not None:
        log.info("closing device %s", device)
        device.close()


def candidates(raw_usage_page=RAW_USAGE_PAGE, raw_usage_id=RAW_USAGE_ID):
    candidates = []
    for dev in hid.enumerate():
        # if dev["usage_page"] == raw_usage_page and dev["usage"] == raw_usage_id and dev["product_id"] == 611:
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


def send(device, data, raw=False):
    request_data = [0x00] * (MESSAGE_LENGTH + 1)  # First byte is Report ID
    if not raw:
        request_data[1] = HID_LAYERS_IN
        request_data[2 : len(data)] = data
    else:
        request_data[1 : len(data)] = data

    request = bytes(request_data)

    return device.write(request)


def recv(device, timeout=None, raw=False):
    response = device.read(MESSAGE_LENGTH, timeout=timeout)
    if len(response) == 0:
        log.info("read timeout")
        return None
    elif raw or (
        response[0] >= HID_LAYERS_OUT_STATE and response[0] <= HID_LAYERS_OUT_ERROR
    ):
        return response
    else:
        log.error("non-protocol HID message received %s", response)
        return None


def send_recv(device, data, raw=False, retries=5):
    while retries > 0:
        send(device, data, raw=raw)
        response = recv(device, timeout=500, raw=raw)
        if response is not None:
            return response
        retries = retries - 1
        log.error("empty response retries = %s", retries)
        if retries > 0:
            time.sleep(0.5)

    return None


def enable_reporting_and_get_state(device):
    log.info("sending GET_LAYERS_STATE")
    response = send_recv(device, [GET_LAYERS_STATE])
    if response is None:
        return None

    if response[3] != 0:
        log.info(
            "layer reporting is enabled %s, presses are enabled %s, current layer %s, caps word %s",
            response[3],
            response[4],
            response[1],
            response[2],
        )
        state = response[1], response[2]  # layer num, caps sword
    else:
        log.info("layer reporting is not enabled %s, will enable it now", response[2])
        response = send_recv(device, [SET_REPORT_CHANGE, 1])
        if response is None:
            return None
        if response[3] != 1:
            log.error("failed to enable layer reporting, dig deeper!")
            return None

        log.info(
            "layer reporting successfully enabled %s, presses are enabled %s, current layer %s, caps word %s",
            response[3],
            response[4],
            response[1],
            response[2],
        )
        state = response[1], response[2]

    if response[4] != 0:
        log.info("report press already enabled %s", response[4])
    else:
        log.info("report press is not enabled %s, will enable it now", response[4])
        response = send_recv(device, [SET_REPORT_PRESS, 1])
        if response is None:
            return None
        if response[4] != 1:
            log.error("failed to enable press reporting, dig deeper!")
            return None

        log.info("press reporting is successfully enabled %s", response[4])

    return state


def disable_reporting(device):
    log.info("disabling reporting")
    send(device, [SET_REPORT_CHANGE, 0])
    send(device, [SET_REPORT_PRESS, 0])


def load_vial_meta(device):
    response = send_recv(device, [CMD_VIA_VIAL_PREFIX, CMD_VIAL_GET_SIZE], raw=True)
    if response is None:
        log.error("failed to load vial meta size with timeout")
        return None
    size = struct.unpack("<I", response[0:4])[0]
    log.info("vial_meta size of device %s is %s", device.product, size)
    remaining_size = size
    layout = b""
    block = 0
    while remaining_size > 0:
        data = send_recv(
            device,
            struct.pack("<BBI", CMD_VIA_VIAL_PREFIX, CMD_VIAL_GET_DEFINITION, block),
            raw=True,
        )
        if data is None:
            log.info("failed to load block %s of vial definition", block)
            return None
        if remaining_size < MESSAGE_LENGTH:
            data = data[:remaining_size]
        layout += data
        block += 1
        remaining_size -= MESSAGE_LENGTH

    log.info("successfully loaded vial meta definition")
    return json.loads(lzma.decompress(layout))


def load_layers_count(device):
    data_ok = False
    attempts = 5
    while not data_ok and attempts > 0:
        response = send_recv(device, [CMD_VIA_GET_LAYER_COUNT], raw=True)
        if response is None:
            return None
        data_ok = response[0] == CMD_VIA_GET_LAYER_COUNT
        if not data_ok:
            attempts = attempts - 1
            log.error(
                "corrupted data received from keyboard %s during load_layers_count attempts remaining %s",
                response,
                attempts,
            )

    if response is None:
        log.error("failed to load layers count")
        return None
    layers_count = response[1]
    log.info("loaded layers count %s", layers_count)
    return layers_count


BUFFER_FETCH_CHUNK = 28


def load_layers_keymaps(device, layers, rows, cols, keys):
    size = layers * rows * cols * 2
    log.info("loading layers/keymaps of size %s", size)
    keymap = b""
    for x in range(0, size, BUFFER_FETCH_CHUNK):
        offset = x
        sz = min(size - offset, BUFFER_FETCH_CHUNK)
        data_ok = False
        attempts = 5
        while not data_ok and attempts > 0:
            data = send_recv(
                device,
                struct.pack(">BHB", CMD_VIA_KEYMAP_GET_BUFFER, offset, sz),
                raw=True,
            )
            data_ok = data is not None and data[0] == CMD_VIA_KEYMAP_GET_BUFFER
            if not data_ok:
                attempts = attempts - 1
                log.error(
                    "corrupted data received from keyboard %s during load_layers_keymaps attempts remaining %s",
                    data,
                    attempts,
                )

        if not data_ok:
            log.error("failed to load layers/keymaps")
            return None

        keymap += data[4 : 4 + sz]

    log.info("successfully loaded layers/keymaps")

    layers_keymaps = []
    for layer in range(layers):
        keydict = {}
        for key in keys:
            row, col = list(map(int, key.split(",")))
            offset = layer * rows * cols * 2 + row * cols * 2 + col * 2
            keycode = struct.unpack(">H", keymap[offset : offset + 2])[0]
            keydict[key] = keycode

        layers_keymaps.append(keydict)

    return layers_keymaps


def discover_capabilities(device):
    info = {}
    response = send_recv(device, [CMD_VIA_GET_PROTOCOL_VERSION], raw=True)
    if response is None:
        info["via"] = None
    else:
        info["via"] = response[2]

    response = send_recv(
        device, [CMD_VIA_VIAL_PREFIX, CMD_VIAL_GET_KEYBOARD_ID], raw=True
    )
    if response is None or response[0] == VIA_UNHANDLED:
        info["vial"] = None
    else:
        info["vial"] = (
            (response[3] << 24) + (response[2] << 16) + (response[1] << 8) + response[0]
        )

    response = send_recv(device, [GET_VERSION])
    if response is None or response[0] != HID_LAYERS_OUT_VERSION:
        info["companion_hid"] = None
    else:
        info["companion_hid"] = response[1]

    return info
