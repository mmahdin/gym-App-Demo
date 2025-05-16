# history_page.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QCalendarWidget, QPushButton
from PySide6.QtCore import Signal, Qt, QDate
from PySide6.QtGui import QTextCharFormat, QColor
from first_page.history_page.day_details.day_details_window import DayDetailsWindow


class HistoryPage(QWidget):
    exit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 225);")
        self.setGeometry(parent.rect())
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.details_window = None

        layout = QVBoxLayout(self)

        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(True)
        self.calendar.setStyleSheet("""
            QCalendarWidget QWidget { background-color: black; color: white; }
            QCalendarWidget QToolButton { background-color: #de5246; }
            QCalendarWidget QMenu { background-color: black; }
        """)
        self.calendar.clicked.connect(self.on_date_clicked)

        back_button = QPushButton("Back to Home")
        back_button.clicked.connect(self.exit_requested.emit)
        back_button.setStyleSheet(back_btn)

        layout.addWidget(self.calendar)
        layout.addWidget(back_button)

        self.setLayout(layout)

        # Modify with your actual file path
        self.load_status_from_file(
            "/home/mahdi/Documents/sensor/ux/first_page/history_page/database/data.txt")

    def load_status_from_file(self, filepath):
        format_green = QTextCharFormat()
        format_green.setBackground(QColor("#00ab00"))

        try:
            with open(filepath, "r") as f:
                for line in f:
                    date_str, value_str = line.strip().split(",")
                    date = QDate.fromString(date_str, "yyyy-MM-dd")
                    value = int(value_str)

                    if not date.isValid():
                        continue  # Skip invalid dates

                    if value == 1:
                        self.calendar.setDateTextFormat(date, format_green)
        except Exception as e:
            print(f"Error reading file: {e}")

    def on_date_clicked(self, date):
        if not self.details_window:
            self.details_window = DayDetailsWindow(parent=self)
            self.details_window.exit_requested.connect(
                self.hide_details_window)
        self.details_window.show_history(date)
        self.details_window.show()
        self.details_window.raise_()

    def hide_details_window(self):
        if self.details_window:
            self.details_window.hide()


back_btn = """
            QPushButton {
                background-color: #de5246;
                color: white;
                border: 2px solid #de5246;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ff6e60;
                border-color: #ff6e60;
            }
            QPushButton:pressed {
                background-color: #c13c32;
                border-color: #c13c32;
            }
        """
