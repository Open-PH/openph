"""Solver Registry for OpenPH Plugin System.

This module provides the registry system for discovering and managing solver plugins
through Python entry points. It handles solver discovery, dependency resolution,
and execution order calculation.

Key Features:
    - Automatic solver discovery via entry points
    - Dependency resolution and ordering
    - Circular dependency detection
    - Solver metadata management

Example:
    >>> registry = SolverRegistry()
    >>> registry.discover_solvers()
    >>> execution_order = registry.get_execution_order()
    >>> for solver_name in execution_order:
    ...     solver_class = registry.get_solver_class(solver_name)
    ...     # Use solver_class...
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from importlib.metadata import entry_points
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Type

from openph.solvers.base import SolverPriority

if TYPE_CHECKING:
    from openph.solvers.base import OpenPhSolver


@dataclass
class SolverInfo:
    """Metadata container for discovered solver plugins.

    This dataclass stores all relevant information about a solver plugin,
    including its class, priority, dependencies, and metadata.

    Attributes:
        name: The unique identifier for the solver (from solver_name property)
        solver_class: The actual solver class implementing OpenPhSolver protocol
        priority: The solver's priority level (from SolverPriority enum)
        depends_on: Set of solver names this solver depends on
        version: Solver version string
        entry_point_name: Original name from entry point registration
    """

    name: str
    solver_class: Type[OpenPhSolver]
    priority: SolverPriority
    depends_on: Set[str] = field(default_factory=set)
    version: str = "0.0.0"
    entry_point_name: str = ""

    def __post_init__(self) -> None:
        """Validate that depends_on is a set."""
        if not isinstance(self.depends_on, set):
            self.depends_on = set(self.depends_on) if self.depends_on else set()


class SolverRegistry:
    """Registry for managing OpenPH solver plugins.

    The SolverRegistry discovers solvers via entry points, validates their
    dependencies, and calculates the correct execution order based on
    priorities and dependencies.

    Attributes:
        _solvers: Dictionary mapping solver names to SolverInfo objects
        _execution_order: Cached list of solver names in execution order
        _discovered: Flag indicating if discovery has been run

    Example:
        >>> registry = SolverRegistry()
        >>> registry.discover_solvers()
        >>>
        >>> # Get execution order
        >>> order = registry.get_execution_order()
        >>>
        >>> # Get specific solver
        >>> ground_solver = registry.get_solver_class("ground")
        >>>
        >>> # List all solvers
        >>> for info in registry.list_solvers():
        ...     print(f"{info.name}: priority={info.priority}")
    """

    def __init__(self) -> None:
        """Initialize an empty solver registry."""
        self._solvers: Dict[str, SolverInfo] = {}
        self._execution_order: Optional[List[str]] = None
        self._discovered: bool = False

    def discover_solvers(self, group: str = "openph.solvers") -> None:
        """Discover and load solver plugins from entry points.

        This method scans the specified entry point group for registered
        solvers, loads them, and validates their protocol compliance.

        Args:
            group: The entry point group name to scan (default: "openph.solvers")

        Raises:
            TypeError: If a discovered plugin doesn't implement OpenPhSolver protocol
            ValueError: If solver metadata is invalid

        Note:
            This method can be called multiple times. Each call will clear
            previous discoveries and rescan entry points.
        """
        # Clear previous discoveries
        self._solvers.clear()
        self._execution_order = None
        self._discovered = False

        # Get entry points for the specified group
        # Handle both Python 3.10+ and 3.9 APIs
        if sys.version_info >= (3, 10):
            eps = entry_points(group=group)
        else:
            eps = entry_points().get(group, [])

        # Load each solver
        for ep in eps:
            try:
                # Load the solver class
                solver_class = ep.load()

                # Validate protocol compliance by checking required attributes
                self._validate_solver_protocol(solver_class)

                # Create SolverInfo from solver class properties
                solver_info = SolverInfo(
                    name=solver_class.solver_name,
                    solver_class=solver_class,
                    priority=solver_class.solver_priority,
                    depends_on=set(solver_class.depends_on)
                    if solver_class.depends_on
                    else set(),
                    version=solver_class.solver_version,
                    entry_point_name=ep.name,
                )

                # Register the solver
                self._solvers[solver_info.name] = solver_info

            except Exception as e:
                # Log or raise discovery errors
                raise RuntimeError(
                    f"Failed to load solver from entry point '{ep.name}': {e}"
                ) from e

        self._discovered = True

        # Calculate execution order after discovery
        self._calculate_execution_order()

    def _validate_solver_protocol(self, solver_class: Type) -> None:
        """Validate that a class implements the OpenPhSolver protocol.

        Args:
            solver_class: The class to validate

        Raises:
            TypeError: If the class doesn't implement required protocol attributes
        """
        required_attrs = [
            "solver_name",
            "solver_version",
            "solver_priority",
            "depends_on",
            "solve",
            "validate_dependencies",
        ]

        missing_attrs = [
            attr for attr in required_attrs if not hasattr(solver_class, attr)
        ]

        if missing_attrs:
            raise TypeError(
                f"Solver class {solver_class.__name__} does not implement "
                f"OpenPhSolver protocol. Missing attributes: {missing_attrs}"
            )

    def _calculate_execution_order(self) -> None:
        """Calculate the correct solver execution order.

        This method uses topological sorting to determine the execution order
        based on solver priorities and dependencies. It ensures that:
        1. Dependencies are resolved before dependents
        2. Solvers execute in priority order (FOUNDATION → ANALYSIS)
        3. No circular dependencies exist

        Raises:
            ValueError: If circular dependencies are detected
            ValueError: If a dependency references a non-existent solver
        """
        if not self._discovered:
            raise RuntimeError(
                "Cannot calculate execution order before discovering solvers. "
                "Call discover_solvers() first."
            )

        # Validate all dependencies exist
        self._validate_all_dependencies()

        # Group solvers by priority
        priority_groups: Dict[SolverPriority, List[str]] = {
            priority: [] for priority in SolverPriority
        }

        for solver_name, solver_info in self._solvers.items():
            priority_groups[solver_info.priority].append(solver_name)

        # Build execution order
        execution_order: List[str] = []
        processed: Set[str] = set()

        # Process each priority level in order
        for priority in sorted(SolverPriority, key=lambda p: p.value):
            solvers_at_priority = priority_groups[priority]

            # Topological sort within this priority level
            for solver_name in solvers_at_priority:
                self._add_solver_to_order(
                    solver_name=solver_name,
                    execution_order=execution_order,
                    processed=processed,
                    visiting=set(),
                )

        self._execution_order = execution_order

    def _add_solver_to_order(
        self,
        solver_name: str,
        execution_order: List[str],
        processed: Set[str],
        visiting: Set[str],
    ) -> None:
        """Recursively add a solver and its dependencies to execution order.

        This implements depth-first topological sorting with cycle detection.

        Args:
            solver_name: Name of solver to add
            execution_order: List being built with execution order
            processed: Set of already-processed solvers
            visiting: Set of solvers currently being visited (for cycle detection)

        Raises:
            ValueError: If a circular dependency is detected
        """
        # Already processed - skip
        if solver_name in processed:
            return

        # Circular dependency check
        if solver_name in visiting:
            cycle_path = " → ".join(list(visiting) + [solver_name])
            raise ValueError(f"Circular dependency detected: {cycle_path}")

        # Mark as visiting
        visiting.add(solver_name)

        # Get solver info
        solver_info = self._solvers[solver_name]

        # Process all dependencies first
        for dep_name in solver_info.depends_on:
            self._add_solver_to_order(
                solver_name=dep_name,
                execution_order=execution_order,
                processed=processed,
                visiting=visiting,
            )

        # Remove from visiting, add to processed
        visiting.remove(solver_name)
        processed.add(solver_name)

        # Add to execution order
        execution_order.append(solver_name)

    def _validate_all_dependencies(self) -> None:
        """Validate that all solver dependencies reference existing solvers.

        Raises:
            ValueError: If any dependency references a non-existent solver
        """
        for solver_name, solver_info in self._solvers.items():
            for dep_name in solver_info.depends_on:
                if dep_name not in self._solvers:
                    raise ValueError(
                        f"Solver '{solver_name}' depends on unknown solver '{dep_name}'"
                    )

    def get_solver_class(self, solver_name: str) -> Type[OpenPhSolver]:
        """Get the solver class for a specific solver.

        Args:
            solver_name: The name of the solver to retrieve

        Returns:
            The solver class implementing OpenPhSolver protocol

        Raises:
            KeyError: If no solver with the given name is registered
        """
        if not self._discovered:
            raise RuntimeError(
                "Cannot get solver before discovering solvers. "
                "Call discover_solvers() first."
            )

        if solver_name not in self._solvers:
            available = ", ".join(self._solvers.keys())
            raise KeyError(
                f"Solver '{solver_name}' not found. "
                f"Available solvers: {available if available else 'none'}"
            )

        return self._solvers[solver_name].solver_class

    def get_execution_order(self) -> List[str]:
        """Get the calculated solver execution order.

        Returns:
            List of solver names in execution order (dependencies first)

        Raises:
            RuntimeError: If solvers haven't been discovered yet
        """
        if not self._discovered:
            raise RuntimeError(
                "Cannot get execution order before discovering solvers. "
                "Call discover_solvers() first."
            )

        if self._execution_order is None:
            self._calculate_execution_order()

        return self._execution_order.copy()  # Return copy to prevent mutation

    def list_solvers(self) -> List[SolverInfo]:
        """Get information about all registered solvers.

        Returns:
            List of SolverInfo objects for all discovered solvers

        Raises:
            RuntimeError: If solvers haven't been discovered yet
        """
        if not self._discovered:
            raise RuntimeError(
                "Cannot list solvers before discovering solvers. "
                "Call discover_solvers() first."
            )

        return list(self._solvers.values())

    def get_solver_info(self, solver_name: str) -> SolverInfo:
        """Get detailed information about a specific solver.

        Args:
            solver_name: The name of the solver

        Returns:
            SolverInfo object with solver metadata

        Raises:
            KeyError: If no solver with the given name is registered
        """
        if not self._discovered:
            raise RuntimeError(
                "Cannot get solver info before discovering solvers. "
                "Call discover_solvers() first."
            )

        if solver_name not in self._solvers:
            available = ", ".join(self._solvers.keys())
            raise KeyError(
                f"Solver '{solver_name}' not found. "
                f"Available solvers: {available if available else 'none'}"
            )

        return self._solvers[solver_name]
