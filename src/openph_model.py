"""OpenPH Model - Main Entry Point for OpenPH Plugin System.

This module provides the main OpenPhModel class which serves as the unified
interface for the OpenPH calculation engine. It integrates both the solver
management system and the attribute extension system.

The OpenPhModel class:
    - Holds building data model (climate, envelope, HVAC, etc.)
    - Manages solver discovery, instantiation, and execution
    - Manages attribute extensions for data model classes
    - Provides convenient methods for interacting with the plugin system

Example:
    >>> from openph.openph_model import OpenPhModel
    >>>
    >>> # Create model and auto-discover plugins
    >>> model = OpenPhModel()
    >>>
    >>> # Set up building data
    >>> model.climate = Climate(...)
    >>> model.envelope = Envelope(...)
    >>>
    >>> # List available solvers
    >>> print(model.list_solvers())
    >>>
    >>> # Execute specific solver
    >>> result = model.solve("heating_demand")
    >>>
    >>> # Execute all solvers
    >>> results = model.solve_all()
    >>>
    >>> # Work with attribute extensions
    >>> print(model.list_attributes())
    >>> cost_data = model.get_attribute_data("cost_data", wall_instance)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from openph.attributes.manager import AttributeManager
from openph.solvers.manager import SolverManager

if TYPE_CHECKING:
    from openph.attributes.base import OpenPhAttribute
    from openph.model.areas import PhAreas
    from openph.model.climate import PhxMonthlyClimateData
    from openph.model.envelope import PhxEnvelope
    from openph.model.hvac.hvac import PhxHVAC
    from openph.model.ihg import PhxInternalGains
    from openph.model.rooms import PhxRoomCollection
    from openph.model.settings import PhxSettings
    from openph.solvers.base import OpenPhSolver


@dataclass
class OpenPhModel:
    """Main model class for OpenPH calculation engine.

    This is the primary entry point for using OpenPH. It combines:
        - Building data model (climate, envelope, HVAC, rooms, etc.)
        - Solver management for calculations
        - Attribute management for data extensions

    The model automatically discovers and initializes both solvers and
    attributes from installed packages using Python entry points.

    Attributes:
        climate: Climate data for the building location
        envelope: Building envelope (walls, windows, etc.)
        hvac: HVAC system data
        rooms: Collection of rooms/zones
        areas: Building areas (TFA, etc.)
        internal_gains: Internal heat gains
        settings: Global calculation settings
        solvers: SolverManager instance for solver operations
        attributes: AttributeManager instance for attribute operations

    Example:
        >>> model = OpenPhModel()
        >>> model.climate = PhxMonthlyClimateData(...)
        >>> model.envelope = PhxEnvelope(...)
        >>>
        >>> # Execute calculations
        >>> heating_result = model.solve("heating_demand")
        >>>
        >>> # Get solver info
        >>> info = model.solver_info("heating_demand")
        >>> print(f"Priority: {info.priority}")
    """

    # Building data model
    climate: Optional[PhxMonthlyClimateData] = None
    envelope: Optional[PhxEnvelope] = None
    hvac: Optional[PhxHVAC] = None
    rooms: Optional[PhxRoomCollection] = None
    areas: Optional[PhAreas] = None
    internal_gains: Optional[PhxInternalGains] = None
    settings: Optional[PhxSettings] = None

    # Plugin managers (initialized in __post_init__)
    solvers: SolverManager = field(default_factory=SolverManager, init=False)
    attributes: AttributeManager = field(default_factory=AttributeManager, init=False)

    def __post_init__(self):
        """Initialize plugin managers and discover extensions.

        This automatically discovers and initializes both solvers and
        attributes from installed packages.
        """
        # Initialize managers
        self.solvers = SolverManager()
        self.attributes = AttributeManager()

        # Discover plugins from entry points
        self.solvers.discover_solvers()
        self.attributes.discover_attributes()

    # -------------------------------------------------------------------------
    # Solver Convenience Methods
    # -------------------------------------------------------------------------

    def solve(
        self,
        solver_name: str,
        *,
        force: bool = False,
        **kwargs: Any,
    ) -> OpenPhSolver:
        """Execute a specific solver.

        This is a convenience method that wraps SolverManager.execute_solver().
        The solver will automatically execute any required dependencies first.

        Args:
            solver_name: Name of the solver to execute (e.g., "heating_demand")
            force: If True, re-execute even if already executed
            **kwargs: Additional arguments passed to solver

        Returns:
            The executed solver instance with results

        Raises:
            ValueError: If solver not found
            SolverExecutionError: If solver execution fails

        Example:
            >>> result = model.solve("heating_demand")
            >>> print(result.annual_demand)
        """
        return self.solvers.execute_solver(
            solver_name, model=self, force=force, **kwargs
        )

    def solve_all(
        self,
        *,
        force: bool = False,
        **kwargs: Any,
    ) -> List[OpenPhSolver]:
        """Execute all available solvers in dependency order.

        This is a convenience method that wraps SolverManager.execute_all().

        Args:
            force: If True, re-execute all solvers
            **kwargs: Additional arguments passed to all solvers

        Returns:
            List of executed solver instances with results

        Raises:
            SolverExecutionError: If any solver execution fails

        Example:
            >>> results = model.solve_all()
            >>> for solver in results:
            ...     print(f"{solver.solver_name}: complete")
        """
        return self.solvers.execute_all(model=self, force=force, **kwargs)

    def solve_subset(
        self,
        solver_names: List[str],
        *,
        force: bool = False,
        **kwargs: Any,
    ) -> List[OpenPhSolver]:
        """Execute a subset of solvers in dependency order.

        Args:
            solver_names: List of solver names to execute
            force: If True, re-execute solvers
            **kwargs: Additional arguments passed to solvers

        Returns:
            List of executed solver instances

        Example:
            >>> results = model.solve_subset(["ground", "heating_demand"])
        """
        return self.solvers.execute_subset(
            solver_names, model=self, force=force, **kwargs
        )

    def list_solvers(self) -> List[str]:
        """Get list of all available solver names.

        Returns:
            List of solver names that can be executed

        Example:
            >>> solvers = model.list_solvers()
            >>> print(solvers)
            ['ground', 'solar_radiation', 'heating_demand', 'cooling_demand']
        """
        return self.solvers.list_available_solvers()

    def solver_info(self, solver_name: str) -> Dict[str, Any]:
        """Get detailed information about a solver.

        Args:
            solver_name: Name of the solver

        Returns:
            Dictionary with solver metadata:
                - name: Solver name
                - version: Solver version
                - priority: Execution priority
                - depends_on: List of dependency solver names
                - description: Solver description

        Raises:
            ValueError: If solver not found

        Example:
            >>> info = model.solver_info("heating_demand")
            >>> print(info['depends_on'])
            ['ground', 'solar_radiation']
        """
        solver_registry = self.solvers.registry
        if solver_name not in solver_registry._solvers:
            raise ValueError(f"Solver '{solver_name}' not found")

        solver_info_obj = solver_registry._solvers[solver_name]
        return {
            "name": solver_name,
            "version": solver_info_obj.version,
            "priority": solver_info_obj.priority,
            "depends_on": solver_info_obj.depends_on,
            "description": solver_info_obj.description,
        }

    def get_execution_order(self) -> List[str]:
        """Get the order solvers will execute in.

        Returns:
            List of solver names in dependency-resolved order

        Example:
            >>> order = model.get_execution_order()
            >>> print(order)
            ['ground', 'solar_radiation', 'heating_demand', 'cooling_demand']
        """
        return self.solvers.get_execution_order()

    def get_execution_history(self) -> List[str]:
        """Get list of solvers that have been executed.

        Returns:
            List of solver names in order they were executed

        Example:
            >>> history = model.get_execution_history()
            >>> print(history)
            ['ground', 'heating_demand']
        """
        return self.solvers.get_execution_history()

    def reset_solvers(self) -> None:
        """Reset all solver state.

        Clears execution history and solver instance cache.
        Use this to force all solvers to re-execute.

        Example:
            >>> model.solve("heating_demand")
            >>> model.reset_solvers()
            >>> model.solve("heating_demand")  # Will re-execute
        """
        self.solvers.reset()

    # -------------------------------------------------------------------------
    # Attribute Convenience Methods
    # -------------------------------------------------------------------------

    def list_attributes(self) -> List[str]:
        """Get list of all available attribute extension names.

        Returns:
            List of attribute names that can be used

        Example:
            >>> attrs = model.list_attributes()
            >>> print(attrs)
            ['cost_data', 'carbon_data', 'lca_data']
        """
        return self.attributes.list_available_attributes()

    def attribute_info(self, attribute_name: str) -> Dict[str, Any]:
        """Get detailed information about an attribute extension.

        Args:
            attribute_name: Name of the attribute

        Returns:
            Dictionary with attribute metadata:
                - name: Attribute name
                - version: Attribute version
                - extends_classes: List of classes this extends
                - description: Attribute description

        Raises:
            ValueError: If attribute not found

        Example:
            >>> info = model.attribute_info("cost_data")
            >>> print(info['extends_classes'])
            ['PhxEnvelope', 'PhxWindow']
        """
        attr_registry = self.attributes.registry
        if attribute_name not in attr_registry._attributes:
            raise ValueError(f"Attribute '{attribute_name}' not found")

        attr_info_obj = attr_registry._attributes[attribute_name]
        return {
            "name": attribute_name,
            "version": attr_info_obj.version,
            "extends_classes": attr_info_obj.extends_classes,
            "description": attr_info_obj.description,
        }

    def get_attributes_for_class(self, class_name: str) -> List[str]:
        """Get all attributes that extend a specific class.

        Args:
            class_name: Name of the class to check

        Returns:
            List of attribute names that extend this class

        Example:
            >>> attrs = model.get_attributes_for_class("PhxEnvelope")
            >>> print(attrs)
            ['cost_data', 'carbon_data']
        """
        return self.attributes.get_attributes_for_class(class_name)

    def set_attribute_data(
        self,
        attribute_name: str,
        instance: Any,
        data: Dict[str, Any],
    ) -> None:
        """Set attribute data for a model instance.

        Args:
            attribute_name: Name of the attribute
            instance: The model instance to attach data to
            data: Dictionary of attribute data

        Raises:
            ValueError: If attribute not found or validation fails

        Example:
            >>> wall = PhxWall(...)
            >>> model.set_attribute_data(
            ...     "cost_data",
            ...     wall,
            ...     {"unit_cost": 150.0, "currency": "USD"}
            ... )
        """
        self.attributes.set_attribute_data(attribute_name, instance, data)

    def get_attribute_data(
        self,
        attribute_name: str,
        instance: Any,
    ) -> Dict[str, Any]:
        """Get attribute data for a model instance.

        Args:
            attribute_name: Name of the attribute
            instance: The model instance to get data from

        Returns:
            Dictionary of attribute data, or default values if not set

        Example:
            >>> cost_data = model.get_attribute_data("cost_data", wall)
            >>> print(cost_data["unit_cost"])
            150.0
        """
        return self.attributes.get_attribute_data(attribute_name, instance)

    def has_attribute_data(
        self,
        attribute_name: str,
        instance: Any,
    ) -> bool:
        """Check if instance has data for an attribute.

        Args:
            attribute_name: Name of the attribute
            instance: The model instance to check

        Returns:
            True if instance has attribute data set

        Example:
            >>> if model.has_attribute_data("cost_data", wall):
            ...     print("Wall has cost data")
        """
        return self.attributes.has_attribute_data(attribute_name, instance)

    def reset_attributes(self) -> None:
        """Reset all attribute state.

        Clears all attribute data and instance cache.

        Example:
            >>> model.reset_attributes()
        """
        self.attributes.reset()

    # -------------------------------------------------------------------------
    # Model Validation
    # -------------------------------------------------------------------------

    def validate(self) -> List[str]:
        """Validate the model is ready for calculations.

        Returns:
            List of validation error messages (empty if valid)

        Example:
            >>> errors = model.validate()
            >>> if errors:
            ...     print("Validation errors:")
            ...     for error in errors:
            ...         print(f"  - {error}")
        """
        errors = []

        # Check required data
        if self.climate is None:
            errors.append("Climate data is required")

        if self.envelope is None:
            errors.append("Envelope data is required")

        if self.rooms is None:
            errors.append("Rooms data is required")

        # Add more validation as needed

        return errors

    def is_valid(self) -> bool:
        """Check if model is valid for calculations.

        Returns:
            True if model passes all validation checks

        Example:
            >>> if model.is_valid():
            ...     results = model.solve_all()
        """
        return len(self.validate()) == 0
