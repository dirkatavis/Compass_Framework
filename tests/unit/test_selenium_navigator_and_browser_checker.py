import subprocess
import re

import pytest

from compass_core.selenium_navigator import SeleniumNavigator
from compass_core.browser_version_checker import BrowserVersionChecker


@pytest.mark.new_slice
def test_verify_page_success(mock_driver, dummy_wait_class):
    mock_driver.current_url = 'https://example.com/page'
    nav = SeleniumNavigator(mock_driver)
    res = nav.verify_page(url='https://example.com')
    assert res['status'] == 'success'
    assert res['current_url'] == mock_driver.current_url


@pytest.mark.new_slice
def test_verify_page_url_mismatch(mock_driver, dummy_wait_class):
    mock_driver.current_url = 'https://other.example.com/page'
    nav = SeleniumNavigator(mock_driver)
    res = nav.verify_page(url='https://example.com')
    assert res['status'] == 'failure'
    assert res.get('error') == 'url_mismatch'


@pytest.mark.new_slice
def test_verify_page_with_locator_success(mock_driver, dummy_wait_class, monkeypatch):
    # Ensure presence_of_element_located returns a callable that succeeds
    monkeypatch.setattr('compass_core.selenium_navigator.EC.presence_of_element_located', lambda loc: (lambda d: True))
    mock_driver.current_url = 'https://example.com/page'
    nav = SeleniumNavigator(mock_driver)
    res = nav.verify_page(check_locator=("id", "some-id"))
    assert res['status'] == 'success'


@pytest.mark.new_slice
def test_verify_page_timeout(mock_driver, monkeypatch):
    # Replace WebDriverWait.until to always raise TimeoutException
    from selenium.common.exceptions import TimeoutException

    class AlwaysTimeout:
        def __init__(self, driver, timeout, poll_frequency=None):
            pass

        def until(self, condition):
            raise TimeoutException('timed out')

    monkeypatch.setattr('compass_core.selenium_navigator.WebDriverWait', AlwaysTimeout)
    mock_driver.current_url = 'https://example.com/page'
    nav = SeleniumNavigator(mock_driver)
    res = nav.verify_page()
    assert res['status'] == 'failure'


@pytest.mark.new_slice
def test_browser_version_checker_executable(monkeypatch, tmp_path):
    checker = BrowserVersionChecker()
    exe = str(tmp_path / 'fakechrome.exe')

    # pretend file exists
    monkeypatch.setattr('os.path.exists', lambda p: True)

    class Result:
        def __init__(self, stdout, returncode=0):
            self.stdout = stdout
            self.returncode = returncode

    # simulate subprocess.run returning a chrome-like string
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: Result('Google Chrome 131.0.6778.85', 0))
    v = checker._get_version_from_executable(exe)
    assert re.match(r'\d+\.\d+\.\d+\.\d+', v)


@pytest.mark.new_slice
def test_check_compatibility_logic(monkeypatch):
    checker = BrowserVersionChecker()
    # Force detected versions
    monkeypatch.setattr(checker, 'get_browser_version', lambda: '131.0.1.1')
    monkeypatch.setattr(checker, 'get_driver_version', lambda p=None: '131.0.2.2')
    res = checker.check_compatibility('chrome')
    assert res['compatible'] is True
    assert res['major_match'] is True
