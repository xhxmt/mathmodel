# Repository Guidelines

## Project Structure & Module Organization
This FastAPI service bootstraps from `main.py`, which wires the application lifespan and prepares the runtime `project/work_dir` scratch space. Keep the repository root on `PYTHONPATH` so imports resolve via `app.*`.
- `core/` drives the agent workflow (`core/workflow.py`, `core/agents/`, `core/llm/`).
- `routers/` defines HTTP entrypoints and request/response wiring; see `routers/modeling_router.py`.
- `schemas/`, `models/`, `services/`, and `utils/` house Pydantic contracts, Redis coordination, and shared utilities such as `utils/common_utils.py`.
- `tools/` wraps external integrations including the E2B interpreter and OpenAlex adapters.
- `config/` stores TOML templates and `settings.py`; `.env.<env>` files feed runtime secrets.

## Build, Test, and Development Commands
Create a Python 3.12 virtual environment and install the dependencies from `requirements.txt`:
```
pip install -r requirements.txt
```

### Web Application
To run the FastAPI server locally:
```
python -m uvicorn main:app --reload
```
Set `PYTHONPATH` to the repo root if the `app.*` imports fail.

### Command-Line Interface (CLI)
The application now includes a command-line interface. You can run it using `python cli.py`.

**CLI Usage:**

*   **Configure Agent APIs:**
    ```bash
    # Set API key for an agent
    python cli.py config set-api-key <agent_name> <api_key>

    # Set model for an agent
    python cli.py config set-model <agent_name> <model_name>

    # Set base URL for an agent
    python cli.py config set-base-url <agent_name> <base_url>
    ```
    Replace `<agent_name>` with `coordinator`, `modeler`, `coder`, or `writer`.

*   **Test API Connections:**
    ```bash
    # Test all agents
    python cli.py test

    # Test a specific agent
    python cli.py test --agent <agent_name>
    ```

*   **Run the Workflow:**
    ```bash
    python cli.py run <path_to_problem_directory>
    ```
    The problem directory should contain a `questions.txt` file and any necessary data files.

### Testing
To run the test suite:
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
