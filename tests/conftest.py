import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "new_slice: unit tests for the ini_configuration slice"
    )
