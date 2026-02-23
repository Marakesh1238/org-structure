from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("departments.id"))

    # Отношения (используем строки)
    parent = relationship("Department", remote_side=[id], backref="children")
    employees = relationship("Employee",
                             back_populates="department",
                             cascade="all, delete-orphan")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
