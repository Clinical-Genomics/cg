"""Common CLI workflow functions"""

import click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.balsamic.base import balsamic
from cg.cli.workflow.balsamic.pon import balsamic_pon
from cg.cli.workflow.balsamic.qc import balsamic_qc
from cg.cli.workflow.balsamic.umi import balsamic_umi
from cg.cli.workflow.raw_data.base import raw_data
from cg.cli.workflow.fluffy.base import fluffy
from cg.cli.workflow.jasen.base import jasen
from cg.cli.workflow.microsalt.base import microsalt
from cg.cli.workflow.mip_dna.base import mip_dna
from cg.cli.workflow.mip_rna.base import mip_rna
from cg.cli.workflow.mutant.base import mutant
from cg.cli.workflow.raredisease.base import raredisease
from cg.cli.workflow.rnafusion.base import rnafusion
from cg.cli.workflow.taxprofiler.base import taxprofiler
from cg.cli.workflow.tomte.base import tomte


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
def workflow():
    """Workflows commands"""


workflow.add_command(balsamic)
workflow.add_command(balsamic_qc)
workflow.add_command(balsamic_umi)
workflow.add_command(balsamic_pon)
workflow.add_command(microsalt)
workflow.add_command(mip_dna)
workflow.add_command(mip_rna)
workflow.add_command(fluffy)
workflow.add_command(jasen)
workflow.add_command(mutant)
workflow.add_command(raredisease)
workflow.add_command(rnafusion)
workflow.add_command(taxprofiler)
workflow.add_command(tomte)
workflow.add_command(raw_data)
