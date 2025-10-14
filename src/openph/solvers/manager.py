"""Solver Manager for OpenPH Plugin System.

This module provides the manager class for coordinating solver execution.
The SolverManager uses the SolverRegistry to discover solvers and execute
them in the correct dependency order.

Key Features:
    - Automatic solver discovery and instantiation
    - Dependency-ordered execution
    - Error handling and reporting
    - Execution state tracking

Example:
    >>> from openph.solvers.manager import SolverManager
    >>>
    >>> # Create manager and discover solvers
    >>> manager = SolverManager()
    >>> manager.discover_solvers()
    >>>
    >>> # Execute all solvers
    >>> result = manager.execute_all(model)
    >>>
    >>> # Execute specific solver
    >>> result = manager.execute_solver("ground", model)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from openph.solvers.registry import SolverRegistry

if TYPE_CHECKING:
    from openph.solvers.base import OpenPhSolver


class SolverExecutionError(Exception):
    """Exception raised when solver execution fails."""

    def __init__(
        self,
        solver_name: str,
        message: str,
        original_exception: Optional[Exception] = None,
    ):
        """Initialize solver execution error.

        Args:
            solver_name: Name of the solver that failed
            message: Error message
            original_exception: The original exception that was raised
        """
        self.solver_name = solver_name
        self.original_exception = original_exception
        super().__init__(f"Solver '{solver_name}' failed: {message}")


class SolverManager:
    """Manager for coordinating solver execution.

    The SolverManager handles the lifecycle of solvers including:
    - Discovery via SolverRegistry
    - Instantiation with caching
    - Execution in dependency order
    - Error handling and reporting

    Attributes:
        registry: The SolverRegistry used for discovery
        _solver_instances: Cache of instantiated solver objects
        _execution_history: List of solver names that have been executed

    Example:
        >>> manager = SolverManager()
        >>> manager.discover_solvers()
        >>>
        >>> # Execute all solvers in order
        >>> result = manager.execute_all(model)
        >>>
        >>> # Check execution history
        >>> executed = manager.get_execution_history()
        >>> print(f"Executed: {executed}")
        >>>
        >>> # Execute specific solver
        >>> result = manager.execute_solver("heating_demand", model)
    """

    def __init__(self, registry: Optional[SolverRegistry] = None):
        """Initialize the solver manager.

        Args:
            registry: Optional SolverRegistry to use. If not provided,
                     a new registry will be created.
        """
        self.registry = registry if registry is not None else SolverRegistry()
        self._solver_instances: Dict[str, OpenPhSolver] = {}
        self._execution_history: List[str] = []

    def discover_solvers(self, group: str = "openph.solvers") -> None:
        """Discover available solvers via entry points.

        This delegates to the registry's discover_solvers method and
        clears any cached instances and execution history.

        Args:
            group: Entry point group to scan (default: "openph.solvers")
        """
        self.registry.discover_solvers(group=group)
        self._solver_instances.clear()
        self._execution_history.clear()

    def get_solver_instance(self, solver_name: str) -> OpenPhSolver:
        """Get or create a solver instance.

        Solver instances are cached, so repeated calls for the same
        solver will return the same instance.

        Args:
            solver_name: Name of the solver to instantiate

        Returns:
            Instantiated solver object

        Raises:
            KeyError: If solver with given name is not found
            RuntimeError: If solver instantiation fails
        """
        # Return cached instance if available
        if solver_name in self._solver_instances:
            return self._solver_instances[solver_name]

        # Get solver class from registry
        solver_class = self.registry.get_solver_class(solver_name)

        # Instantiate solver
        try:
            solver_instance = solver_class()
            self._solver_instances[solver_name] = solver_instance
            return solver_instance
        except Exception as e:
            raise RuntimeError(
                f"Failed to instantiate solver '{solver_name}': {e}"
            ) from e

    def execute_solver(
        self,
        solver_name: str,
        model: Any,
        validate_dependencies: bool = True,
    ) -> Any:
        """Execute a specific solver.

        Args:
            solver_name: Name of the solver to execute
            model: The model object to process
            validate_dependencies: Whether to validate dependencies before execution

        Returns:
            The modified model object

        Raises:
            SolverExecutionError: If solver execution fails
            ValueError: If dependency validation fails
        """
        # Get solver instance
        solver = self.get_solver_instance(solver_name)

        # Validate dependencies if requested
        if validate_dependencies:
            available_solvers = set(self.registry._solvers.keys())
            if not solver.validate_dependencies(available_solvers):
                solver_info = self.registry.get_solver_info(solver_name)
                missing = solver_info.depends_on - available_solvers
                raise ValueError(
                    f"Solver '{solver_name}' has unsatisfied dependencies: {missing}"
                )

        # Execute solver
        try:
            result = solver.solve(model)
            self._execution_history.append(solver_name)
            return result
        except Exception as e:
            raise SolverExecutionError(
                solver_name=solver_name,
                message=str(e),
                original_exception=e,
            ) from e

    def execute_all(
        self,
        model: Any,
        stop_on_error: bool = False,
    ) -> Any:
        """Execute all solvers in dependency order.

        Args:
            model: The model object to process
            stop_on_error: If True, stop execution on first error.
                         If False, collect errors and raise at the end.

        Returns:
            The modified model object

        Raises:
            SolverExecutionError: If any solver fails (immediately if stop_on_error=True,
                                 or after all solvers if stop_on_error=False)
        """
        execution_order = self.registry.get_execution_order()
        errors: List[SolverExecutionError] = []

        for solver_name in execution_order:
            try:
                model = self.execute_solver(
                    solver_name=solver_name,
                    model=model,
                    validate_dependencies=False,  # Already validated by registry ordering
                )
            except SolverExecutionError as e:
                if stop_on_error:
                    raise
                errors.append(e)

        # If we collected errors, raise a combined error
        if errors:
            error_messages = [f"{e.solver_name}: {str(e)}" for e in errors]
            raise SolverExecutionError(
                solver_name="multiple",
                message=f"Multiple solvers failed: {'; '.join(error_messages)}",
                original_exception=None,
            )

        return model

    def execute_subset(
        self,
        solver_names: List[str],
        model: Any,
        respect_order: bool = True,
        stop_on_error: bool = False,
    ) -> Any:
        """Execute a subset of solvers.

        Args:
            solver_names: List of solver names to execute
            model: The model object to process
            respect_order: If True, execute in dependency order.
                          If False, execute in the order provided.
            stop_on_error: If True, stop execution on first error

        Returns:
            The modified model object

        Raises:
            SolverExecutionError: If any solver fails
            KeyError: If any solver name is not found
        """
        # Validate all solver names exist
        for name in solver_names:
            if name not in self.registry._solvers:
                available = ", ".join(self.registry._solvers.keys())
                raise KeyError(f"Solver '{name}' not found. Available: {available}")

        # Determine execution order
        if respect_order:
            # Filter full execution order to include only requested solvers
            full_order = self.registry.get_execution_order()
            execution_order = [s for s in full_order if s in solver_names]
        else:
            execution_order = solver_names

        # Execute solvers
        errors: List[SolverExecutionError] = []

        for solver_name in execution_order:
            try:
                model = self.execute_solver(
                    solver_name=solver_name,
                    model=model,
                    validate_dependencies=False,
                )
            except SolverExecutionError as e:
                if stop_on_error:
                    raise
                errors.append(e)

        # If we collected errors, raise a combined error
        if errors:
            error_messages = [f"{e.solver_name}: {str(e)}" for e in errors]
            raise SolverExecutionError(
                solver_name="multiple",
                message=f"Multiple solvers failed: {'; '.join(error_messages)}",
                original_exception=None,
            )

        return model

    def get_execution_history(self) -> List[str]:
        """Get the history of executed solvers.

        Returns:
            List of solver names in the order they were executed
        """
        return self._execution_history.copy()

    def clear_execution_history(self) -> None:
        """Clear the execution history."""
        self._execution_history.clear()

    def reset(self) -> None:
        """Reset the manager, clearing instances and history.

        This does not clear the registry's discovered solvers.
        Call discover_solvers() to rescan entry points.
        """
        self._solver_instances.clear()
        self._execution_history.clear()

    def list_available_solvers(self) -> List[str]:
        """Get list of available solver names.

        Returns:
            List of solver names that can be executed
        """
        return [info.name for info in self.registry.list_solvers()]

    def get_execution_order(self) -> List[str]:
        """Get the planned execution order for all solvers.

        Returns:
            List of solver names in dependency order
        """
        return self.registry.get_execution_order()
