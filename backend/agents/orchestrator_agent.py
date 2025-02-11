from typing import List, Any, Dict
import asyncio
import os
import difflib
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from backend.agents.planner_agent import PlannerAgent, Plan
from backend.agents.coder_agent import CoderAgent, FullCodeUpdates
from backend.utils import build_full_context, get_file_content, get_relevant_snippets
from backend.agents.utils import send_usage
from backend.repo_map import RepoMap
from backend.models.shared import RelevantFiles, RelevantFile
from backend.communication import WebSocketCommunicator

class OrchestratorAgent:
    MODEL_NAME = "gpt-4o"

    def __init__(self, repo_stub: str, comm: WebSocketCommunicator, review: bool = True, max_iterations: int = 1, root_directory: str = "."):
        self.model = OpenAIModel(self.MODEL_NAME)
        self.repo_stub = repo_stub
        self.comm = comm
        self.planner = PlannerAgent(comm=comm)
        self.review = review
        self.max_iterations = max_iterations
        self.root_directory = root_directory
        self.coder = CoderAgent(review=self.review, max_iterations=self.max_iterations, comm=comm, root_directory=root_directory)  # Pass comm to CoderAgent
        self.user_prompt = None
        self.agent = Agent(
            self.model,
            result_type=str,
            system_prompt=(
                """You are a senior developer responsible for fulfilling a user request within a codebase, 
                by planning and making incremental changes. Given the user request and the initial repository stub, 
                use the available tools to create a plan, identify relevant files, read file contents, search codebase, and update code. 
                Iterate using the tools until the user request is completely resolved. Only change the codebase when necessary, 
                if the user simply asks for explanation, don't use the 'update_the_code' tool.
                Always use the 'read_file' tool to read the content of files that are relevant to fulfill the user's request.
                Use the 'search' tool to find specific code snippets in the codebase as needed. This is not a websearch!"""
            )
        )

        async def create_plan_tool(ctx: RunContext[str], user_prompt: str) -> Plan:
            """Creates a plan to address the user's request based on the repository context."""
            log_msg = f"[Tool Call: create_plan] with user_prompt: {user_prompt}"
            await self.comm.send("log", log_msg)
            result = await self.planner.plan(user_prompt, self.repo_stub)
            
            # Send planner token usage using utility function
            await send_usage(self.comm, result, "orchestrator-planner")
                    
            await self.comm.send("log", f"[Tool Call: create_plan] returned: {result}")
            return result

        async def update_code_tool(ctx: RunContext[str], task: str, files: List[str] | RelevantFiles) -> str:
            """Updates code based on the task and relevant files."""
            # Convert files to RelevantFiles if it's a list of strings
            if isinstance(files, list):
                files = RelevantFiles(files=[RelevantFile(filename=f) for f in files])
            
            # Convert any relative paths in files to absolute paths
            for file in files.files:
                if not os.path.isabs(file.filename):
                    file.filename = os.path.join(self.root_directory, file.filename)

            # Build full context from the repository stub and relevant files.
            context = build_full_context(self.repo_stub, files, self.root_directory)
            # Add original user prompt to the context
            context += f"\n\nOriginal User Request:\n{self.user_prompt}\n"
            await self.comm.send("log", f"[Tool Call: update_code] with task: {task}\nuser_prompt: {self.user_prompt}\n{files}")

            # Get code updates from the coder agent.
            updates: FullCodeUpdates = await self.coder.update_code(task, context)
            await self.comm.send("log", f"[Tool Call: update_code] received updates for: {[u.filename for u in updates.updates]}")
            results = []
            
            # Process each update sequentially
            for update in updates.updates:
                # Ensure absolute path
                if not os.path.isabs(update.filename):
                    update.filename = os.path.join(self.root_directory, update.filename)

                # Generate a unified diff
                diff = difflib.unified_diff(
                    update.original_code.splitlines(),
                    update.updated_code.splitlines(),
                    fromfile=update.filename,
                    tofile=update.filename,
                    lineterm=""
                )
                diff_text = "\n".join(diff)
                await self.comm.send("diff", diff_text)

                # Handle user interaction for this specific update
                confirmed = False
                while not confirmed:
                    await self.comm.send("confirmation", f"Do you want to accept, discard, or provide feedback for the update for {update.filename}? (y/n/f)")
                    response = await self.comm.receive("confirmation")
                    choice = response.get("content", "").strip().lower()
                    
                    if choice == "f":
                        await self.comm.send("question", f"Please provide your feedback for the update of {update.filename}.")
                        feedback_response = await self.comm.receive("question")
                        feedback = feedback_response.get("content", "").strip()
                        await self.comm.send("log", f"User feedback for {update.filename}: {feedback}")
                        await self.comm.send("confirmation", f"Do you want to accept the update for {update.filename} now? (y/n)")
                        final_response = await self.comm.receive("confirmation")
                        final_choice = final_response.get("content", "").strip().lower()
                        
                        if final_choice == "y":
                            confirmed = True
                            try:
                                full_path = os.path.join(self.root_directory, update.filename)
                                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                                with open(full_path, "w", encoding="utf-8") as f:
                                    f.write(update.updated_code)
                                results.append(f"Updated {update.filename}. Feedback provided: {feedback}")
                                # Refresh repository stub
                                rm = RepoMap(self.root_directory)
                                rm.build_map()
                                self.repo_stub = rm.to_python_stub()
                            except Exception as e:
                                results.append(f"Failed to update {update.filename}: {e}")
                        else:
                            confirmed = True
                            results.append(f"Discarded update for {update.filename} after feedback. Feedback: {feedback}")
                    elif choice == "y":
                        confirmed = True
                        try:
                            full_path = os.path.join(self.root_directory, update.filename)
                            os.makedirs(os.path.dirname(full_path), exist_ok=True)
                            with open(full_path, "w", encoding="utf-8") as f:
                                f.write(update.updated_code)
                            results.append(f"Updated {update.filename}.")
                            # Refresh repository stub
                            rm = RepoMap(self.root_directory)
                            rm.build_map()
                            self.repo_stub = rm.to_python_stub()
                        except Exception as e:
                            results.append(f"Failed to update {update.filename}: {e}")
                    elif choice == "n":
                        confirmed = True
                        results.append(f"Discarded update for {update.filename}.")
                    else:
                        await self.comm.send("log", f"Invalid choice '{choice}'. Please enter 'y', 'n', or 'f'.")

            summary = "\n".join(results)
            await self.comm.send("log", f"[Tool Call: update_code] returned: {summary}")
            return summary

        async def ask_user_tool(ctx: RunContext[str], question: str) -> str:
            """Asks the user a question and returns the response."""
            await self.comm.send("question", question)
            try:
                # Specifically wait for a message of type "question"
                response = await self.comm.receive("question")
                return response.get("content", "")
            except Exception as e:
                await self.comm.send("error", f"Error getting user response: {str(e)}")
                return ""

        async def read_file_tool(ctx: RunContext[str], file_path: str) -> str:
            """Reads the content of a file."""
            # Ensure absolute path
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.root_directory, file_path)
            await self.comm.send("log", f"[Tool Call: read_file] with filepath: {file_path}")
            content = get_file_content(file_path, root_directory=self.root_directory)
            return content

        async def search_tool(ctx: RunContext[str], search_terms: str) -> List[Dict[str, str]]:
            """Searches the codebase for the given search terms and returns relevant snippets with filenames."""
            await self.comm.send("log", f"[Tool Call: search] with search_terms: {search_terms}")
            try:
                snippets = await asyncio.to_thread(get_relevant_snippets, search_terms, self.root_directory)
                await self.comm.send("log", f"[Tool Call: search] found {len(snippets)} snippets.")
                return snippets
            except Exception as e:
                await self.comm.send("error", f"Search tool failed: {str(e)}")
                return []

        # Register our wrapper functions as tools.
        #self.agent.tool(create_plan_tool)
        self.agent.tool(update_code_tool)
        self.agent.tool(ask_user_tool)
        self.agent.tool(read_file_tool)
        self.agent.tool(search_tool)

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
            
            # Send token usage information
            await send_usage(self.comm, response, "orchestrator", self.MODEL_NAME)
            
            # If response.data is a tuple, join its parts; otherwise, use it as is
            final_response = "".join(response.data) if isinstance(response.data, tuple) else str(response.data)
            await self.comm.send("log", f"[Final Agent Response]:\n{final_response}")
            await self.comm.send("completed", "Orchestration completed.")

        except Exception as e:
            error_msg = f"Error during orchestration: {str(e)}"
            await self.comm.send("error", error_msg)
            raise  # Re-raise the exception for proper logging in the server