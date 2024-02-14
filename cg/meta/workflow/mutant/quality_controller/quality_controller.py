from pathlib import Path
from cg.meta.workflow.mutant.metrics_parser import MetricsParser, QualityMetrics
from cg.store.api.core import Store
from cg.store.models import Sample

class QualityController:
    def __init__(self, status_db: Store):
        self.status_db = status_db

    def quality_control(self, case_results_file_path: Path) -> :
    
    #TODO
    #parse results
    #implement the QC checks
        #create a utils for the QC checks
    
    #Look at how the logging is done for trailblazer