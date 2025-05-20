from PySide6.QtWidgets import QMainWindow, QStackedWidget
from first_page.view import FirstPageView
from app_settings import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Mobile App")
        self.setFixedSize(W, H)  # Mobile-like size

        apply_gym_theme(self)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Initialize pages
        self.first_page = FirstPageView()
        self.stacked_widget.addWidget(self.first_page)

        # Connect signals
        self.first_page.exit_requested.connect(self.close)


def apply_gym_theme(window):
    window.setStyleSheet("""
        QMainWindow {
            background-color: #14172a; /* Dark background */
        }
    """)

# 14172a
