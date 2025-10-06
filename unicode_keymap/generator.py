#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unicodedata
import sys
import json
from pathlib import Path
import os

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

    # TARGET FORMAT
    #
    # enum unicode_keycodes {
    #   GRINNING_FACE = SAFE_START,
    #   FROWNING_FACE,
    # };
    #
    # const char* unisymbols[][2] = {
    #     {":-)", (char*) U"\U0001F600"},
    #     {"'=D", (char*) U"\U0001F605"},
    #     {">:)", (char*) U"\U0001F605"},
    # };

    #    "customKeycodes": [
    # 	      {
    #            "name": "Grinning face",
    # 	          "title": "Grinning face",
    # 	          "shortName": "UNC_GF"
    # 	      },
    # 	      {
    #            "name": "Sweating face",
    # 	          "title": "Grinning face with sweat",
    # 	          "shortName": "UNC_SF"
    # 	      }
    #    ],
    process_function = """
bool process_record_user(uint16_t keycode, keyrecord_t *record) {
  const char* fallback = unisymbols[keycode - SAFE_START][0];
  const uint32_t symbol = *((uint32_t*) unisymbols[keycode - SAFE_START][1]);
  if(keycode >= SAFE_START && keycode <= %s) {
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

    symbols = sorted(set(sys.argv[1:]))
    for idx, symbol in enumerate(symbols):
        if len(symbol) > 1 and symbol[0].lower() == "u":
            if len(symbol) % 2 == 0:
                symbol = "u0" + symbol[1:]

            symbol_bytes = list((bytes([0, 0, 0]) + bytes.fromhex(symbol[1:]))[-4:])
            symbol = str(bytes(list(reversed(symbol_bytes))), "utf32")
        else:
            symbol_bytes = list(reversed(bytes(symbol, "utf32")[4:]))

        symbol_hex = []
        for byte in symbol_bytes:
            symbol_hex.append("%0.2X" % byte)

        symbol_char = "U" + "".join(symbol_hex)

        title = unicodedata.name(symbol).title()
        constant = title.upper().replace(" ", "_").replace("-", "_")

        if symbol in emojis:
            fallback = emojis[symbol]
        else:
            fallback = ":" + title.lower().replace(" ", "_").replace("-", "_") + ":"

        short_name = "".join(symbol_hex).lstrip("0")
        name = "U+" + short_name

        if idx == 0:
            unicode_keycodes = unicode_keycodes + f"    {constant} = SAFE_START,\n"
        else:
            unicode_keycodes = unicode_keycodes + f"    {constant},\n"

        unisymbols = unisymbols + f'    {{"{fallback}", (char*) U"\\{symbol_char}"}},\n'

        vial_keycodes = (
            vial_keycodes
            + f'        {{\n            "name": "{name}",\n            "title": "{title}",\n            "shortName": "{short_name}"\n        }},\n'
        )

    unicode_keycodes = unicode_keycodes + "};\n"
    unisymbols = unisymbols + "};\n"
    vial_keycodes = vial_keycodes[0:-2] + "\n    ],"

    print("===============  put following code into keymap.c ===============")
    print("#define SAFE_START QK_KB_0\n")
    print(unicode_keycodes)
    print(unisymbols)
    print(process_function % constant)
    print("=============== put following code into vial.json ===============")
    print(vial_keycodes)
    print("=================================================================")
