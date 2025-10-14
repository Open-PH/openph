"""OpenPH Solver System.

This package provides the solver infrastructure for OpenPH, including:
- Base protocols for solver plugins
- Registry system for solver discovery
- Execution order management
"""

from openph.solvers.base import OpenPhSolver, SolverPriority
from openph.solvers.registry import SolverInfo, SolverRegistry

__all__ = [
    "OpenPhSolver",
    "SolverPriority",
    "SolverInfo",
    "SolverRegistry",
]
