"""Tests for Attribute Manager.

This module tests the AttributeManager implementation including:
- Attribute discovery and instantiation
- Data storage and retrieval
- Validation and serialization
- Error handling
"""

import pytest
from typing import Any, Dict, List

from openph.attributes.manager import AttributeManager, AttributeValidationError
from openph.attributes.registry import AttributeInfo, AttributeRegistry


# ============================================================================
# Test Attribute Implementations
# ============================================================================


class CostAttribute:
    """Cost attribute for testing."""

    attribute_name = "cost"
    attribute_version = "1.0.0"
    extends_classes: List[str] = ["Room", "Building"]
    attribute_description = "Cost tracking"

    @staticmethod
    def get_default_values() -> Dict[str, Any]:
        return {"cost": 0.0, "currency": "USD"}

    @staticmethod
    def validate_attribute_data(data: Dict[str, Any]) -> bool:
        return "cost" in data and isinstance(data["cost"], (int, float))

    @staticmethod
    def serialize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        return {"cost": float(data["cost"]), "currency": data.get("currency", "USD")}

    @staticmethod
    def deserialize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        return data


class CarbonAttribute:
    """Carbon attribute for testing."""

    attribute_name = "carbon"
    attribute_version = "1.0.0"
    extends_classes: List[str] = ["Room", "Component"]
    attribute_description = "Carbon tracking"

    @staticmethod
    def get_default_values() -> Dict[str, Any]:
        return {"embodied": 0.0, "operational": 0.0}

    @staticmethod
    def validate_attribute_data(data: Dict[str, Any]) -> bool:
        return "embodied" in data and "operational" in data

    @staticmethod
    def serialize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "embodied_carbon": data["embodied"],
            "operational_carbon": data["operational"],
        }

    @staticmethod
    def deserialize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "embodied": data["embodied_carbon"],
            "operational": data["operational_carbon"],
        }


class InvalidDataAttribute:
    """Attribute with strict validation for testing."""

    attribute_name = "strict"
    attribute_version = "1.0.0"
    extends_classes: List[str] = ["Room"]

    @staticmethod
    def get_default_values() -> Dict[str, Any]:
        return {"value": 0}

    @staticmethod
    def validate_attribute_data(data: Dict[str, Any]) -> bool:
        # Only accepts positive values
        return "value" in data and isinstance(data["value"], int) and data["value"] > 0

    @staticmethod
    def serialize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        return data

    @staticmethod
    def deserialize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        return data


# ============================================================================
# AttributeManager Basic Tests
# ============================================================================


class TestAttributeManagerBasics:
    """Test basic AttributeManager functionality."""

    def test_manager_initialization_default_registry(self):
        """Test manager creates its own registry by default."""
        manager = AttributeManager()

        assert manager.registry is not None
        assert isinstance(manager.registry, AttributeRegistry)
        assert manager._attribute_instances == {}
        assert manager._instance_data == {}

    def test_manager_initialization_with_registry(self):
        """Test manager can use provided registry."""
        registry = AttributeRegistry()
        manager = AttributeManager(registry=registry)

        assert manager.registry is registry

    def test_discover_attributes_clears_state(self):
        """Test that discovery clears instances and data."""
        manager = AttributeManager()

        # Add some fake state
        manager._attribute_instances["fake"] = None  # type: ignore
        manager._instance_data["Room"] = {"inst1": {"cost": {}}}

        # Discover (will find nothing in test environment)
        manager.discover_attributes(group="openph.test.nonexistent")

        # State should be cleared
        assert manager._attribute_instances == {}
        assert manager._instance_data == {}


# ============================================================================
# Attribute Instantiation Tests
# ============================================================================


class TestAttributeInstantiation:
    """Test attribute instantiation and caching."""

    def test_get_attribute_instance_creates_instance(self):
        """Test that getting attribute creates an instance."""
        manager = AttributeManager()

        # Manually register attribute
        info = AttributeInfo(
            name=CostAttribute.attribute_name,
            attribute_class=CostAttribute,
            extends_classes=set(CostAttribute.extends_classes),
        )
        manager.registry._attributes[info.name] = info
        manager.registry._discovered = True

        # Get instance
        instance = manager.get_attribute_instance("cost")

        assert instance is not None
        assert isinstance(instance, CostAttribute)

    def test_get_attribute_instance_caches_instances(self):
        """Test that instances are cached."""
        manager = AttributeManager()

        # Register attribute
        info = AttributeInfo(
            name=CostAttribute.attribute_name,
            attribute_class=CostAttribute,
            extends_classes=set(CostAttribute.extends_classes),
        )
        manager.registry._attributes[info.name] = info
        manager.registry._discovered = True

        # Get instance twice
        instance1 = manager.get_attribute_instance("cost")
        instance2 = manager.get_attribute_instance("cost")

        # Should be the same object
        assert instance1 is instance2

    def test_get_attribute_instance_nonexistent(self):
        """Test getting non-existent attribute raises error."""
        manager = AttributeManager()
        manager.registry._discovered = True

        with pytest.raises(KeyError, match="not found"):
            manager.get_attribute_instance("nonexistent")


