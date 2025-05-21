from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./favorites.db"

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    from models import Favorite
    SQLModel.metadata.create_all(engine)
