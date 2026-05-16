from shared.utils.version import choose_fix_version, is_higher


def test_is_higher_basic():
    assert is_higher("1.2.3", "1.2.2")
    assert not is_higher("1.2.3", "1.2.3")
    assert not is_higher("1.2.3", "1.3.0")


def test_choose_lowest_fix_above_installed():
    fixes = ["4.17.21", "5.0.0", "4.18.0"]
    assert choose_fix_version("4.17.15", fixes) == "4.17.21"


def test_choose_returns_first_fix_when_all_below_installed():
    assert choose_fix_version("9.0.0", ["1.0", "2.0"]) == "1.0"


def test_choose_returns_none_for_empty_fixes():
    assert choose_fix_version("1.0", []) is None
