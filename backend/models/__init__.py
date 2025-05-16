from .database import Base, engine, SessionLocal, get_db
from .trip import Trip
from .route import Route
from .request_dispatch_link import RequestDispatchLink

# 创建所有表
def create_all_tables():
    Base.metadata.create_all(bind=engine) 