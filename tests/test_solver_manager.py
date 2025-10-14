"""Tests for Solver Manager.

This module tests the SolverManager implementation including:
- Solver discovery and instantiation
- Execution ordering
- Error handling
- Execution history tracking
"""

import pytest
from typing import List, Set

from openph.solvers.base import SolverPriority
from openph.solvers.manager import SolverExecutionError, SolverManager
from openph.solvers.registry import SolverInfo, SolverRegistry


# ============================================================================
# Mock Model for Testing
# ============================================================================


class MockModel:
    """Simple model for testing solver execution."""

    def __init__(self):
        self.data = {}
        self.execution_log = []

    def record_execution(self, solver_name: str):
        """Record that a solver was executed."""
        self.execution_log.append(solver_name)


# ============================================================================
# Test Solver Implementations
# ============================================================================


class FoundationSolver:
    """Foundation solver that adds data to model."""

    solver_name = "foundation"
    solver_version = "1.0.0"
    solver_priority = SolverPriority.FOUNDATION
    depends_on: List[str] = []

    def solve(self, model: MockModel) -> MockModel:
        model.data["foundation"] = "complete"
        model.record_execution("foundation")
        return model

    def validate_dependencies(self, available_solvers: Set[str]) -> bool:
        return True


class DemandSolver:
    """Demand solver that depends on foundation."""

    solver_name = "demand"
    solver_version = "1.0.0"
    solver_priority = SolverPriority.DEMAND
    depends_on: List[str] = ["foundation"]

    def solve(self, model: MockModel) -> MockModel:
        # Check that foundation ran first
        assert "foundation" in model.data
        model.data["demand"] = "complete"
        model.record_execution("demand")
        return model

    def validate_dependencies(self, available_solvers: Set[str]) -> bool:
        return "foundation" in available_solvers


class SystemsSolver:
    """Systems solver that depends on demand."""

    solver_name = "systems"
    solver_version = "1.0.0"
    solver_priority = SolverPriority.SYSTEMS
    depends_on: List[str] = ["demand"]

    def solve(self, model: MockModel) -> MockModel:
        assert "demand" in model.data
        model.data["systems"] = "complete"
        model.record_execution("systems")
        return model

    def validate_dependencies(self, available_solvers: Set[str]) -> bool:
        return "demand" in available_solvers


class FailingSolver:
    """Solver that always fails."""
    
    solver_name = "failing"
    solver_version = "1.0.0"
    solver_priority = SolverPriority.SYSTEMS  # Same priority as systems
    depends_on: List[str] = ["demand"]  # But runs before systems due to dependency
    
    def solve(self, model: MockModel) -> MockModel:
        raise RuntimeError("Intentional failure for testing")
    
    def validate_dependencies(self, available_solvers: Set[str]) -> bool:
        return "demand" in available_solvers
# ============================================================================
# SolverManager Basic Tests
# ============================================================================


class TestSolverManagerBasics:
    """Test basic SolverManager functionality."""

    def test_manager_initialization_default_registry(self):
        """Test manager creates its own registry by default."""
        manager = SolverManager()

        assert manager.registry is not None
        assert isinstance(manager.registry, SolverRegistry)
        assert manager._solver_instances == {}
        assert manager._execution_history == []

    def test_manager_initialization_with_registry(self):
        """Test manager can use provided registry."""
        registry = SolverRegistry()
        manager = SolverManager(registry=registry)

        assert manager.registry is registry

    def test_discover_solvers_clears_state(self):
        """Test that discovery clears instances and history."""
        manager = SolverManager()

        # Add some fake state
        manager._solver_instances["fake"] = None  # type: ignore
        manager._execution_history.append("fake")

        # Discover (will find nothing in test environment)
        manager.discover_solvers(group="openph.test.nonexistent")

        # State should be cleared
        assert manager._solver_instances == {}
        assert manager._execution_history == []


# ============================================================================
# Solver Instantiation Tests
# ============================================================================


class TestSolverInstantiation:
    """Test solver instantiation and caching."""

    def test_get_solver_instance_creates_instance(self):
        """Test that getting solver creates an instance."""
        manager = SolverManager()

        # Manually register solver
        info = SolverInfo(
            name=FoundationSolver.solver_name,
            solver_class=FoundationSolver,
            priority=FoundationSolver.solver_priority,
        )
        manager.registry._solvers[info.name] = info
        manager.registry._discovered = True

        # Get instance
        instance = manager.get_solver_instance("foundation")

        assert instance is not None
        assert isinstance(instance, FoundationSolver)

    def test_get_solver_instance_caches_instances(self):
        """Test that instances are cached."""
        manager = SolverManager()

        # Register solver
        info = SolverInfo(
            name=FoundationSolver.solver_name,
            solver_class=FoundationSolver,
            priority=FoundationSolver.solver_priority,
        )
        manager.registry._solvers[info.name] = info
        manager.registry._discovered = True

        # Get instance twice
        instance1 = manager.get_solver_instance("foundation")
        instance2 = manager.get_solver_instance("foundation")

        # Should be the same object
        assert instance1 is instance2

    def test_get_solver_instance_nonexistent(self):
        """Test getting non-existent solver raises error."""
        manager = SolverManager()
        manager.registry._discovered = True

        with pytest.raises(KeyError, match="not found"):
            manager.get_solver_instance("nonexistent")


