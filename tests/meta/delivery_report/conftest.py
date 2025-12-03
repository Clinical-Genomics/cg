from unittest.mock import create_autospec

import pytest

from cg.constants import SexOptions
from cg.models.analysis import NextflowAnalysis
from cg.models.balsamic.analysis import BalsamicAnalysis
from cg.models.balsamic.config import (
    BalsamicConfigAnalysis,
    BalsamicConfigJSON,
    BalsamicConfigPanel,
)
from cg.models.balsamic.metrics import BalsamicTargetedQCMetrics, BalsamicWGSQCMetrics
from cg.models.nallo.nallo import NalloQCMetrics
from cg.models.rnafusion.rnafusion import RnafusionQCMetrics
from cg.models.tomte.tomte import TomteQCMetrics

EXPECTED_BALSAMIC_QC_TABLE_TGA = """<h4 class="mt-4 mb-3">Kvalitetsmått</h4>\n  <table class="table w-auto text-center align-middle" aria-describedby="qc-metrics-table">\n    <thead class="table-secondary">\n      <tr>\n        <th scope="col">Kvalitetsmått</th>\n        \n          <th scope="col">sample_name (sample_id)</th>\n        \n        <th scope="col">Förklaringar</th>\n      </tr>\n    </thead>\n    <tbody>\n      \n      <tr>\n        <th scope="row">Kön</th>\n        \n          <td>Man</td>\n        \n        <td class="text-start">Kön beräknat genom bioinformatisk analys.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Läspar [M]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Antal sekvenseringsläsningar i miljoner läspar.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Duplikat [%]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Sekvenseringsläsningar som är i duplikat och därmed ej unika sekvenser. Hög mängd duplikat kan tyda på dålig komplexitet av sekvenserat bibliotek eller djup sekvensering.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Medelfragmentlängd [baspar]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Medelstorlek av provbiblioteken som laddats på sekvenseringsinstrument.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Fold 80 base penalty</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Jämnhet av täckningsgraden över alla gener i analyspanlen.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Mediantäckning [baser]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Median av täckningen över alla baser inkluderade i analysen. Det beräknas efter borttagning av duplikata läsningar.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Täckningsgrad 250x [%]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Andel baser som är sekvenserade med ett djup över en specificerad gräns (250x). Det beräknas efter borttagning av duplikata läsningar.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Täckningsgrad 500x [%]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Andel baser som är sekvenserade med ett djup över en specificerad gräns (500x). Det beräknas efter borttagning av duplikata läsningar.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">GC Dropout [%]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Ett mått på hur dåligt täckta områden, med &gt;= 50% GC innehåll, är i jämförelse med medelvärdet. Om värdet är 5%, innebär det att 5% av alla läsningar som borde ha kartlagts till områden med GC &lt;= 50%, kartlades någon annanstans.</td>\n      </tr>\n      \n    </tbody>\n  </table>"""
EXPECTED_BALSAMIC_QC_TABLE_WGS = """<h4 class="mt-4 mb-3">Kvalitetsmått</h4>\n  <table class="table w-auto text-center align-middle" aria-describedby="qc-metrics-table">\n    <thead class="table-secondary">\n      <tr>\n        <th scope="col">Kvalitetsmått</th>\n        \n          <th scope="col">sample_name (sample_id)</th>\n        \n        <th scope="col">Förklaringar</th>\n      </tr>\n    </thead>\n    <tbody>\n      \n      <tr>\n        <th scope="row">Kön</th>\n        \n          <td>Kvinna</td>\n        \n        <td class="text-start">Kön beräknat genom bioinformatisk analys.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Läspar [M]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Antal sekvenseringsläsningar i miljoner läspar.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Duplikat [%]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Sekvenseringsläsningar som är i duplikat och därmed ej unika sekvenser. Hög mängd duplikat kan tyda på dålig komplexitet av sekvenserat bibliotek eller djup sekvensering.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Medelfragmentlängd [baspar]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Medelstorlek av provbiblioteken som laddats på sekvenseringsinstrument.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Fold 80 base penalty</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Jämnhet av täckningsgraden över alla gener i analyspanlen.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Täckningsgrad 15x [%]</th>\n        \n          <td>100.0</td>\n        \n        <td class="text-start">Andel baser som är sekvenserade med ett djup över en specificerad gräns (15x). Det beräknas efter borttagning av duplikata läsningar.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Täckningsgrad 60x [%]</th>\n        \n          <td>100.0</td>\n        \n        <td class="text-start">Andel baser som är sekvenserade med ett djup över en specificerad gräns (60x). Det beräknas efter borttagning av duplikata läsningar.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Mediantäckning [baser]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Median av täckningen över alla baser inkluderade i analysen. Det beräknas efter borttagning av duplikata läsningar.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Läsningar med felaktiga par [%]</th>\n        \n          <td>100.0</td>\n        \n        <td class="text-start">Andelen (primära) läsningar som inte är korrekt parvis justerade.</td>\n      </tr>\n      \n    </tbody>\n  </table>\n\n"""
EXPECTED_RNAFUSION_QC_TABLE_WTS = """<table class="table w-auto text-center align-middle" aria-describedby="qc-metrics-table">\n    <thead class="table-secondary">\n      <tr>\n        <th scope="col">Kvalitetsmått</th>\n        \n          <th scope="col">sample_name (sample_id)</th>\n        \n        <th scope="col">Förklaringar</th>\n      </tr>\n    </thead>\n    <tbody>\n      \n      <tr>\n        <th scope="row">RNA Integrity Number (RIN)</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Mått på skala från 1 till 10 för kvalitet och integritet hos RNA-prover. N/A som värde är en varning om att inget tillförlitligt RIN är tillgängligt för det specifika provet.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">DV200</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Andelen RNA-fragment längre än 200 nukleotider.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Ingående mängd [ng]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Mängd RNA som används för sekvensering.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Läspar [M]</th>\n        \n          <td>0.0</td>\n        \n        <td class="text-start">Antal sekvenseringsläsningar i miljoner läspar.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Mappade sekvenser [%]</th>\n        \n          <td>200.0</td>\n        \n        <td class="text-start">Procent sekvenser som matchar en eller flera positioner i referensgenomet.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Unikt mappade sekvenser [%]</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Procentandel sekvenserade läsningar som endast matchar en position i referensgenomet.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Duplikat [%]</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Sekvenseringsläsningar som är duplikat (kopior) och därmed ej unika sekvenser. Hög mängd duplikat kan tyda på dålig komplexitet av sekvenserat bibliotek eller djup sekvensering. Observera att dupliceringar är vanligt förekommande vid WTS.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Adapter [%]</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Andel läsningar som innehåller adaptersekvenser.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">5&#39;-3&#39; bias</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Bias är förhållandet mellan antalet läsningar vid 3&#39;-änden och antalet läsningar vid 5&#39;-änden av fragmentet. Ett förhållande på 1 indikerar brist på bias, medan värden större eller mindre än 1 indikerar 3&#39;- eller 5&#39;-bias, respektive.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Sekvenser som klarar filter [%]</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Procentandel läsningar som passerar kvalitetskontrollfilter.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Genomsnittlig läslängd efter filtrering [bp]</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Genomsnittlig längd på läsningar som passerar kvalitetskontrollfilter.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Q20-baser [%]</th>\n        \n          <td>10.0</td>\n        \n        <td class="text-start">Andel baser med en Phred-poäng på minst 20.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Q30-baser [%]</th>\n        \n          <td>10.0</td>\n        \n        <td class="text-start">Andel baser med en Phred-poäng på minst 30.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">GC innehåll [%]</th>\n        \n          <td>10.0</td>\n        \n        <td class="text-start">Andel guanin- och cytosinbaser i ett prov, beräknat på trimmade läsningar.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">mRNA baser [%]</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Andel baser i ett prov som härstammar från budbärar-RNA.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Ribosomala baser [%]</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Andel baser i ett prov som härstammar från ribosomalt RNA.</td>\n      </tr>\n      \n    </tbody>\n  </table>\n\n\n"""
EXPECTED_TOMTE_QC_TABLE_WTS = """<table class="table w-auto text-center align-middle" aria-describedby="qc-metrics-table">\n    <thead class="table-secondary">\n      <tr>\n        <th scope="col">Kvalitetsmått</th>\n        \n          <th scope="col">sample_name (sample_id)</th>\n        \n        <th scope="col">Förklaringar</th>\n      </tr>\n    </thead>\n    <tbody>\n      \n      <tr>\n        <th scope="row">RNA Integrity Number (RIN)</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Mått på skala från 1 till 10 för kvalitet och integritet hos RNA-prover. N/A som värde är en varning om att inget tillförlitligt RIN är tillgängligt för det specifika provet.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">DV200</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Andelen RNA-fragment längre än 200 nukleotider.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Ingående mängd [ng]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Mängd RNA som används för sekvensering.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Läspar [M]</th>\n        \n          <td>0.0</td>\n        \n        <td class="text-start">Antal sekvenseringsläsningar i miljoner läspar.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Unikt mappade sekvenser [%]</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Procentandel sekvenserade läsningar som endast matchar en position i referensgenomet.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Duplikat [%]</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Sekvenseringsläsningar som är duplikat (kopior) och därmed ej unika sekvenser. Hög mängd duplikat kan tyda på dålig komplexitet av sekvenserat bibliotek eller djup sekvensering. Observera att dupliceringar är vanligt förekommande vid WTS.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Adapter [%]</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Andel läsningar som innehåller adaptersekvenser.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">5&#39;-3&#39; bias</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Bias är förhållandet mellan antalet läsningar vid 3&#39;-änden och antalet läsningar vid 5&#39;-änden av fragmentet. Ett förhållande på 1 indikerar brist på bias, medan värden större eller mindre än 1 indikerar 3&#39;- eller 5&#39;-bias, respektive.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Sekvenser som klarar filter [%]</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Procentandel läsningar som passerar kvalitetskontrollfilter.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Genomsnittlig läslängd efter filtrering [bp]</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Genomsnittlig längd på läsningar som passerar kvalitetskontrollfilter.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Q20-baser [%]</th>\n        \n          <td>10.0</td>\n        \n        <td class="text-start">Andel baser med en Phred-poäng på minst 20.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Q30-baser [%]</th>\n        \n          <td>10.0</td>\n        \n        <td class="text-start">Andel baser med en Phred-poäng på minst 30.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">GC innehåll [%]</th>\n        \n          <td>10.0</td>\n        \n        <td class="text-start">Andel guanin- och cytosinbaser i ett prov, beräknat på trimmade läsningar.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">mRNA baser [%]</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Andel baser i ett prov som härstammar från budbärar-RNA.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Ribosomala baser [%]</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Andel baser i ett prov som härstammar från ribosomalt RNA.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Introniska baser [%]</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Procent baser som ligger i intron. Om målet i den laboratoriska processen är att selektera transkript vars intron är borttagna är, så är ett högt värde avvikande.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Intergeniska baser [%]</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Procent baser som anses ligga i regioner mellan gener. Om målet i den laboratoriska processen är att selektera ut kodande regioner i genomet, så är ett högt värde avvikande.</td>\n      </tr>\n      \n    </tbody>\n  </table>\n\n\n"""
EXPECTED_NALLO_QC = """<h4 class="mt-4 mb-3">Kvalitetsmått</h4>\n  <table class="table w-auto text-center align-middle" aria-describedby="qc-metrics-table">\n    <thead class="table-secondary">\n      <tr>\n        <th scope="col">Kvalitetsmått</th>\n        \n          <th scope="col">sample_name (sample_id)</th>\n        \n        <th scope="col">Förklaringar</th>\n      </tr>\n    </thead>\n    <tbody>\n      \n      <tr>\n        <th scope="row">Kön</th>\n        \n          <td>Kvinna</td>\n        \n        <td class="text-start">Kön beräknat genom bioinformatisk analys.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Mappade HiFi baser [Gb]</th>\n        \n          <td>0.0</td>\n        \n        <td class="text-start">Antal miljarder baser som mappar mot referens genomet.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Medelsekvenslängd</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Medelvärdet av längden av sekvenseringsläsningar.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Mediantäckning [baser]</th>\n        \n          <td>0.1</td>\n        \n        <td class="text-start">Median av täckningen över alla baser inkluderade i analysen.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Medelsekvensdjup</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Medelvärdet av täckningsgraden i baser över genpanelen/genpanelerna angivna under dataanalys.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Täckningsgrad 10x [%]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Andel baser som är sekvenserade med ett djup över en specificerad gräns (10x) över genpanelen/genpanelerna angivna under dataanalys.</td>"""


