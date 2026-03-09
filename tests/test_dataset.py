"""Tests for Dataset I/O."""

import json
import warnings

from openstage.dataset import Dataset, resolve_class
from openstage.models import Procedure
from openstage.models.eu import EUProcedure, EUEvent


def _make_eu_proc(ref="2024/0001/COD", start="2024-01-01", ptype="OLP"):
    """Build a minimal EUProcedure for testing."""
    from openstage.models.core import Identifiers, Identifier

    return EUProcedure(
        identifiers=Identifiers([Identifier(scheme="procedure_ref", value=ref)]),
        title={"en": f"Test procedure {ref}"},
        events=[EUEvent(date=start, type="ADP_byCOM")],
        procedure_type=ptype,
    )


class TestConstruction:

    def test_empty(self):
        ds = Dataset()
        assert len(ds) == 0
        assert ds.name == ""

    def test_with_metadata(self):
        ds = Dataset(
            name="openstage-eu",
            version="2026.02",
            description="Test dataset",
            creation_date="2026-03-09",
        )
        assert ds.name == "openstage-eu"
        assert ds.version == "2026.02"

    def test_inherits_procedure_list(self):
        procs = [_make_eu_proc(), _make_eu_proc(ref="2024/0002/COD")]
        ds = Dataset(procs, name="openstage-eu")
        assert len(ds) == 2
        # ProcedureList methods work
        assert len(ds.by_type("OLP")) == 2


class TestRegistry:

    def test_eu_registered(self):
        assert resolve_class("openstage-eu") is EUProcedure

    def test_unknown_returns_none(self):
        assert resolve_class("nonexistent") is None


class TestDumpLoadIndividualDir(object):

    def test_roundtrip(self, tmp_path):
        procs = [
            _make_eu_proc("2024/0001/COD", "2024-01-01"),
            _make_eu_proc("2024/0002/COD", "2024-02-01"),
        ]
        ds = Dataset(
            procs,
            name="openstage-eu",
            version="2026.02",
            description="EU dataset",
            creation_date="2026-03-09",
        )

        out = tmp_path / "dataset"
        ds.dump(out, format="individual")

        # Files created
        assert (out / "metadata.json").exists()
        assert (out / "2024_0001_COD.json").exists()
        assert (out / "2024_0002_COD.json").exists()

        # Load back
        loaded = Dataset.load(out)
        assert len(loaded) == 2
        assert loaded.name == "openstage-eu"
        assert loaded.version == "2026.02"
        assert isinstance(loaded[0], EUProcedure)
        assert loaded[0].procedure_type == "OLP"

    def test_metadata_json_content(self, tmp_path):
        ds = Dataset(
            [_make_eu_proc()],
            name="openstage-eu",
            version="2026.02",
            creation_date="2026-03-09",
            pipeline_versions={"openstage": "0.1.0"},
        )
        out = tmp_path / "ds"
        ds.dump(out)

        meta = json.loads((out / "metadata.json").read_text())
        assert meta["name"] == "openstage-eu"
        assert meta["total_procedures"] == 1
        assert meta["pipeline_versions"]["openstage"] == "0.1.0"


class TestDumpLoadIndividualZip:

    def test_roundtrip(self, tmp_path):
        procs = [_make_eu_proc(), _make_eu_proc(ref="2024/0002/COD")]
        ds = Dataset(procs, name="openstage-eu", version="2026.02")

        out = tmp_path / "dataset.zip"
        ds.dump(out, format="individual")

        loaded = Dataset.load(out)
        assert len(loaded) == 2
        assert isinstance(loaded[0], EUProcedure)
        assert loaded.name == "openstage-eu"


class TestDumpLoadSingleJson:

    def test_roundtrip(self, tmp_path):
        procs = [_make_eu_proc()]
        ds = Dataset(procs, name="openstage-eu", version="2026.02")

        out = tmp_path / "output"
        ds.dump(out, format="single")

        # Should create procedures.json + metadata.json in the directory
        assert (out / "procedures.json").exists()
        assert (out / "metadata.json").exists()

        loaded = Dataset.load(out / "procedures.json")
        assert len(loaded) == 1
        assert isinstance(loaded[0], EUProcedure)

    def test_load_dir_with_procedures_json(self, tmp_path):
        """Loading a directory that has procedures.json uses single format."""
        procs = [_make_eu_proc()]
        ds = Dataset(procs, name="openstage-eu")
        out = tmp_path / "ds"
        ds.dump(out, format="single")

        loaded = Dataset.load(out)
        assert len(loaded) == 1


