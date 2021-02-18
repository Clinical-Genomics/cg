from enum import Enum
from typing import List, Optional

from cg.models.orders.sample_base import OrderSample
from pydantic import BaseModel


class SexEnum(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class PriorityEnum(str, Enum):
    research = "research"
    standard = "standard"
    priority = "priority"
    express = "express"
    clinical_trials = "clinical trials"


class ContainerEnum(str, Enum):
    agilent_sureselect_cre = "Agilent Sureselect CRE"
    agilent_sureselect_v5 = "Agilent Sureselect V5"
    sureselect_focused_exome = "SureSelect Focused Exome"
    twist_target_hg19_bed = "Twist_Target_hg19.bed"
    other = "other"


class StatusEnum(str, Enum):
    affected = "affected"
    unaffected = "unaffected"
    unknown = "unknown"


NAME_PATTERN = r"^[A-Za-z0-9-]*$"


# Class for holding information about cases in order
class OrderCase(BaseModel):
    name: str
    samples: List[OrderSample]
    require_qcok: bool = False
    priority: str
    panels: Optional[List[str]]


class OrderPool(BaseModel):
    name: str
    data_analysis: str
    data_delivery: Optional[str]
    application: str
    samples: List[OrderSample]


# This is for validating in data
class Orderform(BaseModel):
    comment: Optional[str]
    delivery_type: str
    project_type: str
    customer: str
    name: str
    data_analysis: Optional[str]
    data_delivery: Optional[str]
    ticket: Optional[int]
    samples: List[OrderSample]
    cases: Optional[List[OrderCase]]
