"""Tests for Solver Registry.

This module tests the SolverRegistry implementation including:
- Entry point discovery
- Dependency resolution and ordering
- Circular dependency detection
- Error handling
"""

import pytest
from typing import Any, List, Set

from openph.solvers.base import SolverPriority
from openph.solvers.registry import SolverInfo, SolverRegistry


# ============================================================================
# Test Solver Implementations
# ============================================================================


class MinimalSolver:
    """Minimal solver implementation for testing."""

    solver_name = "minimal"
    solver_version = "1.0.0"
    solver_priority = SolverPriority.FOUNDATION
    depends_on: List[str] = []

    def solve(self, model: Any) -> Any:
        """Minimal solve implementation."""
        return model

    def validate_dependencies(self, available_solvers: Set[str]) -> bool:
        """Minimal validation."""
        return True


class FoundationSolver:
    """Foundation priority solver."""

    solver_name = "foundation"
    solver_version = "1.0.0"
    solver_priority = SolverPriority.FOUNDATION
    depends_on: List[str] = []

    def solve(self, model: Any) -> Any:
        return model

    def validate_dependencies(self, available_solvers: Set[str]) -> bool:
        return True


class DemandSolver:
    """Demand priority solver with foundation dependency."""

    solver_name = "demand"
    solver_version = "1.0.0"
    solver_priority = SolverPriority.DEMAND
    depends_on: List[str] = ["foundation"]

    def solve(self, model: Any) -> Any:
        return model

    def validate_dependencies(self, available_solvers: Set[str]) -> bool:
        return "foundation" in available_solvers


class SystemsSolver:
    """Systems priority solver with demand dependency."""

    solver_name = "systems"
    solver_version = "1.0.0"
    solver_priority = SolverPriority.SYSTEMS
    depends_on: List[str] = ["demand"]

    def solve(self, model: Any) -> Any:
        return model

    def validate_dependencies(self, available_solvers: Set[str]) -> bool:
        return "demand" in available_solvers


class AggregationSolver:
    """Aggregation priority solver with multiple dependencies."""

    solver_name = "aggregation"
    solver_version = "2.0.0"
    solver_priority = SolverPriority.AGGREGATION
    depends_on: List[str] = ["demand", "systems"]

    def solve(self, model: Any) -> Any:
        return model

    def validate_dependencies(self, available_solvers: Set[str]) -> bool:
        return "demand" in available_solvers and "systems" in available_solvers


class CircularSolverA:
    """Solver that depends on CircularSolverB (creates cycle)."""

    solver_name = "circular_a"
    solver_version = "1.0.0"
    solver_priority = SolverPriority.DEMAND
    depends_on: List[str] = ["circular_b"]

    def solve(self, model: Any) -> Any:
        return model

    def validate_dependencies(self, available_solvers: Set[str]) -> bool:
        return "circular_b" in available_solvers


class CircularSolverB:
    """Solver that depends on CircularSolverA (creates cycle)."""

    solver_name = "circular_b"
    solver_version = "1.0.0"
    solver_priority = SolverPriority.DEMAND
    depends_on: List[str] = ["circular_a"]

    def solve(self, model: Any) -> Any:
        return model

    def validate_dependencies(self, available_solvers: Set[str]) -> bool:
        return "circular_a" in available_solvers


class InvalidSolver:
    """Solver missing required protocol attributes."""

    solver_name = "invalid"
    # Missing other required attributes


# ============================================================================
# SolverInfo Tests
# ============================================================================


class TestSolverInfo:
    """Test SolverInfo dataclass functionality."""

    def test_solver_info_creation(self):
        """Test basic SolverInfo creation."""
        info = SolverInfo(
            name="test",
            solver_class=MinimalSolver,
            priority=SolverPriority.FOUNDATION,
            depends_on={"dep1", "dep2"},
            version="1.0.0",
            entry_point_name="test_ep",
        )

        assert info.name == "test"
        assert info.solver_class == MinimalSolver
        assert info.priority == SolverPriority.FOUNDATION
        assert info.depends_on == {"dep1", "dep2"}
        assert info.version == "1.0.0"
        assert info.entry_point_name == "test_ep"

    def test_solver_info_default_values(self):
        """Test SolverInfo default values."""
        info = SolverInfo(
            name="test",
            solver_class=MinimalSolver,
            priority=SolverPriority.FOUNDATION,
        )

        assert info.depends_on == set()
        assert info.version == "0.0.0"
        assert info.entry_point_name == ""

    def test_solver_info_depends_on_conversion(self):
        """Test that depends_on is converted to set."""
        # Pass list instead of set
        info = SolverInfo(
            name="test",
            solver_class=MinimalSolver,
            priority=SolverPriority.FOUNDATION,
            depends_on=["dep1", "dep2"],  # type: ignore
        )

        assert isinstance(info.depends_on, set)
        assert info.depends_on == {"dep1", "dep2"}


