from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer,
                primary_key=True,
                index=True)
    name = Column(String(200),
                  nullable=False)
    parent_id = Column(Integer,
                       ForeignKey("departments.id",
                                  ondelete="CASCADE"),
                       nullable=True, index=True)
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now())

    children = relationship("Department",
                            backref="parent",
                            remote_side=[id])
    employees = relationship("Employee",
                             back_populates="department",
                             cascade="all, delete-orphan")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer,
                primary_key=True,
                index=True)
    department_id = Column(Integer,
                           ForeignKey("departments.id", ondelete="CASCADE"),
                           nullable=False,
                           index=True)
    full_name = Column(String(200), nullable=False)
    position = Column(String(200), nullable=False)
    hired_at = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now())

    department = relationship("Department", back_populates="employees")
