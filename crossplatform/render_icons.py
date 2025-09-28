#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pictex import *

icons = {
    #'default': '\U000F030C',
    #'default': '\U000F09FA',
    "default": "\U000f132e",
    # "default": "\U000004d4",
    "navigation": "\U0000f0ec",
    "pointer": "\U000f037d",
    "numpad": "\U0000215b",
    # 'gaming': '\U000F0297',
    "gaming": "\U000f0eb5",
    "shortcuts": "\U000f1935",
    "media": "\U000f127a",
    # 'caps_word': '\U000F030E',
    "caps_word": "\U000f0a9b",
    "symbols": "\U00002248",
    "wait0": "\U0000f251",
    "wait1": "\U0000f252",
    "wait2": "\U0000f253",
    "not_found": "\U0000eef9",
}

canvas = Canvas().font_family("UbuntuMonoNerdFontMono-Regular.ttf")
size = 44

back_colors = ["white", "black"]

for name, code in icons.items():
    for bc in back_colors:
        box = (
            Row(Text(code).font_size(size * 1.4).color(bc).position("center", "center"))
            # .background_color("red")
            .size(width=size, height=size).horizontal_distribution("center")
        )

        image = canvas.render(box, crop_mode=CropMode.CONTENT_BOX)

        image.save(f"icons/{name}_{bc}.png")
