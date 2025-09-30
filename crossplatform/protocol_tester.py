#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import logging
import protocol
from pprint import pformat

logging.basicConfig(encoding="utf-8", level=logging.DEBUG)
log = logging.getLogger(__name__)

devs = protocol.candidates()
for dev in devs:
    log.info("Testing device: \n%s", pformat(dev))
    dd = protocol.open(dev["vendor_id"], dev["product_id"], dev["path"])
    protocol.send(dd, [protocol.GET_VERSION])
    response = protocol.recv(dd)
    protocol.send(dd, [protocol.GET_LAYERS_STATE])
    response = protocol.recv(dd)
    log.info(
        "current layer: %s, caps_word: %s, report_enabled: %s",
        response[0],
        response[1],
        response[2],
    )
    protocol.close(dd)
