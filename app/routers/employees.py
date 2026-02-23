from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import department as dept_crud
from app.crud import employee as emp_crud
from app.schemas import employee as emp_schema
from app.deps import get_db

router = APIRouter()


@router.post(
    "/departments/{id}/employees/",
    response_model=emp_schema.EmployeeRead,
    summary="Создать сотрудника в подразделении",
    description="Создаёт нового сотрудника в указанном подразделении. Имя и должность обрезаются по краям.",
    responses={
        200: {"description": "Сотрудник успешно создан"},
        404: {"description": "Подразделение не найдено"},
        422: {"description": "Ошибка валидации входных данных"}
    }
)
async def create_employee_endpoint(
    id: int,
    payload: emp_schema.EmployeeCreate,
    db: AsyncSession = Depends(get_db)
):
    dept = await dept_crud.get_department(db, id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    emp = await emp_crud.create_employee(db, id, payload)
    await db.commit()
    await db.refresh(emp)
    return emp
