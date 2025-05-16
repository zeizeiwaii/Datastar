from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, unique=True, index=True)
    vehicle_type = Column(String)  # bus, minibus, etc.
    capacity = Column(Integer)  # 载客量
    current_location = Column(JSON)  # 当前位置 {lat: float, lng: float}
    status = Column(String)  # available, in_service, maintenance
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    routes = relationship("Route", back_populates="vehicle")

    def __repr__(self):
        return f"<Vehicle {self.plate_number}>" 