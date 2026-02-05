"""Tests for the GUI module."""

from typing import Any
from unittest.mock import Mock, patch

import pytest

from mobi_marker.gui import AVAILABLE_MODALITIES, MobiMarkerGUI, main


@pytest.fixture
def mock_gui() -> MobiMarkerGUI:
    """Create a mocked GUI instance."""
    with (
        patch("mobi_marker.gui.QApplication"),
        patch("mobi_marker.gui.QMainWindow.__init__"),
        patch("mobi_marker.gui.MobiMarkerGUI.init_ui"),
        patch("mobi_marker.gui.MobiMarkerGUI.start_lsl_stream"),
    ):
        gui = MobiMarkerGUI()
        gui.lsl_thread = Mock()
        gui.marker_input = Mock()
        gui.status_display = Mock()
        gui.modality_combo = Mock()
        gui.custom_modality_input = Mock()
        gui.send_button = Mock()
        gui.end_modality_button = Mock()
        gui.quick_marker_buttons = [Mock(), Mock(), Mock()]
        return gui


def _lsl_thread(gui: MobiMarkerGUI) -> Any:
    """Return lsl_thread as Any for mock assertions."""
    return gui.lsl_thread


def _marker_input(gui: MobiMarkerGUI) -> Any:
    """Return marker_input as Any for mock assertions."""
    return gui.marker_input


def _status_display(gui: MobiMarkerGUI) -> Any:
    """Return status_display as Any for mock assertions."""
    return gui.status_display


def _modality_combo(gui: MobiMarkerGUI) -> Any:
    """Return modality_combo as Any for mock assertions."""
    return gui.modality_combo


def _custom_modality_input(gui: MobiMarkerGUI) -> Any:
    """Return custom_modality_input as Any for mock assertions."""
    return gui.custom_modality_input


def _send_button(gui: MobiMarkerGUI) -> Any:
    """Return send_button as Any for mock assertions."""
    return gui.send_button


def _end_modality_button(gui: MobiMarkerGUI) -> Any:
    """Return end_modality_button as Any for mock assertions."""
    return gui.end_modality_button


def _quick_marker_buttons(gui: MobiMarkerGUI) -> list[Any]:
    """Return quick_marker_buttons as list[Any] for mock assertions."""
    return gui.quick_marker_buttons  # type: ignore[return-value]


class TestAvailableModalities:
    """Tests for AVAILABLE_MODALITIES constant."""

    def test_contains_eeg(self) -> None:
        """EEG is in the modalities list."""
        assert "EEG" in AVAILABLE_MODALITIES

    def test_other_is_last(self) -> None:
        """Other is the last item for custom input."""
        assert AVAILABLE_MODALITIES[-1] == "Other"


class TestMobiMarkerGUIInit:
    """Tests for MobiMarkerGUI initialization."""

    def test_lsl_thread_starts_none(self) -> None:
        """LSL thread is None before start_lsl_stream runs."""
        with (
            patch("mobi_marker.gui.QApplication"),
            patch("mobi_marker.gui.QMainWindow.__init__"),
            patch("mobi_marker.gui.MobiMarkerGUI.init_ui"),
            patch("mobi_marker.gui.MobiMarkerGUI.start_lsl_stream"),
        ):
            gui = MobiMarkerGUI()

        assert gui.lsl_thread is None


class TestSendMarker:
    """Tests for MobiMarkerGUI.send_marker() method."""

    def test_valid_input_sends_to_thread(self, mock_gui: MobiMarkerGUI) -> None:
        """Valid marker text is sent to the LSL thread."""
        _marker_input(mock_gui).text.return_value.strip.return_value = "Test Marker"

        mock_gui.send_marker()

        _lsl_thread(mock_gui).send_marker.assert_called_once_with("Test Marker")

    def test_valid_input_clears_field(self, mock_gui: MobiMarkerGUI) -> None:
        """Input field is cleared after sending."""
        _marker_input(mock_gui).text.return_value.strip.return_value = "Test"

        mock_gui.send_marker()

        _marker_input(mock_gui).clear.assert_called_once()

    def test_empty_input_shows_error(self, mock_gui: MobiMarkerGUI) -> None:
        """Empty input shows error in status."""
        _marker_input(mock_gui).text.return_value.strip.return_value = ""

        with patch("mobi_marker.gui.format_status_message", return_value="error msg"):
            mock_gui.send_marker()

        _lsl_thread(mock_gui).send_marker.assert_not_called()
        _status_display(mock_gui).append.assert_called()

    def test_no_thread_shows_error(self, mock_gui: MobiMarkerGUI) -> None:
        """No LSL thread shows error in status."""
        mock_gui.lsl_thread = None
        _marker_input(mock_gui).text.return_value.strip.return_value = "Test"

        with patch("mobi_marker.gui.format_status_message", return_value="error msg"):
            mock_gui.send_marker()

        _status_display(mock_gui).append.assert_called()


