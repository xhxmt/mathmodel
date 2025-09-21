import os
import shutil
from app.core.agents import WriterAgent, CoderAgent, CoordinatorAgent, ModelerAgent
from app.schemas.request import Problem
from app.tools.openalex_scholar import OpenAlexScholar
from app.utils.log_util import logger
from app.utils.common_utils import create_work_dir, get_config_template
from app.models.user_output import UserOutput
from app.config.setting import settings
from app.tools.interpreter_factory import create_interpreter
from app.tools.notebook_serializer import NotebookSerializer
from app.core.flows import Flows
from app.core.llm.llm_factory import LLMFactory


class CliMathModelWorkFlow:
    task_id: str
    work_dir: str
    ques_count: int = 0
    questions: dict[str, str | int] = {}

    async def execute(self, problem: Problem, problem_dir: str):
        self.task_id = problem.task_id
        self.work_dir, _ = create_work_dir(self.task_id)

        # Copy files from problem_dir to work_dir
        file_counter = 1
        for item in os.listdir(problem_dir):
            s = os.path.join(problem_dir, item)

            if item == 'questions.txt':
                continue

            # get file extension
            _, ext = os.path.splitext(item)

            # create a new safe filename
            new_filename = f"data_file_{file_counter}{ext}"
            d = os.path.join(self.work_dir, new_filename)

            if os.path.isdir(s):
                # For directories, we can just copy them with a new name
                new_dirname = f"data_dir_{file_counter}"
                d = os.path.join(self.work_dir, new_dirname)
                shutil.copytree(s, d, symlinks=False, ignore=None)
            else:
                shutil.copy2(s, d)

            file_counter += 1

        llm_factory = LLMFactory(self.task_id)
        coordinator_llm, modeler_llm, coder_llm, writer_llm = llm_factory.get_all_llms()

        coordinator_agent = CoordinatorAgent(self.task_id, coordinator_llm)

        print("Identifying user intent and breaking down the problem...")

        try:
            coordinator_response = await coordinator_agent.run(problem.ques_all)
            self.questions = coordinator_response.questions
            self.ques_count = coordinator_response.ques_count
        except Exception as e:
            logger.error(f"CoordinatorAgent failed: {e}")
            raise e

        print("Intent identification and problem breakdown complete. Handing over to the modeler.")
        print("Modeler is starting to model...")

        modeler_agent = ModelerAgent(self.task_id, modeler_llm)
        modeler_response = await modeler_agent.run(coordinator_response)

        user_output = UserOutput(work_dir=self.work_dir, ques_count=self.ques_count)

        print("Creating a code sandbox environment...")

        notebook_serializer = NotebookSerializer(work_dir=self.work_dir)
        code_interpreter = await create_interpreter(
            kind="local",
            task_id=self.task_id,
            work_dir=self.work_dir,
            notebook_serializer=notebook_serializer,
            timeout=3000,
        )

        scholar = OpenAlexScholar(task_id=self.task_id, email=settings.OPENALEX_EMAIL)

        print("Sandbox environment created.")
        print("Initializing the coder...")

        coder_agent = CoderAgent(
            task_id=problem.task_id,
            model=coder_llm,
            work_dir=self.work_dir,
            max_chat_turns=settings.MAX_CHAT_TURNS,
            max_retries=settings.MAX_RETRIES,
            code_interpreter=code_interpreter,
        )

        writer_agent = WriterAgent(
            task_id=problem.task_id,
            model=writer_llm,
            comp_template=problem.comp_template,
            format_output=problem.format_output,
            scholar=scholar,
        )

        flows = Flows(self.questions)

        solution_flows = flows.get_solution_flows(self.questions, modeler_response)
        config_template = get_config_template(problem.comp_template)

        for key, value in solution_flows.items():
            print(f"Coder starts solving for {key}...")

            coder_response = await coder_agent.run(
                prompt=value["coder_prompt"], subtask_title=key
            )

            print(f"Coder successfully solved for {key}.")

            writer_prompt = flows.get_writer_prompt(
                key, coder_response.code_response, code_interpreter, config_template
            )

            print(f"Writer starts writing the {key} section...")

            writer_response = await writer_agent.run(
                writer_prompt,
                available_images=coder_response.created_images,
                sub_title=key,
            )

            print(f"Writer finished the {key} section.")

            user_output.set_res(key, writer_response)

        await code_interpreter.cleanup()
        logger.info(user_output.get_res())

        write_flows = flows.get_write_flows(
            user_output, config_template, problem.ques_all
        )
        for key, value in write_flows.items():
            print(f"Writer starts writing the {key} section...")

            writer_response = await writer_agent.run(prompt=value, sub_title=key)

            user_output.set_res(key, writer_response)

        logger.info(user_output.get_res())

        user_output.save_result()
        print("Workflow finished. Results saved.")
