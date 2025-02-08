from typing import List
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from backend.agents.models import CodeChunkUpdate
import logging
import ast
import esprima

logger = logging.getLogger(__name__)

class MergeAgent:
    def __init__(self):
        self.model = OpenAIModel("gpt-4o-mini")
        self.agent = Agent(
            self.model,
            result_type=str,
            system_prompt=(
                "You are an expert code merging assistant. Your task is to apply code updates "
                "to existing code while preserving structure and context. You receive the original "
                "code and a list of updates to apply. Each update contains the old code to replace "
                "(or empty for insertions), new code, and an anchor context for insertions. "
                "Apply the changes carefully, maintaining proper indentation and structure. "
                "Only output the final merged code, nothing else."
            )
        )

    def _validate_python_code(self, code: str) -> bool:
        """Validate if the merged code is syntactically correct Python code."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def _validate_js_code(self, code: str) -> bool:
        """Validate if the merged code is syntactically correct JavaScript/TypeScript code."""
        try:
            esprima.parseScript(code)
            return True
        except Exception:
            # Try parsing as TypeScript if JavaScript parse fails
            try:
                esprima.parseModule(code)
                return True
            except Exception:
                return False

    def _is_python_file(self, code: str, updates: List[CodeChunkUpdate]) -> bool:
        """Check if we're dealing with a Python file."""
        return code.strip().endswith('.py') or any('.py' in update.filename for update in updates)

    def _is_js_file(self, code: str, updates: List[CodeChunkUpdate]) -> bool:
        """Check if we're dealing with a JavaScript/TypeScript file."""
        return any(ext in update.filename for update in updates for ext in ['.js', '.ts', '.jsx', '.tsx'])

    async def apply_code_updates(self, original_code: str, updates: List[CodeChunkUpdate]) -> str:
        """
        Apply a list of code updates to the original code.
        Uses GPT-4-mini to intelligently merge the changes while preserving context.
        """
        # Sort updates by their position in the code (if they include old_code)
        # This helps maintain consistency when applying multiple updates
        updates = sorted(updates, key=lambda u: original_code.find(u.old_code) if u.old_code else float('inf'))
        
        # Build the prompt for the merge operation
        prompt = (
            f"Original code:\n```\n{original_code}\n```\n\n"
            "Updates to apply:\n"
        )
        
        for i, update in enumerate(updates, 1):
            prompt += f"\nUpdate {i}:\n"
            if update.old_code:
                prompt += f"Replace:\n```\n{update.old_code}\n```\n"
            else:
                prompt += f"Insert after context:\n```\n{update.anchor_context}\n```\n"
            prompt += f"With:\n```\n{update.new_code}\n```\n"
            if update.explanation:
                prompt += f"Explanation: {update.explanation}\n"

        # Add language-specific syntax requirements
        is_python = self._is_python_file(original_code, updates)
        is_js = self._is_js_file(original_code, updates)
        if is_python:
            prompt += "\nNOTE: The output MUST be valid Python code with correct syntax.\n"
        elif is_js:
            prompt += "\nNOTE: The output MUST be valid JavaScript/TypeScript code with correct syntax.\n"

        try:
            result = await self.agent.run(prompt)
            merged_code = result.data.strip()
            # Remove any markdown code block markers that might have been added
            if merged_code.startswith("```"):
                merged_code = "\n".join(merged_code.split("\n")[1:-1])
            
            # Validate syntax based on file type
            is_valid = True
            if is_python:
                is_valid = self._validate_python_code(merged_code)
            elif is_js:
                is_valid = self._validate_js_code(merged_code)

            if not is_valid:
                logger.warning("Merged code has invalid syntax, retrying with explicit validation request")
                prompt += "\nWARNING: Previous merge resulted in invalid syntax. Please ensure valid syntax in the output."
                retry_result = await self.agent.run(prompt)
                retry_merged_code = retry_result.data.strip()
                if retry_merged_code.startswith("```"):
                    retry_merged_code = "\n".join(retry_merged_code.split("\n")[1:-1])
                
                if (is_python and self._validate_python_code(retry_merged_code)) or \
                   (is_js and self._validate_js_code(retry_merged_code)):
                    merged_code = retry_merged_code
                else:
                    logger.error("Failed to generate valid code after retry, returning original code")
                    return original_code
            
            logger.info("Successfully merged code updates")
            return merged_code
            
        except Exception as e:
            logger.error(f"Error merging code updates: {e}")
            # If merge fails, return original code
            return original_code