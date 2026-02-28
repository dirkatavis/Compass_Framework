import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "new_slice: unit tests for the ini_configuration slice"
    )


@pytest.fixture
def mock_driver():
    """Return a simple mock-like driver with minimal attributes used by tests."""
    from unittest.mock import Mock

    d = Mock()
    # default behaviors
    d.execute_script = Mock(return_value="complete")
    d.current_url = "http://example.com/"
    d.find_element = Mock(return_value=Mock())
    return d


@pytest.fixture
def dummy_wait_class(monkeypatch):
    """Provide a Dummy WebDriverWait replacement to control .until behavior."""
    from selenium.common.exceptions import TimeoutException

    class DummyWait:
        def __init__(self, driver, timeout, poll_frequency=None):
            self.driver = driver

        def until(self, condition):
            # call the condition once; if falsy raise TimeoutException
            res = condition(self.driver)
            if res:
                return res
            raise TimeoutException("condition not met")

    MonkeyPatchTarget = 'compass_core.selenium_navigator.WebDriverWait'
    monkeypatch.setattr(MonkeyPatchTarget, DummyWait)
    return DummyWait
