"""LSL stream management module.

Provides thread-safe LSL stream handling for sending markers.
"""

from datetime import datetime
from typing import Optional

from pylsl import StreamInfo, StreamOutlet, local_clock
from PyQt6.QtCore import QMutex, QMutexLocker, QThread, pyqtSignal, pyqtSlot


def format_timestamp() -> tuple[str, float]:
    """Get formatted human time and LSL clock time."""
    human_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    lsl_time = local_clock()
    return human_time, lsl_time


def format_status_message(message: str) -> str:
    """Format a status message with timestamps."""
    human_time, lsl_time = format_timestamp()
    return f"[{human_time} | LSL: {lsl_time:.3f}] {message}"


class LSLStreamThread(QThread):
    """Thread for managing the LSL stream outlet.

    Handles creation and management of an LSL stream in a separate thread
    to keep the GUI responsive.
    """

    status_update = pyqtSignal(str)
    stream_ready = pyqtSignal(bool)
    marker_request = pyqtSignal(str)

    def __init__(self) -> None:
        """Initialize the LSL stream thread."""
        super().__init__()
        self.outlet: Optional[StreamOutlet] = None
        self.stream_info: Optional[StreamInfo] = None
        self._mutex = QMutex()
        self._is_ready = False

    def run(self) -> None:
        """Create and maintain the LSL stream."""
        try:
            stream_info = StreamInfo(
                name="MobiMarkerStream",
                type="Markers",
                channel_count=1,
                nominal_srate=0,
                channel_format="string",
                source_id="mobi_marker_gui_v1",
            )
            outlet = StreamOutlet(stream_info)

            with QMutexLocker(self._mutex):
                self.stream_info = stream_info
                self.outlet = outlet
                self._is_ready = True

            self.status_update.emit(
                format_status_message("LSL stream started successfully")
            )
            self.stream_ready.emit(True)

            self.marker_request.connect(self._handle_marker_request)
            self.exec()

        except Exception as e:
            self.status_update.emit(
                format_status_message(f"Error starting LSL stream: {e}")
            )
            self.stream_ready.emit(False)

    def send_marker(self, marker: str) -> None:
        """Request to send a marker (thread-safe, callable from GUI thread)."""
        with QMutexLocker(self._mutex):
            if not self._is_ready:
                self.status_update.emit(format_status_message("LSL stream not active"))
                return

        self.marker_request.emit(marker)

    @pyqtSlot(str)
    def _handle_marker_request(self, marker: str) -> None:
        """Handle marker request in the worker thread."""
        with QMutexLocker(self._mutex):
            outlet = self.outlet

        if outlet is None:
            self.status_update.emit(format_status_message("LSL stream not active"))
            return

        try:
            outlet.push_sample([marker])
            self.status_update.emit(format_status_message(f"Sent marker: {marker}"))
        except Exception as e:
            self.status_update.emit(format_status_message(f"Error sending marker: {e}"))
