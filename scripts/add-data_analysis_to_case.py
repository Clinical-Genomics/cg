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

    for case in models.Family.query.all():

        click.echo(click.style("processing case : " + case.__str__(), fg="white"))

        if not case.analyses:
            click.echo(
                click.style(
                    "Found case without analysis: " + case.__str__(),
                    fg="yellow",
                )
            )
            case.data_analysis = case.links[0].sample.data_analysis
        else:
            case.data_analysis = case.analyses[0].pipeline

        if not case.data_analysis:

            click.echo(
                click.style(
                    "Found case analysis without pipeline in analysis model: " + case.__str__(),
                    fg="red",
                )
            )
            return

    store.commit()


if __name__ == "__main__":
    add_data_analysis()
