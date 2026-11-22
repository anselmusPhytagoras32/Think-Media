"""Serve the compiled React application from the API origin (NFR02/06)."""

from pathlib import Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def mount_frontend(app, directory):
    root = Path(directory).resolve()
    if not (root / "index.html").is_file():
        raise RuntimeError("Build the React frontend before starting the hosted application.")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(root / "index.html", headers={"Cache-Control": "no-cache"})

    # Hash-based routing needs no HTML fallback. API errors stay JSON and
    # missing assets return 404 instead of a successful HTML response.
    app.mount("/", StaticFiles(directory=root, check_dir=True), name="frontend")
