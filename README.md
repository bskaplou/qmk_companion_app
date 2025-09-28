# QmkLayoutWidget
Qmk layout visualiser frontend part

Details in this reddit post https://www.reddit.com/r/ErgoMechKeyboards/comments/1nofeb6/current_layer_tray_indicator_for_qmkvial_keyboards/

## MacOSX

MacOSX version lives in macosx directory.

### Development

Install dependencies

```
pip install -r requirements.txt
```

Check if keyboard supports protocol

```
python ProtocolTester.py
```

Build MacOSX app

```
python setup.py py2app
```

Run

```
python QmkLayoutWidget.py
```

### Build
```
python setup.py py2app
```

Also necessary to follow this advice to make it work https://github.com/ronaldoussoren/py2app/issues/533

## Crossplatform version

Crossplatform version lives in crossplatform directory

### Development

Install dependencies

```
pip install -r requirements.txt
```

Build MacOSX app

```
python -m nuitka --macos-create-app-bundle --static-libpython=no --macos-app-icon=icon.png --macos-app-mode=background --include-raw-dir=icons=icons --enable-plugin=pyside6 --macos-app-name=QmkLayoutWidget QmkLayoutWidget.py
```


Run

```
python QmkLayoutWidget.py
```

## Linux

Crossplatform version works with Linux well at least on my Raspberry Pi for now (I have no other linux desktops around sorry :( ).

Linux guys are pretty tech-savy usually so prebuilt package is not necessary here.

Python 3.11.9 is required because PySide6 is not ready for 3.12 at the moment :( It might by installed with pyenv for example.

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
