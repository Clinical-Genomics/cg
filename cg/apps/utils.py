import subprocess
from subprocess import CalledProcessError

def execute_command(cmd):
    """
        Prints stdout + stderr of command in real-time while being executed

        Args:
            cmd (list): command sequence

        Yields:
            line (str): line of output from command
    """
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               bufsize=1)

    for line in process.stdout:
        yield line.decode('utf-8').strip()

    def process_failed(process):
        """See if process failed by checking returncode"""
        return process.poll() != 0

    if process_failed(process):
        raise CalledProcessError(returncode=process.returncode, cmd=cmd)

