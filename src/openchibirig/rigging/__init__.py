"""Character-independent rig templates and parameter generation."""

from openchibirig.rigging.errors import RiggingError
from openchibirig.rigging.project_writer import write_project
from openchibirig.rigging.template import build_project

__all__ = ["RiggingError", "build_project", "write_project"]
