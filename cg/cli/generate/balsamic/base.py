"""Commands to generates and/or modify BALSAMIC files"""

import click

from cg.meta.report.balsamic import BalsamicReportAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.cli.generate.commands import delivery_report, available_delivery_reports


@click.group("balsamic", invoke_without_command=True)
@click.pass_context
def balsamic(context: click.Context):
    """Balsamic file generation/modification"""

    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        return

    context.obj.meta_apis["report_api"] = BalsamicReportAPI(
        config=context.obj, analysis_api=BalsamicAnalysisAPI(config=context.obj)
    )


balsamic.add_command(delivery_report)
balsamic.add_command(available_delivery_reports)
