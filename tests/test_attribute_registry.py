"""Tests for Attribute Registry.

This module tests the AttributeRegistry implementation including:
- Entry point discovery
- Class extension tracking
- Attribute validation
- Error handling
"""

import pytest
from typing import Any, Dict, List

from openph.attributes.registry import AttributeInfo, AttributeRegistry


# ============================================================================
# Test Attribute Implementations
# ============================================================================


class MinimalAttribute:
    """Minimal attribute implementation for testing."""

    attribute_name = "minimal"
    attribute_version = "1.0.0"
    extends_classes: List[str] = []

    @staticmethod
    def get_default_values() -> Dict[str, Any]:
        """Minimal default values."""
        return {}

    @staticmethod
    def validate_attribute_data(data: Dict[str, Any]) -> bool:
        """Minimal validation."""
        return True

    @staticmethod
    def serialize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Minimal serialization."""
        return data

    @staticmethod
    def deserialize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Minimal deserialization."""
        return data


class CostAttribute:
    """Cost attribute extending Room and Building."""

    attribute_name = "cost"
    attribute_version = "1.0.0"
    extends_classes: List[str] = ["Room", "Building"]
    attribute_description = "Cost tracking for rooms and buildings"

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
    """Carbon attribute extending multiple classes."""

    attribute_name = "carbon"
    attribute_version = "2.0.0"
    extends_classes: List[str] = ["Room", "Building", "Component"]
    attribute_description = "Carbon emissions tracking"

    @staticmethod
    def get_default_values() -> Dict[str, Any]:
        return {"embodied_carbon": 0.0, "operational_carbon": 0.0}

    @staticmethod
    def validate_attribute_data(data: Dict[str, Any]) -> bool:
        return "embodied_carbon" in data and "operational_carbon" in data

    @staticmethod
    def serialize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        return data

    @staticmethod
    def deserialize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        return data


class RoomOnlyAttribute:
    """Attribute that only extends Room."""

    attribute_name = "room_specific"
    attribute_version = "1.0.0"
    extends_classes: List[str] = ["Room"]
    attribute_description = "Room-specific attribute"

    @staticmethod
    def get_default_values() -> Dict[str, Any]:
        return {"room_data": None}

    @staticmethod
    def validate_attribute_data(data: Dict[str, Any]) -> bool:
        return True

    @staticmethod
    def serialize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        return data

    @staticmethod
    def deserialize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        return data


class InvalidAttribute:
    """Attribute missing required protocol attributes."""

    attribute_name = "invalid"
    # Missing other required attributes


# ============================================================================
# AttributeInfo Tests
# ============================================================================


class TestAttributeInfo:
    """Test AttributeInfo dataclass functionality."""

    def test_attribute_info_creation(self):
        """Test basic AttributeInfo creation."""
        info = AttributeInfo(
            name="test",
            attribute_class=MinimalAttribute,
            extends_classes={"Room", "Building"},
            description="Test attribute",
            version="1.0.0",
            entry_point_name="test_ep",
        )

        assert info.name == "test"
        assert info.attribute_class == MinimalAttribute
        assert info.extends_classes == {"Room", "Building"}
        assert info.description == "Test attribute"
        assert info.version == "1.0.0"
        assert info.entry_point_name == "test_ep"

    def test_attribute_info_default_values(self):
        """Test AttributeInfo default values."""
        info = AttributeInfo(
            name="test",
            attribute_class=MinimalAttribute,
        )

        assert info.extends_classes == set()
        assert info.description == ""
        assert info.version == "0.0.0"
        assert info.entry_point_name == ""

    def test_attribute_info_extends_classes_conversion(self):
        """Test that extends_classes is converted to set."""
        # Pass list instead of set
        info = AttributeInfo(
            name="test",
            attribute_class=MinimalAttribute,
            extends_classes=["Room", "Building"],  # type: ignore
        )

        assert isinstance(info.extends_classes, set)
        assert info.extends_classes == {"Room", "Building"}


# ============================================================================
# AttributeRegistry Basic Tests
# ============================================================================


class TestAttributeRegistryBasics:
    """Test basic AttributeRegistry functionality."""

    def test_registry_initialization(self):
        """Test registry initializes with empty state."""
        registry = AttributeRegistry()

        assert registry._attributes == {}
        assert registry._class_index == {}
        assert registry._discovered is False

    def test_discover_attributes_without_entry_points(self):
        """Test discovery when no entry points exist."""
        registry = AttributeRegistry()

        # Use a non-existent group to ensure no attributes found
        registry.discover_attributes(group="openph.test.nonexistent")

        assert registry._discovered is True
        assert len(registry._attributes) == 0
        assert len(registry._class_index) == 0

    def test_get_attribute_class_before_discovery(self):
        """Test that getting attribute before discovery raises error."""
        registry = AttributeRegistry()

        with pytest.raises(RuntimeError, match="before discovering attributes"):
            registry.get_attribute_class("test")

    def test_get_attributes_for_class_before_discovery(self):
        """Test that getting attributes for class before discovery raises error."""
        registry = AttributeRegistry()

        with pytest.raises(RuntimeError, match="before discovering attributes"):
            registry.get_attributes_for_class("Room")

    def test_list_attributes_before_discovery(self):
        """Test that listing attributes before discovery raises error."""
        registry = AttributeRegistry()

        with pytest.raises(RuntimeError, match="before discovering attributes"):
            registry.list_attributes()


