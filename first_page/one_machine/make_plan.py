import time
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
import platform


from pathlib import Path


# Get the directory of the current script
BASE_DIR = Path(__file__).resolve().parent

# Global queue
data_queue = deque(maxlen=100)


class DiscWorker(QObject):
    finished = Signal()
    output = Signal(str)
    error = Signal(str)

    def __init__(self, mac):
        super().__init__()
        self.mac = mac

    def run(self):
        if platform.system() == "Linux":
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

        if platform.system() == "Linux":
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
    # Emits:
    #   time_vals:       np.ndarray of length window_size (shifted window, from –duration to 0)
    #   buffer:          np.ndarray of length window_size (the latest signal chunk)
    #   peak_indices:    np.ndarray of integer indices (all peaks in the buffer)
    #   peaks_y:         np.ndarray of float amplitudes at those indices
    #   u_ratio:         float (unique‐ratio on last few samples)
    #   peak_count:      int (total peaks detected so far, cumulative)
    #   is_discretized:  bool
    data_ready = Signal(
        np.ndarray,  # time_vals
        np.ndarray,  # buffer
        np.ndarray,  # peak_indices
        np.ndarray,  # peaks_y
        float,       # unique_ratio
        int,         # peak_count
        bool         # is_discretized
    )
    finished = Signal()

    def __init__(self, fs: float, step_sec: float, duration_sec: float, queue_ref):
        """
        fs            : sampling frequency (Hz)
        step_sec      : how many seconds-worth of samples to read per iteration
        duration_sec  : length of the sliding window in seconds
        queue_ref     : a deque or similar supporting popleft()
        """
        super().__init__()

        self.fs = fs
        # Compute how many samples correspond to step_sec; at least 1 sample
        self.step_size = max(1, int(np.round(fs * step_sec)))
        self.duration_sec = duration_sec
        self.window_size = int(np.round(fs * duration_sec))
        self.queue = queue_ref

        # Pre‐allocate circular buffer of length window_size
        self.buffer = np.zeros(self.window_size, dtype=float)

        # time_vals runs from –duration_sec .. 0, then is shifted forward each iteration
        self.time_vals = np.linspace(-duration_sec,
                                     0.0, self.window_size, dtype=float)

        # time increment per sample
        self.timestep = 1.0 / fs

        # Total number of samples processed so far (absolute index)
        self.sample_counter = 0

        # The absolute index (sample number) of the last peak we counted
        self.last_peak_index = -1

        # Cumulative count of peaks detected
        self.peak_count = 0

        # A small buffer‐based threshold for deciding “discretized” vs “continuous”
        self.discretization_threshold = 0.5

        self.running = True

    def process(self):
        """
        Main loop: each iteration, attempt to read self.step_size samples from queue.
        If not enough samples yet, sleep for step_sec (ms) and retry.
        Otherwise, shift the circular buffer, append new_data, run peak‐detection,
        update counts, compute unique_ratio, emit data_ready, then sleep.
        """
        # How long to sleep each iteration (in ms)
        sleep_ms = int(self.step_size / self.fs * 1000)

        while self.running:
            # Wait until at least step_size samples are available
            if len(self.queue) < self.step_size:
                QThread.msleep(sleep_ms)
                continue

            # Pop exactly step_size samples from the queue
            new_block = np.fromiter(
                (self.queue.popleft() for _ in range(self.step_size)),
                dtype=float,
                count=self.step_size
            )

            # Shift buffer left, discard the oldest step_size samples
            self.buffer[:-self.step_size] = self.buffer[self.step_size:]
            # Append new_block at the end
            self.buffer[-self.step_size:] = new_block

            # Advance time_vals by step_size * timestep
            shift_amount = self.step_size * self.timestep
            self.time_vals[:] = self.time_vals + shift_amount

            # Update the absolute sample counter
            self.sample_counter += self.step_size

            # ----- PEAK DETECTION (on the entire buffer) -----
            #
            # We compute a dynamic prominence based on the latest 1‐second window (or at least 20 samples):
            # 1 second or whole window
            lookback_n = min(self.window_size, int(self.fs * 1.0))
            recent_segment = self.buffer[-lookback_n:]
            dynamic_prom = (np.max(recent_segment) -
                            np.min(recent_segment)) * 0.3
            dynamic_prom = max(dynamic_prom, 1.0)

            # Find all peaks in the full buffer
            peaks, _ = find_peaks(
                self.buffer,
                prominence=dynamic_prom,
                # e.g. enforce at least 0.1 seconds between peaks
                distance=int(self.fs * 0.1)
            )

            # Convert buffer-relative indices to absolute sample indices:
            #   If buffer index = i, then absolute_index = sample_counter - window_size + i
            abs_peak_indices = peaks + (self.sample_counter - self.window_size)

            # Only count those peaks that have abs_index > last_peak_index
            new_peaks_mask = abs_peak_indices > self.last_peak_index
            if np.any(new_peaks_mask):
                # Increment peak_count by the number of brand‐new peaks
                newly_detected = abs_peak_indices[new_peaks_mask]
                self.peak_count += len(newly_detected)
                # Update last_peak_index to the maximum of newly counted
                self.last_peak_index = np.max(newly_detected)

            # We'll emit both the buffer-relative indices and their y-values:
            peaks_y = self.buffer[peaks]  # amplitude at each peak
            peak_indices = peaks.copy()

            # ----- DISCRETIZATION CHECK -----
            # Compute unique_ratio on the last 5 samples of the buffer
            last_five = self.buffer[-5:]
            u_ratio = self.unique_ratio(last_five, precision=0)
            is_discretized = (u_ratio < self.discretization_threshold)

            # Emit everything in one signal
            self.data_ready.emit(
                self.time_vals.copy(),
                self.buffer.copy(),
                peak_indices.astype(np.int64),
                peaks_y.copy(),
                float(u_ratio),
                int(self.peak_count),
                bool(is_discretized)
            )

            # Sleep a bit before next iteration
            QThread.msleep(sleep_ms)

        # Once running is set to False, emit finished
        self.finished.emit()

    def unique_ratio(self, signal: np.ndarray, precision: int = 0) -> float:
        """
        Compute the ratio of unique values in 'signal' array,
        after rounding to the given 'precision' decimals.
        """
        rounded = np.round(signal, precision)
        return float(len(np.unique(rounded)) / len(rounded))

    def stop(self):
        """
        Ask the worker to stop gracefully.
        """
        self.running = False


