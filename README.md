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

Run

```
python widget_pystray.py
```


