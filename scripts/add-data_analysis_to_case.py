import datetime as dt

import click
from cg.store import Store, models
from ruamel import yaml


def dict_print(dict_):
    for key in sorted(dict_):
        print(f"{key}: {dict_.get(key)}")


@click.command("add-data-analysis-to-case")
@click.option("-c", "--config-file", type=click.File())
def add_data_analysis(config_file):
    """One-time script to add data analysis for all cases from Analysis table"""
    config = yaml.safe_load(config_file)
    store = Store(config["database"])

    for analyses in models.Analysis.query.all():

        for case_analysis in analyses.family_id:

            if not case_analysis.pipeline:

                click.echo(
                    click.style(
                        "Found case analysis without pipeline in analysis model: "
                        + case_analysis.__str__(),
                        fg="red",
                    )
                )
                return

            click.echo(
                click.style("processing case : " + case_analysis.family_id.__str__(), fg="white")
            )


#            case = case = store.add_analysis_to_case(
#            name=str(ticket), panels=None, priority=microbial_sample.priority_human
#        )
#        click.echo(
#            click.style("changed ticket to: " + str(microbial_sample.ticket_number), fg="green")
#        )

#    store.commit()

if __name__ == "__main__":
    add_data_analysis()
