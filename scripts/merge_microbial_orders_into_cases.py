import json
from pathlib import Path
import datetime as dt
from ruamel import yaml
import shutil
import click

from cg.store import Store, models

COMMENT = f"{dt.datetime.now().date()}: Imported from MicrobialSample/PG"


def dict_print(dict_):
    for key in sorted(dict_):
        print(f"{key}: {dict_.get(key)}")


@click.command("merge-microbial-data")
@click.option("-c", "--config-file", type=click.File())
def merge_microbial_data(config_file):
    """One-time script to merge MicrobialSample into Sample and MicrobialOrder into Family"""
    config = yaml.safe_load(config_file)
    store = Store(config["database"])

    for order in models.MicrobialOrder.query.all():
        click.echo(click.style("processing order: " + order.__str__(), fg="yellow"))
        dict_print(order.__dict__)

        case = store.find_family(order.customer, order.name)
        if not case:
            case = store.add_family(order.name, panels=None)
            case.customer_id = order.customer_id
            click.echo(click.style("Created case (Family): " + case.__str__(), fg="green"))
        else:
            click.echo(click.style("Found existing case (Family): " + case.__str__(), fg="yellow"))

        for ms in order.microbial_samples:

            click.echo(click.style("processing microbial sample: " + ms.__str__(), fg="yellow"))
            dict_print(ms.__dict__)

            sample = store.add_sample(
                        name=ms.name,
                        internal_id=ms.internal_id,
                        comment=COMMENT + "\n" + ms.comment if ms.comment else COMMENT,
                        priority=ms.priority_human,
                        data_analysis=ms.data_analysis,
                        customer=order.customer,
                        ticket=order.ticket_number,
                        sex="unknown"
            )

            sample.created_at = dt.datetime.now()
            sample.ordered_at = order.ordered_at
            sample.received_at = ms.received_at
            sample.prepared_at = ms.prepared_at
            sample.sequenced_at = ms.sequenced_at
            sample.delivered_at = ms.delivered_at
            sample.reads = ms.reads
            sample.invoice_id = ms.invoice_id
            sample.application_version_id = ms.application_version_id
            sample.customer_id = order.customer_id

            click.echo(click.style("Created Sample: " + sample.__str__(), fg="green"))

            case.priority = sample.priority
            click.echo(click.style(f"relating Sample {sample} to case (Family) {case}", fg="green"))
            store.relate_sample(family=case, sample=sample, status="unknown")
            click.echo(click.style("Saving Sample: " + sample.__str__(), fg="yellow"))
            dict_print(sample.__dict__)
            store.add(sample)

            # find flowcells for the microbial sample
            flowcells = ms.flowcells
            click.echo(click.style("found flowcells for microbial sample: " + flowcells,
                                   fg="yellow"))

            # relate the new sample to the flowcell
            for flowcell in flowcells:
                click.echo(click.style(f"Appending Sample {sample} to FC {flowcell}", fg="green"))
                flowcell.samples.append(sample)
                click.echo(click.style(f"Removing microbial sample {ms} from FC {flowcell}",
                                       fg="red"))
                flowcell.microbial_samples.remove(ms)

            click.echo(click.style("Deleting microbial sample: " + ms.__str__(), fg="red"))
            store.delete(ms)

        click.echo(click.style("Saving case (Family): " + case.__str__(), fg="yellow"))
        dict_print(case.__dict__)

        store.add(case)
        click.echo(click.style("Deleting microbial order: " + order.__str__(), fg="red"))
        store.delete(order)
        store.commit()


if __name__ == "__main__":
    merge_microbial_data()
