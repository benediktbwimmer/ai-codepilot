from typing import List
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

# Pydantic models for structured output.
class RelevantFile(BaseModel):
    filename: str

class RelevantFiles(BaseModel):
    files: List[RelevantFile]

class ContextBuilderAgent:
    def __init__(self):
        self.model = OpenAIModel("o1-mini")
        self.agent = Agent(self.model, result_type=str)
        self.parser_model = OpenAIModel("gpt-4o-mini")
        self.parser_agent = Agent(self.parser_model, result_type=RelevantFiles)
    
    async def build_context(self, task: str, repo_map: str) -> RelevantFiles:
        prompt = (
            f"Given the following repository map:\n{repo_map}\n\n"
            f"Identify the list of files that are relevant for the following task:\n{task}\n"
            "Output the list as JSON: an object with a key 'files' that maps to an array of objects "
            "each having a 'filename' key."
        )
        raw_output_response = await self.agent.run(prompt)
        raw_output = raw_output_response.data
        structured_files_response = await self.parser_agent.run(raw_output)
        structured_files = structured_files_response.data
        return structured_files
