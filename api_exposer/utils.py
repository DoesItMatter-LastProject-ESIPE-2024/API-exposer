"""TODO"""

from typing import Iterable, List, Optional


def flat_map[T](items2d: Iterable[Iterable[T]]) -> Iterable[T]:
    """Flattens an iterable"""
    return (item for items in items2d for item in items)


def filter_not_none[T](items: Iterable[Optional[T]]) -> Iterable[T]:
    """Returns an Iterable skipping when elements is None"""
    return (item for item in items if item is not None)
