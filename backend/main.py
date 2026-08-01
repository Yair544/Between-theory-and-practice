"""
FastAPI application.

The frontend is served by the same process as the API. That is a deliberate
simplification for a local analysis tool: one command to start, no CORS, no
second port to explain, and no way to end up running a stale UI against a new
backend.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import __version__
from .api import router
from .config import FRONTEND_DIR, settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("incidentiq")

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Announce the mode at start-up. Offline is a warning, not an info line."""
    if settings.offline:
        logger.warning(
            "Running in OFFLINE mode - no API key found for provider '%s'. "
            "The deterministic engine will be used and every response will say so. "
            "Add a key to .env for the model-assisted analysis.",
            settings.provider,
        )
    else:
        logger.info("Provider: %s  Model: %s", settings.provider, settings.active_model)
    logger.info("Open http://%s:%s in a browser.", settings.host, settings.port)
    yield


app = FastAPI(
    title="IncidentIQ",
    version=__version__,
    description="AI-assisted incident response and root-cause analysis.",
    lifespan=lifespan,
)

app.include_router(router)


# Mounted last so /api/* is matched first.
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:  # pragma: no cover - only if the checkout is incomplete
    logger.error("frontend/ not found at %s - the UI will not be served.", FRONTEND_DIR)
