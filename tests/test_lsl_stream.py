"""Tests for the LSL stream module."""

from unittest.mock import Mock, patch

from mobi_marker.lsl_stream import (
    LSLStreamThread,
    format_status_message,
    format_timestamp,
)


class TestFormatTimestamp:
    """Tests for format_timestamp function."""

    def test_returns_human_time_and_lsl_time(self) -> None:
        """Returns tuple of human-readable time and LSL clock."""
        with patch("mobi_marker.lsl_stream.local_clock", return_value=123.456):
            human_time, lsl_time = format_timestamp()

        assert isinstance(human_time, str)
        assert lsl_time == 123.456

    def test_human_time_format(self) -> None:
        """Human time follows expected format."""
        with patch("mobi_marker.lsl_stream.local_clock", return_value=0):
            human_time, _ = format_timestamp()

        # Should contain date and time components
        assert "-" in human_time  # date separator
        assert ":" in human_time  # time separator


class TestFormatStatusMessage:
    """Tests for format_status_message function."""

    def test_includes_message(self) -> None:
        """Formatted message includes the input message."""
        with patch("mobi_marker.lsl_stream.local_clock", return_value=100.0):
            result = format_status_message("Test message")

        assert "Test message" in result

    def test_includes_timestamps(self) -> None:
        """Formatted message includes LSL timestamp."""
        with patch("mobi_marker.lsl_stream.local_clock", return_value=100.0):
            result = format_status_message("Test")

        assert "100.000" in result


class TestLSLStreamThreadInit:
    """Tests for LSLStreamThread initialization."""

    def test_initializes_with_none_outlet(self) -> None:
        """Outlet is None before stream starts."""
        with (
            patch("mobi_marker.lsl_stream.StreamInfo"),
            patch("mobi_marker.lsl_stream.StreamOutlet"),
        ):
            thread = LSLStreamThread()

        assert thread.outlet is None

    def test_initializes_with_none_stream_info(self) -> None:
        """Stream info is None before stream starts."""
        with (
            patch("mobi_marker.lsl_stream.StreamInfo"),
            patch("mobi_marker.lsl_stream.StreamOutlet"),
        ):
            thread = LSLStreamThread()

        assert thread.stream_info is None

    def test_initializes_not_ready(self) -> None:
        """Thread is not ready before run() is called."""
        with (
            patch("mobi_marker.lsl_stream.StreamInfo"),
            patch("mobi_marker.lsl_stream.StreamOutlet"),
        ):
            thread = LSLStreamThread()

        assert thread._is_ready is False


class TestLSLStreamThreadRun:
    """Tests for LSLStreamThread.run() method."""

    def test_run_success_sets_outlet(self) -> None:
        """Successful run sets the outlet."""
        mock_outlet = Mock()
        with (
            patch("mobi_marker.lsl_stream.StreamInfo"),
            patch("mobi_marker.lsl_stream.StreamOutlet", return_value=mock_outlet),
            patch("mobi_marker.lsl_stream.local_clock", return_value=0),
            patch.object(LSLStreamThread, "exec"),
        ):
            thread = LSLStreamThread()

            thread.run()

        assert thread.outlet == mock_outlet

    def test_run_success_sets_ready(self) -> None:
        """Successful run sets _is_ready to True."""
        with (
            patch("mobi_marker.lsl_stream.StreamInfo"),
            patch("mobi_marker.lsl_stream.StreamOutlet"),
            patch("mobi_marker.lsl_stream.local_clock", return_value=0),
            patch.object(LSLStreamThread, "exec"),
        ):
            thread = LSLStreamThread()

            thread.run()

        assert thread._is_ready is True

    def test_run_success_emits_stream_ready_true(self) -> None:
        """Successful run emits stream_ready with True."""
        with (
            patch("mobi_marker.lsl_stream.StreamInfo"),
            patch("mobi_marker.lsl_stream.StreamOutlet"),
            patch("mobi_marker.lsl_stream.local_clock", return_value=0),
            patch.object(LSLStreamThread, "exec"),
        ):
            thread = LSLStreamThread()
            ready_signals: list[bool] = []
            thread.stream_ready.connect(ready_signals.append)

            thread.run()

        assert ready_signals == [True]

    def test_run_success_emits_status_update(self) -> None:
        """Successful run emits status update with success message."""
        with (
            patch("mobi_marker.lsl_stream.StreamInfo"),
            patch("mobi_marker.lsl_stream.StreamOutlet"),
            patch("mobi_marker.lsl_stream.local_clock", return_value=0),
            patch.object(LSLStreamThread, "exec"),
        ):
            thread = LSLStreamThread()
            status_messages: list[str] = []
            thread.status_update.connect(status_messages.append)

            thread.run()

        assert len(status_messages) == 1
        assert "started successfully" in status_messages[0]

    def test_run_failure_emits_stream_ready_false(self) -> None:
        """Failed run emits stream_ready with False."""
        with (
            patch("mobi_marker.lsl_stream.StreamInfo", side_effect=Exception("fail")),
            patch("mobi_marker.lsl_stream.local_clock", return_value=0),
        ):
            thread = LSLStreamThread()
            ready_signals: list[bool] = []
            thread.stream_ready.connect(ready_signals.append)

            thread.run()

        assert ready_signals == [False]

    def test_run_failure_emits_error_status(self) -> None:
        """Failed run emits status update with error message."""
        with (
            patch(
                "mobi_marker.lsl_stream.StreamInfo", side_effect=Exception("test error")
            ),
            patch("mobi_marker.lsl_stream.local_clock", return_value=0),
        ):
            thread = LSLStreamThread()
            status_messages: list[str] = []
            thread.status_update.connect(status_messages.append)

            thread.run()

        assert len(status_messages) == 1
        assert "Error" in status_messages[0]
        assert "test error" in status_messages[0]


