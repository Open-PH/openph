"""OpenPH - Open Source Passive House Calculation Engine.

This package provides an extensible calculation engine for Passive House
energy modeling with a plugin architecture for solvers and data extensions.

Main Entry Point:
    OpenPhModel: The primary interface for using OpenPH

Example:
    >>> from openph import OpenPhModel
    >>>
    >>> # Create model and set up building data
    >>> model = OpenPhModel()
    >>> model.climate = ...
    >>> model.envelope = ...
    >>>
    >>> # Execute calculations
    >>> results = model.solve_all()

Plugin Development:
    - See OpenPhSolver protocol for creating solver plugins
    - See OpenPhAttribute protocol for creating attribute plugins
    - Register plugins via entry points in pyproject.toml
"""

from openph.openph_model import OpenPhModel

# Version info
__version__ = "0.1.0-alpha.1"

# Main exports
__all__ = [
    "OpenPhModel",
]
