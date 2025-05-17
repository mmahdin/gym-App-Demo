from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QPushButton,
                               QScrollArea, QHBoxLayout)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QSizePolicy
from functools import partial
from first_page.one_machine.make_plan import MakePlan


class PlanePage(QWidget):
    exit_requested = Signal()

    machines = ['Dumbbell', 'Barbell', 'Chest press']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "background-color: rgba(0, 0, 0, 235); color: white;")
        self.setGeometry(parent.rect())
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.make_plane = None

        # Back button setup
        self.back_btn = QPushButton(self)
        self.back_btn.setIcon(
            QIcon('/home/mahdi/Documents/sensor/ux/first_page/images/back2.png'))
        self.back_btn.setStyleSheet(back_btn)
        self.back_btn.move(10, 760)
        self.back_btn.clicked.connect(self.exit_requested.emit)

    def show_machines(self):
        # Clear any existing scroll area
        for i in reversed(range(self.children().__len__())):
            child = self.children()[i]
            if isinstance(child, QScrollArea):
                child.setParent(None)

        # Scroll Area Setup
        scroll_area = QScrollArea(self)
        scroll_area.setGeometry(0, 0, self.width(), self.height() - 80)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(
            "border: none; background-color: transparent;")

        # Container Widget inside scroll area
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignTop)

        # Load machine images and labels
        for machine in self.machines:
            machine_layout = QVBoxLayout()
            machine_layout.setAlignment(Qt.AlignCenter)

            # Load image
            image_path = f'/home/mahdi/Documents/sensor/ux/first_page/history_page/day_details/images/{machine}.png'
            image_label = QPushButton()
            image_label.setIcon(
                QIcon(image_path))
            image_path = image_path.split('.png')[0]
            name = image_path.split('/')[-1]
            image_label.setStyleSheet(machine_btn.format(f'{image_path}p.png'))
            image_label.clicked.connect(partial(self.on_machine_clicked, name))

            # Machine name label
            name_label = QLabel(machine)
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setStyleSheet("font-size: 16px; margin-top: 5px;")

            # Separator line
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            line.setStyleSheet(
                "color: #cc33cc; background-color: #222222; margin: 10px 0px;")
            line.setFixedHeight(4)
            # line.setMinimumWidth(400)  # Increase as needed
            line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            # Add widgets to machine layout
            machine_layout.addWidget(image_label)
            machine_layout.addWidget(name_label)
            machine_layout.addWidget(line)

            # Add to main layout
            layout.addLayout(machine_layout)

        scroll_area.setWidget(container)

    def on_machine_clicked(self, name):
        if not self.make_plane:
            self.make_plane = MakePlan(parent=self)
            self.make_plane.exit_requested.connect(
                self.hide_machine_window)
        self.make_plane.machine(name)
        self.make_plane.show()
        self.make_plane.raise_()

    def hide_machine_window(self):
        if self.make_plane:
            self.make_plane.hide()


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

machine_btn = """
    QPushButton {{
        border: none;
        background-color: transparent;
        icon-size: 200px 200px;
    }}
    QPushButton:pressed {{
        icon: url({});
    }}
"""
