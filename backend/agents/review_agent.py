from typing import Optional
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from backend.agents.models import ReviewFeedback, FullCodeUpdates

class ReviewAgent:
    def __init__(self):
        self.model = OpenAIModel("gpt-4o-mini")  # Using a more capable model for review
        self.agent = Agent(self.model, result_type=ReviewFeedback)

    async def review_updates(self, updates: FullCodeUpdates, task: str) -> ReviewFeedback:
        """
        Review the proposed code updates against the original task requirements.
        Returns detailed feedback including whether the changes pass review and structured suggestions.
        """
        prompt = (
            f"Review the following code changes for this task:\n{task}\n\n"
            "Code Changes:\n"
        )
        
        for update in updates.updates:
            prompt += (
                f"\nFile: {update.filename}\n"
                f"Original Code:\n{update.original_code}\n"
                f"Updated Code:\n{update.updated_code}\n"
                "---\n"
            )

        prompt += (
            "\nAs a code reviewer, evaluate these changes considering:\n"
            "1. Code Placement:\n"
            "   - Are new additions placed in appropriate locations within the file?\n"
            "   - Do they respect the existing code structure?\n"
            "   - Are they properly nested within their parent blocks?\n"
            "\n2. Code Structure:\n"
            "   - Is the indentation correct?\n"
            "   - Are code blocks properly closed?\n"
            "   - Are there any syntax errors?\n"
            "\n3. Implementation:\n"
            "   - Does it fully implement the requested task?\n"
            "   - Are there any potential bugs?\n"
            "   - Is the implementation efficient?\n"
            "\n4. Integration:\n"
            "   - Does it properly integrate with existing code?\n"
            "   - Are there any conflicts with existing functionality?\n"
            "\nIf changes are not correctly placed or structured, provide specific suggestions about:\n"
            "1. The correct location for insertions (e.g., 'after the script tag', 'inside the onMount function')\n"
            "2. The required indentation level\n"
            "3. Any missing context or closing tags\n"
            "\nRespond with a detailed review that will help the coder agent make corrections in the next iteration."
        )

        response = await self.agent.run(prompt)
        return response.data