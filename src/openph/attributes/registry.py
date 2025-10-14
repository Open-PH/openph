"""Attribute Registry for OpenPH Plugin System.

This module provides the registry system for discovering and managing attribute plugins
through Python entry points. It handles attribute discovery, validation, and metadata
management.

Key Features:
    - Automatic attribute discovery via entry points
    - Attribute metadata management
    - Class extension tracking
    - Attribute validation

Example:
    >>> registry = AttributeRegistry()
    >>> registry.discover_attributes()
    >>> 
    >>> # Get attributes for a specific class
    >>> cost_attrs = registry.get_attributes_for_class("Room")
    >>> 
    >>> # Get specific attribute
    >>> cost_attr = registry.get_attribute_class("cost")
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from importlib.metadata import entry_points
from typing import TYPE_CHECKING, Dict, List, Set, Type

if TYPE_CHECKING:
    from openph.attributes.base import OpenPhAttribute


@dataclass
class AttributeInfo:
    """Metadata container for discovered attribute plugins.
    
    This dataclass stores all relevant information about an attribute plugin,
    including its class, the classes it extends, and metadata.
    
    Attributes:
        name: The unique identifier for the attribute (from attribute_name property)
        attribute_class: The actual attribute class implementing OpenPhAttribute protocol
        extends_classes: Set of class names this attribute extends
        description: Human-readable description of the attribute
        version: Attribute version string
        entry_point_name: Original name from entry point registration
    """
    
    name: str
    attribute_class: Type[OpenPhAttribute]
    extends_classes: Set[str] = field(default_factory=set)
    description: str = ""
    version: str = "0.0.0"
    entry_point_name: str = ""
    
    def __post_init__(self) -> None:
        """Validate that extends_classes is a set."""
        if not isinstance(self.extends_classes, set):
            self.extends_classes = set(self.extends_classes) if self.extends_classes else set()


class AttributeRegistry:
    """Registry for managing OpenPH attribute plugins.
    
    The AttributeRegistry discovers attributes via entry points, validates their
    protocol compliance, and organizes them by the classes they extend.
    
    Attributes:
        _attributes: Dictionary mapping attribute names to AttributeInfo objects
        _class_index: Dictionary mapping class names to sets of attribute names
        _discovered: Flag indicating if discovery has been run
    
    Example:
        >>> registry = AttributeRegistry()
        >>> registry.discover_attributes()
        >>> 
        >>> # Get all attributes extending a specific class
        >>> room_attrs = registry.get_attributes_for_class("Room")
        >>> 
        >>> # Get specific attribute
        >>> cost_attr = registry.get_attribute_class("cost")
        >>> 
        >>> # List all attributes
        >>> for info in registry.list_attributes():
        ...     print(f"{info.name}: extends {info.extends_classes}")
    """
    
    def __init__(self) -> None:
        """Initialize an empty attribute registry."""
        self._attributes: Dict[str, AttributeInfo] = {}
        self._class_index: Dict[str, Set[str]] = {}
        self._discovered: bool = False
    
    def discover_attributes(self, group: str = "openph.attributes") -> None:
        """Discover and load attribute plugins from entry points.
        
        This method scans the specified entry point group for registered
        attributes, loads them, and validates their protocol compliance.
        
        Args:
            group: The entry point group name to scan (default: "openph.attributes")
        
        Raises:
            TypeError: If a discovered plugin doesn't implement OpenPhAttribute protocol
            ValueError: If attribute metadata is invalid
        
        Note:
            This method can be called multiple times. Each call will clear
            previous discoveries and rescan entry points.
        """
        # Clear previous discoveries
        self._attributes.clear()
        self._class_index.clear()
        self._discovered = False
        
        # Get entry points for the specified group
        # Handle both Python 3.10+ and 3.9 APIs
        if sys.version_info >= (3, 10):
            eps = entry_points(group=group)
        else:
            eps = entry_points().get(group, [])
        
        # Load each attribute
        for ep in eps:
            try:
                # Load the attribute class
                attribute_class = ep.load()
                
                # Validate protocol compliance
                self._validate_attribute_protocol(attribute_class)
                
                # Create AttributeInfo from attribute class properties
                attribute_info = AttributeInfo(
                    name=attribute_class.attribute_name,
                    attribute_class=attribute_class,
                    extends_classes=set(attribute_class.extends_classes) 
                        if attribute_class.extends_classes else set(),
                    description=attribute_class.attribute_description 
                        if hasattr(attribute_class, "attribute_description") else "",
                    version=attribute_class.attribute_version,
                    entry_point_name=ep.name,
                )
                
                # Register the attribute
                self._attributes[attribute_info.name] = attribute_info
                
                # Update class index
                self._update_class_index(attribute_info)
                
            except Exception as e:
                # Log or raise discovery errors
                raise RuntimeError(
                    f"Failed to load attribute from entry point '{ep.name}': {e}"
                ) from e
        
        self._discovered = True
    
    def _validate_attribute_protocol(self, attribute_class: Type) -> None:
        """Validate that a class implements the OpenPhAttribute protocol.
        
        Args:
            attribute_class: The class to validate
        
        Raises:
            TypeError: If the class doesn't implement required protocol attributes
        """
        required_attrs = [
            "attribute_name",
            "attribute_version",
            "extends_classes",
            "get_default_values",
            "validate_attribute_data",
            "serialize_data",
            "deserialize_data",
        ]
        
        missing_attrs = [
            attr for attr in required_attrs 
            if not hasattr(attribute_class, attr)
        ]
        
        if missing_attrs:
            raise TypeError(
                f"Attribute class {attribute_class.__name__} does not implement "
                f"OpenPhAttribute protocol. Missing attributes: {missing_attrs}"
            )
    
    def _update_class_index(self, attribute_info: AttributeInfo) -> None:
        """Update the class index with this attribute.
        
        Args:
            attribute_info: The attribute to index
        """
        for class_name in attribute_info.extends_classes:
            if class_name not in self._class_index:
                self._class_index[class_name] = set()
            self._class_index[class_name].add(attribute_info.name)
    
    def get_attribute_class(self, attribute_name: str) -> Type[OpenPhAttribute]:
        """Get the attribute class for a specific attribute.
        
        Args:
            attribute_name: The name of the attribute to retrieve
        
        Returns:
            The attribute class implementing OpenPhAttribute protocol
        
        Raises:
            KeyError: If no attribute with the given name is registered
        """
        if not self._discovered:
            raise RuntimeError(
                "Cannot get attribute before discovering attributes. "
                "Call discover_attributes() first."
            )
        
        if attribute_name not in self._attributes:
            available = ", ".join(self._attributes.keys())
            raise KeyError(
                f"Attribute '{attribute_name}' not found. "
                f"Available attributes: {available if available else 'none'}"
            )
        
        return self._attributes[attribute_name].attribute_class
    
    def get_attribute_info(self, attribute_name: str) -> AttributeInfo:
        """Get detailed information about a specific attribute.
        
        Args:
            attribute_name: The name of the attribute
        
        Returns:
            AttributeInfo object with attribute metadata
        
        Raises:
            KeyError: If no attribute with the given name is registered
        """
        if not self._discovered:
            raise RuntimeError(
                "Cannot get attribute info before discovering attributes. "
                "Call discover_attributes() first."
            )
        
        if attribute_name not in self._attributes:
            available = ", ".join(self._attributes.keys())
            raise KeyError(
                f"Attribute '{attribute_name}' not found. "
                f"Available attributes: {available if available else 'none'}"
            )
        
        return self._attributes[attribute_name]
    
    def get_attributes_for_class(self, class_name: str) -> List[AttributeInfo]:
        """Get all attributes that extend a specific class.
        
        Args:
            class_name: The name of the class to find attributes for
        
        Returns:
            List of AttributeInfo objects for attributes extending this class
        
        Raises:
            RuntimeError: If attributes haven't been discovered yet
        """
        if not self._discovered:
            raise RuntimeError(
                "Cannot get attributes before discovering attributes. "
                "Call discover_attributes() first."
            )
        
        # Return empty list if no attributes for this class
        if class_name not in self._class_index:
            return []
        
        attribute_names = self._class_index[class_name]
        return [self._attributes[name] for name in attribute_names]
    
    def list_attributes(self) -> List[AttributeInfo]:
        """Get information about all registered attributes.
        
        Returns:
            List of AttributeInfo objects for all discovered attributes
        
        Raises:
            RuntimeError: If attributes haven't been discovered yet
        """
        if not self._discovered:
            raise RuntimeError(
                "Cannot list attributes before discovering attributes. "
                "Call discover_attributes() first."
            )
        
        return list(self._attributes.values())
    
    def list_extended_classes(self) -> List[str]:
        """Get list of all classes that have attributes extending them.
        
        Returns:
            List of class names that are extended by at least one attribute
        
        Raises:
            RuntimeError: If attributes haven't been discovered yet
        """
        if not self._discovered:
            raise RuntimeError(
                "Cannot list extended classes before discovering attributes. "
                "Call discover_attributes() first."
            )
        
        return list(self._class_index.keys())
    
    def has_attributes_for_class(self, class_name: str) -> bool:
        """Check if any attributes extend a specific class.
        
        Args:
            class_name: The name of the class to check
        
        Returns:
            True if at least one attribute extends this class
        
        Raises:
            RuntimeError: If attributes haven't been discovered yet
        """
        if not self._discovered:
            raise RuntimeError(
                "Cannot check attributes before discovering attributes. "
                "Call discover_attributes() first."
            )
        
        return class_name in self._class_index and len(self._class_index[class_name]) > 0
