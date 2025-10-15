#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unicodedata
import sys
import json
from pathlib import Path
import os

TOUCHBOARD_BUTTONS = {
    "🐁": {
        "name": "Touchboard Move",
        "shortName": "TB_MOVE",
        "title": "Touchboard pointer move button",
    },
    "←": {
        "name": "Touchboard Left button",
        "shortName": "TB_1",
        "title": "Touchboard left button",
    },
    "→": {
        "name": "Touchboard Right button",
        "shortName": "TB_2",
        "title": "Touchboard right button",
    },
}

current_dir = Path(__file__).parent
emojilist_path = os.path.join(current_dir, "emojilist.txt")

emojis = {}
with open(emojilist_path, "r") as f:
    for line in f.readlines():
        sym, sc = line.split(" ")
        if sym not in emojis:
            emojis[sym] = sc[6:-8]

if len(sys.argv) == 1:
    print(json.dumps(emojis, indent=4, ensure_ascii=False))
else:
    process_function = """
bool process_record_user(uint16_t keycode, keyrecord_t *record) {
  if(keycode >= COMPANION_HID_SAFE_RANGE && keycode <= %s) {
      const char* fallback = unisymbols[keycode - COMPANION_HID_SAFE_RANGE][0];
      const uint32_t symbol = *((uint32_t*) unisymbols[keycode - COMPANION_HID_SAFE_RANGE][1]);
      companion_hid_report_press(symbol, fallback, record);
      return false;
  } else {
      return true;
  }
}
"""

    unicode_keycodes = "enum unicode_keycodes {\n"
    unisymbols = "const char* unisymbols[][2] = {\n"
    vial_keycodes = '    "customKeycodes": [\n'

    if sys.argv[1] in (
        "-t",
        "--touchboard",
    ):
        symbols = list(TOUCHBOARD_BUTTONS.keys()) + sorted(set(sys.argv[2:]))
        gen_touchboard = True
    else:
        symbols = sorted(set(sys.argv[1:]))
        gen_touchboard = False

    for idx, symbol in enumerate(symbols):
        if len(symbol) > 1 and symbol[0].lower() == "u":
            if len(symbol) % 2 == 0:
                symbol = "u0" + symbol[1:]

            symbol_bytes = list((bytes([0, 0, 0]) + bytes.fromhex(symbol[1:]))[-4:])
            symbol = str(bytes(list(reversed(symbol_bytes))), "utf32")
        else:
            # FIXME multisymbol unicode is not supported, might be implemented through several symbols ans macros for now
            if len(symbol) > 1:
                symbol = symbol[0]

            symbol_bytes = list(reversed(bytes(symbol, "utf32")[4:]))

        symbol_hex = []
        for byte in symbol_bytes:
            symbol_hex.append("%0.2X" % byte)

        symbol_char = "U" + "".join(symbol_hex)

        if symbol in TOUCHBOARD_BUTTONS:
            tb = TOUCHBOARD_BUTTONS[symbol]
            title = tb["shortName"]
            constant = tb["shortName"]
            short_name = tb["shortName"]
            name = tb["name"]
            fallback = tb["name"]
        else:

            title = unicodedata.name(symbol).title()
            constant = title.upper().replace(" ", "_").replace("-", "_")

            if symbol in emojis:
                fallback = emojis[symbol]
            else:
                fallback = ":" + title.lower().replace(" ", "_").replace("-", "_") + ":"

            if symbol.isascii():
                short_name = symbol
            elif len(title) > 6:
                short_name = "".join(symbol_hex).lstrip("0")
            else:
                short_name = title
            name = "U+" + "".join(symbol_hex).lstrip("0")

        if (idx == 0 and not gen_touchboard) or (idx == 3 and gen_touchboard):
            unicode_keycodes = (
                unicode_keycodes + f"    {constant} = COMPANION_HID_SAFE_RANGE,\n"
            )
            unisymbols = (
                unisymbols + f'    {{"{fallback}", (char*) U"\\{symbol_char}"}},\n'
            )
        elif not gen_touchboard or idx > 3:
            unicode_keycodes = unicode_keycodes + f"    {constant},\n"
            unisymbols = (
                unisymbols + f'    {{"{fallback}", (char*) U"\\{symbol_char}"}},\n'
            )

        vial_keycodes = (
            vial_keycodes
            + f'        {{\n            "name": "{name}",\n            "title": "{title}",\n            "shortName": "{short_name}"\n        }},\n'
        )

    unicode_keycodes = unicode_keycodes + "};\n"
    unisymbols = unisymbols + "};\n"
    vial_keycodes = vial_keycodes[0:-2] + "\n    ],"

    print("===============  put following code into keymap.c ===============")
    if len(unicode_keycodes) > 32:
        print(unicode_keycodes)
        print(unisymbols)
        print(process_function % constant)
    else:
        print("# NOTHING to add into keymap.c, because of no unicode characters to map")
    print("=============== put following code into vial.json ===============")
    print(vial_keycodes)
    print("=================================================================")
