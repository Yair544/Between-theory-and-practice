"""
Shared fixtures.

Every test here runs against the deterministic parts of the engine. Nothing in
this suite calls a model: an assertion whose result depends on a paid API and a
network round-trip is not a test, it is a weather report.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.models import Evidence  # noqa: E402
from backend.services.evidence import extract_evidence  # noqa: E402

SAMPLE_LOGS = """\
2026-05-02T10:14:03Z ERROR payment-client  gateway call failed: read timeout after 5000ms
2026-05-02T10:15:02Z ERROR HikariPool-payment  Connection is not available, request timed out after 30000ms
2026-05-02T10:15:07Z ERROR HikariPool-payment  Connection is not available, request timed out after 30000ms
2026-05-02T10:15:19Z ERROR HikariPool-payment  Connection is not available, request timed out after 30000ms
2026-05-02T10:16:28Z INFO  payment-client  gateway call completed status=200 duration=4910ms
2026-05-02T10:18:06Z WARN  payment-pool    active=10 idle=0 pending=23 maxPoolSize=10
"""

SAMPLE_TRACE = """\
PaymentGatewayTimeout: no response within 5000ms
  at com.acme.payments.PooledGatewayClient.charge(PooledGatewayClient.java:114)
  at com.acme.checkout.CheckoutService.authorize(CheckoutService.java:88)
Caused by: java.net.SocketTimeoutException: Read timed out
"""


@pytest.fixture
def evidence() -> list[Evidence]:
    items, _stats = extract_evidence(
        {"logs": SAMPLE_LOGS, "errors": SAMPLE_TRACE}, max_chars=100_000
    )
    return items


@pytest.fixture
def known_ids(evidence: list[Evidence]) -> set[str]:
    return {item.id for item in evidence}
