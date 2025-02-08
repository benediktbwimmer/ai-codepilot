from typing import List
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.gemini import GeminiModel

# Pydantic models for structured plan output.
class Task(BaseModel):
    name: str
    description: str

class Plan(BaseModel):
    tasks: List[Task]

class PlannerAgent:
    def __init__(self):
        self.model = GeminiModel("gemini-2.0-flash-thinking-exp")
        self.agent = Agent(self.model, result_type=str)
        self.parser_model = OpenAIModel("gpt-4o-mini")
        self.parser_agent = Agent(self.parser_model, result_type=Plan)
    
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
        structured_plan_response = await self.parser_agent.run(raw_plan)
        structured_plan = structured_plan_response.data
        return structured_plan
