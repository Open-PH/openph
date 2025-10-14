"""Tests for OpenPhModel - Main Entry Point."""

import pytest

from openph.attributes.manager import AttributeManager
from openph.openph_model import OpenPhModel
from openph.solvers.manager import SolverManager


class TestOpenPhModelInstantiation:
    """Test OpenPhModel instantiation and initialization."""

    def test_create_empty_model(self):
        """Test creating an empty model."""
        model = OpenPhModel()
        assert model is not None
        assert isinstance(model, OpenPhModel)

    def test_model_has_solver_manager(self):
        """Test that model has SolverManager instance."""
        model = OpenPhModel()
        assert hasattr(model, "solvers")
        assert isinstance(model.solvers, SolverManager)

    def test_model_has_attribute_manager(self):
        """Test that model has AttributeManager instance."""
        model = OpenPhModel()
        assert hasattr(model, "attributes")
        assert isinstance(model.attributes, AttributeManager)

    def test_managers_auto_discover(self):
        """Test that managers auto-discover on initialization."""
        model = OpenPhModel()
        # Should have discovered solvers (even if empty)
        assert model.solvers.registry is not None
        # Should have discovered attributes (even if empty)
        assert model.attributes.registry is not None

    def test_model_data_attributes_default_to_none(self):
        """Test that model data attributes default to None."""
        model = OpenPhModel()
        assert model.climate is None
        assert model.envelope is None
        assert model.hvac is None
        assert model.rooms is None
        assert model.areas is None
        assert model.internal_gains is None
        assert model.settings is None


class TestOpenPhModelSolverMethods:
    """Test OpenPhModel solver convenience methods."""

    def test_list_solvers(self):
        """Test listing available solvers."""
        model = OpenPhModel()
        solvers = model.list_solvers()
        assert isinstance(solvers, list)
        # With no plugins installed, should be empty
        assert solvers == []

    def test_get_execution_order(self):
        """Test getting solver execution order."""
        model = OpenPhModel()
        order = model.get_execution_order()
        assert isinstance(order, list)
        # With no plugins installed, should be empty
        assert order == []

    def test_get_execution_history_empty(self):
        """Test getting execution history when empty."""
        model = OpenPhModel()
        history = model.get_execution_history()
        assert isinstance(history, list)
        assert history == []

    def test_reset_solvers(self):
        """Test resetting solver state."""
        model = OpenPhModel()
        # Should not raise
        model.reset_solvers()
        # History should still be empty
        assert model.get_execution_history() == []

    def test_solver_info_not_found(self):
        """Test solver_info raises for non-existent solver."""
        model = OpenPhModel()
        with pytest.raises(ValueError, match="not found"):
            model.solver_info("nonexistent_solver")


class TestOpenPhModelAttributeMethods:
    """Test OpenPhModel attribute convenience methods."""

    def test_list_attributes(self):
        """Test listing available attributes."""
        model = OpenPhModel()
        attributes = model.list_attributes()
        assert isinstance(attributes, list)
        # With no plugins installed, should be empty
        assert attributes == []

    def test_reset_attributes(self):
        """Test resetting attribute state."""
        model = OpenPhModel()
        # Should not raise
        model.reset_attributes()

    def test_attribute_info_not_found(self):
        """Test attribute_info raises for non-existent attribute."""
        model = OpenPhModel()
        with pytest.raises(ValueError, match="not found"):
            model.attribute_info("nonexistent_attribute")

    def test_get_attributes_for_class(self):
        """Test getting attributes for a class."""
        model = OpenPhModel()
        attrs = model.get_attributes_for_class("PhxEnvelope")
        assert isinstance(attrs, list)
        # With no plugins installed, should be empty
        assert attrs == []


