"""Tests for OpenPhAttribute protocol."""

from dataclasses import dataclass
from typing import Any, Dict

from openph.attributes.base import OpenPhAttribute


class TestOpenPhAttributeProtocol:
    """Test OpenPhAttribute protocol compliance."""

    def test_minimal_attribute_implementation(self):
        """Test that a minimal attribute implementation satisfies the protocol."""

        # Create a minimal attribute implementation
        @dataclass
        class MinimalAttribute:
            model: Any  # Mock model for testing

            @property
            def attribute_name(self) -> str:
                return "test_attribute"

            @property
            def attribute_version(self) -> str:
                return "1.0.0"

            @property
            def extends_classes(self) -> list[str]:
                return ["OpenPhModel"]

            @property
            def attribute_description(self) -> str:
                return ""

            def get_default_values(self) -> Dict[str, Any]:
                return {
                    "field1": "default_value",
                    "field2": 0,
                }

        # Verify it works
        attribute = MinimalAttribute(model=None)
        assert attribute.attribute_name == "test_attribute"
        assert attribute.attribute_version == "1.0.0"
        assert attribute.extends_classes == ["OpenPhModel"]
        assert attribute.attribute_description == ""  # Test default values
        defaults = attribute.get_default_values()
        assert defaults == {"field1": "default_value", "field2": 0}

    def test_attribute_with_extended_properties(self):
        """Test attribute with all properties defined."""

        @dataclass
        class ExtendedAttribute:
            model: Any

            @property
            def attribute_name(self) -> str:
                return "cost_data"

            @property
            def attribute_version(self) -> str:
                return "2.1.0"

            @property
            def extends_classes(self) -> list[str]:
                return ["OpenPhModel", "OpenPhRoom", "OpenPhConstruction"]

            @property
            def attribute_description(self) -> str:
                return "Cost tracking for materials, labor, and lifecycle analysis"

            def get_default_values(self) -> Dict[str, Any]:
                return {
                    "material_cost_per_m2": 0.0,
                    "labor_cost_per_m2": 0.0,
                    "cost_currency": "USD",
                }

        attribute = ExtendedAttribute(model=None)
        assert attribute.attribute_name == "cost_data"
        assert attribute.attribute_version == "2.1.0"
        assert attribute.extends_classes == [
            "OpenPhModel",
            "OpenPhRoom",
            "OpenPhConstruction",
        ]
        assert (
            attribute.attribute_description
            == "Cost tracking for materials, labor, and lifecycle analysis"
        )

        defaults = attribute.get_default_values()
        assert "material_cost_per_m2" in defaults
        assert "labor_cost_per_m2" in defaults
        assert "cost_currency" in defaults

    def test_validate_attribute_data_default_implementation(self):
        """Test the default validate_attribute_data implementation."""

        @dataclass
        class TestAttribute:
            model: Any

            @property
            def attribute_name(self) -> str:
                return "test"

            @property
            def attribute_version(self) -> str:
                return "1.0.0"

            def get_default_values(self) -> Dict[str, Any]:
                return {"value": 0}

            def validate_attribute_data(self, data: Dict[str, Any]) -> list[str]:
                # Use protocol default (returns empty list)
                return []

        attribute = TestAttribute(model=None)

        # Should accept any data with default implementation
        errors = attribute.validate_attribute_data({"value": 100})
        assert len(errors) == 0

        errors = attribute.validate_attribute_data({"invalid_field": "test"})
        assert len(errors) == 0

    def test_validate_attribute_data_custom_implementation(self):
        """Test custom validation logic."""

        @dataclass
        class ValidatingAttribute:
            model: Any

            @property
            def attribute_name(self) -> str:
                return "validated_attribute"

            @property
            def attribute_version(self) -> str:
                return "1.0.0"

            def get_default_values(self) -> Dict[str, Any]:
                return {
                    "cost": 0.0,
                    "currency": "USD",
                }

            def validate_attribute_data(self, data: Dict[str, Any]) -> list[str]:
                errors = []

                # Validate cost is non-negative
                if "cost" in data and data["cost"] < 0:
                    errors.append("cost cannot be negative")

                # Validate currency is valid
                valid_currencies = ["USD", "EUR", "GBP"]
                if "currency" in data and data["currency"] not in valid_currencies:
                    errors.append(f"currency must be one of: {valid_currencies}")

                return errors

        attribute = ValidatingAttribute(model=None)

        # Valid data
        errors = attribute.validate_attribute_data({"cost": 100.0, "currency": "EUR"})
        assert len(errors) == 0

        # Invalid cost
        errors = attribute.validate_attribute_data({"cost": -10.0})
        assert len(errors) == 1
        assert "cost cannot be negative" in errors

        # Invalid currency
        errors = attribute.validate_attribute_data({"currency": "JPY"})
        assert len(errors) == 1
        assert "currency must be one of:" in errors[0]

        # Multiple errors
        errors = attribute.validate_attribute_data({"cost": -5.0, "currency": "CAD"})
        assert len(errors) == 2

    def test_serialize_deserialize_default_implementation(self):
        """Test default serialize/deserialize implementation."""

        @dataclass
        class SimpleAttribute:
            model: Any

            @property
            def attribute_name(self) -> str:
                return "simple"

            @property
            def attribute_version(self) -> str:
                return "1.0.0"

            def get_default_values(self) -> Dict[str, Any]:
                return {"value": 0}

            def serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
                return data  # Default passthrough

            def deserialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
                return data  # Default passthrough

        attribute = SimpleAttribute(model=None)

        # Default implementation returns data unchanged
        test_data = {"value": 42, "extra": "data"}
        serialized = attribute.serialize_data(test_data)
        assert serialized == test_data

        deserialized = attribute.deserialize_data(serialized)
        assert deserialized == test_data

    def test_serialize_deserialize_custom_implementation(self):
        """Test custom serialize/deserialize logic."""

        @dataclass
        class CustomSerializationAttribute:
            model: Any

            @property
            def attribute_name(self) -> str:
                return "custom_serialization"

            @property
            def attribute_version(self) -> str:
                return "1.0.0"

            def get_default_values(self) -> Dict[str, Any]:
                return {
                    "cost": 0.0,
                    "quantity": 0,
                }

            def serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
                """Convert all numbers to strings for JSON compatibility."""
                return {
                    k: str(v) if isinstance(v, (int, float)) else v
                    for k, v in data.items()
                }

            def deserialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
                """Convert string numbers back to appropriate types."""
                result = {}
                for k, v in data.items():
                    if k == "cost":
                        result[k] = float(v)
                    elif k == "quantity":
                        result[k] = int(v)
                    else:
                        result[k] = v
                return result

        attribute = CustomSerializationAttribute(model=None)

        # Test serialization
        original_data = {"cost": 123.45, "quantity": 10, "note": "test"}
        serialized = attribute.serialize_data(original_data)
        assert serialized == {"cost": "123.45", "quantity": "10", "note": "test"}

        # Test deserialization
        deserialized = attribute.deserialize_data(serialized)
        assert deserialized == original_data
        assert isinstance(deserialized["cost"], float)
        assert isinstance(deserialized["quantity"], int)
        assert isinstance(deserialized["note"], str)


