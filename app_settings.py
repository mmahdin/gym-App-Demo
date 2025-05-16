from PySide6.QtCore import QSettings


class AppSettings:
    def __init__(self):
        self.settings = QSettings("MyCompany", "MyApp")

    def save_window_state(self, state):
        self.settings.setValue("window_state", state)

    def load_window_state(self):
        return self.settings.value("window_state")
