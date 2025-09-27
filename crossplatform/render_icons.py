#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pictex import * 

icons = {
    'default': '\U000F030C',
    'navigation': '\U0000F0EC',
    'pointer': '\U000F037D',
    'numpad': '\U0000215B',
    'gaming': '\U000F0297',
    'caps_word': '\U000F030E',
    'wait': '\U0000F252',
    'not_found': '\U0000EEF9',
}

canvas = Canvas().font_family("UbuntuMonoNerdFontMono-Regular.ttf")
size = 44

for name, code in icons.items():
    box = Row(Text(code)
          .font_size(size)
          .color("white")).size(width=size, height=size).horizontal_distribution("center")

    image = canvas.render(box)

    image.save(f"icons/{name}.png")
