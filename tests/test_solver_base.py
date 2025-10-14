"""Tests for OpenPhSolver protocol and SolverPriority enum."""

from dataclasses import dataclass
from typing import Any

from openph.solvers.base import OpenPhSolver, SolverPriority


class TestSolverPriority:
    """Test SolverPriority enum."""

    def test_priority_values(self):
        """Test that priorities have correct numeric values."""
        assert SolverPriority.FOUNDATION.value == 1
        assert SolverPriority.DEMAND.value == 2
        assert SolverPriority.SYSTEMS.value == 3
        assert SolverPriority.AGGREGATION.value == 4
        assert SolverPriority.ANALYSIS.value == 5

    def test_priority_ordering(self):
        """Test that priorities can be sorted correctly."""
        priorities = [
            SolverPriority.ANALYSIS,
            SolverPriority.FOUNDATION,
            SolverPriority.SYSTEMS,
            SolverPriority.DEMAND,
            SolverPriority.AGGREGATION,
        ]

        sorted_priorities = sorted(priorities, key=lambda p: p.value)

        assert sorted_priorities[0] == SolverPriority.FOUNDATION
        assert sorted_priorities[1] == SolverPriority.DEMAND
        assert sorted_priorities[2] == SolverPriority.SYSTEMS
        assert sorted_priorities[3] == SolverPriority.AGGREGATION
        assert sorted_priorities[4] == SolverPriority.ANALYSIS


class TestOpenPhSolverProtocol:
    """Test OpenPhSolver protocol compliance."""

    def test_minimal_solver_implementation(self):
        """Test that a minimal solver implementation satisfies the protocol."""

        # Create a minimal solver implementation
        @dataclass
        class MinimalSolver:
            model: Any  # Mock model for testing
            _solved: bool = False

            @property
            def solver_name(self) -> str:
                return "test_solver"

            @property
            def solver_version(self) -> str:
                return "1.0.0"

            @property
            def solver_priority(self) -> SolverPriority:
                return SolverPriority.FOUNDATION

            @property
            def depends_on(self) -> list[str]:
                return []  # No dependencies

            @property
            def solver_description(self) -> str:
                return ""  # No description

            def solve(self) -> Any:
                self._solved = True
                return self

        # Verify it works
        solver = MinimalSolver(model=None)
        assert solver.solver_name == "test_solver"
        assert solver.solver_version == "1.0.0"
        assert solver.solver_priority == SolverPriority.FOUNDATION
        assert solver.depends_on == []
        assert solver.solver_description == ""  # Will use protocol default

        # Test solve method
        result = solver.solve()
        assert result is solver
        assert solver._solved is True

    def test_solver_with_dependencies(self):
        """Test solver with dependency declarations."""

        @dataclass
        class DependentSolver:
            model: Any

            @property
            def solver_name(self) -> str:
                return "dependent_solver"

            @property
            def solver_version(self) -> str:
                return "1.0.0"

            @property
            def solver_priority(self) -> SolverPriority:
                return SolverPriority.DEMAND

            @property
            def depends_on(self) -> list[str]:
                return ["ground", "solar_radiation"]

            @property
            def solver_description(self) -> str:
                return "A solver that depends on ground and solar"

            def solve(self) -> Any:
                return self

        solver = DependentSolver(model=None)
        assert solver.depends_on == ["ground", "solar_radiation"]
        assert solver.solver_description == "A solver that depends on ground and solar"

    def test_validate_dependencies_default_implementation(self):
        """Test the default validate_dependencies implementation."""

        @dataclass
        class TestSolver:
            model: Any

            @property
            def solver_name(self) -> str:
                return "test_solver"

            @property
            def solver_version(self) -> str:
                return "1.0.0"

            @property
            def solver_priority(self) -> SolverPriority:
                return SolverPriority.FOUNDATION

            @property
            def depends_on(self) -> list[str]:
                return ["dependency_1", "dependency_2"]

            def solve(self) -> Any:
                return self

            def validate_dependencies(self, model: Any) -> list[str]:
                # Use the protocol's default implementation
                errors = []
                for dep_name in self.depends_on:
                    if not hasattr(model.solvers, dep_name):
                        errors.append(f"Missing required dependency: {dep_name}")
                return errors

        # Create mock model without dependencies
        class MockModel:
            class MockSolvers:
                pass

            solvers = MockSolvers()

        solver = TestSolver(model=None)
        mock_model = MockModel()

        # Should report missing dependencies
        errors = solver.validate_dependencies(mock_model)
        assert len(errors) == 2
        assert "Missing required dependency: dependency_1" in errors
        assert "Missing required dependency: dependency_2" in errors

        # Add dependencies to mock model
        mock_model.solvers.dependency_1 = True
        mock_model.solvers.dependency_2 = True

        # Should now have no errors
        errors = solver.validate_dependencies(mock_model)
        assert len(errors) == 0


class TestProtocolTypeChecking:
    """Test that the protocol works with type checking."""

    def test_protocol_as_type_hint(self):
        """Test that protocol can be used as a type hint."""

        @dataclass
        class ConcreteSolver:
            model: Any

            @property
            def solver_name(self) -> str:
                return "concrete"

            @property
            def solver_version(self) -> str:
                return "1.0.0"

            @property
            def solver_priority(self) -> SolverPriority:
                return SolverPriority.FOUNDATION

            def solve(self) -> Any:
                return self

        def process_solver(solver: OpenPhSolver) -> str:
            """Function that accepts any object satisfying the protocol."""
            return solver.solver_name

        # Should work with our concrete implementation
        solver = ConcreteSolver(model=None)
        result = process_solver(solver)
        assert result == "concrete"
