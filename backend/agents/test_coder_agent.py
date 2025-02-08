import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from .coder_agent import CoderAgent, CodeChunkUpdate, CodeChunkUpdates, FullCodeUpdates

@pytest_asyncio.fixture
async def mock_coder_agent():
    with patch('pydantic_ai.models.cohere.AsyncClientV2'):
        with patch('backend.agents.coder_agent.OpenAIModel') as mock_model:
            # Setup mock responses
            mock_model.return_value.generate.return_value = "Mock response"
            agent = CoderAgent()
            return agent

@pytest.mark.asyncio
async def test_update_code_basic(mock_coder_agent):
    # Mock the file content
    original_code = """def hello():
    print("Hello")
"""
    with patch('backend.agents.coder_agent.get_file_content', return_value=original_code):
        # Mock the agent responses
        mock_coder_agent.agent.run = AsyncMock(return_value=Mock(data='''
{
    "updates": [
        {
            "filename": "test.py",
            "old_code": "print(\"Hello\")",
            "new_code": "print(\"Hello, World!\")",
            "explanation": "Making greeting more friendly"
        }
    ]
}
'''))
        mock_coder_agent.parser_agent.run = AsyncMock(return_value=Mock(
            data=CodeChunkUpdates(updates=[
                CodeChunkUpdate(
                    filename="test.py",
                    old_code='print("Hello")',
                    new_code='print("Hello, World!")',
                    explanation="Making greeting more friendly"
                )
            ])
        ))

        # Test the update_code method
        result = await mock_coder_agent.update_code(
            task="Make the greeting more friendly",
            context="We have a simple hello function"
        )

        # Verify the result
        assert isinstance(result, FullCodeUpdates)
        assert len(result.updates) == 1
        assert result.updates[0].filename == "test.py"
        assert result.updates[0].original_code == original_code
        assert 'print("Hello, World!")' in result.updates[0].updated_code

@pytest.mark.asyncio
async def test_update_code_with_insertion(mock_coder_agent):
    # Mock the file content
    original_code = """def hello():
    print("Hello, World!")
"""
    with patch('backend.agents.coder_agent.get_file_content', return_value=original_code):
        # Mock the agent responses
        mock_coder_agent.agent.run = AsyncMock(return_value=Mock(data='''
{
    "updates": [
        {
            "filename": "test.py",
            "old_code": "",
            "new_code": "    return \"Hello, World!\"",
            "explanation": "Adding return statement",
            "anchor_context": "print(\"Hello, World!\")"
        }
    ]
}
'''))
        mock_coder_agent.parser_agent.run = AsyncMock(return_value=Mock(
            data=CodeChunkUpdates(updates=[
                CodeChunkUpdate(
                    filename="test.py",
                    old_code="",
                    new_code='    return "Hello, World!"',
                    explanation="Adding return statement",
                    anchor_context='print("Hello, World!")'
                )
            ])
        ))

        # Test the update_code method
        result = await mock_coder_agent.update_code(
            task="Add a return statement",
            context="Function should return the greeting"
        )

        # Verify the result
        assert isinstance(result, FullCodeUpdates)
        assert len(result.updates) == 1
        assert result.updates[0].filename == "test.py"
        assert result.updates[0].original_code == original_code
        assert 'return "Hello, World!"' in result.updates[0].updated_code