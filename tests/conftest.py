"""Shared fixtures for openstage tests.

Discovers openbasement's RDF fixture files and runs extract() once per session,
providing parametrized procedure dicts for integration tests.
"""

from __future__ import annotations

import pathlib

import pytest

# Try to import openbasement; tests that need it will be skipped if unavailable.
try:
    from rdflib import Graph
    from openbasement import extract

    HAS_OPENBASEMENT = True
except ImportError:
    HAS_OPENBASEMENT = False


def _find_fixture_dir() -> pathlib.Path | None:
    """Locate openbasement's procedure fixtures directory."""
    if not HAS_OPENBASEMENT:
        return None

    # Try package-relative path first (works with editable installs)
    import openbasement

    pkg_dir = pathlib.Path(openbasement.__file__).resolve().parent
    # Package is at src/openbasement/__init__.py -> repo is two levels up
    repo_root = pkg_dir.parent.parent
    candidate = repo_root / "tests" / "fixtures" / "procedures"
    if candidate.is_dir():
        return candidate

    # Fall back to known sibling layout
    sibling = pathlib.Path(__file__).resolve().parents[2] / "openbasement" / "tests" / "fixtures" / "procedures"
    if sibling.is_dir():
        return sibling

    return None


def _extract_all_fixtures(fixture_dir: pathlib.Path) -> dict[str, list[dict]]:
    """Run openbasement extract() on every RDF file, returning {stem: [dicts]}."""
    results = {}
    for rdf_file in sorted(fixture_dir.glob("*.rdf")):
        g = Graph()
        g.parse(rdf_file, format="xml")
        procedures = extract(g, "eu_procedure")
        if procedures:
            results[rdf_file.stem] = procedures
    return results


@pytest.fixture(scope="session")
def extracted_procedures() -> dict[str, list[dict]]:
    """Session-scoped cache of all openbasement extraction results.

    Returns a dict mapping {procedure_ref: list[dict]}.
    Skips if openbasement or fixtures are unavailable.
    """
    if not HAS_OPENBASEMENT:
        pytest.skip("openbasement not installed")

    fixture_dir = _find_fixture_dir()
    if fixture_dir is None:
        pytest.skip("openbasement fixture directory not found")

    results = _extract_all_fixtures(fixture_dir)
    if not results:
        pytest.skip("no fixtures produced extraction results")

    return results


def _collect_procedure_params():
    """Collect parametrize params at collection time (outside fixtures)."""
    if not HAS_OPENBASEMENT:
        return []

    fixture_dir = _find_fixture_dir()
    if fixture_dir is None:
        return []

    return sorted(f.stem for f in fixture_dir.glob("*.rdf"))


_FIXTURE_IDS = _collect_procedure_params()


@pytest.fixture(params=_FIXTURE_IDS if _FIXTURE_IDS else [pytest.param("skip", marks=pytest.mark.skip)])
def procedure_dict(request, extracted_procedures):
    """Parametrized fixture yielding one openbasement procedure dict at a time.

    Each param is a procedure reference (RDF file stem). The actual extraction
    result comes from the session-scoped extracted_procedures cache.
    """
    proc_ref = request.param
    dicts = extracted_procedures.get(proc_ref, [])
    if not dicts:
        pytest.skip(f"no extraction result for {proc_ref}")
    return dicts[0]
