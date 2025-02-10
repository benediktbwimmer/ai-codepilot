from typing import List
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from backend.agents.models import CodeChunkUpdate
from backend.agents.utils import send_usage
import logging

logger = logging.getLogger(__name__)

class MergeAgent:
    MODEL_NAME = "gpt-4o-mini"

    def __init__(self, comm=None, root_directory: str = "."):
        self.model = OpenAIModel(self.MODEL_NAME)
        self.agent = Agent(
            self.model,
            result_type=str,
            system_prompt=(
                "You are an expert code merging assistant. Your task is to apply multiple code updates "
                "to existing code while preserving structure and context. You receive the original "
                "code and a list of updates to apply. Each update will be either:\n"
                "1. A replacement (with old code and new code)\n"
                "2. An insertion (with new code and anchor context to insert after)\n"
                "Apply all changes carefully, maintaining proper indentation and structure. "
                "Only output the final merged code after applying all updates, nothing else."
            )
        )
        self.comm = comm
        self.root_directory = root_directory

    def _sanitize_code(self, code: str) -> str:
        """Strip whitespace and remove triple backticks from code if present."""
        code = code.strip()
        if code.startswith("```"):
            # Remove first line if it starts with backticks
            code = "\n".join(code.split("\n")[1:])
        if code.endswith("```"):
            # Remove last line if it ends with backticks
            code = "\n".join(code.split("\n")[:-1])
        return code.strip()

    async def apply_code_updates(self, original_code: str, updates: List[CodeChunkUpdate]) -> str:
        """Apply all code updates in a single LLM call."""
        # Construct a detailed prompt with all updates
        updates_description = []
        for i, update in enumerate(updates, 1):
            if update.old_code:
                updates_description.append(
                    f"Update {i} (REPLACE):\n"
                    f"Find and replace this code:\n{update.old_code}\n"
                    f"With this new code:\n{update.new_code}\n"
                )
            else:
                updates_description.append(
                    f"Update {i} (INSERT):\n"
                    f"Insert this code:\n{update.new_code}\n"
                    f"After this context:\n{update.anchor_context}\n"
                )

        prompt = (
            "Apply the following updates to the code while maintaining proper indentation and structure.\n"
            f"Original code:\n{original_code}\n\n"
            "Updates to apply:\n" + "\n".join(updates_description) + "\n"
            "Output only the final merged code after applying all updates, nothing else."
        )

        merge_response = await self.agent.run(prompt)
        await send_usage(self.comm, merge_response, "merge", self.MODEL_NAME)
        return self._sanitize_code(merge_response.data)