import logging
from pathlib import Path

from pydantic import BaseModel
from typing_extensions import Literal

LOG = logging.getLogger(__name__)


def gather_datasource(results_dir: Path):
    """Get the information from a run necessary to create a data source"""

    run_dir = Path(run_dir)
    rs = {}  # result set

    # get the run name
    rs["runname"] = str(run_dir.normpath().basename())

    # get the run date
    rs["rundate"] = rs["runname"].split("_")[0]

    # get the machine name
    rs["machine"] = rs["runname"].split("_")[1]

    # get the server name on which the demux took place
    rs["servername"] = socket.gethostname()

    # get the stats file
    document_path = run_dir.joinpath(unaligned_dir, "Stats/ConversionStats.xml")
    if not document_path.isfile():
        logger.error("Stats file not found at '%s'", document_path)
        import errno

        raise IOError(errno.ENOENT, os.strerror(errno.ENOENT), document_path)
    else:
        rs["document_path"] = str(document_path)

    return rs