class MakePlan(QWidget):
    exit_requested = Signal()
    mac = "FE:20:38:F5:42:F9"
    # mac = "F6:DC:E6:17:E5:10"

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
            QIcon(str(BASE_DIR / '../images/back2.png')))
        self.back_btn.setStyleSheet(back_btn)
        self.back_btn.move(10, 720)
        self.back_btn.clicked.connect(self.handle_back)

        # Go button
        self.go_btn = QPushButton(self)
        self.go_btn.setIcon(
            QIcon(str(BASE_DIR / '../images/go.png')))
        self.go_btn.setStyleSheet(connect_btn)
        self.go_btn.move(205, 690)
        self.go_btn.clicked.connect(self.connect_to_device)
        self.go_btn.hide()

        self.disc_btn = QPushButton(self)
        self.disc_btn.setIcon(
            QIcon(str(BASE_DIR / '../images/disconnected.png')))
        self.disc_btn.setStyleSheet(connect_btn)
        self.disc_btn.move(205, 690)
        self.disc_btn.clicked.connect(self.disc)
        self.disc_btn.hide()

        # Top layout for image and name
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)

        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.move(300, 720)
        self.progress_bar.hide()

        # Status label (hidden initially)
        self.status_label = QLabel(self)
        self.status_label.move(10, 620)
        self.status_label.resize(500, 40)
        self.status_label.hide()

        self.plot_widget = pg.PlotWidget(self)
        self.plot_widget.move(5, 160)
        self.plot_widget.resize(430, 420)

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

    def update_plot(self,
                    time_vals: np.ndarray,
                    buffer: np.ndarray,
                    peak_indices: np.ndarray,
                    peaks_y: np.ndarray,
                    u_ratio: float,
                    peak_count: int,
                    is_discretized: bool):
        """
        - time_vals:     array of length window_size → x‐axis
        - buffer:        array of length window_size → y‐axis
        - peak_indices:  integer indices in [0 .. window_size-1]
        - peaks_y:       array of same length as peak_indices
        - u_ratio:       float
        - peak_count:    int
        - is_discretized: bool
        """

        # Update the main signal curve
        self.signal_curve.setData(time_vals, buffer)

        # Convert buffer‐indices → time values for scatter‐plot
        peak_times = time_vals[peak_indices]
        self.peaks_scatter.setData(peak_times, peaks_y)

        # Build title with color depending on discretization
        color = 'red' if is_discretized else 'white'
        status_text = 'DISCRETIZED!' if is_discretized else 'Continuous'
        title_text = (
            f"<span style='font-size:8pt; color:{color};'>"
            f"Real‐Time Signal | Unique Ratio: {u_ratio:.4f} | "
            f"Peaks: {peak_count} | Status: {status_text}"
            f"</span>"
        )
        self.plot.setTitle(title_text, color=color)

    def machine(self, name):
        path = str(
            (BASE_DIR / f'../history_page/day_details/images/{name}.png').resolve().as_posix())
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
            QIcon(str(BASE_DIR / '../images/back2g.png')))

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
            QIcon(str(BASE_DIR / '../images/back2.png')))

        self.start_worker()

    def clear_(self):
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

    def handle_back(self):
        self.clear_()
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
        self.clear_()
        self.analyse_worker.data_ready.disconnect(self.update_plot)

    def on_output(self, text):
        print("Command output:", text)

    def on_error(self, text):
        print("Error:", text)


# Styles
back_btn = f"""
    QPushButton {{
        border: none;
        background-color: transparent;
        icon-size: 50px 50px;
    }}
    QPushButton:pressed {{
        icon: url({(BASE_DIR / '../images/back2p.png').resolve().as_posix()});
    }}
"""

connect_btn = f"""
    QPushButton {{
        border: none;
        background-color: transparent;
        icon-size: 80px 80px;
    }}
    QPushButton:pressed {{
        icon: url({(BASE_DIR / '../images/gop.png').resolve().as_posix()});
    }}
"""
