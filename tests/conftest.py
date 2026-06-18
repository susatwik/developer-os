from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def temp_workspace(tmp_path: Path) -> Path:
    (tmp_path / "data").mkdir()
    return tmp_path
