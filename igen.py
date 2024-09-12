import dotenv

from langchain.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_core.pydantic_v1 import BaseModel
from langchain_experimental.tabular_synthetic_data.openai import (
    create_openai_data_generator,
)
from langchain_openai import ChatOpenAI


class Instruction(BaseModel):
    phrases: list[str]


dotenv.load_dotenv()


def generate(subject: str, operation: str, style: str, examples: list[str], slots: str = '', n=10, extra='',
             runs=1) -> [Instruction]:
    # examples = ["Start cleaning", "begin cleaning"]

    _examples = [
        {
            "example": f"""phrases: {examples}"""
        }
    ]

    prompt_prefix = """"A {subject} app has a voice assistant feature that allows users to interact with the voice assistant and have it perform various operations.
    Your task is to help the user generate the most commonly used phrases in spoken American English so they can give instructions to the voice assistant for related operations.
    
    1. The generated phrases should align with how American English is naturally spoken.
    2. The generated phrases should be as brief as possible.
    
    Now, the user needs to give instructions to the voice assistant to perform the operation "{operation}."
    Spoken style: {style}.
    
    Examples as below:"""

    prompt_suffix = """The curly braces {{}} in the example are placeholders, and the output should retain this format.
    
    The meanings of each placeholder are as follows:
    {slots}
    
    Please generate {n} phrases on each run.
    
    {extra}"""

    prompt_template = PromptTemplate(input_variables=["example"], template="{example}")

    few_shot_prompt_template = FewShotPromptTemplate(
        prefix=prompt_prefix,
        examples=_examples,
        suffix=prompt_suffix,
        input_variables=["subject", "operation", "style", "slots", "n", "extra"],
        example_prompt=prompt_template,
    )

    synthetic_data_generator = create_openai_data_generator(
        output_schema=Instruction,
        llm=ChatOpenAI(model="gpt-4o-mini", temperature=1),
        prompt=few_shot_prompt_template
    )

    synthetic_results = synthetic_data_generator.generate(
        # subject='扫地机器人',
        # operation='开始扫地',
        # style='常规',
        # slots='',
        # extra='',
        # n=5,
        # runs=2,
        subject=subject,
        operation=operation,
        style=style,
        slots=slots,
        extra=extra,
        n=n,
        runs=runs,
    )

    return synthetic_results