class TestSendQuickMarker:
    """Tests for MobiMarkerGUI.send_quick_marker() method."""

    def test_sends_to_thread(self, mock_gui: MobiMarkerGUI) -> None:
        """Quick marker is sent to the LSL thread."""
        mock_gui.send_quick_marker("START")

        _lsl_thread(mock_gui).send_marker.assert_called_once_with("START")

    def test_no_thread_shows_error(self, mock_gui: MobiMarkerGUI) -> None:
        """No LSL thread shows error in status."""
        mock_gui.lsl_thread = None

        with patch("mobi_marker.gui.format_status_message", return_value="error"):
            mock_gui.send_quick_marker("START")

        _status_display(mock_gui).append.assert_called()


class TestSendEndModalityMarker:
    """Tests for MobiMarkerGUI.send_end_modality_marker() method."""

    def test_standard_modality_sends_formatted(self, mock_gui: MobiMarkerGUI) -> None:
        """Standard modality sends 'END <modality>'."""
        _modality_combo(mock_gui).currentText.return_value = "EEG"

        mock_gui.send_end_modality_marker()

        _lsl_thread(mock_gui).send_marker.assert_called_once_with("END EEG")

    def test_custom_modality_sends_uppercase(self, mock_gui: MobiMarkerGUI) -> None:
        """Custom modality is uppercased."""
        _modality_combo(mock_gui).currentText.return_value = "Other"
        _custom_modality_input(mock_gui).text.return_value.strip.return_value = "custom"

        mock_gui.send_end_modality_marker()

        _lsl_thread(mock_gui).send_marker.assert_called_once_with("END CUSTOM")

    def test_custom_modality_clears_input(self, mock_gui: MobiMarkerGUI) -> None:
        """Custom input field is cleared after sending."""
        _modality_combo(mock_gui).currentText.return_value = "Other"
        _custom_modality_input(mock_gui).text.return_value.strip.return_value = "sensor"

        mock_gui.send_end_modality_marker()

        _custom_modality_input(mock_gui).clear.assert_called_once()

    def test_empty_custom_shows_error(self, mock_gui: MobiMarkerGUI) -> None:
        """Empty custom modality shows error."""
        _modality_combo(mock_gui).currentText.return_value = "Other"
        _custom_modality_input(mock_gui).text.return_value.strip.return_value = ""

        with patch("mobi_marker.gui.format_status_message", return_value="error"):
            mock_gui.send_end_modality_marker()

        _lsl_thread(mock_gui).send_marker.assert_not_called()

    def test_no_thread_shows_error(self, mock_gui: MobiMarkerGUI) -> None:
        """No LSL thread shows error in status."""
        mock_gui.lsl_thread = None
        _modality_combo(mock_gui).currentText.return_value = "EEG"

        with patch("mobi_marker.gui.format_status_message", return_value="error"):
            mock_gui.send_end_modality_marker()

        _status_display(mock_gui).append.assert_called()


class TestOnModalityChanged:
    """Tests for MobiMarkerGUI.on_modality_changed() method."""

    def test_other_shows_custom_input(self, mock_gui: MobiMarkerGUI) -> None:
        """Selecting 'Other' shows custom input field."""
        mock_gui.on_modality_changed("Other")

        _custom_modality_input(mock_gui).setVisible.assert_called_once_with(True)

    def test_other_focuses_custom_input(self, mock_gui: MobiMarkerGUI) -> None:
        """Selecting 'Other' focuses custom input field."""
        mock_gui.on_modality_changed("Other")

        _custom_modality_input(mock_gui).setFocus.assert_called_once()

    def test_standard_modality_hides_input(self, mock_gui: MobiMarkerGUI) -> None:
        """Selecting standard modality hides custom input."""
        mock_gui.on_modality_changed("EEG")

        _custom_modality_input(mock_gui).setVisible.assert_called_once_with(False)


class TestOnStreamReady:
    """Tests for MobiMarkerGUI.on_stream_ready() method."""

    def test_ready_enables_send_button(self, mock_gui: MobiMarkerGUI) -> None:
        """Stream ready enables send button."""
        mock_gui.on_stream_ready(True)

        _send_button(mock_gui).setEnabled.assert_called_once_with(True)

    def test_ready_enables_modality_button(self, mock_gui: MobiMarkerGUI) -> None:
        """Stream ready enables end modality button."""
        mock_gui.on_stream_ready(True)

        _end_modality_button(mock_gui).setEnabled.assert_called_once_with(True)

    def test_ready_enables_quick_buttons(self, mock_gui: MobiMarkerGUI) -> None:
        """Stream ready enables all quick marker buttons."""
        mock_gui.on_stream_ready(True)

        for button in _quick_marker_buttons(mock_gui):
            button.setEnabled.assert_called_once_with(True)

    def test_not_ready_disables_buttons(self, mock_gui: MobiMarkerGUI) -> None:
        """Stream not ready disables buttons."""
        with patch("mobi_marker.gui.format_status_message", return_value="warning"):
            mock_gui.on_stream_ready(False)

        _send_button(mock_gui).setEnabled.assert_called_once_with(False)

    def test_not_ready_shows_warning(self, mock_gui: MobiMarkerGUI) -> None:
        """Stream not ready shows warning in status."""
        with patch("mobi_marker.gui.format_status_message", return_value="warning"):
            mock_gui.on_stream_ready(False)

        _status_display(mock_gui).append.assert_called()


