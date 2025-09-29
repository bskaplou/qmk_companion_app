# QmkLayoutWidget
Qmk layout indicator frontend part

Details in this reddit post https://www.reddit.com/r/ErgoMechKeyboards/comments/1nofeb6/current_layer_tray_indicator_for_qmkvial_keyboards/

## Firmware dependency

Companion applicaton should work only with keyboards with firmware including module this https://github.com/bskaplou/companion_hid

## Crossplatform version

Crossplatform version lives in directory 'crossplatform'

### Development

Install dependencies

NB please don't try to install dependencies through pacman/apt or other package manager, use pip. Use pyenv in case of pip problems

Python 3.10 or newer is required.

```
pip install -r requirements.txt
```

Keyboard might be ckecked for compatibility with protocol_tester.py

Build MacOSX app

```
python -m nuitka --macos-create-app-bundle --static-libpython=no --macos-app-icon=icons/app_icon.png --macos-app-mode=background --include-raw-dir=icons=icons --enable-plugin=pyside6 --macos-app-name=QmkLayoutWidget QmkLayoutWidget.py
```

Run

```
python QmkLayoutWidget.py
```

### App and layer icons

Icons are renred from fonts because I'm not a designer. Icons can be created with any tool and should be put into icons directore to be used.
To add new icons with ttf font It's necessary to edit render_icons.py script.

Recreate existing icons

```
python render_icons.py
```

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
