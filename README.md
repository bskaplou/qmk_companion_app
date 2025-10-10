# QMK companion app

Details in this reddit post https://www.reddit.com/r/ErgoMechKeyboards/comments/1nofeb6/current_layer_tray_indicator_for_qmkvial_keyboards/

## Firmware dependency

Companion applicaton should work only with keyboards with firmware compiled with module companion_hid from here https://github.com/bskaplou/qmk_modules

## Crossplatform version

Crossplatform version lives in directory 'crossplatform'

### Development

Install dependencies

NB please don't try to install dependencies through pacman/apt or other package manager, use pip. Use pyenv in case of pip problems.

Python 3.10 or newer is required.

```
pip install -r requirements.txt
```

Keyboard might be checked for compatibility with protocol_tester.py

Run

```
python QmkLayoutWidget.py
```

Build MacOSX app

```
python -m nuitka --macos-create-app-bundle \
           --static-libpython=no \
           --macos-app-icon=icons/app_icon.png \
           --macos-app-mode=background \
           --include-raw-dir=icons=icons \
           --enable-plugin=pyside6 \
           --macos-app-name=QmkLayoutWidget \
           --output-dir=build \
           QmkLayoutWidget.py

```

Assemble dmg image with MacOSX app

```
create-dmg --volname "QmkLayoutWidget Installer" \
        --window-size 800 400 \
        --icon "QmkLayoutWidget.app" 200 190 \
        --app-drop-link 600 185 \
        build/QmkLayoutWidget-Installer.dmg \
        build/QmkLayoutWidget.app
```



### App and layer icons

Icons are rendered from fonts because I'm not a designer. Icons can be created with any tool and should be put into icons directory to be used.
To add new icons with ttf font It's necessary to edit render_icons.py script.

Recreate existing icons with command

```
python render_icons.py
```

User might use own icons, to do so it's necessary to put them info configuration directory nearby the configuration.json file and write icon filename without an extension into configuration.json.

### MacOSX

Layers icons can be configured in file $HOME/Library/Preferences/QmkLayoutWidget/configuration.json after first launch.

### Linux

