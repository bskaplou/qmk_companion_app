#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hid
import time
import logging

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


def open(product_id, vendor_id, path):
    try:
        device = hid.Device(vid=vendor_id, pid=product_id, path=path)
        log.info("successfully opened device %s", path)
        return device
    except hid.HIDException as e:
        log.error("failed to open device %s %s", path, e)
        return None


def close(device):
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

def enable_reporting_and_get_state(device):
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
