# Copyright (c) Microsoft. All rights reserved.

from pydantic import BaseModel


class FileRelevance(BaseModel):
    brief_reasoning: str
    recency_probability: float
    relevance_probability: float


class FileManagerData(BaseModel):
    file_data: dict[str, FileRelevance] = {}
