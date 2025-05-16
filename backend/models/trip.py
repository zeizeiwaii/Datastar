from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from .database import Base

class Trip(Base):
    __tablename__ = "user_request"

    id = Column("request_id", Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    origin_name = Column(String, nullable=False)
    destination_name = Column(String, nullable=False)
    origin_location = Column(Geography('Point', srid=4326), nullable=False)
    destination_location = Column(Geography('Point', srid=4326), nullable=False)
    passenger_count = Column("people_count", Integer, default=1, nullable=False)
    departure_time = Column(DateTime(timezone=True), nullable=False)
    created_at = Column("submit_time", DateTime(timezone=True), server_default=func.now())
    status = Column(String, default='pending')
    cluster_id = Column(Integer, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="trips")
    routes = relationship("Route", secondary="request_dispatch_link", back_populates="trips")

    def __repr__(self):
        return f"<Trip {self.id}>" 