# ============================================================================
# Data Storage Tests
# ============================================================================


class TestDataStorage:
    """Test attribute data storage and retrieval."""

    def test_set_and_get_attribute_data(self):
        """Test basic set and get operations."""
        manager = AttributeManager()

        # Register attribute
        info = AttributeInfo(
            name=CostAttribute.attribute_name,
            attribute_class=CostAttribute,
            extends_classes=set(CostAttribute.extends_classes),
        )
        manager.registry._attributes[info.name] = info
        manager.registry._discovered = True

        # Set data
        data = {"cost": 1000.0, "currency": "USD"}
        manager.set_attribute_data("Room", "room1", "cost", data)

        # Get data
        retrieved = manager.get_attribute_data("Room", "room1", "cost")
        assert retrieved == data

    def test_set_attribute_data_validates(self):
        """Test that set validates data by default."""
        manager = AttributeManager()

        # Register attribute
        info = AttributeInfo(
            name=CostAttribute.attribute_name,
            attribute_class=CostAttribute,
            extends_classes=set(CostAttribute.extends_classes),
        )
        manager.registry._attributes[info.name] = info
        manager.registry._discovered = True

        # Invalid data (missing 'cost' key)
        invalid_data = {"currency": "USD"}

        with pytest.raises(AttributeValidationError):
            manager.set_attribute_data("Room", "room1", "cost", invalid_data)

    def test_set_attribute_data_skip_validation(self):
        """Test that validation can be skipped."""
        manager = AttributeManager()

        # Register attribute
        info = AttributeInfo(
            name=CostAttribute.attribute_name,
            attribute_class=CostAttribute,
            extends_classes=set(CostAttribute.extends_classes),
        )
        manager.registry._attributes[info.name] = info
        manager.registry._discovered = True

        # Invalid data but skip validation
        invalid_data = {"currency": "USD"}
        manager.set_attribute_data(
            "Room", "room1", "cost", invalid_data, validate=False
        )

        # Should be stored
        retrieved = manager.get_attribute_data("Room", "room1", "cost")
        assert retrieved == invalid_data

    def test_set_attribute_wrong_class(self):
        """Test that setting attribute for wrong class raises error."""
        manager = AttributeManager()

        # Register cost attribute (only extends Room and Building)
        info = AttributeInfo(
            name=CostAttribute.attribute_name,
            attribute_class=CostAttribute,
            extends_classes=set(CostAttribute.extends_classes),
        )
        manager.registry._attributes[info.name] = info
        manager.registry._discovered = True

        # Try to set on Component (not extended by cost)
        data = {"cost": 100.0}
        with pytest.raises(ValueError, match="does not extend class"):
            manager.set_attribute_data("Component", "comp1", "cost", data)

    def test_get_attribute_data_with_defaults(self):
        """Test getting data returns defaults if no data exists."""
        manager = AttributeManager()

        # Register attribute
        info = AttributeInfo(
            name=CostAttribute.attribute_name,
            attribute_class=CostAttribute,
            extends_classes=set(CostAttribute.extends_classes),
        )
        manager.registry._attributes[info.name] = info
        manager.registry._discovered = True

        # Get data (no data set, should return defaults)
        data = manager.get_attribute_data("Room", "room1", "cost", use_defaults=True)

        assert data == {"cost": 0.0, "currency": "USD"}

    def test_get_attribute_data_no_defaults_raises(self):
        """Test getting data without defaults raises error if no data."""
        manager = AttributeManager()

        # Register attribute
        info = AttributeInfo(
            name=CostAttribute.attribute_name,
            attribute_class=CostAttribute,
            extends_classes=set(CostAttribute.extends_classes),
        )
        manager.registry._attributes[info.name] = info
        manager.registry._discovered = True

        # Get data without defaults
        with pytest.raises(KeyError, match="No data found"):
            manager.get_attribute_data("Room", "room1", "cost", use_defaults=False)

    def test_has_attribute_data(self):
        """Test checking if attribute data exists."""
        manager = AttributeManager()

        # Register attribute
        info = AttributeInfo(
            name=CostAttribute.attribute_name,
            attribute_class=CostAttribute,
            extends_classes=set(CostAttribute.extends_classes),
        )
        manager.registry._attributes[info.name] = info
        manager.registry._discovered = True

        # No data initially
        assert manager.has_attribute_data("Room", "room1", "cost") is False

        # Set data
        manager.set_attribute_data("Room", "room1", "cost", {"cost": 100.0})

        # Should have data now
        assert manager.has_attribute_data("Room", "room1", "cost") is True

    def test_remove_attribute_data(self):
        """Test removing attribute data."""
        manager = AttributeManager()

        # Register attribute
        info = AttributeInfo(
            name=CostAttribute.attribute_name,
            attribute_class=CostAttribute,
            extends_classes=set(CostAttribute.extends_classes),
        )
        manager.registry._attributes[info.name] = info
        manager.registry._discovered = True

        # Set and verify data
        manager.set_attribute_data("Room", "room1", "cost", {"cost": 100.0})
        assert manager.has_attribute_data("Room", "room1", "cost") is True

        # Remove data
        manager.remove_attribute_data("Room", "room1", "cost")

        # Should be gone
        assert manager.has_attribute_data("Room", "room1", "cost") is False

    def test_remove_nonexistent_data_raises(self):
        """Test removing nonexistent data raises error."""
        manager = AttributeManager()
        manager.registry._discovered = True

        with pytest.raises(KeyError, match="No data found"):
            manager.remove_attribute_data("Room", "room1", "cost")


