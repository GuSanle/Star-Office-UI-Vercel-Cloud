# Agent Cloud (Forked from Star Office UI) - Development Guidelines

## 1. Fork Guidelines & Community Standards
- **Attribution & Upstream:** Always maintain the original attribution to Ring Hyacinth & Simon Lee, and the community contributors. The original `LICENSE` file must be kept intact.
- **README Modifications:** `README.md` can be modified to describe the new "Agent Cloud Dashboard" functionalities. However, you must include a clear notice at the top indicating that this is a modified fork of the original "Star Office UI" project, and include a link back to the original repository.
- **Art Assets License (CRITICAL):** All art assets (sprites, backgrounds, UI elements) are strictly **non-commercial only**. If this project is ever deployed for commercial purposes, **all art assets must be replaced** with original work.

## 2. Technical Standards
- **Dependency Management:** Use `uv` for all dependency management. Do not use `pip install` directly. Add dependencies via `uv add <package>` so they are tracked in `pyproject.toml` and `uv.lock`.
- **Backend Framework:** The project uses **Flask** as the primary backend entry point (`backend/app.py`).
- **State & Caching:** We use Redis for state management and caching via the standard Redis protocol (`backend/redis_utils.py`) to support Vercel Serverless environment.
- **Code Formatting & Linting:** Use `ruff` for all Python linting and formatting. Run `make lint` before committing.
