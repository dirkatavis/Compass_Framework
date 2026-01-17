import unittest
from unittest import mock

import compass_core.pm_actions_selenium as mod
from compass_core.pm_actions_selenium import SeleniumPmActions


class _FakeClickable:
    def click(self):
        pass
    def clear(self):
        pass
    def send_keys(self, *args, **kwargs):
        pass


class _FakeElement:
    text = "Rentable"
    def click(self):
        pass
    def find_element(self, *args, **kwargs):
        return _FakeClickable()


class _FakeWait:
    def __init__(self, driver, timeout):
        self.driver = driver
        self.timeout = timeout
    def until(self, cond):
        # Return a clickable/element for any condition
        if callable(cond):
            return _FakeClickable()
        return _FakeElement()


class _FakeDriver:
    def __init__(self, elements=None):
        self._elements = elements or []
    def find_element(self, *args, **kwargs):
        return _FakeElement()
    def find_elements(self, *args, **kwargs):
        return self._elements
    def back(self):
        pass


class TestSeleniumPmActions(unittest.TestCase):
    def setUp(self):
        # Patch WebDriverWait and EC to simple fakes
        self.wait_patcher = mock.patch.object(mod, 'WebDriverWait', _FakeWait)
        self.ec_patcher = mock.patch.object(mod, 'EC', mock.Mock())
        self.wait_patcher.start()
        self.ec_patcher.start()

    def tearDown(self):
        self.wait_patcher.stop()
        self.ec_patcher.stop()

    def test_get_lighthouse_status_returns_text_or_none(self):
        actions = SeleniumPmActions(_FakeDriver())
        self.assertIsInstance(actions.get_lighthouse_status("MVA"), (str, type(None)))

    def test_has_open_workitem_true_when_tiles_present(self):
        actions = SeleniumPmActions(_FakeDriver(elements=[_FakeElement()]))
        self.assertTrue(actions.has_open_workitem("MVA"))

    def test_has_open_workitem_false_on_error(self):
        class _ErrDriver(_FakeDriver):
            def find_elements(self, *args, **kwargs):
                raise Exception("fail")
        actions = SeleniumPmActions(_ErrDriver())
        self.assertFalse(actions.has_open_workitem("MVA"))

    def test_complete_open_workitem_returns_ok(self):
        actions = SeleniumPmActions(_FakeDriver())
        res = actions.complete_open_workitem("MVA")
        self.assertEqual(res.get('status'), 'ok')

    def test_has_pm_complaint_checks_tiles(self):
        class _FakePMTile(_FakeElement):
            text = "PM"
        actions = SeleniumPmActions(_FakeDriver(elements=[_FakePMTile()]))
        self.assertTrue(actions.has_pm_complaint("MVA"))

    def test_associate_pm_complaint_skips_when_none(self):
        actions = SeleniumPmActions(_FakeDriver(elements=[]))
        res = actions.associate_pm_complaint("MVA")
        self.assertEqual(res.get('status'), 'skipped_no_complaint')

    def test_navigate_back_home_no_exception(self):
        actions = SeleniumPmActions(_FakeDriver())
        actions.navigate_back_home()  # should not raise


if __name__ == '__main__':
    unittest.main()
