from services.remediation_engine.patchers.manifest_patcher import (
    patch_package_json,
    patch_requirements_txt,
)


def test_requirements_txt_bumps_pinned_version():
    src = "flask==2.0.0\nlodash-py==1.0.0\n"
    out, frm = patch_requirements_txt(src, "lodash-py", "1.2.3")
    assert frm == "1.0.0"
    assert "lodash-py==1.2.3" in out
    assert "flask==2.0.0" in out


def test_requirements_txt_preserves_comments_and_unrelated_lines():
    src = "# top comment\nflask==2.0.0\n  # nested\nrequests>=2.30.0\n"
    out, frm = patch_requirements_txt(src, "requests", "2.32.0")
    assert frm == "2.30.0"
    assert "# top comment" in out
    assert "requests==2.32.0" in out


def test_requirements_txt_returns_none_when_package_missing():
    src = "flask==2.0.0\n"
    out, frm = patch_requirements_txt(src, "missing-pkg", "9.9.9")
    assert frm is None
    assert out == src


def test_package_json_preserves_caret_qualifier():
    src = '{"dependencies": {"lodash": "^4.17.15"}}'
    out, frm = patch_package_json(src, "lodash", "4.17.21")
    assert frm == "4.17.15"
    assert '"^4.17.21"' in out


def test_package_json_handles_dev_dependency():
    src = '{"devDependencies": {"jest": "~29.0.0"}}'
    out, frm = patch_package_json(src, "jest", "29.7.0")
    assert frm == "29.0.0"
    assert '"~29.7.0"' in out


def test_package_json_returns_none_on_invalid_json():
    out, frm = patch_package_json("not json", "x", "1")
    assert frm is None
    assert out == "not json"
