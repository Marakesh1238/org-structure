from typing import Optional
from pydantic import BaseModel, Field
from datetime import date, datetime


class EmployeeCreate(BaseModel):
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Полное имя сотрудника",
        example="Иван Петров"
    )
    position: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Должность",
        example="Разработчик"
    )
    hired_at: Optional[date] = Field(
        None,
        description="Дата приёма на работу (YYYY-MM-DD)",
        example="2023-05-15"
    )


class EmployeeRead(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор")
    department_id: int = Field(..., description="ID отдела")
    full_name: str = Field(..., description="Полное имя")
    position: str = Field(..., description="Должность")
    hired_at: Optional[date] = Field(None, description="Дата приёма")
    created_at: datetime = Field(..., description="Дата создания записи")