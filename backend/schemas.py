from pydantic import BaseModel
from typing import List


class GenerateRequest(BaseModel):
    date: str
    model: str
    color: str
    interior: str

    priced_lines: List[str]
    all_codes: List[str]

    format: str  # "excel" | "pdf"
