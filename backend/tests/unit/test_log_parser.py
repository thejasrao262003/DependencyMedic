from services.remediation_engine.ci_analysis.log_parser import classify


def test_module_not_found_classified_as_missing_dependency():
    triage = classify("ModuleNotFoundError: No module named 'foo'")
    assert triage.failure_type == "missing_dependency"
    assert triage.confidence >= 0.8


def test_typeerror_is_api_breakage():
    triage = classify("TypeError: validate() takes 2 positional arguments")
    assert triage.failure_type == "api_breakage"


def test_generic_failure_classified_as_test_failure():
    triage = classify("FAILED tests/foo.py::bar")
    assert triage.failure_type == "test_failure"


def test_empty_logs_unknown_with_low_confidence():
    triage = classify("")
    assert triage.failure_type == "unknown"
    assert triage.confidence < 0.5
