import sys
from PySide6.QtCore import QObject, Signal, QThread
from pyqtgraph import PlotWidget, GraphicsLayoutWidget, plot
from PySide6.QtCore import QObject, QTimer, Signal
from scipy.signal import find_peaks
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QPushButton,
                               QScrollArea, QHBoxLayout, QProgressBar)
from PySide6.QtCore import Qt, Signal, QThread, QTime, Slot, QObject, QTimer
from PySide6.QtGui import QIcon, QPixmap
import asyncio
import device_model
import bleak
from pathlib import Path
import json
from collections import deque
import threading
import subprocess


# Global queue
data_queue = deque()


class DiscWorker(QObject):
    finished = Signal()
    output = Signal(str)
    error = Signal(str)

    def __init__(self, mac):
        super().__init__()
        self.mac = mac

    def run(self):
        command = ["bt-device", "-r", self.mac]
        try:
            result = subprocess.run(
                command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.output.emit(result.stdout)
        except subprocess.CalledProcessError as e:
            self.error.emit(e.stderr)
        self.finished.emit()


class BluetoothScannerWorker(QObject):
    devices_found = Signal(list)
    finished = Signal()
    progress = Signal(str, int)

    def __init__(self, mac):
        super().__init__()
        self.mac = mac
        self._is_running = True

    def run(self):
        asyncio.run(self.scan())

    def stop(self):
        self._is_running = False

    async def scan(self):
        if not self._is_running:
            self.finished.emit()
            return

        self.progress.emit("Checking Bluetooth...", 5)
        command = ["bt-device", "-r", self.mac]
        try:
            result = subprocess.run(
                command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print("Command output:", result.stdout)
        except subprocess.CalledProcessError as e:
            print("Error:", e.stderr)

        if not self._is_running:
            self.finished.emit()
            return

        self.progress.emit("Scanning for Bluetooth devices...", 20)
        print("Searching for Bluetooth devices......")
        try:
            flag = False
            cnt = 0
            all_devices = []
            while not flag and cnt < 4 and self._is_running:
                cnt += 1
                all_devices = await bleak.BleakScanner.discover()
                print("Search ended")
                for d in all_devices:
                    if d.name is not None and "WT" in d.name:
                        print(d)
                        flag = True
                        break
            if self._is_running:
                self.devices_found.emit(all_devices)
        except Exception as ex:
            print("Bluetooth search failed to start")
            print(ex)
        finally:
            self.finished.emit()


class DeviceConnectionWorker(QObject):
    finished = Signal()
    error = Signal(str)
    progress = Signal(str, int)

    def __init__(self, mac_address: str):
        super().__init__()
        self.mac_address = mac_address
        self.device = None
        self.flg = 0
        self._is_running = True

    def run(self):
        asyncio.run(self.connect_device())

    def stop(self):
        self._is_running = False
        if self.device:
            try:
                # Assuming your DeviceModel supports this
                asyncio.run(self.device.closeDevice())
            except Exception as e:
                print("Error closing device:", e)

    async def connect_device(self):
        if not self._is_running:
            self.finished.emit()
            return

        try:
            self.progress.emit("Connecting to device...", 40)
            self.device = device_model.DeviceModel(
                "MyBle5.0", self.mac_address, self.updateData)
            await self.device.openDevice()

            # Keep the connection alive only while running
            while self._is_running:
                await asyncio.sleep(0.1)

        except Exception as ex:
            self.progress.emit(f"Error: {str(ex)}", 0)
        finally:
            self.finished.emit()

    def updateData(self, DeviceModel):
        global data_queue
        if not self._is_running:
            return

        if not self.flg:
            self.progress.emit("Connection established!", 100)
            self.flg = 1

        sensor_data = DeviceModel.deviceData
        data_point = {
            "AccX": sensor_data.get("AccX", 0.0),
            "AccY": sensor_data.get("AccY", 0.0),
            "AccZ": sensor_data.get("AccZ", 0.0),
            "AngX": sensor_data.get("AngX", 0.0),
            "AngY": sensor_data.get("AngY", 0.0),
            "AngZ": sensor_data.get("AngZ", 0.0),
            "AsX": sensor_data["AsX"],
            "AsY": sensor_data["AsY"],
            "AsZ": sensor_data["AsZ"],
            "timestamp": QTime.currentTime().msecsSinceStartOfDay() / 1000.0,
        }
        angles = np.array(
            [data_point["AngX"], data_point["AngY"], data_point["AngZ"]])
        angle_magnitude = np.linalg.norm(angles)
        data_queue.append(angle_magnitude)


class DataAnalyzerWorker(QObject):
    # (time_vals, buffer, peaks_y, u_ratio, peak_count, is_discretized)
    data_ready = Signal(np.ndarray, np.ndarray, np.ndarray, float, int, bool)
    finished = Signal()

    def __init__(self, fs, step_sec, duration_sec, queue_ref):
        super().__init__()
        self.fs = fs
        self.step_sec = step_sec
        self.duration_sec = duration_sec
        self.step_size = int(fs * step_sec)
        self.window_size = int(fs * duration_sec)
        self.queue = queue_ref
        self.running = True

        self.buffer = np.zeros(self.window_size)
        self.time_vals = np.linspace(-self.duration_sec, 0, self.window_size)
        self.timestep = 1 / fs
        self.total_time = 0
        self.peak_count = 0
        self.discretization_threshold = 0.5

    def process(self):
        while self.running:
            if len(self.queue) < self.step_size:
                QThread.msleep(int(self.step_sec * 10))  # Avoid busy wait
                continue
            print(self.queue[-1])
            new_data = np.array([self.queue.popleft()
                                for _ in range(self.step_size)])

            self.buffer[:-self.step_size] = self.buffer[self.step_size:]
            self.buffer[-self.step_size:] = new_data
            self.time_vals += self.step_size * self.timestep
            self.total_time += self.step_size * self.timestep

            # Peak detection
            peaks, _ = find_peaks(
                self.buffer, prominence=0.5, distance=self.fs // 10)
            peaks_y = self.buffer[peaks]
            self.peak_count += len(peaks)

            u_ratio = self.unique_ratio(new_data)
            is_discretized = u_ratio < self.discretization_threshold

            self.data_ready.emit(
                self.time_vals.copy(),
                self.buffer.copy(),
                peaks_y.copy(),
                u_ratio,
                self.peak_count,
                is_discretized
            )

            QThread.msleep(int(self.step_sec * 20))

    def unique_ratio(self, signal):
        return len(np.unique(np.round(signal, 6))) / len(signal)

    def stop(self):
        self.running = False
        self.finished.emit()


class MakePlan(QWidget):
    exit_requested = Signal()
    mac = "FE:20:38:F5:42:F9"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "background-color: rgba(0, 0, 0, 245); color: white;")
        self.setGeometry(parent.rect())
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.device_thread = None
        self.device_worker = None
        self.scanner_thread = None
        self.scanner_worker = None
        self.worker = None
        self.device_worker = None
        self.worker_thread = None
        self.analyse_worker = None

        # Back button
        self.back_btn = QPushButton(self)
        self.back_btn.setIcon(
            QIcon('/home/mahdi/Documents/sensor/ux/first_page/images/back2.png'))
        self.back_btn.setStyleSheet(back_btn)
        self.back_btn.move(10, 760)
        self.back_btn.clicked.connect(self.handle_back)

        # Go button
        self.go_btn = QPushButton(self)
        self.go_btn.setIcon(
            QIcon('/home/mahdi/Documents/sensor/ux/first_page/images/go.png'))
        self.go_btn.setStyleSheet(connect_btn)
        self.go_btn.move(205, 730)
        self.go_btn.clicked.connect(self.connect_to_device)
        self.go_btn.hide()

        self.disc_btn = QPushButton(self)
        self.disc_btn.setIcon(
            QIcon('/home/mahdi/Documents/sensor/ux/first_page/images/disconnected.png'))
        self.disc_btn.setStyleSheet(connect_btn)
        self.disc_btn.move(205, 730)
        self.disc_btn.clicked.connect(self.disc)
        self.disc_btn.hide()

        # Top layout for image and name
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)

        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.move(300, 770)
        self.progress_bar.hide()

        # Status label (hidden initially)
        self.status_label = QLabel(self)
        self.status_label.move(10, 650)
        self.status_label.resize(500, 60)
        self.status_label.hide()

        self.plot_widget = pg.PlotWidget(self)
        self.plot_widget.move(5, 210)
        self.plot_widget.resize(470, 440)

        self.plot = self.plot_widget.getPlotItem()
        self.signal_curve = self.plot.plot(pen='c')
        self.peaks_scatter = self.plot.plot(
            pen=None, symbol='x', symbolBrush='r')

    def start_worker(self):
        global data_queue

        self.worker_thread = QThread()
        self.analyse_worker = DataAnalyzerWorker(
            fs=100, step_sec=0.01, duration_sec=5, queue_ref=data_queue)
        self.analyse_worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.analyse_worker.process)
        self.analyse_worker.data_ready.connect(self.update_plot)
        self.exit_requested.connect(self.analyse_worker.stop)
        self.analyse_worker.finished.connect(self.worker_thread.quit)
        self.analyse_worker.finished.connect(self.analyse_worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()

    def update_plot(self, time_vals, buffer, peaks_y, u_ratio, peak_count, is_discretized):
        self.signal_curve.setData(time_vals, buffer)

        # Find x-locations of peaks for plot
        peak_indices = np.isin(buffer, peaks_y)
        peak_times = time_vals[peak_indices]
        self.peaks_scatter.setData(peak_times, peaks_y)

        title_text = (
            f"<span style='font-size:8pt; color:{'red' if is_discretized else 'white'};'>"
            f"Real-Time Signal | Unique Ratio: {u_ratio:.4f} | "
            f"Peaks: {peak_count} | Status: {'DISCRETIZED!' if is_discretized else 'Continuous'}"
            f"</span>"
        )
        self.plot.setTitle(title_text, color='r' if is_discretized else 'w')

    def machine(self, name):
        path = f'/home/mahdi/Documents/sensor/ux/first_page/history_page/day_details/images/{name}.png'
        self.go_btn.show()

        if not Path(path).exists():
            print(f"Image not found: {path}")
            self.image_label.clear()
            return

        pixmap = QPixmap(path)
        if pixmap.isNull():
            print("Failed to load image")
            self.image_label.clear()
            return

        scaled_pixmap = pixmap.scaled(
            100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.move(10, 10)

    def connect_to_device(self):
        # Show progress indicators
        self.back_btn.clicked.disconnect()
        self.back_btn.setIcon(
            QIcon('/home/mahdi/Documents/sensor/ux/first_page/images/back2g.png'))

        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.status_label.setText("Starting...")
        self.status_label.show()

        self.scanner_thread = QThread()
        self.scanner_worker = BluetoothScannerWorker(self.mac)
        self.scanner_worker.moveToThread(self.scanner_thread)

        self.scanner_worker.progress.connect(self.update_progress)
        self.scanner_thread.started.connect(self.scanner_worker.run)
        self.scanner_worker.devices_found.connect(self.on_devices_found)
        self.scanner_worker.finished.connect(self.scanner_thread.quit)
        self.scanner_worker.finished.connect(self.scanner_worker.deleteLater)
        self.scanner_thread.finished.connect(self.scanner_thread.deleteLater)

        self.scanner_thread.start()

    def on_devices_found(self, devices):
        mac = None
        for device in devices:
            if device.address == self.mac:
                mac = device.address
                break

        if mac:
            self.start_device_connection(mac)
        else:
            print("Device not found")

    def start_device_connection(self, mac_address):
        self.device_thread = QThread()
        self.device_worker = DeviceConnectionWorker(mac_address)
        self.device_worker.moveToThread(self.device_thread)

        self.device_worker.progress.connect(self.update_progress)
        self.device_thread.started.connect(self.device_worker.run)
        self.device_worker.finished.connect(self.device_thread.quit)
        self.device_worker.finished.connect(self.device_worker.deleteLater)
        self.device_thread.finished.connect(self.device_thread.deleteLater)

        self.device_thread.start()

    def update_progress(self, message: str, value: int):
        self.status_label.setText(message)
        self.progress_bar.setValue(value)
        if value == 100:
            QTimer.singleShot(2000, self._hide_progress)

    def _hide_progress(self):
        self.status_label.hide()
        self.progress_bar.hide()
        self.go_btn.hide()
        self.disc_btn.show()
        self.back_btn.clicked.connect(self.handle_back)
        self.back_btn.setIcon(
            QIcon('/home/mahdi/Documents/sensor/ux/first_page/images/back2.png'))

        self.start_worker()

    def handle_back(self):
        self.progress_bar.hide()
        self.status_label.hide()
        self.disc_btn.hide()

        for attr_name in ['device_worker', 'scanner_worker', 'worker']:
            worker = getattr(self, attr_name, None)
            if worker is not None:
                try:
                    worker.stop()
                except Exception as e:
                    print(f"Failed to stop {attr_name}: {e}")

        # Quit and wait for all threads
        for thread_name in ['device_thread', 'scanner_thread', 'dis_thread']:
            thread = getattr(self, thread_name, None)
            if thread is not None:
                try:
                    thread.quit()
                    thread.wait()
                except Exception as e:
                    print(f"Failed to quit {thread_name}: {e}")

        if hasattr(self, 'analyse_worker') and self.analyse_worker:
            self.analyse_worker.stop()

        if hasattr(self, 'worker_thread') and self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()

        self.exit_requested.emit()

    def disc(self):
        self.dis_thread = QThread()
        self.worker = DiscWorker(self.mac)
        self.worker.moveToThread(self.dis_thread)

        self.dis_thread.started.connect(self.worker.run)
        self.worker.output.connect(self.on_output)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.dis_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.dis_thread.finished.connect(self.dis_thread.deleteLater)

        self.dis_thread.start()

        self.disc_btn.hide()
        self.go_btn.show()

    def on_output(self, text):
        print("Command output:", text)

    def on_error(self, text):
        print("Error:", text)


# Styles
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

connect_btn = """
    QPushButton {
        border: none;
        background-color: transparent;
        icon-size: 80px 80px;
    }
    QPushButton:pressed {
        icon: url(/home/mahdi/Documents/sensor/ux/first_page/images/gop.png);
    }
"""
