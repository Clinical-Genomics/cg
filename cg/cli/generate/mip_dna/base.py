"""Commands to generates and/or modify MIP rare disease DNA files"""

import click

from cg.meta.report.mip_dna import MipDNAReportAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.cli.generate.commands import delivery_report, available_delivery_reports


@click.group("mip-dna", invoke_without_command=True)
@click.pass_context
def mip_dna(context: click.Context):
    """Rare disease DNA file generation/modification"""

    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        return

    context.obj.meta_apis["report_api"] = MipDNAReportAPI(
        config=context.obj, analysis_api=MipDNAAnalysisAPI(config=context.obj)
    )


mip_dna.add_command(delivery_report)
mip_dna.add_command(available_delivery_reports)
