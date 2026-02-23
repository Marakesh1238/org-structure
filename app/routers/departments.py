import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.crud import department as dept_crud
from app.schemas import department as dept_schema
from app.deps import get_db
from app.models import Department

logger = logging.getLogger(__name__)

router = APIRouter()


# Вспомогательная функция для построения дерева
async def _build_tree(db: AsyncSession, dept_id: int, depth: int) -> dict:
    stmt = select(Department).where(Department.id == dept_id).options(
        selectinload(Department.employees),
        selectinload(Department.children)
    )
    result = await db.execute(stmt)
    dept = result.scalar_one_or_none()
    if not dept:
        return None

    data = {
        "id": dept.id,
        "name": dept.name,
        "parent_id": dept.parent_id,
        "created_at": dept.created_at,
        "employees": [],
        "children": []
    }

    employees_sorted = sorted(dept.employees, key=lambda e: e.created_at)
    data["employees"] = [
        {
            "id": e.id,
            "department_id": e.department_id,
            "full_name": e.full_name,
            "position": e.position,
            "hired_at": e.hired_at,
            "created_at": e.created_at
        }
        for e in employees_sorted
    ]

    if depth > 1:
        children = []
        for child in dept.children:
            child_tree = await _build_tree(db, child.id, depth - 1)
            if child_tree:
                children.append(child_tree)
        data["children"] = children
    else:
        data["children"] = []

    return data


@router.get(
    "/departments/{id}",
    summary="Получить подразделение с деревом",
    description="""
    Возвращает информацию о подразделении, его сотрудников
    и вложенныи дочерние подразделения
    до указанной глубины (depth).
    Можно исключить сотрудников через include_employees=false.
    """,
    responses={
        200: {
            "description": "Успешный ответ",
            "content": {
                "application/json": {
                    "example": {
                        "department": {"id": 1, "name": "IT",
                                       "parent_id": None,
                                       "created_at": "2023-01-01T00:00:00"},
                        "employees": [{"id": 10, "full_name": "Иван",
                                       "position": "Dev"}],
                        "children": []
                    }
                }
            }
        },
        404: {"description": "Подразделение не найдено"}
    }
)
async def get_department_endpoint(
    id: int,
    depth: int = Query(1, ge=1, le=5),
    include_employees: bool = True,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"GET /departments/{id} called with depth={depth},"
                f"include_employees={include_employees}")
    dept = await dept_crud.get_department(db, id)
    if not dept:
        logger.warning(f"Department {id} not found")
        raise HTTPException(status_code=404, detail="Department not found")

    tree = await _build_tree(db, id, depth)
    if not tree:
        logger.error(f"Failed to build tree for department {id}")
        raise HTTPException(status_code=404, detail="Department not found")

    def strip_employees(node):
        if not include_employees:
            node.pop("employees", None)
        for child in node.get("children", []):
            strip_employees(child)

    strip_employees(tree)

    logger.info(f"Successfully retrieved department {id}")

    return {
        "department": {
            "id": dept.id,
            "name": dept.name,
            "parent_id": dept.parent_id,
            "created_at": dept.created_at
        },
        "employees": tree.get("employees", []) if include_employees else [],
        "children": tree.get("children", [])
    }


