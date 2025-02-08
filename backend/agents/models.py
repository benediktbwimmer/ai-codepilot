from typing import List, Optional
from pydantic import BaseModel

class CodeChunkUpdate(BaseModel):
    filename: str
    old_code: Optional[str] = ""   # May be empty if inserting new code
    new_code: str
    explanation: str
    # If old_code is empty, anchor_context is required to mark where to insert new_code.
    anchor_context: Optional[str] = None

class CodeChunkUpdates(BaseModel):
    updates: List[CodeChunkUpdate]

class FullCodeUpdate(BaseModel):
    filename: str
    original_code: str
    updated_code: str

class FullCodeUpdates(BaseModel):
    updates: List[FullCodeUpdate]

class ReviewFeedback(BaseModel):
    passed: bool
    feedback: str
    suggestions: Optional[str] = None