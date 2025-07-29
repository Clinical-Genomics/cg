""" Ask questions to the shell """

import getpass
import os


def environ_email():
    """Guess email from sudo user environment variable or login name."""
    username = os.environ.get("SUDO_USER") or getpass.getuser()

    return f"{username}@scilifelab.se"