class TestUpdateStatus:
    """Tests for MobiMarkerGUI.update_status() method."""

    def test_appends_message(self, mock_gui: MobiMarkerGUI) -> None:
        """Message is appended to status display."""
        mock_gui.update_status("Test message")

        _status_display(mock_gui).append.assert_called_once_with("Test message")

    def test_scrolls_to_bottom(self, mock_gui: MobiMarkerGUI) -> None:
        """Status display scrolls to bottom."""
        mock_scrollbar = Mock()
        mock_scrollbar.maximum.return_value = 100
        _status_display(mock_gui).verticalScrollBar.return_value = mock_scrollbar

        mock_gui.update_status("Test")

        mock_scrollbar.setValue.assert_called_once_with(100)

    def test_handles_none_scrollbar(self, mock_gui: MobiMarkerGUI) -> None:
        """Handles None scrollbar gracefully."""
        _status_display(mock_gui).verticalScrollBar.return_value = None

        mock_gui.update_status("Test")  # Should not raise


class TestCloseEvent:
    """Tests for MobiMarkerGUI.closeEvent() method."""

    def test_quits_thread(self, mock_gui: MobiMarkerGUI) -> None:
        """Thread is quit on close."""
        _lsl_thread(mock_gui).wait.return_value = True
        mock_event = Mock()

        mock_gui.closeEvent(mock_event)

        _lsl_thread(mock_gui).quit.assert_called_once()

    def test_waits_for_thread(self, mock_gui: MobiMarkerGUI) -> None:
        """Waits for thread with timeout."""
        _lsl_thread(mock_gui).wait.return_value = True
        mock_event = Mock()

        mock_gui.closeEvent(mock_event)

        _lsl_thread(mock_gui).wait.assert_called_once_with(3000)

    def test_accepts_event(self, mock_gui: MobiMarkerGUI) -> None:
        """Event is accepted."""
        _lsl_thread(mock_gui).wait.return_value = True
        mock_event = Mock()

        mock_gui.closeEvent(mock_event)

        mock_event.accept.assert_called_once()

    def test_timeout_terminates_thread(self, mock_gui: MobiMarkerGUI) -> None:
        """Thread is terminated on timeout."""
        _lsl_thread(mock_gui).wait.side_effect = [False, True]
        mock_event = Mock()

        with patch("mobi_marker.gui.format_status_message", return_value="warning"):
            mock_gui.closeEvent(mock_event)

        _lsl_thread(mock_gui).terminate.assert_called_once()

    def test_no_thread_still_accepts(self, mock_gui: MobiMarkerGUI) -> None:
        """Event is accepted even with no thread."""
        mock_gui.lsl_thread = None
        mock_event = Mock()

        mock_gui.closeEvent(mock_event)

        mock_event.accept.assert_called_once()

    def test_none_event_handled(self, mock_gui: MobiMarkerGUI) -> None:
        """None event is handled gracefully."""
        _lsl_thread(mock_gui).wait.return_value = True

        mock_gui.closeEvent(None)  # Should not raise


class TestStartLslStream:
    """Tests for MobiMarkerGUI.start_lsl_stream() method."""

    def test_creates_and_starts_thread(self) -> None:
        """Creates and starts LSLStreamThread instance."""
        with (
            patch("mobi_marker.gui.QApplication"),
            patch("mobi_marker.gui.QMainWindow.__init__"),
            patch("mobi_marker.gui.MobiMarkerGUI.init_ui"),
        ):
            with patch("mobi_marker.gui.LSLStreamThread") as mock_thread_class:
                mock_thread = Mock()
                mock_thread_class.return_value = mock_thread

                _ = MobiMarkerGUI()

        mock_thread_class.assert_called_once()
        mock_thread.start.assert_called_once()


class TestMain:
    """Tests for main() function."""

    def test_creates_application(self) -> None:
        """Creates QApplication."""
        mock_app = Mock()
        mock_app.exec.return_value = 0
        with (
            patch("mobi_marker.gui.QApplication", return_value=mock_app),
            patch("mobi_marker.gui.MobiMarkerGUI"),
            patch("mobi_marker.gui.sys.exit"),
        ):
            main()

        mock_app.setApplicationName.assert_called_once_with("MoBI Marker")

    def test_shows_window(self) -> None:
        """Shows the main window."""
        mock_app = Mock()
        mock_app.exec.return_value = 0
        with (
            patch("mobi_marker.gui.QApplication", return_value=mock_app),
            patch("mobi_marker.gui.MobiMarkerGUI") as mock_gui_class,
            patch("mobi_marker.gui.sys.exit"),
        ):
            mock_window = Mock()
            mock_gui_class.return_value = mock_window

            main()

        mock_window.show.assert_called_once()

    def test_exception_exits_with_error(self) -> None:
        """Exception causes exit with code 1."""
        with (
            patch("mobi_marker.gui.QApplication", side_effect=Exception("fail")),
            patch("mobi_marker.gui.sys.exit") as mock_exit,
            patch("builtins.print"),
        ):
            main()

        mock_exit.assert_called_once_with(1)
