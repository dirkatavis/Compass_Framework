import unittest

from compass_core.pm_actions import PmActions

from compass_core.pm_actions_selenium import SeleniumPmActions


class _FakeDriver:
    def find_element(self, *args, **kwargs):
        class _El:
            text = "PM"
            def click(self):
                pass
        return _El()
    def find_elements(self, *args, **kwargs):
        return []
    def back(self):
        pass


class TestPmActionsInterface(unittest.TestCase):
    def test_protocol_compliance(self):
        impl = SeleniumPmActions(_FakeDriver())
        self.assertIsInstance(impl, PmActions)

    def test_required_methods_exist(self):
        impl = SeleniumPmActions(_FakeDriver())
        for name in [
            'get_lighthouse_status',
            'has_open_workitem',
            'complete_open_workitem',
            'has_pm_complaint',
            'associate_pm_complaint',
            'navigate_back_home',
            'find_workitem',
            'create_workitem',
        ]:
            self.assertTrue(hasattr(impl, name))
            self.assertTrue(callable(getattr(impl, name)))


if __name__ == '__main__':
    unittest.main()
