from pydantic import BaseModel, Field


class IngestRecord(BaseModel):
    source: str = Field(min_length=1, max_length=128)
    payload: dict
