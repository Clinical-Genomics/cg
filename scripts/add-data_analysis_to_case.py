import click
from cg.store import Store, models
from ruamel import yaml


def contains_both_balsamic_and_mip(pipelines: str) -> bool:
    return "mip" in pipelines and "balsamic" in pipelines


def copy_case(case: models.Family, store: Store) -> models.Family:
    new_case_name = f"{case.name}-copy"
    i = 2
    while store.find_family(case.customer, new_case_name):
        new_case_name = f"{case.name}-copy-{i}"
        i += 1

    new_case = store.add_family(
        data_analysis=case.data_analysis, name=new_case_name, panels=case.panels
    )

    new_case.comment = "created by data_analysis migration"
    for attr in ["action", "customer_id", "data_analysis", "ordered_at", "priority"]:
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
    pipeline_map = {"rna": "MIP + RNA", "mip": "MIP", "balsamic": "Balsamic"}

    cases: [models.Family] = [original_case]
    original_case_name: str = original_case.name

    pipelines = set()
    for pipeline in pipeline_map.keys():
        if pipeline in pipelines_in_one:
            pipelines.add(pipeline)

    while len(cases) < len(pipelines):
        new_case = copy_case(original_case, store)
        cases.append(new_case)

    for case in cases:
        pipeline = pipelines.pop()
        case.data_analysis = pipeline_map.get(pipeline)
        case.name = f"{original_case_name}-{pipeline}"

    return cases


@click.command("add-data-analysis-to-case")
@click.option("-c", "--config-file", type=click.File())
def add_data_analysis(config_file: click.File):
    """One-time script to add data analysis for all cases from Analysis table"""
    config = yaml.safe_load(config_file)
    store = Store(config["database"])

    ensure_each_sample_has_a_case(store)

    pull_data_analysis_from_sample_to_case(store)


def pull_data_analysis_from_sample_to_case(store):
    for case in models.Family.query.filter(models.Family.data_analysis.is_(None)).all():

        click.echo(click.style("processing case : " + case.__str__(), fg="white"))

        if case.data_analysis:
            continue

        analysis_pipelines = get_analysis_pipelines(case)
        data_analyses = get_data_analyses(case)

        cases_processed = [case]
        if analysis_pipelines and len(analysis_pipelines) == 1:
            analysis_pipeline = analysis_pipelines.pop()
            if not contains_both_balsamic_and_mip(analysis_pipeline):
                case.data_analysis = analysis_pipeline
            else:
                cases_processed = ensure_one_case_per_pipeline(case, analysis_pipeline, store)
        elif data_analyses and len(data_analyses) == 1:
            data_analysis = data_analyses.pop()
            if not contains_both_balsamic_and_mip(data_analysis):
                case.data_analysis = data_analysis
            else:
                cases_processed = ensure_one_case_per_pipeline(case, data_analysis, store)
        elif (analysis_pipelines and len(analysis_pipelines) > 1) or (
            data_analyses and len(data_analyses) > 1
        ):
            pipelines = " ".join(data_analyses) + " ".join(analysis_pipelines)
            cases_processed = ensure_one_case_per_pipeline(case, pipelines, store)

        reset_data_analysis_on_samples(case)

        output_case_data_analysis_change(cases_processed)

        store.commit()


def get_data_analyses(case):
    data_analyses = set()
    data_analyses.clear()
    for link_obj in case.links:

        if not link_obj.sample.data_analysis:
            continue

        data_analysis = link_obj.sample.data_analysis.lower().strip()
        data_analyses.add(data_analysis)

        if contains_both_balsamic_and_mip(data_analysis):
            click.echo(
                click.style(
                    f"Found sample ({link_obj.sample.__str__()}) with multiple data_analyses "
                    f"on same sample: "
                    f"{data_analysis} ",
                    fg="yellow",
                )
            )

        if len(data_analyses) > 1:
            click.echo(
                click.style(
                    f"Found case ({case.__str__()}) with multiple "
                    f"different sample.data_analysis: "
                    f"{data_analyses} ",
                    fg="yellow",
                )
            )
    return data_analyses


def get_analysis_pipelines(case):
    analysis_pipelines = set()
    analysis_pipelines.clear()
    for analysis_obj in case.analyses:

        if not analysis_obj.pipeline:
            continue

        pipeline = analysis_obj.pipeline.lower().strip()
        analysis_pipelines.add(pipeline)

        if contains_both_balsamic_and_mip(pipeline):
            click.echo(
                click.style(
                    f"Found analysis ({analysis_obj.__str__()}) with multiple pipelines on "
                    f"one analysis: "
                    f"{pipeline} ",
                    fg="yellow",
                )
            )

        if len(analysis_pipelines) > 1:
            click.echo(
                click.style(
                    f"Found case ({case.__str__()}) with multiple analysis pipelines: "
                    f"{analysis_pipelines} ",
                    fg="yellow",
                )
            )
    return analysis_pipelines


def output_case_data_analysis_change(cases_processed):
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


def reset_data_analysis_on_samples(case):
    for link_obj in case.links:
        click.echo(
            click.style(
                f"Set data_analysis on: {link_obj.sample.__str__()} from: "
                f"{str(link_obj.sample.data_analysis)} to: None",
                fg="green",
            )
        )
        link_obj.sample.data_analysis = None


def ensure_each_sample_has_a_case(store: Store) -> None:
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


if __name__ == "__main__":
    add_data_analysis()
