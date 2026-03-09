"""Tests for ProcedureList collection utilities."""

from openstage.collections import (
    ProcedureList,
    open_at,
    backlog_at,
    filter_procedures,
)
from openstage.models.eu import EUProcedure, EUEvent


def _proc(start_date, adoption_type=None, withdrawal_type=None, **kwargs):
    """Helper to build a procedure with events for testing."""
    events = [EUEvent(date=start_date, type="ADP_byCOM")]
    if adoption_type:
        events.append(
            EUEvent(date=kwargs.get("adoption_date", "2025-06-01"), type=adoption_type)
        )
    if withdrawal_type:
        events.append(
            EUEvent(
                date=kwargs.get("withdrawal_date", "2025-03-01"),
                type=withdrawal_type,
            )
        )
    return EUProcedure(
        events=events,
        procedure_type=kwargs.get("procedure_type"),
    )


class TestConstruction:

    def test_empty(self):
        pl = ProcedureList()
        assert len(pl) == 0
        assert not pl

    def test_from_list(self):
        procs = [EUProcedure(), EUProcedure()]
        pl = ProcedureList(procs)
        assert len(pl) == 2

    def test_from_generator(self):
        pl = ProcedureList(EUProcedure() for _ in range(3))
        assert len(pl) == 3


class TestListBehavior:

    def test_iter(self):
        procs = [EUProcedure(), EUProcedure()]
        pl = ProcedureList(procs)
        assert list(pl) == procs

    def test_getitem_int(self):
        p0 = EUProcedure()
        p1 = EUProcedure()
        pl = ProcedureList([p0, p1])
        assert pl[0] is p0
        assert pl[1] is p1

    def test_getitem_slice(self):
        procs = [EUProcedure() for _ in range(5)]
        pl = ProcedureList(procs)
        sliced = pl[1:3]
        assert isinstance(sliced, ProcedureList)
        assert len(sliced) == 2

    def test_contains(self):
        p = EUProcedure()
        pl = ProcedureList([p])
        assert p in pl

    def test_bool_true(self):
        assert ProcedureList([EUProcedure()])

    def test_bool_false(self):
        assert not ProcedureList()

    def test_repr(self):
        pl = ProcedureList([EUProcedure(), EUProcedure()])
        assert "2 procedures" in repr(pl)

    def test_append(self):
        pl = ProcedureList()
        p = EUProcedure()
        pl.append(p)
        assert len(pl) == 1
        assert pl[0] is p

    def test_extend(self):
        pl = ProcedureList([EUProcedure()])
        pl.extend([EUProcedure(), EUProcedure()])
        assert len(pl) == 3


class TestFiltering:

    def test_filter(self):
        procs = [
            _proc("2024-01-01", procedure_type="OLP"),
            _proc("2024-02-01", procedure_type="CNS"),
            _proc("2024-03-01", procedure_type="OLP"),
        ]
        pl = ProcedureList(procs)
        result = pl.filter(lambda p: p.procedure_type == "OLP")
        assert len(result) == 2

    def test_by_status_adopted(self):
        procs = [
            _proc("2024-01-01", adoption_type="ADP_FRM_byCONSIL"),
            _proc("2024-02-01"),  # ongoing
        ]
        pl = ProcedureList(procs)
        assert len(pl.by_status("adopted")) == 1
        assert len(pl.by_status("ongoing")) == 1

    def test_by_type(self):
        procs = [
            _proc("2024-01-01", procedure_type="OLP"),
            _proc("2024-02-01", procedure_type="CNS"),
        ]
        pl = ProcedureList(procs)
        assert len(pl.by_type("OLP")) == 1
        assert len(pl.by_type("CNS")) == 1
        assert len(pl.by_type("NLE")) == 0

    def test_started_between(self):
        procs = [
            _proc("2024-01-15"),
            _proc("2024-06-15"),
            _proc("2024-12-15"),
        ]
        pl = ProcedureList(procs)
        result = pl.started_between("2024-01-01", "2024-06-30")
        assert len(result) == 2


class TestOpenAt:

    def test_started_before(self):
        pl = ProcedureList([_proc("2024-01-01")])
        assert len(pl.open_at("2024-06-01")) == 1

    def test_started_after(self):
        pl = ProcedureList([_proc("2024-06-01")])
        assert len(pl.open_at("2024-01-01")) == 0

    def test_already_adopted(self):
        pl = ProcedureList(
            [
                _proc(
                    "2024-01-01",
                    adoption_type="ADP_FRM_byCONSIL",
                    adoption_date="2024-03-01",
                ),
            ]
        )
        # Before adoption
        assert len(pl.open_at("2024-02-15")) == 1
        # After adoption
        assert len(pl.open_at("2024-03-01")) == 0

    def test_withdrawn_with_date(self):
        pl = ProcedureList(
            [
                _proc(
                    "2024-01-01",
                    withdrawal_type="Retrait par Commission",
                    withdrawal_date="2024-04-01",
                ),
            ]
        )
        # Before withdrawal
        assert len(pl.open_at("2024-03-15")) == 1
        # After withdrawal
        assert len(pl.open_at("2024-04-01")) == 0

    def test_no_start_date_excluded(self):
        p = EUProcedure()
        pl = ProcedureList([p])
        assert len(pl.open_at("2024-06-01")) == 0


class TestAnalytics:

    def test_backlog_at(self):
        procs = [_proc("2024-01-01"), _proc("2024-03-01")]
        pl = ProcedureList(procs)
        assert pl.backlog_at("2024-02-01") == 1
        assert pl.backlog_at("2024-04-01") == 2

    def test_backlog_series(self):
        procs = [_proc("2024-01-01"), _proc("2024-03-01")]
        pl = ProcedureList(procs)
        series = pl.backlog_series(["2024-02-01", "2024-04-01"])
        assert series == [("2024-02-01", 1), ("2024-04-01", 2)]

    def test_date_range(self):
        procs = [_proc("2024-01-15"), _proc("2024-06-15"), _proc("2024-03-01")]
        pl = ProcedureList(procs)
        assert pl.date_range == ("2024-01-15", "2024-06-15")

    def test_date_range_empty(self):
        assert ProcedureList().date_range == (None, None)

    def test_group_by(self):
        procs = [
            _proc("2024-01-01", procedure_type="OLP"),
            _proc("2024-02-01", procedure_type="CNS"),
            _proc("2024-03-01", procedure_type="OLP"),
        ]
        pl = ProcedureList(procs)
        groups = pl.group_by(lambda p: p.procedure_type)
        assert len(groups["OLP"]) == 2
        assert len(groups["CNS"]) == 1
        assert isinstance(groups["OLP"], ProcedureList)


class TestSerialization:

    def test_to_dicts(self):
        procs = [_proc("2024-01-01"), _proc("2024-02-01")]
        pl = ProcedureList(procs)
        dicts = pl.to_dicts()
        assert len(dicts) == 2
        assert isinstance(dicts[0], dict)
        assert "events" in dicts[0]


class TestStandaloneWrappers:

    def test_open_at(self):
        procs = [_proc("2024-01-01"), _proc("2024-06-01")]
        result = open_at(procs, "2024-03-01")
        assert len(result) == 1

    def test_backlog_at(self):
        procs = [_proc("2024-01-01"), _proc("2024-06-01")]
        assert backlog_at(procs, "2024-03-01") == 1

    def test_filter_procedures(self):
        procs = [
            _proc("2024-01-01", procedure_type="OLP"),
            _proc("2024-02-01", procedure_type="CNS"),
        ]
        result = filter_procedures(procs, lambda p: p.procedure_type == "OLP")
        assert len(result) == 1
