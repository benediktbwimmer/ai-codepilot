from typing import Optional
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from backend.agents.models import ReviewFeedback, FullCodeUpdates
from backend.agents.utils import send_usage

class ReviewAgent:
    MODEL_NAME = "gpt-4o-mini"

    def __init__(self, comm=None):
        self.model = OpenAIModel(self.MODEL_NAME)  # Using a more capable model for review
        self.agent = Agent(
            self.model,
            result_type=ReviewFeedback,
            system_prompt=(
                "You are an expert code reviewer. Review the code changes and provide constructive feedback.\n"
                "For each file:\n"
                "1. Check if the changes correctly implement the requested task\n"
                "2. Look for best practices\n"
                "3. Identify potential bugs\n"
                "4. Consider side effects\n"
                "Respond with a ReviewFeedback object containing:\n"
                "- passed: boolean indicating if the changes are acceptable\n"
                "- feedback: string explaining what was checked and what was found\n"
                "- suggestions: string with specific suggestions for improvement (if any)"
            )
        )
        self.comm = comm

    async def review(self, updates: FullCodeUpdates, task: str) -> ReviewFeedback:
        """Review code updates and provide feedback.
        
        Args:
            updates: The code updates to review
            task: The task these changes are meant to implement
            
        Returns:
            ReviewFeedback containing passed status, feedback and suggestions
        """
        # Format the updates for review
        updates_text = ""
        for update in updates.updates:
            updates_text += f"\nFile: {update.filename}\n"
            updates_text += f"Original:\n{update.original_code}\n"
            updates_text += f"Updated:\n{update.updated_code}\n"

        prompt = (
            f"Task to implement:\n{task}\n\n"
            "Review the following code changes that implement this task. Check for:\n"
            "1. Whether the changes correctly implement the requested task\n"
            "2. Best practices\n"
            "3. Potential bugs\n"
            "4. Side effects\n\n"
            f"Changes to review:\n{updates_text}"
        )

        review_response = await self.agent.run(prompt)
        await send_usage(self.comm, review_response, "review", self.MODEL_NAME)

        return review_response.data