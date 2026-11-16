"""The demo's browser engine (docs/demo/engine.js) must agree with the Python engine.

`make_demo_data.py` stores the Python engine's output for every demo shift and sensor scenario in
docs/demo/demo_reference.json; `docs/demo/check_engine.js` replays the same messages through the
JavaScript engine and compares risk, warning state and fallback state minute by minute.
Skipped when Node.js is not installed.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

DEMO = Path(__file__).resolve().parents[1] / "docs" / "demo"


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
def test_browser_engine_matches_python_engine():
    assert (DEMO / "demo_reference.json").exists(), "run make_demo_data.py first"
    run = subprocess.run(["node", str(DEMO / "check_engine.js")], capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
    assert "PASS" in run.stdout


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
def test_demo_page_contains_the_checked_engine():
    """The page that is shown must carry exactly the engine that was checked."""
    page, engine = (DEMO / "heatguard_demo.html").read_text(), (DEMO / "engine.js").read_text()
    assert engine in page
