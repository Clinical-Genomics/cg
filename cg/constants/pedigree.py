from enum import Enum


class Pedigree(str, Enum):
    FATHER = "father"
    MOTHER = "mother"
    CHILD = "child"
    SEX = "sex"
    PHENOTYPE = "phenotype"