class TestDumpLoadSingleZip:

    def test_roundtrip(self, tmp_path):
        procs = [_make_eu_proc()]
        ds = Dataset(procs, name="openstage-eu")

        out = tmp_path / "data.zip"
        ds.dump(out, format="single")

        loaded = Dataset.load(out)
        assert len(loaded) == 1
        assert isinstance(loaded[0], EUProcedure)


class TestClassResolution:

    def test_registry_based(self, tmp_path):
        ds = Dataset([_make_eu_proc()], name="openstage-eu")
        out = tmp_path / "ds"
        ds.dump(out)

        loaded = Dataset.load(out)
        assert isinstance(loaded[0], EUProcedure)

    def test_explicit_override(self, tmp_path):
        ds = Dataset([_make_eu_proc()], name="openstage-eu")
        out = tmp_path / "ds"
        ds.dump(out)

        loaded = Dataset.load(out, procedure_class=Procedure)
        assert type(loaded[0]) is Procedure

    def test_unknown_name_warns_and_uses_base(self, tmp_path):
        ds = Dataset([_make_eu_proc()], name="unknown-dataset")
        out = tmp_path / "ds"
        ds.dump(out)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            loaded = Dataset.load(out)
            relevant = [x for x in w if "No registered class" in str(x.message)]
            assert len(relevant) == 1
        assert type(loaded[0]) is Procedure


class TestFullMode:

    def test_full_mode_includes_raw(self, tmp_path):
        proc = _make_eu_proc()
        proc._raw = {"_rdf_types": ["http://example.org/type1"]}
        ds = Dataset([proc], name="openstage-eu")

        out = tmp_path / "ds"
        ds.dump(out, mode="full")

        # Read back the raw JSON to verify _raw is present
        proc_file = out / "2024_0001_COD.json"
        data = json.loads(proc_file.read_text())
        assert "_raw" in data
        assert "_rdf_types" in data["_raw"]

        # Load restores _raw
        loaded = Dataset.load(out)
        assert loaded[0]._raw["_rdf_types"] == ["http://example.org/type1"]

    def test_clean_mode_excludes_raw(self, tmp_path):
        proc = _make_eu_proc()
        proc._raw = {"_rdf_types": ["http://example.org/type1"]}
        ds = Dataset([proc], name="openstage-eu")

        out = tmp_path / "ds"
        ds.dump(out, mode="clean")

        proc_file = out / "2024_0001_COD.json"
        data = json.loads(proc_file.read_text())
        assert "_raw" not in data


class TestEmptyDataset:

    def test_empty_roundtrip(self, tmp_path):
        ds = Dataset(name="openstage-eu", version="2026.02")
        out = tmp_path / "empty"
        ds.dump(out)

        loaded = Dataset.load(out)
        assert len(loaded) == 0
        assert loaded.name == "openstage-eu"


class TestMissingMetadata:

    def test_load_without_metadata_json(self, tmp_path):
        """Loading a directory without metadata.json still works."""
        out = tmp_path / "ds"
        out.mkdir()
        proc = _make_eu_proc()
        data = proc.model_dump()
        (out / "proc.json").write_text(json.dumps(data))

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            loaded = Dataset.load(out)
        assert len(loaded) == 1
        assert loaded.name == ""


class TestProcedureListMethodsAfterLoad:

    def test_open_at_after_load(self, tmp_path):
        procs = [
            _make_eu_proc("2024/0001/COD", "2024-01-01"),
            _make_eu_proc("2024/0002/COD", "2024-06-01"),
        ]
        ds = Dataset(procs, name="openstage-eu")
        out = tmp_path / "ds.zip"
        ds.dump(out)

        loaded = Dataset.load(out)
        open_procs = loaded.open_at("2024-03-01")
        assert len(open_procs) == 1

    def test_by_status_after_load(self, tmp_path):
        procs = [
            _make_eu_proc("2024/0001/COD"),
        ]
        ds = Dataset(procs, name="openstage-eu")
        out = tmp_path / "ds"
        ds.dump(out)

        loaded = Dataset.load(out)
        assert len(loaded.by_status("ongoing")) == 1


class TestExtraMetadata:

    def test_extra_metadata_preserved(self, tmp_path):
        ds = Dataset(
            [_make_eu_proc()],
            name="openstage-eu",
            metadata={"custom_key": "custom_value"},
        )
        out = tmp_path / "ds"
        ds.dump(out)

        # Extra metadata is in the JSON
        meta = json.loads((out / "metadata.json").read_text())
        assert meta["custom_key"] == "custom_value"

        # Loaded back into metadata dict
        loaded = Dataset.load(out)
        assert loaded.metadata["custom_key"] == "custom_value"
