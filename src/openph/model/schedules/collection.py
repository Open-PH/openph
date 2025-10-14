# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHPP Schedule Collection Manager."""

from dataclasses import dataclass, field
from typing import Any, Generator, Generic, TypeVar

from openph.model.schedules.occupancy import PhEnScheduleOccupancy
from openph.model.schedules.ventilation import PhEnScheduleVentilation


class ScheduleNotFoundError(Exception):
    def __init__(self, _schedule_keys, _search_id):
        self.msg = f"Schedule {_search_id} not Found. Valid schedule keys include only: {_schedule_keys}"
        super().__init__(self.msg)


T = TypeVar("T", PhEnScheduleVentilation, PhEnScheduleOccupancy)


@dataclass
class PhEnScheduleCollection(Generic[T]):
    _schedules: dict[str, T] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        self._schedules = {}

    def __getitem__(self, _key: str) -> T:
        try:
            return self._schedules[_key]
        except KeyError:
            raise ScheduleNotFoundError(list(self._schedules.keys()), _key)

    def __setitem__(self, key: str, value: T) -> None:
        self._schedules[key] = value

    def add_new_schedule(self, _schedule: T) -> None:
        """Add a new Schedule to the Collection."""
        if _schedule is None:
            return

        self._schedules[_schedule.identifier] = _schedule

    def schedule_is_in_collection(self, _schedule: T) -> bool:
        if _schedule.identifier in self._schedules.keys():
            return True
        return False

    def get_schedule_by_key(self, _key: str):
        try:
            return self._schedules[_key]
        except KeyError:
            raise ScheduleNotFoundError(list(self._schedules.keys()), _key)

    def get_schedule_by_id_num(self, _id_num: int) -> T:
        """Return a Schedule from the collection found by an id-num"""
        for schedule in self._schedules.values():
            if schedule.id_num == _id_num:
                return schedule
        msg = f"Error: Cannot locate the Schedule with id-number: {_id_num}"
        raise Exception(msg)

    def __len__(self) -> int:
        return len(self._schedules.keys())

    def __iter__(self) -> Generator[T, Any, None]:
        for v in self._schedules.values():
            yield v

    def __bool__(self) -> bool:
        return bool(self._schedules)

    def items(self):
        return self._schedules.items()

    def keys(self):
        return self._schedules.keys()

    def values(self):
        return self._schedules.values()
