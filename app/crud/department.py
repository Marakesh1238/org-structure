import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.schemas import department as dept_schema
from app.models import Employee, Department

logger = logging.getLogger(__name__)


async def get_department(db: AsyncSession, dept_id: int):
    logger.debug(f"Fetching department with id {dept_id}")

    result = await db.execute(
        select(Department).where(Department.id == dept_id)
    )
    dept = result.scalar_one_or_none()
    if dept:
        logger.debug(f"Department found: {dept.id} - {dept.name}")
    else:
        logger.debug(f"Department with id {dept_id} not found")
    return dept


async def get_department_with_children(db: AsyncSession, dept_id: int):
    logger.debug(f"Fetching department with children, id {dept_id}")
    result = await db.execute(
        select(Department)
        .where(Department.id == dept_id)
        .options(selectinload(Department.children))
    )
    dept = result.scalar_one_or_none()
    if dept:
        logger.debug(f"Department found with {len(dept.children)} children")
    else:
        logger.debug(f"Department with id {dept_id} not found")
    return dept


async def create_department(db: AsyncSession,
                            dept: dept_schema.DepartmentCreate):
    name = dept.name.strip()
    if not name:
        raise ValueError("Department name cannot be empty")
    parent_id = dept.parent_id if dept.parent_id != 0 else None
    logger.info(f"Creating department: name='{name}', parent_id={parent_id}")

    # Проверка уникальности имени в рамках одного родителя
    stmt = select(Department).where(
        Department.name == name,
        Department.parent_id.is_(parent_id) if parent_id is None else Department.parent_id == parent_id
    )
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        logger.warning(f"Duplicate department name '{name}' under parent {parent_id}")
        raise ValueError("Department with this name already exists under the same parent")

    db_dept = Department(
        name=name,
        parent_id=parent_id,
    )
    db.add(db_dept)
    await db.flush()
    await db.refresh(db_dept)
    logger.info(f"Department created with id {db_dept.id}")
    return db_dept


async def update_department(db: AsyncSession, dept_id: int, data: dict):
    logger.info(f"Updating department {dept_id} with data: {data}")
    department = await get_department(db, dept_id)
    if not department:
        logger.warning(f"Department {dept_id} not found")
        return None

    update_values = {}

    # Обработка имени
    if "name" in data:
        new_name = data["name"].strip()
        if not new_name:
            raise ValueError("Department name cannot be empty")
        update_values["name"] = new_name
    else:
        new_name = department.name

    if "parent_id" in data:
        new_parent = data["parent_id"] if data["parent_id"] != 0 else None
        update_values["parent_id"] = new_parent
    else:
        new_parent = department.parent_id

    if "name" in data or "parent_id" in data:
        stmt = select(Department).where(
            Department.name == new_name,
            Department.id != dept_id,
            Department.parent_id.is_(new_parent) if new_parent is None else Department.parent_id == new_parent
        )
        existing = await db.execute(stmt)
        if existing.scalar_one_or_none():
            raise ValueError("Department with this name already exists under the same parent")

    if update_values:
        await db.execute(
            update(Department)
            .where(Department.id == dept_id)
            .values(**update_values)
        )
        logger.info(f"Department {dept_id} updated with {update_values}")
    else:
        logger.info(f"No changes for department {dept_id}")

    return await get_department(db, dept_id)


async def delete_department_cascade(db: AsyncSession, dept: Department):
    logger.info(f"Cascade deleting department {dept.id} ({dept.name})")
    result = await db.execute(
        select(Department).where(Department.parent_id == dept.id)
    )
    children = result.scalars().all()
    if children:
        logger.debug(f"Found {len(children)} child"
                     f" departments, deleting recursively")
        for child in children:
            await delete_department_cascade(db, child)
    await db.delete(dept)
    logger.info(f"Department {dept.id} deleted in cascade mode")


async def delete_department_reassign(db: AsyncSession,
                                     dept: Department,
                                     target_id: int):
    logger.info(f"Reassign deleting department {dept.id}"
                f" ({dept.name}), target_id={target_id}")

    # Перемещаем сотрудников
    result = await db.execute(
        update(Employee)
        .where(Employee.department_id == dept.id)
        .values(department_id=target_id)
        .returning(Employee.id)
    )
    moved_employees = result.scalars().all()
    logger.info(f"Moved {len(moved_employees)} "
                f"employees to department {target_id}")

    # Делаем детей корневыми
    result = await db.execute(
        update(Department)
        .where(Department.parent_id == dept.id)
        .values(parent_id=None)
        .returning(Department.id)
    )
    orphaned_children = result.scalars().all()
    if orphaned_children:
        logger.info(f"Set parent_id=NULL for "
                     f"{len(orphaned_children)} child departments: {orphaned_children}")

    await db.delete(dept)
    logger.info(f"Department {dept.id} deleted in reassign mode")
