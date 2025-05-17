from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QBrush, QMouseEvent, QPainter, QColor, QPen, QPolygon
from PySide6.QtCore import QPoint, QRect, Qt
from first_page.regions_list import *
from first_page.muscle_history.muscle_history import MuscleHistory


class ClickableRegions(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.muscle_history = None
        self.mother = None

        self.face = 1
        self.click_regions1 = {
            "region1": region1
        }

        self.click_regions2 = {
            "region2": region2
        }

        self.update()

    def mousePressEvent(self, event):
        click_pos = event.pos()
        if self.face == 1:
            polygons = self.click_regions1.items()
        else:
            polygons = self.click_regions2.items()

        for name, polygon in polygons:
            if self.point_in_polygon(click_pos, polygon):
                self.on_polygon_clicked(name)

                break
        super().mousePressEvent(event)

    def point_in_polygon(self, point, polygon):
        x, y = point.x(), point.y()
        inside = False
        n = len(polygon)

        px0, py0 = polygon[-1].x(), polygon[-1].y()
        for i in range(n):
            px1, py1 = polygon[i].x(), polygon[i].y()

            if ((py1 > y) != (py0 > y)):
                xinters = (px0 - px1) * (y - py1) / (py0 - py1 + 1e-10) + px1
                if x < xinters:
                    inside = not inside

            px0, py0 = px1, py1

        return inside

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.face == 1:
            polygons = self.click_regions1.items()
        else:
            polygons = self.click_regions2.items()
        for name, polygon in polygons:
            qpoly = QPolygon(polygon)
            painter.setPen(QPen(QColor(255, 0, 100), 1))
            painter.setBrush(QBrush(QColor(255, 0, 0, 100)))
            painter.drawPolygon(qpoly)

    def on_polygon_clicked(self, name):
        if not self.muscle_history:
            self.muscle_history = MuscleHistory(parent=self.mother)
            self.muscle_history.exit_requested.connect(
                self.hide_details_window)
        self.muscle_history.show_machines(name)
        self.muscle_history.show()
        self.muscle_history.raise_()

    def hide_details_window(self):
        print('shet')
        if self.muscle_history:
            self.muscle_history.hide()