# ============================================================================
# SolverRegistry Basic Tests
# ============================================================================


class TestSolverRegistryBasics:
    """Test basic SolverRegistry functionality."""

    def test_registry_initialization(self):
        """Test registry initializes with empty state."""
        registry = SolverRegistry()

        assert registry._solvers == {}
        assert registry._execution_order is None
        assert registry._discovered is False

    def test_discover_solvers_without_entry_points(self):
        """Test discovery when no entry points exist."""
        registry = SolverRegistry()

        # Use a non-existent group to ensure no solvers found
        registry.discover_solvers(group="openph.test.nonexistent")

        assert registry._discovered is True
        assert len(registry._solvers) == 0
        assert registry._execution_order == []

    def test_get_solver_class_before_discovery(self):
        """Test that getting solver before discovery raises error."""
        registry = SolverRegistry()

        with pytest.raises(RuntimeError, match="before discovering solvers"):
            registry.get_solver_class("test")

    def test_get_execution_order_before_discovery(self):
        """Test that getting execution order before discovery raises error."""
        registry = SolverRegistry()

        with pytest.raises(RuntimeError, match="before discovering solvers"):
            registry.get_execution_order()

    def test_list_solvers_before_discovery(self):
        """Test that listing solvers before discovery raises error."""
        registry = SolverRegistry()

        with pytest.raises(RuntimeError, match="before discovering solvers"):
            registry.list_solvers()


# ============================================================================
# Manual Solver Registration Tests (for testing without entry points)
# ============================================================================