@pytest.fixture
def balsamic_tga_analysis():
    return BalsamicAnalysis(
        balsamic_config=create_autospec(
            BalsamicConfigJSON,
            analysis=create_autospec(BalsamicConfigAnalysis, sequencing_type="targeted"),
            panel=create_autospec(
                BalsamicConfigPanel,
                capture_kit="my_fav_capture_kit",
                capture_kit_version="best_version",
            ),
        ),
        sample_metrics={
            "sample_id": BalsamicTargetedQCMetrics(
                percent_duplication=0.01,
                compare_predicted_to_given_sex="male",
                mean_insert_size=1.0,
                fold_80_base_penalty=1.0,
                gc_dropout=1.0,
                median_target_coverage=1.0,
                pct_target_bases_250x=0.01,
                pct_target_bases_500x=0.01,
            )
        },
    )


@pytest.fixture
def balsamic_wgs_analysis():
    return BalsamicAnalysis(
        balsamic_config=create_autospec(
            BalsamicConfigJSON,
            analysis=create_autospec(BalsamicConfigAnalysis, sequencing_type="wgs"),
            panel=None,
        ),
        sample_metrics={
            "sample_id": BalsamicWGSQCMetrics(
                percent_duplication=0.01,
                compare_predicted_to_given_sex="female",
                mean_insert_size=1.0,
                fold_80_base_penalty=1.0,
                median_target_coverage=1.0,
                pct_15x=1.0,
                pct_60x=1.0,
                pct_pf_reads_improper_pairs=1.0,
            )
        },
    )


