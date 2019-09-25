import os
import re

from datetime import datetime
from genologics.lims import Lims
# Should probably call these items directly since we're now up to 3 config files
from genologics.entities import Project, Sample

class LIMS_Fetcher():

  def __init__(self, config, log):
    self.data = {}
    self.lims = Lims(config['genologics']['baseuri'], config['genologics']['username'], config['genologics']['password'])
    self.logger = log
    self.config = config


    #Figuring out the organism
    organism = "Unset"
    reference = "None"
    if 'Reference Genome Microbial' in sample.udf:
      reference = sample.udf['Reference Genome Microbial'].strip()

    if 'Strain' in sample.udf and organism == "Unset":
      #Predefined genus usage. All hail buggy excel files
      if 'gonorrhoeae' in sample.udf['Strain']:
        organism = "Neisseria spp."
      elif 'Cutibacterium acnes' in sample.udf['Strain']:
        organism = "Propionibacterium acnes"
      #Backwards compat, MUST hit first
      elif sample.udf['Strain'] == 'VRE':
        if reference == 'NC_017960.1':
          organism = 'Enterococcus faecium'
        elif reference == 'NC_004668.1':
          organism = 'Enterococcus faecalis'
        elif 'Comment' in sample.udf and not re.match('\w{4}\d{2,3}', sample.udf['Comment']):
          organism = sample.udf['Comment']
      elif sample.udf['Strain'] != 'Other' and sample.udf['Strain'] != 'other':
        organism = sample.udf['Strain']
      elif (sample.udf['Strain'] == 'Other' or sample.udf['Strain'] == 'other') and 'Other species' in sample.udf:
        #Other species predefined genus usage
        if 'gonorrhoeae' in sample.udf['Other species']:
          organism = "Neisseria spp."
        elif 'Cutibacterium acnes' in sample.udf['Other species']:
          organism = "Propionibacterium acnes"
        else:
          organism = sample.udf['Other species']
    if reference != 'None' and organism == "Unset":
      if reference == 'NC_002163':
        organism = "Campylobacter jejuni"
      elif reference == 'NZ_CP007557.1':
        organism = 'Klebsiella oxytoca'
      elif reference == 'NC_000913.3':
        organism = 'Citrobacter freundii'
      elif reference == 'NC_002516.2':
        organism = 'Pseudomonas aeruginosa'
    elif 'Comment' in sample.udf and not re.match('\w{4}\d{2,3}', sample.udf['Comment']) and organism == "Unset":
      organism = sample.udf['Comment'].strip()
    # Consistent safe-guard
    elif organism == "Unset":
      organism = "Other"
      self.logger.warn("Unable to resolve ambigious organism found in sample {}."\
      .format(cg_sampleid))


  def get_organism_refname(self, sample_name):
    """Finds which reference contains the same words as the LIMS reference
       and returns it in a format for database calls."""
    self.load_lims_sample_info(sample_name)
    lims_organ = self.data['organism'].lower()
    orgs = os.listdir(self.config["folders"]["references"])
    organism = re.split('\W+', lims_organ)
    try:
      refs = 0
      for target in orgs:
        hit = 0
        for piece in organism:
          if len(piece) == 1:
            if target.startswith(piece):
              hit += 1
          else:
            if piece in target:
              hit +=1
            #For when people misspell the strain in the orderform
            elif piece == "pneumonsiae" and "pneumoniae" in target:
              hit +=1
            else:
              break
        if hit == len(organism):
          return target
    except Exception as e:
      self.logger.warn("Unable to find existing reference for {}, strain {} has no reference match\nSource: {}"\
      .format(sample_name, lims_organ, e))

  def get_date(self, sample_id, type=""):
    """ Returns the most recent sequencing date of a sample """
    date_list = list()
    if type == "arrival":
      steps = ["CG002 - Reception Control", "CG002 - Reception Control (Dev)", "Reception Control TWIST v1", "Reception Control no placement v1"]
    elif type == "sequencing":
      steps = ["CG002 - Illumina Sequencing (Illumina SBS)", "CG002 Illumina SBS (HiSeq X)", "AUTOMATED - NovaSeq Run"]
    elif type == "libprep":
      steps = ["CG002 - Aggregate QC (Library Validation)", "CG002 - Aggregate QC (Library Validation) (Dev)"]
    else:
      raise Exception("Attempted to get date for {} but no step defined".format(sample_id))
    for step in steps:
      try:
        arts = self.lims.get_artifacts(samplelimsid = sample_id, process_type = step)
        if type == "arrival":
          date_list = date_list + [a.parent_process.udf['date arrived at clinical genomics'] for a in arts]
        elif type == "sequencing":
          if step == 'AUTOMATED - NovaSeq Run':
            date_list = date_list + [a.parent_process.date_run for a in arts]
          else:
            date_list = date_list + [a.parent_process.udf['Finish Date'] for a in arts]
        elif type == "libprep":
          date_list = date_list + [a.parent_process.date_run for a in arts]
      except Exception as e:
        pass
    date_list = [x for x in date_list if x != None]
    if date_list:
      try:
        dp = max(date_list).split('-')
        return datetime(int(dp[0]), int(dp[1]), int(dp[2]))
      except Exception as e:
        return max(date_list)
    else:
      return datetime.min

  def get_method(self, sample_id, type=""):
    """Retrives method document name and version for a sample"""
    steps = dict()

    key_values = dict()
    if type == "libprep":
      steps['CG002 - Microbial Library Prep (Nextera)'] = ("Method","Method Version")
    elif type == "sequencing":
      steps['CG002 - Cluster Generation (Illumina SBS)'] = ('Method Document 1','Document 1 Version')
      steps['CG002 - Cluster Generation (HiSeq X)'] = ('Method','Version')
    else:
      raise Exception("Attempted to get info for {} but no step defined".format(sample_id))
    for step in steps.keys():
      try:
        arts = self.lims.get_artifacts(samplelimsid = sample_id, process_type = step)
        processes = [(a.parent_process.udf[steps[step][0]], a.parent_process.udf[steps[step][1]]) for a in arts]
        processes = list(set(processes))
        if processes:
          process = sorted(processes)[-1]
          out = "{}:{}".format(process[0], process[1])
      except Exception as e:
        pass
    if not 'out' in locals():
      out = "Not in LIMS"
    return out
