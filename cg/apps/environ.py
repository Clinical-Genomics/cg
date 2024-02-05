""" Ask questions to the shell """

import getpass
import os


def environ_email():
    """Guess email from sudo user environment variable or login name."""
    username = os.environ.get("SUDO_USER")
    if not username:
        username = getpass.getuser()

    return f"{username}@scilifelab.se"
