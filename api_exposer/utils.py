"""TODO"""

from asyncio import TaskGroup
from typing import Awaitable, Iterable, List, Optional


async def await_all[T](items: Iterable[Awaitable[T]]) -> List[T]:
    """Returns a list ensuring each elements in the iterable is waited"""
    async with TaskGroup() as tg:
        return [tg.create_task(item) for item in items]


def flat_map[T](items2d: Iterable[Iterable[T]]) -> Iterable[T]:
    """Flattens an iterable"""
    return (item for items in items2d for item in items)


def filter_not_none[T](items: Iterable[Optional[T]]) -> Iterable[T]:
    """Returns an Iterable skipping when elements is None"""
    return (item for item in items if item is not None)
