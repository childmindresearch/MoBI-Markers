"""Tests for the main entry point."""


def test_import() -> None:
    """Main function is importable and callable."""
    from mobi_marker import main

    assert callable(main)
