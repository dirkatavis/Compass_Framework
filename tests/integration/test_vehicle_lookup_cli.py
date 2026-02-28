import os
import tempfile
import unittest
from unittest.mock import Mock
import importlib
import sys


class FakeIniConfiguration:
    def load(self, path):
        return {'credentials': {'username': 'u', 'password': 'p', 'login_id': 'id'}, 'app': {'app_url': 'http://example'}}

    def validate(self):
        return True


class FakeDriverManager:
    def __init__(self):
        self._driver = object()

    def get_or_create_driver(self, **kwargs):
        return self._driver

    def quit_driver(self):
        return None


class FakeSeleniumLoginFlow:
    def __init__(self, driver, navigator, logger):
        pass


class FakeSmartLoginFlow:
    def __init__(self, driver, navigator, base_login, logger):
        pass

    def authenticate(self, **kwargs):
        return {'status': 'success'}


class FakeVehicleActions:
    def __init__(self, driver, logger=None):
        pass

    def enter_mva(self, mva, clear_existing=True):
        return {'status': 'success'}

    def wait_for_property_page_loaded(self, mva):
        return True

    def get_vehicle_property(self, name, timeout=5):
        return f'{name}-VALUE'


class TestVehicleLookupCLI(unittest.TestCase):
    def test_main_runs_with_fakes_and_writes_output(self):
        # Import module fresh to ensure globals are mutable
        spec = importlib.util.spec_from_file_location('vehicle_lookup', os.path.join('clients', 'vehicle_lookup', 'VehicleLookup.py'))
        mod = importlib.util.module_from_spec(spec)
        sys.modules['vehicle_lookup'] = mod
        spec.loader.exec_module(mod)  # type: ignore

        # Patch module globals to inject fakes
        mod.IniConfiguration = FakeIniConfiguration
        mod.StandardDriverManager = FakeDriverManager
        mod.SeleniumLoginFlow = FakeSeleniumLoginFlow
        mod.SmartLoginFlow = FakeSmartLoginFlow
        mod.SeleniumVehicleDataActions = FakeVehicleActions

        # Create temp input and output paths
        td = tempfile.TemporaryDirectory()
        input_path = os.path.join(td.name, 'input.csv')
        output_path = os.path.join(td.name, 'output.csv')
        with open(input_path, 'w', encoding='utf-8') as f:
            f.write('12345678\n')

        # Run main with explicit args via argv
        orig_argv = sys.argv[:]
        try:
            sys.argv = ['VehicleLookup.py', '--input', input_path, '--output', output_path, '--config', 'ignored']
            ret = mod.main()
        finally:
            sys.argv = orig_argv

        self.assertEqual(ret, 0)
        self.assertTrue(os.path.exists(output_path))
        # Basic contents assertion
        with open(output_path, 'r', encoding='utf-8') as f:
            contents = f.read()
        self.assertIn('mva,vin,desc', contents)
        self.assertIn('12345678', contents)


if __name__ == '__main__':
    unittest.main()
