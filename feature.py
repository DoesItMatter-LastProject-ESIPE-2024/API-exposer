"""TODO"""


from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Set, Callable, TypeVar


type ClusterName = str
type FeatureId = int
T = TypeVar('T')


def _iterate_bits(number: int, bit_length: int, zero: T, apply: Callable[[T, int, bool], T]) -> T:
    result = zero
    for i in range(bit_length):
        bit = (number >> i) & 1
        result = apply(result, i, bool(bit))
    return result


@dataclass
class Feature:
    """Contains all specific implementation contained by a cluster feature"""
    writable_attributes: Set[str] = field(default_factory=set)
    readable_attributes: Set[str] = field(default_factory=set)
    implemented_commands: Set[str] = field(default_factory=set)
    name: Optional[str] = None

    def _merge_name(self, other_name: Optional[str]) -> Optional[str]:
        match (self.name, other_name):
            case (None, None): return None
            case (_, None): return self.name
            case (None, _): return other_name
            case (_, _): return f'{self.name}|{other_name}'

    def merge(self, other: Feature) -> Feature:
        return Feature(
            self.writable_attributes.union(other.writable_attributes),
            self.readable_attributes.union(other.readable_attributes),
            self.implemented_commands.union(other.implemented_commands),
            self._merge_name(other.name)
        )
        
    def __json__(self) -> any:
        return {
            "writables_attributes":list(self.writable_attributes),
            "readables_attributes":list(self.readable_attributes),
            "implemented_commands":list(self.implemented_commands)
        }


@dataclass(frozen=True)
class Features:
    """Represents all combinaisons of features a cluster can implements"""
    features: List[Feature] = field(default_factory=list)

    def _get_features_by_id(self, feature_id: int) -> Feature:
        return self.features[feature_id]

    def get_features_by_map(self, feature_map: int) -> Feature:
        return _iterate_bits(
            feature_map,
            len(self.features),
            Feature(),
            lambda f, pos, val: f if not val else f.merge(
                self._get_features_by_id(pos))
        )
        

    def __json__(self) -> any:
        return {f.name : f.__json__() for f in self.features}