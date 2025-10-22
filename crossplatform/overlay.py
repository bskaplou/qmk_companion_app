import math
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QMargins, QRect, QPoint, QSysInfo
from PySide6.QtWidgets import QHBoxLayout, QWidget


# FIXME kle seems to be more complex, some ready and tested lib required here
def keymap_to_positions(keymap, move_buttons_positions):
    buttons = {}
    x_margin = 0.25
    x_pos = 0
    y_pos = 0
    x_mod = 0
    y_mod = 0
    max_x, max_y, min_x, min_y = 0, 0, 1000, 1000
    for row, line in enumerate(keymap):
        height = 1
        width = 1
        for col, data in enumerate(line):
            if isinstance(data, dict):
                if "x" in data:
                    x_mod = x_mod + data["x"]
                if "y" in data:
                    y_mod = y_mod + data["y"]
                if "h" in data:
                    height = height + data["h"]
                if "w" in data:
                    width = data["w"]
            else:
                x = x_pos + x_mod + width / 2
                y = y_pos + y_mod + height / 2
                if (
                    move_buttons_positions is not None
                    and data in move_buttons_positions
                ):
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    buttons[data] = (
                        x,
                        y,
                        width,
                    )

                x_pos = x_pos + x_mod + width

                width = 1
                height = 1

                x_mod = 0

        x_pos = 0
        y_pos = y_pos + 1

    aligned_buttons = {}
    for pos, button in buttons.items():
        aligned_buttons[pos] = (
            button[0] - min_x + 0.5 + x_margin,
            button[1] - min_y + 0.5,
            button[2],
        )

    return aligned_buttons, max_x - min_x + 0.5 + x_margin * 2, max_y - min_y + 0.5


class Window(QWidget):

    def __init__(self, app):
        super().__init__()
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setWindowOpacity(0.5)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint, True)
        self.setWindowFlag(QtCore.Qt.NoDropShadowWindowHint, True)
        self.setWindowFlag(Qt.WindowType.ToolTip, True)
        self.app = app

        self.label = QtWidgets.QLabel()
        self.keymap_labels = None

        lo = QHBoxLayout()
        lo.setContentsMargins(QMargins(0, 0, 0, 0))
        lo.addWidget(self.label)
        self.setLayout(lo)

    def set_keymap(self, keymap, move_buttons_positions=None):
        self.buttons, self.max_x, self.max_y = keymap_to_positions(
            keymap, move_buttons_positions
        )

    def set_keymap_labels(self, labels):
        self.keymap_labels = labels

    def draw_initial(self):
        self.step = 0
        self.step_scale = 2.5
        self.width, self.height = self.app.primaryScreen().size().toTuple()
        self.setGeometry(0, 0, self.width, self.height)
        self.draw_overlay(0, 0, self.width, self.height)

    def draw_overlay(self, left, top, width, height):
        if QSysInfo.kernelType() == "darwin":
            # Retina!
            canvas = QtGui.QPixmap(self.width * 2, self.height * 2)
            canvas.setDevicePixelRatio(2)
            # End of retina
        else:
            canvas = QtGui.QPixmap(self.width, self.height)

        canvas.fill(Qt.white)

        painter = QtGui.QPainter(canvas)

        label_pen = QtGui.QPen()
        label_pen.setWidth(max(1, math.ceil(4 - self.step)))
        label_pen.setColor(Qt.black)
        painter.setPen(label_pen)
        # painter.drawPoint(left + width /2, top + height / 2) # debug

        scale_x = width / (self.max_x + 0.3)
        scale_y = height / (self.max_y + 0.3)
        shift_x = -scale_x / 8
        shift_y = -scale_y / 4
        dot_size = 0.45 * scale_x
        rounding = dot_size * 0.4

        if self.step < 3:
            font = painter.font()
            font.setPixelSize(dot_size * 2 * 0.6)
            painter.setFont(font)

        self.button_coordinates = {}
        for pos, (x, y, w) in self.buttons.items():
            pos_x = left + shift_x + x * scale_x
            pos_y = top + shift_y + y * scale_y
            self.button_coordinates[pos] = (
                pos_x,
                pos_y,
            )
            point = QRect(
                QPoint(pos_x - dot_size * w, pos_y - dot_size),
                QPoint(pos_x + dot_size * w, pos_y + dot_size),
            )
            path = QtGui.QPainterPath()
            path.addRoundedRect(point, rounding, rounding)
            painter.fillPath(path, Qt.gray)

            if self.keymap_labels is not None and self.step < 3:
                # if len(self.keymap_labels) > row and len(self.keymap_labels[row]) > col:
                if self.keymap_labels.get(pos) is not None:
                    painter.drawText(
                        pos_x - dot_size,
                        pos_y - dot_size,
                        dot_size * 2,
                        dot_size * 2,
                        Qt.AlignCenter,
                        self.keymap_labels[pos],
                    )

        painter.end()
        self.label.setPixmap(canvas)

    def mousePressEvent(self, event):
        self.hide()

    def dive(self, row, col):
        key = f"{row},{col}"
        x, y = self.button_coordinates[key]
        self.step = self.step + 1
        width = self.width / (self.step_scale**self.step)
        height = self.height / (self.step_scale**self.step)
        self.draw_overlay(x - width / 2, y - height / 2, width, height)

        # FIXME 26 is strange macosx constant
        return x, y + 26

    def mouseDoubleClickEvent(self, event):
        self.hide()
