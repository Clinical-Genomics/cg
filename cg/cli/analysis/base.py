"""Adds cg cli analysis command and sub commands"""

from cg.cli.analysis.analysis import analysis
from cg.cli.analysis.balsamic import balsamic
from cg.cli.analysis.microsalt import microsalt
from cg.cli.analysis.mip_rd_dna import mip_dna
from cg.cli.analysis.mip_rd_rna import mip_rna

analysis.add_command(balsamic)
analysis.add_command(microsalt)
analysis.add_command(mip_dna)
analysis.add_command(mip_rna)
