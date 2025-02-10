from typing import List, Optional
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.gemini import GeminiModel
from backend.utils import get_file_content
from backend.agents.utils import send_usage
from backend.agents.models import CodeChunkUpdate, CodeChunkUpdates, FullCodeUpdate, FullCodeUpdates
from backend.agents.review_agent import ReviewAgent, ReviewFeedback
import asyncio
import logging
from backend.agents.merge_agent import MergeAgent

logger = logging.getLogger(__name__)

class CoderAgent:
    MAIN_MODEL_NAME = "o1-mini"
    PARSER_MODEL_NAME = "gpt-4o-mini"

    def __init__(self, review: bool = True, max_iterations: int = 1, comm=None, root_directory: str = "."):
        self.model = OpenAIModel(self.MAIN_MODEL_NAME)
        self.agent = Agent(self.model, result_type=str)
        self.parser_model = OpenAIModel(self.PARSER_MODEL_NAME)
        self.parser_agent = Agent(self.parser_model, result_type=CodeChunkUpdates)
        self.review = review
        self.max_iterations = max_iterations
        self.review_agent = ReviewAgent(comm=comm) if review else None  # Pass comm to ReviewAgent
        self.comm = comm
        self.merge_agent = MergeAgent(comm=comm, root_directory=root_directory)  # Pass root_directory to MergeAgent
        self.root_directory = root_directory

    async def update_code(self, task: str, context: str) -> FullCodeUpdates:
        iteration = 0
        previous_feedback = None

        while iteration < self.max_iterations:
            prompt = (
                f"Given the following context:\n{context}\n\n"
                f"Implement the necessary changes for the following task:\n{task}\n"
            )
            
            if previous_feedback:
                prompt += (
                    f"\nPrevious implementation feedback:\n{previous_feedback.feedback}\n"
                    f"Suggestions for improvement:\n{previous_feedback.suggestions}\n"
                    "Please address these issues in this iteration."
                )

            prompt += (
                "\nRespond in JSON format with an array of code updates. Only output valid JSON, nothing else.\n"
                "For each update, provide:\n"
                "- filename: the file to update\n"
                "- old_code: the exact code chunk to be replaced (if empty, it indicates an insertion)\n"
                "- new_code: the new code chunk that will replace the old one or be inserted\n"
                "- explanation: brief explanation of why this change is needed\n"
                "- anchor_context: when inserting new code (empty old_code), this MUST be an exact match of\n"
                "  existing code after which to insert. Include enough context to uniquely identify the location.\n"
            )

            raw_output_response = await self.agent.run(prompt)
            await send_usage(self.comm, raw_output_response, "coder", self.MAIN_MODEL_NAME)
            raw_output = raw_output_response.data
            logger.info(f"Raw output from coder agent (iteration {iteration + 1}): {raw_output}")
            
            structured_updates_response = await self.parser_agent.run(raw_output)
            await send_usage(self.comm, structured_updates_response, "coder-parser", self.PARSER_MODEL_NAME)
            chunk_updates = structured_updates_response.data

            # Group updates by filename and apply changes
            updates_by_file = {}
            for update in chunk_updates.updates:
                updates_by_file.setdefault(update.filename, []).append(update)

            full_updates = []
            for filename, file_updates in updates_by_file.items():
                try:
                    original_code = get_file_content(filename, root_directory=self.root_directory)
                except Exception as e:
                    logger.error(f"Error reading file {filename}: {e}")
                    continue
                
                # Use merge agent to apply updates
                updated_code = await self.merge_agent.apply_code_updates(original_code, file_updates)
                full_updates.append(FullCodeUpdate(
                    filename=filename,
                    original_code=original_code,
                    updated_code=updated_code
                ))

            updates = FullCodeUpdates(updates=full_updates)

            # Review the updates if enabled
            if self.review and self.review_agent:
                review_result = await self.review_agent.review(updates, task)
                
                if review_result.passed:
                    logger.info("Code review passed")
                    if self.comm:
                        await self.comm.send("log", (
                            "\n=== Code Review: PASSED ===\n"
                            f"Feedback: {review_result.feedback}\n"
                            f"Suggestions: {review_result.suggestions or 'None'}\n"
                            "=========================="
                        ))
                    return updates
                else:
                    logger.info(f"Code review failed (iteration {iteration + 1}). Getting feedback and trying again.")
                    if self.comm:
                        await self.comm.send("log", (
                            f"\n=== Code Review: FAILED (Iteration {iteration + 1}/{self.max_iterations}) ===\n"
                            f"Feedback: {review_result.feedback}\n"
                            f"Suggestions: {review_result.suggestions or 'None'}\n"
                            "================================================="
                        ))
                    previous_feedback = review_result
                    iteration += 1
            else:
                return updates

        logger.warning(f"Max iterations ({self.max_iterations}) reached without passing review")
        if self.comm:
            await self.comm.send("log", (
                "\n=== Code Review: MAX ITERATIONS REACHED ===\n"
                f"Final Feedback: {previous_feedback.feedback if previous_feedback else 'No feedback available'}\n"
                f"Final Suggestions: {previous_feedback.suggestions if previous_feedback else 'None'}\n"
                "=========================================="
            ))
        return updates  # Return the last attempt