# ============================================================================
# Solver Execution Tests
# ============================================================================


class TestSolverExecution:
    """Test solver execution functionality."""

    def test_execute_solver_single(self):
        """Test executing a single solver."""
        manager = SolverManager()

        # Register solver
        info = SolverInfo(
            name=FoundationSolver.solver_name,
            solver_class=FoundationSolver,
            priority=FoundationSolver.solver_priority,
        )
        manager.registry._solvers[info.name] = info
        manager.registry._discovered = True

        # Execute
        model = MockModel()
        result = manager.execute_solver("foundation", model)

        assert result is model
        assert model.data["foundation"] == "complete"
        assert "foundation" in manager.get_execution_history()

    def test_execute_solver_updates_history(self):
        """Test that execution updates history."""
        manager = SolverManager()

        # Register solver
        info = SolverInfo(
            name=FoundationSolver.solver_name,
            solver_class=FoundationSolver,
            priority=FoundationSolver.solver_priority,
        )
        manager.registry._solvers[info.name] = info
        manager.registry._discovered = True

        # Execute multiple times
        model = MockModel()
        manager.execute_solver("foundation", model)
        manager.execute_solver("foundation", model)

        history = manager.get_execution_history()
        assert len(history) == 2
        assert history == ["foundation", "foundation"]

    def test_execute_solver_with_error(self):
        """Test that solver errors are properly wrapped."""
        manager = SolverManager()
        
        # Register demand (dependency) and failing solver
        for solver_class in [DemandSolver, FailingSolver]:
            info = SolverInfo(
                name=solver_class.solver_name,
                solver_class=solver_class,
                priority=solver_class.solver_priority,
                depends_on=set(solver_class.depends_on),
            )
            manager.registry._solvers[info.name] = info
        
        manager.registry._discovered = True
        
        # Execute should raise SolverExecutionError
        # First execute demand to satisfy dependency
        model = MockModel()
        model.data["foundation"] = "complete"  # Fake foundation execution
        manager.execute_solver("demand", model, validate_dependencies=False)
        
        # Now execute failing solver
        with pytest.raises(SolverExecutionError) as exc_info:
            manager.execute_solver("failing", model)
        
        error = exc_info.value
        assert error.solver_name == "failing"
        assert "Intentional failure" in str(error)
        assert error.original_exception is not None
# ============================================================================
# Execute All Tests
# ============================================================================


class TestExecuteAll:
    """Test executing all solvers in order."""

    def test_execute_all_in_order(self):
        """Test that all solvers execute in dependency order."""
        manager = SolverManager()

        # Register solvers
        solvers = [FoundationSolver, DemandSolver, SystemsSolver]
        for solver_class in solvers:
            info = SolverInfo(
                name=solver_class.solver_name,
                solver_class=solver_class,
                priority=solver_class.solver_priority,
                depends_on=set(solver_class.depends_on),
            )
            manager.registry._solvers[info.name] = info

        manager.registry._discovered = True
        manager.registry._calculate_execution_order()

        # Execute all
        model = MockModel()
        result = manager.execute_all(model)

        # Verify execution order
        assert result.execution_log == ["foundation", "demand", "systems"]
        assert manager.get_execution_history() == ["foundation", "demand", "systems"]

    def test_execute_all_stop_on_error_true(self):
        """Test that execution stops on first error when stop_on_error=True."""
        manager = SolverManager()

        # Register foundation, demand, failing, and systems solvers
        # This creates order: foundation -> demand -> failing -> systems
        for solver_class in [
            FoundationSolver,
            DemandSolver,
            FailingSolver,
            SystemsSolver,
        ]:
            info = SolverInfo(
                name=solver_class.solver_name,
                solver_class=solver_class,
                priority=solver_class.solver_priority,
                depends_on=set(solver_class.depends_on),
            )
            manager.registry._solvers[info.name] = info

        manager.registry._discovered = True
        manager.registry._calculate_execution_order()

        # Execute all with stop_on_error=True
        model = MockModel()
        with pytest.raises(SolverExecutionError) as exc_info:
            manager.execute_all(model, stop_on_error=True)

        # Should fail on failing solver
        error = exc_info.value
        assert error.solver_name == "failing"

        # Foundation and demand should have executed, but systems should not
        assert "foundation" in model.execution_log
        assert "demand" in model.execution_log
        assert "systems" not in model.execution_log

    def test_execute_all_stop_on_error_false(self):
        """Test that execution continues and collects errors when stop_on_error=False."""
        manager = SolverManager()

        # Register solvers with failing in the middle
        # Order: foundation -> demand -> failing -> systems
        for solver_class in [
            FoundationSolver,
            DemandSolver,
            FailingSolver,
            SystemsSolver,
        ]:
            info = SolverInfo(
                name=solver_class.solver_name,
                solver_class=solver_class,
                priority=solver_class.solver_priority,
                depends_on=set(solver_class.depends_on),
            )
            manager.registry._solvers[info.name] = info

        manager.registry._discovered = True
        manager.registry._calculate_execution_order()

        # Execute all with stop_on_error=False
        model = MockModel()
        with pytest.raises(SolverExecutionError) as exc_info:
            manager.execute_all(model, stop_on_error=False)

        # Should collect all errors
        error = exc_info.value
        assert "Multiple solvers failed" in str(error)

        # All non-failing solvers should have executed
        assert "foundation" in model.execution_log
        assert "demand" in model.execution_log
        assert "systems" in model.execution_log


