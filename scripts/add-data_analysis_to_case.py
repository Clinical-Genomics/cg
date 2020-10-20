import click
from cg.store import Store, models
from ruamel import yaml


@click.command("add-data-analysis-to-case")
@click.option("-c", "--config-file", type=click.File())
def add_data_analysis(config_file: click.File):
    """One-time script to add data analysis for all cases from Analysis table"""
    config = yaml.safe_load(config_file)
    store = Store(config["database"])

    for sample in models.Sample.query.outerjoin(models.Sample.links).filter(models.Sample.links
                                                                            is None
                                                                            ).all():
        # if sample has links then we deal with it later in case processing
        if sample.links:
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

        if sample.name == "4321":
            click.echo(click.style(
                f"Deleting test sample: {sample.__str__()}?",
                fg="red",
            ))
            store.delete(sample)
            click.echo(
                click.style(
                    f"Deleted!"
                )
            )
            continue

        case = store.add_family(data_analysis=sample.data_analysis, panels=None, name=sample.name)
        sample.data_analysis = None
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
        store.commit()

    # pull data_analysis from sample to case
    for case in models.Family.query.filter(
            models.Family.data_analysis.is_(None)
    ).all():

        click.echo(click.style("processing case : " + case.__str__(), fg="white"))

        analysis_pipelines = set()
        for analysis_obj in case.analyses:
            if analysis_obj.pipeline:
                analysis_pipelines.add(analysis_obj.pipeline.lower())

            if (
                    len(analysis_pipelines) > 1
            ):
                click.echo(
                    click.style(
                        f"Found case ({case.__str__()}) with multiple pipelines: {analysis_pipelines} ",
                        fg="red",
                    )
                )

        data_analyses = set()
        for link_obj in case.links:
            if link_obj.sample.data_analysis:
                data_analyses.add(link_obj.sample.data_analysis.lower())

            if (
                    len(data_analyses) > 1
            ):
                click.echo(
                    click.style(
                        f"Found case ({case.__str__()}) with multiple data_analyses: {data_analyses} ",
                        fg="red",
                    )
                )

        if analysis_pipelines:
            if len(analysis_pipelines) == 1:
                case.data_analysis = analysis_pipelines.pop()
            else:
                case.data_analysis = "|".join(analysis_pipelines)
        elif data_analyses:
            if len(data_analyses) == 1:
                case.data_analysis = data_analyses.pop()
            else:
                case.data_analysis = "|".join(data_analyses)
        else:
            case.data_analysis = ""

        for link_obj in case.links:
            link_obj.sample.data_analysis = None

        if not case.data_analysis:
            click.echo(
                click.style(
                    "Case without any data_analysis: " + case.__str__(),
                    fg="yellow",
                )
            )

        click.echo(
            click.style(
                "Set data_analysis on: " + case.__str__() + " to: " + case.data_analysis,
                fg="green",
            )
        )

        store.commit()


if __name__ == "__main__":
    add_data_analysis()
