"""OpenPH Attribute System.

This package provides the attribute infrastructure for OpenPH, including:
- Base protocols for attribute plugins
- Registry system for attribute discovery
- Class extension management
"""

from openph.attributes.base import OpenPhAttribute
from openph.attributes.registry import AttributeInfo, AttributeRegistry

__all__ = [
    "OpenPhAttribute",
    "AttributeInfo",
    "AttributeRegistry",
]
