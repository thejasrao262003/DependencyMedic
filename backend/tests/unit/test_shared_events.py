from shared.events.base import BaseEvent
from shared.events.vuln_events import VulnDiscoveredPayload
from shared.enums import Severity


def test_base_event_defaults():
    event = BaseEvent(
        event_type="vuln.discovered",
        source_service="vuln_intelligence",
        payload={"cve_id": "CVE-2026-1234"},
    )
    assert event.event_id is not None
    assert event.correlation_id is not None
    assert event.timestamp is not None


def test_vuln_discovered_payload():
    payload = VulnDiscoveredPayload(
        vulnerability_id="vuln-123",
        cve_id="CVE-2026-1234",
        severity=Severity.CRITICAL,
        source="NVD",
        summary="Test vulnerability",
    )
    assert payload.severity == Severity.CRITICAL
    assert payload.cve_id == "CVE-2026-1234"
