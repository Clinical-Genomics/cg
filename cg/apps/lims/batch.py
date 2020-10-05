from functools import partial
from typing import List, Dict, Any

from genologics.entities import Artifact, Project, Container, Containertype, Researcher
from lxml import etree
from lxml.objectify import ElementMaker, ObjectifiedElement

SMP_MAKER = ElementMaker(
    namespace="http://genologics.com/ri/sample",
    nsmap={"smp": "http://genologics.com/ri/sample", "udf": "http://genologics.com/ri/userdefined"},
)
SMP_DETAILS = partial(SMP_MAKER, "details")
SMP_SAMPLECREATION = partial(SMP_MAKER, "samplecreation")

CON_MAKER = ElementMaker(
    namespace="http://genologics.com/ri/container",
    nsmap={"con": "http://genologics.com/ri/container"},
)
CON_DETAILS = partial(CON_MAKER, "details")
CON_CONTAINER = partial(CON_MAKER, "container")

UDF_MAKER = ElementMaker(namespace="http://genologics.com/ri/userdefined", annotate=False)
UDF_FIELD = partial(UDF_MAKER, "field")

ART_MAKER = ElementMaker(
    namespace="http://genologics.com/ri/artifact",
    nsmap={"art": "http://genologics.com/ri/artifact"},
)
ART_DETAILS = partial(ART_MAKER, "details")
ART_ARTIFACT = partial(ART_MAKER, "artifact")

XML = ElementMaker(annotate=False)


def build_container(name: str, con_type: Containertype) -> ObjectifiedElement:
    """Build container in XML."""
    return CON_CONTAINER(XML.name(name), XML.type(uri=con_type.uri))


def build_container_batch(containers: List[ObjectifiedElement]) -> ObjectifiedElement:
    """Build batch with containers."""
    root = CON_DETAILS()
    for container in containers:
        root.append(container)
    return root


def build_sample(
    name: str, project: Project, container: Container, location: str, udfs: Dict[str, Any]
) -> ObjectifiedElement:
    """Build sample in XML."""
    xml_sample = SMP_SAMPLECREATION(
        XML.name(name),
        XML.project(uri=project.uri),
        XML.location(XML.container(uri=container.uri), XML.value(location)),
    )
    for udf_name, udf_value in udfs.items():
        xml_sample.append(UDF_FIELD(udf_value, name=udf_name))
    return xml_sample


def build_sample_batch(samples: List[ObjectifiedElement]) -> ObjectifiedElement:
    """Build batch with samples."""
    root = SMP_DETAILS()
    for sample in samples:
        root.append(sample)
    return root


def build_artifact(artifact: Artifact, reagent_label: str):
    """Build artifact in XML."""
    return ART_ARTIFACT(
        XML("reagent-label", name=reagent_label), XML.name(artifact.name), uri=artifact.uri
    )


def build_artifact_batch(artifacts: List[ObjectifiedElement]) -> ObjectifiedElement:
    """Build bathch with artifacts."""
    root = ART_DETAILS()
    for artifact in artifacts:
        root.append(artifact)
    return root
