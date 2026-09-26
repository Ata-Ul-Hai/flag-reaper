"""UI tests. `darkmode-toggle` is only referenced here — production code no
longer uses it, but the tests were never cleaned up."""
from app import flags


def setup_function(fn):
    flags.reset_overrides()


def test_darkmode_toggle_defaults_off():
    assert flags.is_enabled("darkmode-toggle") is False


def test_darkmode_toggle_can_be_forced_on():
    flags.set_test_override("darkmode-toggle", True)
    assert flags.is_enabled("darkmode-toggle") is True
