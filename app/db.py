from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Files(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_path: Mapped[str]
    number_word: Mapped[int]


class FilesBase(BaseModel):
    file_path: str
    number_word: int


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def add_file_to_db(session, files_data):
    files = Files(**files_data.dict())
    session.add(files)
    session.commit()
    session.refresh(files)


def get_file_from_db(session):

    files = session.scalars(
        select(Files)
    ).all()

    return files


