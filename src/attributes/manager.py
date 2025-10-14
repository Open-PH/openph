"""Attribute Manager for OpenPH Plugin System.

This module provides the manager class for coordinating attribute data
management. The AttributeManager uses the AttributeRegistry to discover
attributes and apply them to model instances.

Key Features:
    - Automatic attribute discovery and instantiation
    - Attribute data management for model instances
    - Dynamic attribute application
    - Validation and serialization support

Example:
    >>> from openph.attributes.manager import AttributeManager
    >>>
    >>> # Create manager and discover attributes
    >>> manager = AttributeManager()
    >>> manager.discover_attributes()
    >>>
    >>> # Set attribute data for a model instance
    >>> manager.set_attribute_data("Room", instance_id, "cost", {"cost": 1000.0})
    >>>
    >>> # Get attribute data
    >>> cost_data = manager.get_attribute_data("Room", instance_id, "cost")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from openph.attributes.registry import AttributeRegistry

if TYPE_CHECKING:
    from openph.attributes.base import OpenPhAttribute


class AttributeValidationError(Exception):
    """Exception raised when attribute validation fails."""

    def __init__(
        self,
        attribute_name: str,
        message: str,
        validation_errors: Optional[List[str]] = None,
    ):
        """Initialize attribute validation error.

        Args:
            attribute_name: Name of the attribute that failed validation
            message: Error message
            validation_errors: List of specific validation errors
        """
        self.attribute_name = attribute_name
        self.validation_errors = validation_errors or []
        super().__init__(f"Attribute '{attribute_name}' validation failed: {message}")


class AttributeManager:
    """Manager for coordinating attribute data management.

    The AttributeManager handles attribute lifecycle including:
    - Discovery via AttributeRegistry
    - Data storage per model instance
    - Validation using attribute protocols
    - Serialization/deserialization

    Attributes:
        registry: The AttributeRegistry used for discovery
        _attribute_instances: Cache of instantiated attribute objects
        _instance_data: Storage for attribute data per model instance
                       Structure: {class_name: {instance_id: {attribute_name: data}}}

    Example:
        >>> manager = AttributeManager()
        >>> manager.discover_attributes()
        >>>
        >>> # Set attribute data
        >>> manager.set_attribute_data("Room", "room_1", "cost", {"cost": 1000.0})
        >>>
        >>> # Get attribute data
        >>> cost_data = manager.get_attribute_data("Room", "room_1", "cost")
        >>> print(cost_data["cost"])  # 1000.0
        >>>
        >>> # Get all attributes for an instance
        >>> all_attrs = manager.get_all_instance_attributes("Room", "room_1")
    """

    def __init__(self, registry: Optional[AttributeRegistry] = None):
        """Initialize the attribute manager.

        Args:
            registry: Optional AttributeRegistry to use. If not provided,
                     a new registry will be created.
        """
        self.registry = registry if registry is not None else AttributeRegistry()
        self._attribute_instances: Dict[str, OpenPhAttribute] = {}
        self._instance_data: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def discover_attributes(self, group: str = "openph.attributes") -> None:
        """Discover available attributes via entry points.

        This delegates to the registry's discover_attributes method and
        clears any cached instances and instance data.

        Args:
            group: Entry point group to scan (default: "openph.attributes")
        """
        self.registry.discover_attributes(group=group)
        self._attribute_instances.clear()
        self._instance_data.clear()

    def get_attribute_instance(self, attribute_name: str) -> OpenPhAttribute:
        """Get or create an attribute instance.

        Attribute instances are cached, so repeated calls for the same
        attribute will return the same instance.

        Args:
            attribute_name: Name of the attribute to instantiate

        Returns:
            Instantiated attribute object

        Raises:
            KeyError: If attribute with given name is not found
            RuntimeError: If attribute instantiation fails
        """
        # Return cached instance if available
        if attribute_name in self._attribute_instances:
            return self._attribute_instances[attribute_name]

        # Get attribute class from registry
        attribute_class = self.registry.get_attribute_class(attribute_name)

        # Instantiate attribute
        try:
            attribute_instance = attribute_class()
            self._attribute_instances[attribute_name] = attribute_instance
            return attribute_instance
        except Exception as e:
            raise RuntimeError(
                f"Failed to instantiate attribute '{attribute_name}': {e}"
            ) from e

    def set_attribute_data(
        self,
        class_name: str,
        instance_id: str,
        attribute_name: str,
        data: Dict[str, Any],
        validate: bool = True,
    ) -> None:
        """Set attribute data for a model instance.

        Args:
            class_name: Name of the model class (e.g., "Room", "Building")
            instance_id: Unique identifier for the model instance
            attribute_name: Name of the attribute to set
            data: Attribute data dictionary
            validate: Whether to validate data before setting

        Raises:
            AttributeValidationError: If validation fails and validate=True
            KeyError: If attribute is not found
            ValueError: If attribute doesn't extend the specified class
        """
        # Verify attribute extends this class
        attribute_info = self.registry.get_attribute_info(attribute_name)
        if class_name not in attribute_info.extends_classes:
            raise ValueError(
                f"Attribute '{attribute_name}' does not extend class '{class_name}'. "
                f"It extends: {attribute_info.extends_classes}"
            )

        # Validate data if requested
        if validate:
            attribute = self.get_attribute_instance(attribute_name)
            if not attribute.validate_attribute_data(data):
                raise AttributeValidationError(
                    attribute_name=attribute_name,
                    message=f"Invalid data for attribute '{attribute_name}'",
                )

        # Initialize storage structure if needed
        if class_name not in self._instance_data:
            self._instance_data[class_name] = {}
        if instance_id not in self._instance_data[class_name]:
            self._instance_data[class_name][instance_id] = {}

        # Store data
        self._instance_data[class_name][instance_id][attribute_name] = data

    def get_attribute_data(
        self,
        class_name: str,
        instance_id: str,
        attribute_name: str,
        use_defaults: bool = True,
    ) -> Dict[str, Any]:
        """Get attribute data for a model instance.

        Args:
            class_name: Name of the model class
            instance_id: Unique identifier for the model instance
            attribute_name: Name of the attribute to get
            use_defaults: If True and no data exists, return default values

        Returns:
            Attribute data dictionary

        Raises:
            KeyError: If no data exists and use_defaults=False
        """
        # Try to get existing data
        try:
            return self._instance_data[class_name][instance_id][attribute_name]
        except KeyError:
            if use_defaults:
                # Return default values from attribute
                attribute = self.get_attribute_instance(attribute_name)
                return attribute.get_default_values()
            raise KeyError(
                f"No data found for attribute '{attribute_name}' on "
                f"{class_name} instance '{instance_id}'"
            )

    def has_attribute_data(
        self,
        class_name: str,
        instance_id: str,
        attribute_name: str,
    ) -> bool:
        """Check if attribute data exists for a model instance.

        Args:
            class_name: Name of the model class
            instance_id: Unique identifier for the model instance
            attribute_name: Name of the attribute to check

        Returns:
            True if data exists, False otherwise
        """
        try:
            return (
                class_name in self._instance_data
                and instance_id in self._instance_data[class_name]
                and attribute_name in self._instance_data[class_name][instance_id]
            )
        except (KeyError, TypeError):
            return False

    def remove_attribute_data(
        self,
        class_name: str,
        instance_id: str,
        attribute_name: str,
    ) -> None:
        """Remove attribute data for a model instance.

        Args:
            class_name: Name of the model class
            instance_id: Unique identifier for the model instance
            attribute_name: Name of the attribute to remove

        Raises:
            KeyError: If no data exists to remove
        """
        try:
            del self._instance_data[class_name][instance_id][attribute_name]

            # Clean up empty dictionaries
            if not self._instance_data[class_name][instance_id]:
                del self._instance_data[class_name][instance_id]
            if not self._instance_data[class_name]:
                del self._instance_data[class_name]
        except KeyError as e:
            raise KeyError(
                f"No data found for attribute '{attribute_name}' on "
                f"{class_name} instance '{instance_id}'"
            ) from e

    def get_all_instance_attributes(
        self,
        class_name: str,
        instance_id: str,
    ) -> Dict[str, Dict[str, Any]]:
        """Get all attribute data for a model instance.

        Args:
            class_name: Name of the model class
            instance_id: Unique identifier for the model instance

        Returns:
            Dictionary mapping attribute names to their data
        """
        try:
            return self._instance_data[class_name][instance_id].copy()
        except KeyError:
            return {}

    def get_instances_with_attribute(
        self,
        class_name: str,
        attribute_name: str,
    ) -> List[str]:
        """Get all instance IDs that have a specific attribute.

        Args:
            class_name: Name of the model class
            attribute_name: Name of the attribute

        Returns:
            List of instance IDs that have this attribute
        """
        if class_name not in self._instance_data:
            return []

        instance_ids = []
        for instance_id, attrs in self._instance_data[class_name].items():
            if attribute_name in attrs:
                instance_ids.append(instance_id)

        return instance_ids

    def serialize_instance_attributes(
        self,
        class_name: str,
        instance_id: str,
    ) -> Dict[str, Dict[str, Any]]:
        """Serialize all attributes for a model instance.

        Uses each attribute's serialize_data method.

        Args:
            class_name: Name of the model class
            instance_id: Unique identifier for the model instance

        Returns:
            Dictionary of serialized attribute data
        """
        all_attrs = self.get_all_instance_attributes(class_name, instance_id)
        serialized = {}

        for attr_name, attr_data in all_attrs.items():
            attribute = self.get_attribute_instance(attr_name)
            serialized[attr_name] = attribute.serialize_data(attr_data)

        return serialized

    def deserialize_instance_attributes(
        self,
        class_name: str,
        instance_id: str,
        serialized_data: Dict[str, Dict[str, Any]],
        validate: bool = True,
    ) -> None:
        """Deserialize and set attributes for a model instance.

        Uses each attribute's deserialize_data method.

        Args:
            class_name: Name of the model class
            instance_id: Unique identifier for the model instance
            serialized_data: Dictionary of serialized attribute data
            validate: Whether to validate deserialized data

        Raises:
            AttributeValidationError: If validation fails
        """
        for attr_name, attr_data in serialized_data.items():
            attribute = self.get_attribute_instance(attr_name)
            deserialized = attribute.deserialize_data(attr_data)
            self.set_attribute_data(
                class_name=class_name,
                instance_id=instance_id,
                attribute_name=attr_name,
                data=deserialized,
                validate=validate,
            )

    def list_available_attributes(self) -> List[str]:
        """Get list of available attribute names.

        Returns:
            List of attribute names that can be used
        """
        return [info.name for info in self.registry.list_attributes()]

    def get_attributes_for_class(self, class_name: str) -> List[str]:
        """Get list of attribute names that extend a specific class.

        Args:
            class_name: Name of the model class

        Returns:
            List of attribute names that extend this class
        """
        attribute_infos = self.registry.get_attributes_for_class(class_name)
        return [info.name for info in attribute_infos]

    def clear_all_instance_data(self, class_name: str, instance_id: str) -> None:
        """Clear all attribute data for a specific instance.

        Args:
            class_name: Name of the model class
            instance_id: Unique identifier for the model instance
        """
        try:
            del self._instance_data[class_name][instance_id]
            if not self._instance_data[class_name]:
                del self._instance_data[class_name]
        except KeyError:
            pass  # No data to clear

    def reset(self) -> None:
        """Reset the manager, clearing instances and all data.

        This does not clear the registry's discovered attributes.
        Call discover_attributes() to rescan entry points.
        """
        self._attribute_instances.clear()
        self._instance_data.clear()
