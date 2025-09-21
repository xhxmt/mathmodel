import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import typer
from dotenv import load_dotenv, set_key, find_dotenv
import asyncio
from app.core.llm.llm import LLM
from app.config.setting import settings
import litellm

app = typer.Typer()
config_app = typer.Typer()
app.add_typer(config_app, name="config")

ENV_FILE = find_dotenv(".env.dev")
if not ENV_FILE:
    ENV_FILE = ".env.dev"
if not os.path.exists(ENV_FILE):
    with open(ENV_FILE, "w") as f:
        pass

def set_env_value(key: str, value: str):
    load_dotenv(ENV_FILE, override=True)
    set_key(ENV_FILE, key, value)
    print(f"Set {key} to {value}")

@config_app.command("set-api-key")
def set_api_key(
    agent: str = typer.Argument(..., help="Agent name (e.g., coordinator, modeler, coder, writer)"),
    api_key: str = typer.Argument(..., help="API key"),
):
    """
    Sets the API key for a specific agent.
    """
    variable_name = f"{agent.upper()}_API_KEY"
    set_env_value(variable_name, api_key)

@config_app.command("set-model")
def set_model(
    agent: str = typer.Argument(..., help="Agent name (e.g., coordinator, modeler, coder, writer)"),
    model: str = typer.Argument(..., help="Model name"),
):
    """
    Sets the model for a specific agent.
    """
    variable_name = f"{agent.upper()}_MODEL"
    set_env_value(variable_name, model)

@config_app.command("set-base-url")
def set_base_url(
    agent: str = typer.Argument(..., help="Agent name (e.g., coordinator, modeler, coder, writer)"),
    base_url: str = typer.Argument(..., help="Base URL"),
):
    """
    Sets the base URL for a specific agent.
    """
    variable_name = f"{agent.upper()}_BASE_URL"
    set_env_value(variable_name, base_url)

async def test_agent_connection(agent_name: str):
    """
    Tests the connection for a single agent.
    """
    print(f"Testing connection for {agent_name}...")
    api_key = getattr(settings, f"{agent_name.upper()}_API_KEY")
    model = getattr(settings, f"{agent_name.upper()}_MODEL")
    base_url = getattr(settings, f"{agent_name.upper()}_BASE_URL")

    if not all([api_key, model]):
        print(f"API key or model not configured for {agent_name}. Skipping.")
        return

    llm = LLM(api_key=api_key, model=model, base_url=base_url, task_id="test")
    try:
        history = [{"role": "user", "content": "Hello"}]
        kwargs = {
            "api_key": llm.api_key,
            "model": llm.model,
            "messages": history,
            "stream": False,
        }
        if llm.base_url:
            kwargs["base_url"] = llm.base_url

        await litellm.acompletion(**kwargs)
        print(f"Connection to {agent_name} successful.")
    except Exception as e:
        print(f"Failed to connect to {agent_name}: {e}")

@app.command()
def test(
    agent: str = typer.Option(None, help="Agent name to test (e.g., coordinator, modeler, coder, writer). If not provided, all agents will be tested."),
):
    """
    Tests the API connection for the specified agent(s).
    """
    # Reload settings to pick up changes from .env.dev
    load_dotenv(ENV_FILE, override=True)
    settings_refreshed = settings.from_env()

    agents_to_test = [agent] if agent else ["coordinator", "modeler", "coder", "writer"]

    async def run_tests():
        tasks = [test_agent_connection(agent_name) for agent_name in agents_to_test]
        await asyncio.gather(*tasks)

    asyncio.run(run_tests())

from app.core.cli_workflow import CliMathModelWorkFlow
from app.schemas.request import Problem
from app.schemas.enums import CompTemplate, FormatOutPut
from app.utils.common_utils import create_task_id

@app.command()
def run(
    problem_dir: str = typer.Argument(..., help="Path to the problem directory."),
):
    """
    Runs the MathModelAgent workflow on a given problem.
    """
    print(f"Running workflow for problem in directory: {problem_dir}")
    if not os.path.isdir(problem_dir):
        print(f"Error: Directory not found at {problem_dir}")
        raise typer.Exit(code=1)

    questions_file = os.path.join(problem_dir, "questions.txt")
    if not os.path.isfile(questions_file):
        print(f"Error: questions.txt not found in {problem_dir}")
        raise typer.Exit(code=1)

    with open(questions_file, "r", encoding="utf-8") as f:
        ques_all = f.read()

    print("Questions loaded successfully.")

    task_id = create_task_id()
    problem = Problem(
        task_id=task_id,
        ques_all=ques_all,
        comp_template=CompTemplate.CHINA,
        format_output=FormatOutPut.Markdown,
    )

    async def run_workflow():
        workflow = CliMathModelWorkFlow()
        await workflow.execute(problem, problem_dir)

    asyncio.run(run_workflow())


if __name__ == "__main__":
    app()
