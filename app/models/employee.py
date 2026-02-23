from sqlalchemy import Column, DateTime, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    department_id = Column(Integer,
                           ForeignKey("departments.id", ondelete="CASCADE"),
                           nullable=False)
    full_name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    hired_at = Column(Date)

    department = relationship("Department", back_populates="employees")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
