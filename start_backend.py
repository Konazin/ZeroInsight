"""Entry point for the PyInstaller-packaged desktop app.

Runs only the FastAPI backend (no Vite dev server, no browser open).
FastAPI will also serve the built React frontend from frontend_dist/.
"""
from zero_insight.server.app import run_server

if __name__ == "__main__":
    run_server(open_browser=False)
