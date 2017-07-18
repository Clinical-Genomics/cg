# -*- coding: utf-8 -*-
from .analysis import AnalysisImporter
from .application import ApplicationImporter
from .customer import CustomerImporter
from .panel import PanelImporter
from .sample import SampleImporter
from .user import UserImporter
from .version import VersionImporter

# USER                          => DONE (import scout later)
# CUSTOMER                      => DONE (handle AMSystems manually)
# FAMILY                        => DONE (curate duplicates later)
# SAMPLE                        => DONE (do, handle genotype results later)
# FAMILY-SAMPLE                 => DONE (do)
# FLOWCELL + FLOWCELL-SAMPLE    => cgstats (kenny)
# ANALYSIS                      => housekeeper
# APPLICATION                   => DONE (handle clinicalgenomics.se manually)
# APPLICATION-VERSION           => DONE (do)
# PANEL                         => DONE
