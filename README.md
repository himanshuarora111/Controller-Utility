# Controller Utility Starter

A simple Windows desktop controller utility.

## Features

- Normal desktop window, not just overlay
- Controller detection and live input display
- Mouse mode on/off
- Optional app startup with Windows
- Optional auto-start Mouse Mode when app opens
- Vibration test and continuous vibration
- Stellaris combo cheat sheet

## Install

```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Build EXE later
```bat
pip install pyinstaller
pyinstaller --noconsole --onefile --name ControllerUtility app.py
```
