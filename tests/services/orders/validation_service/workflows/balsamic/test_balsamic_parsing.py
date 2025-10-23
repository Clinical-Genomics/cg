from typing import cast

from cg.services.orders.validation.order_types.balsamic.models.case import BalsamicCase
from cg.services.orders.validation.order_types.balsamic.models.order import BalsamicOrder
from cg.services.orders.validation.order_types.balsamic.models.sample import BalsamicSample


def test_balsamic_parsing():
    balsamic_order = {
        "comment": None,
        "customer": "cust000",
        "delivery_type": "fastq-analysis",
        "project_type": "balsamic",
        "name": "order_name",
        "skip_reception_control": False,
        "cases": [
            {
                "name": "name",
                "priority": "standard",
                "samples": [
                    {
                        "application": "PANKTTR020",
                        "comment": None,
                        "container": "96 well plate",
                        "container_name": "ContainerName",
                        "name": "name1",
                        "volume": 20,
                        "well_position": "A:1",
                        "age_at_sampling": None,
                        "capture_kit": "GIcfDNA",
                        "concentration_ng_ul": None,
                        "control": "",
                        "elution_buffer": "Nuclease-free water",
                        "formalin_fixation_time": None,
                        "phenotype_groups": None,
                        "phenotype_terms": None,
                        "post_formalin_fixation_time": None,
                        "require_qc_ok": True,
                        "sex": "female",
                        "source": "other",
                        "source_comment": "source from comment",
                        "status": "affected",
                        "subject_id": "subject1",
                        "tissue_block_size": None,
                        "tumour": False,
                        "tumour_purity": None,
                    }
                ],
                "cohorts": None,
                "synopsis": None,
            }
        ],
    }

    parsed_order = BalsamicOrder.model_validate(balsamic_order)

    assert parsed_order

    assert (
        cast(BalsamicSample, cast(BalsamicCase, parsed_order.cases[0]).samples[0]).source
        == "source from comment"
    )
