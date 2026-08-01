from __future__ import annotations

import json
from pathlib import Path

from openchibirig.core.project import Project
from openchibirig.rigging.errors import RiggingError
from openchibirig.rigging.template import build_project

__all__ = ["RiggingError", "write_project"]


def write_project(input_root: str | Path, output_path: str | Path) -> Project:
    project = build_project(input_root)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(project.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return project
