import configparser
import os
import textwrap

import pytest

from compass_core.ini_configuration import IniConfiguration


@pytest.mark.new_slice
def test_load_malformed_ini_raises(tmp_path):
    # No section header -> configparser should raise
    f = tmp_path / "bad.ini"
    f.write_text("key = value\n")

    cfg = IniConfiguration()
    with pytest.raises(configparser.Error):
        cfg.load(f)


@pytest.mark.new_slice
def test_missing_section_behavior_returns_default(tmp_path):
    # File has only [defaults] section; requesting missing key returns default
    f = tmp_path / "only_defaults.ini"
    f.write_text("[DEFAULT]\nfoo=bar\n")

    cfg = IniConfiguration()
    cfg.load(f)
    assert cfg.get("nonexistent", "x") == "x"


@pytest.mark.new_slice
def test_large_numeric_and_non_convertible_values(tmp_path):
    content = textwrap.dedent(
        """
        [values]
        big = 9999999999999999999999999
        not_number = 1e1000
        raw = 0000123
        """
    )
    f = tmp_path / "big.ini"
    f.write_text(content)

    cfg = IniConfiguration()
    out = cfg.load(f)
    # big should be parsed as int when possible (may be long int)
    assert isinstance(out["values"]["big"], int)
    # not_number (float overflow) will remain string or raise; ensure present
    assert "not_number" in out["values"]
    # leading-zero string should be parsed to int (0-prefixed treated numeric)
    assert out["values"]["raw"] == 123


@pytest.mark.new_slice
def test_env_vars_do_not_override_loading(tmp_path, monkeypatch):
    # Set COMPASS_* vars to ensure IniConfiguration doesn't implicitly read them
    monkeypatch.setenv("COMPASS_USERNAME", "env_user")
    monkeypatch.setenv("COMPASS_PASSWORD", "env_pass")

    f = tmp_path / "sample.ini"
    f.write_text("[credentials]\nusername=fromfile\n")

    cfg = IniConfiguration()
    cfg.load(f)
    # IniConfiguration does not automatically use COMPASS_* env vars, so file wins
    assert cfg.get("credentials.username") == "fromfile"