class TestProtocolTypeChecking:
    """Test that the protocol works with type checking."""

    def test_protocol_as_type_hint(self):
        """Test that protocol can be used as a type hint."""

        @dataclass
        class ConcreteAttribute:
            model: Any

            @property
            def attribute_name(self) -> str:
                return "concrete"

            @property
            def attribute_version(self) -> str:
                return "1.0.0"

            def get_default_values(self) -> Dict[str, Any]:
                return {"data": "value"}

        def process_attribute(attribute: OpenPhAttribute) -> str:
            """Function that accepts any object satisfying the protocol."""
            return attribute.attribute_name

        # Should work with our concrete implementation
        attribute = ConcreteAttribute(model=None)
        result = process_attribute(attribute)
        assert result == "concrete"

    def test_protocol_with_multiple_implementations(self):
        """Test that multiple classes can satisfy the protocol."""

        @dataclass
        class AttributeA:
            model: Any

            @property
            def attribute_name(self) -> str:
                return "attribute_a"

            @property
            def attribute_version(self) -> str:
                return "1.0.0"

            def get_default_values(self) -> Dict[str, Any]:
                return {"value_a": 1}

        @dataclass
        class AttributeB:
            model: Any

            @property
            def attribute_name(self) -> str:
                return "attribute_b"

            @property
            def attribute_version(self) -> str:
                return "2.0.0"

            def get_default_values(self) -> Dict[str, Any]:
                return {"value_b": 2}

        def collect_attribute_names(attributes: list[OpenPhAttribute]) -> list[str]:
            """Function that works with a list of protocol-satisfying objects."""
            return [attr.attribute_name for attr in attributes]

        # Both classes satisfy the protocol
        attr_a = AttributeA(model=None)
        attr_b = AttributeB(model=None)

        names = collect_attribute_names([attr_a, attr_b])
        assert names == ["attribute_a", "attribute_b"]
