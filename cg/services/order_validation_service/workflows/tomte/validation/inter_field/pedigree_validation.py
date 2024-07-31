from pydantic import BaseModel
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample


class Node:
    def __init__(self, sample: TomteSample, mother: TomteSample | None, father: TomteSample | None):
        self.sample = sample
        self.father = father
        self.mother = mother
        self.visited = False


class Pedigree:
    def __init__(self, case: TomteCase):
        self.pedigree = {}
        self.case = case

        for sample in case.samples:
            self._add_node(sample)

    def _add_node(self, sample: TomteSample) -> None:
        mother = self.case.get_sample(sample.mother)
        father = self.case.get_sample(sample.father)
        node = Node(sample=sample, mother=mother, father=father)
        self.pedigree[sample.name] = node

    def validate_cycles():
        pass


def validate_pedigree(case: TomteCase):
    pedigree = Pedigree(case)
    return pedigree.validate_cycles()
