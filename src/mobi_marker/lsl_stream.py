"""LSL stream management module.

Provides thread-safe LSL stream handling for sending markers.
"""

import logging
import threading
import traceback
from datetime import datetime
from typing import Optional

from pylsl import StreamInfo, StreamOutlet, local_clock
from PyQt6.QtCore import QMutex, QMutexLocker, QThread, pyqtSignal, pyqtSlot

logger = logging.getLogger(__name__)

STREAM_NAME = "MobiMarkerStream"
STREAM_TYPE = "Markers"
STREAM_CHANNEL_COUNT = 1
STREAM_NOMINAL_SRATE = 0
STREAM_CHANNEL_FORMAT = "string"
STREAM_SOURCE_ID = "mobi_marker_gui_v1"


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
        self.moveToThread(self)
        self.outlet: Optional[StreamOutlet] = None
        self.stream_info: Optional[StreamInfo] = None
        self._mutex = QMutex()
        self._is_ready = False
        logger.info(
            "LSLStreamThread.__init__  |  QThread id=%s  |  Python thread=%s"
            "  |  thread affinity moved to self",
            id(self),
            threading.current_thread().name,
        )

    def run(self) -> None:
        """Create and maintain the LSL stream."""
        logger.info(
            "run() ENTER  |  Python thread=%s  tid=%s",
            threading.current_thread().name,
            threading.current_thread().ident,
        )
        try:
            logger.debug(
                "Creating StreamInfo  name=%s  type=%s  source_id=%s",
                STREAM_NAME,
                STREAM_TYPE,
                STREAM_SOURCE_ID,
            )
            stream_info = StreamInfo(
                name=STREAM_NAME,
                type=STREAM_TYPE,
                channel_count=STREAM_CHANNEL_COUNT,
                nominal_srate=STREAM_NOMINAL_SRATE,
                channel_format=STREAM_CHANNEL_FORMAT,
                source_id=STREAM_SOURCE_ID,
            )
            logger.debug("StreamInfo created: %s", stream_info)

            logger.debug("Creating StreamOutlet …")
            outlet = StreamOutlet(stream_info)
            logger.info("StreamOutlet created successfully: %s", outlet)

            logger.debug("Acquiring mutex to store outlet & mark ready …")
            with QMutexLocker(self._mutex):
                self.stream_info = stream_info
                self.outlet = outlet
                self._is_ready = True
            logger.debug("Mutex released  |  _is_ready=%s", self._is_ready)

            logger.debug(
                "Connecting marker_request → _handle_marker_request"
                "  (QueuedConnection)"
            )
            self.marker_request.connect(self._handle_marker_request)

            status_msg = format_status_message("LSL stream started successfully")
            logger.info("Emitting status_update: %s", status_msg)
            self.status_update.emit(status_msg)

            logger.info("Emitting stream_ready(True)")
            self.stream_ready.emit(True)

            logger.info("Entering event loop (exec) …")
            self.exec()
            logger.info("Event loop (exec) exited normally")

        except Exception as e:
            logger.critical(
                "EXCEPTION in run(): %s\n%s", e, traceback.format_exc()
            )
            self.status_update.emit(
                format_status_message(f"Error starting LSL stream: {e}")
            )
            self.stream_ready.emit(False)

    def send_marker(self, marker: str) -> None:
        """Request to send a marker (thread-safe, callable from GUI thread)."""
        logger.debug(
            "send_marker('%s') called  |  Python thread=%s",
            marker,
            threading.current_thread().name,
        )
        with QMutexLocker(self._mutex):
            ready = self._is_ready
            logger.debug("send_marker  |  _is_ready=%s", ready)
            if not ready:
                logger.warning(
                    "send_marker REJECTED — stream not active  |  marker='%s'",
                    marker,
                )
                self.status_update.emit(format_status_message("LSL stream not active"))
                return

        logger.debug("Emitting marker_request('%s')", marker)
        self.marker_request.emit(marker)

    @pyqtSlot(str)
    def _handle_marker_request(self, marker: str) -> None:
        """Handle marker request in the worker thread."""
        logger.debug(
            "_handle_marker_request('%s')  |  Python thread=%s",
            marker,
            threading.current_thread().name,
        )
        with QMutexLocker(self._mutex):
            outlet = self.outlet
            logger.debug(
                "_handle_marker_request  |  outlet=%s",
                "present" if outlet is not None else "NONE",
            )

        if outlet is None:
            logger.error(
                "_handle_marker_request  |  outlet is None — cannot send '%s'",
                marker,
            )
            self.status_update.emit(format_status_message("LSL stream not active"))
            return

        try:
            logger.debug("push_sample(['%s']) …", marker)
            outlet.push_sample([marker])
            status_msg = format_status_message(f"Sent marker: {marker}")
            logger.info("Marker sent OK  |  marker='%s'", marker)
            self.status_update.emit(status_msg)
        except Exception as e:
            logger.error(
                "push_sample FAILED  |  marker='%s'  |  error=%s\n%s",
                marker,
                e,
                traceback.format_exc(),
            )
            self.status_update.emit(
                format_status_message(f"Error sending marker: {e}")
            )