class TestLSLStreamThreadSendMarker:
    """Tests for LSLStreamThread.send_marker() method."""

    def test_send_marker_when_not_ready_emits_error(self) -> None:
        """Sending marker when not ready emits error status."""
        with (
            patch("mobi_marker.lsl_stream.StreamInfo"),
            patch("mobi_marker.lsl_stream.StreamOutlet"),
            patch("mobi_marker.lsl_stream.local_clock", return_value=0),
        ):
            thread = LSLStreamThread()
            status_messages: list[str] = []
            thread.status_update.connect(status_messages.append)

            thread.send_marker("TEST")

        assert len(status_messages) == 1
        assert "not active" in status_messages[0]

    def test_send_marker_when_ready_emits_request(self) -> None:
        """Sending marker when ready emits marker_request signal."""
        with (
            patch("mobi_marker.lsl_stream.StreamInfo"),
            patch("mobi_marker.lsl_stream.StreamOutlet"),
        ):
            thread = LSLStreamThread()
            thread._is_ready = True
            marker_requests: list[str] = []
            thread.marker_request.connect(marker_requests.append)

            thread.send_marker("TEST_MARKER")

        assert marker_requests == ["TEST_MARKER"]


class TestLSLStreamThreadHandleMarkerRequest:
    """Tests for LSLStreamThread._handle_marker_request() method."""

    def test_handle_request_with_outlet_pushes_sample(self) -> None:
        """Handler with valid outlet calls push_sample."""
        mock_outlet = Mock()
        with (
            patch("mobi_marker.lsl_stream.StreamInfo"),
            patch("mobi_marker.lsl_stream.StreamOutlet"),
            patch("mobi_marker.lsl_stream.local_clock", return_value=0),
        ):
            thread = LSLStreamThread()
            thread.outlet = mock_outlet

            thread._handle_marker_request("MARKER")

        mock_outlet.push_sample.assert_called_once_with(["MARKER"])

    def test_handle_request_success_emits_status(self) -> None:
        """Successful marker send emits status update."""
        mock_outlet = Mock()
        with (
            patch("mobi_marker.lsl_stream.StreamInfo"),
            patch("mobi_marker.lsl_stream.StreamOutlet"),
            patch("mobi_marker.lsl_stream.local_clock", return_value=0),
        ):
            thread = LSLStreamThread()
            thread.outlet = mock_outlet
            status_messages: list[str] = []
            thread.status_update.connect(status_messages.append)

            thread._handle_marker_request("MY_MARKER")

        assert len(status_messages) == 1
        assert "Sent marker: MY_MARKER" in status_messages[0]

    def test_handle_request_with_none_outlet_emits_error(self) -> None:
        """Handler with None outlet emits error status."""
        with (
            patch("mobi_marker.lsl_stream.StreamInfo"),
            patch("mobi_marker.lsl_stream.StreamOutlet"),
            patch("mobi_marker.lsl_stream.local_clock", return_value=0),
        ):
            thread = LSLStreamThread()
            thread.outlet = None
            status_messages: list[str] = []
            thread.status_update.connect(status_messages.append)

            thread._handle_marker_request("MARKER")

        assert len(status_messages) == 1
        assert "not active" in status_messages[0]

    def test_handle_request_push_failure_emits_error(self) -> None:
        """Handler emits error when push_sample fails."""
        mock_outlet = Mock()
        mock_outlet.push_sample.side_effect = Exception("push failed")
        with (
            patch("mobi_marker.lsl_stream.StreamInfo"),
            patch("mobi_marker.lsl_stream.StreamOutlet"),
            patch("mobi_marker.lsl_stream.local_clock", return_value=0),
        ):
            thread = LSLStreamThread()
            thread.outlet = mock_outlet
            status_messages: list[str] = []
            thread.status_update.connect(status_messages.append)

            thread._handle_marker_request("MARKER")

        assert len(status_messages) == 1
        assert "Error sending marker" in status_messages[0]
        assert "push failed" in status_messages[0]
