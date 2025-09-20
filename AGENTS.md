# Repository Guidelines

## Project Structure & Module Organization
This FastAPI service bootstraps from `main.py`, which wires the application lifespan and prepares the runtime `project/work_dir` scratch space. Keep the repository root on `PYTHONPATH` so imports resolve via `app.*`.
- `core/` drives the agent workflow (`core/workflow.py`, `core/agents/`, `core/llm/`).
- `routers/` defines HTTP entrypoints and request/response wiring; see `routers/modeling_router.py`.
- `schemas/`, `models/`, `services/`, and `utils/` house Pydantic contracts, Redis coordination, and shared utilities such as `utils/common_utils.py`.
- `tools/` wraps external integrations including the E2B interpreter and OpenAlex adapters.
- `config/` stores TOML templates and `settings.py`; `.env.<env>` files feed runtime secrets.

## Build, Test, and Development Commands
Create a Python 3.12 virtual environment and install the FastAPI, uvicorn, litellm, pydantic-settings, python-dotenv, redis, and pypandoc packages.
```
python -m uvicorn main:app --reload
```
runs the FastAPI server locally. Set `PYTHONPATH` to the repo root if the `app.*` imports fail.
```
python -m unittest discover tests
```
executes the current suite. Add integration-specific scripts under `tools/` if you need ad-hoc runs.

## Coding Style & Naming Conventions
Follow PEP 8, 4-space indentation, snake_case for modules and functions, PascalCase for classes, and UPPER_CASE constants. Use type hints and concise docstrings on public helpers. Prefer structured logging via `utils/log_util.py` over `print`. Keep new assets ASCII unless an external dataset requires otherwise; align with the existing bilingual comments only when they add clarity.

## Testing Guidelines
Mirror `tests/test_common_utils.py` for unit tests and place fixtures under `tests/mock/`. Skip external tests gracefully when secrets such as `E2B_API_KEY` are missing, using `self.skipTest`. Name new suites `test_*.py` so `unittest` discovery finds them. When verifying data transformations, add sample inputs in `example/` instead of the runtime `project/` folder.

## Commit & Pull Request Guidelines
With no Git history in this snapshot, adopt Conventional Commit prefixes (`feat:`, `fix:`, `chore:`, `docs:`) and keep summaries under 72 characters. PRs should outline motivation, highlight touched directories, list the commands you ran, and note configuration changes (new environment keys, Redis tweaks, third-party services). Attach screenshots or curl traces when modifying FastAPI responses.

## Environment & Configuration Tips
Adjust `.env.dev` for local work and create `.env.<env>` variants for deployments. Keep secrets out of source control. When new models or agents are introduced, update `config/model_config.toml` and any router defaults so validation stays in sync. If you add persistent storage, document required services alongside Redis in the PR checklist.