@router.post(
    "/departments/",
    response_model=dept_schema.DepartmentRead,
    summary="Создать новое подразделение",
    description="Создаёт подразделение с уникальным именем в рамках одного родителя. Имя обрезается по краям.",
    responses={
        200: {"description": "Подразделение успешно создано"},
        400: {"description": "Ошибка валидации (имя уже существует или пустое)"},
        422: {"description": "Ошибка валидации входных данных"}
    }
)
async def create_department_endpoint(
    payload: dept_schema.DepartmentCreate,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"POST /departments/ called with payload: {payload.model_dump()}")
    try:
        dept = await dept_crud.create_department(db, payload)
        await db.commit()
        await db.refresh(dept)
        logger.info(f"Department created successfully with id={dept.id}")
    except ValueError as e:
        logger.warning(f"Department creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    return dept


@router.patch(
    "/departments/{id}",
    response_model=dept_schema.DepartmentRead,
    summary="Обновить подразделение",
    description="Обновляет название и/или родителя подразделения. Проверяет уникальность имени в новом родителе и предотвращает циклы.",
    responses={
        200: {"description": "Подразделение успешно обновлено"},
        400: {"description": "Ошибка валидации (неверный родитель, дубликат имени или попытка сделать себя родителем)"},
        404: {"description": "Подразделение не найдено"},
        409: {"description": "Обнаружен цикл (попытка переместить подразделение внутрь своего поддерева)"}
    }
)
async def patch_department(
    id: int,
    payload: dept_schema.DepartmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"PATCH /departments/{id} called with payload:"
                f"{payload.model_dump(exclude_unset=True)}")
    dept = await dept_crud.get_department(db, id)
    if not dept:
        logger.warning(f"Department {id} not found for update")
        raise HTTPException(status_code=404, detail="Department not found")

    new_parent_id = payload.parent_id
    if new_parent_id == id:
        logger.warning(f"Attempt to set department {id} as its own parent")
        raise HTTPException(status_code=400,
                            detail="Cannot set department as its own parent")

    if new_parent_id is not None:
        parent = await dept_crud.get_department(db, new_parent_id)
        if not parent:
            logger.warning(f"Parent department {new_parent_id} not found")
            raise HTTPException(status_code=400,
                                detail="Parent department not found")
        cur = parent
        while cur:
            if cur.id == id:
                logger.warning(f"Cycle detected: moving department"
                               f"{id} into its own subtree")
                raise HTTPException(status_code=409,
                                    detail="Cannot move department \n"
                                    "inside its own subtree")
            if cur.parent_id:
                cur = await dept_crud.get_department(db, cur.parent_id)
            else:
                cur = None

    data = payload.dict(exclude_unset=True)
    try:
        updated = await dept_crud.update_department(db, id, data)
        await db.commit()
        logger.info(f"Department {id} updated successfully")
    except ValueError as e:
        logger.warning(f"Department update failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    return updated


@router.delete(
    "/departments/{id}",
    summary="Удалить подразделение",
    description="""
    Удаляет подразделение. Доступны два режима:
    - **cascade** (по умолчанию): удаляет подразделение и всех его сотрудников (каскадно через БД).
    - **reassign**: переводит всех сотрудников в указанное подразделение (reassign_to_department_id),
      делает дочерние подразделения корневыми (parent_id=NULL) и удаляет само подразделение.
    """,
    responses={
        200: {"description": "Подразделение успешно удалено"},
        400: {"description": "Ошибка в параметрах удаления (неверный режим, отсутствует целевой ID для reassign, целевой отдел не найден)"},
        404: {"description": "Подразделение не найдено"}
    }
)
async def delete_department_endpoint(
    id: int,
    mode: str = Query("cascade"),
    reassign_to_department_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"DELETE /departments/{id} called with mode={mode},"
                f"reassign_to={reassign_to_department_id}")
    dept = await dept_crud.get_department(db, id)
    if not dept:
        logger.warning(f"Department {id} not found for deletion")
        raise HTTPException(status_code=404, detail="Department not found")

    if mode not in ("cascade", "reassign"):
        logger.warning(f"Invalid deletion mode: {mode}")
        raise HTTPException(status_code=400, detail="Invalid mode")

    if mode == "reassign":
        if reassign_to_department_id is None:
            logger.warning("reassign_to_department_id "
                           "missing for reassign mode")
            raise HTTPException(status_code=400,
                                detail="reassign_to_department_id \n"
                                "is required for reassign mode")
        target = await dept_crud.get_department(db, reassign_to_department_id)
        if not target:
            logger.warning(f"Target department "
                           f"{reassign_to_department_id} not found")
            raise HTTPException(status_code=400,
                                detail="Target department not found")
        await dept_crud.delete_department_reassign(db,
                                                   dept,
                                                   reassign_to_department_id)
        logger.info(f"Department {id} deleted in reassign mode, "
                    f"employees moved to {reassign_to_department_id}")
    else:
        await dept_crud.delete_department_cascade(db, dept)
        logger.info(f"Department {id} deleted in cascade mode")

    await db.commit()
    logger.info(f"Department {id} deletion committed")
    return {"status": "deleted"}