# ============================================================================
# Manual Attribute Registration Tests (for testing without entry points)
# ============================================================================


class TestAttributeRegistryManual:
    """Test registry functionality by manually adding attributes."""

    def test_manual_registration_single_attribute(self):
        """Test manually registering a single attribute."""
        registry = AttributeRegistry()

        # Manually add attribute
        attribute_info = AttributeInfo(
            name=MinimalAttribute.attribute_name,
            attribute_class=MinimalAttribute,
            extends_classes=set(MinimalAttribute.extends_classes),
            version=MinimalAttribute.attribute_version,
        )
        registry._attributes[attribute_info.name] = attribute_info
        registry._discovered = True

        # Verify
        assert len(registry._attributes) == 1
        assert registry.get_attribute_class("minimal") == MinimalAttribute
        assert len(registry.list_attributes()) == 1

    def test_manual_registration_multiple_attributes(self):
        """Test multiple attributes with various class extensions."""
        registry = AttributeRegistry()

        # Manually add attributes
        attributes = [CostAttribute, CarbonAttribute, RoomOnlyAttribute]
        for attr_class in attributes:
            info = AttributeInfo(
                name=attr_class.attribute_name,
                attribute_class=attr_class,
                extends_classes=set(attr_class.extends_classes),
                version=attr_class.attribute_version,
                description=getattr(attr_class, "attribute_description", ""),
            )
            registry._attributes[info.name] = info
            registry._update_class_index(info)

        registry._discovered = True

        # Verify all attributes registered
        assert len(registry._attributes) == 3
        assert set(registry._attributes.keys()) == {"cost", "carbon", "room_specific"}

    def test_get_attributes_for_class_single_match(self):
        """Test getting attributes for a class with one match."""
        registry = AttributeRegistry()

        # Add room-only attribute
        info = AttributeInfo(
            name=RoomOnlyAttribute.attribute_name,
            attribute_class=RoomOnlyAttribute,
            extends_classes=set(RoomOnlyAttribute.extends_classes),
        )
        registry._attributes[info.name] = info
        registry._update_class_index(info)
        registry._discovered = True

        # Get attributes for Room
        room_attrs = registry.get_attributes_for_class("Room")

        assert len(room_attrs) == 1
        assert room_attrs[0].name == "room_specific"

    def test_get_attributes_for_class_multiple_matches(self):
        """Test getting attributes for a class with multiple matches."""
        registry = AttributeRegistry()

        # Add multiple attributes extending Room
        attributes = [CostAttribute, CarbonAttribute, RoomOnlyAttribute]
        for attr_class in attributes:
            info = AttributeInfo(
                name=attr_class.attribute_name,
                attribute_class=attr_class,
                extends_classes=set(attr_class.extends_classes),
            )
            registry._attributes[info.name] = info
            registry._update_class_index(info)

        registry._discovered = True

        # Get attributes for Room - should have all 3
        room_attrs = registry.get_attributes_for_class("Room")

        assert len(room_attrs) == 3
        attr_names = {attr.name for attr in room_attrs}
        assert attr_names == {"cost", "carbon", "room_specific"}

    def test_get_attributes_for_class_no_matches(self):
        """Test getting attributes for a class with no matches."""
        registry = AttributeRegistry()

        # Add attribute that doesn't extend "Building"
        info = AttributeInfo(
            name=RoomOnlyAttribute.attribute_name,
            attribute_class=RoomOnlyAttribute,
            extends_classes=set(RoomOnlyAttribute.extends_classes),
        )
        registry._attributes[info.name] = info
        registry._update_class_index(info)
        registry._discovered = True

        # Get attributes for Building - should be empty
        building_attrs = registry.get_attributes_for_class("Building")

        assert len(building_attrs) == 0
        assert building_attrs == []

    def test_class_index_updated_correctly(self):
        """Test that class index is maintained correctly."""
        registry = AttributeRegistry()

        # Add cost attribute (extends Room and Building)
        info = AttributeInfo(
            name=CostAttribute.attribute_name,
            attribute_class=CostAttribute,
            extends_classes=set(CostAttribute.extends_classes),
        )
        registry._attributes[info.name] = info
        registry._update_class_index(info)
        registry._discovered = True

        # Check class index
        assert "Room" in registry._class_index
        assert "Building" in registry._class_index
        assert "cost" in registry._class_index["Room"]
        assert "cost" in registry._class_index["Building"]

    def test_get_attribute_info(self):
        """Test getting detailed attribute info."""
        registry = AttributeRegistry()

        attribute_info = AttributeInfo(
            name=CostAttribute.attribute_name,
            attribute_class=CostAttribute,
            extends_classes=set(CostAttribute.extends_classes),
            description=CostAttribute.attribute_description,
            version=CostAttribute.attribute_version,
            entry_point_name="test_cost_ep",
        )
        registry._attributes[attribute_info.name] = attribute_info
        registry._discovered = True

        # Get info
        info = registry.get_attribute_info("cost")

        assert info.name == "cost"
        assert info.attribute_class == CostAttribute
        assert info.extends_classes == {"Room", "Building"}
        assert info.description == "Cost tracking for rooms and buildings"
        assert info.version == "1.0.0"
        assert info.entry_point_name == "test_cost_ep"

    def test_get_attribute_info_nonexistent(self):
        """Test getting info for non-existent attribute."""
        registry = AttributeRegistry()
        registry._discovered = True

        with pytest.raises(KeyError, match="not found"):
            registry.get_attribute_info("nonexistent")

    def test_list_attributes(self):
        """Test listing all registered attributes."""
        registry = AttributeRegistry()

        # Add multiple attributes
        for attr_class in [CostAttribute, CarbonAttribute]:
            info = AttributeInfo(
                name=attr_class.attribute_name,
                attribute_class=attr_class,
                extends_classes=set(attr_class.extends_classes),
            )
            registry._attributes[info.name] = info

        registry._discovered = True

        # List attributes
        attributes = registry.list_attributes()

        assert len(attributes) == 2
        attr_names = {a.name for a in attributes}
        assert attr_names == {"cost", "carbon"}

    def test_list_extended_classes(self):
        """Test listing all classes that have attributes."""
        registry = AttributeRegistry()

        # Add attributes extending different classes
        for attr_class in [CostAttribute, CarbonAttribute, RoomOnlyAttribute]:
            info = AttributeInfo(
                name=attr_class.attribute_name,
                attribute_class=attr_class,
                extends_classes=set(attr_class.extends_classes),
            )
            registry._attributes[info.name] = info
            registry._update_class_index(info)

        registry._discovered = True

        # List extended classes
        extended_classes = registry.list_extended_classes()

        assert set(extended_classes) == {"Room", "Building", "Component"}

    def test_has_attributes_for_class(self):
        """Test checking if a class has attributes."""
        registry = AttributeRegistry()

        # Add room-only attribute
        info = AttributeInfo(
            name=RoomOnlyAttribute.attribute_name,
            attribute_class=RoomOnlyAttribute,
            extends_classes=set(RoomOnlyAttribute.extends_classes),
        )
        registry._attributes[info.name] = info
        registry._update_class_index(info)
        registry._discovered = True

        # Check various classes
        assert registry.has_attributes_for_class("Room") is True
        assert registry.has_attributes_for_class("Building") is False
        assert registry.has_attributes_for_class("NonExistent") is False

    def test_has_attributes_for_class_before_discovery(self):
        """Test that checking for attributes before discovery raises error."""
        registry = AttributeRegistry()

        with pytest.raises(RuntimeError, match="before discovering attributes"):
            registry.has_attributes_for_class("Room")

    def test_list_extended_classes_before_discovery(self):
        """Test that listing extended classes before discovery raises error."""
        registry = AttributeRegistry()

        with pytest.raises(RuntimeError, match="before discovering attributes"):
            registry.list_extended_classes()


