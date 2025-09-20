from pydantic import BaseModel
from app.schemas.enums import CompTemplate, FormatOutPut


class ExampleRequest(BaseModel):
    example_id: str
    source: str


class Problem(BaseModel):
    task_id: str
    ques_all: str = ""
    comp_template: CompTemplate = CompTemplate.CHINA
    format_output: FormatOutPut = FormatOutPut.Markdown

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        data["comp_template"] = self.comp_template.value
        data["format_output"] = self.format_output.value
        return data
