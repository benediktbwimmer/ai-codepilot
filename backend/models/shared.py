from typing import List
from pydantic import BaseModel

class RelevantFile(BaseModel):
    filename: str

class RelevantFiles(BaseModel):
    files: List[RelevantFile]