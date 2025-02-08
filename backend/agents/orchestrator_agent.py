# ./agents/orchestrator_agent.py
from typing import List, Any, Dict
from pydantic import BaseModel, Field
import asyncio
import difflib
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from backend.agents.planner_agent import PlannerAgent, Plan
from backend.agents.context_builder import ContextBuilderAgent, RelevantFiles
from backend.agents.coder_agent import CoderAgent, FullCodeUpdate, FullCodeUpdates
from backend.utils import build_full_context, get_file_content
from backend.repo_map import RepoMap

class OrchestratorAgent:
    def __init__(self, repo_stub: str, comm, review: bool = True, max_iterations: int = 1, root_directory: str = "."):
        self.model = OpenAIModel("gpt-4o")
        self.repo_stub = repo_stub
        self.comm = comm
        self.planner = PlannerAgent()
        self.context_builder = ContextBuilderAgent()
        self.review = review
        self.max_iterations = max_iterations
        self.root_directory = root_directory
        self.coder = CoderAgent(review=self.review, max_iterations=self.max_iterations, comm=comm)  # Pass comm to CoderAgent
        self.user_prompt = None  # Initialize user_prompt attribute
        self.agent = Agent(
            self.model,
            result_type=str,
            system_prompt=(
                "You are a senior developer responsible for fulfilling a user request within a codebase, "
                "by planning and making incremental changes. Given the user request and the initial repository stub, "
                "use the available tools to create a plan, identify relevant files, read file contents and update code. "
                "Iterate using the tools until the user request is completely resolved. Only change the codebase when necessary, "
                "if the user simply asks for explanation, don't use the 'update_the_code' tool."
                "Always use the 'read_file' tool to read the content of files that are relevant to fulfill the user's request."
            )
        )

        async def create_plan_tool(ctx: RunContext[str], user_prompt: str) -> Plan:
            """Creates a plan to address the user's request based on the repository context."""
            log_msg = f"[Tool Call: create_plan] with user_prompt: {user_prompt}"
            await self.comm.send("log", log_msg)
            result = await self.planner.plan(user_prompt, self.repo_stub)
            await self.comm.send("log", f"[Tool Call: create_plan] returned: {result}")
            return result

        # disused tool
        async def find_relevant_files_tool(
            ctx: RunContext[str],
            task_description: str = Field(..., alias="Task Description")
        ) -> RelevantFiles:
            """Finds relevant files in the repository for the given task."""
            await self.comm.send("log", f"[Tool Call: find_relevant_files] with task_description: {task_description}, repo_map: {self.repo_stub[:50]}...")
            result = await self.context_builder.build_context(task_description, self.repo_stub)
            await self.comm.send("log", f"[Tool Call: find_relevant_files] returned: {result}")
            return result

        async def update_code_tool(ctx: RunContext[str], task: str, files: RelevantFiles) -> str:
            """Updates code based on the task and relevant files."""
            # Build full context from the repository stub and relevant files.
            context = build_full_context(self.repo_stub, files)
            # Add original user prompt to the context
            context += f"\n\nOriginal User Request:\n{self.user_prompt}\n"
            await self.comm.send("log", f"[Tool Call: update_code] with task: {task}, user_prompt: {self.user_prompt} files: {files}")
            
            # Get code updates from the coder agent.
            updates: FullCodeUpdates = await self.coder.update_code(task, context)
            await self.comm.send("log", f"[Tool Call: update_code] received updates for: {[u.filename for u in updates.updates]}")
            results = []
            for update in updates.updates:
                # Generate a unified diff between the original and updated code.
                diff = difflib.unified_diff(
                    update.original_code.splitlines(),
                    update.updated_code.splitlines(),
                    fromfile=update.filename,
                    tofile=update.filename,
                    lineterm=""
                )
                diff_text = "\n".join(diff)

                # Send the diff so that the frontend's diff2html can render it.
                await self.comm.send("diff", diff_text)

                # Ask for confirmation with three options.
                await self.comm.send("confirmation", f"Do you want to accept, discard, or provide feedback for the update for {update.filename}? (y/n/f)")
                choice = (await self.comm.receive()).strip().lower()

                if choice == "f":
                    # Ask for feedback
                    await self.comm.send("question", f"Please provide your feedback for the update of {update.filename}.")
                    feedback = (await self.comm.receive()).strip()
                    await self.comm.send("log", f"User feedback for {update.filename}: {feedback}")
                    # Ask for final confirmation after receiving feedback.
                    await self.comm.send("confirmation", f"Do you want to accept the update for {update.filename} now? (y/n)")
                    final_choice = (await self.comm.receive()).strip().lower()
                    if final_choice == "y":
                        try:
                            with open(update.filename, "w", encoding="utf-8") as f:
                                f.write(update.updated_code)
                            results.append(f"Updated {update.filename}. Feedback provided: {feedback}")
                            # Refresh repository stub after each update.
                            rm = RepoMap(self.root_directory)
                            rm.build_map()
                            self.repo_stub = rm.to_python_stub()
                        except Exception as e:
                            results.append(f"Failed to update {update.filename}: {e}")
                    else:
                        results.append(f"Discarded update for {update.filename} after feedback. Feedback: {feedback}")
                elif choice == "y":
                    try:
                        with open(update.filename, "w", encoding="utf-8") as f:
                            f.write(update.updated_code)
                        results.append(f"Updated {update.filename}.")
                        # Refresh repository stub after each update.
                        rm = RepoMap(self.root_directory)
                        rm.build_map()
                        self.repo_stub = rm.to_python_stub()
                    except Exception as e:
                        results.append(f"Failed to update {update.filename}: {e}")
                else:
                    results.append(f"Discarded update for {update.filename}.")
            summary = "\n".join(results)
            await self.comm.send("log", f"[Tool Call: update_code] returned: {summary}")
            return summary

        async def ask_user_tool(ctx: RunContext[str], question: str) -> str:
            """Asks the user a question and returns the response."""
            await self.comm.send("question", question)
            response = await self.comm.receive()
            return response

        async def read_file_tool(ctx: RunContext[str], file_path: str) -> str:
            """Reads the content of a file."""
            await self.comm.send("log", f"[Tool Call: read_file] with filepath: {file_path}")
            content = await asyncio.to_thread(get_file_content, file_path)
            return content

        # Register our wrapper functions as tools.
        self.agent.tool(create_plan_tool)
        #self.agent.tool(find_relevant_files_tool)
        self.agent.tool(update_code_tool)
        self.agent.tool(ask_user_tool)
        self.agent.tool(read_file_tool)

    async def run(self, user_prompt: str):
        """Starts the agentic process to solve the user request."""
        try:
            self.user_prompt = user_prompt  # Set the user_prompt attribute
            initial_prompt = f"User Request: {self.user_prompt}\n\nRepository Context:\n{self.repo_stub}"
            response = await self.agent.run(initial_prompt)
            
            if response is None or response.data is None:
                error_msg = "Agent returned no response"
                await self.comm.send("error", error_msg)
                return
            
            # If response.data is a tuple, join its parts; otherwise, use it as is
            final_response = "".join(response.data) if isinstance(response.data, tuple) else str(response.data)
            await self.comm.send("log", f"[Final Agent Response]:\n{final_response}")
            await self.comm.send("completed", "Orchestration completed.")

        except Exception as e:
            error_msg = f"Error during orchestration: {str(e)}"
            await self.comm.send("error", error_msg)
            raise  # Re-raise the exception for proper logging in the server