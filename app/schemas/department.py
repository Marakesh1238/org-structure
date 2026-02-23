from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .employee import EmployeeRead


class DepartmentCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Название подразделения, \n"
        "уникальное в рамках одного родителя",
        example="IT-отдел"
    )
    parent_id: Optional[int] = Field(
        None,
        description="ID родительского подразделения (null для корневого)",
        example=5
    )


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Новое название подразделения",
        example="Backend-отдел"
    )
    parent_id: Optional[int] = Field(
        None,
        description="Новый ID родительского подразделения",
        example=3
    )


class DepartmentRead(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор")
    name: str = Field(..., description="Название подразделения")
    parent_id: Optional[int] = Field(None, description="ID родителя или null")
    created_at: datetime = Field(..., description="Дата и время создания")


class DepartmentTree(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    children: List["DepartmentTree"] = Field(default_factory=list,
                                             description="Дочерние подразделения")


class DepartmentWithEmployees(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    created_at: datetime
    employees: List[EmployeeRead] = Field(default_factory=list,
                                          description="Сотрудники отдела")


class DepartmentDetail(BaseModel):
    department: DepartmentRead
    employees: List[EmployeeRead] = Field(default_factory=list,
                                          description="Сотрудники текущего отдела")
    children: List["DepartmentDetail"] = Field(default_factory=list,
                                               description="Дочерние отделы с их сотрудниками")
