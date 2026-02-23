import asyncio
import logging
from datetime import date

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Department, Employee

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def clear_database(db: AsyncSession):
    """Очищает таблицы перед заполнением (удаляет все записи)."""
    logger.info("Clearing database...")
    await db.execute(delete(Employee))
    await db.execute(delete(Department))
    await db.commit()
    logger.info("Database cleared.")


async def seed_database(db: AsyncSession):
    """Заполняет базу тестовыми данными."""
    logger.info("Seeding database...")

    company = Department(name="Компания", parent_id=None)
    db.add(company)
    await db.flush()

    it_dept = Department(name="IT", parent_id=company.id)
    hr_dept = Department(name="HR", parent_id=company.id)
    accounting_dept = Department(name="Бухгалтерия", parent_id=company.id)
    db.add_all([it_dept, hr_dept, accounting_dept])
    await db.flush()

    backend_dept = Department(name="Backend", parent_id=it_dept.id)
    frontend_dept = Department(name="Frontend", parent_id=it_dept.id)
    db.add_all([backend_dept, frontend_dept])
    await db.flush()

    employees = [
        Employee(department_id=it_dept.id, full_name="Иван Иванов", position="Программист", hired_at=date.fromisoformat("2023-01-10")),
        Employee(department_id=it_dept.id, full_name="Петр Петров", position="Тестировщик", hired_at=date.fromisoformat("2023-02-15")),

        Employee(department_id=hr_dept.id, full_name="Анна Сергеева", position="HR-менеджер", hired_at=date.fromisoformat("2022-11-20")),


        Employee(department_id=backend_dept.id, full_name="Сергей Смирнов", position="Backend-разработчик", hired_at=date.fromisoformat("2023-03-01")),
        Employee(department_id=backend_dept.id, full_name="Дмитрий Козлов", position="DevOps", hired_at=date.fromisoformat("2023-04-12")),

        Employee(department_id=frontend_dept.id, full_name="Елена Новикова", position="Frontend-разработчик", hired_at=date.fromisoformat("2023-05-20")),
    ]
    db.add_all(employees)

    await db.commit()
    logger.info("Database seeded successfully.")


async def main():
    async with AsyncSessionLocal() as db:
        await clear_database(db)
        await seed_database(db)


if __name__ == "__main__":
    asyncio.run(main())
