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
    info = protocol.discover_capabilities(dd)
    log.info("capabilities discovered %s", info)
    protocol.send(dd, [protocol.GET_LAYERS_STATE])
    response = protocol.recv(dd, timeout=200)
    if response is None:
        log.error("failed to get GET_LAYERS_STATE response")
    else:
        log.info(
            "current layer: %s, caps_word: %s, report_enabled: %s",
            response[1],
            response[2],
            response[3],
        )
    protocol.close(dd)
