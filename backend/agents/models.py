from typing import List, Optional
from pydantic import BaseModel

class ReviewFeedback(BaseModel):
    """Model representing the feedback from a code review."""
    passed: bool
    feedback: str
    suggestions: Optional[str] = None

class CodeChunkUpdate(BaseModel):
    """Model representing a single code update."""
    filename: str
    old_code: str
    new_code: str
    explanation: str
    anchor_context: Optional[str] = None

class CodeChunkUpdates(BaseModel):
    """Model representing a collection of code updates."""
    updates: List[CodeChunkUpdate]

class FullCodeUpdate(BaseModel):
    """Model representing a full file update."""
    filename: str
    original_code: str
    updated_code: str

class FullCodeUpdates(BaseModel):
    """Model representing a collection of full file updates."""
    updates: List[FullCodeUpdate]