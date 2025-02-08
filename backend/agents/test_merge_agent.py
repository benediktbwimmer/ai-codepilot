import pytest
from backend.agents.merge_agent import MergeAgent
from backend.agents.models import CodeChunkUpdate

@pytest.fixture
def merge_agent():
    return MergeAgent()

@pytest.mark.asyncio
async def test_replace_code(merge_agent):
    original_code = """def hello():
    print("Hello")
    print("World")
    return True"""
    
    updates = [CodeChunkUpdate(
        filename="test.py",
        old_code='print("World")',
        new_code='print("Updated World")',
        explanation="Update print statement",
        anchor_context=""
    )]
    
    result = await merge_agent.apply_code_updates(original_code, updates)
    assert 'print("Updated World")' in result
    assert merge_agent._validate_python_code(result)

@pytest.mark.asyncio
async def test_insert_code(merge_agent):
    original_code = """def hello():
    print("Hello")
    return True"""
    
    updates = [CodeChunkUpdate(
        filename="test.py",
        old_code="",
        new_code='    print("World")',
        explanation="Add new print statement",
        anchor_context='print("Hello")'
    )]
    
    result = await merge_agent.apply_code_updates(original_code, updates)
    assert 'print("World")' in result
    assert merge_agent._validate_python_code(result)

@pytest.mark.asyncio
async def test_multiple_updates(merge_agent):
    original_code = """def hello():
    print("Hello")
    print("World")
    return True"""
    
    updates = [
        CodeChunkUpdate(
            filename="test.py",
            old_code='print("Hello")',
            new_code='print("Updated Hello")',
            explanation="Update first print",
            anchor_context=""
        ),
        CodeChunkUpdate(
            filename="test.py",
            old_code='print("World")',
            new_code='print("Updated World")',
            explanation="Update second print",
            anchor_context=""
        )
    ]
    
    result = await merge_agent.apply_code_updates(original_code, updates)
    assert 'print("Updated Hello")' in result
    assert 'print("Updated World")' in result
    assert merge_agent._validate_python_code(result)

@pytest.mark.asyncio
async def test_syntax_validation(merge_agent):
    # Test that invalid Python syntax is caught and original code is returned
    original_code = """def hello():
    print("Hello")
    return True"""
    
    updates = [CodeChunkUpdate(
        filename="test.py",
        old_code="",
        new_code='    print("World"',  # Missing closing parenthesis
        explanation="Add invalid print statement",
        anchor_context='print("Hello")'
    )]
    
    result = await merge_agent.apply_code_updates(original_code, updates)
    assert result == original_code  # Should return original code when syntax is invalid

@pytest.mark.asyncio
async def test_js_syntax_validation(merge_agent):
    original_code = """function hello() {
    console.log("Hello");
    return true;
}"""
    
    updates = [CodeChunkUpdate(
        filename="test.js",
        old_code="",
        new_code='    console.log("World"',  # Missing semicolon and parenthesis
        explanation="Add invalid console.log",
        anchor_context='console.log("Hello");'
    )]
    
    result = await merge_agent.apply_code_updates(original_code, updates)
    assert result == original_code  # Should return original code when syntax is invalid

@pytest.mark.asyncio
async def test_typescript_validation(merge_agent):
    original_code = """interface Person {
    name: string;
    age: number;
}

function greet(person: Person): void {
    console.log(`Hello ${person.name}`);
}"""
    
    updates = [
        CodeChunkUpdate(
            filename="test.ts",
            old_code="",
            new_code='    const age: string = person.age;  // Type mismatch to test validation',
            explanation="Add code with TypeScript error",
            anchor_context='console.log(`Hello ${person.name}`);'
        )
    ]
    
    result = await merge_agent.apply_code_updates(original_code, updates)
    assert merge_agent._validate_js_code(result)  # Should still be valid JS/TS syntax even if types are wrong

@pytest.mark.asyncio
async def test_mixed_file_updates(merge_agent):
    # Test that the agent correctly handles updates to different file types
    js_code = """function hello() {
    console.log("Hello");
}"""
    
    py_code = """def hello():
    print("Hello")"""
    
    js_update = CodeChunkUpdate(
        filename="test.js",
        old_code='console.log("Hello")',
        new_code='console.log("Updated Hello");',
        explanation="Update JS log",
        anchor_context=""
    )
    
    py_update = CodeChunkUpdate(
        filename="test.py",
        old_code='print("Hello")',
        new_code='print("Updated Hello")',
        explanation="Update Python print",
        anchor_context=""
    )
    
    # Test JS update
    js_result = await merge_agent.apply_code_updates(js_code, [js_update])
    assert merge_agent._validate_js_code(js_result)
    assert 'console.log("Updated Hello");' in js_result
    
    # Test Python update
    py_result = await merge_agent.apply_code_updates(py_code, [py_update])
    assert merge_agent._validate_python_code(py_result)
    assert 'print("Updated Hello")' in py_result