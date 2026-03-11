"""Collection utilities for working with multiple procedures."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from typing import Any

from openstage.models.procedure import Procedure


class ProcedureList:
    """A list-like container for procedures with filtering and analytics.

    Wraps a plain list of Procedure instances and provides methods for
    cross-procedure analysis: filtering by status/type/date, computing
    open procedure counts over time, and grouping.
    """

    __slots__ = ("_procedures",)

    def __init__(self, procedures: Iterable[Procedure] = ()) -> None:
        self._procedures: list[Procedure] = list(procedures)

    # -- List-like interface --------------------------------------------------

    def __len__(self) -> int:
        return len(self._procedures)

    def __iter__(self) -> Iterator[Procedure]:
        return iter(self._procedures)

    def __getitem__(self, index: int | slice) -> Procedure | ProcedureList:
        if isinstance(index, slice):
            return ProcedureList(self._procedures[index])
        return self._procedures[index]

    def __contains__(self, item: object) -> bool:
        return item in self._procedures

    def __bool__(self) -> bool:
        return bool(self._procedures)

    def __repr__(self) -> str:
        return f"ProcedureList({len(self._procedures)} procedures)"

    def append(self, procedure: Procedure) -> None:
        """Append a procedure to the list."""
        self._procedures.append(procedure)

    def extend(self, procedures: Iterable[Procedure]) -> None:
        """Extend the list with procedures from an iterable."""
        self._procedures.extend(procedures)

    # -- Filtering (return new ProcedureList) ---------------------------------

    def filter(self, predicate: Callable[[Procedure], bool]) -> ProcedureList:
        """Return a new ProcedureList with only procedures matching predicate."""
        return ProcedureList(p for p in self._procedures if predicate(p))

    def by_status(self, status: str) -> ProcedureList:
        """Filter procedures by status."""
        return self.filter(lambda p: p.status == status)

    def by_type(self, procedure_type: str) -> ProcedureList:
        """Filter procedures by procedure_type (extra field)."""
        return self.filter(
            lambda p: getattr(p, "procedure_type", None) == procedure_type
        )

    def started_between(self, start: str, end: str) -> ProcedureList:
        """Filter procedures whose start_date falls within [start, end]."""
        return self.filter(
            lambda p: p.start_date is not None and start <= p.start_date <= end
        )

    # -- Cross-procedure analytics --------------------------------------------

    def open_at(self, date: str) -> ProcedureList:
        """Return procedures that were open (started but not yet concluded) at date.

        A procedure is open at a given date if:
        - It has a start_date and start_date <= date
        - It has no end_date, or end_date > date
        """

        def _is_open(p: Procedure) -> bool:
            if p.start_date is None or p.start_date > date:
                return False
            if p.end_date is not None and p.end_date <= date:
                return False
            return True

        return self.filter(_is_open)

    def backlog_at(self, date: str) -> int:
        """Count of procedures open at the given date."""
        return len(self.open_at(date))

    def backlog_series(self, dates: Iterable[str]) -> list[tuple[str, int]]:
        """Compute backlog counts for a sequence of dates."""
        return [(d, self.backlog_at(d)) for d in dates]

    @property
    def date_range(self) -> tuple[str | None, str | None]:
        """Earliest and latest start_date across all procedures."""
        dates = [p.start_date for p in self._procedures if p.start_date]
        if not dates:
            return (None, None)
        return (min(dates), max(dates))

    def group_by(self, key: Callable[[Procedure], Any]) -> dict[Any, ProcedureList]:
        """Group procedures by a key function.

        Returns a dict mapping key values to ProcedureLists.
        """
        groups: dict[Any, list[Procedure]] = {}
        for p in self._procedures:
            k = key(p)
            groups.setdefault(k, []).append(p)
        return {k: ProcedureList(v) for k, v in groups.items()}

    # -- Serialization --------------------------------------------------------

    def to_dicts(self) -> list[dict]:
        """Serialize all procedures to dicts via model_dump()."""
        return [p.model_dump() for p in self._procedures]


# -- Standalone function wrappers ---------------------------------------------


def open_at(procedures: Iterable[Procedure], date: str) -> ProcedureList:
    """Return procedures that were open at the given date."""
    return ProcedureList(procedures).open_at(date)


def backlog_at(procedures: Iterable[Procedure], date: str) -> int:
    """Count of procedures open at the given date."""
    return ProcedureList(procedures).backlog_at(date)


def filter_procedures(
    procedures: Iterable[Procedure],
    predicate: Callable[[Procedure], bool],
) -> ProcedureList:
    """Filter procedures by a predicate function."""
    return ProcedureList(procedures).filter(predicate)
