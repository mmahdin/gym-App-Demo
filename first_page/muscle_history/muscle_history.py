# day_details_window.py
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QPushButton,
                               QScrollArea, QHBoxLayout)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QIcon, QPixmap
import csv
from datetime import datetime, date


class MuscleHistory(QWidget):
    exit_requested = Signal()

    muscles2machine = {
        'region1': ['Barbell', 'Chest press'],
        'region2': ['Dumbbell']
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "background-color: rgba(0, 0, 0, 245); color: white;")
        self.setGeometry(parent.rect())
        self.setAttribute(Qt.WA_StyledBackground, True)

        # Back button setup
        self.back_btn = QPushButton(self)
        self.back_btn.setIcon(
            QIcon('/home/mahdi/Documents/sensor/ux/first_page/images/back2.png'))
        self.back_btn.setStyleSheet(back_btn)
        self.back_btn.move(10, 760)
        self.back_btn.clicked.connect(self.exit_requested.emit)

        # Scroll area setup
        self.history_scroll_area = QScrollArea(self)
        self.history_scroll_area.setGeometry(0, 0, self.width(), 500)
        self.history_scroll_area.setWidgetResizable(True)

        # Content widget for scroll area
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.history_scroll_area.setWidget(self.scroll_content)
        self.history_scroll_area.move(1, 30)

        self.history_label = QLabel(
            "Your workout history for this muscle", self)
        self.history_label.setStyleSheet(
            "color: white; font-size: 18px; font-weight: bold;")
        self.history_label.setAlignment(Qt.AlignCenter)
        self.history_label.move(10, 10)

    def show_machines(self, region):

        self.show_history(region)

        path = "/home/mahdi/Documents/sensor/ux/first_page/history_page/day_details/images/{}.png"
        # Retrieve the list of machines for the given region
        machines = self.muscles2machine.get(region, [])

        # Remove existing scroll area if present
        if hasattr(self, 'scroll_area'):
            self.scroll_area.deleteLater()

        # Create a new scroll area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setGeometry(0, 0, self.width(), self.height() - 650)
        self.scroll_area.setWidgetResizable(True)
        # self.scroll_area.setStyleSheet("background-color: transparent;")

        # Create container widget with vertical layout
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        self.scroll_area.setWidget(container)
        layout = QHBoxLayout(container)

        # Load and display images for each machine
        # Load and display images with names for each machine
        for machine in machines:
            image_path = path.format(machine)
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                print(f"Image not found: {image_path}")
                continue

            # Create a vertical layout for image and label
            machine_widget = QWidget()
            machine_layout = QVBoxLayout(machine_widget)
            machine_layout.setContentsMargins(5, 5, 5, 5)
            machine_layout.setAlignment(Qt.AlignCenter)

            # Image label
            image_label = QLabel()
            image_label.setPixmap(pixmap.scaledToWidth(
                100, Qt.SmoothTransformation))
            image_label.setAlignment(Qt.AlignCenter)

            # Text label
            name_label = QLabel(machine)
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setStyleSheet("color: white; font-size: 14px;")

            # Add image and text to layout
            machine_layout.addWidget(image_label)
            machine_layout.addWidget(name_label)

            layout.addWidget(machine_widget)

        # Add stretch to push content to the top
        layout.addStretch()
        self.scroll_area.show()
        self.scroll_area.move(10, 570)

        self.instruction_label = QLabel(
            "Choose a machine to work this muscle", self)
        self.instruction_label.setStyleSheet(
            "color: white; font-size: 18px; font-weight: bold;")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.move(10, 560)

    def show_history(self, region):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        path = "/home/mahdi/Documents/sensor/ux/first_page/history_page/day_details/database/data.csv"

        try:
            with open(path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                if region not in self.muscles2machine:
                    print(f"Region '{region}' not found in muscles2machine.")
                    return

                valid_types = self.muscles2machine[region]
                valid_rows = [
                    row for row in reader if row['type'] in valid_types]
                valid_rows.sort(key=lambda row: datetime.strptime(
                    row['date'], "%Y-%m-%d"), reverse=True)
                for row in valid_rows:
                    self._create_entry_widget(row)
        except FileNotFoundError:
            print(f"CSV file '{path}' not found.")
        except Exception as e:
            print(f"Error reading CSV: {e}")

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

        target_date = datetime.strptime(row_data['date'], "%Y-%m-%d").date()
        today = date.today()
        delta = (today - target_date).days

        day_label = QLabel(f'{delta} day ago')

        layout.addWidget(image_label)
        layout.addWidget(type_label)
        layout.addWidget(count_label)
        layout.addWidget(day_label)
        self.scroll_layout.addWidget(widget)

    def _get_image_path(self, type_str):
        return f"/home/mahdi/Documents/sensor/ux/first_page/history_page/day_details/images/{type_str}.png"


back_btn = """
    QPushButton {
        border: none;
        background-color: transparent;
        icon-size: 50px 50px;
    }
    QPushButton:pressed {
        icon: url(/home/mahdi/Documents/sensor/ux/first_page/images/back2p.png);
    }
"""
