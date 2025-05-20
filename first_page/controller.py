from PySide6.QtGui import QPixmap
from PySide6.QtCore import QPoint
from .regions import ClickableRegions
from PySide6.QtCore import Qt
from pathlib import Path
from app_settings import *

# Get the directory of the current script
BASE_DIR = Path(__file__).resolve().parent


class FirstPageController:
    def __init__(self, view):
        self.view = view
        self.img1 = str(BASE_DIR / "images/f.png")
        self.img2 = str(BASE_DIR / "images/b.png")
        self.pixmap1 = QPixmap(self.img1).scaledToWidth(
            int(W_RATIO*340), Qt.SmoothTransformation)
        self.pixmap2 = QPixmap(self.img2).scaledToWidth(
            int(W_RATIO*340), Qt.SmoothTransformation)

        self.show_img1 = True

    def toggle_image(self):
        """Toggle between images and return the new pixmap"""
        self.show_img1 = not self.show_img1
        return self.pixmap1 if self.show_img1 else self.pixmap2