# ============================================================================
# Multi-Attribute Tests
# ============================================================================


class TestMultipleAttributes:
    """Test managing multiple attributes."""

    def test_get_all_instance_attributes(self):
        """Test getting all attributes for an instance."""
        manager = AttributeManager()

        # Register attributes
        for attr_class in [CostAttribute, CarbonAttribute]:
            info = AttributeInfo(
                name=attr_class.attribute_name,
                attribute_class=attr_class,
                extends_classes=set(attr_class.extends_classes),
            )
            manager.registry._attributes[info.name] = info
            manager.registry._update_class_index(info)

        manager.registry._discovered = True

        # Set multiple attributes
        manager.set_attribute_data("Room", "room1", "cost", {"cost": 1000.0})
        manager.set_attribute_data(
            "Room", "room1", "carbon", {"embodied": 50.0, "operational": 100.0}
        )

        # Get all
        all_attrs = manager.get_all_instance_attributes("Room", "room1")

        assert len(all_attrs) == 2
        assert "cost" in all_attrs
        assert "carbon" in all_attrs
        assert all_attrs["cost"]["cost"] == 1000.0

    def test_get_all_instance_attributes_empty(self):
        """Test getting all attributes returns empty dict if none."""
        manager = AttributeManager()
        manager.registry._discovered = True

        all_attrs = manager.get_all_instance_attributes("Room", "room1")

        assert all_attrs == {}

    def test_get_instances_with_attribute(self):
        """Test finding all instances with a specific attribute."""
        manager = AttributeManager()

        # Register attribute
        info = AttributeInfo(
            name=CostAttribute.attribute_name,
            attribute_class=CostAttribute,
            extends_classes=set(CostAttribute.extends_classes),
        )
        manager.registry._attributes[info.name] = info
        manager.registry._discovered = True

        # Set cost on multiple rooms
        manager.set_attribute_data("Room", "room1", "cost", {"cost": 100.0})
        manager.set_attribute_data("Room", "room2", "cost", {"cost": 200.0})
        manager.set_attribute_data("Room", "room3", "cost", {"cost": 300.0})

        # Find instances
        instances = manager.get_instances_with_attribute("Room", "cost")

        assert len(instances) == 3
        assert set(instances) == {"room1", "room2", "room3"}

    def test_get_instances_with_attribute_none(self):
        """Test finding instances returns empty if none."""
        manager = AttributeManager()
        manager.registry._discovered = True

        instances = manager.get_instances_with_attribute("Room", "cost")

        assert instances == []


# ============================================================================
# Serialization Tests
# ============================================================================


