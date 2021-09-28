"""Tests for public methods in auto.py"""


def test_auto():
    """Test that create_app works"""
    # GIVEN all required configurations present in os.environ

    # WHEN app is imported from auto
    from cg.server.auto import app

    # THEN app exists
    assert app
