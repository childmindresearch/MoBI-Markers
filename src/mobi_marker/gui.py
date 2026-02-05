"""GUI module for the MoBI Marker application.

Provides the PyQt6-based user interface for sending LSL markers.
"""

import sys
import traceback
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from mobi_marker.lsl_stream import LSLStreamThread, format_status_message

AVAILABLE_MODALITIES = [
    "EEG",
    "fNIRS",
    "EMG",
    "EOG",
    "ECG",
    "Motion Capture",
    "Eye Tracking",
    "Audio",
    "Video",
    "Other",
]


class MobiMarkerGUI(QMainWindow):
    """Main GUI window for the LSL marker application.

    This class provides the main window interface for sending LSL markers.
    It includes input fields, status display, control buttons for managing
    the LSL stream, and quick marker buttons for common neuroscience events.

    Attributes:
        lsl_thread: The LSL stream thread for handling marker transmission.
        marker_input: Text input field for entering custom marker text.
        status_display: Text area for displaying status messages with both
            human-readable and LSL timestamps.
        send_button: Button for sending custom markers from the input field.
        end_modality_button: Button for sending END [modality] markers.
        modality_combo: Dropdown for selecting recording modality.
        custom_modality_input: Text field for custom modality when "Other" is selected.
    """

    def __init__(self) -> None:
        """Initialize the main window.

        Sets up the GUI components and starts the LSL stream.
        """
        super().__init__()
        self.lsl_thread: Optional[LSLStreamThread] = None
        self.init_ui()
        self.start_lsl_stream()

    def init_ui(self) -> None:
        """Initialize the user interface.

        Creates and configures all GUI components including input fields,
        buttons, and status display area.
        """
        self.setWindowTitle("MoBI Marker - LSL Stream")
        self.setGeometry(300, 300, 600, 400)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)

        # Title
        title_label = QLabel("MoBI LSL Event Marker Sender")
        title_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; margin: 20px; color: #2c3e50;"
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Input section
        input_layout = QHBoxLayout()

        # Marker input
        input_label = QLabel("Marker:")
        input_layout.addWidget(input_label)

        self.marker_input = QLineEdit()
        self.marker_input.setPlaceholderText("What happened...?")
        self.marker_input.setMinimumHeight(25)
        self.marker_input.setStyleSheet("font-size: 14px; padding: 5px;")
        self.marker_input.returnPressed.connect(self.send_marker)
        input_layout.addWidget(self.marker_input)

        # Send button
        self.send_button = QPushButton("Send Marker")
        self.send_button.setEnabled(False)  # Disabled until stream is ready
        self.send_button.clicked.connect(self.send_marker)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        # Quick marker buttons
        quick_buttons_label = QLabel("Quick Markers:")
        quick_buttons_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        layout.addWidget(quick_buttons_label)

        quick_buttons_layout = QGridLayout()

        # Define quick marker buttons
        quick_markers = [
            ("START", "#27ae60"),  # Green
            ("END", "#e74c3c"),  # Red
            ("PAUSE", "#f39c12"),  # Orange
            ("RESUME", "#2ecc71"),  # Light green
            ("ERROR", "#c0392b"),  # Dark red
            ("NOTE", "#3498db"),  # Blue
            ("START BREAK", "#8e44ad"),  # Purple
            ("END BREAK", "#e67e22"),  # Dark orange
        ]

        # Create and add quick marker buttons
        self.quick_marker_buttons: list[QPushButton] = []
        row = 0
        col = 0
        for marker_text, color in quick_markers:
            button = QPushButton(marker_text)
            button.setEnabled(False)  # Disabled until stream is ready
            button.setStyleSheet(
                f"QPushButton {{"
                f"    background-color: {color};"
                f"    color: white;"
                f"    font-weight: bold;"
                f"    padding: 8px 16px;"
                f"    border: none;"
                f"    border-radius: 4px;"
                f"    min-height: 30px;"
                f"}}"
                f"QPushButton:hover {{"
                f"    background-color: {color}CC;"  # Add transparency on hover
                f"}}"
                f"QPushButton:pressed {{"
                f"    background-color: {color}99;"  # More transparency when pressed
                f"}}"
            )
            button.clicked.connect(
                lambda checked, text=marker_text: self.send_quick_marker(text)
            )
            quick_buttons_layout.addWidget(button, row, col)
            self.quick_marker_buttons.append(button)

            col += 1
            if col > 2:  # 3 columns per row
                col = 0
                row += 1

        layout.addLayout(quick_buttons_layout)

        # Add separate modality section with better design
        modality_label = QLabel("End Modality:")
        modality_label.setStyleSheet("font-weight: bold; margin-top: 15px;")
        layout.addWidget(modality_label)

        # Create a nice-looking modality section
        modality_widget = QWidget()
        modality_widget.setStyleSheet(
            "QWidget {"
            "    background-color: #f8f9fa;"
            "    border: 1px solid #dee2e6;"
            "    border-radius: 8px;"
            "    padding: 12px;"
            "}"
        )

        modality_layout = QHBoxLayout(modality_widget)
        modality_layout.setContentsMargins(12, 8, 12, 8)
        modality_layout.setSpacing(10)

        # END button for modality
        self.end_modality_button = QPushButton("END")
        self.end_modality_button.setStyleSheet(
            "QPushButton {"
            "    background-color: #6c757d;"
            "    color: white;"
            "    font-weight: bold;"
            "    padding: 10px 20px;"
            "    border: none;"
            "    border-radius: 6px;"
            "    min-width: 60px;"
            "    font-size: 14px;"
            "}"
            "QPushButton:hover {"
            "    background-color: #5a6268;"
            "}"
            "QPushButton:pressed {"
            "    background-color: #545b62;"
            "}"
        )
        self.end_modality_button.setEnabled(False)  # Disabled until stream is ready
        self.end_modality_button.clicked.connect(self.send_end_modality_marker)
        modality_layout.addWidget(self.end_modality_button)

        # Modality dropdown
        self.modality_combo = QComboBox()
        self.modality_combo.addItems(AVAILABLE_MODALITIES)
        self.modality_combo.setStyleSheet(
            "QComboBox {"
            "    padding: 8px 12px;"
            "    border: 2px solid #ced4da;"
            "    border-radius: 6px;"
            "    background-color: white;"
            "    font-size: 14px;"
            "    min-width: 140px;"
            "}"
            "QComboBox:hover {"
            "    border-color: #80bdff;"
            "}"
            "QComboBox::drop-down {"
            "    border: none;"
            "    width: 30px;"
            "}"
            "QComboBox::down-arrow {"
            "    width: 12px;"
            "    height: 12px;"
            "}"
        )
        self.modality_combo.currentTextChanged.connect(self.on_modality_changed)
        modality_layout.addWidget(self.modality_combo)

        # Custom modality input (initially hidden)
        self.custom_modality_input = QLineEdit()
        self.custom_modality_input.setPlaceholderText("Enter custom modality...")
        self.custom_modality_input.setStyleSheet(
            "QLineEdit {"
            "    padding: 8px 12px;"
            "    border: 2px solid #ced4da;"
            "    border-radius: 6px;"
            "    font-size: 14px;"
            "    min-width: 150px;"
            "}"
            "QLineEdit:focus {"
            "    border-color: #80bdff;"
            "    outline: none;"
            "}"
        )
        self.custom_modality_input.setVisible(False)
        modality_layout.addWidget(self.custom_modality_input)

        # Add stretch to center the content
        modality_layout.addStretch()

        layout.addWidget(modality_widget)

        # Status display
        status_label = QLabel("Status Log:")
        status_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        layout.addWidget(status_label)

        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        self.status_display.setMaximumHeight(200)
        layout.addWidget(self.status_display)

        # Focus on the input field
        self.marker_input.setFocus()

    def start_lsl_stream(self) -> None:
        """Start the LSL stream in a separate thread.

        Creates and initializes the LSL stream thread, connecting its
        status update signal to the GUI's status display.
        """
        self.lsl_thread = LSLStreamThread()
        self.lsl_thread.status_update.connect(self.update_status)
        self.lsl_thread.stream_ready.connect(self.on_stream_ready)
        self.lsl_thread.start()

    @pyqtSlot(bool)
    def on_stream_ready(self, ready: bool) -> None:
        """Handle stream ready signal.

        Enables or disables marker buttons based on stream status.

        Args:
            ready: True if stream is ready, False otherwise.
        """
        self.send_button.setEnabled(ready)
        self.end_modality_button.setEnabled(ready)
        for button in self.quick_marker_buttons:
            button.setEnabled(ready)

        if not ready:
            self.update_status(
                format_status_message(
                    "Warning: LSL stream failed to start. Marker buttons disabled."
                )
            )

    def send_marker(self) -> None:
        """Send the marker from the input field.

        Retrieves the text from the marker input field and sends it
        through the LSL stream. Validates that the marker text is not
        empty and that the LSL stream is initialized.
        """
        marker_text = self.marker_input.text().strip()

        if not marker_text:
            self.update_status(format_status_message("Error: Empty marker text"))
            return

        if self.lsl_thread is not None:
            self.lsl_thread.send_marker(marker_text)
            self.marker_input.clear()
        else:
            self.update_status(
                format_status_message("Error: LSL stream not initialized")
            )

    def send_quick_marker(self, marker_text: str) -> None:
        """Send a predefined quick marker.

        Args:
            marker_text: The predefined marker text to send through the LSL stream.

        Note:
            This method sends quick markers immediately without needing text input.
            It validates that the LSL stream is initialized before sending.
        """
        if self.lsl_thread is not None:
            self.lsl_thread.send_marker(marker_text)
        else:
            self.update_status(
                format_status_message("Error: LSL stream not initialized")
            )

    def on_modality_changed(self, modality: str) -> None:
        """Handle modality dropdown selection change.

        Args:
            modality: The selected modality from the dropdown.

        Note:
            Shows/hides the custom modality input field based on selection.
        """
        if modality == "Other":
            self.custom_modality_input.setVisible(True)
            self.custom_modality_input.setFocus()
        else:
            self.custom_modality_input.setVisible(False)

    def send_end_modality_marker(self) -> None:
        """Send an 'END [modality]' marker.

        Constructs the marker text based on the selected modality from the
        dropdown or custom input field, then sends it through the LSL stream.

        Note:
            Uses the dropdown selection unless "Other" is selected, in which
            case it uses the custom input field text.
        """
        modality = self.modality_combo.currentText()

        if modality == "Other":
            custom_modality = self.custom_modality_input.text().strip()
            if not custom_modality:
                self.update_status(
                    format_status_message("Error: Please enter a custom modality")
                )
                return
            marker_text = f"END {custom_modality.upper()}"
            self.custom_modality_input.clear()
        else:
            marker_text = f"END {modality}"

        if self.lsl_thread is not None:
            self.lsl_thread.send_marker(marker_text)
        else:
            self.update_status(
                format_status_message("Error: LSL stream not initialized")
            )

    def update_status(self, message: str) -> None:
        """Update the status display with a new message.

        Args:
            message: The status message to display in the status log.

        Note:
            The status display automatically scrolls to show the newest message.
        """
        self.status_display.append(message)
        # Auto-scroll to bottom
        scrollbar = self.status_display.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event: QCloseEvent | None) -> None:
        """Handle window close event.

        Properly shuts down the LSL stream thread before closing the window.

        Args:
            event: The close event from Qt.
        """
        if self.lsl_thread is not None:
            self.lsl_thread.quit()
            if not self.lsl_thread.wait(3000):
                self.update_status(
                    format_status_message("Warning: LSL thread did not stop gracefully")
                )
                self.lsl_thread.terminate()
                self.lsl_thread.wait()
        if event is not None:
            event.accept()


def main() -> None:
    """Main entry point for the GUI application.

    Creates and runs the Qt application with the MoBI Marker GUI.
    Sets up application properties and handles the application lifecycle.

    Returns:
        None

    Raises:
        SystemExit: When the application is closed.
    """
    try:
        app = QApplication(sys.argv)

        # Set application properties
        app.setApplicationName("MoBI Marker")
        app.setApplicationVersion("0.1.0")
        app.setOrganizationName("MoBI Research")

        # Create and show the main window
        window = MobiMarkerGUI()
        window.show()

        # Run the application
        sys.exit(app.exec())

    except Exception as e:
        # Log any unexpected exceptions
        error_msg = f"Fatal error: {e}\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
