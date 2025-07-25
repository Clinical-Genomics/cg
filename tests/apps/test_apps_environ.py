""" Test the environ app """

import os
from unittest import mock

from cg.apps.environ import environ_email


def test_environ_email_sudo():
    """Test getting the email based on SUDO_USER"""
    # GIVEN $SUDO_USER is set to a diplomat
    sudo_user = "chrisjen.avasarala"
    os.environ["SUDO_USER"] = sudo_user

    # WHEN asking for the email
    email = environ_email()

    # THEN it should provide us with the email
    assert email == f"{sudo_user}@scilifelab.se"


def test_environ_email_env(monkeypatch):
    """Test getting the email based on logged in user"""
    # GIVEN $SUDO_USER is not set
    user = "chrisjen.avasarala"

    # WHEN asking for the email
    with mock.patch("getpass.getuser", return_value=user):
        email = environ_email()

    # THEN it should provide us with the email
    assert email == f"{user}@scilifelab.se"