class TestSolverRegistryManual:
    """Test registry functionality by manually adding solvers."""

    def test_manual_registration_single_solver(self):
        """Test manually registering a single solver."""
        registry = SolverRegistry()

        # Manually add solver
        solver_info = SolverInfo(
            name=MinimalSolver.solver_name,
            solver_class=MinimalSolver,
            priority=MinimalSolver.solver_priority,
            depends_on=set(MinimalSolver.depends_on),
            version=MinimalSolver.solver_version,
        )
        registry._solvers[solver_info.name] = solver_info
        registry._discovered = True

        # Calculate execution order
        registry._calculate_execution_order()

        # Verify
        assert len(registry._solvers) == 1
        assert registry.get_solver_class("minimal") == MinimalSolver
        assert registry.get_execution_order() == ["minimal"]

    def test_manual_registration_multiple_solvers_with_dependencies(self):
        """Test multiple solvers with dependency chain."""
        registry = SolverRegistry()

        # Manually add solvers
        solvers = [FoundationSolver, DemandSolver, SystemsSolver]
        for solver_class in solvers:
            info = SolverInfo(
                name=solver_class.solver_name,
                solver_class=solver_class,
                priority=solver_class.solver_priority,
                depends_on=set(solver_class.depends_on),
                version=solver_class.solver_version,
            )
            registry._solvers[info.name] = info

        registry._discovered = True
        registry._calculate_execution_order()

        # Verify execution order respects dependencies
        order = registry.get_execution_order()
        assert order == ["foundation", "demand", "systems"]

        # Verify foundation comes before demand
        assert order.index("foundation") < order.index("demand")
        # Verify demand comes before systems
        assert order.index("demand") < order.index("systems")

    def test_manual_registration_complex_dependency_tree(self):
        """Test complex dependency tree with multiple branches."""
        registry = SolverRegistry()

        # Create dependency tree:
        #   foundation
        #   └── demand
        #       ├── systems
        #       └── aggregation (also depends on systems)

        solvers = [FoundationSolver, DemandSolver, SystemsSolver, AggregationSolver]
        for solver_class in solvers:
            info = SolverInfo(
                name=solver_class.solver_name,
                solver_class=solver_class,
                priority=solver_class.solver_priority,
                depends_on=set(solver_class.depends_on),
                version=solver_class.solver_version,
            )
            registry._solvers[info.name] = info

        registry._discovered = True
        registry._calculate_execution_order()

        order = registry.get_execution_order()

        # Verify all dependencies come before dependents
        assert order.index("foundation") < order.index("demand")
        assert order.index("demand") < order.index("systems")
        assert order.index("demand") < order.index("aggregation")
        assert order.index("systems") < order.index("aggregation")

    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected."""
        registry = SolverRegistry()

        # Add circular solvers
        for solver_class in [CircularSolverA, CircularSolverB]:
            info = SolverInfo(
                name=solver_class.solver_name,
                solver_class=solver_class,
                priority=solver_class.solver_priority,
                depends_on=set(solver_class.depends_on),
                version=solver_class.solver_version,
            )
            registry._solvers[info.name] = info

        registry._discovered = True

        # Should raise ValueError for circular dependency
        with pytest.raises(ValueError, match="Circular dependency detected"):
            registry._calculate_execution_order()

    def test_missing_dependency_detection(self):
        """Test that missing dependencies are detected."""
        registry = SolverRegistry()

        # Add solver that depends on non-existent solver
        info = SolverInfo(
            name=DemandSolver.solver_name,
            solver_class=DemandSolver,
            priority=DemandSolver.solver_priority,
            depends_on={"foundation"},  # But foundation is not registered
            version=DemandSolver.solver_version,
        )
        registry._solvers[info.name] = info
        registry._discovered = True

        # Should raise ValueError for missing dependency
        with pytest.raises(ValueError, match="depends on unknown solver"):
            registry._calculate_execution_order()

    def test_get_solver_info(self):
        """Test getting detailed solver info."""
        registry = SolverRegistry()

        solver_info = SolverInfo(
            name=MinimalSolver.solver_name,
            solver_class=MinimalSolver,
            priority=MinimalSolver.solver_priority,
            depends_on=set(MinimalSolver.depends_on),
            version=MinimalSolver.solver_version,
            entry_point_name="test_ep",
        )
        registry._solvers[solver_info.name] = solver_info
        registry._discovered = True

        # Get info
        info = registry.get_solver_info("minimal")

        assert info.name == "minimal"
        assert info.solver_class == MinimalSolver
        assert info.priority == SolverPriority.FOUNDATION
        assert info.version == "1.0.0"
        assert info.entry_point_name == "test_ep"

    def test_get_solver_info_nonexistent(self):
        """Test getting info for non-existent solver."""
        registry = SolverRegistry()
        registry._discovered = True

        with pytest.raises(KeyError, match="not found"):
            registry.get_solver_info("nonexistent")

    def test_list_solvers(self):
        """Test listing all registered solvers."""
        registry = SolverRegistry()

        # Add multiple solvers
        for solver_class in [FoundationSolver, DemandSolver]:
            info = SolverInfo(
                name=solver_class.solver_name,
                solver_class=solver_class,
                priority=solver_class.solver_priority,
                depends_on=set(solver_class.depends_on),
                version=solver_class.solver_version,
            )
            registry._solvers[info.name] = info

        registry._discovered = True

        # List solvers
        solvers = registry.list_solvers()

        assert len(solvers) == 2
        solver_names = {s.name for s in solvers}
        assert solver_names == {"foundation", "demand"}

    def test_get_execution_order_returns_copy(self):
        """Test that execution order returns a copy, not the internal list."""
        registry = SolverRegistry()

        info = SolverInfo(
            name=MinimalSolver.solver_name,
            solver_class=MinimalSolver,
            priority=MinimalSolver.solver_priority,
        )
        registry._solvers[info.name] = info
        registry._discovered = True
        registry._calculate_execution_order()

        # Get order and modify it
        order1 = registry.get_execution_order()
        order1.append("fake_solver")

        # Get order again - should be unchanged
        order2 = registry.get_execution_order()

        assert "fake_solver" not in order2
        assert len(order2) == 1


# ============================================================================
# Protocol Validation Tests
# ============================================================================


class TestProtocolValidation:
    """Test solver protocol validation."""

    def test_validate_solver_protocol_valid(self):
        """Test validation passes for valid solver."""
        registry = SolverRegistry()

        # Should not raise
        registry._validate_solver_protocol(MinimalSolver)

    def test_validate_solver_protocol_invalid(self):
        """Test validation fails for invalid solver."""
        registry = SolverRegistry()

        with pytest.raises(TypeError, match="does not implement OpenPhSolver protocol"):
            registry._validate_solver_protocol(InvalidSolver)

    def test_validate_solver_protocol_missing_multiple_attrs(self):
        """Test validation reports all missing attributes."""
        registry = SolverRegistry()

        class PartialSolver:
            solver_name = "partial"
            # Missing all other attributes

        with pytest.raises(TypeError) as exc_info:
            registry._validate_solver_protocol(PartialSolver)

        error_msg = str(exc_info.value)
        assert "solver_version" in error_msg
        assert "solver_priority" in error_msg
        assert "depends_on" in error_msg
        assert "solve" in error_msg
        assert "validate_dependencies" in error_msg
