"""Utility wrappers for nuclide calculations.

This module previously duplicated a number of helper functions.  To
avoid code drift we simply re-export the implementations from
``src.models.entities.nuclide``.
"""

from .entities.nuclide import (
    calculate_decayed_activity,
    calculate_initial_activity,
    calculate_time_to_target,
    convert_activity_unit,
)

__all__ = [
    "calculate_decayed_activity",
    "calculate_initial_activity",
    "calculate_time_to_target",
    "convert_activity_unit",
]
