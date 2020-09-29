import datetime as dt

import click
from cg.store import Store, models
from ruamel import yaml

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

        for ms in order.microbial_samples:

            click.echo(click.style("processing microbial sample: " + ms.__str__(), fg="yellow"))
            dict_print(ms.__dict__)

            data_analysis = "microbial|" + ms.data_analysis if ms.data_analysis else "microbial"

            sample = store.add_sample(
                application_version_id=ms.application_version_id,
                comment=COMMENT + "\n" + ms.comment if ms.comment else COMMENT,
                created_at=dt.datetime.now(),
                customer_id=order.customer_id,
                data_analysis=data_analysis,
                delivered_at=ms.delivered_at,
                internal_id=ms.internal_id,
                invoice_id=ms.invoice_id,
                name=ms.name,
                order=order.name,
                ordered=order.ordered_at,
                organism_id=ms.organism_id,
                prepared_at=ms.prepared_at,
                priority=ms.priority_human,
                reads=ms.reads,
                received=ms.received_at,
                reference_genome=ms.reference_genome,
                sequence_start=ms.sequence_start,
                sequenced_at=ms.sequenced_at,
                sex="unknown",
                ticket=order.ticket_number,
            )
            if sample.invoice:
                sample.invoice.record_type = "Sample"

            click.echo(click.style("Saving Sample: " + sample.__str__(), fg="yellow"))
            dict_print(sample.__dict__)
            store.add(sample)

            # find flowcells for the microbial sample
            flowcells = ms.flowcells
            click.echo(
                click.style(
                    "found flowcells for microbial sample: " + flowcells.__str__(), fg="yellow"
                )
            )

            # relate the new sample to the flowcell
            for flowcell in flowcells:
                click.echo(click.style(f"Appending Sample {sample} to FC {flowcell}", fg="green"))
                flowcell.samples.append(sample)
                click.echo(
                    click.style(f"Removing microbial sample {ms} from FC {flowcell}", fg="red")
                )
                flowcell.microbial_samples.remove(ms)

            click.echo(click.style("Deleting microbial sample: " + ms.__str__(), fg="red"))
            store.delete(ms)

        click.echo(click.style("Deleting microbial order: " + order.__str__(), fg="red"))
        store.delete(order)
        store.commit()


if __name__ == "__main__":
    merge_microbial_data()
