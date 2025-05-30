from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from first_page.regions import ClickableRegions
from first_page.controller import FirstPageController
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize
from first_page.history_page.history_window import HistoryPage
from first_page.plan_page.plan_window import PlanePage
from app_settings import *

from pathlib import Path

# Get the directory of the current script
BASE_DIR = Path(__file__).resolve().parent


class FirstPageView(QWidget):
    exit_requested = Signal()

    def __init__(self):
        super().__init__()
        self.controller = FirstPageController(self)
        self.history_page = None
        self.plan_page = None
        self._init_ui()

    def _init_ui(self):
        # Image label
        # Assuming ClickableRegions is a QLabel subclass
        self.image_label = ClickableRegions()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setPixmap(self.controller.pixmap1)
        self.image_label.mother = self
        self.image_label.setParent(self)
        self.image_label.move(int(70*W_RATIO), int(30*H_RATIO))
        # self.image_label.resize(int(480*W_RATIO), int(640*H_RATIO))
        print(self.image_label.size())

        # Special button setup
        self.change_btn = QPushButton(self)
        self.change_btn.setIcon(
            QIcon(str(BASE_DIR / 'images/rotp.png')))
        self.change_btn.setStyleSheet(change_btn)
        self.change_btn.move(int(10*W_RATIO), int(450*H_RATIO))
        self.change_btn.clicked.connect(self.toggle_image)

        self.hist_btn = QPushButton(self)
        self.hist_btn.setIcon(
            QIcon(str(BASE_DIR / 'images/hist.png')))
        self.hist_btn.setStyleSheet(hist_btn)
        self.hist_btn.move(int(140*W_RATIO), int(680*H_RATIO))
        self.hist_btn.clicked.connect(self.show_history_page)

        self.plan_btn = QPushButton(self)
        self.plan_btn.setIcon(
            QIcon(str(BASE_DIR / 'images/plan.png')))
        self.plan_btn.setStyleSheet(plan_btn)
        self.plan_btn.move(int(250*W_RATIO), int(680*H_RATIO))
        self.plan_btn.clicked.connect(self.show_plan_page)

        self.btn3 = QPushButton("Workout Plan")

    def toggle_image(self):
        """Handle button click to toggle image"""
        new_pixmap = self.controller.toggle_image()
        self.image_label.setPixmap(new_pixmap)
        self.image_label.face = (self.image_label.face + 1) % 2
        self.image_label.update()

    def show_history_page(self):
        if not self.history_page:
            self.history_page = HistoryPage(parent=self)
            self.history_page.exit_requested.connect(self.hide_history_page)
        self.history_page.show()
        self.history_page.raise_()

    def hide_history_page(self):
        if self.history_page:
            self.history_page.hide()

    def show_plan_page(self):
        if not self.plan_page:
            self.plan_page = PlanePage(parent=self)
            self.plan_page.exit_requested.connect(self.hide_plan_page)
        self.plan_page.show_machines()
        self.plan_page.show()
        self.plan_page.raise_()

    def hide_plan_page(self):
        if self.plan_page:
            self.plan_page.hide()


change_btn = f"""
            QPushButton {{
                border: none;
                background-color: transparent;
                icon: url(first_page/images/rotp.png);
                icon-size: {int(50*W_RATIO)}px {int(50*H_RATIO)}px;
            }}
            QPushButton:pressed {{
                icon: url({(BASE_DIR / 'images/rotpc2.png').resolve().as_posix()});
            }}
        """

plan_btn = f"""
            QPushButton {{
                border: none;
                background-color: transparent;
                icon: url(first_page/images/hist.png);
                icon-size: {int(90*W_RATIO)}px {int(130*H_RATIO)}px;
            }}
            QPushButton:pressed {{
                icon: url({(BASE_DIR / 'images/histc.png').resolve().as_posix()});
            }}
        """

hist_btn = f"""
            QPushButton {{
                border: none;
                background-color: transparent;
                icon: url(first_page/images/date.png);
                icon-size: {int(90*W_RATIO)}px {int(130*H_RATIO)}px;
            }}
            QPushButton:pressed {{
                icon: url({(BASE_DIR / 'images/datep.png').resolve().as_posix()});
            }}
        """