# ============================================================================
# Protocol Validation Tests
# ============================================================================


class TestProtocolValidation:
    """Test attribute protocol validation."""

    def test_validate_attribute_protocol_valid(self):
        """Test validation passes for valid attribute."""
        registry = AttributeRegistry()

        # Should not raise
        registry._validate_attribute_protocol(MinimalAttribute)

    def test_validate_attribute_protocol_invalid(self):
        """Test validation fails for invalid attribute."""
        registry = AttributeRegistry()

        with pytest.raises(
            TypeError, match="does not implement OpenPhAttribute protocol"
        ):
            registry._validate_attribute_protocol(InvalidAttribute)

    def test_validate_attribute_protocol_missing_multiple_attrs(self):
        """Test validation reports all missing attributes."""
        registry = AttributeRegistry()

        class PartialAttribute:
            attribute_name = "partial"
            # Missing all other attributes

        with pytest.raises(TypeError) as exc_info:
            registry._validate_attribute_protocol(PartialAttribute)

        error_msg = str(exc_info.value)
        assert "attribute_version" in error_msg
        assert "extends_classes" in error_msg
        assert "get_default_values" in error_msg
        assert "validate_attribute_data" in error_msg
        assert "serialize_data" in error_msg
        assert "deserialize_data" in error_msg
