from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class RequestDispatchLink(Base):
    __tablename__ = "request_dispatch_link"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("user_request.request_id"))
    plan_id = Column(Integer, ForeignKey("dispatch_plan.plan_id")) 