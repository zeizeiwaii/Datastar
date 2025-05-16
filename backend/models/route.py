from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class Route(Base):
    __tablename__ = "dispatch_plan"

    id = Column("plan_id", Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    path = Column("route_polyline", Text, nullable=False)
    status = Column(String, default='planned')
    start_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联关系
    vehicle = relationship("Vehicle", back_populates="routes")
    trips = relationship("Trip", secondary="request_dispatch_link", back_populates="routes")

    def __repr__(self):
        return f"<Route {self.id}>" 