@pytest.fixture
def balsamic_wgs_analysis_without_predicted_sex() -> BalsamicAnalysis:
    return BalsamicAnalysis(
        balsamic_config=create_autospec(
            BalsamicConfigJSON,
            analysis=create_autospec(BalsamicConfigAnalysis, sequencing_type="wgs"),
            panel=None,
        ),
        sample_metrics={
            "sample_id": BalsamicWGSQCMetrics(
                percent_duplication=0.01,
                compare_predicted_to_given_sex=None,
                mean_insert_size=1.0,
                fold_80_base_penalty=1.0,
                median_target_coverage=1.0,
                pct_15x=1.0,
                pct_60x=1.0,
                pct_pf_reads_improper_pairs=1.0,
            )
        },
    )


@pytest.fixture
def rnafusion_analysis() -> NextflowAnalysis:
    return NextflowAnalysis(
        sample_metrics={
            "sample_id": RnafusionQCMetrics(
                after_filtering_gc_content=0.1,
                after_filtering_q20_rate=0.1,
                after_filtering_q30_rate=0.1,
                after_filtering_read1_mean_length=0.1,
                before_filtering_total_reads=0.1,
                median_5prime_to_3prime_bias=0.1,
                pct_adapter=0.1,
                pct_mrna_bases=0.1,
                pct_ribosomal_bases=0.1,
                pct_surviving=0.1,
                pct_duplication=0.1,
                read_pairs_examined=0.1,
                uniquely_mapped_percent=0.1,
            )
        },
    )


@pytest.fixture
def tomte_analysis() -> NextflowAnalysis:
    return NextflowAnalysis(
        sample_metrics={
            "sample_id": TomteQCMetrics(
                after_filtering_gc_content=0.1,
                after_filtering_q20_rate=0.1,
                after_filtering_q30_rate=0.1,
                after_filtering_read1_mean_length=0.1,
                before_filtering_total_reads=0.1,
                median_5prime_to_3prime_bias=0.1,
                pct_adapter=0.1,
                pct_duplication=0.1,
                pct_intergenic_bases=0.1,
                pct_intronic_bases=0.1,
                pct_mrna_bases=0.1,
                pct_ribosomal_bases=0.1,
                pct_surviving=0.1,
                uniquely_mapped_percent=0.1,
            )
        },
    )


@pytest.fixture
def nallo_analysis() -> NextflowAnalysis:
    return NextflowAnalysis(
        sample_metrics={
            "sample_id": NalloQCMetrics(
                avg_sequence_length=0.1,
                coverage_bases=0.1,
                median_coverage=0.1,
                percent_duplicates=0.1,
                predicted_sex_sex_check=SexOptions.FEMALE,
            )
        }
    )
