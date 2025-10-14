"""Base protocol and types for OpenPH data model attributes.

This module defines the core interfaces that all OpenPH attribute extensions must implement.
Attributes are discovered via entry points and managed by the AttributeRegistry.
"""

from typing import Protocol, TYPE_CHECKING, Any, Dict
from abc import abstractmethod

if TYPE_CHECKING:
    from openph.model import OpenPhModel


class OpenPhAttribute(Protocol):
    """Protocol that all OpenPH attribute extensions must implement.

    This protocol defines the interface for pluggable data model extensions.
    Attributes allow external packages to add custom data fields to the core
    data model without modifying the core package.

    Attributes are discovered via entry points in pyproject.toml and managed
    by the AttributeRegistry and AttributeManager.

    Example:
        >>> @dataclass
        >>> class CostDataAttribute:
        >>>     model: OpenPhModel
        >>>
        >>>     @property
        >>>     def attribute_name(self) -> str:
        >>>         return "cost_data"
        >>>
        >>>     def get_default_values(self) -> Dict[str, Any]:
        >>>         return {
        >>>             "material_cost_per_m2": 0.0,
        >>>             "labor_cost_per_m2": 0.0,
        >>>             "cost_currency": "USD",
        >>>         }
    """

    @property
    @abstractmethod
    def attribute_name(self) -> str:
        """Unique identifier for this attribute extension (e.g., 'cost_data').

        This name is used:
        - In entry point registration
        - For attribute access via AttributeManager
        - In attribute discovery and management

        Returns:
            Unique attribute name as a string.
        """
        ...

    @property
    @abstractmethod
    def attribute_version(self) -> str:
        """Version of attribute schema (e.g., '1.0.0').

        Used for:
        - Tracking data schema version
        - Backward compatibility management
        - Migration and validation

        Returns:
            Semantic version string.
        """
        ...

    @property
    def extends_classes(self) -> list[str]:
        """List of core model classes this attribute extends.

        Specifies which parts of the data model this attribute applies to.
        Common values: "OpenPhModel", "OpenPhRoom", "OpenPhConstruction", etc.

        Example:
            >>> @property
            >>> def extends_classes(self) -> list[str]:
            >>>     return ["OpenPhModel", "OpenPhRoom"]

        Returns:
            List of class names. Default is ["OpenPhModel"] if not specified.
        """
        return ["OpenPhModel"]

    @property
    def attribute_description(self) -> str:
        """Human-readable description of what this attribute provides.

        Used for:
        - Documentation
        - User interfaces
        - Debugging output

        Returns:
            Description string. Empty string if not specified.
        """
        return ""

    def __init__(self, model: "OpenPhModel") -> None:
        """All attributes must accept OpenPhModel reference.

        Args:
            model: The OpenPhModel instance to extend with this attribute.
        """
        ...

    @abstractmethod
    def get_default_values(self) -> Dict[str, Any]:
        """Return dict of field_name -> default_value for this attribute.

        This method defines the data schema for the attribute by providing
        default values for all fields. The AttributeManager uses this to
        initialize attribute data.

        Example:
            >>> def get_default_values(self) -> Dict[str, Any]:
            >>>     return {
            >>>         'material_cost_per_m2': 0.0,
            >>>         'labor_cost_per_m2': 0.0,
            >>>         'equipment_cost': 0.0,
            >>>         'cost_currency': 'USD',
            >>>         'cost_year': 2024,
            >>>     }

        Returns:
            Dictionary mapping field names to their default values.
        """
        ...

    def validate_attribute_data(self, data: Dict[str, Any]) -> list[str]:
        """Validate attribute data values.

        This method is called by AttributeManager.set() before updating
        attribute data. It should check that values are valid and return
        any error messages.

        Example:
            >>> def validate_attribute_data(self, data: Dict[str, Any]) -> list[str]:
            >>>     errors = []
            >>>
            >>>     # Check numeric fields are non-negative
            >>>     if 'material_cost_per_m2' in data and data['material_cost_per_m2'] < 0:
            >>>         errors.append("material_cost_per_m2 cannot be negative")
            >>>
            >>>     # Check currency code is valid
            >>>     valid_currencies = ["USD", "EUR", "GBP"]
            >>>     if 'cost_currency' in data and data['cost_currency'] not in valid_currencies:
            >>>         errors.append(f"cost_currency must be one of: {valid_currencies}")
            >>>
            >>>     return errors

        Args:
            data: Dictionary of field names and values to validate.

        Returns:
            List of error messages. Empty list if all data is valid.
        """
        return []

    def serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize attribute data for storage/export.

        Override this method to customize how attribute data is serialized
        (e.g., for JSON export, database storage, file I/O).

        Default implementation returns data unchanged.

        Example:
            >>> def serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
            >>>     # Convert all numeric values to strings for JSON
            >>>     return {
            >>>         k: str(v) if isinstance(v, (int, float)) else v
            >>>         for k, v in data.items()
            >>>     }

        Args:
            data: Dictionary of attribute data to serialize.

        Returns:
            Serialized data dictionary.
        """
        return data

    def deserialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize attribute data from storage/import.

        Override this method to customize how attribute data is deserialized
        (e.g., from JSON import, database retrieval, file I/O).

        Default implementation returns data unchanged.

        Example:
            >>> def deserialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
            >>>     # Convert string values back to numeric
            >>>     result = {}
            >>>     for k, v in data.items():
            >>>         if k.endswith('_cost') or k.endswith('_m2'):
            >>>             result[k] = float(v)
            >>>         else:
            >>>             result[k] = v
            >>>     return result

        Args:
            data: Dictionary of serialized attribute data.

        Returns:
            Deserialized data dictionary.
        """
        return data