class TestOpenPhModelValidation:
    """Test OpenPhModel validation methods."""

    def test_validate_empty_model_has_errors(self):
        """Test that empty model fails validation."""
        model = OpenPhModel()
        errors = model.validate()
        assert isinstance(errors, list)
        assert len(errors) > 0
        # Should have errors for missing required data
        assert any("climate" in error.lower() for error in errors)
        assert any("envelope" in error.lower() for error in errors)
        assert any("rooms" in error.lower() for error in errors)

    def test_is_valid_returns_false_for_empty_model(self):
        """Test that empty model is not valid."""
        model = OpenPhModel()
        assert model.is_valid() is False

    def test_validate_returns_empty_list_when_valid(self):
        """Test that valid model returns empty error list."""
        # This test will need to be updated when we have actual data classes
        # For now, just test the structure
        model = OpenPhModel()
        errors = model.validate()
        assert isinstance(errors, list)


class TestOpenPhModelIntegration:
    """Integration tests for OpenPhModel."""

    def test_model_can_be_created_and_reset(self):
        """Test creating model and resetting state."""
        model = OpenPhModel()

        # Reset both managers
        model.reset_solvers()
        model.reset_attributes()

        # Should still work
        assert model.list_solvers() == []
        assert model.list_attributes() == []

    def test_model_managers_are_independent(self):
        """Test that solver and attribute managers work independently."""
        model = OpenPhModel()

        # Reset solvers shouldn't affect attributes
        model.reset_solvers()
        attrs = model.list_attributes()
        assert isinstance(attrs, list)

        # Reset attributes shouldn't affect solvers
        model.reset_attributes()
        solvers = model.list_solvers()
        assert isinstance(solvers, list)

    def test_multiple_models_independent(self):
        """Test that multiple model instances are independent."""
        model1 = OpenPhModel()
        model2 = OpenPhModel()

        # Should have separate managers
        assert model1.solvers is not model2.solvers
        assert model1.attributes is not model2.attributes

        # Resetting one shouldn't affect the other
        model1.reset_solvers()
        # This is a basic test - with real solvers we could verify more


class TestOpenPhModelDataAttributes:
    """Test OpenPhModel data attribute handling."""

    def test_can_set_climate_data(self):
        """Test setting climate data."""
        model = OpenPhModel()
        # For now, just test we can set to any value
        model.climate = "dummy_climate"
        assert model.climate == "dummy_climate"

    def test_can_set_envelope_data(self):
        """Test setting envelope data."""
        model = OpenPhModel()
        model.envelope = "dummy_envelope"
        assert model.envelope == "dummy_envelope"

    def test_can_set_all_data_attributes(self):
        """Test setting all data attributes."""
        model = OpenPhModel()

        model.climate = "climate"
        model.envelope = "envelope"
        model.hvac = "hvac"
        model.rooms = "rooms"
        model.areas = "areas"
        model.internal_gains = "gains"
        model.settings = "settings"

        assert model.climate == "climate"
        assert model.envelope == "envelope"
        assert model.hvac == "hvac"
        assert model.rooms == "rooms"
        assert model.areas == "areas"
        assert model.internal_gains == "gains"
        assert model.settings == "settings"


class TestOpenPhModelDocumentation:
    """Test that OpenPhModel is well documented."""

    def test_class_has_docstring(self):
        """Test that class has docstring."""
        assert OpenPhModel.__doc__ is not None
        assert len(OpenPhModel.__doc__) > 0

    def test_solve_method_has_docstring(self):
        """Test that solve method has docstring."""
        assert OpenPhModel.solve.__doc__ is not None
        assert "solver_name" in OpenPhModel.solve.__doc__

    def test_validate_method_has_docstring(self):
        """Test that validate method has docstring."""
        assert OpenPhModel.validate.__doc__ is not None

    def test_convenience_methods_have_docstrings(self):
        """Test that all public methods have docstrings."""
        model = OpenPhModel()
        public_methods = [
            method
            for method in dir(model)
            if not method.startswith("_") and callable(getattr(model, method))
        ]

        for method_name in public_methods:
            method = getattr(model, method_name)
            assert method.__doc__ is not None, f"Method {method_name} missing docstring"
