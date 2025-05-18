# day_details_window.py
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QPushButton,
                               QScrollArea, QHBoxLayout)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QIcon, QPixmap
import csv
from pathlib import Path

# Get the directory of the current script
BASE_DIR = Path(__file__).resolve().parent


class DayDetailsWindow(QWidget):
    exit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "background-color: rgba(0, 0, 0, 220); color: white;")
        self.setGeometry(parent.rect())
        self.setAttribute(Qt.WA_StyledBackground, True)

        # Back button setup
        self.back_btn = QPushButton(self)
        self.back_btn.setIcon(
            QIcon(str(BASE_DIR / '../../images/back2.png')))
        self.back_btn.setStyleSheet(back_btn)
        self.back_btn.move(10, 720)
        self.back_btn.clicked.connect(self.exit_requested.emit)

        # Scroll area setup
        self.scroll_area = QScrollArea(self)
        # Adjust height to fit above button
        self.scroll_area.setGeometry(0, 0, self.width(), 750)
        self.scroll_area.setWidgetResizable(True)

        # Content widget for scroll area
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)

    def show_history(self, date):
        # Clear previous content
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Get date in CSV format (adjust format as needed)
        date_str = date.toString("yyyy-MM-dd")

        # Read CSV file (update path to your CSV file)
        csv_path = str(
            BASE_DIR / "database/data.csv")
        try:
            with open(csv_path, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row.get('date') == date_str:
                        self._create_entry_widget(row)
        except FileNotFoundError:
            print("CSV file not found.")

    def _create_entry_widget(self, row_data):
        # Create widget for each entry
        widget = QWidget()
        # widget.setStyleSheet("margin: 5px; border-bottom: 1px solid gray;")
        layout = QHBoxLayout(widget)

        # Image from type (customize image paths as needed)
        image_label = QLabel()
        image_path = self._get_image_path(row_data['type'])
        pixmap = QPixmap(image_path).scaled(100, 100, Qt.KeepAspectRatio)
        image_label.setPixmap(pixmap)

        # Type and count labels
        type_label = QLabel(row_data['type'])
        count_label = QLabel(row_data['count'])

        layout.addWidget(image_label)
        layout.addWidget(type_label)
        layout.addWidget(count_label)
        self.scroll_layout.addWidget(widget)

    def _get_image_path(self, type_str):
        return str(BASE_DIR / f"images/{type_str}.png")


back_btn = f"""
    QPushButton {{
        border: none;
        background-color: transparent;
        icon-size: 50px 50px;
    }}
    QPushButton:pressed {{
        icon: url({BASE_DIR / '../../images/back2p.png'});
    }}
"""
