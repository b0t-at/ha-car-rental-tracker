"""Pytest configuration.

The pure-Python helper modules of the integration (no Home Assistant imports)
are made importable as top-level modules so they can be tested without
installing Home Assistant.
"""
import os
import sys

COMPONENT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "custom_components", "car_rental_tracker"
)
sys.path.insert(0, os.path.abspath(COMPONENT_DIR))
