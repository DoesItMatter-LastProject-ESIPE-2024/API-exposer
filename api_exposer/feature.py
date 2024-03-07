"""TODO"""


from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Callable, TypeVar


type ClusterName = str
type FeatureId = int
T = TypeVar('T')


@dataclass(frozen=True)
class NamedId:
    """TODO"""
    id: int
    name: str

    @staticmethod
    def of(value: any) -> NamedId:
        """Returns a view of the value as a NamedId"""
        return NamedId(value.id, value.name)

    def __to_json__(self):
        return {'id': self.id, 'name': self.name}

    @staticmethod
    def __from_json__(json_dict: Dict[str, Any]) -> NamedId:
        return NamedId(
            json_dict['id'],
            json_dict['name']
        )


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

    def __to_json__(self) -> any:
        v = self.value.__to_json__()
        v['name'] = self.name
        v['id'] = self.id
        return v

    @staticmethod
    def __from_json__(json_dict: Dict[str, Any]) -> NamedFeature:
        return NamedFeature(
            json_dict['id'],
            json_dict['name'],
            FeatureComponents.__from_json__(json_dict)
        )


@dataclass(frozen=True)
class FeatureComponents:
    """Groups together the components of one or multiple features"""
    not_writable_attributes: Set[NamedId] = field(default_factory=set)
    not_readable_attributes: Set[NamedId] = field(default_factory=set)
    not_implemented_commands: Set[NamedId] = field(default_factory=set)

    def is_readable(self, attribute_id: int) -> bool:
        """Returns True if the attribute is writable
        for this specific feature component False otherwise"""
        return not any(
            attribute_id == v.id
            for v in self.not_readable_attributes
        )

    def is_writable(self, attribute_id: int) -> bool:
        """Returns True if the attribute is readable
        for this specific feature component False otherwise"""
        return not any(
            attribute_id == v.id
            for v in self.not_writable_attributes
        )

    def is_implemented(self, command_id: int) -> bool:
        """Returns True if the command is implemented
        for this specific feature component False otherwise"""
        return not any(
            command_id == v.id
            for v in self.not_implemented_commands
        )

    def intersection(self, other: FeatureComponents) -> FeatureComponents:
        """Returns an intersection of all sets"""
        return FeatureComponents(
            self.not_writable_attributes.intersection(
                other.not_writable_attributes),
            self.not_readable_attributes.intersection(
                other.not_readable_attributes),
            self.not_implemented_commands.intersection(
                other.not_implemented_commands)
        )

    def union(self, other: FeatureComponents) -> FeatureComponents:
        """Returns an union of all sets"""
        return FeatureComponents(
            self.not_writable_attributes.union(
                other.not_writable_attributes),
            self.not_readable_attributes.union(
                other.not_readable_attributes),
            self.not_implemented_commands.union(
                other.not_implemented_commands)
        )

    def __to_json__(self) -> any:
        return {
            'not_writable_attributes': list(v.__to_json__() for v in self.not_writable_attributes),
            'not_readable_attributes': list(v.__to_json__() for v in self.not_readable_attributes),
            'not_implemented_commands': list(v.__to_json__() for v in self.not_implemented_commands)
        }

    @staticmethod
    def __from_json__(json_dict: Dict[str, Any]) -> FeatureComponents:
        return FeatureComponents(
            set(
                NamedId.__from_json__(v)
                for v in json_dict['not_writable_attributes']
            ),
            set(
                NamedId.__from_json__(v)
                for v in json_dict['not_readable_attributes']
            ),
            set(
                NamedId.__from_json__(v)
                for v in json_dict['not_implemented_commands']
            )
        )


@dataclass(frozen=True)
class Features:
    """Represents all combinaisons of features a cluster can implements"""
    features: List[NamedFeature] = field(default_factory=list)

    def _intersection(self, f: FeatureComponents, pos: int, val: bool):
        if not val:
            return f
        return f.intersection(self.features[pos].value)

    def _initial(self) -> FeatureComponents:
        result = FeatureComponents()
        for f in self.features:
            result = result.union(f.value)
        return result

    def get_features_by_map(self, feature_map: int) -> FeatureComponents:
        """Returns the feature components of a specific feature map returned """
        return _iterate_bits(
            feature_map,
            len(self.features),
            self._initial(),
            self._intersection
        )

    def __to_json__(self) -> any:
        return [f.__to_json__() for f in self.features]

    @staticmethod
    def __from_json__(json_list: List[Any]) -> Features:
        return Features([
            NamedFeature.__from_json__(v)
            for v in json_list
        ])
