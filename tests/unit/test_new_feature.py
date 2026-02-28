import importlib
from pathlib import Path
import textwrap

import pytest

from compass_core.ini_configuration import IniConfiguration


@pytest.mark.new_slice
def test_default_file_priority_uses_local(tmp_path, monkeypatch):
    # create both files; local should be used
    local = tmp_path / "webdriver.ini.local"
    default = tmp_path / "webdriver.ini"
    local.write_text("[webdriver]\nedge_path=local/edge.exe\n")
    default.write_text("[webdriver]\nedge_path=default/edge.exe\n")

    monkeypatch.chdir(tmp_path)
    cfg = IniConfiguration()  # no path -> uses default-file priority
    data = cfg.get_all()
    assert "webdriver" in data
    assert data["webdriver"]["edge_path"] == "local/edge.exe"


@pytest.mark.new_slice
def test_load_converts_types_and_booleans(tmp_path):
    content = textwrap.dedent(
        """
        [timeouts]
        page_load = 5
        implicit_wait = 2

        [flags]
        enabled = true
        disabled = false

        [values]
        pi = 3.14
        name = example
        """
    )
    f = tmp_path / "test.ini"
    f.write_text(content)

    cfg = IniConfiguration()
    out = cfg.load(f)
    # numeric conversions
    assert isinstance(out["timeouts"]["page_load"], int)
    assert out["timeouts"]["page_load"] == 5
    assert isinstance(out["values"]["pi"], float)
    assert out["values"]["pi"] == pytest.approx(3.14)
    # boolean conversions
    assert out["flags"]["enabled"] is True
    assert out["flags"]["disabled"] is False
    # string remains string
    assert out["values"]["name"] == "example"


@pytest.mark.new_slice
def test_load_nonexistent_raises(tmp_path):
    cfg = IniConfiguration()
    with pytest.raises(FileNotFoundError):
        cfg.load(tmp_path / "no-such-file.ini")


@pytest.mark.new_slice
def test_save_writes_file_and_contents(tmp_path):
    cfg = IniConfiguration()
    config_data = {
        "webdriver": {"edge_path": "C:\\drivers\\edge.exe"},
        "timeouts": {"page_load": 10}
    }
    dest = tmp_path / "out.ini"
    ok = cfg.save(config_data, dest)
    assert ok is True
    assert dest.exists()
    # reload using configparser indirectly via IniConfiguration.load
    reloaded = IniConfiguration()
    loaded = reloaded.load(dest)
    assert loaded["webdriver"]["edge_path"] == "C:\\drivers\\edge.exe"
    assert isinstance(loaded["timeouts"]["page_load"], int)


@pytest.mark.new_slice
def test_save_returns_false_on_mkdir_failure(tmp_path):
    # Create a file where the parent directory is expected to be a directory.
    parent_as_file = tmp_path / "parentfile"
    parent_as_file.write_text("not a dir")
    dest = parent_as_file / "out.ini"  # parent is a file, mkdir will raise
    cfg = IniConfiguration()
    ok = cfg.save({"s": {"k": "v"}}, dest)
    assert ok is False


@pytest.mark.new_slice
def test_get_and_set_dot_notation_and_default_section():
    cfg = IniConfiguration()
    # set with dot notation
    assert cfg.set("webdriver.edge_path", r"C:\\x\\edge.exe") is True
    assert cfg.get("webdriver.edge_path") == r"C:\\x\\edge.exe"
    # set without dot -> DEFAULT section
    assert cfg.set("simple_key", "value") is True
    assert cfg.get("simple_key") == "value"


@pytest.mark.new_slice
def test_validate_reports_missing_driver_and_invalid_timeouts():
    cfg = IniConfiguration()
    cfg._data = {
        "webdriver": {"edge_path": "C:/nonexistent/edge.exe"},
        "timeouts": {"page_load": -5, "implicit_wait": "not-a-number"}
    }
    res = cfg.validate()
    assert res["status"] == "invalid"
    # expect at least one driver-not-found and timeout-related error
    assert any("Driver not found" in e for e in res["errors"])
    assert any("Invalid timeout value" in e for e in res["errors"])
