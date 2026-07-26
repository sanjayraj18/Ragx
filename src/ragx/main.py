"""Uvicorn entrypoint: `uvicorn ragx.main:app`.

The only module in the codebase allowed to build the app at import time —
its sole purpose is to be imported by the server process. Nothing else
imports this module.
"""

from ragx.api.app import create_app

app = create_app()