"""Tests for public methods in app.py"""

from cg.server.app import create_app


def test_create_app():
    """Test that can do what it says ut can"""
    # GIVEN all required configurations present in os.environ

    # WHEN creating app
    app = create_app()

    # THEN app exists
    assert app
