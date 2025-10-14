# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-


"""Component Collections"""

from typing import Generic, TypeVar

from openph.model.constructions import PhEnConstructionAperture, PhEnConstructionOpaque

T = TypeVar("T", PhEnConstructionOpaque, PhEnConstructionAperture)


class ConstructionCollection(Generic[T]):
    """Collection of Opaque-Construction-Type Objects"""

    def __init__(self) -> None:
        self._collection: dict[str, T] = {}

    @property
    def construction_type_id_numbers(self) -> set[int]:
        return {_.id_num for _ in self._collection.values()}

    def add_new_construction(self, _construction: T, _key: str | None = None) -> None:
        """Adds a new PhEnConstructionOpaque | PhEnConstructionAperture to the Project's collection"""
        if _key:
            self._collection[_key] = _construction
        else:
            self._collection[_construction.identifier] = _construction

    def get_construction_by_identifier(self, _identifier: str) -> T:
        """Returns the Construction with the given Identifier"""
        try:
            return self._collection[_identifier]
        except KeyError:
            raise KeyError(
                f"Aperture Construction with Identifier '{_identifier}' was not found in the collection."
                f"Valid constructions in the collection include: {self._collection.keys()}"
            )

    def __len__(self) -> int:
        return len(self._collection)
