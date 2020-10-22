import click
from cg.store import Store, models
from ruamel import yaml


def contains_only_one_pipeline(pipelines: str) -> bool:
    return "+" not in pipelines and " and " not in pipelines


def copy_case(case: models.Family, store: Store) -> models.Family:
    new_case = store.add_family(
        data_analysis=case.data_analysis, name=case.name, panels=case.panels
    )
    for attr in ["action", "comment", "customer_id", "data_analysis", "ordered_at", "priority"]:
        new_case.__setattr__(attr, case.__getattribute__(attr))

    for link_obj in case.links:
        store.relate_sample(
            family=new_case,
            sample=link_obj.sample,
            status=link_obj.status,
            mother=link_obj.mother,
            father=link_obj.father,
        )

    return new_case


def ensure_one_case_per_pipeline(
    original_case: models.Family, pipelines_in_one: str, store: Store
) -> [models.Family]:

    cases: [models.Family] = [original_case]

    pipelines = set()
    for pipeline in ["mip", "balsamic", "rna"]:
        if pipeline in pipelines_in_one:
            pipelines.add(pipeline)

    while len(cases) < len(pipelines):
        new_case = copy_case(original_case, store)
        cases.append(new_case)

    for case in cases:
        case.data_analysis = pipelines.pop()
        case.name = f"{case.name}-{case.data_analysis}"

    return cases


@click.command("add-data-analysis-to-case")
@click.option("-c", "--config-file", type=click.File())
def add_data_analysis(config_file: click.File):
    """One-time script to add data analysis for all cases from Analysis table"""
    config = yaml.safe_load(config_file)
    store = Store(config["database"])

    for sample in (
        models.Sample.query.outerjoin(models.Sample.links).filter(models.Sample.links == None).all()
    ):
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
            click.echo(
                click.style(
                    f"Deleting test sample: {sample.__str__()}",
                    fg="red",
                )
            )
            store.delete(sample)
            click.echo(click.style(f"Deleted!"))
            continue

        new_case_name = sample.name
        i = 1
        while store.find_family(sample.customer, new_case_name):
            new_case_name = f"{sample.name}-{i}"
            i += 1

        case = store.add_family(data_analysis=sample.data_analysis, panels=None, name=new_case_name)
        sample.data_analysis = None
        case.comment = "created by data_analysis migration"
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
    for case in models.Family.query.filter(models.Family.data_analysis.is_(None)).all():

        click.echo(click.style("processing case : " + case.__str__(), fg="white"))

        skip_case = False
        analysis_pipelines = set()
        for analysis_obj in case.analyses:

            if not analysis_obj.pipeline:
                continue

            pipeline = analysis_obj.pipeline.lower().strip()
            analysis_pipelines.add(pipeline)

            if "mip" in pipeline and "balsamic" in pipeline:
                click.echo(
                    click.style(
                        f"Found analysis ({analysis_obj.__str__()}) with multiple pipelines on "
                        f"one analysis: "
                        f"{pipeline} ",
                        fg="red",
                    )
                )
                skip_case = True

            if len(analysis_pipelines) > 1:
                click.echo(
                    click.style(
                        f"Found case ({case.__str__()}) with multiple analysis pipelines: "
                        f"{analysis_pipelines} ",
                        fg="red",
                    )
                )
                skip_case = True

        data_analyses = set()
        for link_obj in case.links:

            if not link_obj.sample.data_analysis:
                continue

            data_analysis = link_obj.sample.data_analysis.lower().strip()
            data_analyses.add(data_analysis)

            if "mip" in data_analysis and "balsamic" in data_analysis:
                click.echo(
                    click.style(
                        f"Found sample ({link_obj.sample.__str__()}) with multiple data_analyses "
                        f"on same sample: "
                        f"{data_analysis} ",
                        fg="red",
                    )
                )
                skip_case = True

            if len(data_analyses) > 1:
                click.echo(
                    click.style(
                        f"Found case ({case.__str__()}) with multiple "
                        f"different sample.data_analysis: "
                        f"{data_analyses} ",
                        fg="red",
                    )
                )
                skip_case = True

        cases_processed = [case]
        if analysis_pipelines and len(analysis_pipelines) == 1:
            analysis_pipeline = analysis_pipelines.pop()
            if contains_only_one_pipeline(analysis_pipeline):
                case.data_analysis = analysis_pipeline
            else:
                cases_processed = ensure_one_case_per_pipeline(case, analysis_pipeline, store)
        elif data_analyses and len(data_analyses) == 1:
            data_analysis = data_analyses.pop()
            if contains_only_one_pipeline(data_analysis):
                case.data_analysis = data_analysis
            else:
                cases_processed = ensure_one_case_per_pipeline(case, data_analysis, store)
        elif (analysis_pipelines and len(analysis_pipelines) > 1) or (
            data_analyses and len(data_analyses) > 1
        ):
            click.echo(
                click.style(
                    f"Found unsupported case ({case.__str__()}) with multiple "
                    f"different data_analysis: "
                    f"{str(data_analyses)} and/or pipelines: {str(analysis_pipelines)}",
                    fg="red",
                )
            )
            if skip_case:
                continue

        for link_obj in case.links:
            link_obj.sample.data_analysis = None
            click.echo(
                click.style(
                    "Set data_analysis on: "
                    + link_obj.sample.__str__()
                    + " to: "
                    + str(link_obj.sample.data_analysis),
                    fg="green",
                )
            )

        for case_processed in cases_processed:
            if not case_processed.data_analysis:
                click.echo(
                    click.style(
                        "Case without any data_analysis: " + case_processed.__str__(),
                        fg="yellow",
                    )
                )

            click.echo(
                click.style(
                    "Set data_analysis on: "
                    + case_processed.__str__()
                    + " to: "
                    + str(case_processed.data_analysis),
                    fg="green",
                )
            )

        store.commit()


if __name__ == "__main__":
    add_data_analysis()
