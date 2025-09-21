import unittest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from cli import app
import os

runner = CliRunner()

class TestCli(unittest.TestCase):

    def setUp(self):
        # Create a dummy .env.dev file for testing
        self.env_file = ".env.test"
        with open(self.env_file, "w") as f:
            f.write("ENV=test\n")

    def tearDown(self):
        # Remove the dummy .env.dev file
        if os.path.exists(self.env_file):
            os.remove(self.env_file)

    @patch('cli.ENV_FILE', '.env.test')
    def test_config_set_api_key(self):
        result = runner.invoke(app, ["config", "set-api-key", "coordinator", "test_key_123"])
        self.assertEqual(result.exit_code, 0)
        with open(self.env_file, "r") as f:
            content = f.read()
            self.assertIn("COORDINATOR_API_KEY='test_key_123'", content)

    @patch('cli.ENV_FILE', '.env.test')
    def test_config_set_model(self):
        result = runner.invoke(app, ["config", "set-model", "modeler", "test_model_abc"])
        self.assertEqual(result.exit_code, 0)
        with open(self.env_file, "r") as f:
            content = f.read()
            self.assertIn("MODELER_MODEL='test_model_abc'", content)

    @patch('cli.ENV_FILE', '.env.test')
    def test_config_set_base_url(self):
        result = runner.invoke(app, ["config", "set-base-url", "writer", "http://localhost:1234"])
        self.assertEqual(result.exit_code, 0)
        with open(self.env_file, "r") as f:
            content = f.read()
            self.assertIn("WRITER_BASE_URL='http://localhost:1234'", content)

    @patch('litellm.acompletion')
    @patch('cli.settings')
    @patch('cli.ENV_FILE', '.env.test')
    def test_test_command_success(self, mock_settings, mock_acompletion):
        mock_settings.COORDINATOR_API_KEY = "test_key"
        mock_settings.COORDINATOR_MODEL = "test_model"
        mock_settings.COORDINATOR_BASE_URL = "http://localhost"

        # Make the async mock function awaitable
        async def async_mock(*args, **kwargs):
            return MagicMock()
        mock_acompletion.side_effect = async_mock

        result = runner.invoke(app, ["test", "--agent", "coordinator"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Connection to coordinator successful.", result.stdout)

    @patch('app.core.cli_workflow.CliMathModelWorkFlow.execute')
    def test_run_command(self, mock_execute):
        # Create a dummy problem directory
        problem_dir = "test_problem_dir"
        os.makedirs(problem_dir, exist_ok=True)
        with open(os.path.join(problem_dir, "questions.txt"), "w") as f:
            f.write("This is a test question.")

        # Make the async mock function awaitable
        async def async_mock(*args, **kwargs):
            return MagicMock()
        mock_execute.side_effect = async_mock

        result = runner.invoke(app, ["run", problem_dir])

        self.assertEqual(result.exit_code, 0)
        mock_execute.assert_called_once()

        # Clean up the dummy problem directory
        os.remove(os.path.join(problem_dir, "questions.txt"))
        os.rmdir(problem_dir)

if __name__ == '__main__':
    unittest.main()
