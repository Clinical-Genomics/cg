# Sample/Analysis queues

There's a list of queues available in the [portal][portal] for keeping track of samples.

Most queues are based around dates in _status_. You can manually set a sample as e.g. "sequenced" by logging into the database [admin inteface][clinical-api].

## Incoming samples

Samples where the order has been placed but the samples haven't been given a "reception date" in LIMS.

External (based on application) and downsampled samples are excluded. If a sample is marked as "sequenced" they also dissaprear from this queue.

Samples are sorted on the date they were ordered.

## Samples to prep

Samples that have been received but not marked as prepared in LIMS.

External/downsampled samples are excluded. Also samples marked as "sequenced" are excluded.

Samples are ordered by priority first and reception date second.

## Samples to sequence

Samples that have been prepared but not yet _completely_ sequenced.

External/downsampled samples are excluded. Pools of RML samples currently don't show up in this list.

Samples are sorted by priority, and reception date.

## Families to analyze

Families where _each_ of the samples have been marked "sequenced" and who haven't been analyzed before OR who have the action set to "analyze".

Families with actions other than "analyze" are excluded ("running", "hold" etc.) You can manually set a family to show up in the queue by running:

    cg set family --action analyze FAMILY-ID

Families are sorted based on priority and date of order.

Analysis for families in this queue are automatically started.

    @ rasta:~/servers/crontab/analysis-auto.sh
    $ cg analysis auto
    $ cg analysis -f FAMILY-ID

## Analyses to upload

Analyses that have successfully completed but haven't yet uploaded.

Analyses in this queue are automatically uploaded.

    @ rasta:~/servers/crontab/upload-auto.sh
    $ cg upload auto
    $ cg upload -f FAMILY-ID

## Analyses to deliver

Currently not in use :warning:

[portal]: https://clinical.scilifelab.se/
[clinical-api]: https://clinical-api.scilifelab.se/admin/