Crossplatform version works with Linux well at least on my Raspberry Pi for now (I have no other linux desktops around sorry :( ).

Linux guys are pretty tech-savy usually so prebuilt package is not necessary here.

Python 3.11.9 is required because PySide6 is not ready for 3.12 at the moment :( It might by installed with pyenv for example.

NB please don't try to install dependencies through pacman/apt or other package manager, use pip. Use pyenv in case of pip problems

Install dependencies

```
pip install -r requirements.txt
```

It's necessary to set suitable permissions on /dev/hidraw? device possibly with udev as described here https://get.vial.today/manual/linux-udev.html

Run

```
python QmkLayoutWidget.py
```

Logs are pretty detailed so if something works wrong please open the issue with description and logs attached.

Layers configuration might be updated in file $HOME/.config/QmkLayoutWidget/configuration.json which is created on first launch.

# Unicode characters with fallback and Vial support

Desktop component allows a wide range of new features and unicode character is just a simple example.

Qmk already has unicode support which is pretty complex to setup and system dependent.
https://docs.qmk.fm/features/unicode

Qmk unicode support is even called a "hack" sometimes.
https://getreuer.info/posts/keyboards/non-english/index.html#unicode-input

Current implementation expected to be less hacky.

## How it works and how to run it with QMK/Vial

QMK/Vial firmware compilation skill required to make it work.

Unicode characters are embedded into firmware.
They are embedded into two places:

* keymap.c - to add characters and ralated processing
* vial.json - to allow keymap configuration in vial

Current repository contains python script which creates both parts for unicode characters of your selection.

This script takes unicode characters as arguments and dumps code for both keymap.c and vial.json as a result.

It's necessary to put related peaces of code into keymap.c after the last include and into vial.json after first '{'. 

If you are using QMK without Vial, ignore vial.json part.

NB both companion_hid and qmk_companion_app required for full functionality.

It's not necessary to update OS keyboard settings, not necessary to add special unicode layout.

Vial will allow to assign unicode characters with "User" tab of tab "Keymap" after keyboard firmware update.

If keyboard with firmware which includes these changes is connected to computer with companion app user will be able just to push buttons and get unicode characters like 😁 and 😂.

If keyboard is connected to computer without companion app runing it will send fallback strings instead like : grin : and : joy : .

NB Such complex way setup is POC. If feature will be interested to community it will be possible to move whole the setup into Vial.

## Example

```
❯ python unicode_keymap/generator.py 😁 😂
===============  put following code into keymap.c ===============
#define SAFE_START QK_KB_0

enum unicode_keycodes {
    GRINNING_FACE_WITH_SMILING_EYES = SAFE_START,
    FACE_WITH_TEARS_OF_JOY,
};

const char* unisymbols[][2] = {
    {":grin:", (char*) U"\U0001F601"},
    {":joy:", (char*) U"\U0001F602"},
};


bool process_record_user(uint16_t keycode, keyrecord_t *record) {
  const char* fallback = unisymbols[keycode - SAFE_START][0];
  const uint32_t symbol = *((uint32_t*) unisymbols[keycode - SAFE_START][1]);
  if(keycode >= SAFE_START && keycode <= FACE_WITH_TEARS_OF_JOY) {
      if (record->event.pressed) {
          companion_hid_report_press(symbol, fallback);
      }
      return false;
  } else {
      return true;
  }
}

=============== put following code into vial.json ===============
    "customKeycodes": [
        {
            "name": "U+1F601",
            "title": "Grinning Face With Smiling Eyes",
            "shortName": "1F601"
        },
        {
            "name": "U+1F602",
            "title": "Face With Tears Of Joy",
            "shortName": "1F602"
        }
    ],
=================================================================
```

# Pointer operation with keayboard

This feature is called "touchboard" all around the code.


## How to prepare firmware
It's necessary put following string into the file keyboards/<your_keyboard>/keymaps/<your_keymap>/config.h

```
#define COMPANION_HID_TOUCHBOARD
```

For configuration with Vial it's necessary to run unicode_keymap/generator.py with option -t to create additional content for file keyboards/<your_keyboard>/keymaps/<your_keymap>/vial.json. This step is necessary to assign TB_MOVE, TB_1, TB_2 to user configured buttons in Vial.

Example

```
❯ python ../unicode_keymap/generator.py -t
===============  put following code into keymap.c ===============
# NOTHING to add into keymap.c, because of no unicode characters to map
=============== put following code into vial.json ===============
    "customKeycodes": [
        {
            "name": "Touchboard Move",
            "title": "TB_MOVE",
            "shortName": "TB_MOVE"
        },
        {
            "name": "Touchboard Left button",
            "title": "TB_1",
            "shortName": "TB_1"
        },
        {
            "name": "Touchboard Right button",
            "title": "TB_2",
            "shortName": "TB_2"
        }
    ],
=================================================================
```

If you need to use unicode characters and touchboard at once additional symbols might be passed to generator.py

```
❯ python ../unicode_keymap/generator.py -t 😂
===============  put following code into keymap.c ===============
enum unicode_keycodes {
    FACE_WITH_TEARS_OF_JOY = COMPANION_HID_SAFE_RANGE,
};

const char* unisymbols[][2] = {
    {":joy:", (char*) U"\U0001F602"},
};


bool process_record_user(uint16_t keycode, keyrecord_t *record) {
  if(keycode >= COMPANION_HID_SAFE_RANGE && keycode <= FACE_WITH_TEARS_OF_JOY) {
      const char* fallback = unisymbols[keycode - COMPANION_HID_SAFE_RANGE][0];
      const uint32_t symbol = *((uint32_t*) unisymbols[keycode - COMPANION_HID_SAFE_RANGE][1]);
      companion_hid_report_press(symbol, fallback, record);
      return false;
  } else {
      return true;
  }
}

=============== put following code into vial.json ===============
    "customKeycodes": [
        {
            "name": "Touchboard Move",
            "title": "TB_MOVE",
            "shortName": "TB_MOVE"
        },
        {
            "name": "Touchboard Left button",
            "title": "TB_1",
            "shortName": "TB_1"
        },
        {
            "name": "Touchboard Right button",
            "title": "TB_2",
            "shortName": "TB_2"
        },
        {
            "name": "U+1F602",
            "title": "Face With Tears Of Joy",
            "shortName": "1F602"
        }
    ],
=================================================================
```

Put generated code into related files.

## Layout setup

With QMK or Vial assign TB_* buttons on the layer of your choice.
For now TB_MOVE should be assigned to all buttons except last row. TB_1 and TB_2 should be assigned to the last row.

## Companion app configuration

It's necessaty to add key with number of layer which is used for navigation with touchboard as follows.

```
    "touchboard-layer": "5",

```

If keyboard uses Vial firmware app will load keymap directly from keyboard and build keymap labels.

For QMK firmware it's necessary to add keymap configuration in keymap-layout-editor format as in example below.

```
    "touchboard-keymap": [
      [
        {"y": 0.25}, "0,0", "0,1", {"y": -0.25}, "0,2", "0,3", {"y": 0.25}, "0,4", {"y": 0.25}, "0,5",
        {"x": 1.25}, "5,5", {"y": -0.25}, "5,4", {"y": -0.25}, "5,3", "5,2", {"y": 0.25}, "5,1", "5,0"
      ],
      [
        "1,0", "1,1", {"y": -0.25}, "1,2", "1,3", {"y": 0.25}, "1,4", {"y": 0.25}, "1,5", {"x": 1.25},
        "6,5", {"y": -0.25}, "6,4", {"y": -0.25}, "6,3", "6,2", {"y": 0.25}, "6,1", "6,0"
      ],
      [
        "2,0", "2,1", {"y": -0.25}, "2,2", "2,3", {"y": 0.25}, "2,4", {"y": 0.25}, "2,5",
        {"x": 1.25}, "7,5", {"y": -0.25}, "7,4", {"y": -0.25}, "7,3", "7,2", {"y": 0.25}, "7,1", "7,0"
      ],
      [
        "3,0","3,1", {"y": -0.25}, "3,2", "3,3", {"y": 0.25}, "3,4", {"y": 0.25}, "3,5",
        {"x": 1.25}, "8,5", {"y": -0.25}, "8,4", {"y": -0.25}, "8,3", "8,2", {"y": 0.25}, "8,1", "8,0"
      ]
    ],
    "touchboard-keymap-labels": {
      "0,0": "\u238b",
      "0,1": "1",
      "0,2": "2",
      "0,3": "3",
      "0,4": "4",
      "0,5": "5",
      "5,5": "6",
      "5,4": "7",
      "5,3": "8",
      "5,2": "9",
      "5,1": "0",
      "5,0": "-",
      "1,0": "\u21e5",
      "1,1": "Q",
      "1,2": "W",
      "1,3": "E",
      "1,4": "R",
      "1,5": "T",
      "6,5": "Y",
      "6,4": "U",
      "6,3": "I",
      "6,2": "O",
      "6,1": "P",
      "6,0": "=",
      "2,0": "Fn",
      "2,1": "A",
      "2,2": "S",
      "2,3": "D",
      "2,4": "F",
      "2,5": "G",
      "7,5": "H",
      "7,4": "J",
      "7,3": "K",
      "7,2": "L",
      "7,1": ";",
      "7,0": "'",
      "3,0": "\u21e7",
      "3,1": "Z",
      "3,2": "X",
      "3,3": "C",
      "3,4": "V",
      "3,5": "B",
      "8,5": "N",
      "8,4": "M",
      "8,3": ",",
      "8,2": ".",
      "8,1": "/",
      "8,0": "\u21e7",
      "4,3": "\u2303",
      "4,4": "\u2325",
      "4,5": "\u2318",
      "9,5": "\u2423",
      "9,4": "\u23ce",
      "9,3": "\u2318"
    }
```
