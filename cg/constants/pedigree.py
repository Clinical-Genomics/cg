from enum import StrEnum


class Pedigree(StrEnum):
    FATHER = "father"
    MOTHER = "mother"
    CHILD = "child"
    SEX = "sex"
    PHENOTYPE = "phenotype"
