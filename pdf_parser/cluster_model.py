from typing import List
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AttributeExtractionModel:
    id: int
    name: str
    conformance: str


@dataclass(frozen=True)
class FeatureExtractionModel:
    id: int
    code: str
    name: str


@dataclass(frozen=True)
class InfoExtractionModel:
    id: int
    name: str


@dataclass
class ClusterExtractionModel:
    info: List[InfoExtractionModel] = field(default_factory=list)
    features: List[FeatureExtractionModel] = field(default_factory=list)
    attributes: List[AttributeExtractionModel] = field(default_factory=list)
    commands: List[AttributeExtractionModel] = field(default_factory=list)
