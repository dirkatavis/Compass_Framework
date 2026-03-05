import unittest
from unittest import mock

import compass_core.pm_actions_selenium as mod
from compass_core.pm_actions_selenium import SeleniumPmActions


class _FakeClickable:
    text = "Fake Button"
    def click(self):
        pass
    def clear(self):
        pass
    def is_displayed(self):
        return True
    def is_enabled(self):
        return True
    def send_keys(self, *args, **kwargs):
        pass


class _FakeElement:
    text = "Rentable"
    def click(self):
        pass
    def find_element(self, *args, **kwargs):
        return _FakeClickable()


class _FakeWait:
    def __init__(self, driver, timeout, poll_frequency=0.5):
        self.driver = driver
        self.timeout = timeout
        self.poll_frequency = poll_frequency
    def until(self, cond):
        # Return a clickable/element for any condition
        if callable(cond):
            return _FakeClickable()
        return _FakeElement()


class _FakeDriver:
    def __init__(self, elements=None):
        self._elements = elements or []
        self.current_url = "https://fake.url/health"
        self.title = "Fake PWA"
    def find_element(self, *args, **kwargs):
        return _FakeElement()
    def find_elements(self, *args, **kwargs):
        return self._elements
    def back(self):
        pass
    def execute_script(self, *args, **kwargs):
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

    def test_create_workitem_skips_when_open_card_exists(self):
        """Test Step 0: Dashboard Audit correctly identifies existing open cards."""
        # Create a fake card element that matches the "Glass Damage" type
        class _OpenCard:
            text = "[OPEN] Glass Damage - Needs attention"
            def is_displayed(self): return True
            def is_enabled(self): return True

        # Driver should return this card when looking for status-red tiles
        actions = SeleniumPmActions(_FakeDriver(elements=[_OpenCard()]))
        
        # We need to ensure find_elements returns the card for the audit XPath
        res = actions.create_workitem("MVA123", "Glass Damage", "Windshield", "Repair")
        
        self.assertEqual(res.get('status'), 'success')
        self.assertEqual(res.get('message'), 'skipped_duplicate')
        self.assertEqual(res.get('reason'), 'existing_open_workitem')

    def test_create_workitem_wizard_icon_xpath_mapping(self):
        """Verify the wizard uses correct icon-based XPaths for categories."""
        actions = SeleniumPmActions(_FakeDriver())
        
        with mock.patch.object(actions, '_select_existing_complaint_by_damage_type', return_value={"status": "not_found"}):
            with mock.patch('compass_core.pm_actions_selenium.WebDriverWait') as mock_wait_class:
                with mock.patch('compass_core.pm_actions_selenium.EC') as mock_ec:
                    mock_wait_instance = mock_wait_class.return_value
                    mock_wait_instance.until.return_value = _FakeClickable()
                    
                    # Directly call the method
                    actions.create_workitem("MVA123", "PM", "Oil Change", "Service")
                    
                    # Check for Oil Can icon in the calls to EC.element_to_be_clickable
                    all_ec_calls_str = str(mock_ec.element_to_be_clickable.call_args_list)
                    self.assertIn('bp6-icon-oil-can', all_ec_calls_str, "Oil Can icon XPath should be used for PM category")

if __name__ == '__main__':
    unittest.main()
