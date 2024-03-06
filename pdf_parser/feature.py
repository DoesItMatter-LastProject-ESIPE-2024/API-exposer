"""TODO"""


from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Set, Callable, TypeVar, NamedTuple


type ClusterName = str
type FeatureId = int
T = TypeVar('T')


@dataclass(frozen=True)
class NamedId:
    """TODO"""
    id: int
    name: str

    @classmethod
    def of(cls, value: any) -> NamedId:
        """Returns a view of the value as a NamedId"""
        return cls(value.id, value.name)

    def __json__(self):
        return {'id': self.id, 'name': self.name}


def _iterate_bits(number: int, bit_length: int, zero: T, apply: Callable[[T, int, bool], T]) -> T:
    result = zero
    for i in range(bit_length):
        bit = (number >> i) & 1
        result = apply(result, i, bool(bit))
    return result


@dataclass(frozen=True)
class NamedFeature(NamedId):
    """Contains all specific implementation contained by a cluster feature"""
    value: FeatureComponents

    def __json__(self) -> any:
        v = self.value.__json__()
        v['name'] = self.name
        v['id'] = self.id
        return v


@dataclass(frozen=True)
class FeatureComponents:
    """Groups together the components of one or multiple features"""
    not_writable_attributes: Set[NamedId] = field(default_factory=set)
    not_readable_attributes: Set[NamedId] = field(default_factory=set)
    not_implemented_commands: Set[NamedId] = field(default_factory=set)

    def union(self, other: FeatureComponents) -> FeatureComponents:
        """Returns a union of all sets"""
        return FeatureComponents(
            self.not_writable_attributes.union(other.not_writable_attributes),
            self.not_readable_attributes.union(other.not_readable_attributes),
            self.not_implemented_commands.union(other.not_implemented_commands)
        )

    def __json__(self) -> any:
        return {
            'writable_attributes': list(v.__json__() for v in self.not_writable_attributes),
            'readable_attributes': list(v.__json__() for v in self.not_readable_attributes),
            'implemented_commands': list(v.__json__() for v in self.not_implemented_commands)
        }


@dataclass(frozen=True)
class Features:
    """Represents all combinaisons of features a cluster can implements"""
    features: List[NamedFeature] = field(default_factory=list)

    def _get_features_by_id(self, feature_id: int) -> NamedFeature:
        return self.features[feature_id]

    def _union(self, f: FeatureComponents, pos: int, val: bool):
        return f if not val else f.union(self._get_features_by_id(pos))

    def get_features_by_map(self, feature_map: int) -> FeatureComponents:
        """Returns the feature components of a specific feature map returned """
        return _iterate_bits(
            feature_map,
            len(self.features),
            FeatureComponents(),
            self._union
        )

    def __json__(self) -> any:
        return [f.__json__() for f in self.features]
