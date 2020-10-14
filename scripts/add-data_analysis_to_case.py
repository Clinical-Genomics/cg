import click
from cg.store import Store, models
from ruamel import yaml


def dict_print(dict_):
    for key in sorted(dict_):
        print(f"{key}: {dict_.get(key)}")


@click.command("add-data-analysis-to-case")
@click.option("-c", "--config-file", type=click.File())
def add_data_analysis(config_file: click.File):
    """One-time script to add data analysis for all cases from Analysis table"""
    config = yaml.safe_load(config_file)
    store = Store(config["database"])

    for sample in models.Sample.query.all():
        # if sample has links then we deal with it later in case processing
        # if sample does have empty data_analysis then its ok to put on case
        # if sample is fastq then ??
        if sample.links or not sample.data_analysis or sample.data_analysis == "fastq":
            print(".", end="", flush=True)
            continue

        print(".")
        click.echo(
            click.style(
                "Found sample without case: "
                + sample.__str__()
                + " data_analysis: "
                + str(sample.data_analysis)
                + " reads: "
                + str(sample.reads)
                + " comment: "
                + str(sample.comment),
                fg="yellow",
            )
        )
        # if sample.reads == 0 and click.confirm(click.style(
        #             f"Delete sample: {sample.__str__()}?",
        #             fg="red",
        #         )):
        #     store.delete(sample)
        #     click.echo(
        #         click.style(
        #             f"Deleted!"
        #         )
        #     )
        #     continue

        case = store.add_family(data_analysis=sample.data_analysis, panels=None, name=sample.name)
        case.customer_id = sample.customer.id
        click.echo(
            click.style(
                "Added case: " + case.__str__(),
                fg="green",
            )
        )
        click.echo(
            click.style(
                "relating sample to case: " + sample.__str__(),
                fg="green",
            )
        )
        store.relate_sample(sample=sample, family=case, status="unknown")

    # pull data_analysis from sample to case
    for case in models.Family.query.all():

        click.echo(click.style("processing case : " + case.__str__(), fg="white"))

        data_analysis = None
        for link_obj in case.links:
            if (
                data_analysis
                and link_obj.sample.data_analysis
                and data_analysis != link_obj.sample.data_analysis
            ):
                click.echo(
                    click.style(
                        "Found case with mixed data_analysis: " + case.__str__(),
                        fg="red",
                    )
                )
                continue

            data_analysis = data_analysis or link_obj.sample.data_analysis

        if case.analyses:
            case.data_analysis = case.analyses[0].pipeline
        else:
            click.echo(
                click.style(
                    "Found case without analysis: " + case.__str__(),
                    fg="yellow",
                )
            )
            case.data_analysis = data_analysis

        for link_obj in case.links:
            link_obj.sample.data_analysis = None

        if not case.data_analysis:
            click.echo(
                click.style(
                    "Case without any data_analysis: " + case.__str__(),
                    fg="yellow",
                )
            )
            continue

        click.echo(
            click.style(
                "Set data_analysis on: " + case.__str__() + " to: " + case.data_analysis,
                fg="green",
            )
        )

    store.commit()


if __name__ == "__main__":
    add_data_analysis()
