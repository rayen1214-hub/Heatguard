"""Checks for the extra analyses made after the locked run (posthoc_v5.py)."""
from pathlib import Path

import pytest

import posthoc_v5 as P


@pytest.mark.parametrize("tdb, rh, chart", [(35, 50, 45), (38, 40, 47), (40, 30, 47), (42, 25, 48), (30, 70, 41)])
def test_humidex_reproduces_the_dubai_chart_cells(tdb, rh, chart):
    """Dubai Municipality guideline DM-HSD-GU38: five cells read from its Heat Index chart."""
    assert round(float(P.humidex(tdb, rh))) == chart


def test_extra_checks_can_never_write_to_the_locked_folder():
    with pytest.raises(AssertionError):
        P._safe(Path("outputs/v5"))
    assert P.PH.resolve() != Path("outputs/v5").resolve()
