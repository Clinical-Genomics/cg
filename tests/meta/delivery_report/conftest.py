from unittest.mock import create_autospec

import pytest

from cg.models.balsamic.analysis import BalsamicAnalysis
from cg.models.balsamic.config import BalsamicConfigJSON
from cg.models.balsamic.metrics import BalsamicTargetedQCMetrics

EXPECTED_BALSAMIC_QC_TABLE = """<h4 class="mt-4 mb-3">Kvalitetsmått</h4>\n  <table class="table w-auto text-center align-middle" aria-describedby="qc-metrics-table">\n    <thead class="table-secondary">\n      <tr>\n        <th scope="col">Kvalitetsmått</th>\n        \n          <th scope="col">sample_name (sample_id)</th>\n        \n        <th scope="col">Förklaringar</th>\n      </tr>\n    </thead>\n    <tbody>\n      \n      <tr>\n        <th scope="row">Kön</th>\n        \n          <td>Man</td>\n        \n        <td class="text-start">Kön beräknat genom bioinformatisk analys.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Läspar [M]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Antal sekvenseringsläsningar i miljoner läspar.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Duplikat [%]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Sekvenseringsläsningar som är i duplikat och därmed ej unika sekvenser. Hög mängd duplikat kan tyda på dålig komplexitet av sekvenserat bibliotek eller djup sekvensering.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Medelfragmentlängd [baspar]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Medelstorlek av provbiblioteken som laddats på sekvenseringsinstrument.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Fold 80 base penalty</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Jämnhet av täckningsgraden över alla gener i analyspanlen.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Mediantäckning [baser]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Median av täckningen över alla baser inkluderade i analysen. Det beräknas efter borttagning av duplikata läsningar.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Täckningsgrad 250x [%]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Andel baser som är sekvenserade med ett djup över en specificerad gräns (250x). Det beräknas efter borttagning av duplikata läsningar.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">Täckningsgrad 500x [%]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Andel baser som är sekvenserade med ett djup över en specificerad gräns (500x). Det beräknas efter borttagning av duplikata läsningar.</td>\n      </tr>\n      \n      <tr>\n        <th scope="row">GC Dropout [%]</th>\n        \n          <td>1.0</td>\n        \n        <td class="text-start">Ett mått på hur dåligt täckta områden, med &gt;= 50% GC innehåll, är i jämförelse med medelvärdet. Om värdet är 5%, innebär det att 5% av alla läsningar som borde ha kartlagts till områden med GC &lt;= 50%, kartlades någon annanstans.</td>\n      </tr>\n      \n    </tbody>\n  </table>\
"""


@pytest.fixture
def balsamic_tga_analysis():
    return BalsamicAnalysis(
        balsamic_config=create_autospec(BalsamicConfigJSON),
        sample_metrics={"sample_id": create_autospec(BalsamicTargetedQCMetrics)},
    )
