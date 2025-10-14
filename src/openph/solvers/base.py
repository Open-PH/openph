"""Base protocol and types for OpenPH solvers.

This module defines the core interfaces that all OpenPH solvers must implement.
Solvers are discovered via entry points and managed by the SolverRegistry.
"""

from typing import Protocol, TYPE_CHECKING, Any
from abc import abstractmethod
from enum import Enum

if TYPE_CHECKING:
    from openph.model import OpenPhModel


class SolverPriority(Enum):
    """Execution priority for solver ordering.

    Solvers are executed in priority order, with lower numbers running first.
    Within each priority level, solvers are ordered by their dependencies.
    """

    FOUNDATION = 1  # Ground, climate, geometry (no dependencies)
    DEMAND = 2  # Heating/cooling demand (depends on foundation)
    SYSTEMS = 3  # HVAC, DHW systems (depends on demand)
    AGGREGATION = 4  # Site energy, carbon (depends on systems)
    ANALYSIS = 5  # Compliance, reporting (depends on aggregation)


class OpenPhSolver(Protocol):
    """Protocol that all OpenPH solvers must implement.

    This protocol defines the interface for pluggable calculation solvers.
    Solvers are discovered via entry points in pyproject.toml and managed
    by the SolverRegistry and SolverManager.

    Example:
        >>> @dataclass
        >>> class MyCustomSolver:
        >>>     model: OpenPhModel
        >>>
        >>>     @property
        >>>     def solver_name(self) -> str:
        >>>         return "my_custom_solver"
        >>>
        >>>     def solve(self) -> Any:
        >>>         # Perform calculations
        >>>         return self
    """

    @property
    @abstractmethod
    def solver_name(self) -> str:
        """Unique identifier for this solver (e.g., 'cooling_demand').

        This name is used:
        - In entry point registration
        - For dependency declarations
        - In solver discovery and execution
        """
        ...

    @property
    @abstractmethod
    def solver_version(self) -> str:
        """Version of solver algorithm (e.g., 'PHPP-10.4').

        Used for:
        - Tracking calculation methodology version
        - Validation against reference calculations
        - Debugging and auditing
        """
        ...

    @property
    @abstractmethod
    def solver_priority(self) -> SolverPriority:
        """Execution priority for dependency ordering.

        Determines when this solver runs relative to others.
        See SolverPriority enum for available levels.
        """
        ...

    @property
    def depends_on(self) -> list[str]:
        """List of solver names this solver depends on.

        The SolverManager will ensure these solvers are executed
        before this solver runs.

        Example:
            >>> @property
            >>> def depends_on(self) -> list[str]:
            >>>     return ['ground', 'solar_radiation']

        Returns:
            List of solver names (must match their solver_name property).
            Empty list if no dependencies.
        """
        return []

    @property
    def solver_description(self) -> str:
        """Human-readable description of what this solver calculates.

        Used for:
        - Documentation
        - User interfaces
        - Debugging output
        """
        return ""

    def __init__(self, model: "OpenPhModel") -> None:
        """All solvers must accept OpenPhModel reference.

        Args:
            model: The OpenPhModel instance containing building data.
        """
        ...

    @abstractmethod
    def solve(self) -> Any:
        """Execute the solver calculation and return results.

        This method should:
        1. Check if already solved (use cached results)
        2. Validate that dependencies are satisfied
        3. Perform calculations using model data
        4. Cache results for repeated calls
        5. Return calculation results (typically self for chaining)

        The SolverManager handles dependency resolution, so this method
        can assume all dependencies have been solved.

        Returns:
            Calculation results. Typically returns self to allow
            method chaining and property access.

        Raises:
            ValueError: If dependencies are not satisfied or data is invalid.

        Example:
            >>> def solve(self) -> Any:
            >>>     if self._solved:
            >>>         return self
            >>>
            >>>     # Perform calculations
            >>>     self._result = self._calculate()
            >>>     self._solved = True
            >>>     return self
        """
        ...

    def validate_dependencies(self, model: "OpenPhModel") -> list[str]:
        """Validate that required dependencies are available.

        This method is called by the SolverManager before executing
        the solver to ensure all dependencies are registered and available.

        Args:
            model: The OpenPhModel instance to check for dependencies.

        Returns:
            List of error messages. Empty list if all dependencies are satisfied.

        Example:
            >>> def validate_dependencies(self, model: OpenPhModel) -> list[str]:
            >>>     errors = []
            >>>     for dep_name in self.depends_on:
            >>>         if not hasattr(model.solvers, dep_name):
            >>>             errors.append(f"Missing required dependency: {dep_name}")
            >>>     return errors
        """
        errors = []
        for dep_name in self.depends_on:
            if not hasattr(model.solvers, dep_name):
                errors.append(f"Missing required dependency: {dep_name}")
        return errors
