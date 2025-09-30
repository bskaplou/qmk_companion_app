#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pynput.keyboard import Key, Controller
import copykitten
import time

keyboard = Controller()

original = copykitten.paste()
copykitten.copy("The 🐈 says meow")
keyboard.press(Key.cmd_l)
keyboard.press("v")
keyboard.release("v")
keyboard.release(Key.cmd_l)
time.sleep(0.01)
copykitten.copy(original)