# ============================================================================
# Execute Subset Tests
# ============================================================================


class TestExecuteSubset:
    """Test executing a subset of solvers."""

    def test_execute_subset_respect_order(self):
        """Test subset execution respects dependency order."""
        manager = SolverManager()

        # Register solvers
        for solver_class in [FoundationSolver, DemandSolver, SystemsSolver]:
            info = SolverInfo(
                name=solver_class.solver_name,
                solver_class=solver_class,
                priority=solver_class.solver_priority,
                depends_on=set(solver_class.depends_on),
            )
            manager.registry._solvers[info.name] = info

        manager.registry._discovered = True
        manager.registry._calculate_execution_order()

        # Execute subset in wrong order, but with respect_order=True
        model = MockModel()
        result = manager.execute_subset(
            solver_names=["systems", "foundation", "demand"],
            model=model,
            respect_order=True,
        )

        # Should execute in correct order
        assert result.execution_log == ["foundation", "demand", "systems"]

    def test_execute_subset_ignore_order(self):
        """Test subset execution can ignore dependency order."""
        manager = SolverManager()

        # Register solvers
        for solver_class in [FoundationSolver, DemandSolver]:
            info = SolverInfo(
                name=solver_class.solver_name,
                solver_class=solver_class,
                priority=solver_class.solver_priority,
                depends_on=set(solver_class.depends_on),
            )
            manager.registry._solvers[info.name] = info

        manager.registry._discovered = True
        manager.registry._calculate_execution_order()

        # Execute just foundation
        model = MockModel()
        manager.execute_subset(
            solver_names=["foundation"],
            model=model,
            respect_order=False,
        )

        # Then execute demand in provided order
        manager.execute_subset(
            solver_names=["demand"],
            model=model,
            respect_order=False,
        )

        assert model.execution_log == ["foundation", "demand"]

    def test_execute_subset_nonexistent_solver(self):
        """Test that subset with nonexistent solver raises error."""
        manager = SolverManager()
        manager.registry._discovered = True

        model = MockModel()
        with pytest.raises(KeyError, match="not found"):
            manager.execute_subset(
                solver_names=["nonexistent"],
                model=model,
            )


# ============================================================================
# Utility Methods Tests
# ============================================================================


class TestUtilityMethods:
    """Test manager utility methods."""

    def test_get_execution_history_returns_copy(self):
        """Test that execution history returns a copy."""
        manager = SolverManager()

        # Add to history
        manager._execution_history.append("test")

        # Get history and modify it
        history1 = manager.get_execution_history()
        history1.append("modified")

        # Get history again
        history2 = manager.get_execution_history()

        # Should not include modification
        assert "modified" not in history2
        assert len(history2) == 1

    def test_clear_execution_history(self):
        """Test clearing execution history."""
        manager = SolverManager()
        manager._execution_history.extend(["test1", "test2"])

        manager.clear_execution_history()

        assert manager.get_execution_history() == []

    def test_reset(self):
        """Test resetting manager state."""
        manager = SolverManager()

        # Add state
        manager._solver_instances["fake"] = None  # type: ignore
        manager._execution_history.append("fake")

        # Reset
        manager.reset()

        assert manager._solver_instances == {}
        assert manager._execution_history == []

    def test_list_available_solvers(self):
        """Test listing available solvers."""
        manager = SolverManager()

        # Register solvers
        for solver_class in [FoundationSolver, DemandSolver]:
            info = SolverInfo(
                name=solver_class.solver_name,
                solver_class=solver_class,
                priority=solver_class.solver_priority,
            )
            manager.registry._solvers[info.name] = info

        manager.registry._discovered = True

        solvers = manager.list_available_solvers()
        assert set(solvers) == {"foundation", "demand"}

    def test_get_execution_order(self):
        """Test getting planned execution order."""
        manager = SolverManager()

        # Register solvers
        for solver_class in [FoundationSolver, DemandSolver, SystemsSolver]:
            info = SolverInfo(
                name=solver_class.solver_name,
                solver_class=solver_class,
                priority=solver_class.solver_priority,
                depends_on=set(solver_class.depends_on),
            )
            manager.registry._solvers[info.name] = info

        manager.registry._discovered = True
        manager.registry._calculate_execution_order()

        order = manager.get_execution_order()
        assert order == ["foundation", "demand", "systems"]
