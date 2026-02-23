import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Employee
from app.schemas import employee as emp_schema

logger = logging.getLogger(__name__)


async def create_employee(db: AsyncSession,
                          department_id: int,
                          emp: emp_schema.EmployeeCreate):
    logger.info(f"Creating employee in department_id={department_id}: "
                f"full_name='{emp.full_name}', position='{emp.position}',"
                f"hired_at={emp.hired_at}")

    db_emp = Employee(
        department_id=department_id,
        full_name=emp.full_name.strip(),
        position=emp.position.strip(),
        hired_at=emp.hired_at,
    )
    db.add(db_emp)
    await db.flush()
    await db.refresh(db_emp)

    logger.info(f"Employee created successfully with id={db_emp.id}")
    return db_emp
