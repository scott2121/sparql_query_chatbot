import os
from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "postgresql://user:password@db:5432/chatdb"

engine = create_engine(os.environ["DATABASE_URL"])

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
