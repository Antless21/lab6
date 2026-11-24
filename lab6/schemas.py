"""Схемы входных и выходных JSON-данных."""

from pydantic import BaseModel, ConfigDict, Field


class StudentInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=1, le=120, strict=True)
    group_name: str = Field(min_length=1, max_length=30)


class Student(StudentInput):
    id: int
