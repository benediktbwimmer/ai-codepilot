from typing import List
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.gemini import GeminiModel
from backend.agents.utils import send_usage

# Pydantic models for structured plan output.
class Task(BaseModel):
    name: str
    description: str

class Plan(BaseModel):
    tasks: List[Task]

class PlannerAgent:
    MAIN_MODEL_NAME = "o1-mini"
    PARSER_MODEL_NAME = "gpt-4o-mini"

    def __init__(self, comm=None):
        #self.model = GeminiModel("gemini-2.0-flash-thinking-exp")
        self.model = OpenAIModel(self.MAIN_MODEL_NAME)
        self.agent = Agent(self.model, result_type=str)
        self.parser_model = OpenAIModel(self.PARSER_MODEL_NAME)
        self.parser_agent = Agent(self.parser_model, result_type=Plan)
        self.comm = comm

    async def plan(self, user_prompt: str, context: str) -> Plan:
        system_prompt = (
            f"Context:\n{context}\n\n"
            "Given the above context, create a detailed yet minimal plan consisting of tasks with names and descriptions. Exclude testing and installation tasks; focus on file-creating tasks when feature implementations are requested, and explanation tasks when user requests are for explanations.\n"
            "Address the following user request:\n"
            f"{user_prompt}\n"
            "Output the plan in plain text."
        )
        raw_plan_response = await self.agent.run(system_prompt)
        raw_plan = raw_plan_response.data
        await send_usage(self.comm, raw_plan_response, "planner", self.MAIN_MODEL_NAME)

        structured_plan_response = await self.parser_agent.run(raw_plan)
        structured_plan = structured_plan_response.data
        await send_usage(self.comm, structured_plan_response, "planner-parser", self.PARSER_MODEL_NAME)

        return structured_plan
