from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QBrush, QMouseEvent, QPainter, QColor, QPen, QPolygon
from PySide6.QtCore import QPoint, QRect, Qt


class ClickableRegions(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.click_regions = {
            "region1": [
                QPoint(194, 252), QPoint(198, 250), QPoint(202, 249),
                QPoint(208, 249), QPoint(213, 248), QPoint(219, 249),
                QPoint(222, 249), QPoint(225, 250), QPoint(227, 252),
                QPoint(229, 255), QPoint(230, 259), QPoint(230, 262),
                QPoint(230, 266), QPoint(230, 270), QPoint(230, 275),
                QPoint(229, 279), QPoint(228, 284), QPoint(227, 286),
                QPoint(224, 289), QPoint(221, 290), QPoint(218, 291),
                QPoint(214, 293), QPoint(211, 296), QPoint(208, 297),
                QPoint(205, 297), QPoint(200, 298), QPoint(197, 298),
                QPoint(194, 298), QPoint(190, 298), QPoint(187, 297),
                QPoint(185, 296), QPoint(182, 293), QPoint(179, 291),
                QPoint(178, 289), QPoint(177, 287), QPoint(176, 286),
                QPoint(175, 284), QPoint(173, 282), QPoint(176, 280),
                QPoint(179, 277), QPoint(182, 274), QPoint(183, 272),
                QPoint(186, 268), QPoint(189, 264), QPoint(191, 261),
                QPoint(193, 259), QPoint(193, 256), QPoint(194, 254),
                QPoint(194, 252), QPoint(197, 251), QPoint(199, 250)
            ],
        }

        self.selected_regions = set()  # Track clicked regions

    def mousePressEvent(self, event):
        click_pos = event.pos()
        for name, polygon in self.click_regions.items():
            if self.point_in_polygon(click_pos, polygon):
                # Toggle selection on click
                if name in self.selected_regions:
                    self.selected_regions.remove(name)
                else:
                    self.selected_regions.add(name)
                self.update()  # Trigger repaint
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
                # Compute intersection only if necessary
                xinters = (px0 - px1) * (y - py1) / (py0 - py1 + 1e-10) + px1
                if x < xinters:
                    inside = not inside

            px0, py0 = px1, py1

        return inside

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for name, polygon in self.click_regions.items():
            qpoly = QPolygon(polygon)
            if name in self.selected_regions:
                painter.setPen(QPen(QColor(255, 0, 100), 1))
                painter.setBrush(QBrush(QColor(255, 0, 0, 100)))
            else:
                painter.setPen(Qt.NoPen)  # Prevents drawing the polygon border
                painter.setBrush(Qt.NoBrush)
            painter.drawPolygon(qpoly)
