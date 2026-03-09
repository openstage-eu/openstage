"""Dataset I/O for packaged procedure collections."""

from __future__ import annotations

import json
import warnings
import zipfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from openstage.collections import ProcedureList
from openstage.models.procedure import Procedure

# -- Class registry -----------------------------------------------------------

_DATASET_REGISTRY: dict[str, type[Procedure]] = {}


def register_dataset(identifier: str, procedure_class: type[Procedure]) -> None:
    """Register a dataset identifier to a procedure class."""
    _DATASET_REGISTRY[identifier] = procedure_class


def resolve_class(identifier: str) -> type[Procedure] | None:
    """Look up the procedure class for a dataset identifier."""
    return _DATASET_REGISTRY.get(identifier)


# Register EU procedures on import
def _register_defaults() -> None:
    from openstage.models.eu.procedure import EUProcedure

    register_dataset("openstage-eu", EUProcedure)


_register_defaults()

# Metadata keys that map to Dataset constructor arguments
_META_FIELDS = {
    "name",
    "version",
    "description",
    "creation_date",
    "total_procedures",
    "pipeline_versions",
}


class Dataset(ProcedureList):
    """A ProcedureList with metadata and file I/O.

    Supports loading from and dumping to two formats:
    - individual: one JSON file per procedure + metadata.json
    - single: one procedures.json array + metadata.json

    Both formats can be stored as directories or ZIP archives.
    """

    def __init__(
        self,
        procedures: Iterable[Procedure] = (),
        *,
        name: str = "",
        version: str = "",
        description: str = "",
        creation_date: str = "",
        pipeline_versions: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(procedures)
        self.name = name
        self.version = version
        self.description = description
        self.creation_date = creation_date
        self.pipeline_versions: dict[str, str] = pipeline_versions or {}
        self.metadata: dict[str, Any] = metadata or {}

    def _build_metadata(self) -> dict[str, Any]:
        """Build the canonical metadata dict."""
        meta: dict[str, Any] = {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "creation_date": self.creation_date,
            "total_procedures": len(self),
        }
        if self.pipeline_versions:
            meta["pipeline_versions"] = self.pipeline_versions
        # Include any extra metadata
        for k, v in self.metadata.items():
            if k not in meta:
                meta[k] = v
        return meta

    # -- Dump -----------------------------------------------------------------

    def dump(
        self,
        path: str | Path,
        *,
        format: str = "individual",
        mode: str = "clean",
    ) -> None:
        """Write the dataset to disk.

        Args:
            path: Output path. A .zip extension creates a ZIP archive.
                  A .json extension (with format="single") creates a single file.
                  Otherwise creates a directory.
            format: "individual" (one file per procedure) or "single"
                    (one procedures.json array).
            mode: "clean" (model_dump only) or "full" (model_dump + _raw).
        """
        path = Path(path)
        meta = self._build_metadata()
        proc_dicts = self._serialize_procedures(mode)

        if format == "single":
            self._dump_single(path, meta, proc_dicts)
        else:
            self._dump_individual(path, meta, proc_dicts)

    def _serialize_procedures(self, mode: str) -> list[dict]:
        dicts = []
        for p in self:
            d = p.model_dump()
            if mode == "full" and hasattr(p, "_raw") and p._raw:
                d["_raw"] = p._raw
            dicts.append(d)
        return dicts

    def _procedure_filename(self, proc: Procedure, index: int) -> str:
        """Derive a filename for a procedure."""
        ref = proc.identifiers.get("procedure_ref")
        if ref:
            # Replace / with _ for filesystem safety
            return ref.replace("/", "_") + ".json"
        return f"procedure_{index:04d}.json"

    def _dump_individual(
        self,
        path: Path,
        meta: dict,
        proc_dicts: list[dict],
    ) -> None:
        if path.suffix == ".zip":
            self._dump_individual_zip(path, meta, proc_dicts)
        else:
            self._dump_individual_dir(path, meta, proc_dicts)

    def _dump_individual_dir(
        self,
        path: Path,
        meta: dict,
        proc_dicts: list[dict],
    ) -> None:
        path.mkdir(parents=True, exist_ok=True)
        (path / "metadata.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2)
        )
        for i, (proc, d) in enumerate(zip(self, proc_dicts)):
            filename = self._procedure_filename(proc, i)
            (path / filename).write_text(json.dumps(d, ensure_ascii=False, indent=2))

    def _dump_individual_zip(
        self,
        path: Path,
        meta: dict,
        proc_dicts: list[dict],
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                "metadata.json",
                json.dumps(meta, ensure_ascii=False, indent=2),
            )
            for i, (proc, d) in enumerate(zip(self, proc_dicts)):
                filename = self._procedure_filename(proc, i)
                zf.writestr(
                    filename,
                    json.dumps(d, ensure_ascii=False, indent=2),
                )

    def _dump_single(
        self,
        path: Path,
        meta: dict,
        proc_dicts: list[dict],
    ) -> None:
        if path.suffix == ".zip":
            self._dump_single_zip(path, meta, proc_dicts)
        else:
            # Directory: write metadata.json + procedures.json inside it
            self._write_single_files(path, meta, proc_dicts)

    def _dump_single_zip(
        self,
        path: Path,
        meta: dict,
        proc_dicts: list[dict],
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                "metadata.json",
                json.dumps(meta, ensure_ascii=False, indent=2),
            )
            zf.writestr(
                "procedures.json",
                json.dumps(proc_dicts, ensure_ascii=False, indent=2),
            )

    def _write_single_files(
        self,
        directory: Path,
        meta: dict,
        proc_dicts: list[dict],
    ) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "metadata.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2)
        )
        (directory / "procedures.json").write_text(
            json.dumps(proc_dicts, ensure_ascii=False, indent=2)
        )

    # -- Load -----------------------------------------------------------------

    @classmethod
    def load(
        cls,
        path: str | Path,
        *,
        procedure_class: type[Procedure] | None = None,
    ) -> Dataset:
        """Load a dataset from disk.

        Auto-detects the format (individual vs single, directory vs ZIP).
        Resolves the procedure class from the registry if not provided.

        Args:
            path: Path to a .json file, .zip archive, or directory.
            procedure_class: Explicit procedure class for deserialization.
                If None, resolved from dataset name in metadata via registry.
        """
        path = Path(path)

        if path.suffix == ".zip":
            return cls._load_zip(path, procedure_class=procedure_class)
        elif path.suffix == ".json":
            return cls._load_single_json(path, procedure_class=procedure_class)
        elif path.is_dir():
            return cls._load_dir(path, procedure_class=procedure_class)
        else:
            raise ValueError(f"Cannot determine format for: {path}")

    @classmethod
    def _load_zip(
        cls,
        path: Path,
        *,
        procedure_class: type[Procedure] | None = None,
    ) -> Dataset:
        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()

            # Read metadata
            meta = {}
            if "metadata.json" in names:
                meta = json.loads(zf.read("metadata.json"))

            # Determine format
            if "procedures.json" in names:
                # Single format
                proc_dicts = json.loads(zf.read("procedures.json"))
            else:
                # Individual format
                proc_files = sorted(
                    n for n in names if n.endswith(".json") and n != "metadata.json"
                )
                proc_dicts = [json.loads(zf.read(f)) for f in proc_files]

        return cls._build_from_loaded(meta, proc_dicts, procedure_class)

    @classmethod
    def _load_single_json(
        cls,
        path: Path,
        *,
        procedure_class: type[Procedure] | None = None,
    ) -> Dataset:
        # Single .json file: look for metadata.json + procedures.json in same dir
        directory = path.parent
        meta = {}
        meta_path = directory / "metadata.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())

        if path.name == "procedures.json":
            proc_dicts = json.loads(path.read_text())
        else:
            # Assume the file itself is the procedures array
            proc_dicts = json.loads(path.read_text())

        return cls._build_from_loaded(meta, proc_dicts, procedure_class)

    @classmethod
    def _load_dir(
        cls,
        path: Path,
        *,
        procedure_class: type[Procedure] | None = None,
    ) -> Dataset:
        meta = {}
        meta_path = path / "metadata.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())

        procedures_path = path / "procedures.json"
        if procedures_path.exists():
            # Single format in directory
            proc_dicts = json.loads(procedures_path.read_text())
        else:
            # Individual format
            proc_files = sorted(
                f for f in path.glob("*.json") if f.name != "metadata.json"
            )
            proc_dicts = [json.loads(f.read_text()) for f in proc_files]

        return cls._build_from_loaded(meta, proc_dicts, procedure_class)

    @classmethod
    def _build_from_loaded(
        cls,
        meta: dict[str, Any],
        proc_dicts: list[dict],
        procedure_class: type[Procedure] | None,
    ) -> Dataset:
        # Resolve procedure class
        if procedure_class is None:
            name = meta.get("name", "")
            procedure_class = resolve_class(name)
            if procedure_class is None:
                warnings.warn(
                    f"No registered class for dataset '{name}', "
                    f"using base Procedure.",
                    stacklevel=3,
                )
                procedure_class = Procedure

        # Deserialize procedures
        procedures = []
        for d in proc_dicts:
            raw = d.pop("_raw", None)
            p = procedure_class.model_validate(d)
            if raw is not None:
                p._raw = raw
            procedures.append(p)

        # Split metadata into known fields and extras
        known_meta = {}
        extra_meta = {}
        for k, v in meta.items():
            if k in _META_FIELDS:
                known_meta[k] = v
            else:
                extra_meta[k] = v

        return cls(
            procedures,
            name=known_meta.get("name", ""),
            version=known_meta.get("version", ""),
            description=known_meta.get("description", ""),
            creation_date=known_meta.get("creation_date", ""),
            pipeline_versions=known_meta.get("pipeline_versions"),
            metadata=extra_meta,
        )