class TestSerialization:
    """Test attribute serialization and deserialization."""

    def test_serialize_instance_attributes(self):
        """Test serializing all attributes for an instance."""
        manager = AttributeManager()

        # Register carbon attribute (has custom serialization)
        info = AttributeInfo(
            name=CarbonAttribute.attribute_name,
            attribute_class=CarbonAttribute,
            extends_classes=set(CarbonAttribute.extends_classes),
        )
        manager.registry._attributes[info.name] = info
        manager.registry._discovered = True

        # Set data
        manager.set_attribute_data(
            "Room", "room1", "carbon", {"embodied": 50.0, "operational": 100.0}
        )

        # Serialize
        serialized = manager.serialize_instance_attributes("Room", "room1")

        assert "carbon" in serialized
        assert serialized["carbon"]["embodied_carbon"] == 50.0
        assert serialized["carbon"]["operational_carbon"] == 100.0

    def test_deserialize_instance_attributes(self):
        """Test deserializing attributes for an instance."""
        manager = AttributeManager()

        # Register carbon attribute
        info = AttributeInfo(
            name=CarbonAttribute.attribute_name,
            attribute_class=CarbonAttribute,
            extends_classes=set(CarbonAttribute.extends_classes),
        )
        manager.registry._attributes[info.name] = info
        manager.registry._discovered = True

        # Serialized data (with different key names)
        serialized = {"carbon": {"embodied_carbon": 75.0, "operational_carbon": 125.0}}

        # Deserialize
        manager.deserialize_instance_attributes("Room", "room1", serialized)

        # Get data
        data = manager.get_attribute_data("Room", "room1", "carbon")

        assert data["embodied"] == 75.0
        assert data["operational"] == 125.0

    def test_serialize_empty_returns_empty(self):
        """Test serializing instance with no attributes returns empty dict."""
        manager = AttributeManager()
        manager.registry._discovered = True

        serialized = manager.serialize_instance_attributes("Room", "room1")

        assert serialized == {}


# ============================================================================
# Utility Methods Tests
# ============================================================================


class TestUtilityMethods:
    """Test manager utility methods."""

    def test_list_available_attributes(self):
        """Test listing available attributes."""
        manager = AttributeManager()

        # Register attributes
        for attr_class in [CostAttribute, CarbonAttribute]:
            info = AttributeInfo(
                name=attr_class.attribute_name,
                attribute_class=attr_class,
                extends_classes=set(attr_class.extends_classes),
            )
            manager.registry._attributes[info.name] = info

        manager.registry._discovered = True

        attributes = manager.list_available_attributes()
        assert set(attributes) == {"cost", "carbon"}

    def test_get_attributes_for_class(self):
        """Test getting attributes for a specific class."""
        manager = AttributeManager()

        # Register attributes
        for attr_class in [CostAttribute, CarbonAttribute]:
            info = AttributeInfo(
                name=attr_class.attribute_name,
                attribute_class=attr_class,
                extends_classes=set(attr_class.extends_classes),
            )
            manager.registry._attributes[info.name] = info
            manager.registry._update_class_index(info)

        manager.registry._discovered = True

        # Get for Room (both extend Room)
        room_attrs = manager.get_attributes_for_class("Room")
        assert set(room_attrs) == {"cost", "carbon"}

        # Get for Component (only carbon extends)
        comp_attrs = manager.get_attributes_for_class("Component")
        assert comp_attrs == ["carbon"]

        # Get for Building (only cost extends)
        build_attrs = manager.get_attributes_for_class("Building")
        assert build_attrs == ["cost"]

    def test_clear_all_instance_data(self):
        """Test clearing all data for an instance."""
        manager = AttributeManager()

        # Register attributes
        for attr_class in [CostAttribute, CarbonAttribute]:
            info = AttributeInfo(
                name=attr_class.attribute_name,
                attribute_class=attr_class,
                extends_classes=set(attr_class.extends_classes),
            )
            manager.registry._attributes[info.name] = info

        manager.registry._discovered = True

        # Set multiple attributes
        manager.set_attribute_data("Room", "room1", "cost", {"cost": 100.0})
        manager.set_attribute_data(
            "Room", "room1", "carbon", {"embodied": 50.0, "operational": 100.0}
        )

        # Verify data exists
        assert len(manager.get_all_instance_attributes("Room", "room1")) == 2

        # Clear all
        manager.clear_all_instance_data("Room", "room1")

        # Should be empty
        assert manager.get_all_instance_attributes("Room", "room1") == {}

    def test_clear_nonexistent_instance_succeeds(self):
        """Test clearing nonexistent instance doesn't raise error."""
        manager = AttributeManager()
        manager.registry._discovered = True

        # Should not raise
        manager.clear_all_instance_data("Room", "room1")

    def test_reset(self):
        """Test resetting manager state."""
        manager = AttributeManager()

        # Add state
        manager._attribute_instances["fake"] = None  # type: ignore
        manager._instance_data["Room"] = {"room1": {"cost": {}}}

        # Reset
        manager.reset()

        assert manager._attribute_instances == {}
        assert manager._instance_data == {}
