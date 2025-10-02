# QmkLayoutWidget
Qmk layout indicator frontend part

Details in this reddit post https://www.reddit.com/r/ErgoMechKeyboards/comments/1nofeb6/current_layer_tray_indicator_for_qmkvial_keyboards/

## Firmware dependency

Companion applicaton should work only with keyboards with firmware including module this https://github.com/bskaplou/companion_hid

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

Qmk unicode support is even called a hach sometimes.
https://getreuer.info/posts/keyboards/non-english/index.html#unicode-input

Current implementation expected to be less hacky.

## How it works and how to run it work

Vial firmware compilation skill required to make it work.

Unicode characters are embedded into firmware.
They are embedded into two places:

* keymap.c - to add characters and ralated processing
* vial.json - to allow keymap configuration in vial

Current repository contains python script which creates both parts for unicode characters of your selection.

This script takes unicode characters as arguments and dumps code for both keymap.c and vial.json as a result.

It's necessary to put related peaces of code into keymap.c after the last include and into vial.json after first '{'

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
  if(keycode >= SAFE_START) {
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
