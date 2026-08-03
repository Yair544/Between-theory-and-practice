"""
Shared fixtures.

Every test here runs against the deterministic parts of the engine. Nothing in
this suite calls a model: an assertion whose result depends on a paid API and a
network round-trip is not a test, it is a weather report.

That invariant used to be a comment rather than a mechanism. The suite simply
assumed no key was configured - true in CI, false on a developer machine with a
real `.env`, where the API tests quietly started making paid network calls. They
passed anyway, right up until a rate limit made one fail: the pipeline degraded
to the offline engine exactly as designed, the response then disagreed with
`/api/health`, and a test that had nothing to do with networking failed on a
quota error. `_force_offline` below makes the docstring true by construction.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend import config  # noqa: E402
from backend.api import routes  # noqa: E402
from backend.models import Evidence  # noqa: E402
from backend.services.evidence import extract_evidence  # noqa: E402


@pytest.fixture(autouse=True)
def _force_offline(monkeypatch):
    """
    Pin every test to the offline engine, whatever the developer's .env says.

    `routes.py` binds the settings singleton at import time and reads it inside
    each handler, so both names have to be patched: the module the handler reads
    and the one anything else imports later.
    """
    offline = replace(config.settings, provider="offline")
    monkeypatch.setattr(config, "settings", offline)
    monkeypatch.setattr(routes, "settings", offline)
    return offline

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
